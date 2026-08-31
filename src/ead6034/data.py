from __future__ import annotations

import hashlib
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = (
    "symbol",
    "candle",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "financial_volume",
    "num_trades",
)


@dataclass(frozen=True)
class SampleConfig:
    # 2024 e usado para identificacao; 2025 fica reservado para OOS.
    # O ano de 2023 foi descartado apos a auditoria revelar mudanca de horario
    # de negociacao no meio do ano.
    start_date: str = "2024-01-01"
    end_date: str = "2025-11-28"
    source_timezone: str = "UTC"
    market_timezone: str = "America/Sao_Paulo"
    # Em 2024-2025, a sessao regular observada vai de 09:00 a 18:30. Os
    # primeiros cinco minutos e a pausa/leilao final ficam fora da serie.
    session_start: str = "09:05"
    session_end: str = "18:25"
    frequency: str = "5min"
    minimum_daily_coverage: float = 0.95
    train_end_date: str = "2024-12-31"
    test_start_date: str = "2025-01-01"
    max_lag: int = 30


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_win_parquet(directory: Path) -> Path:
    candidates = sorted(directory.rglob("WIN.parquet"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Esperado exatamente um WIN.parquet em {directory}; "
            f"encontrados {len(candidates)}."
        )
    return candidates[0]


def load_win_minutes(source: str | Path) -> tuple[pd.DataFrame, dict[str, object]]:
    """Carrega WIN de um parquet, diretorio extraido ou ZIP original."""

    source = Path(source).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Fonte de dados nao encontrada: {source}")

    metadata: dict[str, object] = {
        "source_sha256": sha256_file(source) if source.is_file() else None,
    }

    if source.is_dir():
        parquet_path = _find_win_parquet(source)
        frame = pd.read_parquet(parquet_path, columns=list(REQUIRED_COLUMNS))
        metadata["member_name"] = str(parquet_path.relative_to(source))
    elif source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            members = [name for name in archive.namelist() if name.endswith("/WIN.parquet")]
            if len(members) != 1:
                raise FileNotFoundError(
                    f"Esperado exatamente um WIN.parquet no ZIP; encontrados {len(members)}."
                )
            metadata["member_name"] = members[0]
            with archive.open(members[0]) as stream:
                frame = pd.read_parquet(stream, columns=list(REQUIRED_COLUMNS))
    elif source.suffix.lower() == ".parquet":
        frame = pd.read_parquet(source, columns=list(REQUIRED_COLUMNS))
        metadata["member_name"] = source.name
    else:
        raise ValueError("Use um arquivo .zip, um WIN.parquet ou um diretorio extraido.")

    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {sorted(missing)}")
    return frame, metadata


def select_active_contract(minutes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida e usa o encadeamento de contrato ativo fornecido no arquivo."""

    symbols_per_day = minutes.groupby("date", observed=True)["symbol"].nunique()
    if int(symbols_per_day.max()) != 1:
        raise ValueError(
            "WIN deveria conter um unico contrato ativo por pregao. "
            "Nao e seguro inferir a rolagem quando ha contratos concorrentes."
        )
    active = (
        minutes.groupby("date", as_index=False, observed=True)
        .agg(symbol=("symbol", "first"), daily_contract_volume=("volume", "sum"))
        .sort_values("date")
        .reset_index(drop=True)
    )
    return minutes.copy(), active


def _to_market_timezone(
    values: pd.Series, source_timezone: str, market_timezone: str
) -> pd.Series:
    """Localiza timestamps ingênuos na origem e converte para o mercado."""

    timestamps = pd.to_datetime(values)
    if timestamps.dt.tz is None:
        timestamps = timestamps.dt.tz_localize(source_timezone)
    return timestamps.dt.tz_convert(market_timezone)


def audit_minutes(minutes: pd.DataFrame, config: SampleConfig) -> dict[str, object]:
    local = _to_market_timezone(
        minutes["candle"], config.source_timezone, config.market_timezone
    )
    local_date = local.dt.strftime("%Y-%m-%d")
    symbols_per_day = minutes.groupby("date", observed=True)["symbol"].nunique()
    invalid_ohlc = (
        (minutes["low"] > minutes["high"])
        | (minutes["open"] < minutes["low"])
        | (minutes["open"] > minutes["high"])
        | (minutes["close"] < minutes["low"])
        | (minutes["close"] > minutes["high"])
    )
    return {
        "raw_rows": int(len(minutes)),
        "raw_start": str(minutes["candle"].min()),
        "raw_end": str(minutes["candle"].max()),
        "trading_days": int(minutes["date"].nunique()),
        "contracts": int(minutes["symbol"].nunique()),
        "maximum_symbols_per_day": int(symbols_per_day.max()),
        "duplicate_symbol_timestamps": int(minutes.duplicated(["symbol", "candle"]).sum()),
        "missing_values": int(minutes[list(REQUIRED_COLUMNS)].isna().sum().sum()),
        "nonpositive_closes": int((minutes["close"] <= 0).sum()),
        "invalid_ohlc_rows": int(invalid_ohlc.sum()),
        "local_date_mismatches": int((minutes["date"].astype(str) != local_date).sum()),
    }


def _clock_to_timestamp(day: str, clock: str, timezone: str) -> pd.Timestamp:
    return pd.Timestamp(f"{day} {clock}", tz=timezone)


def build_five_minute_bars(
    minutes: pd.DataFrame, config: SampleConfig
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Constroi barras regulares e retornos sem atravessar pregao ou rolagem."""

    frame = minutes.copy()
    frame["date"] = frame["date"].astype(str)
    frame = frame.loc[
        (frame["date"] >= config.start_date) & (frame["date"] <= config.end_date)
    ].copy()
    if frame.empty:
        raise ValueError("A janela solicitada nao possui observacoes de WIN.")

    frame["timestamp"] = _to_market_timezone(
        frame["candle"], config.source_timezone, config.market_timezone
    )
    frame, active = select_active_contract(frame)

    frequency = pd.Timedelta(config.frequency)
    expected_rows: list[pd.DataFrame] = []
    coverage_rows: list[dict[str, object]] = []

    for day, group in frame.groupby("date", sort=True, observed=True):
        group = group.set_index("timestamp").sort_index()
        start = _clock_to_timestamp(day, config.session_start, config.market_timezone)
        end = _clock_to_timestamp(day, config.session_end, config.market_timezone)
        labels = pd.date_range(start=start + frequency, end=end, freq=config.frequency)

        intraday = group.loc[(group.index >= start) & (group.index < end)]
        bars = intraday.resample(
            config.frequency, closed="left", label="right", origin="start_day"
        ).agg(
            symbol=("symbol", "last"),
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            financial_volume=("financial_volume", "sum"),
            num_trades=("num_trades", "sum"),
        )
        bars = bars.reindex(labels)
        observed = bars["close"].notna()
        coverage = float(observed.mean())
        coverage_rows.append(
            {
                "date": day,
                "symbol": active.loc[active["date"] == day, "symbol"].iloc[0],
                "observed_bars": int(observed.sum()),
                "expected_bars": int(len(labels)),
                "coverage": coverage,
                "included": bool(coverage >= config.minimum_daily_coverage),
            }
        )
        if coverage < config.minimum_daily_coverage:
            continue

        bars["was_observed"] = observed
        bars["close"] = bars["close"].ffill()
        bars["volume"] = bars["volume"].fillna(0).astype("int64")
        bars["financial_volume"] = bars["financial_volume"].fillna(0.0)
        bars["num_trades"] = bars["num_trades"].fillna(0).astype("int64")
        active_symbol = active.loc[active["date"] == day, "symbol"].iloc[0]
        bars["symbol"] = bars["symbol"].fillna(active_symbol)
        bars["date"] = day
        bars.index.name = "timestamp"
        bars["return_pct"] = 100.0 * np.log(bars["close"]).diff()
        expected_rows.append(bars.reset_index())

    if not expected_rows:
        raise ValueError("Nenhum pregao atingiu a cobertura minima configurada.")

    result = pd.concat(expected_rows, ignore_index=True).sort_values("timestamp")
    result["sample"] = "unassigned"
    coverage_table = pd.DataFrame(coverage_rows)
    return result, coverage_table
