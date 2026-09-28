"""Deterministic numerical and holdout-isolation checks for Aula 6."""
import unittest

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox

from ead6034.conditional_volatility import (
    _ljung_box, fit_volatility, forecast_variance, variance_parameters_valid,
)


def _innovations(n=480):
    # Deterministic fixture, not a synthetic empirical dataset or bootstrap.
    t = np.arange(n, dtype=float)
    return .07 * (1 + .4 * np.sin(t / 31)) * (np.sin(t * 1.731) + .4 * np.cos(t * 2.413))


class TestVarianceRecursion(unittest.TestCase):
    def test_manual_garch_recursion(self):
        result = forecast_variance(
            np.array([.3, -.4, .5]), last_residual=.2, last_variance=.05,
            omega=.01, alpha=.2, beta=.5,
        )
        np.testing.assert_allclose(result, [.043, .0495, .06675], atol=1e-14)

    def test_current_and_future_innovations_do_not_affect_current_forecast(self):
        kwargs = dict(last_residual=.2, last_variance=.05, omega=.01, alpha=.2, beta=.5)
        first = forecast_variance(np.array([.3, -.4, .5]), **kwargs)
        poisoned = forecast_variance(np.array([.3, 1000., -2000.]), **kwargs)
        np.testing.assert_array_equal(first[:2], poisoned[:2])
        self.assertNotEqual(first[2], poisoned[2])

    def test_first_forecast_keeps_previous_training_state(self):
        result = forecast_variance(np.array([0.]), last_residual=2., last_variance=4.,
                                   omega=.1, alpha=.2, beta=.7)
        self.assertAlmostEqual(result[0], 3.7)

    def test_positivity_and_strict_stability(self):
        self.assertTrue(variance_parameters_valid(.01, .1, .8))
        self.assertFalse(variance_parameters_valid(0., .1, .8))
        self.assertFalse(variance_parameters_valid(.01, -.1, .8))
        self.assertFalse(variance_parameters_valid(.01, .1, .9))
        self.assertFalse(variance_parameters_valid(.01, .1, .90001))
        self.assertFalse(variance_parameters_valid(.01, np.nan, .8))

    def test_variance_units_follow_squared_innovation_units(self):
        residuals = np.array([.3, -.4, .5])
        first = forecast_variance(residuals, last_residual=.2, last_variance=.05,
                                  omega=.01, alpha=.2, beta=.5)
        factor = 100.
        scaled = forecast_variance(residuals * factor, last_residual=.2 * factor,
                                   last_variance=.05 * factor**2, omega=.01 * factor**2,
                                   alpha=.2, beta=.5)
        np.testing.assert_allclose(scaled, first * factor**2)

    def test_ordinary_ljung_box_matches_statsmodels(self):
        x = _innovations(240)
        actual = _ljung_box(x, [5, 10, 20])
        reference = acorr_ljungbox(x, lags=[5, 10, 20], model_df=0, return_df=True)
        np.testing.assert_allclose(actual.statistic, reference.lb_stat, rtol=1e-12)
        np.testing.assert_allclose(actual.pvalue, reference.lb_pvalue, rtol=1e-12)


class TestConditionalVolatility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        residuals = _innovations(600)
        cls.train, cls.test = residuals[:480], residuals[480:]
        cls.grid, cls.diagnostics, cls.arrays, cls.summary = fit_volatility(
            cls.train, cls.test, "fixture", diagnostic_lags=[5, 10]
        )

    def test_all_candidate_outcomes_and_bic_counts(self):
        self.assertEqual(self.grid.model.tolist(), ["constant", "arch1", "garch11"])
        self.assertEqual(self.grid.variance_parameter_count.tolist(), [1, 2, 3])
        self.assertEqual(int(self.grid.selected_bic.sum()), 1)
        for row in self.grid[self.grid.eligible].itertuples():
            self.assertAlmostEqual(row.bic, -2 * row.loglikelihood + row.variance_parameter_count * np.log(480))
            self.assertTrue(variance_parameters_valid(row.omega, row.alpha, row.beta))

    def test_original_unit_gaussian_likelihood(self):
        for row in self.grid[self.grid.eligible].itertuples():
            h = self.arrays[f"{row.model}_train_variance"]
            reference = -.5 * np.sum(np.log(2 * np.pi) + np.log(h) + self.train**2 / h)
            self.assertAlmostEqual(row.loglikelihood, reference, places=7)

    def test_future_poison_preserves_fit_selection_and_training_diagnostics(self):
        other_grid, other_diag, other_arrays, other_summary = fit_volatility(
            self.train, self.test * 17. + 3., "fixture", diagnostic_lags=[5, 10]
        )
        columns = [c for c in self.grid.columns if not c.startswith("oos_")]
        pd.testing.assert_frame_equal(self.grid[columns], other_grid[columns])
        pd.testing.assert_frame_equal(self.diagnostics, other_diag)
        self.assertEqual(self.summary, other_summary)
        for model in self.grid.loc[self.grid.eligible, "model"]:
            np.testing.assert_array_equal(self.arrays[f"{model}_train_variance"],
                                          other_arrays[f"{model}_train_variance"])
            self.assertEqual(self.arrays[f"{model}_test_variance"][0],
                             other_arrays[f"{model}_test_variance"][0])

    def test_fixed_mean_has_same_squared_innovation_proxy_for_all_models(self):
        self.assertTrue(self.summary["mean_forecast_shared"])
        self.assertFalse(self.summary["mean_parameters_refitted"])
        self.assertFalse(self.grid.mean_refitted.any())
        for row in self.grid[self.grid.eligible].itertuples():
            h = self.arrays[f"{row.model}_test_variance"]
            np.testing.assert_allclose(
                self.arrays[f"{row.model}_test_standardized_residuals"] * np.sqrt(h), self.test
            )
            self.assertAlmostEqual(row.oos_variance_proxy_mse, np.mean((self.test**2 - h)**2))
            self.assertAlmostEqual(row.oos_variance_proxy_mae, np.mean(abs(self.test**2 - h)))

    def test_scaling_backtransform_and_likelihood_jacobian(self):
        factor = 100.
        grid, _, arrays, summary = fit_volatility(self.train * factor, self.test * factor,
                                                 "fixture", diagnostic_lags=[5, 10])
        self.assertEqual(summary["selected_model"], self.summary["selected_model"])
        for row in self.grid[self.grid.eligible].itertuples():
            other = grid.loc[grid.model == row.model].iloc[0]
            self.assertTrue(other.eligible)
            self.assertAlmostEqual(other.loglikelihood, row.loglikelihood - len(self.train) * np.log(factor), places=4)
            np.testing.assert_allclose(arrays[f"{row.model}_test_variance"] / factor**2,
                                       self.arrays[f"{row.model}_test_variance"], rtol=2e-4, atol=1e-8)

    def test_empty_test_sample_is_allowed(self):
        grid, _, arrays, summary = fit_volatility(self.train, np.array([]), "fixture", [5])
        self.assertEqual(summary["nobs_test"], 0)
        self.assertTrue(grid.oos_variance_proxy_mse.isna().all())
        self.assertEqual(len(arrays["constant_test_variance"]), 0)

    def test_invalid_samples_are_rejected_not_silently_cleaned(self):
        for train in (np.zeros(50), np.array([1., np.nan] * 25), np.ones(10)):
            with self.assertRaises(ValueError):
                fit_volatility(train, self.test, "fixture")


if __name__ == "__main__":
    unittest.main()
