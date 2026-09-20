from __future__ import annotations

import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from ead6034.multiscale import MultiscaleConfig
from ead6034.trading_time_data import build_trading_time_data


def source_days(days):
    parts = []
    for day, symbol, level in days:
        stamps = pd.date_range(f"{day} 09:00", f"{day} 18:29", freq="min", tz="America/Sao_Paulo")
        # Exactly additive log returns makes cumulative-horizon checking exact.
        close = level * np.exp(np.arange(len(stamps)) * 0.00001)
        parts.append(pd.DataFrame({
            "symbol": symbol, "date": day,
            "candle": stamps.tz_convert("UTC").tz_localize(None),
            "open": close * np.exp(-0.000005), "close": close,
            "high": close * 1.0001, "low": close * 0.9999,
            "volume": 10, "financial_volume": close * 10, "num_trades": 1,
        }))
    return pd.concat(parts, ignore_index=True)


class TradingTimeDataTests(unittest.TestCase):
    def test_returns_exclude_overnight_but_lags_bridge_sessions(self):
        source = source_days([("2024-01-02", "WING24", 100.),
                              ("2024-01-03", "WING24", 200.)])
        frames, coverage, context, meta = build_trading_time_data(source)
        hour = frames["60min"]
        self.assertEqual(len(hour), 18)
        self.assertEqual(hour["sequence_index"].tolist(), list(range(18)))
        self.assertTrue(hour.loc[9, "cross_session_lag1"])
        self.assertEqual(hour.loc[9, "position_in_session"], 0)
        self.assertAlmostEqual(hour.loc[9, "return_pct"], .06, places=10)
        self.assertAlmostEqual(hour["return_pct"].shift().iloc[9], hour.loc[8, "return_pct"])
        self.assertNotIn("segment_id", frames["1d"])
        self.assertEqual(meta["sample_day_counts"], {"train": 2})
        self.assertGreater(context.loc[1, "observed_session_gap_pct"], 60.)
        self.assertTrue(context.loc[1, "observed_session_gap_valid"])

    def test_training_unchanged_when_holdout_prices_are_poisoned(self):
        source = source_days([("2024-12-27", "WING25", 99.),
                              ("2024-12-30", "WING25", 100.),
                              ("2025-01-02", "WING25", 110.)])
        first, cov_a, ctx_a, meta_a = build_trading_time_data(source)
        poisoned = source.copy()
        poison = poisoned["date"].str.startswith("2025")
        price_columns = ["open", "high", "low", "close", "financial_volume"]
        # Change both price levels AND the return path, not just numeraire.
        factors = 1000 * np.exp(np.linspace(0, 2, int(poison.sum())))
        poisoned.loc[poison, price_columns] = (
            poisoned.loc[poison, price_columns].to_numpy() * factors[:, None])
        second, cov_b, ctx_b, meta_b = build_trading_time_data(poisoned)
        for scale in first:
            assert_frame_equal(first[scale].query("sample == 'train'"),
                               second[scale].query("sample == 'train'"))
        assert_frame_equal(cov_a.query("sample == 'train'"), cov_b.query("sample == 'train'"))
        assert_frame_equal(ctx_a.query("sample == 'train'"), ctx_b.query("sample == 'train'"))
        self.assertEqual(meta_a["minute_profile_2024"], meta_b["minute_profile_2024"])
        self.assertEqual(meta_a["audits"]["train"], meta_b["audits"]["train"])
        self.assertEqual(meta_a["absolute_gap_threshold_train"], meta_b["absolute_gap_threshold_train"])
        self.assertFalse(np.allclose(first["60min"].query("sample == 'test'")["return_pct"],
                                     second["60min"].query("sample == 'test'")["return_pct"]))

    def test_rolls_missing_weekdays_and_excluded_source_days_flagged(self):
        source = source_days([("2024-01-02", "WING24", 100.),
                              ("2024-01-03", "WINJ24", 200.),
                              ("2024-01-05", "WINJ24", 201.),
                              ("2024-01-08", "WINJ24", 202.),
                              ("2024-01-09", "WINJ24", 203.)])
        # Remove one minute from 8 January; excluded from ALL six scales.
        missing = pd.Timestamp("2024-01-08 12:00", tz="America/Sao_Paulo").tz_convert("UTC").tz_localize(None)
        source = source.loc[source["candle"].ne(missing)]
        frames, coverage, context, _ = build_trading_time_data(source)
        ctx = context.set_index("date")
        self.assertTrue(ctx.loc["2024-01-03", "roll_transition"])
        self.assertTrue(pd.isna(ctx.loc["2024-01-03", "observed_session_gap_pct"]))
        self.assertEqual(ctx.loc["2024-01-05", "source_missing_days_between"], 1)
        self.assertTrue(pd.isna(ctx.loc["2024-01-05", "observed_session_gap_pct"]))
        for frame in frames.values():
            self.assertNotIn("2024-01-08", set(frame["date"]))
            last = frame.loc[frame["date"].eq("2024-01-09")].iloc[0]
            self.assertEqual(last["excluded_source_days_between"], 1)
            self.assertEqual(last["calendar_gap_days"], 4)
            self.assertTrue(last["cross_session_lag1"])

    def test_hourly_target_identity_and_equal_time_bands(self):
        frames, _, _, _ = build_trading_time_data(source_days([
            ("2024-01-02", "WING24", 100.), ("2024-01-03", "WING24", 200.)]))
        reference = frames["60min"].set_index("timestamp")["return_pct"]
        for scale, count in (("1min", 60), ("5min", 12), ("15min", 4), ("30min", 2), ("60min", 1)):
            frame = frames[scale]
            targets = (frame.assign(hour=frame["position_in_session"] // count)
                       .groupby(["date", "hour"], observed=True)
                       .agg(timestamp=("timestamp", "max"), target=("return_pct", "sum"))
                       .set_index("timestamp")["target"])
            np.testing.assert_allclose(targets, reference.loc[targets.index], rtol=0, atol=1e-10)
            by_band = frame.groupby("time_band").size()
            self.assertEqual(by_band["inicio"], count * 2)
            self.assertEqual(by_band["fim"], count * 2)
            self.assertEqual(by_band["meio"], count * 7 * 2)

    def test_filter_before_audit_and_no_future_gap_labels(self):
        source = source_days([("2023-12-29", "WING24", 100.),
                              ("2024-01-02", "WING24", 101.)])
        source.loc[source["date"].eq("2023-12-29"), "low"] = 1e9
        frames, _, context, metadata = build_trading_time_data(source)
        self.assertEqual(metadata["audits"]["train"]["invalid_ohlc_rows"], 0)
        self.assertTrue(context["observed_session_gap_pct"].isna().all())
        self.assertEqual(context.loc[0, "rows_before_window"], 5)
        self.assertEqual(context.loc[0, "rows_at_or_after_window_end"], 25)

    def test_minute_profile_suppresses_low_count_private_returns(self):
        _, _, _, metadata = build_trading_time_data(source_days([
            ("2024-01-02", "WING24", 100.), ("2024-01-03", "WING24", 101.)]))
        self.assertEqual(metadata["minute_profile_minimum_returns_for_statistics"], 10)
        for row in metadata["minute_profile_2024"]:
            self.assertTrue(row["return_statistics_suppressed"])
            self.assertLess(row["returns_n"], 10)
            for column in ("mean_return_pct", "std_return_pct", "mean_abs_return_pct"):
                self.assertIsNone(row[column])

        days = [(day.strftime("%Y-%m-%d"), "WING24", 100. + i)
                for i, day in enumerate(pd.bdate_range("2024-01-02", periods=10))]
        _, _, _, metadata = build_trading_time_data(source_days(days))
        profile = {row["clock"]: row for row in metadata["minute_profile_2024"]}
        self.assertTrue(profile["09:00"]["return_statistics_suppressed"])
        self.assertFalse(profile["09:01"]["return_statistics_suppressed"])
        self.assertIsNotNone(profile["09:01"]["mean_return_pct"])


if __name__ == "__main__":
    unittest.main()
