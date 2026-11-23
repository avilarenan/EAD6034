"""Cálculos Python independentes, com as convenções do exercício em R.

Não há chamada a R nem leitura de resultados R neste módulo. Os dois programas
recebem os mesmos dados, porque ``set.seed(10)`` e a semente 10 do NumPy não geram
a mesma sequência de números aleatórios.

Convenções conferidas no código/documentação original dos pacotes:
* ur.df: https://github.com/cran/urca/blob/master/R/ur-df.R
* ca.jo: https://github.com/cran/urca/blob/master/R/ca-jo.R
* cajorls: https://github.com/cran/urca/blob/master/R/cajorls.R
* VECM: https://www.statsmodels.org/stable/generated/statsmodels.tsa.vector_ar.vecm.VECM.html

A implementação matricial abaixo é deliberadamente limitada às especificações
do exercício. Em especial, o teste de Johansen usa constante RESTRITA à relação
de cointegração (Case II), não o padrão de coint_johansen(det_order=0).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from scipy.linalg import eigh


@dataclass
class OLSResult:
    """Mínimos quadrados com erros padrão condicionais usuais de lm()."""

    params: np.ndarray
    stderr: np.ndarray
    tvalues: np.ndarray
    residuals: np.ndarray
    fittedvalues: np.ndarray
    nobs: int
    df_resid: int
    rss: np.ndarray | float

    def table(self, names: list[str]) -> pd.DataFrame:
        if self.params.ndim != 1:
            raise ValueError("Use uma equação por vez para construir esta tabela.")
        return pd.DataFrame(
            {"coeficiente": self.params, "erro_padrao": self.stderr,
             "estatistica_t": self.tvalues}, index=names
        )


def ols(y: np.ndarray, x: np.ndarray) -> OLSResult:
    """Ajusta y=Xb; inclua uma coluna de 1 em X se desejar intercepto.

    O divisor da variância residual é n-k, como em summary(lm()), inclusive
    nas equações do VECM. Isso evita confundir erros padrão OLS condicionais
    com os erros padrão de máxima verossimilhança do VECM em statsmodels.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or y.ndim not in (1, 2) or len(x) != len(y):
        raise ValueError("Dimensões incompatíveis para OLS.")
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError("OLS exige dados finitos, sem valores ausentes.")
    params, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    n, k = x.shape
    if rank != k or n <= k:
        raise ValueError("OLS exige matriz de regressores de posto completo e n > k.")
    fitted = x @ params
    residuals = y - fitted
    rss = np.sum(residuals ** 2, axis=0)
    # QR evita formar a inversa de X'X para obter as variâncias.
    _, r = np.linalg.qr(x, mode="reduced")
    r_inv = np.linalg.solve(r, np.eye(k))
    variance_diagonal = np.sum(r_inv ** 2, axis=1)
    if y.ndim == 1:
        stderr = np.sqrt(variance_diagonal * rss / (n - k))
    else:
        stderr = np.sqrt(variance_diagonal[:, None] * rss[None, :] / (n - k))
    return OLSResult(params, stderr, params / stderr, residuals, fitted,
                     n, n - k, rss)


@dataclass
class ADFResult:
    statistic: float
    critical_5pct: float
    lags: int
    nobs: int
    model: OLSResult
    aic_candidates: dict[int, float]

    @property
    def reject_unit_root_5pct(self) -> bool:
        return self.statistic < self.critical_5pct


