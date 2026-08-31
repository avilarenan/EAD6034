from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from .analysis import (
    chronological_split,
    correlogram,
    daily_summary,
    dependence_in_magnitude,
    descriptive_statistics,
    intraday_profile,
)
from .data import SampleConfig, audit_minutes, build_five_minute_bars, load_win_minutes
from .plots import plot_correlogram, plot_intraday_dependence, plot_series_overview
from .report import create_pdf_report


def _write_markdown(path: Path, summary: dict[str, object], stats: pd.DataFrame) -> None:
    train_stats = stats.loc[stats["sample"] == "in_sample"].iloc[0]
    excluded = int(summary["excluded_days"])
    excluded_dates = ", ".join(str(item) for item in summary["excluded_train_dates"])
    exclusion_text = (
        f"1 sessão de horário reduzido ({excluded_dates}) ficou abaixo de 95% e foi excluída"
        if excluded == 1
        else f"{excluded} sessões ficaram abaixo de 95% de cobertura e foram excluídas"
    )
    text = f"""# Entrega de 31/08 - análise visual, FAC e FACP

## Recorte

- Série: retorno logarítmico percentual de 5 minutos do WIN.
- Identificação: {summary['train_period']} ({summary['train_days']} pregões; {summary['train_returns']} retornos).
- Holdout: 2025, iniciado em {summary['test_start']}, sem uso na FAC/FACP.
- Sessão: 09:05-18:25, horário de São Paulo; primeiro bloco de 5 minutos e período final de leilão/pausa excluídos.
- Rolagem: encadeamento do contrato ativo fornecido; nenhum retorno atravessa dia ou ticker.

## Auditoria

O arquivo WIN possui {summary['raw_rows']} linhas, {summary['raw_contracts']} contratos, {summary['duplicates']} duplicatas de chave, {summary['missing_values']} valores ausentes e {summary['invalid_ohlc']} violações OHLC. No treino, {exclusion_text} por regra definida antes de observar retornos.

## Leitura dos resultados

Na amostra de 2024, a média do retorno é {train_stats['mean']:.6f}% por barra e o desvio-padrão é {train_stats['std']:.6f}%. A proporção de retornos exatamente zero é {100 * train_stats['zero_share']:.2f}%. A distribuição apresenta assimetria {train_stats['skewness']:.2f} e excesso de curtose {train_stats['excess_kurtosis']:.2f}; os extremos foram mantidos.

A FAC e a FACP da média têm magnitudes pequenas e não mostram truncamento ou decaimento simples. O maior valor absoluto da FAC entre 1 e 30 lags é {summary['max_abs_acf']:.4f}. Na separação temporal de 60 minutos (lag 12), FAC={summary['acf_12']:.4f} e FACP={summary['pacf_12']:.4f}; isso não representa um retorno acumulado de 60 minutos. Picos isolados não devem ser transformados diretamente em uma ordem ARMA, especialmente sob múltiplos testes e com amostra intradiária grande.

Em contraste, a FAC de retornos absolutos no primeiro lag é {summary['abs_acf_1']:.3f}. O padrão é compatível com clustering de volatilidade, mas também contém a sazonalidade intradiária observada e não deve ser confundido com previsibilidade linear da média.

## Limites desta etapa

Esta entrega não conclui estacionariedade, não seleciona um ARMA final e não avalia previsão fora da amostra. ADF/PP/KPSS, Box-Jenkins, diagnóstico residual e comparação preditiva pertencem às entregas de 14/09 e 21/09.
"""
    path.write_text(text, encoding="utf-8")


