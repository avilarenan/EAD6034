"""Synthetic, private-data-free integration checks for the 21/09 pipeline."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from ead6034 import forecast_pipeline as pipeline


def _common_targets():
    starts = pd.date_range("2025-01-02 09:05", periods=3, freq="1h", tz="America/Sao_Paulo")
    rows = []
    for model in ("ZERO", "AR_BIC", "MA_BIC"):
        for position, start in enumerate(starts):
            rows.append(dict(
                evaluation="common_60min", model=model, target_start=start,
                target_end=start + pd.Timedelta(hours=1), actual=.01 * position,
            ))
    return {scale: pd.DataFrame(rows) for scale in pipeline.SCALE_MINUTES}


def _frame():
    rng = np.random.default_rng(21092026)
    rows = []
    for day in ("2024-12-27", "2024-12-30", "2025-01-02", "2025-01-03"):
        starts = pd.date_range(f"{day} 09:05", periods=9, freq="1h", tz="America/Sao_Paulo")
        for position, start in enumerate(starts):
            rows.append(dict(
                timestamp=start + pd.Timedelta(hours=1), bar_start=start,
                date=day, sample="train" if day.startswith("2024") else "test",
                time_band="first_hour" if position == 0 else "last_hour" if position == 8 else "middle",
                gap_group="small" if day.endswith("02") else "large",
                position_in_session=position, return_pct=float(rng.normal(scale=.1)),
            ))
    return pd.DataFrame(rows)


def _cheap_grid(y, **kwargs):
    """Real state-space filter objects; no optimizer or external data."""
    specifications = {
        "ARMA_BIC": ((0, 0, 0), [.01, .02]),
        "AR_BIC": ((1, 0, 0), [.01, .2, .02]),
        "MA_BIC": ((0, 0, 1), [.01, .15, .02]),
    }
    fitted, selected, grid = {}, [], []
    for name, (order, params) in specifications.items():
        result = ARIMA(y, order=order, trend="c").filter(params, cov_type="none")
        fitted[name] = result
        record = dict(p=order[0], q=order[2], bic=float(result.bic), status="eligible")
        grid.append(record)
        selected.append(dict(model=name, **record))
    return pd.DataFrame(grid), fitted, pd.DataFrame(selected)


def _cheap_volatility(train, test, scale, **kwargs):
    return (
        pd.DataFrame([dict(scale=scale, model="CONSTANT", status="eligible")]),
        pd.DataFrame([dict(scale=scale, model="CONSTANT", p_value=.5)]),
        {"CONSTANT_train": np.full(len(train), .02), "CONSTANT_test": np.full(len(test), .02)},
        dict(selected_model="CONSTANT"),
    )


class TestCommonTargetAudit(unittest.TestCase):
    def test_all_five_scales_accept_same_targets_even_if_row_order_differs(self):
        inputs = _common_targets()
        inputs["15min"] = inputs["15min"].sample(frac=1, random_state=6034)
        audited = pipeline.verify_common_targets(inputs)
        self.assertEqual(audited.scale.tolist(), list(pipeline.SCALE_MINUTES))
        self.assertTrue(audited.targets.eq(3).all())
        self.assertTrue(audited.identical_origins.all())
        self.assertTrue(audited.max_target_reconciliation_error_pct.eq(0).all())
        self.assertTrue(audited.checked_after_finite_prediction_mask.all())

    def test_missing_common_target_fails(self):
        inputs = _common_targets()
        remove = inputs["5min"].target_start.min()
        inputs["5min"] = inputs["5min"].loc[inputs["5min"].target_start.ne(remove)]
        with self.assertRaisesRegex(AssertionError, "different origins/endpoints"):
            pipeline.verify_common_targets(inputs)

    def test_changed_realized_return_fails(self):
        inputs = _common_targets()
        inputs["30min"].loc[0, "actual"] += .001
        with self.assertRaisesRegex(AssertionError, "model-specific common targets differ"):
            pipeline.verify_common_targets(inputs)

    def test_duplicate_model_target_fails(self):
        inputs = _common_targets()
        # Duplicate a non-ZERO model to exercise the all-model duplicate guard.
        inputs["60min"] = pd.concat([inputs["60min"], inputs["60min"].iloc[[4]]], ignore_index=True)
        with self.assertRaisesRegex(AssertionError, "duplicate common target"):
            pipeline.verify_common_targets(inputs)

    def test_changed_endpoint_fails_even_with_unchanged_return(self):
        inputs = _common_targets()
        inputs["15min"].loc[0, "target_end"] += pd.Timedelta(minutes=1)
        with self.assertRaisesRegex(AssertionError, "model-specific common targets differ"):
            pipeline.verify_common_targets(inputs)

    def test_changed_nonzero_model_return_fails(self):
        inputs = _common_targets()
        index = inputs["5min"].index[inputs["5min"].model.eq("AR_BIC")][0]
        inputs["5min"].loc[index, "actual"] += .001
        with self.assertRaisesRegex(AssertionError, "5min/AR_BIC: model-specific common targets differ"):
            pipeline.verify_common_targets(inputs)

    def test_missing_nonzero_model_target_fails(self):
        inputs = _common_targets()
        index = inputs["30min"].index[inputs["30min"].model.eq("MA_BIC")][0]
        inputs["30min"] = inputs["30min"].drop(index=index)
        with self.assertRaisesRegex(AssertionError, "30min/MA_BIC: model-specific common targets differ"):
            pipeline.verify_common_targets(inputs)

    def test_zero_targets_missing_or_all_common_targets_empty_fail_explicitly(self):
        for empty_all in (False, True):
            with self.subTest(empty_all=empty_all):
                inputs = _common_targets()
                if empty_all:
                    inputs["1min"] = inputs["1min"].iloc[:0]
                else:
                    inputs["1min"] = inputs["1min"].loc[inputs["1min"].model.ne("ZERO")]
                with self.assertRaisesRegex(AssertionError, "1min: no common ZERO targets"):
                    pipeline.verify_common_targets(inputs)

    def test_consistent_within_scale_but_different_across_scales_still_fails(self):
        inputs = _common_targets()
        inputs["60min"].loc[:, "actual"] += .001
        with self.assertRaisesRegex(AssertionError, "different realized returns"):
            pipeline.verify_common_targets(inputs)

    def test_reconciliation_tolerance_is_explicit(self):
        inputs = _common_targets()
        inputs["60min"].loc[0, "actual"] += 1e-12
        audited = pipeline.verify_common_targets(inputs)
        error = audited.loc[audited.scale.eq("60min"), "max_target_reconciliation_error_pct"].iloc[0]
        self.assertGreater(error, 0)
        self.assertLess(error, 1e-10)


class TestJsonSafety(unittest.TestCase):
    def test_recursive_conversion_accepts_strict_json_without_nan_or_inf(self):
        source = {
            np.int64(2): np.array([1., np.nan, np.inf, -np.inf]),
            "tuple": (np.int64(3), np.float64(.25), np.bool_(True)),
            "nested": {"bad": float("nan"), "path": Path("relative/code.py")},
            "time": pd.Timestamp("2025-01-02T09:05:00-03:00"),
        }
        converted = pipeline.json_safe(source)
        encoded = json.dumps(converted, allow_nan=False)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["2"], [1., None, None, None])
        self.assertEqual(decoded["tuple"], [3, .25, True])
        self.assertIsNone(decoded["nested"]["bad"])
        self.assertEqual(decoded["nested"]["path"], "relative/code.py")
        self.assertIn("2025-01-02", decoded["time"])

    def test_write_json_is_strict_and_preserves_unicode(self):
        with tempfile.TemporaryDirectory(prefix="ead6034-json-test-") as directory:
            path = Path(directory) / "summary.json"
            pipeline.write_json(path, {"ação": np.float64(np.nan), "válido": np.int64(8)})
            text = path.read_text(encoding="utf-8")
            self.assertIn("ação", text)
            self.assertNotIn("NaN", text)
            self.assertEqual(json.loads(text), {"ação": None, "válido": 8})


class TestProcessScaleIntegration(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ead6034-pipeline-test-")
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        (self.output / "private").mkdir()
        (self.output / "tables").mkdir()
        self.frame = _frame()
        self.frame_path = self.output / "private" / "frames_60min.parquet"
        self.frame.to_parquet(self.frame_path, index=False)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.fit = self.stack.enter_context(patch.object(pipeline, "fit_annual_grid", side_effect=_cheap_grid))
        self.stationarity = self.stack.enter_context(patch.object(
            pipeline, "annual_stationarity", return_value=pd.DataFrame([dict(test="ADF", p_value=.01)])))
        self.stack.enter_context(patch.object(
            pipeline, "diagnose_mean", return_value=pd.DataFrame([dict(lag=1, p_value=.5)])))
        self.stack.enter_context(patch.object(
            pipeline, "correlogram", return_value=pd.DataFrame([dict(lag=1, acf=.1, pacf=.1)])))
        self.stack.enter_context(patch.object(pipeline, "fit_volatility", side_effect=_cheap_volatility))
        # Fixed code/version fingerprints keep these tests independent of
        # simultaneous edits elsewhere in the working tree.
        self.stack.enter_context(patch.object(pipeline, "source_digest", side_effect=lambda names: "synthetic:" + ",".join(names)))
        self.stack.enter_context(patch.object(pipeline, "numerical_versions", return_value={"test": "1"}))

    def run_scale(self, **kwargs):
        return pipeline.process_scale("60min", self.output, max_order=1, **kwargs)

    def test_smoke_real_forecasts_prediction_column_and_completed_checkpoint(self):
        summary = self.run_scale()
        self.assertEqual(summary["n_train"], 18)
        self.assertEqual(summary["n_test"], 18)
        self.assertFalse(summary["fitted_parameters_use_holdout"])
        predictions = pd.read_parquet(self.output / "private" / "predictions_60min.parquet")
        self.assertIn("prediction", predictions.columns)
        self.assertNotIn("predicted", predictions.columns)
        self.assertEqual(set(predictions.model.astype(str)), {
            "ARMA_BIC", "AR_BIC", "MA_BIC", "AR_MA_50_50", "ZERO", "TRAIN_MEAN",
        })
        self.assertTrue(predictions.target_end.dt.year.eq(2025).all())
        for table in pipeline.COMBINED_TABLES:
            self.assertTrue((self.output / "tables" / f"{table}_60min.csv").is_file(), table)
        equivalence = pd.read_csv(self.output / "tables" / "forecast_equivalence_60min.csv")
        self.assertEqual(len(equivalence), 30)  # 6 choose 2, for two evaluations.
        self.assertEqual(self.fit.call_count, 1)
        self.assertEqual(self.stationarity.call_count, 1)
        repeated = self.run_scale()
        self.assertEqual(repeated, summary)
        self.assertEqual(self.fit.call_count, 1)
        self.assertEqual(self.stationarity.call_count, 1)

    def test_holdout_change_invalidates_completion_but_reuses_training_model_cache(self):
        before = self.run_scale()
        self.frame.loc[18, "return_pct"] += 5
        self.frame.to_parquet(self.frame_path, index=False)
        after = self.run_scale()
        self.assertEqual(self.fit.call_count, 1)
        self.assertEqual(self.stationarity.call_count, 2)
        self.assertEqual(before["train_sha256"], after["train_sha256"])
        self.assertNotEqual(before["full_sequence_sha256"], after["full_sequence_sha256"])
        self.assertEqual(before["model"], after["model"])

    def test_training_change_invalidates_both_completion_and_model_cache(self):
        before = self.run_scale()
        self.frame.loc[0, "return_pct"] += .03
        self.frame.to_parquet(self.frame_path, index=False)
        after = self.run_scale()
        self.assertEqual(self.fit.call_count, 2)
        self.assertNotEqual(before["train_sha256"], after["train_sha256"])

    def test_missing_required_export_prevents_completed_checkpoint_reuse(self):
        self.run_scale()
        # Deliberately remove one disposable synthetic export, not user data.
        (self.output / "tables" / "accuracy_60min.csv").unlink()
        self.run_scale()
        self.assertEqual(self.stationarity.call_count, 2)
        self.assertEqual(self.fit.call_count, 1)
        self.assertTrue((self.output / "tables" / "accuracy_60min.csv").exists())

    def test_no_resume_explicitly_refits(self):
        self.run_scale()
        self.run_scale(resume=False)
        self.assertEqual(self.fit.call_count, 2)


if __name__ == "__main__":
    unittest.main()
