"""Cross-scale, common-horizon evaluation of conditional-variance forecasts.

Mirrors forecast_evaluation.py's common_60min design for the mean: the same
realized target (sum of squared returns over the next 60 minutes, at the
same non-overlapping origins already used for return forecasts) lets
variance forecasts from different base scales -- and from non-GARCH model
classes (MLP, a zero-shot foundation model), which are NOT nested within
the GARCH family -- be compared on equal footing and, unlike the GARCH
family's own nested hierarchy (see conditional_volatility.py), legitimately
Diebold-Mariano tested against a GARCH-family benchmark.

Private per-origin realized/predicted variance values are never published,
only aggregated metrics, mirroring forecast_evaluation.evaluate_scale()'s
own public/private split.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .forecast_evaluation import _evaluation_origins


def realized_variance_targets(frame: pd.DataFrame, scale: str):
    """(origins, horizon, realized_variance) at the common_60min origins.

    realized_variance = sum of squared realized returns over the horizon --
    a standard realized-variance proxy (Andersen-Bollerslev style) built
    from the same bars already used for the mean-forecast comparison.
    """
    y = frame.return_pct.to_numpy(float)
    origins, horizon = _evaluation_origins(frame, scale, "common_60min")
    realized = np.array([np.sum(y[o:o + horizon] ** 2) for o in origins], dtype=float)
    return origins, horizon, realized


def align_native_variance(train_n: int, total_len: int, test_variance: np.ndarray) -> np.ndarray:
    """Place a test-only one-step h_t sequence into a full-length, NaN-padded array."""
    full = np.full(total_len, np.nan, dtype=float)
    test_variance = np.asarray(test_variance, dtype=float)
    if train_n + len(test_variance) > total_len:
        raise ValueError("test_variance does not fit after train_n within total_len")
    full[train_n:train_n + len(test_variance)] = test_variance
    return full


def summed_prediction(full_h: np.ndarray, origins: np.ndarray, horizon: int) -> np.ndarray:
    """Sum a native one-step variance-forecast path over each origin's horizon."""
    return np.array([np.sum(full_h[o:o + horizon]) for o in origins], dtype=float)


def qlike(realized: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    """QLIKE loss: realized/predicted - log(realized/predicted) - 1 (Patton 2011).

    Standard robust loss for variance-forecast comparison; unlike MSE it is
    well-behaved for a strictly positive, heavy-tailed target and penalizes
    under- and over-prediction asymmetrically in the way the literature
    prefers for volatility forecasts. Requires predicted > 0.
    """
    ratio = realized / predicted
    return ratio - np.log(ratio) - 1


def evaluate_variance_common_horizon(
    frame: pd.DataFrame, scale: str, model_variance_paths: dict[str, np.ndarray],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Public metrics + private per-origin table for one scale's variance models.

    model_variance_paths: dict[name] -> full-length (len(frame),) array of
    one-step-ahead conditional-variance forecasts (NaN for training rows;
    see align_native_variance() to build these from a GARCH test_variance
    array, or a neural_baselines.*_variance_forecast() matrix column 0).
    """
    origins, horizon, realized = realized_variance_targets(frame, scale)
    private = pd.DataFrame({"scale": scale, "origin": origins, "horizon": horizon,
                           "realized_variance": realized})
    metric_rows = []
    for name, full_h in model_variance_paths.items():
        predicted = summed_prediction(np.asarray(full_h, dtype=float), origins, horizon)
        private[f"predicted_{name}"] = predicted
        # MSE/MAE only need a finite, positive prediction. QLIKE additionally
        # needs realized > 0 (ratio=realized/predicted appears inside a log);
        # a handful of exactly-flat realized 60-minute returns (a genuine,
        # non-negligible share at coarser scales) would otherwise silently
        # poison the mean with -inf/+inf. Excluded, not zero-padded.
        valid_mse = np.isfinite(predicted) & (predicted > 0) & np.isfinite(realized)
        valid_qlike = valid_mse & (realized > 0)
        error = realized[valid_mse] - predicted[valid_mse]
        metric_rows.append(dict(
            scale=scale, model=name, n=int(valid_mse.sum()),
            n_dropped_nonpositive_or_nonfinite=int((~valid_mse).sum()),
            mse=float(np.mean(error ** 2)), mae=float(np.mean(np.abs(error))),
            n_qlike=int(valid_qlike.sum()),
            n_dropped_zero_realized_for_qlike=int((valid_mse & ~valid_qlike).sum()),
            qlike=float(np.mean(qlike(realized[valid_qlike], predicted[valid_qlike]))),
        ))
    metrics = pd.DataFrame(metric_rows)
    if not metrics.empty and (metrics.model == "constant").any():
        base_mse = float(metrics.loc[metrics.model.eq("constant"), "mse"].iloc[0])
        base_qlike = float(metrics.loc[metrics.model.eq("constant"), "qlike"].iloc[0])
        metrics["mse_ratio_vs_constant"] = metrics.mse / base_mse if base_mse > 0 else np.nan
        metrics["qlike_ratio_vs_constant"] = metrics.qlike / base_qlike if base_qlike > 0 else np.nan
    return private, metrics
