from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ead6034.analysis import chronological_split, correlogram
from ead6034.multiscale import (
    MultiscaleConfig,
    build_daily_open_to_close,
    build_multiscale_bars,
)


def _complete_minutes(
    days: list[tuple[str, str, float]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for day, symbol, base in days:
        local = pd.date_range(
            f"{day} 09:04", f"{day} 18:04", freq="1min", tz="America/Sao_Paulo"
        )
        prices = base + np.arange(len(local), dtype=float)
        for timestamp, price in zip(local, prices):
            rows.append(
                {
                    "symbol": symbol,
                    "candle": timestamp.tz_convert("UTC").tz_localize(None),
                    "date": day,
                    "open": price - 0.25,
                    "high": price + 0.5,
                    "low": price - 0.5,
                    "close": price,
                    "volume": 10,
                    "financial_volume": price * 10,
                    "num_trades": 1,
                }
            )
    return pd.DataFrame(rows)


class MultiscaleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = MultiscaleConfig(
            start_date="2024-01-01",
            end_date="2025-01-03",
            train_end_date="2024-12-31",
            test_start_date="2025-01-01",
            known_source_gaps=(),
        )

    def test_common_window_alignment_and_counts(self) -> None:
        source = _complete_minutes([("2024-01-02", "WING24", 100_000.0)])
        bars, coverage = build_multiscale_bars(source, self.config)
        self.assertTrue(coverage["included"].all())
        expected = {
            "1min": (540, "09:06"),
            "5min": (108, "09:10"),
            "15min": (36, "09:20"),
            "30min": (18, "09:35"),
            "60min": (9, "10:05"),
        }
        for scale, (count, first_clock) in expected.items():
            self.assertEqual(len(bars[scale]), count)
            self.assertEqual(bars[scale]["timestamp"].iloc[0].strftime("%H:%M"), first_clock)
            self.assertEqual(bars[scale]["timestamp"].iloc[-1].strftime("%H:%M"), "18:05")
            self.assertFalse(bars[scale]["return_pct"].isna().any())

    def test_one_missing_minute_excludes_day_from_every_scale(self) -> None:
        source = _complete_minutes(
            [
                ("2024-01-02", "WING24", 100_000.0),
                ("2024-01-03", "WING24", 101_000.0),
            ]
        )
        missing = pd.Timestamp("2024-01-03 12:00", tz="America/Sao_Paulo")
        missing_utc = missing.tz_convert("UTC").tz_localize(None)
        source = source.loc[source["candle"] != missing_utc].copy()
        bars, coverage = build_multiscale_bars(source, self.config)
        excluded = coverage.loc[~coverage["included"], "date"].tolist()
        self.assertEqual(excluded, ["2024-01-03"])
        for frame in bars.values():
            self.assertEqual(set(frame["date"]), {"2024-01-02"})

    def test_daily_open_to_close_and_intraday_reconciliation(self) -> None:
        source = _complete_minutes(
            [
                ("2024-01-02", "WING24", 100_000.0),
                ("2024-01-03", "WING24", 101_000.0),
                ("2024-01-04", "WINJ24", 120_000.0),
            ]
        )
        bars, coverage = build_multiscale_bars(source, self.config)
        daily = build_daily_open_to_close(bars["1min"], coverage, self.config)
        daily_indexed = daily.set_index("date")
        expected_open_to_close = 100.0 * np.log(
            daily_indexed["session_close"] / daily_indexed["session_open"]
        )
        np.testing.assert_allclose(daily_indexed["return_pct"], expected_open_to_close)
        for scale, frame in bars.items():
            summed = frame.groupby("date")["return_pct"].sum()
            np.testing.assert_allclose(
                daily_indexed.loc[summed.index, "boundary_to_close_return_pct"],
                summed,
                err_msg=f"Soma inconsistente na escala {scale}",
            )
        np.testing.assert_allclose(
            daily_indexed["boundary_to_close_return_pct"],
            daily_indexed["boundary_to_open_return_pct"]
            + daily_indexed["return_pct"],
        )
        self.assertEqual(daily["segment_id"].tolist(), [1, 1, 2])
        self.assertEqual(int(daily["close_to_close_return_pct"].notna().sum()), 1)

    def test_daily_correlogram_and_holdout(self) -> None:
        source = _complete_minutes(
            [
                ("2024-01-02", "WING24", 100_000.0),
                ("2024-01-03", "WING24", 101_000.0),
                ("2024-01-04", "WING24", 102_000.0),
                ("2025-01-02", "WING25", 120_000.0),
                ("2025-01-03", "WING25", 121_000.0),
            ]
        )
        bars, coverage = build_multiscale_bars(source, self.config)
        daily = build_daily_open_to_close(bars["1min"], coverage, self.config)
        train, test, _, _ = chronological_split(
            daily, self.config.train_end_date, self.config.test_start_date
        )
        self.assertEqual(set(train["date"]), {"2024-01-02", "2024-01-03", "2024-01-04"})
        self.assertEqual(set(test["date"]), {"2025-01-02", "2025-01-03"})
        table = correlogram(
            train,
            max_lag=1,
            session_column="segment_id",
            acf_normalization="pairwise",
        )
        self.assertEqual(int(table.loc[table["lag"] == 1, "acf_n_pairs"].iloc[0]), 2)

    def test_pairwise_acf_uses_valid_pairs_without_attenuation(self) -> None:
        frame = pd.DataFrame(
            {
                "date": ["2024-01-02"] * 3 + ["2024-01-03"] * 3,
                "return_pct": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            }
        )
        table = correlogram(
            frame,
            max_lag=1,
            session_column="date",
            acf_normalization="pairwise",
        )
        self.assertAlmostEqual(float(table.loc[1, "acf"]), 1.0)
        self.assertEqual(int(table.loc[1, "acf_n_pairs"]), 4)

    def test_known_source_gap_breaks_daily_segment(self) -> None:
        config = MultiscaleConfig(
            start_date="2024-01-01",
            end_date="2025-01-03",
            train_end_date="2024-12-31",
            test_start_date="2025-01-01",
            known_source_gaps=("2024-01-03",),
        )
        source = _complete_minutes(
            [
                ("2024-01-02", "WING24", 100_000.0),
                ("2024-01-04", "WING24", 101_000.0),
            ]
        )
        bars, coverage = build_multiscale_bars(source, config)
        daily = build_daily_open_to_close(bars["1min"], coverage, config)
        self.assertEqual(daily["segment_id"].tolist(), [1, 2])

    def test_invalid_multiscale_configuration_fails_early(self) -> None:
        with self.assertRaisesRegex(ValueError, "separação física comum"):
            MultiscaleConfig(comparison_horizon_minutes=0)
        with self.assertRaisesRegex(ValueError, "daily_max_lag"):
            MultiscaleConfig(daily_max_lag=0)


if __name__ == "__main__":
    unittest.main()
