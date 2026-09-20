import unittest

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from ead6034.forecast_evaluation import diebold_mariano, evaluate_scale, forecast_fixed


def frame_fixture(minutes=30, days=("2024-12-30", "2025-01-02", "2025-01-03")):
    rows = []
    for day in days:
        starts = pd.date_range(f"{day} 09:05", periods=540 // minutes, freq=f"{minutes}min", tz="America/Sao_Paulo")
        for position, start in enumerate(starts):
            elapsed = position * minutes
            rows.append({
                "timestamp": start + pd.Timedelta(minutes=minutes), "bar_start": start,
                "date": day, "sample": "train" if day.startswith("2024") else "test",
                "time_band": "first_hour" if elapsed < 60 else "last_hour" if elapsed >= 480 else "middle",
                "position_in_session": position, "return_pct": (len(rows) % 7 - 3) / 10,
            })
    return pd.DataFrame(rows)


class TestFixedForecasts(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(6034)
        innovations = rng.normal(size=120)
        self.y = np.zeros(120)
        for t in range(1, len(self.y)):
            self.y[t] = .12 + .4 * self.y[t - 1] + innovations[t] + .3 * innovations[t - 1]

    def test_matches_append_forecast_with_exact_state_initialization(self):
        for order in ((0, 0, 0), (1, 0, 0), (0, 0, 2), (2, 0, 1)):
            result = ARIMA(self.y[:70], order=order, trend="c").fit()
            actual = forecast_fixed(result, self.y, 70, 5)
            self.assertTrue(np.isnan(actual[:70]).all())
            for origin in (70, 71, 90, 119):
                reference = result if origin == 70 else result.append(self.y[70:origin], refit=False)
                np.testing.assert_allclose(actual[origin], reference.forecast(5), atol=1e-10, rtol=1e-9)

    def test_poisoned_future_cannot_affect_current_multistep_forecast(self):
        result = ARIMA(self.y[:70], order=(2, 0, 1)).fit()
        original = forecast_fixed(result, self.y, 70, 7)
        poisoned = self.y.copy()
        poisoned[90:] += np.arange(30) * 1000 + 999
        other = forecast_fixed(result, poisoned, 70, 7)
        np.testing.assert_array_equal(original[70:91], other[70:91])
        self.assertFalse(np.allclose(original[91], other[91]))

    def test_rejects_fitted_holdout_and_changed_training_prefix(self):
        result = ARIMA(self.y[:70], order=(1, 0, 0)).fit()
        with self.assertRaises(ValueError):
            forecast_fixed(result, self.y, 71, 2)
        changed = self.y.copy()
        changed[0] += 1
        with self.assertRaises(ValueError):
            forecast_fixed(result, changed, 70, 2)

    def test_multi_step_ar_recursion_uses_same_origin(self):
        result = ARIMA(self.y[:70], order=(1, 0, 0)).fit()
        mu, phi = result.params[:2]
        predictions = forecast_fixed(result, self.y, 70, 5)
        expected = mu + phi ** np.arange(1, 6) * (self.y[79] - mu)
        np.testing.assert_allclose(predictions[80], expected, atol=1e-10)


class TestEvaluation(unittest.TestCase):
    def test_common_hour_uses_origin_specific_multistep_sum(self):
        frame = frame_fixture()
        ar = np.column_stack((np.arange(len(frame), dtype=float), np.full(len(frame), 1000.)))
        ma = ar / 2
        private, metrics, dm = evaluate_scale(frame, {"AR_BIC": ar, "MA_BIC": ma}, "30min")
        common = private[(private.model == "AR_BIC") & (private.evaluation == "common_60min")]
        self.assertEqual(len(common), 18)
        self.assertEqual(common.prediction.iloc[0], 18 + 1000)
        self.assertNotEqual(common.prediction.iloc[0], 18 + 19)
        self.assertAlmostEqual(common.actual.iloc[0], frame.return_pct.iloc[18:20].sum())
        self.assertTrue((common.target_end - common.target_start).eq(pd.Timedelta(hours=1)).all())
        self.assertTrue(common.target_start.dt.date.eq(common.target_end.dt.date).all())
        self.assertTrue(common.target_end.dt.year.eq(2025).all())
        self.assertTrue(common.groupby("date").size().eq(9).all())
        self.assertTrue(dm.loc[dm.evaluation.eq("common_60min"), "h_loss"].eq(1).all())
        self.assertTrue(dm.loc[dm.evaluation.eq("common_60min"), "horizon_bars"].eq(2).all())
        self.assertEqual(metrics.loc[(metrics.model == "ZERO") & (metrics.group_type == "all"), "mse_ratio_vs_zero"].tolist(), [1., 1.])

    def test_fixed_equal_weight_combination_and_all_models_same_targets(self):
        frame = frame_fixture(60)
        ar, ma = np.full((len(frame), 1), .2), np.full((len(frame), 1), .6)
        ar[10] = np.nan
        private, metrics, _ = evaluate_scale(frame, {"AR_BIC": ar, "MA_BIC": ma}, "60min")
        combination = private[private.model == "AR_MA_50_50"]
        np.testing.assert_allclose(combination.prediction, .4)
        all_metrics = metrics[metrics.group_type == "all"]
        self.assertTrue(all_metrics.n.eq(17).all())
        self.assertTrue(all_metrics.n_dropped_nonfinite_all.eq(1).all())

    def test_common_hour_does_not_cross_session_or_missing_bar(self):
        frame = frame_fixture(30)
        # Remove the second bar of the first test day: its first hourly target
        # must disappear, not be completed using a later bar or another day.
        frame = frame.drop(index=19).reset_index(drop=True)
        private, _, _ = evaluate_scale(frame, {"ARMA_BIC": np.zeros((len(frame), 2))}, "30min")
        common = private[(private.model == "ARMA_BIC") & (private.evaluation == "common_60min")]
        self.assertEqual(len(common), 17)
        self.assertTrue(common.target_end.dt.date.eq(common.target_start.dt.date).all())

    def test_common_origins_align_across_all_intraday_scales(self):
        origin_sets = []
        for minutes in (1, 5, 15, 30, 60):
            frame = frame_fixture(minutes)
            private, _, _ = evaluate_scale(frame, {}, f"{minutes}min")
            common = private[(private.model == "ZERO") & (private.evaluation == "common_60min")]
            origin_sets.append(common.origin.tolist())
        for origins in origin_sets[1:]:
            self.assertEqual(origins, origin_sets[0])

    def test_daily_only_native_and_preassigned_gap_groups(self):
        frame = frame_fixture(540)
        context = pd.DataFrame({"date": frame.date, "gap_group": ["low", "high", "low"]})
        private, metrics, _ = evaluate_scale(frame, {}, "1d", context)
        self.assertEqual(private.evaluation.unique().tolist(), ["native"])
        self.assertEqual(set(metrics.loc[metrics.group_type == "gap_group", "group"]), {"high", "low"})
        self.assertFalse(metrics.group_type.eq("time_band").any())

    def test_rejects_holdout_other_than_2025(self):
        frame = frame_fixture(days=("2024-12-30", "2026-01-02"))
        with self.assertRaises(ValueError):
            evaluate_scale(frame, {}, "30min")


class TestDieboldMariano(unittest.TestCase):
    def test_symmetry_and_hln_lecture_formula(self):
        a = np.array([.1, .2, -.8, .3, .1, -.2])
        b = np.array([.2, .3, -.2, .5, .6, .1])
        ab = diebold_mariano(a, b, q=0)
        ba = diebold_mariano(b, a, q=0)
        d = a ** 2 - b ** 2
        expected = d.mean() * np.sqrt((len(d) - 1) / d.var())
        self.assertAlmostEqual(ab["statistic"], expected)
        self.assertAlmostEqual(ab["statistic"], -ba["statistic"])
        self.assertAlmostEqual(ab["p_value"], ba["p_value"])

    def test_identical_and_zero_variance_have_no_test(self):
        identical = diebold_mariano(np.ones(10), np.ones(10))
        constant_difference = diebold_mariano(np.ones(10), np.zeros(10))
        self.assertEqual(identical["status"], "identical_losses")
        self.assertTrue(np.isnan(identical["p_value"]))
        self.assertTrue(np.isnan(constant_difference["p_value"]))

    def test_rectangular_covariances_and_negative_lrv_not_forced_positive(self):
        a = np.sqrt(np.array([2., 0., 2., 0., 2., 0., 2., 0.]))
        b = np.ones(8)
        result = diebold_mariano(a, b, q=1)
        self.assertLess(result["long_run_variance"], 0)
        self.assertTrue(np.isnan(result["p_value"]))
        self.assertEqual(result["q"], 1)


if __name__ == "__main__":
    unittest.main()
