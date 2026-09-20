"""Trading-observation sequences for the cumulative 21 September delivery.

Returns never cross a session or contract.  Lags and model state deliberately do:
the integer index is *observation time*, not uninterrupted wall-clock time.
Individual prices/returns and the returned daily context are PRIVATE data.
Only coverage and appropriately aggregated audit tables should be published.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from .data import (
    REQUIRED_COLUMNS,
    SampleConfig,
    _to_market_timezone,
    audit_minutes,
    load_win_minutes,
)
from .multiscale import (
    INTRADAY_SCALES,
    MultiscaleConfig,
    build_daily_open_to_close,
    build_multiscale_bars,
)

SCALES = tuple(key for key, _, _ in INTRADAY_SCALES) + ("1d",)
MIN_PROFILE_RETURNS = 10
_AUDIT_ERRORS = (
    "duplicate_symbol_timestamps", "missing_values", "nonpositive_closes",
    "invalid_ohlc_rows", "local_date_mismatches",
)


def _missing_weekdays(previous: str | None, current: str, source_days: set[str]) -> int:
    """Conservative missing weekdays, NOT a claim that the exchange was open.

    Holidays and genuine missing source sessions cannot be distinguished without
    an independently validated historical exchange calendar.  Both are flagged.
    """
    if previous is None:
        return 0
    between = pd.bdate_range(pd.Timestamp(previous) + pd.Timedelta(days=1),
                             pd.Timestamp(current) - pd.Timedelta(days=1))
    return sum(day.strftime("%Y-%m-%d") not in source_days for day in between)


def _daily_context(raw: pd.DataFrame, coverage: pd.DataFrame,
                   config: MultiscaleConfig) -> pd.DataFrame:
    local = raw.copy()
    local["timestamp"] = _to_market_timezone(
        local["candle"], config.source_timezone, config.market_timezone)
    local = local.sort_values("timestamp")
    rows = []
    for day, group in local.groupby("date", sort=True, observed=True):
        times = group["timestamp"]
        clock = times.dt.strftime("%H:%M")
        in_window = clock.ge(config.session_start) & clock.lt(config.session_end)
        # Missing minutes are a property of the source, not verified auctions.
        minutes_between = int((times.iloc[-1] - times.iloc[0]).total_seconds() / 60) + 1
        rows.append({
            "date": day,
            "sample": "train" if day <= config.train_end_date else "test",
            "symbol": group["symbol"].iloc[0],
            "source_first_timestamp": times.iloc[0],
            "source_last_timestamp": times.iloc[-1],
            "source_first_clock": clock.iloc[0],
            "source_last_clock": clock.iloc[-1],
            "source_first_open": float(group["open"].iloc[0]),
            "source_last_close": float(group["close"].iloc[-1]),
            "source_rows": len(group),
            "source_missing_minutes_between_first_last": minutes_between - len(group),
            "rows_before_window": int(clock.lt(config.session_start).sum()),
            "rows_in_window": int(in_window.sum()),
            "rows_at_or_after_window_end": int(clock.ge(config.session_end).sum()),
            "auction_phase_observed": False,
        })
    context = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    source_days = set(context["date"])
    previous = context["date"].shift()
    context["calendar_gap_days"] = (
        pd.to_datetime(context["date"]) - pd.to_datetime(previous)).dt.days.astype("Int64")
    context["source_missing_days_between"] = [
        _missing_weekdays(None if pd.isna(prev) else prev, day, source_days)
        for prev, day in zip(previous, context["date"])
    ]
    context["roll_transition"] = (
        context["symbol"].ne(context["symbol"].shift()) & previous.notna())
    context["known_source_gap_between"] = [
        any(prev < gap < day for gap in config.known_source_gaps)
        if pd.notna(prev) else False
        for prev, day in zip(previous, context["date"])
    ]
    context["observed_session_gap_valid"] = (
        previous.notna() & ~context["roll_transition"]
        & context["source_missing_days_between"].eq(0)
        & ~context["known_source_gap_between"])
    context["observed_session_gap_pct"] = (
        100.0 * np.log(context["source_first_open"] / context["source_last_close"].shift())
    ).where(context["observed_session_gap_valid"])
    context["observed_gap_elapsed_minutes"] = (
        context["source_first_timestamp"] - context["source_last_timestamp"].shift()
    ).dt.total_seconds() / 60.0
    # The previous close is a candle observation, not a verified market close;
    # the current open is likewise not a verified opening-auction execution.
    context["observed_gap_label"] = "between_source_days_not_verified_overnight"
    context = context.merge(
        coverage[["date", "included", "missing_minutes", "anchor_available"]],
        on="date", how="left", validate="one_to_one")
    train_gaps = context.loc[context["sample"].eq("train") & context["included"],
                             "observed_session_gap_pct"].abs().dropna()
    threshold = float(train_gaps.median()) if len(train_gaps) else np.nan
    context["absolute_gap_threshold_train"] = threshold
    context["gap_group"] = "unavailable"
    if np.isfinite(threshold):
        valid = context["observed_session_gap_pct"].notna()
        context.loc[valid, "gap_group"] = np.where(
            context.loc[valid, "observed_session_gap_pct"].abs().le(threshold), "low", "high")
    return context


def _minute_profile_2024(raw: pd.DataFrame, config: MultiscaleConfig) -> list[dict]:
    """Public-safe training-only minute-of-day aggregates, never price levels."""
    minute = raw.loc[raw["date"].le(config.train_end_date)].copy()
    if minute.empty:
        return []
    minute["timestamp"] = _to_market_timezone(
        minute["candle"], config.source_timezone, config.market_timezone)
    minute = minute.sort_values("timestamp")
    adjacent = (minute["date"].eq(minute["date"].shift())
                & minute["symbol"].eq(minute["symbol"].shift())
                & minute["timestamp"].diff().eq(pd.Timedelta(minutes=1)))
    minute["return_pct"] = (100.0 * np.log(
        minute["close"].astype(float) / minute["close"].shift())).where(adjacent)
    minute["abs_return_pct"] = minute["return_pct"].abs()
    minute["clock"] = minute["timestamp"].dt.strftime("%H:%M")
    profile = minute.groupby("clock", as_index=False, observed=True).agg(
        observed_days=("date", "nunique"),
        returns_n=("return_pct", "count"),
        mean_return_pct=("return_pct", "mean"),
        std_return_pct=("return_pct", "std"),
        mean_abs_return_pct=("abs_return_pct", "mean"),
    )
    profile["inside_analysis_window"] = (
        profile["clock"].ge(config.session_start) & profile["clock"].lt(config.session_end))
    # An aggregate of one observation discloses that proprietary observation.
    # Retain source-coverage counts but suppress all low-count return summaries.
    profile["return_statistics_suppressed"] = profile["returns_n"].lt(MIN_PROFILE_RETURNS)
    profile.loc[profile["return_statistics_suppressed"],
                ["mean_return_pct", "std_return_pct", "mean_abs_return_pct"]] = np.nan
    # Explicit nulls are valid strict JSON; no NaN-bearing audit metadata.
    return profile.astype(object).where(profile.notna(), None).to_dict(orient="records")


def _annotate_sequence(frame: pd.DataFrame, scale: str, context: pd.DataFrame,
                       config: MultiscaleConfig) -> pd.DataFrame:
    frame = frame.rename(columns={"segment_id": "prior_segment_id"})
    frame = frame.drop(columns=["source_day_position",
                                "close_to_close_return_pct"], errors="ignore")
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    minutes = dict((key, n) for key, _, n in INTRADAY_SCALES)
    if scale == "1d":
        frame["bar_start"] = pd.to_datetime(frame["date"] + " " + config.session_start).dt.tz_localize(
            config.market_timezone)
        frame["time_band"] = "diario"
    else:
        frame["bar_start"] = frame["timestamp"] - pd.Timedelta(minutes=minutes[scale])
        offset = (frame["bar_start"] - frame["bar_start"].dt.normalize()).dt.total_seconds() / 60
        start_minute = sum(int(v) * m for v, m in zip(config.session_start.split(":"), (60, 1)))
        end_minute = sum(int(v) * m for v, m in zip(config.session_end.split(":"), (60, 1)))
        frame["time_band"] = np.select(
            [offset.lt(start_minute + 60), offset.ge(end_minute - 60)],
            ["inicio", "fim"], default="meio")
    frame["position_in_session"] = frame.groupby("date", observed=True).cumcount()
    frame["bars_per_day"] = frame.groupby("date", observed=True)["date"].transform("size")
    frame["sequence_index"] = np.arange(len(frame), dtype=np.int64)
    frame["cross_session_lag1"] = (
        frame["date"].ne(frame["date"].shift()) & frame.index.to_series().gt(0))
    frame["calendar_gap_days"] = (
        pd.to_datetime(frame["date"]) - pd.to_datetime(frame["date"].shift())
    ).dt.days.astype("Int64")
    frame["roll_transition"] = (
        frame["symbol"].ne(frame["symbol"].shift()) & frame.index.to_series().gt(0))
    frame["source_missing_days_between"] = 0
    frame["excluded_source_days_between"] = 0
    frame["known_source_gap_between"] = False
    source_days = set(context["date"])
    included_days = frame["date"].drop_duplicates().tolist()
    for previous, day in zip(included_days[:-1], included_days[1:]):
        first = frame.index[frame["date"].eq(day)][0]
        frame.loc[first, "source_missing_days_between"] = _missing_weekdays(previous, day, source_days)
        frame.loc[first, "excluded_source_days_between"] = sum(
            previous < source_day < day for source_day in source_days)
        frame.loc[first, "known_source_gap_between"] = any(
            previous < gap < day for gap in config.known_source_gaps)
    gap_map = context.set_index("date")["observed_session_gap_pct"]
    frame["observed_session_gap_pct"] = frame["date"].map(gap_map)
    frame["gap_group"] = frame["date"].map(context.set_index("date")["gap_group"])
    return frame


def build_trading_time_data(
    source: str | Path | pd.DataFrame,
    config: MultiscaleConfig | None = None,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, dict]:
    """Build independent train/test samples, then join in observation time.

    ``source`` may be the original ZIP, extracted directory, WIN parquet, or a
    DataFrame for tests. No estimates, coverage choices or statistics from 2025
    enter 2024 construction. Only backward-looking annotations span the split.
    ``coverage`` is public-safe; ``frames`` and ``daily_context`` are private.
    """
    config = config or MultiscaleConfig()
    if config.train_end_date >= config.test_start_date:
        raise ValueError("Training and test ranges must not overlap")
    if isinstance(source, pd.DataFrame):
        raw, metadata = source.copy(), {"source_sha256": None, "member_name": "in_memory"}
        missing = set(REQUIRED_COLUMNS) - set(raw.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
    else:
        raw, metadata = load_win_minutes(source)
    raw["date"] = raw["date"].astype(str)
    # Must precede audits: unused historical data must not invalidate the sample.
    raw = raw.loc[raw["date"].between(config.start_date, config.end_date)].copy()
    raw = raw.loc[raw["date"].le(config.train_end_date)
                  | raw["date"].ge(config.test_start_date)].copy()
    if raw.empty:
        raise ValueError("No observations inside the requested sample")
    pieces: dict[str, list[pd.DataFrame]] = {scale: [] for scale in SCALES}
    coverages = []
    audits = {}
    for label, subset in (
        ("train", raw.loc[raw["date"].le(config.train_end_date)].copy()),
        ("test", raw.loc[raw["date"].ge(config.test_start_date)].copy()),
    ):
        if subset.empty:
            continue
        audit = audit_minutes(subset, SampleConfig(
            start_date=str(subset["date"].min()), end_date=str(subset["date"].max()),
            source_timezone=config.source_timezone, market_timezone=config.market_timezone))
        if audit["maximum_symbols_per_day"] != 1:
            raise ValueError(f"{label}: multiple active symbols per source day")
        for key in _AUDIT_ERRORS:
            if audit[key]:
                raise ValueError(f"{label} audit failed: {key}={audit[key]}")
        if (subset[["open", "high", "low", "close"]] <= 0).any().any():
            raise ValueError(f"{label}: nonpositive OHLC price")
        audits[label] = audit
        subconfig = replace(config, start_date=str(subset["date"].min()),
                            end_date=str(subset["date"].max()))
        bars, coverage = build_multiscale_bars(subset, subconfig)
        bars["1d"] = build_daily_open_to_close(bars["1min"], coverage, subconfig)
        coverage["sample"] = label
        coverages.append(coverage)
        for scale, frame in bars.items():
            frame["sample"] = label
            pieces[scale].append(frame)
    coverage = pd.concat(coverages, ignore_index=True).sort_values("date").reset_index(drop=True)
    context = _daily_context(raw, coverage, config)
    frames = {scale: _annotate_sequence(pd.concat(parts, ignore_index=True), scale, context, config)
              for scale, parts in pieces.items()}
    metadata.update({
        "config": asdict(config), "audits": audits,
        "sample_day_counts": coverage.groupby("sample", observed=True)["included"].sum().astype(int).to_dict(),
        "sample_row_counts": {scale: frame.groupby("sample", observed=True).size().to_dict()
                              for scale, frame in frames.items()},
        "trading_time_convention": "chronological_observations_cross_session_lags_no_overnight_return",
        "parameter_estimation_uses_holdout": False,
        "source_gap_convention": "unobserved_weekdays_conservatively_flagged_no_exchange_calendar",
        "auction_identification": "not_available_in_source_columns",
        "observed_gap_convention": "first_open_current_source_day_vs_last_close_previous_source_day_same_symbol_only",
        "absolute_gap_threshold_train": (
            float(context["absolute_gap_threshold_train"].iloc[0])
            if pd.notna(context["absolute_gap_threshold_train"].iloc[0]) else None),
        "gap_group_convention": "low_at_or_below_training_included_days_median_absolute_observed_gap_high_above",
        "minute_profile_2024": _minute_profile_2024(raw, config),
        "minute_profile_minimum_returns_for_statistics": MIN_PROFILE_RETURNS,
        "private_columns_warning": "frames and daily_context include proprietary prices/returns; do not publish",
    })
    return frames, coverage, context, metadata
