"""Build + execute a notebook from a list of (celltype, source) cells, saving outputs.

Avoids the JupyterHub `nbconvert --inplace` quirk (exits 0 with no saved outputs)
by executing with nbclient and writing the populated notebook explicitly.

Usage:  from _build import build_and_run; build_and_run("00_x.ipynb", cells)
"""
from __future__ import annotations
import sys
from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
from nbclient import NotebookClient


def build_and_run(filename: str, cells: list[tuple[str, str]], timeout: int = 1800) -> Path:
    nb = new_notebook()
    nb.cells = [
        (new_markdown_cell(src) if kind == "md" else new_code_cell(src))
        for kind, src in cells
    ]
    here = Path(__file__).resolve().parent
    out = here / filename
    client = NotebookClient(
        nb, timeout=timeout, kernel_name="python3",
        resources={"metadata": {"path": str(here)}},
    )
    client.execute()
    nbformat.write(nb, out)
    # sanity: count code cells that produced output
    n_out = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("outputs"))
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    print(f"[build] wrote {out} — {n_out}/{n_code} code cells have outputs")
    if n_out == 0 and n_code > 0:
        print("[build] WARNING: no outputs captured", file=sys.stderr)
    return out
