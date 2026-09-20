import unittest
from unittest.mock import patch

import numpy as np
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import acf

from ead6034.annual_models import (
    _fit_candidate, annual_stationarity, correlogram, diagnose_mean, fit_annual_grid,
)


class TestAnnualModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(603421)
        cls.y = rng.normal(loc=0.004, scale=0.035, size=700)
        cls.grid, cls.selected, cls.selection = fit_annual_grid(cls.y, max_order=1)

    def test_whole_annual_n_and_ordinary_penalty(self):
        self.assertEqual(len(self.grid), 4)
        self.assertTrue((self.grid.nobs == len(self.y)).all())
        np.testing.assert_allclose(self.grid.bic,
                                   -2 * self.grid.llf + self.grid.parameters * np.log(len(self.y)))
        np.testing.assert_allclose(self.grid.aic, -2 * self.grid.llf + 2 * self.grid.parameters)
        self.assertEqual(set(self.selected), {"ARMA_BIC", "AR_BIC", "MA_BIC"})
        self.assertEqual(self.selected["AR_BIC"].model.order, (1, 0, 0))
        self.assertEqual(self.selected["MA_BIC"].model.order, (0, 0, 1))

    def test_white_noise_closed_form_and_original_units(self):
        row = self.grid.loc[(self.grid.p == 0) & (self.grid.q == 0)].iloc[0]
        self.assertAlmostEqual(row.mu_pct, self.y.mean(), places=8)
        self.assertAlmostEqual(row.sigma2_pct, self.y.var(), places=8)
        reference = -.5 * len(self.y) * (np.log(2 * np.pi * self.y.var()) + 1)
        self.assertAlmostEqual(row.llf, reference, places=5)
        self.assertEqual(row.method, "closed_form_gaussian_ml")

    def test_white_noise_closed_form_never_invokes_numerical_optimizer(self):
        with patch.object(ARIMA, "fit", side_effect=ZeroDivisionError("trial sigma2=0")):
            result, converged, method, _ = _fit_candidate(self.y, 0, 0)
        self.assertTrue(converged)
        self.assertEqual(method, "closed_form_gaussian_ml")
        np.testing.assert_allclose(result.params, [self.y.mean(), self.y.var()])

    def test_arithmetic_failure_retries_with_statespace(self):
        actual_fit = ARIMA.fit
        def fail_innovations_only(model, *args, **kwargs):
            if kwargs.get("method") == "innovations_mle":
                raise ZeroDivisionError("trial sigma2=0")
            return actual_fit(model, *args, **kwargs)
        with patch.object(ARIMA, "fit", new=fail_innovations_only):
            _, converged, method, attempts = _fit_candidate(self.y / self.y.std(), 1, 0)
        self.assertTrue(converged)
        self.assertEqual(method, "statespace_retry")
        self.assertEqual(len(attempts), 2)
        self.assertIn("trial sigma2=0", attempts[0]["message"])

    def test_selected_likelihood_matches_independent_package(self):
        for label, result in self.selected.items():
            reference = ARIMA(self.y, order=result.model.order, trend="c").loglike(result.params)
            self.assertAlmostEqual(result.llf, reference, places=6)
            row = self.selection.loc[self.selection.model == label].iloc[0]
            self.assertAlmostEqual(row.bic, result.bic, places=5)

    def test_lags_continue_across_former_session_boundary(self):
        y = np.tile(np.r_[np.ones(8), -8.], 15)
        table = correlogram(y, "60min", 3)
        expected = acf(y, nlags=3, fft=False)[1:]
        np.testing.assert_allclose(table.acf, expected)
        self.assertEqual(table.valid_pairs.iloc[0], len(y) - 1)
        # Fifteen independent nine-bar sessions would have only 15*8 pairs.
        self.assertNotEqual(table.valid_pairs.iloc[0], 15 * 8)

    def test_stationarity_is_six_full_sample_tests_not_per_session(self):
        table = annual_stationarity(self.y, "60min")
        self.assertEqual(len(table), 6)
        self.assertTrue((table.n == len(self.y)).all())
        self.assertTrue((table.status == "ok").all())
        self.assertEqual(set(table.test), {"ADF", "PP", "KPSS"})
        self.assertEqual(set(table.trend), {"c", "ct"})
        self.assertTrue((table.loc[table.test == "ADF", "lags"] <= 12).all())

    def test_ljung_box_is_conventional(self):
        result = self.selected["AR_BIC"]
        table = diagnose_mean(result, "60min")
        z = result.filter_results.standardized_forecasts_error[0]
        expected = acorr_ljungbox(z, lags=table.h.tolist(), model_df=1)
        lecture_expected = acorr_ljungbox(z, lags=table.h.tolist(), model_df=2)
        np.testing.assert_allclose(table.lb_stat, expected.lb_stat)
        np.testing.assert_allclose(table.lb_pvalue_software, expected.lb_pvalue)
        np.testing.assert_allclose(table.lb_pvalue, lecture_expected.lb_pvalue)

    def test_scale_change_preserves_orders_and_likelihood_jacobian(self):
        grid, selected, _ = fit_annual_grid(self.y * 100, max_order=1)
        self.assertEqual(selected["ARMA_BIC"].model.order,
                         self.selected["ARMA_BIC"].model.order)
        np.testing.assert_allclose(grid.llf,
                                   self.grid.llf - len(self.y) * np.log(100), atol=1e-5)
        np.testing.assert_allclose(grid.mu_pct, self.grid.mu_pct * 100, atol=1e-7)
        np.testing.assert_allclose(grid.sigma2_pct, self.grid.sigma2_pct * 10000, atol=1e-5)

    def test_identifies_strong_ar_process_and_agrees_with_statespace_fit(self):
        rng = np.random.default_rng(217)
        innovations = rng.normal(size=2000)
        y = np.zeros(2000)
        for t in range(1, len(y)):
            y[t] = 0.65 * y[t - 1] + innovations[t]
        _, selected, _ = fit_annual_grid(y, max_order=1)
        result = selected["AR_BIC"]
        self.assertAlmostEqual(result.arparams[0], 0.65, delta=0.05)
        reference = ARIMA(y, order=(1, 0, 0), trend="c").fit(cov_type="none")
        self.assertAlmostEqual(result.llf, reference.llf, places=3)

    def test_nonfinite_and_constant_series_rejected(self):
        for y in (np.ones(30), np.r_[np.arange(30), np.nan], np.arange(10)):
            with self.assertRaises(ValueError):
                fit_annual_grid(y, max_order=1)


if __name__ == "__main__":
    unittest.main()
