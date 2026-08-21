"""Tests for verify_ingest row-count classification (scripts/ingest_lib.py).

verify_ingest compares Iceberg COUNT(*) against the SOURCE data, so it can catch
the pipeline dropping rows. Text sources use the source-file line count; Parquet
sources are counted with Spark's reader against the uploaded bronze object,
because a line count of binary content is meaningless.

Comparing against the progress log's `total_rows` instead would check the run's
own report against its own output and could not detect row loss. That approach
was tried and rejected in review; `test_dropped_source_rows_are_caught` is the
case that motivated the change.

Everything is mocked, so these need no BERDL infrastructure.
"""
from __future__ import annotations

import sys
import types


def _stub_if_missing(name, attr):
    try:
        __import__(name)
    except (ImportError, ModuleNotFoundError):
        mod = types.ModuleType(name)
        setattr(mod, attr, lambda *a, **k: None)
        sys.modules[name] = mod


# ingest_lib imports these at module load; stub them only if unavailable so the
# test runs without BERDL/Spark installed.
_stub_if_missing("data_lakehouse_ingest", "ingest")
_stub_if_missing("get_spark_session", "get_spark_session")

from scripts import ingest_lib  # noqa: E402

COMPLETE = {"table": "biosample", "status": "complete", "total_rows": 1, "total_chunks": 1}


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def collect(self):
        return [[self._value]]


class _FakeDataFrame:
    def __init__(self, n):
        self._n = n

    def count(self):
        return self._n


class _FakeReader:
    """Stands in for `spark.read`, keyed by the s3a URI verify_ingest builds."""

    def __init__(self, source_counts, unreadable):
        self._counts = source_counts
        self._unreadable = unreadable

    def parquet(self, uri):
        if uri in self._unreadable:
            raise RuntimeError("Path does not exist")
        if uri not in self._counts:
            raise AssertionError(f"unexpected parquet uri: {uri}")
        return _FakeDataFrame(self._counts[uri])


class _FakeSpark:
    """Returns a configured COUNT(*) per table, matched on the quoted table name."""

    def __init__(self, counts, source_counts=None, unreadable=()):
        self._counts = counts
        self.read = _FakeReader(source_counts or {}, set(unreadable))

    def sql(self, query):
        for table, count in self._counts.items():
            if f"`{table}`" in query:
                return _FakeResult(count)
        raise AssertionError(f"unexpected query: {query}")


def _run(monkeypatch, capsys, table_stats, progress_log, iceberg_counts,
         source_counts=None, unreadable=(), bronze_prefix="bronze/nmdc"):
    monkeypatch.setattr(ingest_lib, "_load_progress_log", lambda *a, **k: progress_log)
    ingest_lib.verify_ingest(
        _FakeSpark(iceberg_counts, source_counts, unreadable),
        "nmdc.metadata",
        table_stats,
        object(),
        "bucket",
        "progress_key",
        bronze_prefix=bronze_prefix,
    )
    return capsys.readouterr().out


def _tsv(data_lines):
    return {"biosample": {"path": "/work/biosample.tsv", "data_lines": data_lines}}


def _parquet(data_lines=999):
    # data_lines is deliberately garbage: it is _count_lines() over binary content.
    return {"biosample": {"path": "/work/biosample.parquet", "data_lines": data_lines}}


URI = "s3a://bucket/bronze/nmdc/biosample.parquet"


def test_text_source_compares_against_line_count(monkeypatch, capsys):
    out = _run(monkeypatch, capsys, _tsv(12345), [COMPLETE], {"biosample": 12345})

    assert "[OK]" in out
    assert "source lines" in out
    assert "All row counts match" in out


def test_parquet_source_is_counted_with_spark_not_line_counted(monkeypatch, capsys):
    """The original bug: data_lines for Parquet is binary garbage (999 here),
    so using it reported MISMATCH on a correct ingest."""
    out = _run(monkeypatch, capsys, _parquet(), [COMPLETE], {"biosample": 12345},
               source_counts={URI: 12345})

    assert "[OK]" in out
    assert "MISMATCH" not in out
    assert "source parquet" in out
    assert "999" not in out


def test_dropped_source_rows_are_caught(monkeypatch, capsys):
    """The reason this compares against the source rather than the run's own
    report. The pipeline wrote 12,000 of 12,345 source rows; a report-based
    check would have compared 12,000 to 12,000 and passed."""
    out = _run(monkeypatch, capsys, _parquet(), [COMPLETE], {"biosample": 12000},
               source_counts={URI: 12345})

    assert "[MISMATCH]" in out
    assert "mismatch detected" in out.lower()


def test_text_mismatch_is_flagged(monkeypatch, capsys):
    out = _run(monkeypatch, capsys, _tsv(12345), [COMPLETE], {"biosample": 12000})

    assert "[MISMATCH]" in out
    assert "mismatch detected" in out.lower()


def test_parquet_without_a_bronze_prefix_is_unverified_not_ok(monkeypatch, capsys):
    """Degrading to the progress log here would silently restore the weaker
    check, so an uncountable source is reported rather than assumed good."""
    out = _run(monkeypatch, capsys, _parquet(), [COMPLETE], {"biosample": 12345},
               bronze_prefix=None)

    assert "[UNVERIFIED]" in out
    assert "bronze_prefix not supplied" in out
    assert "[OK]" not in out
    assert "mismatch detected" in out.lower()


def test_an_unreadable_parquet_source_is_unverified(monkeypatch, capsys):
    out = _run(monkeypatch, capsys, _parquet(), [COMPLETE], {"biosample": 12345},
               source_counts={}, unreadable={URI})

    assert "[UNVERIFIED]" in out
    assert "unreadable" in out
    assert "mismatch detected" in out.lower()


def test_table_missing_from_log_is_incomplete(monkeypatch, capsys):
    out = _run(monkeypatch, capsys,
               {"orphan": {"path": "/work/orphan.tsv", "data_lines": 5}}, [], {})

    assert "[INCOMPLETE]" in out
    assert "mismatch detected" in out.lower()
