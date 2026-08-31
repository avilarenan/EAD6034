from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from .analysis import (
    chronological_split,
    correlogram,
    daily_summary,
    dependence_in_magnitude,
    descriptive_statistics,
)
from .data import audit_minutes, load_win_minutes
from .multiscale import (
    INTRADAY_SCALES,
    MultiscaleConfig,
    build_daily_open_to_close,
    build_multiscale_bars,
    scale_label,
    scale_minutes,
)
from .multiscale_plots import (
    plot_multiscale_correlograms,
    plot_multiscale_dependence_and_daily,
    plot_multiscale_descriptives,
)
from .multiscale_report import create_multiscale_pdf_report
from .plots import plot_series_overview


SCALE_ORDER = [key for key, _, _ in INTRADAY_SCALES] + ["1d"]
NATIVE_MAX_LAGS = {
    "1min": 60,  # inclui a comparação física em 60 minutos
    "5min": 30,
    "15min": 30,
    "30min": 17,
    "60min": 8,
}


def _json_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return json.loads(frame.to_json(orient="records"))


def _software_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "matplotlib": version("matplotlib"),
        "numpy": version("numpy"),
        "pandas": version("pandas"),
        "pyarrow": version("pyarrow"),
        "scipy": version("scipy"),
        "statsmodels": version("statsmodels"),
    }


