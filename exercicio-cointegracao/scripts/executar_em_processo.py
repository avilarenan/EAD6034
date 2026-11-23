"""Executa um notebook com um kernel IPython real, inteiramente em memória.

Alternativa para ambientes que não permitem os sockets locais usados pelo
nbclient. Cada célula é executada de verdade por ipykernel.inprocess; stdout,
tabelas, Markdown, imagens e resultados são capturados das mensagens IOPub.
Não altera a especificação do kernel do notebook, que continua utilizável
normalmente no Jupyter e no Codespaces.

Uso:
    python scripts/executar_em_processo.py entrada.ipynb saida.ipynb --cwd .

API:
    executed = execute_notebook_inprocess(notebook, cwd=exercise_directory)

Execute apenas notebooks confiáveis: assim como um kernel Jupyter comum,
este mecanismo executa o código Python fornecido pelo notebook.
"""

from __future__ import annotations

import argparse
import copy
import os
import platform
import sys
from pathlib import Path
from queue import Empty

import ipykernel
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager


class NotebookExecutionError(RuntimeError):
    """Uma célula executada pelo kernel terminou com erro."""


def _collect_outputs(client, request_id: str, cell, displays: dict) -> None:
    """Consome, em ordem, as mensagens reais do kernel para uma célula."""
    pending_clear = False
    while True:
        try:
            message = client.get_iopub_msg(timeout=10)
        except Empty as error:
            raise NotebookExecutionError("O kernel não confirmou o término da célula.") from error
        kind, content = message["msg_type"], message["content"]
        parent_id = message.get("parent_header", {}).get("msg_id")
        # OutStream do kernel in-process pode emitir stdout/stderr sem parent.
        # Como as execuções são estritamente sequenciais, esse stream pertence
        # à célula atual; o próprio kernel o envia antes do estado idle.
        if parent_id != request_id and not (kind == "stream" and parent_id is None):
            continue
        if kind == "status" and content["execution_state"] == "idle":
            return
        if kind == "execute_input":
            cell["execution_count"] = content["execution_count"]
        elif kind == "clear_output":
            pending_clear = content.get("wait", False)
            if not pending_clear:
                cell["outputs"] = []
        elif kind in {"stream", "display_data", "execute_result", "error", "update_display_data"}:
            if pending_clear:
                cell["outputs"] = []
                pending_clear = False
            if kind == "stream":
                if (cell["outputs"] and cell["outputs"][-1]["output_type"] == "stream"
                        and cell["outputs"][-1]["name"] == content["name"]):
                    cell["outputs"][-1]["text"] += content["text"]
                else:
                    cell["outputs"].append(nbformat.v4.new_output(
                        "stream", name=content["name"], text=content["text"]))
            elif kind == "error":
                cell["outputs"].append(nbformat.v4.new_output(
                    "error", ename=content["ename"], evalue=content["evalue"],
                    traceback=content["traceback"]))
            elif kind == "update_display_data":
                display_id = content.get("transient", {}).get("display_id")
                for output in displays.get(display_id, []):
                    output["data"] = copy.deepcopy(content["data"])
                    output["metadata"] = copy.deepcopy(content.get("metadata", {}))
            else:
                fields = {"data": copy.deepcopy(content["data"]),
                          "metadata": copy.deepcopy(content.get("metadata", {}))}
                if kind == "execute_result":
                    fields["execution_count"] = content["execution_count"]
                output = nbformat.v4.new_output(kind, **fields)
                cell["outputs"].append(output)
                display_id = content.get("transient", {}).get("display_id")
                if display_id is not None:
                    displays.setdefault(display_id, []).append(output)


def execute_notebook_inprocess(notebook, cwd: str | Path):
    """Retorna uma cópia executada; falha imediatamente em qualquer erro de célula.

    Usa o mesmo estado Python entre células, captura todos os resultados pelo
    protocolo Jupyter e mantém os execution_counts realmente emitidos pelo
    kernel. A pasta de execução e sys.path são restaurados mesmo após erro.

    Para assegurar isolamento de estado entre notebooks independentes, prefira
    invocar este script em um novo processo Python para cada notebook.
    """
    executed = copy.deepcopy(notebook)
    nbformat.validate(executed)
    for cell in executed.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    cwd = Path(cwd).resolve(strict=True)
    previous_cwd = Path.cwd()
    previous_sys_path = sys.path[:]
    # A comunicação do cliente in-process é por filas em memória, sem bind().
    # ip explícito evita uma descoberta desnecessária de interfaces de rede.
    manager = InProcessKernelManager(ip="127.0.0.1")
    client = None
    try:
        os.chdir(cwd)
        sys.path.insert(0, str(cwd))
        manager.start_kernel()
        manager.kernel.shell.enable_matplotlib("inline")
        client = manager.client()
        client.start_channels()
        displays: dict = {}
        code_cells_executed = 0
        for index, cell in enumerate(executed.cells):
            if cell.cell_type != "code" or not cell.source.strip():
                continue
            request_id = client.execute(cell.source, allow_stdin=False, store_history=True)
            _collect_outputs(client, request_id, cell, displays)
            try:
                reply = client.get_shell_msg(timeout=10)
            except Empty as error:
                raise NotebookExecutionError(f"Sem resposta da célula {index + 1}.") from error
            if reply.get("parent_header", {}).get("msg_id") != request_id:
                raise NotebookExecutionError("Resposta de execução não corresponde à célula.")
            result = reply["content"]
            cell.execution_count = result.get("execution_count", cell.execution_count)
            if result.get("status") != "ok":
                description = f"{result.get('ename', 'Erro')}: {result.get('evalue', '')}"
                raise NotebookExecutionError(f"Célula {index + 1}: {description}")
            code_cells_executed += 1
        executed.metadata["language_info"] = copy.deepcopy(manager.kernel.language_info)
        executed.metadata["ead6034_execution"] = {
            "engine": "ipykernel.inprocess",
            "transport": "in-memory",
            "python_version": platform.python_version(),
            "ipykernel_version": ipykernel.__version__,
            "code_cells_executed": code_cells_executed,
        }
        nbformat.validate(executed)
        return executed
    finally:
        if client is not None:
            client.stop_channels()
        if manager.has_kernel:
            manager.shutdown_kernel()
        os.chdir(previous_cwd)
        sys.path[:] = previous_sys_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Notebook a executar.")
    parser.add_argument("output", type=Path, help="Notebook executado a salvar.")
    parser.add_argument("--cwd", type=Path, help="Pasta de execução; padrão: pasta do notebook.")
    args = parser.parse_args()
    source = args.input.resolve(strict=True)
    destination = args.output.resolve()
    notebook = nbformat.read(source, as_version=4)
    executed = execute_notebook_inprocess(notebook, args.cwd or source.parent)
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(executed, destination)
    print(f"Notebook executado e validado: {destination}")


if __name__ == "__main__":
    main()