def run_pipeline(source: Path, output_dir: Path, config: SampleConfig) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    raw, source_metadata = load_win_minutes(source)
    raw_audit = audit_minutes(raw, config)
    bars, coverage = build_five_minute_bars(raw, config)
    train, test, train_end, test_start = chronological_split(
        bars, config.train_end_date, config.test_start_date
    )
    train_bars = bars.loc[bars["date"] <= config.train_end_date].copy()

    stats = descriptive_statistics({"in_sample": train["return_pct"]})
    corr = correlogram(train, config.max_lag)
    daily = daily_summary(train_bars)
    profile = intraday_profile(train)
    magnitude = dependence_in_magnitude(train, config.max_lag)

    contracts = (
        train_bars.groupby("date", as_index=False, observed=True)["symbol"].first().sort_values("date")
    )
    rolls = contracts.loc[contracts["symbol"].ne(contracts["symbol"].shift())].copy()
    rolls["is_initial_contract"] = [True] + [False] * (len(rolls) - 1)

    coverage.to_csv(tables_dir / "coverage_by_day.csv", index=False)
    stats.to_csv(tables_dir / "descriptive_statistics.csv", index=False)
    corr.to_csv(tables_dir / "acf_pacf.csv", index=False)
    daily.to_csv(tables_dir / "daily_summary_in_sample.csv", index=False)
    profile.to_csv(tables_dir / "intraday_profile.csv", index=False)
    magnitude.to_csv(tables_dir / "dependence_in_magnitude.csv", index=False)
    rolls.to_csv(tables_dir / "contract_rolls_in_sample.csv", index=False)

    overview_path = plot_series_overview(
        train, daily, figures_dir / "01_series_overview.png"
    )
    correlogram_path = plot_correlogram(corr, figures_dir / "02_acf_pacf.png")
    dependence_path = plot_intraday_dependence(
        profile, magnitude, figures_dir / "03_intraday_dependence.png"
    )

    train_coverage = coverage.loc[
        (coverage["date"] >= config.start_date)
        & (coverage["date"] <= config.train_end_date)
    ]
    excluded_train_dates = train_coverage.loc[~train_coverage["included"], "date"].tolist()
    train_stats = stats.loc[stats["sample"] == "in_sample"].iloc[0]
    nonzero_lags = corr.loc[corr["lag"] > 0]
    lag_12 = corr.loc[corr["lag"] == 12].iloc[0]
    summary: dict[str, object] = {
        "config": asdict(config),
        "source": source_metadata,
        "software_versions": {
            "python": platform.python_version(),
            "matplotlib": version("matplotlib"),
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "pyarrow": version("pyarrow"),
            "scipy": version("scipy"),
            "statsmodels": version("statsmodels"),
        },
        "raw_audit": raw_audit,
        "train_period": f"{train['date'].min()} a {train_end}",
        "train_days": int(train["date"].nunique()),
        "train_returns": int(len(train)),
        "test_start": test_start,
        "test_end": str(test["date"].max()),
        "test_days_reserved": int(test["date"].nunique()),
        "excluded_days": int(len(excluded_train_dates)),
        "excluded_train_dates": excluded_train_dates,
        "raw_rows": raw_audit["raw_rows"],
        "raw_contracts": raw_audit["contracts"],
        "duplicates": raw_audit["duplicate_symbol_timestamps"],
        "missing_values": raw_audit["missing_values"],
        "invalid_ohlc": raw_audit["invalid_ohlc_rows"],
        "rolls_in_sample": int(max(len(rolls) - 1, 0)),
        "mean_return": float(train_stats["mean"]),
        "standard_deviation": float(train_stats["std"]),
        "minimum_return": float(train_stats["min"]),
        "maximum_return": float(train_stats["max"]),
        "zero_share": float(train_stats["zero_share"]),
        "skewness": float(train_stats["skewness"]),
        "excess_kurtosis": float(train_stats["excess_kurtosis"]),
        "max_abs_acf": float(nonzero_lags["acf"].abs().max()),
        "max_abs_pacf": float(nonzero_lags["pacf"].abs().max()),
        "acf_12": float(lag_12["acf"]),
        "pacf_12": float(lag_12["pacf"]),
        "abs_acf_1": float(magnitude.loc[magnitude["lag"] == 1, "acf_absolute_returns"].iloc[0]),
    }
    (output_dir / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _write_markdown(output_dir / "ENTREGA_31_08.md", summary, stats)
    create_pdf_report(
        output_dir / "ENTREGA_31_08.pdf",
        overview_path,
        correlogram_path,
        dependence_path,
        summary,
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reproduz a entrega de 31/08 da disciplina EAD6034."
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
        default=Path("results/entrega_31_08"),
        help="Diretório de resultados (padrão: results/entrega_31_08).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = run_pipeline(args.input, args.output, SampleConfig())
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
