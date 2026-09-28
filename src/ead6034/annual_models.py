"""Conventional univariate tests and Gaussian ARMA ML in trading time.

The input is ONE chronologically ordered, finite 2024 return sequence per
scale. Its observations may straddle trading sessions; no latent state or lag
is reset at a session boundary. No overnight return is manufactured here.

Estimation uses statsmodels' exact innovations likelihood with stationary
initialization and iterative GLS for the unconditional mean. Numerical input
standardization is reversed before returning parameters, log likelihoods and
information criteria. Gaussian ML is a working likelihood when conditional
heteroskedasticity is present, not a claim of homoskedastic financial returns.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
from arch.unitroot import ADF, KPSS, PhillipsPerron
from scipy.stats import chi2, jarque_bera
from statsmodels.stats.diagnostic import het_arch
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import acf, pacf, q_stat


def _finite_series(y):
    values = np.asarray(y, dtype=float)
    if values.ndim != 1 or len(values) < 20 or not np.isfinite(values).all():
        raise ValueError("Provide one finite, chronological series with at least 20 observations.")
    if np.std(values) <= 0:
        raise ValueError("The series must have positive variance.")
    return values


def annual_stationarity(y, scale):
    """ADF (none/drift/trend) and PP/KPSS (short/long) on the complete input.

    ADF chooses lags by BIC among 0..min(12, floor(n/2)-3), in all three Aula 5
    specifications (none, drift=c, trend=ct). PP and KPSS each run twice, at
    the Schwert (1989) short and long bandwidths (ceil(4*(n/100)**.25) and
    ceil(12*(n/100)**.25) respectively, both Bartlett-weighted) -- the same
    "short"/"long" pair named in Aula 5 and the TA checklist, using this
    package's own ceil convention rather than R urca's trunc (an
    implementação choice, not a claim of bit-for-bit equivalence with R).
    The ct/trend rows are pre-specified sensitivity checks, not a data-driven
    replacement of the primary constant (drift) test.
    """
    y = _finite_series(y)
    n = len(y)
    max_lags = min(12, n // 2 - 3)
    short_bw = int(np.ceil(4.0 * (n / 100.0) ** 0.25))
    long_bw = int(np.ceil(12.0 * (n / 100.0) ** 0.25))
    rows = []
    adf_trends = (("no_constant_sensitivity", "n"), ("main", "c"), ("trend_sensitivity", "ct"))
    pp_kpss_trends = (("main", "c"), ("trend_sensitivity", "ct"))
    bandwidths = (("short", short_bw), ("long", long_bw))

    def _run(name, trend, specification, bandwidth_label, bandwidth, **extra):
        row = dict(scale=scale, specification=specification, test=name,
                   trend=trend, n=n, sequence="annual_trading_time",
                   null="unit_root" if name != "KPSS" else
                   ("level_stationarity" if trend == "c" else "trend_stationarity"),
                   bandwidth_label=bandwidth_label, **extra)
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                if name == "ADF":
                    test = ADF(y, trend=trend, max_lags=max_lags, method="bic")
                elif name == "PP":
                    test = PhillipsPerron(y, trend=trend, lags=bandwidth, test_type="tau")
                else:
                    test = KPSS(y, trend=trend, lags=bandwidth)
                statistic = float(test.stat)
                critical = test.critical_values
                reject = statistic > critical["5%"] if name == "KPSS" else statistic < critical["5%"]
                row.update(status="ok", statistic=statistic, pvalue=float(test.pvalue),
                           critical_1=float(critical["1%"]), critical_5=float(critical["5%"]),
                           critical_10=float(critical["10%"]), lags=int(test.lags),
                           nobs=int(test.nobs), reject_5pct=bool(reject),
                           conclusion="reject_H0" if reject else "do_not_reject_H0",
                           warning="; ".join(str(item.message) for item in caught))
        except (ValueError, np.linalg.LinAlgError) as exc:
            row.update(status="failed", warning=str(exc))
        rows.append(row)

    for specification, trend in adf_trends:
        _run("ADF", trend, specification, "BIC_0_to_cap12", None, adf_max_lags=max_lags,
             lag_rule="BIC_0_to_cap12")
    for specification, trend in pp_kpss_trends:
        for bandwidth_label, bandwidth in bandwidths:
            for name in ("PP", "KPSS"):
                _run(name, trend, specification, bandwidth_label, bandwidth,
                     lag_rule=f"schwert_1989_{bandwidth_label}_ceil_bartlett")
    return pd.DataFrame(rows)


def _root_min(coefficients, ar):
    coefficients = np.asarray(coefficients, dtype=float)
    if not len(coefficients) or np.all(coefficients == 0):
        return float("inf")
    polynomial = np.r_[1.0, -coefficients if ar else coefficients]
    return float(np.min(np.abs(np.polynomial.polynomial.polyroots(polynomial))))


def _fit_candidate(z, p, q):
    """Package ML, deterministic initialization, state-space retry on failure."""
    model = ARIMA(z, order=(p, 0, q), trend="c", enforce_stationarity=True,
                  enforce_invertibility=True)
    if p == 0 and q == 0:
        # Exact Gaussian ML: an optimizer adds nothing and can trial sigma2=0
        # at a line-search endpoint in statsmodels' innovations implementation.
        result = model.filter(np.array([np.mean(z), np.var(z, ddof=0)]), cov_type="none")
        attempts = [dict(method="closed_form_gaussian_ml", converged=True,
                         message="mu=sample_mean; sigma2=sample_variance_ddof0", iterations=0)]
        return result, True, "closed_form_gaussian_ml", attempts
    attempts, candidates = [], []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = model.fit(
                method="innovations_mle", cov_type="none", low_memory=True,
                gls_kwargs={"max_iter": 20, "tolerance": 1e-9},
                method_kwargs={"minimize_kwargs": {"method": "L-BFGS-B", "options": {
                    "maxiter": 300, "ftol": 1e-12, "gtol": 1e-5, "maxls": 30}}})
            detail = result.fit_details
            optimization = detail.arma_results[-1].minimize_results
            converged = bool(detail.converged and optimization.success)
            attempts.append(dict(method="innovations_mle_gls", converged=converged,
                                 message=str(optimization.message), iterations=int(optimization.nit),
                                 gls_iterations=int(detail.iterations),
                                 gradient_per_observation=float(np.max(np.abs(optimization.jac)) / len(z)),
                                 warning="; ".join(str(item.message) for item in caught)))
            candidates.append((result, converged, "innovations_mle_gls"))
    except (ValueError, RuntimeError, np.linalg.LinAlgError, ArithmeticError) as exc:
        attempts.append(dict(method="innovations_mle_gls", converged=False, message=str(exc)))
    if not any(item[1] for item in candidates):
        try:
            initial = candidates[-1][0].params if candidates else None
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = model.fit(method="statespace", start_params=initial, cov_type="none",
                                   low_memory=True, method_kwargs={"maxiter": 600, "disp": False,
                                                                    "pgtol": 1e-7, "factr": 100.0})
                detail = result.mle_retvals
                converged = bool(detail.get("converged", False))
                attempts.append(dict(method="statespace_retry", converged=converged,
                                     message=str(detail.get("warnflag", "")),
                                     iterations=int(detail.get("iterations", -1)),
                                     warning="; ".join(str(item.message) for item in caught)))
                candidates.append((result, converged, "statespace_retry"))
        except (ValueError, RuntimeError, np.linalg.LinAlgError, ArithmeticError) as exc:
            attempts.append(dict(method="statespace_retry", converged=False, message=str(exc)))
    if not candidates:
        raise RuntimeError(json.dumps(attempts, ensure_ascii=False))
    successful = [item for item in candidates if item[1]]
    result, converged, method = max(successful or candidates, key=lambda item: item[0].llf)
    return result, converged, method, attempts


def _filter_with_best_available_cov_type(y, p, q, params, label):
    """Construct a filtered ARIMAResults with a real covariance type when possible.

    Grid search fits (_fit_candidate) deliberately keep cov_type="none" for
    speed/stability over dozens of candidates; only models actually selected
    for presentation need a real covariance type, so coefficient
    t-statistics are available (result.cov_type/.bse/.tvalues/.pvalues are
    standard statsmodels attributes once a real cov_type is used). Tries
    "robust" then "opg" then falls back to "none" (no SEs) if both fail.
    """
    for candidate_cov_type in ("robust", "opg", "none"):
        try:
            candidate = ARIMA(y, order=(p, 0, q), trend="c", enforce_stationarity=True,
                              enforce_invertibility=True).filter(params, cov_type=candidate_cov_type)
            if candidate_cov_type != "none" and not np.all(np.isfinite(np.asarray(candidate.bse, float))):
                raise ValueError("non-finite standard errors")
            return candidate
        except (ValueError, np.linalg.LinAlgError) as exc:
            if candidate_cov_type == "none":
                raise RuntimeError(f"{label}: could not construct even a cov_type='none' result") from exc
            continue


def fit_annual_grid(y, max_order=5, progress=None):
    """Return (public grid, selected statsmodels results, public selections).

    The grid includes every p,q=0..max_order. Only finite, converged stationary
    and invertible fits are eligible. k=p+q+2 counts the mean and variance.
    AR_BIC and MA_BIC deliberately require positive orders; they are comparator
    families, not replacements for the unrestricted BIC winner. Failed fits
    remain visible. No residual diagnostic or 2025 result changes eligibility.
    """
    y = _finite_series(y)
    if not isinstance(max_order, int) or max_order < 1:
        raise ValueError("max_order must be a positive integer (positive AR/MA comparators required).")
    n, scale = len(y), float(np.std(y))
    z = y / scale
    rows, params_by_order = [], {}
    orders = sorted(((p, q) for p in range(max_order + 1) for q in range(max_order + 1)),
                    key=lambda order: (sum(order), order))
    for p, q in orders:
        row = dict(p=p, q=q, nobs=n, parameters=p + q + 2,
                   sequence="annual_trading_time", trend="c")
        try:
            fitted, converged, method, attempts = _fit_candidate(z, p, q)
            params = np.asarray(fitted.params, dtype=float).copy()
            params[0] *= scale
            params[-1] *= scale ** 2
            ar, ma = params[1:1 + p], params[1 + p:1 + p + q]
            root_ar, root_ma = _root_min(ar, True), _root_min(ma, False)
            llf = float(fitted.llf - n * np.log(scale))
            finite = bool(np.isfinite(params).all() and np.isfinite(llf) and params[-1] > 0)
            stable = root_ar > 1 and root_ma > 1
            eligible = converged and finite and stable
            row.update(llf=llf, aic=-2 * llf + 2 * (p + q + 2),
                       bic=-2 * llf + (p + q + 2) * np.log(n),
                       mu_pct=float(params[0]), sigma2_pct=float(params[-1]),
                       sigma_pct=float(np.sqrt(params[-1])), ar=json.dumps(ar.tolist()),
                       ma=json.dumps(ma.tolist()), params_json=json.dumps(params.tolist()),
                       converged=converged, min_ar_root=root_ar, min_ma_root=root_ma,
                       method=method, attempts=len(attempts), numerical_attempts=json.dumps(attempts),
                       status="eligible" if eligible else "nonconverged_or_invalid_roots")
            params_by_order[p, q] = params
        except (ValueError, RuntimeError, np.linalg.LinAlgError, ArithmeticError) as exc:
            row.update(status="failed", converged=False, message=str(exc))
        rows.append(row)
        if progress is not None:
            progress(p, q, row)
    grid = pd.DataFrame(rows)
    eligible = grid.loc[grid.status == "eligible"].sort_values(["bic", "parameters", "p", "q"])
    if eligible.empty:
        raise RuntimeError("No converged stationary/invertible candidate was obtained.")
    grid["delta_bic"] = grid.bic - float(eligible.iloc[0].bic)
    grid["selected"] = False
    selected_results, selections = {}, []
    groups = {"ARMA_BIC": eligible,
              "AR_BIC": eligible.loc[(eligible.p > 0) & (eligible.q == 0)],
              "MA_BIC": eligible.loc[(eligible.p == 0) & (eligible.q > 0)]}
    for label, candidates in groups.items():
        if candidates.empty:
            selections.append(dict(model=label, status="no_eligible_candidate"))
            continue
        best = candidates.iloc[0]
        p, q = int(best.p), int(best.q)
        # Construct only selected filter results in original percentage units.
        result = _filter_with_best_available_cov_type(y, p, q, params_by_order[p, q], label)
        if not np.isclose(result.llf, best.llf, rtol=1e-8, atol=1e-5):
            raise RuntimeError("Scaled innovations likelihood disagrees with original-unit Kalman likelihood.")
        selected_results[label] = result
        selected_row = best.to_dict()
        selected_row.update(model=label, delta_bic=float(best.bic - eligible.iloc[0].bic))
        selections.append(selected_row)
        if label == "ARMA_BIC":
            grid.loc[(grid.p == p) & (grid.q == q), "selected"] = True
    return grid, selected_results, pd.DataFrame(selections)


def correlogram(y, scale, maxlag=60):
    """Ordinary FFT ACF and Yule-Walker (MLE denominator) PACF, without resets."""
    y = _finite_series(y)
    maxlag = min(int(maxlag), len(y) // 2 - 1)
    if maxlag < 1:
        raise ValueError("maxlag must be positive.")
    values = acf(y, nlags=maxlag, fft=True, adjusted=False)
    partial = pacf(y, nlags=maxlag, method="ywmle")
    return pd.DataFrame(dict(scale=scale, lag=np.arange(1, maxlag + 1),
                             acf=values[1:], pacf=partial[1:], n=len(y),
                             valid_pairs=len(y) - np.arange(1, maxlag + 1),
                             white_noise_pointwise_band=1.96 / np.sqrt(len(y)),
                             pacf_method="Yule_Walker_MLE", sequence="annual_trading_time"))


def diagnose_mean(result, scale):
    """Conventional residual diagnostics; no bootstrap or session correction.

    The main Ljung-Box reference follows Aula 4's df=h-p-q-1 (constant
    counted), and df=h-p-q is also exported as the common software reference.
    The Q statistic is identical. Squared innovations use df=h, as a
    heteroskedasticity screen, not a fitted GARCH
    goodness-of-fit test. ARCH-LM uses residuals and ddof=p+q. Heteroskedasticity
    can affect nominal mean-equation Ljung-Box calibration.
    """
    p, _, q = result.model.order
    z = np.asarray(result.filter_results.standardized_forecasts_error[0], dtype=float)
    z = z[np.isfinite(z)]
    n = len(z)
    horizons = sorted(set(h for h in (10, 12, 20, 24, 60) if h < n // 5))
    if not horizons:
        # Sample too small for any pre-registered horizon (n < 55): return an
        # empty-but-valid table rather than crash. Never occurs on real
        # trading-time data (thousands of observations per scale); only
        # reachable with tiny synthetic/test series.
        columns = ("scale", "p", "q", "nobs", "h", "df", "principal_horizon",
                  "lb_stat", "lb_pvalue", "lb_df_software", "lb_pvalue_software",
                  "lb_squared_stat", "lb_squared_pvalue", "arch_lags", "arch_lm",
                  "arch_lm_pvalue", "arch_f", "arch_f_pvalue", "jb_stat", "jb_pvalue",
                  "residual_type", "main_df_rule", "calibration")
        return pd.DataFrame(columns=columns)
    # statsmodels.acorr_ljungbox currently computes a direct non-FFT ACF,
    # quadratic in N. FFT ACF plus its ordinary q_stat implements exactly
    # the same conventional statistic, with no boundary correction.
    max_h = max(horizons)
    q_values, _ = q_stat(acf(z, nlags=max_h, fft=True)[1:], nobs=n)
    q_squared, p_squared = q_stat(acf(z ** 2, nlags=max_h, fft=True)[1:], nobs=n)
    arch_lags = min(12, n // 5 - 1)
    lm, lm_p, f_stat, f_p = het_arch(z, nlags=arch_lags, ddof=p + q)
    jb = jarque_bera(z)
    rows = []
    for h in horizons:
        lecture_df, software_df = h - p - q - 1, h - p - q
        principal_h = 60 if scale == "1min" else (20 if scale == "1d" else 24)
        rows.append(dict(scale=scale, p=p, q=q, nobs=n, h=h, df=lecture_df,
                         principal_horizon=h == principal_h,
                         lb_stat=float(q_values[h - 1]),
                         lb_pvalue=float(chi2.sf(q_values[h - 1], lecture_df)) if lecture_df > 0 else np.nan,
                         lb_df_software=software_df,
                         lb_pvalue_software=float(chi2.sf(q_values[h - 1], software_df)) if software_df > 0 else np.nan,
                         lb_squared_stat=float(q_squared[h - 1]),
                         lb_squared_pvalue=float(p_squared[h - 1]),
                         arch_lags=arch_lags, arch_lm=float(lm), arch_lm_pvalue=float(lm_p),
                         arch_f=float(f_stat), arch_f_pvalue=float(f_p),
                         jb_stat=float(jb.statistic), jb_pvalue=float(jb.pvalue),
                         residual_type="standardized_one_step_innovation",
                         main_df_rule="Aula4_h_minus_p_minus_q_minus_constant",
                         calibration="conventional_asymptotic_not_heteroskedasticity_robust"))
    return pd.DataFrame(rows)


def select_ljungbox_passing_arma(y, grid, scale):
    """Among eligible ARMA_BIC-family candidates, select the lowest-BIC one
    whose residuals pass Ljung-Box at EVERY diagnose_mean() horizon (not
    just the scale's principal one) -- a pre-registered, non-cherry-picked
    residual-adequacy gate applied in ADDITION to BIC, per the professor's
    explicit requirement that the selected model pass Ljung-Box.

    This does not search for a lag that happens to pass; it requires
    lb_pvalue > 0.05 at every horizon diagnose_mean() already tests. If no
    eligible candidate in the grid satisfies the gate, the pure-BIC
    candidate is returned with gate_satisfied=False -- never silently
    disguised as passing.
    """
    eligible = grid.loc[grid.status.eq("eligible")].sort_values("bic").reset_index(drop=True)
    if eligible.empty:
        raise RuntimeError(f"{scale}: no eligible ARMA candidate to gate")
    unconstrained_bic = float(eligible.iloc[0].bic)
    checked = 0
    chosen_row, chosen_diagnostics, satisfied = None, None, False
    for _, row in eligible.iterrows():
        p, q = int(row.p), int(row.q)
        params = np.asarray(json.loads(row.params_json), dtype=float)
        # cov_type="none" here: only residuals/p-values matter while scanning
        # candidates; a real covariance type is computed once, below, only
        # for whichever single candidate is ultimately chosen.
        scan_result = ARIMA(y, order=(p, 0, q), trend="c", enforce_stationarity=True,
                            enforce_invertibility=True).filter(params, cov_type="none")
        checked += 1
        diagnostics = diagnose_mean(scan_result, scale)
        if bool((diagnostics.lb_pvalue > 0.05).all()):
            chosen_row, chosen_diagnostics, satisfied = row, diagnostics, True
            break
    if chosen_row is None:
        chosen_row = eligible.iloc[0]
        params = np.asarray(json.loads(chosen_row.params_json), dtype=float)
        scan_result = ARIMA(y, order=(int(chosen_row.p), 0, int(chosen_row.q)), trend="c",
                            enforce_stationarity=True, enforce_invertibility=True).filter(
                                params, cov_type="none")
        chosen_diagnostics = diagnose_mean(scan_result, scale)
    p, q = int(chosen_row.p), int(chosen_row.q)
    params = np.asarray(json.loads(chosen_row.params_json), dtype=float)
    result = _filter_with_best_available_cov_type(y, p, q, params, "ARMA_LB_BIC")
    return dict(p=p, q=q, result=result, gate_satisfied=satisfied,
               candidates_checked=checked, candidates_total=len(eligible),
               bic=float(chosen_row.bic), min_lb_pvalue=float(chosen_diagnostics.lb_pvalue.min()),
               delta_bic_vs_unconstrained=float(chosen_row.bic - unconstrained_bic) if satisfied else 0.0)
