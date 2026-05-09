"""Canonical hashing for Jupyter notebooks (and SHA-256 prefix helpers).

Used by `/submit` to record a stable hash of each notebook in the approval
block, so accidental drift between approval and lakehouse upload (e.g., the
author re-runs a cell while debugging) is detected before publication.

Canonicalization tolerates JupyterLab autosave (UI metadata mutations don't
invalidate the hash) but detects content changes (source edits or output
changes from re-execution).

Canonical JSON serialization rule (must be reproduced byte-for-byte by any
re-implementation):

    json.dumps(canonical, sort_keys=True, separators=(",", ":"),
               ensure_ascii=False).encode("utf-8")

Whitelisted fields (everything else is dropped):

Notebook-level:
    - nbformat, nbformat_minor
    - metadata.kernelspec.name
    - metadata.language_info.name, .mimetype
    - cells (with per-cell canonicalization below)

Cell-level (for every cell_type):
    - cell_type
    - source (normalized: list-of-strings → joined; string → unchanged)
    - metadata.tags (papermill / nbgrader directives — content-bearing)

Code cells additionally:
    - outputs (with per-output canonicalization below)

Per-output (by output_type):
    - stream:                 output_type, name, text (normalized)
    - display_data, execute_result: output_type, data
    - error:                  output_type, ename, evalue, traceback (normalized)
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

NOTEBOOKS_SUBDIR = "notebooks"
CHECKPOINTS_DIR = ".ipynb_checkpoints"
NOTEBOOK_SUFFIX = ".ipynb"


def _normalize_text(value):
    """Notebook spec allows a multiline string to be either ``"a\\nb"`` or
    ``["a\\n", "b"]``. Normalize to a single string so equivalent notebooks
    hash equal regardless of which form was written."""
    if isinstance(value, list):
        return "".join(str(x) for x in value)
    return value


def _normalize_data_bundle(data):
    """Apply multiline normalization recursively to a MIME-bundle ``data`` dict.

    Notebook MIME bundles can serialize each value as either a plain string or
    a list-of-strings (same convention as cell ``source``). For example
    ``{"text/plain": ["a\\n", "b"]}`` and ``{"text/plain": "a\\nb"}`` are
    equivalent and must hash equal.

    We only touch top-level values (the MIME-keyed entries) and lists of
    strings within those. Nested structures (e.g., ``application/json``
    containing arbitrary objects) pass through unchanged — they're already
    hashed structurally by the canonical JSON serializer.
    """
    if not isinstance(data, dict):
        return data
    out: dict = {}
    for k, v in data.items():
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            out[k] = "".join(v)
        else:
            out[k] = v
    return out


# Known output types: each maps to the keys we preserve canonically. Unknown
# output_types fall through to a "preserve everything verbatim" branch so an
# integrity check doesn't silently miss content from future or extension-
# defined output kinds.
_KNOWN_OUTPUT_TYPES = frozenset({"stream", "display_data", "execute_result", "error"})


def _canonical_output(output: dict) -> dict:
    """Whitelist canonicalization for a single output cell entry.

    For known output types (stream / display_data / execute_result / error)
    keep only the content-bearing fields; for unknown types preserve the
    full output dict so an integrity check can still detect changes (better
    a noisy hash than a silent false negative if Jupyter or an extension
    introduces a new output kind).
    """
    out_type = output.get("output_type")
    if out_type == "stream":
        return {
            "output_type": out_type,
            "name": output.get("name"),
            "text": _normalize_text(output.get("text", "")),
        }
    if out_type in ("display_data", "execute_result"):
        return {
            "output_type": out_type,
            "data": _normalize_data_bundle(output.get("data", {})),
        }
    if out_type == "error":
        return {
            "output_type": out_type,
            "ename": output.get("ename"),
            "evalue": output.get("evalue"),
            "traceback": [_normalize_text(t) for t in output.get("traceback", [])],
        }
    # Unknown output type: preserve the entire output dict, but apply the
    # text-normalization recursively wherever a string-or-list pattern shows
    # up at top level so equivalent forms hash equal.
    canonical: dict = {}
    for key, value in output.items():
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            canonical[key] = "".join(value)
        elif isinstance(value, dict):
            canonical[key] = _normalize_data_bundle(value)
        else:
            canonical[key] = value
    return canonical


def _canonical_cell(cell: dict) -> dict:
    """Whitelist canonicalization for a single cell."""
    cell_type = cell.get("cell_type")
    canonical: dict = {
        "cell_type": cell_type,
        "source": _normalize_text(cell.get("source", "")),
    }
    cell_meta = cell.get("metadata", {}) or {}
    if "tags" in cell_meta:
        canonical["metadata"] = {"tags": cell_meta["tags"]}
    if cell_type == "code":
        canonical["outputs"] = [
            _canonical_output(o) for o in cell.get("outputs", []) or []
        ]
    return canonical


def _canonical_notebook(nb: dict) -> dict:
    """Whitelist canonicalization for a notebook dict."""
    notebook_meta = nb.get("metadata", {}) or {}
    canonical_meta: dict = {}
    kernelspec = notebook_meta.get("kernelspec")
    if isinstance(kernelspec, dict) and "name" in kernelspec:
        canonical_meta["kernelspec"] = {"name": kernelspec["name"]}
    language_info = notebook_meta.get("language_info")
    if isinstance(language_info, dict):
        keep = {k: language_info[k] for k in ("name", "mimetype") if k in language_info}
        if keep:
            canonical_meta["language_info"] = keep

    canonical: dict = {
        "nbformat": nb.get("nbformat"),
        "nbformat_minor": nb.get("nbformat_minor"),
        "cells": [_canonical_cell(c) for c in nb.get("cells", []) or []],
    }
    if canonical_meta:
        canonical["metadata"] = canonical_meta
    return canonical


def canonicalize_ipynb(path: Path) -> bytes:
    """Read a notebook from `path` and return its canonical JSON bytes.

    Raises ValueError on invalid JSON, with the path included in the message
    so the caller can identify which notebook failed.
    """
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as f:
            nb = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid notebook JSON at {path}: {exc}") from exc
    canonical = _canonical_notebook(nb)
    return json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def hash_notebook(path: Path) -> str:
    """Return the SHA-256 hex digest of `path`'s canonical form.

    The returned string is raw hex (no ``sha256:`` prefix). Use ``prefixed()``
    when writing to YAML; comparisons should pass the stored value through
    ``unprefixed()`` first.
    """
    return hashlib.sha256(canonicalize_ipynb(path)).hexdigest()


def compute_notebook_hashes(project_path: Path) -> dict[str, str]:
    """Walk ``{project_path}/notebooks/`` and return ``{relpath: hex}``.

    - Excludes ``.ipynb_checkpoints/`` (any depth).
    - Recurses into subdirectories.
    - Returns POSIX-style relative paths (forward slashes on all platforms).
    - Returns an empty dict if ``notebooks/`` is missing or empty.
    - Result is sorted by path for stable YAML output.
    """
    project_path = Path(project_path)
    notebooks_dir = project_path / NOTEBOOKS_SUBDIR
    if not notebooks_dir.is_dir():
        return {}

    hashes: dict[str, str] = {}
    for root, dirs, files in os.walk(notebooks_dir):
        # Prune checkpoint dirs in-place so os.walk doesn't descend.
        dirs[:] = sorted(d for d in dirs if d != CHECKPOINTS_DIR)
        for fname in sorted(files):
            if not fname.endswith(NOTEBOOK_SUFFIX):
                continue
            full = Path(root) / fname
            rel = full.relative_to(project_path).as_posix()
            hashes[rel] = hash_notebook(full)
    # Re-sort by relpath: the os.walk order above is per-directory, but we
    # want a single global lex order so YAML output is stable across reruns.
    return {k: hashes[k] for k in sorted(hashes)}


def prefixed(h: str) -> str:
    """Return ``h`` annotated with ``sha256:`` prefix.

    Idempotent: ``prefixed("sha256:abc") == "sha256:abc"``.
    Rejects other algorithms: ``prefixed("sha512:abc")`` raises ValueError.
    Bare hex passes through with prefix added.
    """
    if not isinstance(h, str):
        raise TypeError(f"prefixed expected str, got {type(h).__name__}")
    if h.startswith("sha256:"):
        return h
    if ":" in h:
        algo = h.split(":", 1)[0]
        raise ValueError(f"unsupported hash algorithm: {algo}")
    return f"sha256:{h}"


def unprefixed(h: str) -> str:
    """Strip the ``sha256:`` prefix if present, returning raw hex.

    Bare hex passes through unchanged.
    Rejects other algorithms: ``unprefixed("sha512:abc")`` raises ValueError.
    """
    if not isinstance(h, str):
        raise TypeError(f"unprefixed expected str, got {type(h).__name__}")
    if h.startswith("sha256:"):
        return h[len("sha256:") :]
    if ":" in h:
        algo = h.split(":", 1)[0]
        raise ValueError(f"unsupported hash algorithm: {algo}")
    return h


def _cli(argv: list[str]) -> int:
    """CLI entrypoint for skill text and shell scripts.

    The /submit and /berdl_start skills can run from anywhere (including
    inside ``projects/<id>/``), so importing ``tools.notebook_hash`` from
    a Python one-liner is fragile (depends on cwd / PYTHONPATH). Instead
    they invoke this script directly:

        python /abs/path/to/tools/notebook_hash.py compute-hashes <project_dir>

    Output: a single-line JSON object on stdout: ``{"<relpath>": "sha256:<hex>", ...}``.
    Hashes are emitted with the ``sha256:`` prefix so the caller can write
    them to YAML directly without further processing.

    Exit codes:
        0  on success (JSON written to stdout, even for empty result {}).
        1  on bad usage or filesystem error.
        2  on a corrupt notebook (the path is included in the stderr message).
    """
    import sys

    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        sys.stderr.write(
            "usage: notebook_hash.py compute-hashes <project_dir>\n"
            "       notebook_hash.py hash-notebook <ipynb_path>\n"
        )
        return 0 if (len(argv) >= 2 and argv[1] in ("-h", "--help")) else 1

    cmd = argv[1]
    if cmd == "compute-hashes":
        if len(argv) != 3:
            sys.stderr.write("error: compute-hashes requires <project_dir>\n")
            return 1
        project_dir = Path(argv[2])
        if not project_dir.is_dir():
            sys.stderr.write(f"error: not a directory: {project_dir}\n")
            return 1
        try:
            raw = compute_notebook_hashes(project_dir)
        except ValueError as exc:
            sys.stderr.write(f"error: {exc}\n")
            return 2
        prefixed_hashes = {k: prefixed(v) for k, v in raw.items()}
        sys.stdout.write(json.dumps(prefixed_hashes, sort_keys=True))
        sys.stdout.write("\n")
        return 0

    if cmd == "hash-notebook":
        if len(argv) != 3:
            sys.stderr.write("error: hash-notebook requires <ipynb_path>\n")
            return 1
        path = Path(argv[2])
        if not path.is_file():
            sys.stderr.write(f"error: not a file: {path}\n")
            return 1
        try:
            h = hash_notebook(path)
        except ValueError as exc:
            sys.stderr.write(f"error: {exc}\n")
            return 2
        sys.stdout.write(prefixed(h))
        sys.stdout.write("\n")
        return 0

    sys.stderr.write(f"error: unknown command: {cmd}\n")
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(_cli(sys.argv))
