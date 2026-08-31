from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew
from statsmodels.tsa.stattools import acf, pacf


def _within_session_acf(
    groups: list[np.ndarray], max_lag: int
) -> tuple[np.ndarray, np.ndarray]:
    """FAC viesada no estilo Box-Jenkins, usando apenas pares intrassessão."""

    concatenated = np.concatenate(groups)
    mean = float(np.mean(concatenated))
    denominator = float(np.sum((concatenated - mean) ** 2))
    values = [1.0]
    pair_counts = [len(concatenated)]
    for lag in range(1, max_lag + 1):
        numerator = 0.0
        pairs = 0
        for group in groups:
            if len(group) <= lag:
                continue
            numerator += float(np.sum((group[lag:] - mean) * (group[:-lag] - mean)))
            pairs += len(group) - lag
        values.append(numerator / denominator)
        pair_counts.append(pairs)
    return np.asarray(values), np.asarray(pair_counts, dtype=int)


def chronological_split(
    bars: pd.DataFrame, train_end_date: str, test_start_date: str
) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    returns = bars.dropna(subset=["return_pct"]).copy()
    train = returns.loc[returns["date"] <= train_end_date].copy()
    test = returns.loc[returns["date"] >= test_start_date].copy()
    if train.empty or test.empty:
        raise ValueError("O corte cronologico produziu treino ou teste vazio.")
    train["sample"] = "in_sample"
    test["sample"] = "out_of_sample"
    return train, test, str(train["date"].max()), str(test["date"].min())


def descriptive_statistics(samples: dict[str, pd.Series]) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for label, values in samples.items():
        x = pd.Series(values).dropna().astype(float).to_numpy()
        rows.append(
            {
                "sample": label,
                "n": int(len(x)),
                "mean": float(np.mean(x)),
                "std": float(np.std(x, ddof=1)),
                "min": float(np.min(x)),
                "q01": float(np.quantile(x, 0.01)),
                "q05": float(np.quantile(x, 0.05)),
                "median": float(np.median(x)),
                "q95": float(np.quantile(x, 0.95)),
                "q99": float(np.quantile(x, 0.99)),
                "max": float(np.max(x)),
                "skewness": float(skew(x, bias=False)),
                "excess_kurtosis": float(kurtosis(x, fisher=True, bias=False)),
                "zero_share": float(np.mean(x == 0.0)),
            }
        )
    return pd.DataFrame(rows)


def correlogram(
    frame: pd.DataFrame,
    max_lag: int,
    value_column: str = "return_pct",
    session_column: str = "date",
) -> pd.DataFrame:
    """FAC/FACP principal sem criar defasagens artificiais entre pregoes.

    Tambem calcula a versao convencional por concatenacao como verificacao de
    sensibilidade. A FACP intrapregao e o ultimo coeficiente de uma regressao
    AR(k) pooled, com intercepto e somente linhas inteiramente no mesmo dia.
    """

    clean = frame.dropna(subset=[value_column]).copy()
    groups = [
        group[value_column].astype(float).to_numpy()
        for _, group in clean.groupby(session_column, sort=True, observed=True)
    ]
    x = np.concatenate(groups)
    if len(x) <= max_lag + 1:
        raise ValueError("A amostra e curta demais para o numero de defasagens.")
    conventional_acf = acf(x, nlags=max_lag, fft=True)
    conventional_pacf = pacf(x, nlags=max_lag, method="ywmle")

    acf_values, pair_counts_array = _within_session_acf(groups, max_lag)
    pacf_values = [1.0]
    pair_counts = pair_counts_array.tolist()
    regression_counts = [len(x)]

    for lag in range(1, max_lag + 1):
        y_parts: list[np.ndarray] = []
        x_parts: list[np.ndarray] = []
        for values in groups:
            if len(values) <= lag:
                continue
            y_parts.append(values[lag:])
            x_parts.append(
                np.column_stack([values[lag - j : len(values) - j] for j in range(1, lag + 1)])
            )
        y = np.concatenate(y_parts)
        design = np.vstack(x_parts)
        design = np.column_stack([np.ones(len(design)), design])
        coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
        pacf_values.append(float(coefficients[-1]))
        regression_counts.append(len(y))

    acf_ci = 1.96 / np.sqrt(np.asarray(pair_counts, dtype=float))
    pacf_ci = 1.96 / np.sqrt(np.asarray(regression_counts, dtype=float))
    table = pd.DataFrame(
        {
            "lag": np.arange(max_lag + 1, dtype=int),
            "minutes": np.arange(max_lag + 1, dtype=int) * 5,
            "acf": acf_values,
            "pacf": pacf_values,
            "acf_ci_95": acf_ci,
            "pacf_ci_95": pacf_ci,
            "acf_n_pairs": pair_counts,
            "pacf_nobs": regression_counts,
            "acf_conventional": conventional_acf,
            "pacf_conventional": conventional_pacf,
        }
    )
    table["acf_significant"] = table["acf"].abs() > table["acf_ci_95"]
    table["pacf_significant"] = table["pacf"].abs() > table["pacf_ci_95"]
    table.loc[table["lag"] == 0, ["acf_significant", "pacf_significant"]] = False
    return table


def daily_summary(bars: pd.DataFrame) -> pd.DataFrame:
    frame = bars.copy()
    frame["squared_return"] = frame["return_pct"].pow(2)
    result = frame.groupby("date", as_index=False, observed=True).agg(
        timestamp=("timestamp", "max"),
        symbol=("symbol", "last"),
        close=("close", "last"),
        mean_return=("return_pct", "mean"),
        standard_deviation=("return_pct", "std"),
        realized_volatility=("squared_return", lambda x: float(np.sqrt(x.sum()))),
        volume=("volume", "sum"),
        observations=("return_pct", "count"),
    )
    return result


def intraday_profile(bars: pd.DataFrame) -> pd.DataFrame:
    frame = bars.dropna(subset=["return_pct"]).copy()
    frame["clock"] = frame["timestamp"].dt.strftime("%H:%M")
    frame["absolute_return"] = frame["return_pct"].abs()
    return frame.groupby("clock", as_index=False, observed=True).agg(
        mean_return=("return_pct", "mean"),
        median_absolute_return=("absolute_return", "median"),
        mean_absolute_return=("absolute_return", "mean"),
        mean_volume=("volume", "mean"),
        observations=("return_pct", "count"),
    )


def dependence_in_magnitude(
    frame: pd.DataFrame,
    max_lag: int = 30,
    value_column: str = "return_pct",
    session_column: str = "date",
) -> pd.DataFrame:
    clean = frame.dropna(subset=[value_column]).copy()
    groups = [
        group[value_column].astype(float).to_numpy()
        for _, group in clean.groupby(session_column, sort=True, observed=True)
    ]
    absolute, pair_counts = _within_session_acf(
        [np.abs(values) for values in groups], max_lag
    )
    squared, _ = _within_session_acf([values**2 for values in groups], max_lag)
    return pd.DataFrame(
        {
            "lag": np.arange(max_lag + 1, dtype=int),
            "minutes": np.arange(max_lag + 1, dtype=int) * 5,
            "acf_absolute_returns": absolute,
            "acf_squared_returns": squared,
            "n_pairs": pair_counts,
        }
    )
