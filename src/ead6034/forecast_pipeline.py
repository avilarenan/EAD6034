"""Cumulative 21 September delivery: annual inference and genuine 2025 forecasts."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA

from .annual_models import annual_stationarity, correlogram, diagnose_mean, fit_annual_grid
from .conditional_volatility import fit_volatility
from .forecast_evaluation import evaluate_scale, forecast_fixed
from .trading_time_data import SCALES, build_trading_time_data

MODULE_DIR = Path(__file__).resolve().parent
SCALE_MINUTES = {"1min": 1, "5min": 5, "15min": 15, "30min": 30, "60min": 60}
COMBINED_TABLES = (
    "stationarity", "arma_grid", "selected_models", "mean_diagnostics", "return_acf_pacf",
    "residual_acf_pacf", "squared_residual_acf", "accuracy", "diebold_mariano",
    "variance_models", "variance_diagnostics", "descriptive", "time_band_description",
    "monthly_description", "lag_boundary_description", "forecast_equivalence",
)


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    return value


def write_json(path, value):
    Path(path).write_text(json.dumps(json_safe(value), ensure_ascii=False, indent=2,
                                   allow_nan=False) + "\n", encoding="utf-8")


def source_digest(names):
    digest = hashlib.sha256()
    for name in sorted(names):
        digest.update(name.encode())
        digest.update((MODULE_DIR / name).read_bytes())
    return digest.hexdigest()


def array_digest(y):
    return hashlib.sha256(np.asarray(y, dtype="<f8").tobytes()).hexdigest()


def numerical_versions():
    return {name: importlib.metadata.version(name)
            for name in ("numpy", "pandas", "scipy", "statsmodels", "arch")}


def _read_model_cache(path, y, model_key):
    if not path.exists():
        return None
    cached = json.loads(path.read_text())
    if cached.get("key") != model_key:
        return None
    results = {}
    for name, spec in cached["models"].items():
        results[name] = ARIMA(y, order=(spec["p"], 0, spec["q"]), trend="c",
                              enforce_stationarity=True, enforce_invertibility=True).filter(
                                  np.asarray(spec["params"], float), cov_type="none")
    return results


def _summary(values):
    y = np.asarray(values, float)
    return dict(n=len(y), mean_pct=float(y.mean()), std_pct=float(y.std(ddof=1)),
                skewness=float(stats.skew(y)), excess_kurtosis=float(stats.kurtosis(y)),
                zero_share=float(np.mean(y == 0)))


def describe_training(frame, scale):
    train = frame.loc[frame["sample"].eq("train")].copy()
    overall = pd.DataFrame([dict(scale=scale, **_summary(train.return_pct),
                                 start=train.date.min(), end=train.date.max(),
                                 trading_days=train.date.nunique())])
    by_band = pd.DataFrame([dict(scale=scale, time_band=band, **_summary(g.return_pct))
                            for band, g in train.groupby("time_band", observed=True)])
    train["month"] = train.date.str[:7]
    monthly = pd.DataFrame([dict(scale=scale, month=month, **_summary(g.return_pct))
                           for month, g in train.groupby("month", observed=True)])
    rows = []
    y = train.return_pct.to_numpy(float)
    boundaries = train.date.to_numpy()[1:] != train.date.to_numpy()[:-1]
    # Descriptive pair correlations, NOT a modified significance test.
    for name, mask in (("all_pairs", np.ones(len(y)-1, dtype=bool)),
                       ("within_session", ~boundaries), ("across_sessions", boundaries)):
        a, b = y[:-1][mask], y[1:][mask]
        correlation = float(np.corrcoef(a, b)[0, 1]) if len(a) >= 10 and a.std() > 0 and b.std() > 0 else np.nan
        rows.append(dict(scale=scale, pair_type=name, n_pairs=len(a),
                         pair_correlation=correlation, method="descriptive_Pearson_no_p_value"))
    return overall, by_band, monthly, pd.DataFrame(rows)


def process_scale(scale, output, max_order=5, resume=True):
    out, tables = Path(output), Path(output) / "tables"
    private = out / "private"
    frame = pd.read_parquet(private / f"frames_{scale}.parquet")
    y = frame.return_pct.to_numpy(float)
    n_train = int(frame["sample"].eq("train").sum())
    train = y[:n_train]
    if not frame.loc[:n_train-1, "date"].str.startswith("2024").all():
        raise AssertionError("Training prefix must contain only 2024")
    code_hash = source_digest(["annual_models.py", "forecast_evaluation.py",
                               "conditional_volatility.py", "forecast_pipeline.py"])
    frame_hash = hashlib.sha256(pd.util.hash_pandas_object(
        frame[["timestamp", "bar_start", "return_pct", "sample", "time_band", "gap_group"]], index=False
    ).to_numpy().tobytes()).hexdigest()
    versions_key = json.dumps(numerical_versions(), sort_keys=True)
    run_key = hashlib.sha256(f"{code_hash}:{frame_hash}:{max_order}:{versions_key}".encode()).hexdigest()
    checkpoint = private / f"completed_{scale}.json"
    if resume and checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        private_files = [private / f"{name}_{scale}.{suffix}" for name, suffix in
                         (("predictions", "parquet"), ("variance_paths", "npz"), ("mean_innovations", "npz"))]
        if (state.get("key") == run_key
                and all((tables / f"{name}_{scale}.csv").exists() for name in COMBINED_TABLES)
                and all(path.exists() for path in private_files)):
            print(f"{scale}: verified identical-input checkpoint reused", flush=True)
            return state["summary"]

    tested = annual_stationarity(train, scale)
    tested.to_csv(tables / f"stationarity_{scale}.csv", index=False)
    print(f"{scale}: annual stationarity complete, n={n_train}; fitting ARMA grid", flush=True)
    model_key = hashlib.sha256((source_digest(["annual_models.py"]) + array_digest(train)
                               + str(max_order) + versions_key).encode()).hexdigest()
    model_cache = private / f"models_{scale}.json"
    fitted = _read_model_cache(model_cache, train, model_key) if resume else None
    selection_path = tables / f"selected_models_{scale}.csv"
    grid_path = tables / f"arma_grid_{scale}.csv"
    if fitted is not None and selection_path.exists() and grid_path.exists():
        selected, grid = pd.read_csv(selection_path), pd.read_csv(grid_path)
        print(f"{scale}: verified training-only model cache reused", flush=True)
    else:
        def progress(p, q, row):
            print(f"  {scale} ARMA({p},{q}) {row['status']} BIC={row.get('bic', float('nan')):.4f}", flush=True)
        grid, fitted, selected = fit_annual_grid(train, max_order=max_order, progress=progress)
        grid["scale"], selected["scale"] = scale, scale
        grid.to_csv(grid_path, index=False)
        selected.to_csv(selection_path, index=False)
        write_json(model_cache, dict(key=model_key, train_sha256=array_digest(train),
                                     models={name: dict(p=result.model.order[0], q=result.model.order[2],
                                                       params=np.asarray(result.params).tolist())
                                             for name, result in fitted.items()}))
    if set(fitted) != {"ARMA_BIC", "AR_BIC", "MA_BIC"}:
        raise RuntimeError(f"{scale}: a required comparator has no eligible model; inspect the published grid")
    max_lag = 60 if scale == "1min" else (20 if scale == "1d" else 24)
    return_corr = correlogram(train, scale, maxlag=max_lag)
    residual_parts, squared_parts, diagnostics = [], [], []
    for name, result in fitted.items():
        diagnostic = diagnose_mean(result, scale)
        diagnostic["model"] = name
        diagnostics.append(diagnostic)
        z = np.asarray(result.filter_results.standardized_forecasts_error[0], float)
        corr, square = correlogram(z, scale, maxlag=max_lag), correlogram(z*z, scale, maxlag=max_lag)
        corr["model"], square["model"] = name, name
        residual_parts.append(corr)
        squared_parts.append(square)
    horizon = 1 if scale == "1d" else 60 // SCALE_MINUTES[scale]
    prediction_map = {name: forecast_fixed(result, y, n_train, horizon) for name, result in fitted.items()}
    predictions, accuracy, dm = evaluate_scale(frame, prediction_map, scale)
    predictions.to_parquet(private / f"predictions_{scale}.parquet", index=False)
    # Same innovations for each conditional-variance candidate, no smoothing.
    train_residuals = np.asarray(fitted["ARMA_BIC"].resid, float)
    test_residuals = y[n_train:] - prediction_map["ARMA_BIC"][n_train:, 0]
    variance_grid, variance_diagnostics, variance_arrays, variance_summary = fit_volatility(
        train_residuals, test_residuals, scale, diagnostic_lags=sorted(set([10, 20, max_lag])))
    np.savez_compressed(private / f"variance_paths_{scale}.npz", **variance_arrays)
    np.savez_compressed(private / f"mean_innovations_{scale}.npz",
                        train=train_residuals, test=test_residuals)
    overall, bands, monthly, boundaries = describe_training(frame, scale)
    equivalence = []
    for evaluation, part in predictions.groupby("evaluation", observed=True):
        pivot = part.pivot(index=["target_start", "target_end"], columns="model", values="prediction")
        models = list(pivot.columns)
        for i, a in enumerate(models):
            for b in models[i+1:]:
                difference = (pivot[a] - pivot[b]).to_numpy(float)
                equivalence.append(dict(scale=scale, evaluation=evaluation, model_a=a, model_b=b,
                                        max_abs_difference=float(np.max(np.abs(difference))),
                                        equal_within_1e_10=bool(np.allclose(pivot[a], pivot[b], atol=1e-10, rtol=0))))
    exports = dict(stationarity=tested, arma_grid=grid, selected_models=selected,
                   mean_diagnostics=pd.concat(diagnostics, ignore_index=True), return_acf_pacf=return_corr,
                   residual_acf_pacf=pd.concat(residual_parts, ignore_index=True),
                   squared_residual_acf=pd.concat(squared_parts, ignore_index=True),
                   accuracy=accuracy, diebold_mariano=dm, variance_models=variance_grid,
                   variance_diagnostics=variance_diagnostics, descriptive=overall,
                   time_band_description=bands, monthly_description=monthly,
                   lag_boundary_description=boundaries, forecast_equivalence=pd.DataFrame(equivalence))
    for name, table in exports.items():
        table.to_csv(tables / f"{name}_{scale}.csv", index=False)
    selected_main = selected.loc[selected.model.eq("ARMA_BIC")].iloc[0]
    summary = dict(scale=scale, n_train=n_train, n_test=len(y)-n_train,
                   train_sha256=array_digest(train), full_sequence_sha256=array_digest(y),
                   model=dict(p=int(selected_main.p), q=int(selected_main.q), bic=float(selected_main.bic)),
                   variance=variance_summary,
                   eligible_arma_candidates=int(grid.status.eq("eligible").sum()),
                   total_arma_candidates=len(grid), fitted_parameters_use_holdout=False)
    write_json(checkpoint, dict(key=run_key, summary=summary))
    print(f"{scale}: complete, ARMA({summary['model']['p']},{summary['model']['q']}), variance={variance_summary['selected_model']}", flush=True)
    return summary


def verify_common_targets(predictions_by_scale):
    """Prove alignment AFTER each scale's common finite-prediction mask."""
    baseline, rows = None, []
    for scale in SCALE_MINUTES:
        predictions = predictions_by_scale[scale]
        common = predictions.loc[predictions.evaluation.eq("common_60min")]
        # All model rows share a target, but require no duplicate model-target.
        if common.duplicated(["model", "target_start", "target_end"]).any():
            raise AssertionError(f"{scale}: duplicate common target")
        part = common.loc[common.model.eq("ZERO"), ["target_start", "target_end", "actual"]].sort_values(
            ["target_start", "target_end"]).reset_index(drop=True)
        if part.empty:
            raise AssertionError(f"{scale}: no common ZERO targets")
        for model, group in common.groupby("model", observed=True):
            candidate = group[["target_start", "target_end", "actual"]].sort_values(
                ["target_start", "target_end"]).reset_index(drop=True)
            if (not candidate[["target_start", "target_end"]].equals(part[["target_start", "target_end"]])
                    or not np.allclose(candidate.actual, part.actual, rtol=0, atol=1e-10)):
                raise AssertionError(f"{scale}/{model}: model-specific common targets differ")
        if baseline is None:
            baseline = part
        same_origins = part[["target_start", "target_end"]].equals(baseline[["target_start", "target_end"]])
        if not same_origins or len(part) != len(baseline):
            raise AssertionError(f"{scale}: common targets have different origins/endpoints")
        max_error = float(np.max(np.abs(part.actual.to_numpy() - baseline.actual.to_numpy())))
        if not np.allclose(part.actual, baseline.actual, rtol=0, atol=1e-10):
            raise AssertionError(f"{scale}: common targets contain different realized returns")
        rows.append(dict(scale=scale, targets=len(part), identical_origins=True,
                         max_target_reconciliation_error_pct=max_error,
                         tolerance_pct=1e-10, sample="2025", checked_after_finite_prediction_mask=True))
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="results/entrega_21_09")
    parser.add_argument("--max-order", type=int, choices=range(1, 6), default=5)
    parser.add_argument("--workers", type=int, choices=range(1, 7), default=3)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--skip-report", action="store_true")
    parser.add_argument("--code-ref", default="main")
    args = parser.parse_args(argv)
    out = Path(args.output).resolve()
    tables, private = out / "tables", out / "private"
    tables.mkdir(parents=True, exist_ok=True)
    private.mkdir(exist_ok=True)
    frames, coverage, daily_context, metadata = build_trading_time_data(args.input)
    for scale, frame in frames.items():
        frame.to_parquet(private / f"frames_{scale}.parquet", index=False)
    daily_context.to_parquet(private / "daily_context.parquet", index=False)
    coverage.to_csv(tables / "coverage.csv", index=False)
    # Coverage-only profile summaries may not reveal singleton return values.
    profile = pd.DataFrame(metadata.pop("minute_profile_2024"))
    sensitive = profile.returns_n.lt(10)
    profile.loc[sensitive, ["mean_return_pct", "std_return_pct", "mean_abs_return_pct"]] = np.nan
    profile.to_csv(tables / "minute_of_day_profile_2024.csv", index=False)
    session_hours = daily_context.groupby(
        ["sample", "source_first_clock", "source_last_clock"], observed=True).size().rename("days").reset_index()
    session_hours.to_csv(tables / "observed_source_hours.csv", index=False)
    gap_summary = daily_context.loc[daily_context.included].groupby(
        ["sample", "gap_group"], observed=True).agg(
            days=("date", "size"), gaps_available=("observed_session_gap_pct", "count"),
            gap_mean_pct=("observed_session_gap_pct", "mean"),
            gap_std_pct=("observed_session_gap_pct", "std")).reset_index()
    gap_summary.loc[gap_summary.gaps_available.lt(10), ["gap_mean_pct", "gap_std_pct"]] = np.nan
    gap_summary.to_csv(tables / "observed_gap_summary.csv", index=False)
    sequence_audit = []
    for scale, frame in frames.items():
        for sample, g in frame.groupby("sample", observed=True):
            sequence_audit.append(dict(scale=scale, sample=sample, n=len(g), days=g.date.nunique(),
                                       start=g.date.min(), end=g.date.max(),
                                       cross_session_lag1_count=int(g.cross_session_lag1.sum()),
                                       roll_transitions=int(g.roll_transition.sum()),
                                       excluded_source_days_between=int(g.excluded_source_days_between.sum()),
                                       unobserved_weekdays_between=int(g.source_missing_days_between.sum())))
    pd.DataFrame(sequence_audit).to_csv(tables / "sequence_audit.csv", index=False)
    write_json(private / "data_metadata.json", metadata)
    print(f"Data: {metadata['sample_day_counts']}; annual chronological sequences ready", flush=True)
    # Large arrays are read per worker from the verified private caches.
    del frames, daily_context
    summaries = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(process_scale, scale, str(out), args.max_order, not args.no_resume): scale
                   for scale in SCALES}
        for future in as_completed(pending):
            scale = pending[future]
            summaries[scale] = future.result()
    for name in COMBINED_TABLES:
        combined = pd.concat([pd.read_csv(tables / f"{name}_{scale}.csv") for scale in SCALES], ignore_index=True)
        combined.to_csv(tables / f"{name}.csv", index=False)
    predictions = {scale: pd.read_parquet(private / f"predictions_{scale}.parquet") for scale in SCALE_MINUTES}
    alignment = verify_common_targets(predictions)
    alignment.to_csv(tables / "common_target_alignment.csv", index=False)
    versions = {name: importlib.metadata.version(name) for name in (
        "numpy", "pandas", "scipy", "statsmodels", "arch", "pyarrow", "matplotlib", "reportlab")}
    metadata.update(created_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                    versions=versions, max_order=args.max_order, code_ref=args.code_ref,
                    input_source=str(Path(args.input).name), scales=[summaries[s] for s in SCALES],
                    evaluation_uses_2025=True, estimation_or_selection_uses_2025=False,
                    common_targets_verified=True,
                    course_only=True, mean_order_selection="BIC within each candidate family on 2024",
                    approved_protocol="docs/PROTOCOL_21_09.md",
                    code_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in MODULE_DIR.glob("*.py")},
                    sources={"course": "Aulas 3,4,5,6 supplied by user",
                             "market_hours": "docs/market_hours_2024_2025.md"})
    write_json(out / "analysis_summary.json", metadata)
    if not args.skip_report:
        from .forecast_report import write_report
        write_report(out, code_ref=args.code_ref)
    print(f"Completed analysis: {out}", flush=True)
    return metadata


if __name__ == "__main__":
    main()
