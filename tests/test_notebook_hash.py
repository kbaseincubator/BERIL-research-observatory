"""Tests for `tools.notebook_hash` — canonical .ipynb hashing for /submit."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Allow `import tools.notebook_hash` from the repo-root tests/ directory.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.notebook_hash import (  # noqa: E402
    canonicalize_ipynb,
    compute_notebook_hashes,
    hash_notebook,
    prefixed,
    unprefixed,
)


# -----------------------------------------------------------------------------
# Notebook builders
# -----------------------------------------------------------------------------


def _code_cell(source, *, outputs=None, **extras):
    cell = {
        "cell_type": "code",
        "source": source,
        "outputs": outputs or [],
        "metadata": {},
    }
    cell.update(extras)
    return cell


def _markdown_cell(source, **extras):
    cell = {"cell_type": "markdown", "source": source, "metadata": {}}
    cell.update(extras)
    return cell


def _make_notebook(cells, *, metadata=None):
    return {
        "cells": cells,
        "metadata": metadata or {
            "kernelspec": {"name": "python3", "display_name": "Python 3 (ipykernel)"},
            "language_info": {"name": "python", "mimetype": "text/x-python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _write(path: Path, nb: dict) -> Path:
    path.write_text(json.dumps(nb), encoding="utf-8")
    return path


# -----------------------------------------------------------------------------
# Canonicalization correctness
# -----------------------------------------------------------------------------


def test_identical_notebooks_hash_equal(tmp_path):
    nb = _make_notebook([_code_cell("print(1)")])
    a = _write(tmp_path / "a.ipynb", nb)
    b = _write(tmp_path / "b.ipynb", nb)
    assert hash_notebook(a) == hash_notebook(b)


def test_different_source_different_hash(tmp_path):
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("print(1)")]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("print(2)")]))
    assert hash_notebook(a) != hash_notebook(b)


def test_autosave_volatile_metadata_does_not_change_hash(tmp_path):
    """JupyterLab autosave perturbs UI metadata + cell ids without changing
    source/outputs. The hash must be stable across this."""
    cell_a = _code_cell(
        "x = 1",
        id="abcd-1234",
        execution_count=3,
        metadata={"collapsed": False, "scrolled": True, "jupyter": {"source_hidden": False}},
    )
    cell_b = _code_cell(
        "x = 1",
        id="ffff-9999",  # regenerated UUID
        execution_count=7,  # different execution number
        metadata={
            "collapsed": True,
            "scrolled": False,
            "vscode": {"languageId": "python"},
            "jp-MarkdownHeadingCollapsed": True,
            "jupyter": {"source_hidden": True},
        },
    )

    meta_a = {
        "kernelspec": {"name": "python3", "display_name": "Python 3 (a)"},
        "language_info": {
            "name": "python",
            "mimetype": "text/x-python",
            "version": "3.11.5",
            "codemirror_mode": {"name": "ipython", "version": 3},
        },
        "signature": "deadbeef",
        "widgets": {"foo": "bar"},
    }
    meta_b = {
        "kernelspec": {"name": "python3", "display_name": "Python 3 (renamed)"},
        "language_info": {
            "name": "python",
            "mimetype": "text/x-python",
            "version": "3.12.1",
            "codemirror_mode": {"name": "ipython", "version": 3},
        },
        "toc": {"some": "extension"},
        "celltoolbar": "Edit Metadata",
    }

    a = _write(tmp_path / "a.ipynb", _make_notebook([cell_a], metadata=meta_a))
    b = _write(tmp_path / "b.ipynb", _make_notebook([cell_b], metadata=meta_b))
    assert hash_notebook(a) == hash_notebook(b)


def test_output_change_changes_hash(tmp_path):
    out_a = [{"output_type": "execute_result", "data": {"text/plain": "1"}, "execution_count": 1}]
    out_b = [{"output_type": "execute_result", "data": {"text/plain": "2"}, "execution_count": 1}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_multiline_source_normalization(tmp_path):
    """Notebook spec allows source as either string or list-of-strings."""
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("line1\nline2")]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell(["line1\n", "line2"])]))
    assert hash_notebook(a) == hash_notebook(b)


def test_stream_output_hashing(tmp_path):
    out_a = [{"output_type": "stream", "name": "stdout", "text": "hello\n"}]
    out_b = [{"output_type": "stream", "name": "stdout", "text": "world\n"}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) != hash_notebook(b)
    # Multiline normalization on stream.text:
    out_split = [{"output_type": "stream", "name": "stdout", "text": ["hello", "\n"]}]
    out_joined = [{"output_type": "stream", "name": "stdout", "text": "hello\n"}]
    c = _write(tmp_path / "c.ipynb", _make_notebook([_code_cell("x", outputs=out_split)]))
    d = _write(tmp_path / "d.ipynb", _make_notebook([_code_cell("x", outputs=out_joined)]))
    assert hash_notebook(c) == hash_notebook(d)


def test_error_output_hashing(tmp_path):
    err_a = [{
        "output_type": "error",
        "ename": "ValueError",
        "evalue": "bad",
        "traceback": ["Traceback...", "ValueError: bad"],
    }]
    err_b = [{
        "output_type": "error",
        "ename": "TypeError",  # different
        "evalue": "bad",
        "traceback": ["Traceback...", "TypeError: bad"],
    }]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=err_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=err_b)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_metadata_tags_preserved(tmp_path):
    """Cell tags (papermill parameters, nbgrader directives) ARE content."""
    cell_no_tags = _code_cell("alpha = 1")
    cell_with_tags = _code_cell("alpha = 1", metadata={"tags": ["parameters"]})
    a = _write(tmp_path / "a.ipynb", _make_notebook([cell_no_tags]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([cell_with_tags]))
    assert hash_notebook(a) != hash_notebook(b)


def test_kernelspec_display_name_not_preserved(tmp_path):
    nb_a = _make_notebook([_code_cell("x")])
    nb_b = _make_notebook(
        [_code_cell("x")],
        metadata={
            "kernelspec": {"name": "python3", "display_name": "Renamed Kernel"},
            "language_info": {"name": "python", "mimetype": "text/x-python"},
        },
    )
    a = _write(tmp_path / "a.ipynb", nb_a)
    b = _write(tmp_path / "b.ipynb", nb_b)
    assert hash_notebook(a) == hash_notebook(b)


def test_language_info_version_not_preserved(tmp_path):
    nb_a = _make_notebook([_code_cell("x")])
    nb_b = _make_notebook(
        [_code_cell("x")],
        metadata={
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {
                "name": "python",
                "mimetype": "text/x-python",
                "version": "3.99.99",  # patch version drift
                "codemirror_mode": {"name": "ipython", "version": 4},
            },
        },
    )
    a = _write(tmp_path / "a.ipynb", nb_a)
    b = _write(tmp_path / "b.ipynb", nb_b)
    assert hash_notebook(a) == hash_notebook(b)


def test_cell_id_not_preserved(tmp_path):
    cell_a = _code_cell("y = 2", id="aaaa-bbbb")
    cell_b = _code_cell("y = 2", id="zzzz-yyyy")
    a = _write(tmp_path / "a.ipynb", _make_notebook([cell_a]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([cell_b]))
    assert hash_notebook(a) == hash_notebook(b)


def test_canonical_json_is_deterministic_bytes(tmp_path):
    """The exact serialization rule must be reproducible byte-for-byte."""
    nb = _make_notebook([_code_cell("z = 3")])
    p = _write(tmp_path / "n.ipynb", nb)
    bytes1 = canonicalize_ipynb(p)
    bytes2 = canonicalize_ipynb(p)
    assert bytes1 == bytes2
    # And: separators are tight, keys sorted.
    assert b", " not in bytes1  # tight separators
    assert b": " not in bytes1


def test_corrupt_notebook_raises_with_path(tmp_path):
    bad = tmp_path / "broken.ipynb"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match=str(bad)):
        hash_notebook(bad)


# -----------------------------------------------------------------------------
# compute_notebook_hashes selector
# -----------------------------------------------------------------------------


def _make_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    (project / "notebooks").mkdir(parents=True)
    return project


def test_compute_excludes_checkpoints(tmp_path):
    project = _make_project(tmp_path)
    nb = _make_notebook([_code_cell("x")])
    _write(project / "notebooks" / "01.ipynb", nb)
    _write(project / "notebooks" / "02.ipynb", nb)
    (project / "notebooks" / ".ipynb_checkpoints").mkdir()
    _write(project / "notebooks" / ".ipynb_checkpoints" / "01-checkpoint.ipynb", nb)
    result = compute_notebook_hashes(project)
    assert set(result.keys()) == {"notebooks/01.ipynb", "notebooks/02.ipynb"}


def test_compute_no_notebooks_dir(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    assert compute_notebook_hashes(project) == {}


def test_compute_empty_notebooks_dir(tmp_path):
    project = _make_project(tmp_path)
    assert compute_notebook_hashes(project) == {}


def test_compute_recurses_into_subdirs(tmp_path):
    project = _make_project(tmp_path)
    (project / "notebooks" / "exploratory").mkdir()
    nb = _make_notebook([_code_cell("x")])
    _write(project / "notebooks" / "01.ipynb", nb)
    _write(project / "notebooks" / "exploratory" / "drafts.ipynb", nb)
    result = compute_notebook_hashes(project)
    assert set(result.keys()) == {"notebooks/01.ipynb", "notebooks/exploratory/drafts.ipynb"}


def test_compute_uses_posix_paths(tmp_path):
    project = _make_project(tmp_path)
    (project / "notebooks" / "sub").mkdir()
    nb = _make_notebook([_code_cell("x")])
    _write(project / "notebooks" / "sub" / "n.ipynb", nb)
    result = compute_notebook_hashes(project)
    assert "notebooks/sub/n.ipynb" in result
    # No backslashes even on Windows-style paths.
    assert all("\\" not in k for k in result)


def test_compute_sort_stable(tmp_path):
    project = _make_project(tmp_path)
    nb = _make_notebook([_code_cell("x")])
    _write(project / "notebooks" / "99.ipynb", nb)
    _write(project / "notebooks" / "10.ipynb", nb)
    _write(project / "notebooks" / "02.ipynb", nb)
    result_keys = list(compute_notebook_hashes(project).keys())
    assert result_keys == sorted(result_keys)


def test_compute_skips_non_ipynb_files(tmp_path):
    project = _make_project(tmp_path)
    nb = _make_notebook([_code_cell("x")])
    _write(project / "notebooks" / "01.ipynb", nb)
    (project / "notebooks" / "README.md").write_text("notes", encoding="utf-8")
    (project / "notebooks" / "data.csv").write_text("a,b", encoding="utf-8")
    result = compute_notebook_hashes(project)
    assert set(result.keys()) == {"notebooks/01.ipynb"}


# -----------------------------------------------------------------------------
# Hash-prefix helpers
# -----------------------------------------------------------------------------


HEX64 = "a" * 64


def test_prefixed_adds_prefix_to_bare_hex():
    assert prefixed(HEX64) == f"sha256:{HEX64}"


def test_prefixed_idempotent_for_sha256():
    assert prefixed(f"sha256:{HEX64}") == f"sha256:{HEX64}"


def test_prefixed_rejects_other_algorithms():
    with pytest.raises(ValueError, match="sha512"):
        prefixed(f"sha512:{HEX64}")
    with pytest.raises(ValueError, match="md5"):
        prefixed("md5:abc")


def test_unprefixed_strips_sha256():
    assert unprefixed(f"sha256:{HEX64}") == HEX64


def test_unprefixed_passes_through_bare_hex():
    assert unprefixed(HEX64) == HEX64


def test_unprefixed_rejects_other_algorithms():
    with pytest.raises(ValueError, match="sha512"):
        unprefixed(f"sha512:{HEX64}")


def test_prefix_helpers_typecheck():
    with pytest.raises(TypeError):
        prefixed(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        unprefixed(None)  # type: ignore[arg-type]


# -----------------------------------------------------------------------------
# MIME bundle multiline normalization (display_data / execute_result)
# -----------------------------------------------------------------------------


def test_mime_bundle_text_plain_normalization(tmp_path):
    """{"text/plain": ["a\\n", "b"]} and {"text/plain": "a\\nb"} should hash equal."""
    out_a = [{"output_type": "execute_result", "data": {"text/plain": ["hello\n", "world"]}}]
    out_b = [{"output_type": "execute_result", "data": {"text/plain": "hello\nworld"}}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) == hash_notebook(b)


def test_mime_bundle_html_normalization(tmp_path):
    out_a = [{"output_type": "display_data", "data": {"text/html": ["<p>", "hi", "</p>"]}}]
    out_b = [{"output_type": "display_data", "data": {"text/html": "<p>hi</p>"}}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) == hash_notebook(b)


def test_mime_bundle_non_string_passthrough(tmp_path):
    """application/json with arbitrary objects should pass through unchanged
    (not coerced to a string)."""
    out_a = [{"output_type": "execute_result", "data": {"application/json": {"k": 1}}}]
    out_b = [{"output_type": "execute_result", "data": {"application/json": {"k": 2}}}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_mime_bundle_json_string_list_is_structural(tmp_path):
    """application/json values that happen to be a JSON array of strings must
    NOT be collapsed into a single string. ``["a", "b"]`` is real JSON content,
    not a chunked text representation, so it must hash differently from
    ``"ab"``."""
    out_array = [{"output_type": "execute_result", "data": {"application/json": ["a", "b"]}}]
    out_string = [{"output_type": "execute_result", "data": {"application/json": "ab"}}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_array)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_string)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_mime_bundle_json_empty_array_distinct_from_empty_string(tmp_path):
    """Same regression class: ``[]`` and ``""`` are distinct JSON values."""
    out_empty_array = [{"output_type": "execute_result", "data": {"application/json": []}}]
    out_empty_string = [{"output_type": "execute_result", "data": {"application/json": ""}}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_empty_array)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_empty_string)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_mime_bundle_vendor_plus_json_is_structural(tmp_path):
    """Vendor-specific *+json types are structural (e.g., Jupyter widget state)."""
    out_a = [{"output_type": "display_data", "data": {
        "application/vnd.jupyter.widget-view+json": ["a", "b"],
    }}]
    out_b = [{"output_type": "display_data", "data": {
        "application/vnd.jupyter.widget-view+json": "ab",
    }}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_mime_bundle_svg_normalized(tmp_path):
    """image/svg+xml is text-like under nbformat — normalize like text/*."""
    out_a = [{"output_type": "display_data", "data": {
        "image/svg+xml": ["<svg>", "...</svg>"],
    }}]
    out_b = [{"output_type": "display_data", "data": {
        "image/svg+xml": "<svg>...</svg>",
    }}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) == hash_notebook(b)


# -----------------------------------------------------------------------------
# Unknown output types — preserve, don't silently drop
# -----------------------------------------------------------------------------


def test_unknown_output_type_preserves_fields(tmp_path):
    """A future or extension output type with novel fields must affect the hash."""
    out_a = [{"output_type": "future_kind", "novel_field": "a", "extra": [1, 2]}]
    out_b = [{"output_type": "future_kind", "novel_field": "b", "extra": [1, 2]}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_unknown_output_type_string_list_preserved_structurally(tmp_path):
    """Unknown output type list-of-strings fields are preserved as JSON arrays,
    NOT auto-joined. Without knowing the field's semantics we don't know
    whether the list is a chunked multiline-text save or a real JSON array
    — preserve structurally so a real array isn't silently collapsed.

    The trade-off is a noisy false positive (different save format produces
    different hash) instead of a silent false negative."""
    out_list = [{"output_type": "future_kind", "novel_field": ["a", "b"]}]
    out_string = [{"output_type": "future_kind", "novel_field": "ab"}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_list)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_string)]))
    assert hash_notebook(a) != hash_notebook(b)


def test_unknown_output_type_nested_data_dict_normalized(tmp_path):
    """If an unknown output type happens to nest a `data: {...}` MIME bundle
    (mirroring display_data shape), apply text-MIME normalization to that
    nested dict. text/plain list-vs-string still hashes equal; JSON arrays
    stay structural."""
    out_a = [{"output_type": "future_kind", "data": {"text/plain": ["a\n", "b"]}}]
    out_b = [{"output_type": "future_kind", "data": {"text/plain": "a\nb"}}]
    a = _write(tmp_path / "a.ipynb", _make_notebook([_code_cell("x", outputs=out_a)]))
    b = _write(tmp_path / "b.ipynb", _make_notebook([_code_cell("x", outputs=out_b)]))
    assert hash_notebook(a) == hash_notebook(b)


# -----------------------------------------------------------------------------
# CLI entrypoint
# -----------------------------------------------------------------------------


def _run_cli(*args, cwd=None):
    """Invoke the script via subprocess so we exercise the real entrypoint."""
    import subprocess

    cmd = [sys.executable, str(ROOT / "tools" / "notebook_hash.py"), *args]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result


def test_cli_compute_hashes_emits_prefixed_json(tmp_path):
    project = _make_project(tmp_path)
    nb = _make_notebook([_code_cell("x")])
    _write(project / "notebooks" / "01.ipynb", nb)
    result = _run_cli("compute-hashes", str(project))
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert set(payload.keys()) == {"notebooks/01.ipynb"}
    assert payload["notebooks/01.ipynb"].startswith("sha256:")


def test_cli_compute_hashes_empty_project(tmp_path):
    project = tmp_path / "empty"
    project.mkdir()
    result = _run_cli("compute-hashes", str(project))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {}


def test_cli_works_from_subdir_cwd(tmp_path):
    """The /submit skill may run from inside projects/<id>/. The CLI must work
    with an absolute project path regardless of cwd."""
    project = _make_project(tmp_path)
    nb = _make_notebook([_code_cell("y")])
    _write(project / "notebooks" / "01.ipynb", nb)
    # Execute from inside the project itself.
    result = _run_cli("compute-hashes", str(project), cwd=str(project))
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "notebooks/01.ipynb" in payload


def test_cli_hash_notebook_emits_prefixed_hex(tmp_path):
    nb_path = tmp_path / "n.ipynb"
    _write(nb_path, _make_notebook([_code_cell("z")]))
    result = _run_cli("hash-notebook", str(nb_path))
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip()
    assert out.startswith("sha256:")
    assert len(out) == len("sha256:") + 64


def test_cli_invalid_project_dir_returns_1(tmp_path):
    result = _run_cli("compute-hashes", str(tmp_path / "does_not_exist"))
    assert result.returncode == 1
    assert "not a directory" in result.stderr


def test_cli_corrupt_notebook_returns_2(tmp_path):
    nb_path = tmp_path / "broken.ipynb"
    nb_path.write_text("{not valid", encoding="utf-8")
    result = _run_cli("hash-notebook", str(nb_path))
    assert result.returncode == 2
    assert str(nb_path) in result.stderr


def test_cli_unknown_command_returns_1(tmp_path):
    result = _run_cli("frobnicate")
    assert result.returncode == 1
    assert "unknown command" in result.stderr
