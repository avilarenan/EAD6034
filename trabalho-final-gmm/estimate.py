"""GMM para os painéis ND/VWR e NDS/VWR, Hansen e Singleton (1982; errata 1984)."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import solve_triangular
from scipy.optimize import minimize_scalar
from scipy.stats import chi2

# Tabela I, ND+VWR, errata de 1984 p. 268. PROB é a CDF, não a cauda superior.
# Ordem: expoente de Euler, EP, desconto mensal, EP, J, graus de liberdade, PROB.
PUBLISHED_ND = {
    1: (-1.2028, .7789, .9976, .0027, 1.457, 1, .7726),
    2: (-.5761, .7067, .9975, .0027, 5.819, 3, .8792),
    4: (-.6565, .6896, .9978, .0027, 7.923, 7, .6606),
    6: (-.9638, .6425, .9985, .0027, 10.522, 11, .5159),
}


# Nondurables + services / same VWR, separate rows of the same corrected table.
PUBLISHED_NDS = {
    1: (-1.0350, 1.8765, .9982, .0045, 1.071, 1, .6993),
    2: (.1426, 1.7002, .9965, .0044, 3.467, 3, .6749),
    4: (-.0210, 1.6525, .9969, .0043, 5.718, 7, .4270),
    6: (-1.1643, 1.5104, .9997, .0041, 11.040, 11, .5601),
}


def assemble(data, lag, trim):
    """Target row s: z=(1,R[s-1],x[s-1],...,R[s-L],x[s-L]); no future instruments."""
    if not lag <= trim < len(data):
        raise ValueError("Invalid lag or trim")
    values = data[["gross_real_return", "gross_cons_growth"]].to_numpy()
    aligned = [values[trim-j:len(values)-j] for j in range(1, lag+1)]
    instruments = np.column_stack([np.ones(len(values)-trim), *aligned])
    if np.linalg.matrix_rank(instruments) != 1 + 2*lag:
        raise ValueError("Singular instrument matrix")
    # Re-express the SAME moment restrictions in orthogonal coordinates for stability.
    # Identity weight after QR equals inverse instrument second moment on original scale.
    orth, _ = np.linalg.qr(instruments, mode="reduced")
    return orth * np.sqrt(len(orth)), values[trim:, 0], np.log(values[trim:, 1])


def fit(data, lag, trim, iterated=False, centered=False):
    z, r, logx = assemble(data, lag, trim)
    n, q = z.shape
    b = z.mean(axis=0)
    def estimate_fixed_weight(s):
        # For fixed alpha, profile out beta analytically: gbar = beta*a-b.
        lower = np.linalg.cholesky(s)
        white = solve_triangular(lower, z.T/n, lower=True)
        wb = solve_triangular(lower, b, lower=True)
        def profile(alpha):
            a = white @ (r*np.exp(alpha*logx))
            beta = (a @ wb) / (a @ a)
            e = beta*a - wb
            return e @ e, beta
        # Broad search for an interior minimum; do not impose preference signs.
        grid = np.linspace(-50., 50., 201)
        vals = np.array([profile(x)[0] for x in grid])
        best = int(vals.argmin())
        if best in (0,len(grid)-1):
            raise ArithmeticError("GMM minimized on search boundary")
        minima = np.flatnonzero((vals[1:-1] <= vals[:-2]) & (vals[1:-1] <= vals[2:])) + 1
        fits = [minimize_scalar(lambda x: profile(x)[0], method="bounded",
                                bounds=(grid[j-1], grid[j+1]), options={"xatol": 1e-11})
                for j in minima]
        fit = min(fits, key=lambda f: f.fun)
        if not fit.success:
            raise ArithmeticError("GMM minimization failed")
        a = fit.x
        return np.array([a, profile(a)[1]])
    def moments(theta):
        alpha, beta = theta
        f = r*np.exp(alpha*logx)
        h = (beta*f - 1.)[:, None]*z
        D = z.T @ np.column_stack([beta*f*logx, f])/n
        return h, D
    s = np.eye(q)
    prelim = estimate_fixed_weight(s)
    prev = prelim
    for step in range(2, 102):
        m, _ = moments(prev)
        v = m-m.mean(axis=0) if centered else m
        s = v.T @ v/n  # horizon one: contemporaneous moment covariance
        theta = estimate_fixed_weight(s)
        if not iterated or np.max(np.abs(theta-prev)) < 2e-7:
            break
        prev = theta
    else:
        raise ArithmeticError("Iterated GMM did not converge")
    m, d = moments(theta)
    # Two-step sandwich evaluated at final theta, using the SAME weight as the final fit.
    # At convergence of iterated GMM it reduces to the efficient-GMM covariance.
    v = m-m.mean(axis=0) if centered else m
    s_final = v.T @ v/n
    wd = np.linalg.solve(s, d)
    bread = d.T @ wd
    influence = np.linalg.solve(bread, wd.T)
    cov = influence @ s_final @ influence.T/n
    se = np.sqrt(np.diag(cov))
    g = m.mean(axis=0)
    j = float(n*g @ np.linalg.solve(s, g))
    df = q-2
    if np.linalg.matrix_rank(d) != 2 or not (np.isfinite(se).all() and (se > 0).all()):
        raise ArithmeticError("Unidentified model / invalid standard errors")
    return dict(lag=lag, n=n, first_month=str(data.date.iloc[trim])[:7],
                last_month=str(data.date.iloc[-1])[:7], instruments=q, df=df,
                alpha=theta[0], se_alpha=se[0], beta=theta[1], se_beta=se[1],
                j=j, p_value=chi2.sf(j,df), steps=step)


def run(data_path, output_dir, panel="ND"):
    published = {"ND": PUBLISHED_ND, "NDS": PUBLISHED_NDS}[panel]
    data = pd.read_csv(data_path, parse_dates=["date"])
    months = data.date.dt.to_period("M")
    expected = pd.period_range("1959-02", "1978-12", freq="M")
    if not pd.Index(months).equals(expected):
        raise ValueError("Expected the uninterrupted original order, 1959-02 to 1978-12.")
    x = data[["gross_cons_growth", "gross_real_return"]].to_numpy()
    if not np.isfinite(x).all() or x.min() <= 0:
        raise ValueError("Gross real quantities must be finite and positive")
    rows, alternatives = [], []
    for lag, (alpha, a_se, beta, b_se, j, df, prob) in published.items():
        base = fit(data, lag, lag, iterated=True, centered=True)
        assert base["df"] == df and base["n"] == 239-lag
        rows.append({"panel":panel, **base, "alpha_original":alpha, "se_alpha_original":a_se,
                     "beta_original":beta, "se_beta_original":b_se, "j_original":j,
                     "prob_cdf_original":prob, "p_value_original":1-prob,
                     "delta_alpha":base["alpha"]-alpha, "delta_beta":base["beta"]-beta,
                     "delta_j":base["j"]-j})
        alternatives.append({"panel":panel, "specification":"iterated_centered_all", **base})
        for label, trim, it, center in [
                ("iterated_centered_common", 6, True, True),
                ("iterated_uncentered_all", lag, True, False),
                ("two_step_uncentered_all", lag, False, False),
                ("two_step_centered_all", lag, False, True)]:
            alternatives.append({"panel": panel, "specification": label,
                                 **fit(data, lag, trim, it, center)})
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    comparison = pd.DataFrame(rows)
    comparison.to_csv(out/"comparison.csv", index=False, float_format="%.9g")
    pd.DataFrame(alternatives).to_csv(out/"sensitivity.csv", index=False, float_format="%.9g")
    return comparison
