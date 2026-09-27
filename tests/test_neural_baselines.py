import numpy as np
import unittest

from ead6034.neural_baselines import _lag_features, mlp_native_forecast


class TestLagFeatures(unittest.TestCase):
    def test_windows_are_causal_and_aligned(self):
        y = np.arange(10, dtype=float)
        X, target = _lag_features(y, window=3)
        # target[k] = y[3+k], X[k] = y[k:k+3] -- strictly the 3 values before it.
        np.testing.assert_array_equal(target, y[3:])
        np.testing.assert_array_equal(X[0], [0., 1., 2.])
        np.testing.assert_array_equal(X[-1], y[len(y) - 4:len(y) - 1])


class TestMLPNativeForecast(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(6034)
        n = 400
        self.y = np.zeros(n)
        for t in range(1, n):
            self.y[t] = .3 * self.y[t - 1] + rng.normal(scale=.1)
        self.train_n = 300

    def test_training_rows_and_pre_window_rows_are_nan(self):
        matrix, _ = mlp_native_forecast(self.y, self.train_n, window=10,
                                        hidden_layer_candidates=((4,),), alpha_candidates=(1e-2,))
        self.assertTrue(np.isnan(matrix[:self.train_n, 0]).all())
        self.assertTrue(np.isfinite(matrix[self.train_n:, 0]).all())

    def test_poisoning_the_future_does_not_change_earlier_test_predictions(self):
        matrix, _ = mlp_native_forecast(self.y, self.train_n, window=10,
                                        hidden_layer_candidates=((4,),), alpha_candidates=(1e-2,))
        poisoned = self.y.copy()
        poisoned[self.train_n + 20:] += 1000.
        poisoned_matrix, _ = mlp_native_forecast(poisoned, self.train_n, window=10,
                                                  hidden_layer_candidates=((4,),), alpha_candidates=(1e-2,))
        # Rows strictly before the poisoned region use only past (unpoisoned)
        # context and an identically-trained model (poisoning is all in the
        # test suffix, which never enters training/validation) -- must match.
        np.testing.assert_allclose(
            matrix[self.train_n:self.train_n + 20], poisoned_matrix[self.train_n:self.train_n + 20])

    def test_hyperparameter_selection_never_touches_the_test_partition(self):
        matrix, summary = mlp_native_forecast(self.y, self.train_n, window=10,
                                              hidden_layer_candidates=((4,), (8,)),
                                              alpha_candidates=(1e-3, 1e-2))
        poisoned = self.y.copy()
        poisoned[self.train_n:] += 1000.
        _, poisoned_summary = mlp_native_forecast(poisoned, self.train_n, window=10,
                                                   hidden_layer_candidates=((4,), (8,)),
                                                   alpha_candidates=(1e-3, 1e-2))
        self.assertEqual(summary["selected_hidden_layer_sizes"], poisoned_summary["selected_hidden_layer_sizes"])
        self.assertEqual(summary["selected_alpha"], poisoned_summary["selected_alpha"])
        self.assertAlmostEqual(summary["selected_validation_mse"], poisoned_summary["selected_validation_mse"])

    def test_rejects_window_not_smaller_than_train_n(self):
        with self.assertRaises(ValueError):
            mlp_native_forecast(self.y, train_n=5, window=10)


if __name__ == "__main__":
    unittest.main()
