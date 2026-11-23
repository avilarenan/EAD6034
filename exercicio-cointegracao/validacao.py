"""Comparação efetiva R/Python e registro de proveniência da execução."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd


def comparar(folder: Path, metrics: dict[str, float]) -> pd.DataFrame:
    """Compara cada cálculo Python com a referência realmente produzida por R.

    A referência não participa da estimação Python. O notebook pode consultar
    a execução R versionada; scripts/reproduzir.py recalcula também essa referência.
    """
    reference = pd.read_csv(folder / "resultados/r_metrics.csv",
                            float_precision="round_trip")
    if reference["key"].duplicated().any() or set(reference["key"]) != set(metrics):
        raise AssertionError("As listas de métricas R/Python não coincidem.")
    table = reference.rename(columns={"value": "R"})
    table["Python"] = table["key"].map(metrics)
    if not np.isfinite(table[["R", "Python"]].to_numpy()).all():
        raise AssertionError("Resultado não finito na comparação.")
    table["erro_absoluto"] = np.abs(table["Python"] - table["R"])
    table["tolerancia"] = 1e-8 + 1e-8 * np.abs(table["R"])
    table["confere"] = table["erro_absoluto"] <= table["tolerancia"]
    if not table["confere"].all():
        raise AssertionError("Divergência R/Python:\n" + table.loc[~table["confere"]].to_string(index=False))
    return table


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def salvar_resultados(folder: Path, results: dict, comparison: pd.DataFrame) -> dict:
    """Exporta números, incerteza dos coeficientes e hashes de dados/código/tabelas."""
    from cointegracao import metrics_frame

    output = folder / "resultados"
    output.mkdir(exist_ok=True)
    metrics_frame(results).to_csv(output / "python_metrics.csv", index=False, float_format="%.17g")
    comparison.to_csv(output / "comparacao_r_python.csv", index=False, float_format="%.17g")
    results["adf_table"].to_csv(output / "adf_python.csv", float_format="%.17g")
    results["johansen"].trace_table().to_csv(output / "johansen_python.csv", float_format="%.17g")

    coefficients = []
    for model_name, model, names in [
        ("A_longo_prazo", results["part_a"].long_run, ["constante", "x"]),
        ("A_ecm", results["part_a"].ecm, ["constante", "erro_equilibrio_lag1", "dx"]),
    ]:
        table = model.table(names).rename_axis("termo").reset_index()
        table.insert(0, "modelo", model_name)
        coefficients.append(table)
    vecm = results["johansen"].vecm
    for equation, name in enumerate(["media", "curta"]):
        coefficients.append(pd.DataFrame({
            "modelo": f"B_vecm_{name}",
            "termo": ["erro_equilibrio_lag1", "dmedia_lag1", "dcurta_lag1"],
            "coeficiente": vecm.params[:, equation],
            "erro_padrao": vecm.stderr[:, equation],
            "estatistica_t": vecm.tvalues[:, equation],
        }))
    pd.concat(coefficients, ignore_index=True).to_csv(
        output / "coeficientes_python.csv", index=False, float_format="%.17g")

    paths = [*sorted((folder / "data").glob("*.csv")),
             folder / "exercicio_cointegracao.R", folder / "cointegracao.py",
             folder / "validacao.py", folder / "requirements.txt",
             *sorted((folder / "scripts").glob("*.py")),
             *sorted((folder / "scripts").glob("*.R")),
             *sorted((folder / "scripts").glob("*.sh")),
             *sorted(output.glob("*.csv"))]
    notebook = folder / "exercicio_cointegracao.ipynb"
    source_hash = None
    if notebook.exists():
        source = json.loads(notebook.read_text(encoding="utf-8"))
        cells = [{"cell_type": cell["cell_type"], "source": cell["source"]}
                 for cell in source["cells"]]
        source_hash = hashlib.sha256(json.dumps(cells, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    r_versions = output / "r_versions.txt"
    manifest = {
        "dados": {
            "simulacao_n": len(results["simulation"]),
            "juros_n": len(results["rates"]),
            "juros_inicio": str(results["rates"]["date"].iloc[0].date()),
            "juros_fim": str(results["rates"]["date"].iloc[-1].date()),
            "frequencia_juros": "mensal", "unidade_juros": "% ao ano",
            "fonte": "tseries::tcm; Federal Reserve H.15 (distribuição do pacote)",
        },
        "especificacao": {
            "semente_R": 10, "rho": 0.6, "rho_desafio": 1,
            "engle_granger": {"intercepto_etapa1": True, "adf_lags": 1,
                              "adf_deterministico": "none", "critico_aula_5pct": -3.34},
            "adf_juros": {"type": "drift", "max_lags": 6,
                          "selectlags": "AIC", "candidatos": [1, 2, 3, 4, 5, 6],
                          "amostra_fixa_no_maximo": True},
            "johansen": {"type": "trace", "ecdet": "const", "K": 2,
                         "spec": "transitory", "rank_estimado_5pct": results["johansen"].rank_5pct},
            "erros_padrao_vecm": "OLS condicionais ao beta estimado; divisor n-k, como cajorls",
        },
        "validacao": {
            "metricas_comparadas": len(comparison),
            "todas_conferem": bool(comparison["confere"].all()),
            "erro_absoluto_maximo": float(comparison["erro_absoluto"].max()),
            "atol": 1e-8, "rtol": 1e-8,
            "referencia_R": "resultados/r_metrics.csv; recalculável pelo script R",
        },
        "ambiente": {
            "python": platform.python_version(),
            "pacotes_python": {name: importlib.metadata.version(name)
                               for name in ["numpy", "pandas", "scipy", "statsmodels", "matplotlib", "nbformat", "nbclient", "ipykernel"]},
            "versoes_R": r_versions.read_text(encoding="utf-8") if r_versions.exists() else "Ver console R",
        },
        "sha256": {str(path.relative_to(folder)): sha256(path) for path in paths if path.is_file()},
        "notebook_source_sha256": source_hash,
        "narrativa_numerica": ["resultados/comparacao_r_python.csv", "resultados/adf_python.csv",
                              "resultados/johansen_python.csv", "resultados/coeficientes_python.csv"],
    }
    (output / "manifesto.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest
