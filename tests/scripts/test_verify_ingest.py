"""Tests for verify_ingest row-count classification (scripts/ingest_lib.py).

verify_ingest compares Iceberg COUNT(*) against the ingest progress log's
`total_rows` (the rows actually written), not the source-file line count.
These tests exercise the OK / MISMATCH / INCOMPLETE classification with a
mocked Spark session and progress log, so they need no BERDL infrastructure.
"""
from __future__ import annotations

import sys
import types


def _stub_if_missing(name, attr):
    try:
        __import__(name)
    except Exception:
        mod = types.ModuleType(name)
        setattr(mod, attr, lambda *a, **k: None)
        sys.modules[name] = mod


# ingest_lib imports these at module load; stub them only if unavailable so the
# test runs without BERDL/Spark installed.
_stub_if_missing("data_lakehouse_ingest", "ingest")
_stub_if_missing("get_spark_session", "get_spark_session")

from scripts import ingest_lib  # noqa: E402


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def collect(self):
        return [[self._value]]


class _FakeSpark:
    """Return a configured COUNT(*) per table, matched on the quoted table name."""

    def __init__(self, counts):
        self._counts = counts

    def sql(self, query):
        for table, count in self._counts.items():
            if f"`{table}`" in query:
                return _FakeResult(count)
        raise AssertionError(f"unexpected query: {query}")


def _run(monkeypatch, capsys, table_stats, progress_log, iceberg_counts):
    monkeypatch.setattr(ingest_lib, "_load_progress_log", lambda *a, **k: progress_log)
    ingest_lib.verify_ingest(
        _FakeSpark(iceberg_counts),
        "nmdc.metadata",
        table_stats,
        object(),
        "bucket",
        "progress_key",
    )
    return capsys.readouterr().out


def test_parquet_count_matches_rows_written(monkeypatch, capsys):
    # Parquet source: data_lines (999) is not the row count; rows actually
    # written is 12345. Comparing against total_rows (not data_lines) passes.
    out = _run(
        monkeypatch, capsys,
        {"biosample": {"data_lines": 999}},
        [{"table": "biosample", "status": "complete", "total_rows": 12345, "total_chunks": 1}],
        {"biosample": 12345},
    )
    assert "[OK]" in out
    assert "MISMATCH" not in out
    assert "All row counts match" in out


def test_real_mismatch_is_flagged(monkeypatch, capsys):
    out = _run(
        monkeypatch, capsys,
        {"biosample": {"data_lines": 999}},
        [{"table": "biosample", "status": "complete", "total_rows": 12345, "total_chunks": 1}],
        {"biosample": 12000},
    )
    assert "[MISMATCH]" in out
    assert "mismatch detected" in out.lower()


def test_table_missing_from_log_is_incomplete(monkeypatch, capsys):
    out = _run(
        monkeypatch, capsys,
        {"orphan": {"data_lines": 5}},
        [],
        {},
    )
    assert "[INCOMPLETE]" in out
    assert "mismatch detected" in out.lower()
