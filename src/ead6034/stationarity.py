"""Conventional unit-root tests on actual, uninterrupted series.

Never attach conventional MacKinnon/KPSS p-values to a pooled regression
whose lags reset at session boundaries. Each row is a separate test. Summary
rejection rates and medians are descriptive, not panel tests or pooled p-values.
"""
from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
from arch.unitroot import ADF, KPSS, PhillipsPerron


def test_segments(frame: pd.DataFrame, scale: str, group_column: str) -> pd.DataFrame:
    rows = []
    for group_id, g in frame.groupby(group_column, sort=True, observed=True):
        g = g.sort_values("timestamp")
        y = g["return_pct"].to_numpy(dtype=float)
        n = len(y)
        base = dict(scale=scale, segment=str(group_id), start=str(g.date.iloc[0]),
                    end=str(g.date.iloc[-1]), n=n)
        # Small-sample cap is chosen before examining the test statistics.
        cap = min(12, max(0, n // 5 - 1), max(0, n // 2 - 3))
        bw = min(max(1, int(np.floor(4 * (n / 100) ** .25))), max(1, (n - 1) // 4))
        specs = [("main", "c", "bic", bw)]
        if n >= 20:
            specs += [("trend_sensitivity", "ct", "bic", bw)]
        specs += [("lag_sensitivity", "c", "aic", min(2 * bw, max(1, (n - 1) // 3)))]
        for spec, trend, method, bandwidth in specs:
            for name in ("ADF", "PP", "KPSS"):
                row = dict(base, specification=spec, test=name, trend=trend,
                           null="unit_root" if name != "KPSS" else "level_or_trend_stationarity",
                           adf_max_lags=cap if name == "ADF" else None,
                           lag_rule=method if name == "ADF" else "Bartlett_short_bandwidth",
                           small_sample=n < 25)
                if n < 8:
                    rows.append(dict(row, status="too_short", warning="n < 8; test not computed"))
                    continue
                try:
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        if name == "ADF":
                            test = ADF(y, trend=trend, max_lags=cap, method=method)
                        elif name == "PP":
                            test = PhillipsPerron(y, trend=trend, lags=bandwidth, test_type="tau")
                        else:
                            test = KPSS(y, trend=trend, lags=bandwidth)
                        stat, pv, cv = float(test.stat), float(test.pvalue), test.critical_values
                        reject = stat > cv["5%"] if name == "KPSS" else stat < cv["5%"]
                        rows.append(dict(row, status="ok", statistic=stat, pvalue=pv,
                                         critical_1=float(cv["1%"]), critical_5=float(cv["5%"]),
                                         critical_10=float(cv["10%"]), lags=int(test.lags),
                                         nobs=int(test.nobs), reject_5pct=bool(reject),
                                         warning="; ".join(str(w.message) for w in caught)))
                except (ValueError, np.linalg.LinAlgError) as exc:
                    rows.append(dict(row, status="failed", warning=str(exc)))
    return pd.DataFrame(rows)


def summarize_tests(tests: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    good = tests.loc[(tests.status == "ok") & (tests.specification == "main")].copy()
    good["reject_5pct"] = good.reject_5pct.astype(float)
    summary = good.groupby(["scale", "test"], sort=False).agg(
        segments=("segment", "count"), n_min=("n", "min"), n_max=("n", "max"),
        statistic_median=("statistic", "median"), pvalue_median=("pvalue", "median"),
        rejection_share=("reject_5pct", "mean"), lags_min=("lags", "min"),
        lags_median=("lags", "median"), lags_max=("lags", "max"),
        critical_5_min=("critical_5", "min"), critical_5_max=("critical_5", "max"),
    ).reset_index()
    p = good.pivot(index=["scale", "segment", "n"], columns="test", values="reject_5pct").reset_index()
    p["supports_i0"] = (p.ADF == 1) & (p.PP == 1) & (p.KPSS == 0)
    p["supports_unit_root"] = (p.ADF == 0) & (p.PP == 0) & (p.KPSS == 1)
    p["inconclusive_or_conflicting"] = ~(p.supports_i0 | p.supports_unit_root)
    joint = p.groupby("scale", sort=False).agg(
        tested_segments=("segment", "count"), n_min=("n", "min"), n_max=("n", "max"),
        supports_i0_share=("supports_i0", "mean"),
        supports_unit_root_share=("supports_unit_root", "mean"),
        inconclusive_share=("inconclusive_or_conflicting", "mean"),
    ).reset_index()
    return summary, joint
