import numpy as np
import pandas as pd
import unittest

from ead6034.variance_evaluation import (
    align_native_variance, evaluate_variance_common_horizon, qlike,
    realized_variance_targets, summed_prediction,
)


def _frame(minutes=30, days=("2024-12-30", "2025-01-02", "2025-01-03")):
    rows = []
    for day in days:
        starts = pd.date_range(f"{day} 09:05", periods=540 // minutes, freq=f"{minutes}min", tz="America/Sao_Paulo")
        for position, start in enumerate(starts):
            rows.append({
                "timestamp": start + pd.Timedelta(minutes=minutes), "bar_start": start,
                "date": day, "sample": "train" if day.startswith("2024") else "test",
                "time_band": "middle", "position_in_session": position,
                "return_pct": (position % 5 - 2) / 10,
            })
    return pd.DataFrame(rows)


class TestRealizedVarianceTargets(unittest.TestCase):
    def test_realized_variance_is_sum_of_squares_over_horizon(self):
        frame = _frame(30)
        origins, horizon, realized = realized_variance_targets(frame, "30min")
        self.assertEqual(horizon, 2)
        y = frame.return_pct.to_numpy(float)
        for origin, value in zip(origins, realized):
            np.testing.assert_allclose(value, np.sum(y[origin:origin + horizon] ** 2))


class TestAlignAndSum(unittest.TestCase):
    def test_align_places_test_variance_at_train_offset(self):
        full = align_native_variance(train_n=3, total_len=7, test_variance=[10., 20., 30., 40.])
        self.assertTrue(np.isnan(full[:3]).all())
        np.testing.assert_allclose(full[3:], [10., 20., 30., 40.])

    def test_align_rejects_overflow(self):
        with self.assertRaises(ValueError):
            align_native_variance(train_n=5, total_len=7, test_variance=[1., 2., 3.])

    def test_summed_prediction_matches_manual_sum(self):
        full_h = np.arange(10, dtype=float)
        origins = np.array([2, 5])
        result = summed_prediction(full_h, origins, horizon=3)
        np.testing.assert_allclose(result, [full_h[2:5].sum(), full_h[5:8].sum()])


class TestQlike(unittest.TestCase):
    def test_zero_at_perfect_forecast(self):
        realized = np.array([1., 2., 3.])
        np.testing.assert_allclose(qlike(realized, realized), 0., atol=1e-12)

    def test_positive_away_from_perfect_forecast(self):
        realized = np.array([1., 2., 3.])
        predicted = np.array([2.5, 2.5, 2.5])  # none coincide with realized
        self.assertTrue((qlike(realized, predicted) > 0).all())


class TestEvaluateVarianceCommonHorizon(unittest.TestCase):
    def test_constant_baseline_and_ratio_columns(self):
        frame = _frame(30)
        origins, horizon, realized = realized_variance_targets(frame, "30min")
        total_len = len(frame)
        constant_path = np.full(total_len, np.nan)
        constant_path[frame["sample"].eq("test").to_numpy()] = float(realized.mean())
        perfect_path = np.full(total_len, np.nan)
        test_mask = frame["sample"].eq("test").to_numpy()
        # A "perfect" per-bar path: constant such that summing over each
        # origin's horizon exactly reproduces that origin's realized value
        # is not generally constructible bar-by-bar, so just reuse constant
        # baseline vs a scaled variant to check ratio columns behave.
        scaled_path = constant_path * 0.5
        private, metrics = evaluate_variance_common_horizon(
            frame, "30min", {"constant": constant_path, "scaled": scaled_path})
        self.assertEqual(set(metrics.model), {"constant", "scaled"})
        self.assertIn("mse_ratio_vs_constant", metrics.columns)
        self.assertAlmostEqual(float(metrics.loc[metrics.model.eq("constant"), "mse_ratio_vs_constant"].iloc[0]), 1.0)
        self.assertIn("predicted_constant", private.columns)
        self.assertIn("realized_variance", private.columns)


if __name__ == "__main__":
    unittest.main()
