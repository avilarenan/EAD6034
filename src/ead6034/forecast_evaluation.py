"""Causal, fixed-parameter forecasts and the evaluation protocol of Aula 4.

Time is the chronological sequence of observed trading bars. Returns do not
contain overnight price changes, but lagged observations may cross sessions.
Private forecast rows contain returns and must not be committed to the repo.
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy import stats


SCALE_MINUTES = {"1min": 1, "5min": 5, "15min": 15, "30min": 30, "60min": 60}


def _constant_matrix(value: np.ndarray, name: str) -> np.ndarray:
    """Remove the time axis, rejecting non-constant state-space matrices."""
    value = np.asarray(value, dtype=float)
    first = value[..., 0]
    if value.shape[-1] != 1 and not np.allclose(
        value, first[..., None], rtol=1e-12, atol=1e-14
    ):
        raise ValueError(f"{name} must be time invariant for this ARMA protocol.")
    return first


def forecast_fixed(
    result: Any, full_y: np.ndarray, train_n: int, max_horizon: int
) -> np.ndarray:
    """Forecast with parameters estimated only on the prefix ``y[:train_n]``.

    Row i, column j predicts y[i+j] using observations strictly before i.
    Training rows are NaN. Each horizon uses the SAME origin: intermediate
    realized observations are never inserted into a multi-step prediction.

    A fixed-parameter Kalman *filter*, never a smoother or optimizer, supplies
    the exact predicted state at each origin. The state is then propagated
    without observations. Filtering the whole observed vector is causal;
    changing later observations cannot change an earlier predicted state.
    Supports time-invariant, univariate ARIMA(p,0,q) with constant or no trend.
    """
    y = np.asarray(full_y, dtype=float)
    if y.ndim != 1 or not np.isfinite(y).all():
        raise ValueError("full_y must be a finite one-dimensional sequence.")
    if not 1 <= train_n < len(y) or max_horizon < 1:
        raise ValueError("Need a nonempty training prefix, test suffix and horizon.")
    trained = np.asarray(result.model.endog, dtype=float).reshape(-1)
    if len(trained) != train_n or not np.array_equal(trained, y[:train_n]):
        raise ValueError("The fitted sample must equal full_y[:train_n] exactly.")
    if tuple(result.model.order)[1] != 0:
        raise ValueError("This return-forecast protocol is restricted to d=0.")

    model = result.model.clone(y)
    filtered = model.filter(result.params, cov_type="none", low_memory=False)
    kalman = filtered.filter_results
    design = _constant_matrix(kalman.design, "design")
    transition = _constant_matrix(kalman.transition, "transition")
    state_intercept = _constant_matrix(kalman.state_intercept, "state_intercept")
    obs_intercept = _constant_matrix(kalman.obs_intercept, "obs_intercept")
    if design.shape[0] != 1:
        raise ValueError("Only univariate forecasts are supported.")
    state = kalman.predicted_state[:, train_n:len(y)].copy()
    predictions = np.full((len(y), max_horizon), np.nan, dtype=float)
    for step in range(max_horizon):
        predictions[train_n:, step] = (design @ state)[0] + obs_intercept[0]
        if step + 1 < max_horizon:
            state = transition @ state + state_intercept[:, None]
    return predictions


def diebold_mariano(
    errors_a: np.ndarray,
    errors_b: np.ndarray,
    *,
    loss: str = "squared",
    q: int = 0,
    h_loss: int = 1,
) -> dict[str, Any]:
    """Lecture DM/HLN test with a rectangular long-run covariance sum.

    d = loss(A) - loss(B), so a negative statistic favors A. Autocovariances
    use denominator n, including at positive lags. This is the unweighted
    gamma(0)+2*sum(gamma(j)) formula of Aula 4, not a Bartlett estimator.
    ``h_loss`` is measured in successive evaluation origins, not original
    bar units. Native one-step and hourly, nonoverlapping 60-minute targets
    both use h_loss=1. Serial dependence beyond overlap is handled by q.

    Inference is approximate and assumes a suitable stationary loss process;
    no robustness to arbitrary heteroskedasticity/nonstationarity is claimed.
    """
    a, b = np.asarray(errors_a, float), np.asarray(errors_b, float)
    if a.ndim != 1 or b.shape != a.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("DM errors must be aligned finite one-dimensional arrays.")
    if loss not in {"squared", "absolute"}:
        raise ValueError("loss must be squared or absolute.")
    if q < 0 or h_loss < 1:
        raise ValueError("q must be nonnegative and h_loss positive.")
    n = len(a)
    effective_q = min(int(q), max(0, n - 2))
    answer: dict[str, Any] = {
        "n": n, "loss": loss, "q_requested": int(q), "q": effective_q,
        "h_loss": h_loss, "mean_loss_difference": np.nan,
        "long_run_variance": np.nan, "statistic": np.nan, "p_value": np.nan,
        "status": "insufficient_observations", "lrv_estimator": "rectangular_autocovariance_sum",
        "reference_distribution": "Student_t_n_minus_1_with_HLN_correction",
    }
    if n < 3:
        return answer
    d = a * a - b * b if loss == "squared" else np.abs(a) - np.abs(b)
    mean = float(d.mean())
    answer["mean_loss_difference"] = mean
    if np.all(d == 0):
        answer.update(status="identical_losses", long_run_variance=0.0)
        return answer
    centered = d - mean
    lrv = float(np.dot(centered, centered) / n)
    for lag in range(1, effective_q + 1):
        lrv += 2.0 * float(np.dot(centered[lag:], centered[:-lag]) / n)
    answer["long_run_variance"] = lrv
    numerical_floor = np.finfo(float).eps * max(float(np.mean(d * d)), np.finfo(float).tiny)
    if not np.isfinite(lrv) or lrv <= numerical_floor:
        answer["status"] = "nonpositive_or_degenerate_long_run_variance"
        return answer
    corrected_n = n + 1 - 2 * h_loss + h_loss * (h_loss - 1) / n
    if corrected_n <= 0:
        answer["status"] = "invalid_HLN_correction"
        return answer
    statistic = mean * np.sqrt(corrected_n / lrv)
    answer.update(
        statistic=float(statistic), p_value=float(2 * stats.t.sf(abs(statistic), df=n - 1)),
        status="computed_approximate",
    )
    return answer


def _validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "bar_start", "date", "sample", "return_pct", "time_band"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing forecast-frame fields: {sorted(missing)}")
    result = frame.reset_index(drop=True).copy()
    for column in ("timestamp", "bar_start"):
        result[column] = pd.to_datetime(result[column])
    if not result.timestamp.is_monotonic_increasing or result.timestamp.duplicated().any():
        raise ValueError("Forecast observations must have unique chronological timestamps.")
    if not np.isfinite(result.return_pct.to_numpy(float)).all():
        raise ValueError("Returns must be finite; missing bars must not be replaced by zero.")
    result["date"] = result.date.astype(str)
    if not result.timestamp.dt.strftime("%Y-%m-%d").eq(result.date).all():
        raise ValueError("date must match the local timestamp date.")
    train = result["sample"].eq("train").to_numpy()
    test = result["sample"].eq("test").to_numpy()
    train_n = int(train.sum())
    if not train_n or not test.any() or not train[:train_n].all() or not test[train_n:].all():
        raise ValueError("Expected a training prefix followed by an evaluation suffix.")
    if not result.loc[train, "timestamp"].dt.year.eq(2024).all():
        raise ValueError("The fixed study protocol uses only 2024 for training.")
    if not result.loc[test, "timestamp"].dt.year.eq(2025).all():
        raise ValueError("The fixed study protocol evaluates only 2025.")
    return result


def _evaluation_origins(frame: pd.DataFrame, scale: str, evaluation: str) -> tuple[np.ndarray, int]:
    test = frame["sample"].eq("test").to_numpy()
    if evaluation == "native":
        return np.flatnonzero(test), 1
    minutes = SCALE_MINUTES[scale]
    horizon = 60 // minutes
    start = frame.bar_start
    clock = start.dt.hour.to_numpy() * 60 + start.dt.minute.to_numpy()
    aligned = (clock >= 9 * 60 + 5) & (clock <= 17 * 60 + 5) & ((clock - (9 * 60 + 5)) % 60 == 0)
    candidates = np.flatnonzero(test & aligned)
    dates = frame.date.to_numpy()
    valid = []
    for i in candidates:
        end = i + horizon
        if end > len(frame) or not test[i:end].all() or not (dates[i:end] == dates[i]).all():
            continue
        # Reject partial targets, missing bars and off-grid timestamps rather
        # than allowing a target to silently cross a session or a source gap.
        expected_ends = pd.date_range(start.iloc[i] + pd.Timedelta(minutes=minutes), periods=horizon, freq=f"{minutes}min")
        if not pd.DatetimeIndex(frame.timestamp.iloc[i:end]).equals(expected_ends):
            continue
        expected_starts = expected_ends - pd.Timedelta(minutes=minutes)
        if not pd.DatetimeIndex(start.iloc[i:end]).equals(expected_starts):
            continue
        valid.append(i)
    return np.asarray(valid, dtype=int), horizon


def evaluate_scale(
    frame: pd.DataFrame,
    prediction_map: Mapping[str, np.ndarray],
    scale: str,
    daily_context: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (PRIVATE forecasts, public accuracy metrics, public DM table).

    Forecast matrices have shape (len(frame), at least 60/bar_minutes), or
    one column for daily. ZERO and TRAIN_MEAN are automatically supplied.
    AR_MA_50_50 is always computed from AR_BIC and MA_BIC when both exist.

    Optional daily_context must have unique date and gap_group columns, with
    groups already assigned using thresholds determined ONLY on 2024. This
    function does not learn groups from evaluation data. Gap-conditioned
    metrics are descriptive, not additional model selection or DM tests.

    Public metric rows contain evaluation, model, group_type/group, n, mse,
    mae, rmse, mse_ratio_vs_zero and mse_gain_vs_zero. DM is only AR_BIC vs
    MA_BIC on the entire chronological loss sequence, for squared/absolute
    loss, principal one-hour serial q and ancillary q=0. No subgroup DM or
    multiple-testing correction outside the supplied course is introduced.
    """
    frame = _validate_frame(frame)
    if scale not in {*SCALE_MINUTES, "1d"}:
        raise ValueError(f"Unsupported scale: {scale}")
    required_horizon = 1 if scale == "1d" else 60 // SCALE_MINUTES[scale]
    arrays: dict[str, np.ndarray] = {}
    for model, predictions in prediction_map.items():
        arr = np.asarray(predictions, dtype=float)
        if arr.ndim != 2 or arr.shape[0] != len(frame) or arr.shape[1] < required_horizon:
            raise ValueError(f"{model}: need ({len(frame)}, >= {required_horizon}) forecast matrix.")
        arrays[model] = arr
    if "AR_BIC" in arrays and "MA_BIC" in arrays:
        arrays["AR_MA_50_50"] = (arrays["AR_BIC"][:, :required_horizon] + arrays["MA_BIC"][:, :required_horizon]) / 2
    y = frame.return_pct.to_numpy(float)
    train_mean = float(frame.loc[frame["sample"].eq("train"), "return_pct"].mean())
    context = pd.Series("unavailable", index=frame.index, dtype=object)
    if "gap_group" in frame:
        context = frame.gap_group.fillna("unavailable").astype(str)
    if daily_context is not None:
        if not {"date", "gap_group"}.issubset(daily_context.columns):
            raise ValueError("daily_context must contain date and gap_group.")
        daily_context = daily_context.copy()
        daily_context["date"] = daily_context.date.astype(str)
        if daily_context.date.duplicated().any():
            raise ValueError("daily_context must have exactly one group per date.")
        context = frame.date.map(daily_context.set_index("date").gap_group).fillna("unavailable")

    private_parts, metric_rows, dm_rows = [], [], []
    evaluations = ["native"] if scale == "1d" else ["native", "common_60min"]
    for evaluation in evaluations:
        origins, horizon = _evaluation_origins(frame, scale, evaluation)
        if not len(origins):
            continue
        actual = np.asarray([y[i:i + horizon].sum() for i in origins])
        predicted = {model: arr[origins, :horizon].sum(axis=1) for model, arr in arrays.items()}
        predicted.setdefault("ZERO", np.zeros(len(origins)))
        predicted.setdefault("TRAIN_MEAN", np.full(len(origins), train_mean * horizon))
        complete = np.logical_and.reduce([np.isfinite(values) for values in predicted.values()])
        n_candidate_origins = len(origins)
        origins, actual = origins[complete], actual[complete]
        predicted = {model: values[complete] for model, values in predicted.items()}
        if not len(origins):
            continue
        end_positions = origins + horizon - 1
        base = pd.DataFrame({
            "scale": scale, "evaluation": evaluation, "horizon_bars": horizon,
            "horizon_minutes": np.nan if scale == "1d" else horizon * SCALE_MINUTES[scale],
            "origin": frame.bar_start.iloc[origins].to_numpy(),
            "target_start": frame.bar_start.iloc[origins].to_numpy(),
            "target_end": frame.timestamp.iloc[end_positions].to_numpy(),
            "date": frame.date.iloc[origins].to_numpy(),
            "time_band": frame.time_band.iloc[origins].to_numpy(),
            "gap_group": context.iloc[origins].to_numpy(),
            "actual": actual,
        })
        errors = {model: actual - values for model, values in predicted.items()}
        grouping: list[tuple[str, str, np.ndarray]] = [("all", "all", np.ones(len(base), dtype=bool))]
        for column in ("time_band", "gap_group"):
            if column == "time_band" and scale == "1d":
                continue
            for group in sorted(base[column].dropna().astype(str).unique()):
                if column == "gap_group" and group == "unavailable":
                    continue
                grouping.append((column, group, base[column].astype(str).eq(group).to_numpy()))
        for model, values in predicted.items():
            rows = base.copy()
            rows["model"], rows["prediction"] = model, values
            rows["error"] = errors[model]
            rows["squared_error"], rows["absolute_error"] = errors[model] ** 2, np.abs(errors[model])
            private_parts.append(rows)
            for group_type, group, mask in grouping:
                error = errors[model][mask]
                mse, mae = float(np.mean(error ** 2)), float(np.mean(np.abs(error)))
                zero_mse = float(np.mean(errors["ZERO"][mask] ** 2))
                ratio = mse / zero_mse if zero_mse > 0 else np.nan
                metric_rows.append({
                    "scale": scale, "evaluation": evaluation, "horizon_bars": horizon,
                    "horizon_minutes": np.nan if scale == "1d" else horizon * SCALE_MINUTES[scale],
                    "model": model, "group_type": group_type, "group": group, "n": len(error),
                    "mse": mse, "mae": mae, "rmse": float(np.sqrt(mse)),
                    "mse_ratio_vs_zero": ratio, "mse_gain_vs_zero": 1 - ratio,
                    "n_candidate_origins_all": n_candidate_origins,
                    "n_dropped_nonfinite_all": n_candidate_origins - len(origins),
                })
        if "AR_BIC" in errors and "MA_BIC" in errors:
            serial_q = 1 if scale == "1d" or evaluation == "common_60min" else 60 // SCALE_MINUTES[scale]
            for loss in ("squared", "absolute"):
                for variant, q in (("principal_serial_dependence", serial_q), ("ancillary_no_serial_dependence", 0)):
                    test = diebold_mariano(errors["AR_BIC"], errors["MA_BIC"], loss=loss, q=q, h_loss=1)
                    dm_rows.append({
                        "scale": scale, "evaluation": evaluation, "model_a": "AR_BIC", "model_b": "MA_BIC",
                        "horizon_bars": horizon, "variant": variant, **test,
                        "interpretation": "negative_statistic_favors_AR; unadjusted_multiple_comparisons; approximate_stationary_loss_assumption",
                    })
    private = pd.concat(private_parts, ignore_index=True) if private_parts else pd.DataFrame()
    for column in ("scale", "evaluation", "time_band", "gap_group", "model"):
        if column in private:
            private[column] = private[column].astype("category")
    return private, pd.DataFrame(metric_rows), pd.DataFrame(dm_rows)
