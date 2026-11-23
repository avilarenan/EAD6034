"""Reexecuta R, notebook Python e comparação; falha se houver qualquer erro."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import nbformat
from nbclient import NotebookClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--so-python", action="store_true", help="Usa a referência R versionada e recalcula somente Python.")
    parser.add_argument("--rscript", default="Rscript", help="Caminho do executável Rscript, se fora do PATH.")
    parser.add_argument("--in-process", action="store_true",
                        help="Executa com IPython em memória, para ambientes sem sockets locais.")
    args = parser.parse_args()
    folder = Path(__file__).resolve().parents[1]
    if not args.so_python:
        executable = shutil.which(args.rscript)
        if executable is None:
            raise SystemExit("Rscript não encontrado. Instale R ou use --rscript CAMINHO. Para consultar a referência R já salva: --so-python.")
        subprocess.run([executable, str(folder / "exercicio_cointegracao.R")], cwd=folder, check=True)

    path = folder / "exercicio_cointegracao.ipynb"
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    if args.in_process:
        from executar_em_processo import execute_notebook_inprocess
        notebook = execute_notebook_inprocess(notebook, cwd=folder)
    else:
        # Este kernelspec temporário usa o Python que chamou o script.
        with tempfile.TemporaryDirectory(prefix="ead6034-jupyter-") as temporary:
            kernel = Path(temporary) / "kernels" / "ead6034-exec"
            kernel.mkdir(parents=True)
            (kernel / "kernel.json").write_text(json.dumps({
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "EAD6034 execução", "language": "python"
            }), encoding="utf-8")
            previous = os.environ.get("JUPYTER_PATH")
            os.environ["JUPYTER_PATH"] = temporary + (os.pathsep + previous if previous else "")
            try:
                NotebookClient(notebook, timeout=180, kernel_name="ead6034-exec",
                               resources={"metadata": {"path": str(folder)}},
                               allow_errors=False).execute()
            finally:
                if previous is None:
                    os.environ.pop("JUPYTER_PATH", None)
                else:
                    os.environ["JUPYTER_PATH"] = previous
        notebook.metadata["ead6034_execution"] = {
            "engine": "nbclient", "transport": "tcp",
            "code_cells_executed": sum(c.cell_type == "code" for c in notebook.cells),
        }
    nbformat.validate(notebook)
    assert all(cell.get("execution_count") is not None for cell in notebook.cells if cell.cell_type == "code")
    assert not any(output.output_type == "error" for cell in notebook.cells if cell.cell_type == "code" for output in cell.outputs)
    nbformat.write(notebook, path)
    manifest = json.loads((folder / "resultados/manifesto.json").read_text(encoding="utf-8"))
    manifest["execucao_notebook"] = dict(notebook.metadata["ead6034_execution"])
    (folder / "resultados/manifesto.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest["validacao"], indent=2, ensure_ascii=False))
    print("Notebook reexecutado e salvo com todas as saídas; nenhum erro de célula.")


if __name__ == "__main__":
    main()