def adf_urca(
    series: np.ndarray,
    regression: Literal["none", "drift"] = "drift",
    max_lags: int = 6,
    select_lags: Literal["AIC", "Fixed"] = "AIC",
) -> ADFResult:
    """Reproduz o tau de ur.df nas duas especificações usadas na aula.

    ur.df(selectlags='AIC') compara 1..max_lags, NÃO inclui lag zero, e
    conserva em todos os ajustes a amostra cortada pelo máximo de defasagens.
    Os valores críticos tabulados são os mesmos de urca, por faixa de tamanho
    de amostra original em diferenças. Para resíduos Engle-Granger, NÃO use
    este valor crítico ADF: o exercício fornece o crítico específico -3.34.
    """
    series = np.asarray(series, dtype=float)
    if series.ndim != 1 or not np.isfinite(series).all():
        raise ValueError("ADF exige uma série univariada finita.")
    if regression not in {"none", "drift"} or select_lags not in {"AIC", "Fixed"}:
        raise ValueError("Especificação ADF não implementada neste exercício.")
    if not isinstance(max_lags, int) or max_lags < 0:
        raise ValueError("max_lags deve ser inteiro não negativo.")
    if len(series) < 2 * max_lags + 5:
        raise ValueError("Série curta demais para a especificação ADF.")
    differences = np.diff(series)
    response = differences[max_lags:]
    lagged_level = series[max_lags:-1]
    differences_lags = np.column_stack([
        differences[max_lags - lag:len(differences) - lag]
        for lag in range(1, max_lags + 1)
    ]) if max_lags else np.empty((len(response), 0))

    def fit(lags: int) -> OLSResult:
        components = ([np.ones(len(response))] if regression == "drift" else [])
        components += [lagged_level]
        components += [differences_lags[:, lag] for lag in range(lags)]
        return ols(response, np.column_stack(components))

    candidates = range(1, max_lags + 1) if select_lags == "AIC" and max_lags else [max_lags]
    fitted = {lags: fit(lags) for lags in candidates}
    # Gaussian AIC(lm) includes the estimated residual variance as a parameter.
    aics = {
        lags: float(model.nobs * (np.log(2 * np.pi) + 1
                    + np.log(model.rss / model.nobs))
                    + 2 * (len(model.params) + 1))
        for lags, model in fitted.items()
    }
    selected_lags = min(aics, key=aics.get) if select_lags == "AIC" else max_lags
    model = fitted[selected_lags]
    level_position = 1 if regression == "drift" else 0
    n_original_differences = len(differences)
    row = int(np.searchsorted([25, 50, 100, 250, 500], n_original_differences, side="right"))
    critical = -1.95 if regression == "none" else [-3.00, -2.93, -2.89, -2.88, -2.87, -2.86][row]
    return ADFResult(float(model.tvalues[level_position]), critical, selected_lags,
                     model.nobs, model, aics)


@dataclass
class EngleGrangerECM:
    long_run: OLSResult
    eg_adf: ADFResult
    ecm: OLSResult
    critical_5pct: float = -3.34

    @property
    def cointegrated_5pct(self) -> bool:
        return self.eg_adf.statistic < self.critical_5pct


