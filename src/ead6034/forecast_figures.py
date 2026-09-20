"""Scientific figures sourced exclusively from the published aggregate CSVs.

No private parquet/NPZ data, individual returns, or fitted objects are read.
All statistics come from the public pipeline tables; figures introduce no new
estimator, test, fitted scaling exponent, or conclusion selected by appearance.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import pandas as pd


SCALES = ("1min", "5min", "15min", "30min", "60min", "1d")
INTRADAY = SCALES[:-1]
LABELS = {"1min": "1 minuto", "5min": "5 minutos", "15min": "15 minutos",
          "30min": "30 minutos", "60min": "60 minutos", "1d": "Diário OC"}
NAVY, TEAL, ORANGE = "#15324F", "#087F8C", "#D47927"
GRAY, BLUE, PALE = "#697C8D", "#5A91B4", "#D9E5EC"
SCALE_COLORS = dict(zip(INTRADAY, (NAVY, TEAL, ORANGE, BLUE, GRAY)))
MODEL_STYLE = {
    "ARMA_BIC": ("ARMA por BIC", NAVY, "o", "-"),
    "AR_BIC": ("AR por BIC", TEAL, "s", "--"),
    "MA_BIC": ("MA por BIC", ORANGE, "^", ":"),
    "AR_MA_50_50": ("AR + MA (50% / 50%)", BLUE, "D", "-."),
}
STYLE = {
    "font.family": "DejaVu Sans", "font.size": 13,
    "axes.titlesize": 16, "axes.labelsize": 13,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11,
    "figure.titlesize": 22, "axes.spines.top": False,
    "axes.spines.right": False, "axes.edgecolor": GRAY,
    "text.color": NAVY, "axes.labelcolor": NAVY,
    "xtick.color": NAVY, "ytick.color": NAVY,
    "axes.grid": True, "grid.alpha": .2,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.facecolor": "white", "figure.facecolor": "white",
}


def _table(tables: Path, name: str, columns: tuple[str, ...]) -> pd.DataFrame:
    path = tables / f"{name}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Public aggregate table not ready: {path}")
    frame = pd.read_csv(path)
    missing = set(columns) - set(frame)
    if missing:
        raise ValueError(f"{path.name}: missing required columns {sorted(missing)}")
    return frame


def _subset(frame: pd.DataFrame, scale: str) -> pd.DataFrame:
    result = frame.loc[frame.scale.eq(scale)].copy()
    if result.empty:
        raise ValueError(f"Public figure input is missing scale {scale}")
    return result


def _true(values: pd.Series) -> pd.Series:
    return values.astype(str).str.lower().isin(("true", "1"))


def _pt_number(value: float, _position=None) -> str:
    return f"{value:g}".replace(".", ",")


def _finish(fig, title, note, directory, name, code_ref, *, handles=None, ncol=4):
    fig.suptitle(title, x=.055, y=.985, ha="left", weight="bold")
    if handles:
        fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.52, .945),
                   ncol=ncol, frameon=False, columnspacing=1.6)
    fig.text(.055, .057, note, fontsize=10.5, va="bottom", color=GRAY,
             linespacing=1.4)
    fig.text(.945, .017, "Código: forecast_figures.py", fontsize=9, ha="right",
             color=TEAL,
             url=f"https://github.com/avilarenan/EAD6034/blob/{code_ref}/src/ead6034/forecast_figures.py")
    fig.tight_layout(rect=(.035, .13, .98, .88 if handles else .925), h_pad=2.3, w_pad=2.4)
    paths = {}
    for suffix in ("png", "pdf"):
        path = directory / f"{name}.{suffix}"
        fig.savefig(path, dpi=160, facecolor="white")
        paths[suffix] = str(path)
    plt.close(fig)
    return paths


def _correlation_panel(ax, frame, scale, series):
    frame = frame.sort_values("lag")
    x = frame.lag.to_numpy(float)
    band = frame.white_noise_pointwise_band.to_numpy(float)
    ax.fill_between(x, -band, band, color=PALE, alpha=.7, zorder=0)
    ax.plot(x, band, color=GRAY, linewidth=.7, linestyle="--")
    ax.plot(x, -band, color=GRAY, linewidth=.7, linestyle="--")
    ax.axhline(0, color=GRAY, linewidth=.8)
    for column, color, marker, offset in series:
        y = frame[column].to_numpy(float)
        ax.vlines(x + offset, 0, y, color=color, linewidth=1.2, alpha=.8)
        ax.plot(x + offset, y, linestyle="none", color=color, marker=marker,
                markersize=3.3)
    ax.set_title(f"{LABELS[scale]}  |  n = {int(frame.n.iloc[0]):,}".replace(",", "."))
    ax.set_xlabel("Defasagem (pregões)" if scale == "1d" else "Defasagem (barras)")
    ax.set_ylabel("Correlação")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
    ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
    ax.set_xlim(.45, x.max() + .55)
    low, high = ax.get_ylim()
    ax.set_ylim(min(low, -.025), max(high, .025))


def _returns_correlogram(tables, directory, code_ref):
    frame = _table(tables, "return_acf_pacf", ("scale", "lag", "acf", "pacf", "n", "white_noise_pointwise_band"))
    fig, axes = plt.subplots(2, 3, figsize=(16, 9.5))
    for ax, scale in zip(axes.flat, SCALES):
        _correlation_panel(ax, _subset(frame, scale), scale,
                           (("acf", NAVY, "o", -.12), ("pacf", TEAL, "s", .12)))
    handles = [Line2D([], [], color=NAVY, marker="o", label="FAC"),
               Line2D([], [], color=TEAL, marker="s", label="FACP"),
               Patch(facecolor=PALE, label="Referência pontual ±1,96 / √n")]
    return _finish(fig, "Dependência dos retornos | 2024",
                   "Sequência anual de barras; defasagens podem atravessar pregões. Um lag não representa sempre o mesmo tempo de relógio.\n"
                   "Bandas pontuais sob referência de ruído branco; não são teste conjunto nem correção para múltiplas defasagens.",
                   directory, "01_return_acf_pacf", code_ref, handles=handles, ncol=3)


def _returns_correlogram_slide(tables, directory, code_ref):
    """Wide six-panel version; slide provides the title, notes and code link."""
    frame = _table(tables, "return_acf_pacf", ("scale", "lag", "acf", "pacf", "n", "white_noise_pointwise_band"))
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 4.4))
    for index, (ax, scale) in enumerate(zip(axes.flat, SCALES)):
        _correlation_panel(ax, _subset(frame, scale), scale,
                           (("acf", NAVY, "o", -.12), ("pacf", TEAL, "s", .12)))
        ax.set_title(LABELS[scale], fontsize=16, pad=4)
        ax.tick_params(axis="both", labelsize=12, pad=2)
        ax.set_ylabel("Correlação" if index % 3 == 0 else "", fontsize=13)
        if index < 3:
            ax.set_xlabel("")
        else:
            ax.set_xlabel("Lag (pregões)" if scale == "1d" else "Lag (barras)", fontsize=13, labelpad=2)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    handles = [Line2D([], [], color=NAVY, marker="o", markersize=5, label="FAC"),
               Line2D([], [], color=TEAL, marker="s", markersize=5, label="FACP"),
               Patch(facecolor=PALE, label="Referência pontual ±1,96 / √n")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.52, 1.015),
               ncol=3, frameon=False, fontsize=13, columnspacing=2,
               handlelength=1.8, borderaxespad=.3)
    fig.subplots_adjust(left=.08, right=.99, bottom=.14, top=.81, hspace=.57, wspace=.32)
    paths = {}
    for suffix in ("png", "pdf"):
        path = directory / f"01b_return_acf_pacf_slide.{suffix}"
        fig.savefig(path, dpi=200, facecolor="white")
        paths[suffix] = str(path)
    plt.close(fig)
    return paths


def _dispersion(tables, directory, code_ref):
    frame = _table(tables, "descriptive", ("scale", "std_pct"))
    x = np.array([1, 5, 15, 30, 60], float)
    y = np.array([float(_subset(frame, scale).std_pct.iloc[0]) for scale in INTRADAY])
    daily = float(_subset(frame, "1d").std_pct.iloc[0])
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.4), gridspec_kw={"width_ratios": [3.5, 1]})
    axes[0].plot(x, y, "o-", color=NAVY, markersize=7, linewidth=2)
    smooth = np.linspace(1, 60, 200)
    axes[0].plot(smooth, y[0] * np.sqrt(smooth), "--", color=ORANGE, linewidth=2)
    axes[0].set_xticks(x)
    axes[0].set_xlabel("Duração da barra intradiária (minutos)")
    axes[0].set_ylabel("Desvio-padrão do retorno (%)")
    axes[0].set_ylim(bottom=0)
    axes[1].bar([0], [daily], width=.55, color=TEAL)
    axes[1].set_xticks([0], ["Diário OC"])
    axes[1].set_title("Outra definição")
    axes[1].set_ylabel("Desvio-padrão (%)")
    axes[1].set_xlim(-.65, .65)
    for ax in axes:
        ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
    handles = [Line2D([], [], color=NAVY, marker="o", label="Observado em 2024"),
               Line2D([], [], color=ORANGE, linestyle="--", label="Referência: σ(1 min) × √minutos")]
    return _finish(fig, "Dispersão por escala | 2024",
                   "A raiz do tempo é somente uma referência ancorada em 1 minuto, não um expoente estimado nem uma hipótese confirmada.\n"
                   "Diário OC: abertura às 09:05 até fechamento da janela às 18:05, sem overnight; eixo próprio e definição distinta.",
                   directory, "02_dispersion_scales", code_ref, handles=handles, ncol=2)


def _residuals(tables, directory, code_ref):
    columns = ("scale", "model", "lag", "acf", "n", "white_noise_pointwise_band")
    residual = _table(tables, "residual_acf_pacf", columns)
    squared = _table(tables, "squared_residual_acf", columns)
    residual = residual.loc[residual.model.eq("ARMA_BIC")]
    squared = squared.loc[squared.model.eq("ARMA_BIC")]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9.5))
    for ax, scale in zip(axes.flat, SCALES):
        data = _subset(residual, scale).merge(
            _subset(squared, scale)[["lag", "acf"]].rename(columns={"acf": "acf_squared"}),
            on="lag", validate="one_to_one")
        _correlation_panel(ax, data, scale,
                           (("acf", NAVY, "o", -.12), ("acf_squared", ORANGE, "s", .12)))
    handles = [Line2D([], [], color=NAVY, marker="o", label="FAC dos resíduos padronizados"),
               Line2D([], [], color=ORANGE, marker="s", label="FAC dos resíduos padronizados²"),
               Patch(facecolor=PALE, label="Referência pontual ±1,96 / √n")]
    return _finish(fig, "Diagnóstico da média ARMA por BIC | 2024",
                   "Resíduos da equação da média, antes da extensão ARCH/GARCH. Dependência linear e dependência nos quadrados são propriedades distintas.\n"
                   "As bandas são referências pontuais aproximadas; os testes formais estão nas tabelas públicas de diagnóstico.",
                   directory, "03_residual_acf", code_ref, handles=handles, ncol=3)


def _forecast_accuracy(tables, directory, code_ref):
    frame = _table(tables, "accuracy", ("scale", "evaluation", "group_type", "model", "mse_ratio_vs_zero", "n"))
    frame = frame.loc[frame.evaluation.eq("common_60min") & frame.group_type.eq("all")]
    fig, ax = plt.subplots(figsize=(14, 7.4))
    x = np.arange(len(INTRADAY))
    handles = []
    for model, (label, color, marker, linestyle) in MODEL_STYLE.items():
        part = frame.loc[frame.model.eq(model)]
        values = [float(_subset(part, scale).mse_ratio_vs_zero.iloc[0]) for scale in INTRADAY]
        ax.plot(x, values, color=color, marker=marker, linestyle=linestyle,
                linewidth=2.1, markersize=8, markerfacecolor="white", markeredgewidth=1.5)
        handles.append(Line2D([], [], color=color, marker=marker, linestyle=linestyle, label=label))
    ax.axhline(1, color=GRAY, linewidth=1.4, linestyle="--")
    ax.set_xticks(x, [LABELS[scale] for scale in INTRADAY])
    ax.set_xlabel("Escala usada pelo modelo")
    ax.set_ylabel("MSE do modelo / MSE da previsão ZERO")
    ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
    counts = sorted(set(frame.n.astype(int)))
    ntext = str(counts[0]) if len(counts) == 1 else ", ".join(map(str, counts))
    return _finish(fig, "Previsão do mesmo retorno de 60 minutos | 2025",
                   f"Mesmos alvos, origens horárias e preços de referência entre as escalas; n = {ntext}. Linha 1: previsão de retorno zero.\n"
                   "Razão menor que 1 indica menor MSE. Eixo ampliado para leitura; curvas coincidentes podem se sobrepor. Parâmetros fixados em 2024.",
                   directory, "04_common_hour_accuracy", code_ref, handles=handles, ncol=4)


def _session_bands(tables, directory, code_ref):
    descriptive = _table(tables, "time_band_description", ("scale", "time_band", "std_pct"))
    accuracy = _table(tables, "accuracy", ("scale", "evaluation", "group_type", "group", "model", "mse_ratio_vs_zero"))
    accuracy = accuracy.loc[accuracy.evaluation.eq("common_60min")
                            & accuracy.group_type.eq("time_band") & accuracy.model.eq("ARMA_BIC")]
    bands = ["inicio", "meio", "fim"]
    fig, axes = plt.subplots(1, 2, figsize=(16, 7.7))
    handles = []
    for scale in INTRADAY:
        color = SCALE_COLORS[scale]
        train = _subset(descriptive, scale).set_index("time_band")
        test = _subset(accuracy, scale).set_index("group")
        if not set(bands).issubset(train.index) or not set(bands).issubset(test.index):
            raise ValueError(f"{scale}: incomplete time-band public metrics")
        axes[0].plot(range(3), train.loc[bands, "std_pct"], "o-", color=color, linewidth=2, markersize=7)
        axes[1].plot(range(3), test.loc[bands, "mse_ratio_vs_zero"], "o-", color=color, linewidth=2, markersize=7)
        handles.append(Line2D([], [], color=color, marker="o", label=LABELS[scale]))
    axes[0].set_title("Dispersão da barra | treino 2024")
    axes[0].set_ylabel("Desvio-padrão do retorno (%)")
    axes[0].set_ylim(bottom=0)
    axes[1].set_title("ARMA por BIC | previsão 60 min em 2025")
    axes[1].set_ylabel("MSE / MSE da previsão ZERO na faixa")
    axes[1].axhline(1, color=GRAY, linestyle="--", linewidth=1.2)
    for ax in axes:
        ax.set_xticks(range(3), ["Início\n09:05-10:05", "Meio\n10:05-17:05", "Fim\n17:05-18:05"])
        ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
    return _finish(fig, "Posição na janela de análise",
                   "À esquerda: retornos da própria escala, com durações distintas. À direita: os mesmos retornos acumulados de 60 minutos.\n"
                   "As faixas são bordas da janela 09:05-18:05; não identificam, por si, leilões de abertura ou fechamento. Comparação descritiva, não causal.",
                   directory, "05_session_bands", code_ref, handles=handles, ncol=5)


def _minute_profile(tables, directory, code_ref):
    frame = _table(tables, "minute_of_day_profile_2024", ("clock", "returns_n", "mean_abs_return_pct"))
    clock = frame.clock.str.split(":", expand=True).astype(int)
    frame = frame.assign(clock_minutes=clock[0] * 60 + clock[1]).sort_values("clock_minutes")
    # Defense in depth: never plot a low-count summary even if an old CSV has it.
    values = frame.mean_abs_return_pct.where(frame.returns_n.ge(10))
    fig, ax = plt.subplots(figsize=(14, 7.4))
    ax.axvspan(9 * 60 + 5, 18 * 60 + 5, color=TEAL, alpha=.07)
    ax.plot(frame.clock_minutes, values, color=NAVY, linewidth=1.6)
    ax.axvline(9 * 60 + 5, color=TEAL, linestyle="--", linewidth=1)
    ax.axvline(18 * 60 + 5, color=TEAL, linestyle="--", linewidth=1)
    low, high = int(frame.clock_minutes.min()), int(frame.clock_minutes.max())
    ticks = np.arange(low // 60 * 60, (high // 60 + 1) * 60 + 1, 60)
    ax.set_xticks(ticks, [f"{int(value) // 60:02d}:00" for value in ticks])
    ax.set_xlim(low - 5, high + 5)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Horário do candle da fonte (São Paulo)")
    ax.set_ylabel("Média de |retorno de 1 minuto| (%)")
    ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
    handles = [Line2D([], [], color=NAVY, label="Média por horário em 2024"),
               Patch(facecolor=TEAL, alpha=.15, label="Janela principal 09:05-18:05")]
    return _finish(fig, "Perfil por minuto observado | 2024",
                   "Retornos entre candles consecutivos do mesmo pregão e contrato; sem retorno overnight. Estatísticas omitidas quando n < 10.\n"
                   "O horário do candle não identifica a fase de negociação; este gráfico não classifica negócios como pertencentes a leilões.",
                   directory, "06_minute_profile", code_ref, handles=handles, ncol=2)


def _variance_accuracy(tables, directory, code_ref):
    frame = _table(tables, "variance_models", ("scale", "model", "eligible", "oos_variance_proxy_mse"))
    frame = frame.loc[_true(frame.eligible)]
    fig, ax = plt.subplots(figsize=(14, 7.4))
    x = np.arange(len(SCALES))
    handles = []
    all_ratios = []
    for model, label, color, marker in (("arch1", "ARCH(1)", TEAL, "s"),
                                        ("garch11", "GARCH(1,1)", ORANGE, "o")):
        ratios = []
        for scale in SCALES:
            part = _subset(frame, scale)
            baseline = part.loc[part.model.eq("constant"), "oos_variance_proxy_mse"]
            candidate = part.loc[part.model.eq(model), "oos_variance_proxy_mse"]
            ratios.append(float(candidate.iloc[0] / baseline.iloc[0])
                          if len(candidate) and len(baseline) and baseline.iloc[0] > 0 else np.nan)
        ax.plot(x, ratios, color=color, marker=marker, linewidth=2, markersize=8)
        all_ratios.extend(value for value in ratios if np.isfinite(value) and value > 0)
        handles.append(Line2D([], [], color=color, marker=marker, label=label))
    ax.axhline(1, color=GRAY, linestyle="--", linewidth=1.3)
    ax.axvline(4.5, color=PALE, linewidth=1.5)
    ax.set_xticks(x, [LABELS[scale] for scale in SCALES])
    ax.set_xlabel("Escala da próxima observação prevista")
    ax.set_ylabel("MSE da proxy de variância / MSE da variância constante")
    if all_ratios and max(all_ratios) / min(all_ratios) > 10:
        ax.set_yscale("log")
        ax.set_ylabel("Razão de MSE da proxy de variância (eixo log)")
    else:
        ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
    return _finish(fig, "Previsão da variância | 2025",
                   "Alvo: inovação ARMA², proxy ruidosa da variância, comum aos candidatos em cada escala. Linha 1: variância constante estimada em 2024.\n"
                   "Horizonte nativo de uma observação: durações diferem entre escalas. Modelos inelegíveis não são plotados; previsão pontual da média é a mesma.",
                   directory, "07_variance_accuracy", code_ref, handles=handles, ncol=2)


def _monthly_mean_5min(tables, directory, code_ref):
    """Compact training-only temporal description for the cumulative deck.

    Each point is the mean of five-minute returns in that month, NOT a
    cumulative monthly return. All twelve months are required and displayed.
    """
    frame = _table(tables, "monthly_description", ("scale", "month", "n", "mean_pct"))
    frame = _subset(frame, "5min").sort_values("month")
    expected = [f"2024-{month:02d}" for month in range(1, 13)]
    if frame.month.tolist() != expected:
        raise ValueError("The compact monthly figure requires all 12 distinct months of 2024")
    if frame.n.lt(10).any() or not np.isfinite(frame.mean_pct.to_numpy(float)).all():
        raise ValueError("Monthly public means must be finite aggregates with at least 10 returns")
    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    ax.plot(range(12), frame.mean_pct, color=NAVY, linewidth=1.7, marker="o",
            markersize=4.5, markerfacecolor=TEAL, markeredgecolor=TEAL)
    ax.axhline(0, color=GRAY, linewidth=1, linestyle="--")
    ax.set_title("Média mensal | 5 min · 2024", fontsize=14, weight="bold", pad=8,
                 url=f"https://github.com/avilarenan/EAD6034/blob/{code_ref}/src/ead6034/forecast_figures.py")
    ax.set_ylabel("Média (%)", fontsize=13)
    ax.set_xticks(range(12), ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                             "Jul", "Ago", "Set", "Out", "Nov", "Dez"])
    ax.tick_params(axis="both", labelsize=12)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
    ax.set_xlim(-.3, 11.3)
    ax.grid(False, axis="x")
    fig.tight_layout(pad=.6)
    paths = {}
    for suffix in ("png", "pdf"):
        path = directory / f"08_monthly_mean_5min.{suffix}"
        fig.savefig(path, dpi=200, facecolor="white")
        paths[suffix] = str(path)
    plt.close(fig)
    return paths


def make_figures(output: str | Path, *, code_ref: str = "main") -> dict:
    """Write vector PDFs and PNGs using ONLY ``output/tables/*.csv``.

    Run after all six scales have completed and combined tables exist. Returns
    ``{figure_key: {png: absolute_path, pdf: absolute_path}, skipped: [...]}``.
    The variance figure is optional when its public OOS-MSE field is absent.
    The caller must complete the PDF-skill authoring marker before execution.
    """
    output = Path(output).resolve()
    tables, directory = output / "tables", output / "figures"
    directory.mkdir(parents=True, exist_ok=True)
    results = {}
    with plt.rc_context(STYLE):
        for key, function in (
            ("return_acf_pacf", _returns_correlogram),
            ("return_acf_pacf_slide", _returns_correlogram_slide),
            ("dispersion_scales", _dispersion),
            ("residual_acf", _residuals),
            ("common_hour_accuracy", _forecast_accuracy),
            ("session_bands", _session_bands),
            ("minute_profile", _minute_profile),
            ("monthly_mean_5min", _monthly_mean_5min),
        ):
            results[key] = function(tables, directory, code_ref)
        variance_path = tables / "variance_models.csv"
        if variance_path.is_file() and "oos_variance_proxy_mse" in pd.read_csv(variance_path, nrows=0).columns:
            results["variance_accuracy"] = _variance_accuracy(tables, directory, code_ref)
            results["skipped"] = []
        else:
            results["skipped"] = ["variance_accuracy: no public OOS variance-MSE table available"]
    return results
