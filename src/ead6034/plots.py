from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


NAVY = "#102A43"
BLUE = "#1F5FAE"
TEAL = "#008C95"
RED = "#C83E4D"
GOLD = "#D89B2B"
LIGHT_BLUE = "#EAF2FB"
GRAY = "#66788A"
LIGHT_GRAY = "#D7E0E8"


def set_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.edgecolor": "#A7B4C0",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#E6EBF0",
            "grid.linewidth": 0.7,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_series_overview(
    train: pd.DataFrame,
    daily: pd.DataFrame,
    output_path: Path,
) -> Path:
    set_style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 8.3), constrained_layout=True)
    ax_price, ax_returns, ax_distribution, ax_volatility = axes.flat

    daily_time = pd.to_datetime(daily["date"])
    ax_price.plot(daily_time, daily["close"], color=BLUE, linewidth=1.3)
    roll_mask = daily["symbol"].ne(daily["symbol"].shift())
    for x in daily_time.loc[roll_mask].iloc[1:]:
        ax_price.axvline(x, color=GOLD, linewidth=0.65, alpha=0.55)
    ax_price.set_title("Nível do contrato ativo (último preço regular do dia)", loc="left")
    ax_price.set_ylabel("Pontos de índice")
    ax_price.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
    ax_price.tick_params(axis="x", rotation=30)
    ax_price.text(
        0.99,
        0.03,
        "Linhas douradas: mudança do ticker ativo; série não retroajustada",
        transform=ax_price.transAxes,
        ha="right",
        color=GRAY,
        fontsize=8.5,
    )

    ax_returns.plot(
        train["timestamp"], train["return_pct"], color=TEAL, linewidth=0.35, alpha=0.72
    )
    ax_returns.axhline(0.0, color=NAVY, linewidth=0.8)
    ax_returns.set_title("Retornos logarítmicos intradiários de 5 minutos", loc="left")
    ax_returns.set_ylabel("Retorno (%)")
    ax_returns.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_returns.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
    ax_returns.tick_params(axis="x", rotation=30)

    values = train["return_pct"].dropna().to_numpy()
    lower, upper = np.quantile(values, [0.001, 0.999])
    clipped = values[(values >= lower) & (values <= upper)]
    ax_distribution.hist(
        clipped, bins=100, color=BLUE, alpha=0.82, density=True, edgecolor="none"
    )
    ax_distribution.axvline(np.mean(values), color=RED, linewidth=1.2, label="média")
    ax_distribution.axvline(np.median(values), color=NAVY, linewidth=1.2, label="mediana")
    ax_distribution.set_title("Distribuição (zoom entre quantis 0,1% e 99,9%)", loc="left")
    ax_distribution.set_xlabel("Retorno de 5 minutos (%)")
    ax_distribution.set_ylabel("Densidade")
    ax_distribution.legend(frameon=False)
    ax_distribution.text(
        0.99,
        0.94,
        "Extremos preservados nos cálculos",
        transform=ax_distribution.transAxes,
        ha="right",
        va="top",
        color=GRAY,
        fontsize=8.5,
    )

    rolling = daily["realized_volatility"].rolling(20, min_periods=10).mean()
    ax_volatility.plot(
        daily_time,
        daily["realized_volatility"],
        color=LIGHT_GRAY,
        linewidth=0.8,
        label="diária",
    )
    ax_volatility.plot(daily_time, rolling, color=RED, linewidth=1.7, label="média móvel 20d")
    ax_volatility.set_title("Volatilidade realizada intradiária", loc="left")
    ax_volatility.set_ylabel(r"$\sqrt{\sum r_{d,j}^{2}}$ (%)")
    ax_volatility.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax_volatility.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
    ax_volatility.tick_params(axis="x", rotation=30)
    ax_volatility.legend(frameon=False)

    fig.suptitle(
        "WIN - leitura visual da série dentro da amostra (2024)",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    return _save(fig, output_path)


def plot_correlogram(table: pd.DataFrame, output_path: Path) -> Path:
    set_style()
    data = table.loc[table["lag"] > 0].copy()
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True, constrained_layout=True)

    specs = [
        ("acf", "acf_ci_95", "FAC - função de autocorrelação"),
        ("pacf", "pacf_ci_95", "FACP - função de autocorrelação parcial"),
    ]
    for ax, (column, ci_column, title) in zip(axes, specs):
        significant = data[column].abs() > data[ci_column]
        colors = np.where(significant, RED, BLUE)
        ax.vlines(data["lag"], 0, data[column], color=colors, linewidth=2.1)
        ax.scatter(data["lag"], data[column], color=colors, s=18, zorder=3)
        ax.plot(data["lag"], data[ci_column], color=GRAY, linestyle="--", linewidth=0.9)
        ax.plot(data["lag"], -data[ci_column], color=GRAY, linestyle="--", linewidth=0.9)
        ax.axhline(0.0, color=NAVY, linewidth=0.8)
        ax.set_title(title, loc="left")
        ax.set_ylabel("Correlação")
        ax.set_xlim(0.4, data["lag"].max() + 0.6)
        for lag in (1, 2, 4, 6, 12):
            if lag <= data["lag"].max():
                ax.axvline(lag, color=GOLD, alpha=0.16, linewidth=3)

    axes[-1].set_xlabel("Defasagem (barras de 5 minutos)")
    axes[-1].set_xticks(np.arange(1, int(data["lag"].max()) + 1))
    top = axes[0].secondary_xaxis("top", functions=(lambda lag: lag * 5, lambda minute: minute / 5))
    top.set_xlabel("Separação temporal (minutos)")
    top.set_xticks([5, 10, 20, 30, 60, 90, 120, 150])
    fig.suptitle(
        "Correlogramas intrapregão dos retornos de 5 minutos - amostra de 2024",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    fig.text(
        0.5,
        -0.015,
        "Bandas aproximadas de 95%; barras vermelhas, se houver, indicam ultrapassagem pontual. "
        "As defasagens não atravessam a fronteira entre pregões.",
        ha="center",
        color=GRAY,
        fontsize=9,
    )
    return _save(fig, output_path)


def plot_intraday_dependence(
    profile: pd.DataFrame,
    magnitude: pd.DataFrame,
    output_path: Path,
) -> Path:
    set_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), constrained_layout=True)
    ax_profile, ax_dependence = axes

    x = np.arange(len(profile))
    ax_profile.plot(x, profile["median_absolute_return"], color=TEAL, linewidth=1.8)
    ax_profile.set_title("Sazonalidade intradiária da magnitude", loc="left")
    ax_profile.set_ylabel("Mediana de |retorno| (%)")
    ax_profile.set_xlabel("Horário local da barra")
    tick_positions = np.linspace(0, len(profile) - 1, 7).round().astype(int)
    ax_profile.set_xticks(tick_positions)
    ax_profile.set_xticklabels(profile.iloc[tick_positions]["clock"], rotation=30)

    data = magnitude.loc[magnitude["lag"] > 0]
    ax_dependence.plot(
        data["lag"],
        data["acf_absolute_returns"],
        marker="o",
        markersize=3.5,
        color=RED,
        linewidth=1.4,
        label=r"FAC de $|r_t|$",
    )
    ax_dependence.plot(
        data["lag"],
        data["acf_squared_returns"],
        marker="s",
        markersize=3.0,
        color=BLUE,
        linewidth=1.2,
        label=r"FAC de $r_t^2$",
    )
    ax_dependence.axhline(0.0, color=NAVY, linewidth=0.8)
    ax_dependence.set_title("Dependência na magnitude dos retornos", loc="left")
    ax_dependence.set_xlabel("Defasagem (barras de 5 minutos)")
    ax_dependence.set_ylabel("Autocorrelação")
    ax_dependence.legend(frameon=False)

    fig.suptitle(
        "Volatilidade: padrão intradiário e persistência",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    return _save(fig, output_path)