def engle_granger_ecm(x: np.ndarray, y: np.ndarray) -> EngleGrangerECM:
    """As duas etapas de Engle-Granger e ECM da Parte A, sem atalhos."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    long_run = ols(y, np.column_stack([np.ones(len(x)), x]))
    residuals = long_run.residuals
    eg_adf = adf_urca(residuals, regression="none", max_lags=1, select_lags="Fixed")
    ecm = ols(np.diff(y), np.column_stack([
        np.ones(len(x) - 1), residuals[:-1], np.diff(x)
    ]))
    return EngleGrangerECM(long_run, eg_adf, ecm)


@dataclass
class JohansenResult:
    eigenvalues: np.ndarray
    trace_statistics: np.ndarray
    critical_values: np.ndarray
    beta: np.ndarray
    vecm: OLSResult
    rank_5pct: int
    nobs: int
    ect: np.ndarray
    z0: np.ndarray
    z1: np.ndarray
    zk: np.ndarray

    @property
    def alpha(self) -> np.ndarray:
        return self.vecm.params[0, :]

    @property
    def alpha_tvalues(self) -> np.ndarray:
        return self.vecm.tvalues[0, :]

    def trace_table(self) -> pd.DataFrame:
        return pd.DataFrame({
            "estatistica": self.trace_statistics,
            "critico_10pct": self.critical_values[:, 0],
            "critico_5pct": self.critical_values[:, 1],
            "critico_1pct": self.critical_values[:, 2],
            "rejeita_5pct": self.trace_statistics > self.critical_values[:, 1],
        }, index=["r = 0", "r <= 1"])


def johansen_restricted_constant(rates: np.ndarray, K: int = 2) -> JohansenResult:
    """Johansen trace + VECM r=1 para duas séries, constante restrita.

    Equivale a ca.jo(..., type='trace', ecdet='const', K=K,
    spec='transitory') seguido por cajorls(..., r=1). A constante é uma
    terceira coluna do vetor de níveis defasados; não se subtrai a média
    das séries e não se inclui intercepto separado na equação em diferenças.

    Após retirar a influência das diferenças defasadas, resolve-se
    (SK0 S00^-1 S0K) beta = lambda SKK beta por scipy.linalg.eigh. Não há
    resultados R embutidos: somente valores críticos da tabela de urca
    (Osterwald-Lenum, 1992, Case II). beta é normalizado para beta[0]=1.
    """
    rates = np.asarray(rates, dtype=float)
    if rates.ndim != 2 or rates.shape[1] != 2 or not np.isfinite(rates).all():
        raise ValueError("Este exercício exige exatamente duas séries finitas.")
    if not isinstance(K, int) or K < 2 or len(rates) <= 2 * K + 3:
        raise ValueError("K deve ser inteiro >=2, com observações suficientes.")
    differences = np.diff(rates, axis=0)
    z0 = differences[K - 1:]
    z1 = np.column_stack([
        differences[K - 1 - lag:len(differences) - lag]
        for lag in range(1, K)
    ])
    zk = np.column_stack([rates[K - 1:-1], np.ones(len(z0))])
    r0 = z0 - z1 @ np.linalg.lstsq(z1, z0, rcond=None)[0]
    rk = zk - z1 @ np.linalg.lstsq(z1, zk, rcond=None)[0]
    nobs = len(z0)
    s00 = r0.T @ r0 / nobs
    skk = rk.T @ rk / nobs
    sk0 = rk.T @ r0 / nobs
    canonical = sk0 @ np.linalg.solve(s00, sk0.T)
    # Symmetrize only floating-point noise; these matrices are symmetric by definition.
    eigenvalues, eigenvectors = eigh((canonical + canonical.T) / 2,
                                     (skk + skk.T) / 2)
    eigenvalues = eigenvalues[::-1]
    eigenvectors = eigenvectors[:, ::-1]
    if np.any(eigenvalues[:2] < -1e-10) or np.any(eigenvalues[:2] >= 1):
        raise ArithmeticError("Autovalores inválidos no teste de Johansen.")
    # The augmented system has three eigenvalues; the last is zero up to roundoff.
    eigenvalues[np.abs(eigenvalues) < 1e-14] = 0.0
    trace = np.array([-nobs * np.log1p(-eigenvalues[rank:]).sum()
                      for rank in (0, 1)])
    critical_values = np.array([[17.85, 19.96, 24.60], [7.52, 9.24, 12.97]])
    rank = 0
    for statistic, critical in zip(trace, critical_values[:, 1]):
        if statistic <= critical:
            break
        rank += 1
    beta = eigenvectors[:, 0] / eigenvectors[0, 0]
    ect = zk @ beta
    vecm = ols(z0, np.column_stack([ect, z1]))
    return JohansenResult(eigenvalues, trace, critical_values, beta, vecm,
                          rank, nobs, ect, z0, z1, zk)


def analyze(folder: str | Path | None = None) -> dict:
    """Executa todas as perguntas e desafios sobre os CSVs compartilhados.

    Retorna resultados completos para exploração no notebook e ``metrics``
    com chaves estáveis para a comparação numérica com o programa R. Os dados
    e cálculos são sempre locais; nenhuma conexão à internet é necessária.
    """
    folder = Path(folder) if folder is not None else Path(__file__).resolve().parent
    simulation = pd.read_csv(folder / "data" / "simulacao.csv", float_precision="round_trip")
    rates_frame = pd.read_csv(folder / "data" / "juros.csv", parse_dates=["date"],
                             float_precision="round_trip")
    if not {"t", "x", "z", "y", "z_rho1", "y_rho1"} <= set(simulation.columns):
        raise ValueError("Colunas ausentes em data/simulacao.csv.")
    if not {"date", "media", "curta"} <= set(rates_frame.columns):
        raise ValueError("Colunas ausentes em data/juros.csv.")
    x, y = simulation["x"].to_numpy(), simulation["y"].to_numpy()
    part_a = engle_granger_ecm(x, y)
    challenge1 = engle_granger_ecm(x, simulation["y_rho1"].to_numpy())
    rates = rates_frame[["media", "curta"]].to_numpy()
    adfs = {
        "media_level": adf_urca(rates[:, 0]),
        "curta_level": adf_urca(rates[:, 1]),
        "media_diff": adf_urca(np.diff(rates[:, 0])),
        "curta_diff": adf_urca(np.diff(rates[:, 1])),
    }
    johansen = johansen_restricted_constant(rates, K=2)
    challenge2 = adf_urca(rates[:, 0] - rates[:, 1])

    metrics = {
        "A.ols.intercept": part_a.long_run.params[0],
        "A.ols.slope": part_a.long_run.params[1],
        "A.eg.stat": part_a.eg_adf.statistic,
        "A.eg.cv5": part_a.critical_5pct,
        "A.ecm.intercept": part_a.ecm.params[0],
        "A.ecm.alpha": part_a.ecm.params[1],
        "A.ecm.dx": part_a.ecm.params[2],
        "A.ecm.alpha_t": part_a.ecm.tvalues[1],
        "A.alpha_theory": 0.6 - 1,
    }
    for name, adf in adfs.items():
        for label, value in {"stat": adf.statistic, "cv5": adf.critical_5pct,
                             "lags": adf.lags, "nobs": adf.nobs}.items():
            metrics[f"B.adf.{name}.{label}"] = value
    for rank in range(2):
        metrics[f"B.johansen.r{rank}.trace"] = johansen.trace_statistics[rank]
        metrics[f"B.johansen.r{rank}.cv10"] = johansen.critical_values[rank, 0]
        metrics[f"B.johansen.r{rank}.cv5"] = johansen.critical_values[rank, 1]
        metrics[f"B.johansen.r{rank}.cv1"] = johansen.critical_values[rank, 2]
    metrics["B.rank5"] = johansen.rank_5pct
    for index, name in enumerate(["media", "curta", "const"]):
        metrics[f"B.beta.{name}"] = johansen.beta[index]
    for index, name in enumerate(["media", "curta"]):
        metrics[f"B.alpha.{name}"] = johansen.alpha[index]
        metrics[f"B.alpha_t.{name}"] = johansen.alpha_tvalues[index]
    # In each key the first name is the dependent equation, then the lagged difference.
    for equation, eq_name in enumerate(["media", "curta"]):
        for regressor, reg_name in enumerate(["media", "curta"]):
            metrics[f"B.gamma.{eq_name}_{reg_name}"] = johansen.vecm.params[regressor + 1, equation]
    metrics.update({
        "D1.eg.stat": challenge1.eg_adf.statistic,
        "D1.eg.cv5": challenge1.critical_5pct,
        "D1.eg.ols_slope": challenge1.long_run.params[1],
        "D2.spread.stat": challenge2.statistic,
        "D2.spread.cv5": challenge2.critical_5pct,
        "D2.spread.lags": challenge2.lags,
        "D2.spread.nobs": challenge2.nobs,
    })
    metrics = {key: float(value) for key, value in metrics.items()}
    adf_table = pd.DataFrame.from_dict({
        name: {"estatistica": adf.statistic, "critico_5pct": adf.critical_5pct,
               "defasagens": adf.lags, "observacoes": adf.nobs,
               "rejeita_raiz_unitaria_5pct": adf.reject_unit_root_5pct}
        for name, adf in adfs.items()
    }, orient="index")
    return {"simulation": simulation, "rates": rates_frame, "part_a": part_a,
            "adfs": adfs, "adf_table": adf_table, "johansen": johansen,
            "challenge1": challenge1, "challenge2": challenge2,
            "metrics": metrics}


def metrics_frame(results: dict) -> pd.DataFrame:
    """Tabela key,value, preservando a precisão de ponto flutuante."""
    return pd.DataFrame(results["metrics"].items(), columns=["key", "value"])


if __name__ == "__main__":
    results = analyze()
    destination = Path(__file__).resolve().parent / "resultados"
    destination.mkdir(exist_ok=True)
    metrics_frame(results).to_csv(destination / "python_metrics.csv", index=False,
                                 float_format="%.17g")
    print(results["adf_table"].to_string())
    print("\nJohansen, constante restrita e K=2:")
    print(results["johansen"].trace_table().to_string())
    print("\nVetor beta [media, curta, constante]:", results["johansen"].beta)
    print("Alpha [media, curta]:", results["johansen"].alpha)
    print("\nMétricas Python salvas em:", destination / "python_metrics.csv")
