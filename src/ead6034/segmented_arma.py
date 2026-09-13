"""Gaussian ARMA likelihood summed over independent, stationary-initialized segments.

The model has a common unconditional mean, AR/MA coefficients and innovation
variance. The innovations algorithm resets for each segment. Under the observed
heteroskedasticity this is a Gaussian quasi-likelihood and its BIC is a working
selection criterion. No assertion of independence between trading days follows.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from statsmodels.tsa.innovations.arma_innovations import arma_innovations
from statsmodels.tsa.statespace.tools import constrain_stationary_univariate


def innovations(y, ar, ma):
    """Padding only enables the algorithm on very short segments; it adds no likelihood."""
    n = len(y)
    needed = max(len(ar), len(ma)) + 1
    if n < needed:
        padding = ((0, needed-n),) + ((0, 0),) * (np.ndim(y)-1)
        y = np.pad(y, padding)
    u, v = arma_innovations(y, ar, ma)
    return u[:n], v[:n]


@dataclass
class Fit:
    p: int
    q: int
    ar: np.ndarray
    ma: np.ndarray
    mu: float
    sigma2: float
    llf: float
    nobs: int
    success: bool
    message: str
    raw: np.ndarray
    starts: int
    gradient_max: float

    @property
    def k(self):
        return self.p + self.q + 2  # Includes the profiled mean and variance.

    @property
    def bic(self):
        return -2 * self.llf + self.k * np.log(self.nobs)

    @property
    def aic(self):
        return -2 * self.llf + 2 * self.k

    def row(self):
        return dict(p=self.p, q=self.q, nobs=self.nobs, parameters=self.k,
                    llf=self.llf, aic=self.aic, bic=self.bic, mu_pct=self.mu,
                    sigma_pct=np.sqrt(self.sigma2), ar=json.dumps(self.ar.tolist()),
                    ma=json.dumps(self.ma.tolist()), converged=self.success,
                    message=self.message, starts=self.starts, gradient_max=self.gradient_max,
                    min_ar_root=min_root(self.ar, ar=True), min_ma_root=min_root(self.ma, ar=False))


def min_root(params, ar=True):
    if len(params) == 0 or np.all(np.asarray(params) == 0):
        return float("inf")
    return float(np.min(np.abs(np.polynomial.polynomial.polyroots(
        np.r_[1., -np.asarray(params) if ar else np.asarray(params)]))))


class SegmentedARMA:
    def __init__(self, segments: list[np.ndarray]):
        self.segments = [np.asarray(x, dtype=float) for x in segments]
        if not self.segments or any(len(x) == 0 or not np.isfinite(x).all() for x in self.segments):
            raise ValueError("Provide nonempty, finite continuous segments.")
        self.nobs = sum(map(len, self.segments))
        self.scale = float(np.std(np.concatenate(self.segments)))
        if self.scale <= 0:
            raise ValueError("Cannot fit constant data.")
        self.batches = []
        for n in sorted(set(map(len, self.segments))):
            # Innovations on the final column give the filter response to a
            # constant, permitting exact GLS concentration of the common mean.
            same = [x / self.scale for x in self.segments if len(x) == n]
            self.batches.append(np.asfortranarray(np.column_stack(same + [np.ones(n)])))

    def profile(self, ar, ma):
        yy = yo = oo = logdet = 0.
        for batch in self.batches:
            u, v = innovations(batch, ar, ma)
            data, ones = u[:, :-1], u[:, -1]
            m = data.shape[1]
            yy += np.sum(data * data / v[:, None])
            yo += np.sum(data.sum(axis=1) * ones / v)
            oo += m * np.sum(ones * ones / v)
            logdet += m * np.log(v).sum()
        mu = yo / oo
        sigma2 = (yy - yo * mu) / self.nobs
        if sigma2 <= 0 or not np.isfinite(sigma2):
            raise ValueError("Invalid concentrated variance")
        llf = -.5 * (self.nobs * (np.log(2 * np.pi) + 1 + np.log(sigma2)) + logdet)
        return float(llf - self.nobs * np.log(self.scale)), float(mu * self.scale), float(sigma2 * self.scale**2)

    @staticmethod
    def transform(raw, p):
        ar = constrain_stationary_univariate(raw[:p]) if p else np.array([])
        ma = -constrain_stationary_univariate(raw[p:]) if len(raw) > p else np.array([])
        return ar, ma

    def fit(self, p, q, starts=3, seed=6034, warm=None, maxiter=600):
        if p < 0 or q < 0:
            raise ValueError("Orders must be nonnegative")
        if p + q == 0:
            llf, mu, s2 = self.profile([], [])
            return Fit(p,q,np.array([]),np.array([]),mu,s2,llf,self.nobs,True,
                       "closed_form",np.array([]),1,0.)
        def objective(raw):
            try:
                ar, ma = self.transform(raw, p)
                return -self.profile(ar, ma)[0] / self.nobs
            except (ValueError, np.linalg.LinAlgError, FloatingPointError):
                return 1e6
        rng = np.random.default_rng(seed + p * 37 + q * 101)
        initials = [np.zeros(p + q)]
        if warm is not None and len(warm) == p + q:
            initials.append(np.asarray(warm))
        while len(initials) < starts:
            initials.append(rng.normal(0, .25, p + q))
        results = []
        for initial in initials[:starts]:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                result = minimize(objective, initial, method="L-BFGS-B",
                                  options=dict(maxiter=maxiter, ftol=1e-12, gtol=2e-7, maxls=30))
            if np.isfinite(result.fun) and result.fun < 1e5:
                results.append(result)
        if not results:
            raise RuntimeError(f"All optimizations failed for ARMA({p},{q})")
        # Prefer a converged solution, while recording all candidates separately.
        converged = [r for r in results if r.success]
        result = min(converged or results, key=lambda r:r.fun)
        ar, ma = self.transform(result.x, p)
        llf, mu, s2 = self.profile(ar, ma)
        return Fit(p,q,ar,ma,mu,s2,llf,self.nobs,bool(result.success),str(result.message),
                   result.x,len(initials[:starts]),float(np.max(np.abs(result.jac))))

    def residuals(self, fit):
        out = []
        for y in self.segments:
            u, v = innovations(y - fit.mu, fit.ar, fit.ma)
            out.append(u / np.sqrt(fit.sigma2 * v))
        return out


def fit_grid(segments, max_order=5, starts=3, progress=None):
    model = SegmentedARMA(segments)
    rows, fits = [], {}
    orders = sorted(((p,q) for p in range(max_order+1) for q in range(max_order+1)), key=lambda x:(sum(x),x))
    for p,q in orders:
        # With length m replicates there are only m distinct covariances.
        # p+q+1 covariance parameters cannot exceed that dimension.
        if p + q + 1 > max(map(len, segments)):
            rows.append(dict(p=p,q=q,status="not_identifiable_from_segment_length",converged=False))
            continue
        warm = None
        if p and (p-1,q) in fits:
            parent = fits[p-1,q]
            warm = np.r_[parent.raw[:p-1], 0., parent.raw[p-1:]]
        elif q and (p,q-1) in fits:
            parent = fits[p,q-1]
            warm = np.r_[parent.raw, 0.]
        try:
            fit = model.fit(p,q,starts=starts,warm=warm)
            fits[p,q] = fit
            stable = min_root(fit.ar) > 1.001 and min_root(fit.ma, ar=False) > 1.001
            row = dict(fit.row(), status="eligible" if fit.success and stable else "numerical_or_root_restriction")
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            row = dict(p=p,q=q,status="failed",converged=False,message=str(exc))
        rows.append(row)
        if progress:
            progress(p,q,row)
    table = pd.DataFrame(rows)
    eligible = table.loc[table.status == "eligible"].sort_values(["bic","parameters","p","q"])
    best = eligible.iloc[0]
    selected = fits[int(best.p),int(best.q)]
    table["delta_bic"] = table.bic - float(best.bic)
    table["selected"] = (table.p == selected.p) & (table.q == selected.q)
    return model, selected, table, fits
