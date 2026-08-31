from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import _clock_to_timestamp, _to_market_timezone, select_active_contract


INTRADAY_SCALES: tuple[tuple[str, str, int], ...] = (
    ("1min", "1 minuto", 1),
    ("5min", "5 minutos", 5),
    ("15min", "15 minutos", 15),
    ("30min", "30 minutos", 30),
    ("60min", "60 minutos", 60),
)


@dataclass(frozen=True)
class MultiscaleConfig:
    start_date: str = "2024-01-01"
    end_date: str = "2025-11-28"
    source_timezone: str = "UTC"
    market_timezone: str = "America/Sao_Paulo"
    session_start: str = "09:05"
    # Nove horas: janela comum divisível por 1, 5, 15, 30 e 60 minutos.
    session_end: str = "18:05"
    train_end_date: str = "2024-12-31"
    test_start_date: str = "2025-01-01"
    comparison_horizon_minutes: int = 60
    daily_max_lag: int = 15
    # Lacuna sem qualquer linha em WIN/WDO/DI1, identificada na auditoria.
    known_source_gaps: tuple[str, ...] = ("2024-04-16",)

    def __post_init__(self) -> None:
        start = pd.Timestamp(f"2000-01-01 {self.session_start}")
        end = pd.Timestamp(f"2000-01-01 {self.session_end}")
        duration_minutes = int((end - start).total_seconds() // 60)
        if duration_minutes <= 0:
            raise ValueError("A janela intradiária deve ter duração positiva.")
        for _, _, bar_minutes in INTRADAY_SCALES:
            if duration_minutes % bar_minutes != 0:
                raise ValueError(
                    "A janela intradiária deve ser divisível por todas as escalas."
                )
            if self.comparison_horizon_minutes % bar_minutes != 0:
                raise ValueError(
                    "A separação física comum deve ser divisível por todas as escalas."
                )
        if not 0 < self.comparison_horizon_minutes < duration_minutes:
            raise ValueError(
                "A separação física comum deve ficar entre zero e a duração da sessão."
            )
        if self.daily_max_lag <= 0:
            raise ValueError("daily_max_lag deve ser positivo.")


def _frequency_map() -> dict[str, int]:
    return {key: minutes for key, _, minutes in INTRADAY_SCALES}


def build_multiscale_bars(
    minutes: pd.DataFrame,
    config: MultiscaleConfig,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Constrói barras alinhadas e comparáveis usando apenas pregões completos.

    A cobertura é aferida uma única vez na grade de 1 minuto. O preço de
    fronteira em 09:05 é o fechamento do candle iniciado às 09:04; assim, o
    primeiro retorno de cada escala cobre integralmente seu primeiro bloco e
    nenhum retorno atravessa pregão ou contrato.
    """

    frame = minutes.copy()
    frame["date"] = frame["date"].astype(str)
    frame = frame.loc[
        (frame["date"] >= config.start_date) & (frame["date"] <= config.end_date)
    ].copy()
    if frame.empty:
        raise ValueError("A janela solicitada não possui observações de WIN.")

    frame["timestamp"] = _to_market_timezone(
        frame["candle"], config.source_timezone, config.market_timezone
    )
    frame, active = select_active_contract(frame)
    active_symbol = active.set_index("date")["symbol"].to_dict()

    rows_by_scale: dict[str, list[pd.DataFrame]] = {
        key: [] for key, _, _ in INTRADAY_SCALES
    }
    coverage_rows: list[dict[str, object]] = []

    for day, raw_group in frame.groupby("date", sort=True, observed=True):
        group = raw_group.set_index("timestamp").sort_index()
        start = _clock_to_timestamp(day, config.session_start, config.market_timezone)
        end = _clock_to_timestamp(day, config.session_end, config.market_timezone)
        expected_minutes = pd.date_range(
            start=start, end=end - pd.Timedelta(minutes=1), freq="1min"
        )
        intraday = group.loc[(group.index >= start) & (group.index < end)]
        observed_index = pd.DatetimeIndex(intraday.index.unique())
        missing_minutes = expected_minutes.difference(observed_index)

        anchor_time = start - pd.Timedelta(minutes=1)
        anchor = group.loc[group.index == anchor_time]
        anchor_available = len(anchor) == 1
        included = bool(anchor_available and len(missing_minutes) == 0)

        coverage_rows.append(
            {
                "date": day,
                "symbol": active_symbol[day],
                "observed_minutes": int(len(observed_index.intersection(expected_minutes))),
                "expected_minutes": int(len(expected_minutes)),
                "missing_minutes": int(len(missing_minutes)),
                "anchor_available": anchor_available,
                "coverage": float(
                    len(observed_index.intersection(expected_minutes))
                    / len(expected_minutes)
                ),
                "included": included,
            }
        )
        if not included:
            continue

        anchor_close = float(anchor["close"].iloc[0])
        if anchor_close <= 0:
            raise ValueError(f"Preço de fronteira não positivo em {day}.")

        for key, _, bar_minutes in INTRADAY_SCALES:
            frequency = pd.Timedelta(minutes=bar_minutes)
            duration = end - start
            if duration % frequency != pd.Timedelta(0):
                raise ValueError(
                    f"A janela {config.session_start}-{config.session_end} "
                    f"não é divisível por {key}."
                )
            labels = pd.date_range(start=start + frequency, end=end, freq=frequency)
            bars = intraday.resample(
                frequency,
                closed="left",
                label="right",
                origin=start,
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
            if bars["close"].isna().any() or len(bars) != len(labels):
                raise ValueError(
                    f"Pregão completo {day} gerou barra vazia na escala {key}."
                )

            closes = bars["close"].astype(float).to_numpy()
            previous = np.concatenate(([anchor_close], closes[:-1]))
            bars["return_pct"] = 100.0 * np.log(closes / previous)
            bars["anchor_close"] = anchor_close
            bars["date"] = day
            bars["scale"] = key
            bars["was_observed"] = True
            bars.index.name = "timestamp"
            rows_by_scale[key].append(bars.reset_index())

    if not all(rows_by_scale.values()):
        raise ValueError("Nenhum pregão completo foi encontrado para todas as escalas.")

    result = {
        key: pd.concat(parts, ignore_index=True).sort_values("timestamp")
        for key, parts in rows_by_scale.items()
    }
    for bars in result.values():
        bars["sample"] = "unassigned"
    coverage = pd.DataFrame(coverage_rows).sort_values("date").reset_index(drop=True)
    return result, coverage


def build_daily_open_to_close(
    one_minute_bars: pd.DataFrame,
    coverage: pd.DataFrame,
    config: MultiscaleConfig,
) -> pd.DataFrame:
    """Agrega a janela comum em um retorno diário open-to-close.

    O retorno principal usa o `open` da primeira barra às 09:05 e o `close`
    final. A soma telescópica dos retornos intradiários close-to-close é
    preservada separadamente para reconciliação. `segment_id` impede FAC/FACP
    através de sessões excluídas, lacunas conhecidas da fonte ou mudanças de
    contrato.
    """

    daily = (
        one_minute_bars.groupby("date", as_index=False, observed=True)
        .agg(
            timestamp=("timestamp", "max"),
            symbol=("symbol", "first"),
            session_open=("open", "first"),
            boundary_close=("anchor_close", "first"),
            session_close=("close", "last"),
            boundary_to_close_return_pct=("return_pct", "sum"),
            volume=("volume", "sum"),
            observations=("return_pct", "count"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    daily["return_pct"] = 100.0 * np.log(
        daily["session_close"] / daily["session_open"]
    )
    daily["boundary_to_open_return_pct"] = 100.0 * np.log(
        daily["session_open"] / daily["boundary_close"]
    )
    order = coverage.reset_index().set_index("date")["index"]
    daily["source_day_position"] = daily["date"].map(order).astype(int)

    previous_date = pd.to_datetime(daily["date"].shift())
    current_date = pd.to_datetime(daily["date"])
    gap_between = np.zeros(len(daily), dtype=bool)
    for gap in pd.to_datetime(list(config.known_source_gaps)):
        gap_between |= ((previous_date < gap) & (gap < current_date)).fillna(False).to_numpy()

    adjacent_source_day = daily["source_day_position"].diff().eq(1)
    same_symbol = daily["symbol"].eq(daily["symbol"].shift())
    continuation = adjacent_source_day & same_symbol & ~gap_between
    daily["segment_id"] = (~continuation).cumsum().astype(int)

    same_segment = daily["segment_id"].eq(daily["segment_id"].shift())
    daily["close_to_close_return_pct"] = (
        100.0 * np.log(daily["session_close"] / daily["session_close"].shift())
    ).where(same_segment)
    daily["scale"] = "1d"
    daily["sample"] = "unassigned"
    return daily


def scale_minutes(scale: str) -> int | None:
    if scale == "1d":
        return None
    try:
        return _frequency_map()[scale]
    except KeyError as exc:
        raise ValueError(f"Escala desconhecida: {scale}") from exc


def scale_label(scale: str) -> str:
    if scale == "1d":
        return "1 dia"
    labels = {key: label for key, label, _ in INTRADAY_SCALES}
    try:
        return labels[scale]
    except KeyError as exc:
        raise ValueError(f"Escala desconhecida: {scale}") from exc
