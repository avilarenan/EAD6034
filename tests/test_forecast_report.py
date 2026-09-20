"""Regression checks for the editable slides and the published numeric tables."""
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from ead6034.forecast_report import number, pformat, table, tex


class TestSlidePrimitives(unittest.TestCase):
    def test_table_ends_paragraph_before_following_text(self):
        rendered = table(["Escala", "N"], [["1 min", "100"]])
        self.assertTrue(rendered.endswith("\\end{tabular}\\par\n"))
        self.assertEqual(rendered.count("\\begin{tabular}"), 1)

    def test_tex_escapes_literal_percent_underscore_ampersand(self):
        self.assertEqual(tex("AR_MA & 50%"), r"AR\_MA \& 50\%")

    def test_small_pvalues_are_not_displayed_as_zero(self):
        self.assertEqual(pformat(0), "$<0{,}001$")
        self.assertEqual(pformat(.0124), "0,012")
        self.assertEqual(pformat(np.nan), "--")
        self.assertEqual(number(1.002031, 4), "1,0020")


class TestPublishedResults(unittest.TestCase):
    def setUp(self):
        self.tables = Path(__file__).resolve().parents[1] / "results/entrega_21_09/tables"
        if not (self.tables / "common_target_alignment.csv").is_file():
            self.skipTest("Consolidated published results not generated yet")

    def test_common_targets_and_no_prediction_discards(self):
        alignment = pd.read_csv(self.tables / "common_target_alignment.csv")
        self.assertEqual(len(alignment), 5)
        self.assertEqual(alignment.targets.nunique(), 1)
        self.assertTrue(alignment.identical_origins.all())
        self.assertTrue((alignment.max_target_reconciliation_error_pct <= alignment.tolerance_pct).all())
        accuracy = pd.read_csv(self.tables / "accuracy.csv")
        self.assertTrue(accuracy.n_dropped_nonfinite_all.eq(0).all())

    def test_selected_model_minimizes_bic_in_each_declared_family(self):
        grid = pd.read_csv(self.tables / "arma_grid.csv")
        selected = pd.read_csv(self.tables / "selected_models.csv")
        self.assertEqual(len(selected), 18)
        for row in selected.itertuples():
            eligible = grid.loc[grid.scale.eq(row.scale) & grid.status.eq("eligible")]
            if row.model == "AR_BIC":
                eligible = eligible.loc[eligible.p.gt(0) & eligible.q.eq(0)]
            elif row.model == "MA_BIC":
                eligible = eligible.loc[eligible.p.eq(0) & eligible.q.gt(0)]
            self.assertAlmostEqual(row.bic, eligible.bic.min(), places=7)


if __name__ == "__main__":
    unittest.main()
