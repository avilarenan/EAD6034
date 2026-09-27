"""Two lightweight, explicitly out-of-core-methodology baselines.

Aula 4's own forecasting checklist names "ARMA, ETS, MLP, SVM, Deep Learning" as
example benchmark classes -- an MLP is a named Aula-4 benchmark, and a zero-shot
pretrained time-series foundation model sits in its "Deep Learning" bucket. Neither
is part of the graded ARIMA/GARCH methodology (see golden_rules.md #1); both are
reported separately and labeled as exploratory, time-budget-driven additions.

Fairness discipline (golden_rules.md #4): the classical models here select order
via in-sample BIC on the training partition, with no validation slice. The MLP,
which does need a validation split for hyperparameter selection, carves that slice
from the TAIL OF THE TRAINING PARTITION ONLY, then refits on the full training
partition (train+validation) before generating test predictions -- so it gets
the same amount of training signal as the BIC-selected models, not an advantage
or a disadvantage. Chronos runs zero-shot (no fitting at all), so there is no
validation-leakage question for it.
"""
from __future__ import annotations

import numpy as np

from .forecast_evaluation import _evaluation_origins


def _lag_features(y: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    """X[k] = y[k:k+window] (causal), target[k] = y[window+k]."""
    windows = np.lib.stride_tricks.sliding_window_view(y, window)
    return windows[:-1], y[window:]


def mlp_native_forecast(
    y: np.ndarray,
    train_n: int,
    window: int = 30,
    validation_fraction: float = 0.15,
    hidden_layer_candidates: tuple = ((8,), (16,), (32,)),
    alpha_candidates: tuple = (1e-4, 1e-3, 1e-2),
    random_state: int = 6034,
) -> tuple[np.ndarray, dict]:
    """One-step-ahead MLP forecast matrix for the native (horizon=1) evaluation.

    Returns a ``(len(y), 1)`` matrix, NaN for training rows and for the first
    ``window`` observations (mirrors forecast_fixed()'s row/NaN convention),
    plus a metadata dict (validation split sizes, the small hyperparameter
    grid tried, the selected combination and its validation MSE).

    Hyperparameters (hidden layer size, L2 alpha) are selected by MSE on a
    validation slice = the last ``validation_fraction`` of the training
    partition, chronologically -- never the test partition. The final model
    is then refit on the FULL training partition (fit+validation combined)
    with the selected hyperparameters before generating test predictions.
    """
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler

    y = np.asarray(y, dtype=float)
    if y.ndim != 1 or not np.isfinite(y).all():
        raise ValueError("y must be a finite one-dimensional sequence")
    if not (0 < window < train_n < len(y)):
        raise ValueError("Need 0 < window < train_n < len(y)")
    val_n = max(1, int(round(train_n * validation_fraction)))
    fit_n = train_n - val_n
    if fit_n <= window:
        raise ValueError("Training partition too short for this window/validation_fraction")

    X_all, target_all = _lag_features(y[:train_n], window)
    split = fit_n - window
    X_fit, target_fit = X_all[:split], target_all[:split]
    X_val, target_val = X_all[split:], target_all[split:]

    scaler = StandardScaler().fit(X_fit)
    trials, best = [], None
    for hidden in hidden_layer_candidates:
        for alpha in alpha_candidates:
            model = MLPRegressor(hidden_layer_sizes=hidden, activation="relu", solver="adam",
                                  alpha=alpha, max_iter=500, random_state=random_state,
                                  early_stopping=False)
            model.fit(scaler.transform(X_fit), target_fit)
            val_mse = float(np.mean((model.predict(scaler.transform(X_val)) - target_val) ** 2))
            trial = dict(hidden_layer_sizes=hidden, alpha=alpha, val_mse=val_mse)
            trials.append(trial)
            if best is None or val_mse < best["val_mse"]:
                best = trial

    # Refit on train+validation with the selected hyperparameters: this is what
    # makes the test-period comparison fair against ARIMA/GARCH, which use the
    # full training partition for their final BIC-selected parameters.
    final_scaler = StandardScaler().fit(X_all)
    final_model = MLPRegressor(hidden_layer_sizes=best["hidden_layer_sizes"], activation="relu",
                                solver="adam", alpha=best["alpha"], max_iter=500,
                                random_state=random_state, early_stopping=False)
    final_model.fit(final_scaler.transform(X_all), target_all)

    X_full, _ = _lag_features(y, window)
    predictions = final_model.predict(final_scaler.transform(X_full))
    matrix = np.full((len(y), 1), np.nan, dtype=float)
    matrix[window:, 0] = predictions
    matrix[:train_n, 0] = np.nan
    summary = dict(
        method="MLPRegressor_lagged_returns", window=window, validation_fraction=validation_fraction,
        fit_n=fit_n, val_n=val_n, hyperparameter_trials=trials,
        selected_hidden_layer_sizes=best["hidden_layer_sizes"], selected_alpha=best["alpha"],
        selected_validation_mse=best["val_mse"], refit_on_train_plus_validation=True,
        random_state=random_state,
    )
    return matrix, summary


def chronos_common_60min_forecast(
    y: np.ndarray,
    frame,
    scale: str,
    context_length: int = 512,
    batch_size: int = 64,
    model_name: str = "amazon/chronos-2",
    min_context: int = 20,
) -> tuple[np.ndarray, dict]:
    """Zero-shot Chronos-2 forecasts at the pipeline's own common_60min origins.

    No fitting at all (zero-shot), so there is no validation-leakage question.
    Bounded to the existing common_60min origins (forecast_evaluation's own
    _evaluation_origins), not every native 1-minute row, purely for CPU
    time-budget reasons -- an explicit, stated engineering choice, not a
    silent restriction of the evaluation.
    """
    import os
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from chronos.chronos2 import Chronos2Pipeline

    y = np.asarray(y, dtype=float)
    if y.ndim != 1 or not np.isfinite(y).all():
        raise ValueError("y must be a finite one-dimensional sequence")
    origins, horizon = _evaluation_origins(frame, scale, "common_60min")
    pipeline = Chronos2Pipeline.from_pretrained(model_name, device_map="cpu", dtype=torch.float32)

    contexts, valid_origins = [], []
    for origin in origins:
        start = max(0, origin - context_length)
        if origin - start < min_context:
            continue
        contexts.append(torch.tensor(y[start:origin], dtype=torch.float32))
        valid_origins.append(int(origin))

    matrix = np.full((len(y), horizon), np.nan, dtype=float)
    for batch_start in range(0, len(contexts), batch_size):
        batch = contexts[batch_start:batch_start + batch_size]
        _, means = pipeline.predict_quantiles(batch, prediction_length=horizon, quantile_levels=[0.5])
        for origin, mean in zip(valid_origins[batch_start:batch_start + batch_size], means):
            matrix[origin, :] = np.asarray(mean, dtype=float).reshape(-1)[:horizon]

    summary = dict(
        method="chronos2_zero_shot", model_name=model_name, context_length=context_length,
        n_origins_total=int(len(origins)), n_origins_scored=len(valid_origins), horizon=int(horizon),
        batch_size=batch_size, fitted=False,
    )
    return matrix, summary