def _statistics_by_scale(train_by_scale: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for scale in SCALE_ORDER:
        train = train_by_scale[scale]
        row = descriptive_statistics({"in_sample": train["return_pct"]}).iloc[0].to_dict()
        minutes = scale_minutes(scale)
        equivalent_minutes = 540 if scale == "1d" else int(minutes)
        row.update(
            {
                "scale": scale,
                "label": scale_label(scale),
                "bar_minutes": None if minutes is None else int(minutes),
                "equivalent_minutes": equivalent_minutes,
                "train_days": int(train["date"].nunique()),
                "returns_per_session": int(train.groupby("date").size().mode().iloc[0]),
                "std_per_sqrt_minute": float(row["std"] / np.sqrt(equivalent_minutes)),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _scaled_correlogram(
    frame: pd.DataFrame,
    scale: str,
    max_lag: int,
    session_column: str,
) -> pd.DataFrame:
    result = correlogram(
        frame,
        max_lag=max_lag,
        value_column="return_pct",
        session_column=session_column,
        acf_normalization="pairwise",
    )
    minutes = scale_minutes(scale)
    result["scale"] = scale
    result["label"] = scale_label(scale)
    result["bar_minutes"] = np.nan if minutes is None else minutes
    result["separation_value"] = (
        result["lag"] if minutes is None else result["lag"] * minutes
    )
    result["separation_unit"] = "pregões" if minutes is None else "minutos"
    if minutes is not None:
        result["minutes"] = result["separation_value"]
    else:
        result["minutes"] = np.nan
    return result


def _scaled_magnitude(
    frame: pd.DataFrame,
    scale: str,
    max_lag: int,
    session_column: str,
) -> pd.DataFrame:
    result = dependence_in_magnitude(
        frame,
        max_lag=max_lag,
        value_column="return_pct",
        session_column=session_column,
        acf_normalization="pairwise",
    )
    minutes = scale_minutes(scale)
    result["scale"] = scale
    result["label"] = scale_label(scale)
    result["bar_minutes"] = np.nan if minutes is None else minutes
    result["separation_value"] = (
        result["lag"] if minutes is None else result["lag"] * minutes
    )
    result["separation_unit"] = "pregões" if minutes is None else "minutos"
    if minutes is not None:
        result["minutes"] = result["separation_value"]
    else:
        result["minutes"] = np.nan
    return result


def _scale_summary(
    stats: pd.DataFrame,
    correlations: pd.DataFrame,
    magnitude: pd.DataFrame,
    comparison_horizon_minutes: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for scale in SCALE_ORDER:
        stat = stats.loc[stats["scale"] == scale].iloc[0]
        corr = correlations.loc[(correlations["scale"] == scale) & (correlations["lag"] > 0)]
        mag = magnitude.loc[(magnitude["scale"] == scale) & (magnitude["lag"] > 0)]
        lag_one = corr.loc[corr["lag"] == 1].iloc[0]
        mag_one = mag.loc[mag["lag"] == 1].iloc[0]
        max_acf_row = corr.loc[corr["acf"].abs().idxmax()]
        max_pacf_row = corr.loc[corr["pacf"].abs().idxmax()]
        row: dict[str, object] = {
            "scale": scale,
            "label": scale_label(scale),
            "n": int(stat["n"]),
            "train_days": int(stat["train_days"]),
            "returns_per_session": int(stat["returns_per_session"]),
            "mean": float(stat["mean"]),
            "std": float(stat["std"]),
            "zero_share": float(stat["zero_share"]),
            "skewness": float(stat["skewness"]),
            "excess_kurtosis": float(stat["excess_kurtosis"]),
            "acf_lag1": float(lag_one["acf"]),
            "pacf_lag1": float(lag_one["pacf"]),
            "acf_ci_lag1": float(lag_one["acf_ci_95"]),
            "abs_acf_lag1": float(mag_one["acf_absolute_returns"]),
            "squared_acf_lag1": float(mag_one["acf_squared_returns"]),
            "max_abs_acf_native": float(abs(max_acf_row["acf"])),
            "max_abs_acf_native_lag": int(max_acf_row["lag"]),
            "max_abs_pacf_native": float(abs(max_pacf_row["pacf"])),
            "max_abs_pacf_native_lag": int(max_pacf_row["lag"]),
            "native_max_lag": int(corr["lag"].max()),
            "acf_at_common_horizon": np.nan,
            "pacf_at_common_horizon": np.nan,
            "acf_ci_at_common_horizon": np.nan,
            "abs_acf_at_common_horizon": np.nan,
        }
        minutes = scale_minutes(scale)
        if minutes is not None:
            if comparison_horizon_minutes % minutes != 0:
                raise ValueError(
                    "A separação física comum deve ser divisível por todas as escalas."
                )
            common_lag = comparison_horizon_minutes // minutes
            common = corr.loc[corr["lag"] == common_lag].iloc[0]
            common_mag = mag.loc[mag["lag"] == common_lag].iloc[0]
            row.update(
                {
                    "acf_at_common_horizon": float(common["acf"]),
                    "pacf_at_common_horizon": float(common["pacf"]),
                    "acf_ci_at_common_horizon": float(common["acf_ci_95"]),
                    "abs_acf_at_common_horizon": float(
                        common_mag["acf_absolute_returns"]
                    ),
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def _daily_robustness(
    daily_train: pd.DataFrame,
    daily_corr: pd.DataFrame,
    max_lag: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    open_stats = descriptive_statistics({"open_to_close": daily_train["return_pct"]}).iloc[0]
    open_nonzero = daily_corr.loc[daily_corr["lag"] > 0]
    rows.append(
        {
            "definition": "open_to_close_common_window",
            "n": int(open_stats["n"]),
            "mean": float(open_stats["mean"]),
            "std": float(open_stats["std"]),
            "skewness": float(open_stats["skewness"]),
            "excess_kurtosis": float(open_stats["excess_kurtosis"]),
            "max_abs_acf": float(open_nonzero["acf"].abs().max()),
            "max_abs_pacf": float(open_nonzero["pacf"].abs().max()),
        }
    )

    boundary_stats = descriptive_statistics(
        {"boundary_to_close": daily_train["boundary_to_close_return_pct"]}
    ).iloc[0]
    boundary_corr = correlogram(
        daily_train,
        max_lag=max_lag,
        value_column="boundary_to_close_return_pct",
        session_column="segment_id",
        acf_normalization="pairwise",
    )
    boundary_nonzero = boundary_corr.loc[boundary_corr["lag"] > 0]
    rows.append(
        {
            "definition": "boundary_to_close_intraday_reconciliation",
            "n": int(boundary_stats["n"]),
            "mean": float(boundary_stats["mean"]),
            "std": float(boundary_stats["std"]),
            "skewness": float(boundary_stats["skewness"]),
            "excess_kurtosis": float(boundary_stats["excess_kurtosis"]),
            "max_abs_acf": float(boundary_nonzero["acf"].abs().max()),
            "max_abs_pacf": float(boundary_nonzero["pacf"].abs().max()),
        }
    )

    close_train = daily_train.dropna(subset=["close_to_close_return_pct"]).copy()
    close_stats = descriptive_statistics(
        {"close_to_close": close_train["close_to_close_return_pct"]}
    ).iloc[0]
    close_corr = correlogram(
        close_train,
        max_lag=max_lag,
        value_column="close_to_close_return_pct",
        session_column="segment_id",
        acf_normalization="pairwise",
    )
    close_nonzero = close_corr.loc[close_corr["lag"] > 0]
    rows.append(
        {
            "definition": "close_to_close_same_contract_robustness",
            "n": int(close_stats["n"]),
            "mean": float(close_stats["mean"]),
            "std": float(close_stats["std"]),
            "skewness": float(close_stats["skewness"]),
            "excess_kurtosis": float(close_stats["excess_kurtosis"]),
            "max_abs_acf": float(close_nonzero["acf"].abs().max()),
            "max_abs_pacf": float(close_nonzero["pacf"].abs().max()),
        }
    )
    return pd.DataFrame(rows)


def _write_markdown(
    path: Path,
    summary: dict[str, object],
    scale_summary: pd.DataFrame,
) -> None:
    rows = []
    for _, row in scale_summary.iterrows():
        acf_common = (
            "-"
            if pd.isna(row["acf_at_common_horizon"])
            else f"{row['acf_at_common_horizon']:.4f}"
        )
        rows.append(
            f"| {row['label']} | {int(row['n']):,} | {row['std']:.4f}% | "
            f"{100 * row['zero_share']:.2f}% | {row['acf_lag1']:.4f} | {acf_common} | "
            f"{row['abs_acf_lag1']:.3f} |".replace(",", ".")
        )
    table = "\n".join(rows)
    exclusions = ", ".join(summary["excluded_train_dates"])
    horizon = int(summary["comparison_horizon_minutes"])
    acf_min, acf_max = summary["acf_at_common_horizon_range"]
    mag_min, mag_max = summary["abs_acf_at_common_horizon_range"]
    text = f"""# Entrega de 31/08 - análise visual multiescala, FAC e FACP

## Pergunta desta etapa

Como a dependência linear amostral do retorno do WIN muda quando o mesmo processo é observado em diferentes escalas?

O retorno de 5 minutos permanece como série principal e replicação adaptada do benchmark de Matías e Reboredo (2012). As escalas de 1, 15, 30 e 60 minutos e o diário são extensões descritivas que começam a executar o eixo escala da proposta.

## Protocolo comum

- Identificação: {summary['train_period']}; 2025 permanece reservado para avaliação fora da amostra.
- Janela intradiária: `[09:05,18:05)`, com 540 minutos, ancorada exatamente em 09:05.
- Escalas: 1, 5, 15, 30 e 60 minutos; retorno diário open-to-close da mesma janela.
- Amostra comum: {summary['train_days']} pregões completos; excluídos {exclusions}.
- Preço inicial intradiário: fechamento do candle iniciado às 09:04, imediatamente anterior à fronteira de 09:05.
- Preço inicial diário: `open` da primeira barra às 09:05, conforme a definição open-to-close da proposta.
- Retornos: logarítmicos percentuais, sem overnight, sem rolagem, sem winsorização e sem barras parciais.
- FAC intradiária: correlação pooled dos pares válidos no mesmo pregão; FACP: último coeficiente da AR(k) pooled. No diário, a lacuna integral de 2024-04-16, dias excluídos e trocas de contrato quebram a sequência.

## Comparação

| Escala | N | Desvio-padrão | Zeros | FAC lag 1 | FAC a {horizon} min | FAC do retorno absoluto lag 1 |
|---|---:|---:|---:|---:|---:|---:|
{table}

Na origem fixa de 09:05 e na separação física comum de {horizon} minutos, a FAC da média varia entre {acf_min:.4f} e {acf_max:.4f}, com mudança de sinal entre escalas. Não aparece uma redução monotônica nem um padrão simples de truncamento ou decaimento. Em contraste, a FAC de retornos absolutos nessa mesma separação permanece positiva, entre {mag_min:.3f} e {mag_max:.3f}.

Os zeros diminuem monotonicamente; o excesso de curtose se atenua nas escalas mais grossas, embora não de forma perfeitamente monotônica. A dispersão cresce aproximadamente com a raiz do tempo. Essas regularidades descrevem a distribuição; não demonstram capacidade preditiva.

## Limites

- Escala da barra, lag e horizonte futuro de previsão são conceitos distintos.
- Bandas pontuais de 95% não corrigem múltiplos testes, heteroscedasticidade ou dependência comum dentro do pregão.
- A escala de 1 minuto pode refletir bid-ask bounce, discretização e último negócio; o arquivo não possui midquotes para separar esses mecanismos.
- A FAC de |r| mistura clustering de volatilidade e sazonalidade intradiária.
- Barras não sobrepostas dependem da origem 09:05; deslocamentos da grade são uma robustez futura.
- O diário possui amostra pequena e usa lags em pregões, não em minutos.
- Esta etapa não conclui estacionariedade, não escolhe ordem ARMA e não avalia previsão OOS.

O relatório original de 5 minutos em `results/entrega_31_08/` foi preservado como piloto. A versão multiescala usa um protocolo comum mais estrito e não mistura silenciosamente os dois recortes.
"""
    path.write_text(text, encoding="utf-8")


def run_multiscale_pipeline(
    source: Path,
    output_dir: Path,
    config: MultiscaleConfig,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    raw, source_metadata = load_win_minutes(source)
    # A auditoria bruta cobre o arquivo inteiro e usa os mesmos fusos do protocolo.
    from .data import SampleConfig

    audit_config = SampleConfig(
        start_date=config.start_date,
        end_date=config.end_date,
        source_timezone=config.source_timezone,
        market_timezone=config.market_timezone,
    )
    raw_audit = audit_minutes(raw, audit_config)
    bars_by_scale, coverage = build_multiscale_bars(raw, config)
    daily = build_daily_open_to_close(bars_by_scale["1min"], coverage, config)
    all_series: dict[str, pd.DataFrame] = {**bars_by_scale, "1d": daily}

    train_by_scale: dict[str, pd.DataFrame] = {}
    test_by_scale: dict[str, pd.DataFrame] = {}
    train_end = ""
    test_start = ""
    for scale in SCALE_ORDER:
        train, test, train_end, test_start = chronological_split(
            all_series[scale], config.train_end_date, config.test_start_date
        )
        train_by_scale[scale] = train
        test_by_scale[scale] = test

    stats = _statistics_by_scale(train_by_scale)
    correlation_parts: list[pd.DataFrame] = []
    magnitude_parts: list[pd.DataFrame] = []
    for scale in SCALE_ORDER:
        session_column = "segment_id" if scale == "1d" else "date"
        if scale == "1d":
            max_lag = config.daily_max_lag
        else:
            minutes = scale_minutes(scale)
            if minutes is None or config.comparison_horizon_minutes % minutes != 0:
                raise ValueError(
                    "A separação física comum deve ser divisível por todas as escalas."
                )
            max_lag = max(
                NATIVE_MAX_LAGS[scale],
                config.comparison_horizon_minutes // minutes,
            )
        correlation_parts.append(
            _scaled_correlogram(
                train_by_scale[scale], scale, max_lag, session_column
            )
        )
        magnitude_parts.append(
            _scaled_magnitude(
                train_by_scale[scale], scale, max_lag, session_column
            )
        )
    correlations = pd.concat(correlation_parts, ignore_index=True)
    magnitude = pd.concat(magnitude_parts, ignore_index=True)
    scale_summary = _scale_summary(
        stats,
        correlations,
        magnitude,
        config.comparison_horizon_minutes,
    )
    daily_corr = correlations.loc[correlations["scale"] == "1d"].copy()
    daily_robustness = _daily_robustness(
        train_by_scale["1d"], daily_corr, config.daily_max_lag
    )

    five_minute_bars = bars_by_scale["5min"].loc[
        bars_by_scale["5min"]["date"] <= config.train_end_date
    ].copy()
    five_minute_daily = daily_summary(five_minute_bars)
    contracts = (
        five_minute_bars.groupby("date", as_index=False, observed=True)["symbol"]
        .first()
        .sort_values("date")
    )
    rolls = contracts.loc[contracts["symbol"].ne(contracts["symbol"].shift())].copy()
    rolls["is_initial_contract"] = [True] + [False] * (len(rolls) - 1)

    coverage.to_csv(tables_dir / "coverage_by_day.csv", index=False)
    stats.to_csv(tables_dir / "descriptive_statistics_by_scale.csv", index=False)
    scale_summary.to_csv(tables_dir / "scale_summary.csv", index=False)
    correlations.to_csv(tables_dir / "acf_pacf_by_scale.csv", index=False)
    magnitude.to_csv(tables_dir / "dependence_in_magnitude_by_scale.csv", index=False)
    daily_robustness.to_csv(tables_dir / "daily_robustness_summary.csv", index=False)
    rolls.to_csv(tables_dir / "contract_rolls_in_sample.csv", index=False)
    # Usada na figura, mas ignorada pelo Git por conter níveis exatos do feed.
    five_minute_daily.to_csv(tables_dir / "daily_summary_in_sample.csv", index=False)

    overview_path = plot_series_overview(
        train_by_scale["5min"],
        five_minute_daily,
        figures_dir / "01_series_overview.png",
    )
    descriptives_path = plot_multiscale_descriptives(
        stats, figures_dir / "02_multiscale_descriptives.png"
    )
    correlograms_path = plot_multiscale_correlograms(
        correlations,
        scale_summary,
        figures_dir / "03_multiscale_acf_pacf.png",
        config.comparison_horizon_minutes,
    )
    dependence_path = plot_multiscale_dependence_and_daily(
        magnitude,
        train_by_scale["1d"],
        daily_corr,
        figures_dir / "04_multiscale_dependence_daily.png",
        config.comparison_horizon_minutes,
    )

    train_coverage = coverage.loc[
        (coverage["date"] >= config.start_date)
        & (coverage["date"] <= config.train_end_date)
    ]
    test_coverage = coverage.loc[coverage["date"] >= config.test_start_date]
    excluded_train_dates = train_coverage.loc[~train_coverage["included"], "date"].tolist()
    excluded_test_dates = test_coverage.loc[~test_coverage["included"], "date"].tolist()
    intraday_summary = scale_summary.loc[scale_summary["scale"] != "1d"]
    summary: dict[str, object] = {
        "config": asdict(config),
        "source": source_metadata,
        "software_versions": _software_versions(),
        "raw_audit": raw_audit,
        "acf_estimator": "pooled_pairwise_within_session",
        "pacf_estimator": "pooled_ar_last_coefficient_within_session",
        "primary_scale": "5min",
        "comparison_horizon_minutes": config.comparison_horizon_minutes,
        "scales": SCALE_ORDER,
        "train_period": f"{train_by_scale['5min']['date'].min()} a {train_end}",
        "train_days": int(train_by_scale["5min"]["date"].nunique()),
        "test_start": test_start,
        "test_end": str(test_by_scale["5min"]["date"].max()),
        "test_days_reserved": int(test_by_scale["5min"]["date"].nunique()),
        "excluded_train_dates": excluded_train_dates,
        "excluded_test_dates": excluded_test_dates,
        "known_source_gaps": list(config.known_source_gaps),
        "raw_rows": raw_audit["raw_rows"],
        "raw_contracts": raw_audit["contracts"],
        "duplicates": raw_audit["duplicate_symbol_timestamps"],
        "missing_values": raw_audit["missing_values"],
        "invalid_ohlc": raw_audit["invalid_ohlc_rows"],
        "rolls_in_sample": int(max(len(rolls) - 1, 0)),
        "acf_at_common_horizon_range": [
            float(intraday_summary["acf_at_common_horizon"].min()),
            float(intraday_summary["acf_at_common_horizon"].max()),
        ],
        "abs_acf_at_common_horizon_range": [
            float(intraday_summary["abs_acf_at_common_horizon"].min()),
            float(intraday_summary["abs_acf_at_common_horizon"].max()),
        ],
        "scale_results": _json_records(scale_summary),
        "daily_robustness": _json_records(daily_robustness),
        "daily_boundary_open_gap_pct": {
            "mean_absolute": float(
                train_by_scale["1d"]["boundary_to_open_return_pct"].abs().mean()
            ),
            "maximum_absolute": float(
                train_by_scale["1d"]["boundary_to_open_return_pct"].abs().max()
            ),
        },
        "legacy_pilot": "results/entrega_31_08/ENTREGA_31_08.pdf",
    }

    (output_dir / "analysis_summary_multiscale.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _write_markdown(
        output_dir / "ENTREGA_31_08_MULTIESCALA.md", summary, scale_summary
    )
    create_multiscale_pdf_report(
        output_dir / "ENTREGA_31_08_MULTIESCALA.pdf",
        overview_path,
        descriptives_path,
        correlograms_path,
        dependence_path,
        summary,
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reproduz a extensão multiescala da entrega de 31/08 da EAD6034."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="ZIP BTG-ATS-A26, WIN.parquet ou diretório extraído.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/entrega_31_08_multiescala"),
        help="Diretório de resultados multiescala.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run_multiscale_pipeline(args.input, args.output, MultiscaleConfig())
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
