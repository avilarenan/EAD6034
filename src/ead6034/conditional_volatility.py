"""Aula 6: conditional variance of innovations from a fixed ARMA mean.

The mean is estimated by the caller using training observations only.  This
module estimates variance parameters on its training innovations, without
estimating a second mean or jointly re-estimating ARMA coefficients.  Gaussian
likelihoods, AIC and BIC here are conditional on that common fitted mean and
must NOT be compared with the likelihood of the original state-space ARMA.

After fitting, a one-step variance forecast uses only the previous observed
innovation and variance.  The observation index continues across sessions;
there is no overnight return and no daily reset.  Squared test innovations are
noisy evaluation proxies, NOT observed conditional variances.  No variance
model changes the shared point forecasts of the fixed ARMA mean.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from arch import arch_model
from statsmodels.stats.diagnostic import het_arch
from statsmodels.tsa.stattools import acf, q_stat


# Exclude optimizers effectively on the IGARCH boundary, rather than treating
# a rounding difference of 1e-15 below one as evidence of a finite variance.
STATIONARITY_MARGIN = 1e-8
NEAR_BOUNDARY = 0.98
MODEL_LABELS = {
    "constant": "Constant variance",
    "arch1": "ARCH(1)",
    "garch11": "GARCH(1,1)",
}


def _vector(values: np.ndarray, name: str, *, allow_empty: bool = False) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    if x.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional array")
    if not allow_empty and x.size == 0:
        raise ValueError(f"{name} must not be empty")
    if not np.isfinite(x).all():
        raise ValueError(f"{name} must contain only finite observations")
    return x


def variance_parameters_valid(omega: float, alpha: float, beta: float) -> bool:
    """Positive intercept, nonnegative coefficients and finite long-run variance."""
    return bool(
        np.isfinite([omega, alpha, beta]).all()
        and omega > 0
        and alpha >= 0
        and beta >= 0
        and alpha + beta < 1.0 - STATIONARITY_MARGIN
    )


def forecast_variance(
    test_residuals: np.ndarray,
    *,
    last_residual: float,
    last_variance: float,
    omega: float,
    alpha: float,
    beta: float,
) -> np.ndarray:
    """Causal one-step ARCH/GARCH recursion with fixed training parameters.

    ``out[t]`` is calculated BEFORE using ``test_residuals[t]``.  The latter
    becomes available only to forecast ``out[t + 1]``.  For a constant variance,
    pass alpha=beta=0 and omega equal to the training residual second moment.
    """
    residuals = _vector(test_residuals, "test_residuals", allow_empty=True)
    if not variance_parameters_valid(omega, alpha, beta):
        raise ValueError("Variance parameters violate positivity/stability")
    if not np.isfinite(last_residual) or not np.isfinite(last_variance) or last_variance <= 0:
        raise ValueError("Initial innovation and positive variance must be finite")
    output = np.empty(len(residuals), dtype=float)
    previous_residual, previous_variance = float(last_residual), float(last_variance)
    for index, residual in enumerate(residuals):
        variance = omega + alpha * previous_residual**2 + beta * previous_variance
        if not np.isfinite(variance) or variance <= 0:
            raise FloatingPointError("Variance recursion produced invalid variance")
        output[index] = variance
        previous_residual, previous_variance = float(residual), variance
    return output


def _diagnostic_lags(n: int, requested: list[int] | None) -> list[int]:
    lags = [5, 10, 20] if requested is None else list(requested)
    if not lags or any(not isinstance(lag, (int, np.integer)) or lag <= 0 for lag in lags):
        raise ValueError("diagnostic_lags must be a nonempty list of positive integers")
    # Defaults are capped only by sample size, not by the observed diagnostics.
    if requested is None:
        return sorted({min(lag, max(1, (n - 1) // 5)) for lag in lags})
    if max(lags) >= n / 2:
        raise ValueError("Diagnostic lags must be smaller than half the training sample")
    return sorted(set(map(int, lags)))


def _ljung_box(values: np.ndarray, lags: list[int]) -> pd.DataFrame:
    """Ordinary Ljung-Box, evaluated with an FFT for long intraday series.

    This is exactly statsmodels' conventional statistic and chi-square(lag)
    reference (model_df=0), not the former boundary-adjusted statistic.  No
    ad-hoc degrees-of-freedom subtraction for the GARCH parameters is used.
    Its reference distribution after sequential fitting is approximate.
    """
    correlations = acf(values, adjusted=False, nlags=max(lags), fft=True)
    statistics, pvalues = q_stat(correlations[1:], len(values))
    return pd.DataFrame(
        {"lag": lags, "statistic": statistics[np.array(lags) - 1],
         "pvalue": pvalues[np.array(lags) - 1]}
    )


def fit_volatility(
    train_residuals: np.ndarray,
    test_residuals: np.ndarray,
    scale: str,
    diagnostic_lags: list[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, np.ndarray], dict]:
    """Fit constant, ARCH(1), GARCH(1,1) variances using TRAINING ONLY.

    Return public candidate and training-diagnostic tables, private arrays,
    and a JSON-serializable summary. ``test_residuals`` must be actual outcomes
    minus causal one-step forecasts from the SAME fixed ARMA mean model.
    They never influence fitting, eligibility, diagnostic lags or selection.

    The caller must retain missing-observation and auction metadata separately:
    no values are deleted, interpolated, demeaned, winsorized or reset here.
    Numeric scaling uses the training RMS only and is undone for all variances,
    omega parameters and log-likelihoods. Input units are preserved.
    """
    train = _vector(train_residuals, "train_residuals")
    test = _vector(test_residuals, "test_residuals", allow_empty=True)
    n = len(train)
    if n < 20:
        raise ValueError("At least 20 training innovations are required")
    rms = float(np.sqrt(np.mean(train**2)))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("Training innovations must have positive finite second moment")
    lags = _diagnostic_lags(n, diagnostic_lags)
    scaled = train / rms
    diagnostic_rows: list[dict] = []
    arrays: dict[str, np.ndarray] = {}
    rows: list[dict] = []

    for lag in lags:
        lm, lm_p, f_stat, f_p = het_arch(scaled, nlags=lag, ddof=0)
        diagnostic_rows.append({
            "scale": scale, "model": "fixed_arma_mean", "series": "innovations",
            "test": "ARCH-LM", "lag": lag, "nobs": n, "statistic": float(lm),
            "pvalue": float(lm_p), "reference_df": lag, "model_df": 0,
            "f_statistic": float(f_stat), "f_pvalue": float(f_p),
            "reject_5pct": bool(lm_p < .05), "sample": "train_2024",
            "reference_caveat": "asymptotic; innovations from a pre-estimated mean",
        })

    for model, q in (("constant", None), ("arch1", 0), ("garch11", 1)):
        k = {"constant": 1, "arch1": 2, "garch11": 3}[model]
        row = {
            "scale": scale, "model": model, "model_label": MODEL_LABELS[model],
            "nobs": n, "nobs_test": len(test), "variance_parameter_count": k,
            "distribution": "normal", "mean_refitted": False,
            "fit_method": "variance_MLE_conditional_on_fixed_ARMA_mean",
            "input_rms_scaling": rms, "converged": False, "eligible": False,
            "selected_bic": False, "status": "failed", "warning": "",
            "near_boundary": False,
        }
        try:
            if model == "constant":
                omega, alpha, beta = rms**2, 0.0, 0.0
                h_train = np.full(n, omega)
                llf = -.5 * n * (np.log(2 * np.pi) + np.log(omega) + 1)
                convergence_flag, convergence_message, fit_warnings = 0, "closed_form", []
            else:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    fitted = arch_model(
                        scaled, mean="Zero", vol="GARCH", p=1, o=0, q=q,
                        power=2.0, dist="normal", rescale=False,
                    ).fit(
                        update_freq=0, disp="off", show_warning=False,
                        options={"maxiter": 2000, "ftol": 1e-9},
                    )
                fit_warnings = [str(w.message) for w in caught]
                omega = float(fitted.params["omega"]) * rms**2
                alpha = float(fitted.params["alpha[1]"])
                beta = float(fitted.params["beta[1]"]) if q else 0.0
                # Keep arch's exact training initialization/backcast and bounds.
                h_train = np.asarray(fitted.conditional_volatility, dtype=float)**2 * rms**2
                # f_e(e) = f_scaled(e / rms) / rms: essential Jacobian.
                llf = float(fitted.loglikelihood) - n * np.log(rms)
                convergence_flag = int(fitted.convergence_flag)
                convergence_message = str(fitted.optimization_result.message)
            converged = convergence_flag == 0
            valid_params = variance_parameters_valid(omega, alpha, beta)
            valid_path = bool(np.isfinite(h_train).all() and (h_train > 0).all())
            eligible = bool(converged and valid_params and valid_path and np.isfinite(llf))
            persistence = alpha + beta
            near_boundary = bool(persistence >= NEAR_BOUNDARY)
            if near_boundary:
                fit_warnings.append("persistence >= 0.98; near the unit-persistence boundary")
            if not valid_params:
                fit_warnings.append("excluded: positivity or persistence < 1 - 1e-8 not satisfied")
            if not converged:
                fit_warnings.append("excluded: optimizer did not converge")
            if not valid_path:
                fit_warnings.append("excluded: invalid training variance path")
            row.update({
                "omega": omega, "alpha": alpha, "beta": beta, "persistence": persistence,
                "unconditional_variance": omega / (1 - persistence) if valid_params else np.nan,
                "loglikelihood": float(llf), "aic": float(-2 * llf + 2 * k),
                "bic": float(-2 * llf + k * np.log(n)),
                "converged": converged, "convergence_flag": convergence_flag,
                "convergence_message": convergence_message, "eligible": eligible,
                "status": "eligible" if eligible else "excluded",
                "near_boundary": near_boundary, "warning": "; ".join(fit_warnings),
                "positive_stable_parameters": valid_params,
            })
            if eligible:
                h_test = forecast_variance(
                    test, last_residual=float(train[-1]), last_variance=float(h_train[-1]),
                    omega=omega, alpha=alpha, beta=beta,
                )
                z_train, z_test = train / np.sqrt(h_train), test / np.sqrt(h_test)
                arrays[f"{model}_train_variance"] = h_train
                arrays[f"{model}_test_variance"] = h_test
                arrays[f"{model}_train_standardized_residuals"] = z_train
                arrays[f"{model}_test_standardized_residuals"] = z_test
                # Same proxy for ALL candidates; the mean forecast never changes.
                variance_errors = test**2 - h_test
                row["oos_variance_proxy_mse"] = float(np.mean(variance_errors**2)) if len(test) else np.nan
                row["oos_variance_proxy_mae"] = float(np.mean(np.abs(variance_errors))) if len(test) else np.nan
                for series, values in (("standardized_residuals", z_train),
                                       ("squared_standardized_residuals", z_train**2)):
                    for result in _ljung_box(values, lags).itertuples(index=False):
                        diagnostic_rows.append({
                            "scale": scale, "model": model, "series": series,
                            "test": "Ljung-Box", "lag": int(result.lag), "nobs": n,
                            "statistic": float(result.statistic), "pvalue": float(result.pvalue),
                            "reference_df": int(result.lag), "model_df": 0,
                            "reject_5pct": bool(result.pvalue < .05), "sample": "train_2024",
                            "reference_caveat": "approximate after fixed-mean and variance estimation; no df adjustment",
                        })
        except (ValueError, FloatingPointError, np.linalg.LinAlgError, RuntimeError) as exc:
            row.update(status="failed", eligible=False, warning=f"{type(exc).__name__}: {exc}")
        rows.append(row)

    grid = pd.DataFrame(rows)
    eligible = grid.loc[grid.eligible]
    if eligible.empty:
        raise RuntimeError("No eligible variance candidate, including the constant baseline")
    selected_index = eligible.bic.idxmin()
    grid.loc[selected_index, "selected_bic"] = True
    grid["delta_bic"] = grid.bic - grid.loc[selected_index, "bic"]
    # A finite delta is not an eligibility or selection endorsement.
    grid.loc[~grid.eligible, "delta_bic"] = np.nan
    selected = str(grid.loc[selected_index, "model"])
    diagnostics = pd.DataFrame(diagnostic_rows)
    summary = {
        "scale": scale, "nobs_train": n, "nobs_test": len(test),
        "selected_model": selected, "selected_model_label": MODEL_LABELS[selected],
        "selected_bic": float(grid.loc[selected_index, "bic"]),
        "eligible_models": eligible.model.tolist(), "diagnostic_lags": lags,
        "selection_sample": "train_2024", "fit_method": "sequential_not_joint_MLE",
        "mean_forecast_shared": True, "mean_parameters_refitted": False,
        "likelihood_comparison": "only variance candidates conditional on the same fixed mean; not ARMA likelihood",
        "bic_parameter_count": "variance parameters only; shared fixed mean not counted",
        "variance_unit": "input_residual_unit_squared",
        "proxy_mse_unit": "input_residual_unit_fourth_power",
        "evaluation_target": "same squared fixed-ARMA forecast innovation; noisy proxy, not observed variance",
        "boundary_policy": "continue observation index across sessions without overnight returns",
        "diagnostic_reference": "ordinary asymptotic ARCH-LM and Ljung-Box; approximate after sequential fitting",
        "stationarity_margin": STATIONARITY_MARGIN,
        "notes": [
            "Fitting, scaling, lag choices and BIC selection do not use test observations.",
            "OOS recursion uses the previous actual innovation, never the current/future one.",
            "No Diebold-Mariano test for these nested variance specifications.",
            "A better variance forecast is not a better point forecast of returns.",
            "A rejected standardized-residual Ljung-Box still indicates limitations of the mean equation.",
        ],
    }
    return grid, diagnostics, arrays, summary
