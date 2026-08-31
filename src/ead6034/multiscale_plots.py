from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .multiscale import INTRADAY_SCALES, scale_label
from .plots import BLUE, GOLD, GRAY, NAVY, RED, TEAL, set_style


PALETTE = ["#1F5FAE", "#008C95", "#7A5AF8", "#D89B2B", "#C83E4D", "#66788A"]
SCALE_ORDER = [key for key, _, _ in INTRADAY_SCALES] + ["1d"]


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def _ordered(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["scale"] = pd.Categorical(result["scale"], SCALE_ORDER, ordered=True)
    return result.sort_values("scale")


def plot_multiscale_descriptives(stats: pd.DataFrame, output_path: Path) -> Path:
    set_style()
    data = _ordered(stats)
    labels = [scale_label(str(value)) for value in data["scale"].astype(str)]
    colors = PALETTE[: len(data)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 8.1), constrained_layout=True)
    ax_std, ax_zero, ax_kurtosis, ax_n = axes.flat

    horizons = data["equivalent_minutes"].astype(float).to_numpy()
    standard_deviation = data["std"].astype(float).to_numpy()
    diffusion = standard_deviation[0] * np.sqrt(horizons / horizons[0])
    ax_std.plot(
        horizons,
        standard_deviation,
        color=BLUE,
        marker="o",
        linewidth=2.0,
        label="observado",
    )
    ax_std.plot(
        horizons,
        diffusion,
        color=GRAY,
        linestyle="--",
        linewidth=1.4,
        label=r"referência $\sigma_{1m}\sqrt{\Delta}$",
    )
    for x, y, label in zip(horizons, standard_deviation, labels):
        ax_std.annotate(label, (x, y), xytext=(3, 5), textcoords="offset points", fontsize=8)
    ax_std.set_xscale("log")
    ax_std.set_yscale("log")
    ax_std.set_title("Dispersão cresce aproximadamente com a raiz da escala", loc="left")
    ax_std.set_xlabel("Duração da barra ou sessão (minutos, escala log)")
    ax_std.set_ylabel("Desvio-padrão do retorno (%)")
    ax_std.legend(frameon=False, fontsize=8.5)

    zero_values = 100.0 * data["zero_share"].astype(float).to_numpy()
    bars = ax_zero.bar(labels, zero_values, color=colors)
    ax_zero.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
    ax_zero.set_title("Retornos exatamente zero diminuem com a agregação", loc="left")
    ax_zero.set_ylabel("Proporção (%)")
    ax_zero.tick_params(axis="x", rotation=25)

    kurtosis = data["excess_kurtosis"].astype(float).to_numpy()
    bars = ax_kurtosis.bar(labels, kurtosis, color=colors)
    ax_kurtosis.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
    ax_kurtosis.axhline(0.0, color=NAVY, linewidth=0.8)
    ax_kurtosis.set_title("Caudas pesadas se atenuam nas escalas mais grossas", loc="left")
    ax_kurtosis.set_ylabel("Excesso de curtose")
    ax_kurtosis.tick_params(axis="x", rotation=25)

    observations = data["n"].astype(int).to_numpy()
    bars = ax_n.bar(labels, observations, color=colors)
    ax_n.bar_label(
        bars,
        labels=[f"{value:,}".replace(",", ".") for value in observations],
        padding=2,
        fontsize=8,
    )
    ax_n.set_yscale("log")
    ax_n.set_title("O tamanho amostral cai fortemente com a escala", loc="left")
    ax_n.set_ylabel("Retornos no treino (escala log)")
    ax_n.tick_params(axis="x", rotation=25)

    fig.suptitle(
        "WIN em 2024 - estatísticas descritivas por escala",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    fig.text(
        0.5,
        -0.018,
        "O retorno diário é open-to-close na janela comum de 09:05 a 18:05. "
        "Variância, zeros e curtose não medem previsibilidade por si sós.",
        ha="center",
        color=GRAY,
        fontsize=9,
    )
    return _save(fig, output_path)


def plot_multiscale_correlograms(
    correlations: pd.DataFrame,
    scale_summary: pd.DataFrame,
    output_path: Path,
    comparison_horizon_minutes: int,
) -> Path:
    set_style()
    intraday_keys = [key for key, _, _ in INTRADAY_SCALES]
    comparable = correlations.loc[
        correlations["scale"].isin(intraday_keys)
        & (correlations["lag"] > 0)
        & (correlations["separation_value"] <= comparison_horizon_minutes)
    ].copy()
    summary = _ordered(scale_summary.loc[scale_summary["scale"] != "1d"])
    comparison_values = summary["acf_at_common_horizon"].astype(float).to_numpy()
    comparison_errors = summary["acf_ci_at_common_horizon"].astype(float).to_numpy()
    bound = float(
        comparable[["acf", "pacf", "acf_ci_95", "pacf_ci_95"]]
        .abs()
        .to_numpy()
        .max()
    )
    bound = max(bound, float(np.max(np.abs(comparison_values) + comparison_errors)))
    y_limit = max(0.035, 1.18 * bound)
    x_ticks = np.linspace(0, comparison_horizon_minutes, 5)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8.2), sharey=True, constrained_layout=True)
    for ax, (key, label, _) in zip(axes.flat[:5], INTRADAY_SCALES):
        data = comparable.loc[comparable["scale"] == key]
        x = data["separation_value"].astype(float)
        ax.plot(x, data["acf"], color=BLUE, marker="o", markersize=3, label="FAC")
        ax.plot(x, data["pacf"], color=TEAL, marker="s", markersize=2.5, label="FACP")
        ax.plot(x, data["acf_ci_95"], color=GRAY, linestyle="--", linewidth=0.8)
        ax.plot(x, -data["acf_ci_95"], color=GRAY, linestyle="--", linewidth=0.8)
        ax.axhline(0.0, color=NAVY, linewidth=0.8)
        ax.set_title(label, loc="left")
        ax.set_xlim(0, comparison_horizon_minutes * 1.03)
        ax.set_ylim(-y_limit, y_limit)
        ax.set_xticks(x_ticks)
        ax.set_xlabel("Separação temporal (minutos)")
        ax.set_ylabel("Correlação")
    axes.flat[0].legend(frameon=False, fontsize=8.5, ncol=2)

    ax_compare = axes.flat[5]
    labels = [scale_label(str(value)) for value in summary["scale"].astype(str)]
    values = comparison_values
    errors = comparison_errors
    positions = np.arange(len(summary))
    ax_compare.bar(positions, values, color=PALETTE[:5], width=0.7)
    ax_compare.errorbar(
        positions,
        values,
        yerr=errors,
        fmt="none",
        ecolor=NAVY,
        elinewidth=1,
        capsize=3,
    )
    ax_compare.axhline(0.0, color=NAVY, linewidth=0.8)
    ax_compare.set_xticks(positions)
    ax_compare.set_xticklabels(labels, rotation=25)
    ax_compare.set_ylim(-y_limit, y_limit)
    ax_compare.set_title(
        f"FAC na separação comum de {comparison_horizon_minutes} minutos",
        loc="left",
    )
    ax_compare.set_ylabel("FAC e banda pontual de 95%")

    fig.suptitle(
        "FAC e FACP intrapregão - comparação em tempo físico",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    fig.text(
        0.5,
        -0.018,
        "As bandas são referências pontuais sob ruído branco e variam com N. "
        "Escala da barra, lag e horizonte de previsão são conceitos distintos.",
        ha="center",
        color=GRAY,
        fontsize=9,
    )
    return _save(fig, output_path)


def plot_multiscale_dependence_and_daily(
    magnitude: pd.DataFrame,
    daily_train: pd.DataFrame,
    daily_corr: pd.DataFrame,
    output_path: Path,
    comparison_horizon_minutes: int,
) -> Path:
    set_style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 8.2), constrained_layout=True)
    ax_magnitude, ax_adjacent, ax_daily, ax_daily_corr = axes.flat

    for color, (key, label, _) in zip(PALETTE, INTRADAY_SCALES):
        data = magnitude.loc[
            (magnitude["scale"] == key)
            & (magnitude["lag"] > 0)
            & (magnitude["separation_value"] <= comparison_horizon_minutes)
        ]
        ax_magnitude.plot(
            data["separation_value"],
            data["acf_absolute_returns"],
            color=color,
            linewidth=1.5,
            marker="o",
            markersize=2.7,
            label=label,
        )
    ax_magnitude.axhline(0.0, color=NAVY, linewidth=0.8)
    ax_magnitude.set_title("Dependência em |r| permanece positiva", loc="left")
    ax_magnitude.set_xlabel("Separação temporal (minutos)")
    ax_magnitude.set_ylabel("FAC de |r|")
    ax_magnitude.legend(frameon=False, fontsize=8, ncol=2)

    lag_one = magnitude.loc[magnitude["lag"] == 1].copy()
    lag_one = _ordered(lag_one)
    labels = [scale_label(str(value)) for value in lag_one["scale"].astype(str)]
    values = lag_one["acf_absolute_returns"].astype(float).to_numpy()
    bars = ax_adjacent.bar(labels, values, color=PALETTE[: len(lag_one)])
    ax_adjacent.bar_label(bars, fmt="%.3f", padding=2, fontsize=8)
    ax_adjacent.set_title("FAC de |r| entre barras adjacentes", loc="left")
    ax_adjacent.set_ylabel("Autocorrelação")
    ax_adjacent.tick_params(axis="x", rotation=25)

    dates = pd.to_datetime(daily_train["date"])
    ax_daily.plot(dates, daily_train["return_pct"], color=TEAL, linewidth=0.8)
    ax_daily.axhline(0.0, color=NAVY, linewidth=0.8)
    ax_daily.set_title("Retorno diário open-to-close", loc="left")
    ax_daily.set_ylabel("Retorno (%)")
    ax_daily.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_daily.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
    ax_daily.tick_params(axis="x", rotation=25)

    daily_data = daily_corr.loc[daily_corr["lag"] > 0]
    ax_daily_corr.plot(
        daily_data["lag"], daily_data["acf"], color=BLUE, marker="o", markersize=3, label="FAC"
    )
    ax_daily_corr.plot(
        daily_data["lag"], daily_data["pacf"], color=TEAL, marker="s", markersize=2.7, label="FACP"
    )
    ax_daily_corr.plot(
        daily_data["lag"], daily_data["acf_ci_95"], color=GRAY, linestyle="--", linewidth=0.8
    )
    ax_daily_corr.plot(
        daily_data["lag"], -daily_data["acf_ci_95"], color=GRAY, linestyle="--", linewidth=0.8
    )
    ax_daily_corr.axhline(0.0, color=NAVY, linewidth=0.8)
    ax_daily_corr.set_title("Diário: FAC/FACP em pregões", loc="left")
    ax_daily_corr.set_xlabel("Lag (pregões)")
    ax_daily_corr.set_ylabel("Correlação")
    ax_daily_corr.legend(frameon=False, fontsize=8.5, ncol=2)

    fig.suptitle(
        "Dependência na magnitude e diagnóstico diário",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    fig.text(
        0.5,
        -0.018,
        "A persistência em |r| mistura clustering de volatilidade e sazonalidade intradiária. "
        "No painel diário, um lag equivale a um pregão observado dentro do mesmo segmento.",
        ha="center",
        color=GRAY,
        fontsize=9,
    )
    return _save(fig, output_path)
