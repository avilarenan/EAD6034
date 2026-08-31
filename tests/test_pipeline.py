from __future__ import annotations

import numpy as np
import pandas as pd
import unittest

from ead6034.analysis import chronological_split, correlogram, dependence_in_magnitude
from ead6034.data import SampleConfig, build_five_minute_bars


def _synthetic_minutes() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    days = [("2024-01-02", "WING24", 100_000.0), ("2025-01-02", "WING25", 150_000.0)]
    for day, symbol, base in days:
        local = pd.date_range(
            f"{day} 09:05", f"{day} 18:24", freq="1min", tz="America/Sao_Paulo"
        )
        prices = base + np.arange(len(local), dtype=float) * 5.0
        for timestamp, price in zip(local, prices):
            rows.append(
                {
                    "symbol": symbol,
                    "candle": timestamp.tz_convert("UTC").tz_localize(None),
                    "date": day,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 10,
                    "financial_volume": price * 10,
                    "num_trades": 1,
                }
            )
    return pd.DataFrame(rows)


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = SampleConfig(
            start_date="2024-01-01",
            end_date="2025-01-03",
            train_end_date="2024-12-31",
            test_start_date="2025-01-01",
        )

    def test_returns_never_cross_day_or_contract(self) -> None:
        bars, coverage = build_five_minute_bars(_synthetic_minutes(), self.config)
        self.assertTrue(coverage["included"].all())
        missing_first = bars.groupby("date")["return_pct"].apply(lambda x: x.isna().sum())
        self.assertTrue((missing_first == 1).all())
        self.assertTrue(bars.groupby("date").size().eq(112).all())
        self.assertLess(bars.dropna(subset=["return_pct"])["return_pct"].abs().max(), 0.05)

    def test_calendar_split_locks_2025(self) -> None:
        bars, _ = build_five_minute_bars(_synthetic_minutes(), self.config)
        train, test, train_end, test_start = chronological_split(
            bars, self.config.train_end_date, self.config.test_start_date
        )
        self.assertEqual(set(train["date"]), {"2024-01-02"})
        self.assertEqual(set(test["date"]), {"2025-01-02"})
        self.assertEqual(train_end, "2024-01-02")
        self.assertEqual(test_start, "2025-01-02")

    def test_correlogram_stays_inside_sessions(self) -> None:
        rng = np.random.default_rng(42)
        frame = pd.DataFrame(
            {
                "date": np.repeat(["2024-01-02", "2024-01-03"], 120),
                "return_pct": rng.normal(size=240),
            }
        )
        table = correlogram(frame, max_lag=12)
        self.assertEqual(list(table["lag"]), list(range(13)))
        self.assertEqual(table.loc[table["lag"] == 1, "acf_n_pairs"].iloc[0], 238)
        self.assertTrue(table[["acf", "pacf"]].notna().all().all())

    def test_magnitude_dependence_stays_inside_sessions(self) -> None:
        frame = pd.DataFrame(
            {
                "date": ["2024-01-02"] * 4 + ["2024-01-03"] * 4,
                "return_pct": [1.0, -2.0, 3.0, -4.0, 100.0, -90.0, 80.0, -70.0],
            }
        )
        table = dependence_in_magnitude(frame, max_lag=2)
        self.assertEqual(table.loc[table["lag"] == 1, "n_pairs"].iloc[0], 6)
        self.assertEqual(table.loc[table["lag"] == 2, "n_pairs"].iloc[0], 4)
        self.assertTrue(table[["acf_absolute_returns", "acf_squared_returns"]].notna().all().all())


if __name__ == "__main__":
    unittest.main()
