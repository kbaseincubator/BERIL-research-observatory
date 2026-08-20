"""Offline tests for the non-interactive BERDL staging command."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import types
from pathlib import Path

import pytest


def _stub_if_missing(name, attr):
    try:
        __import__(name)
    except Exception:
        module = types.ModuleType(name)
        setattr(module, attr, lambda *args, **kwargs: None)
        sys.modules[name] = module


_stub_if_missing("data_lakehouse_ingest", "ingest")
_stub_if_missing("get_spark_session", "get_spark_session")

from scripts import ingest_dataset  # noqa: E402
from scripts import ingest_lib  # noqa: E402


def _args(data_dir: Path, outcome: Path | None = None, **changes) -> argparse.Namespace:
    values = {
        "data_dir": data_dir,
        "tenant": "nmdc",
        "dataset": "nmdc_metadata_staging_20260819",
        "staging_namespace": "nmdc.nmdc_metadata_staging_20260819",
        "mode": "overwrite",
        "bucket": "cdm-lake",
        "bronze_prefix": "tenant-general-warehouse/nmdc/staging/20260819",
        "progress_key": "tenant-general-warehouse/nmdc/staging/20260819/progress.jsonl",
        "config_key": "tenant-general-warehouse/nmdc/staging/20260819/config.json",
        "chunk_target_gb": 20.0,
        "outcome": outcome,
        "execute_staging": False,
    }
    values.update(changes)
    return argparse.Namespace(**values)


@pytest.fixture
def parquet_dir(tmp_path: Path) -> Path:
    (tmp_path / "biosample_set.parquet").write_bytes(b"PAR1-not-line-oriented")
    (tmp_path / "snapshot-manifest.json").write_text("{}", encoding="utf-8")
    return tmp_path


def test_plan_only_never_initializes_external_clients(parquet_dir, monkeypatch, capsys):
    monkeypatch.setattr(
        "scripts.ingest_lib._count_lines",
        lambda _path: pytest.fail("Parquet must never be binary-line-counted"),
    )
    monkeypatch.setattr(
        ingest_dataset,
        "initialize",
        lambda: pytest.fail("plan-only mode must not initialize live clients"),
    )

    assert ingest_dataset.run(_args(parquet_dir)) == 0
    output = capsys.readouterr().out
    assert "nmdc.nmdc_metadata_staging_20260819" in output
    assert "PLAN ONLY" in output
    assert "rows verified after upload" in output


def test_execute_runs_maintained_sequence_and_writes_verified_outcome(
    parquet_dir, tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(ingest_dataset, "initialize", lambda: ("spark", "minio"))
    source_sha256 = hashlib.sha256(
        (parquet_dir / "biosample_set.parquet").read_bytes()
    ).hexdigest()
    monkeypatch.setattr(
        ingest_dataset,
        "upload_files",
        lambda *args, **kwargs: calls.append(("upload", kwargs))
        or {"biosample_set": source_sha256},
    )
    monkeypatch.setattr(
        ingest_dataset,
        "run_ingest",
        lambda *args: calls.append(("ingest", args[13], args[14])) or "reconnected-spark",
    )
    monkeypatch.setattr(
        ingest_dataset,
        "verify_ingest",
        lambda *args, **kwargs: {
            "verified": True,
            "namespace": "nmdc.nmdc_metadata_staging_20260819",
            "tables": [{
                "table": "biosample_set",
                "status": "verified",
                "source_rows": 10,
                "destination_rows": 10,
                "source_basis": "source parquet",
            }],
        },
    )
    outcome = tmp_path / "outcome.json"

    assert ingest_dataset.run(
        _args(parquet_dir, outcome, execute_staging=True)
    ) == 0
    assert calls == [
        ("upload", {"force": True, "verify_sha256": True}),
        (
            "ingest",
            "tenant-general-warehouse/nmdc/staging/20260819/progress.jsonl",
            "tenant-general-warehouse/nmdc/staging/20260819/config.json",
        ),
    ]
    document = json.loads(outcome.read_text(encoding="utf-8"))
    assert document["status"] == "verified"
    assert document["verification"]["tables"][0]["source_rows"] == 10
    assert document["verification"]["tables"][0]["source_sha256"] == source_sha256


def test_guarded_upload_replaces_and_hashes_stored_object(parquet_dir):
    source = parquet_dir / "biosample_set.parquet"

    class Response(io.BytesIO):
        def release_conn(self):
            return None

    class Client:
        def __init__(self):
            self.stored = b"x" * source.stat().st_size
            self.uploads = 0

        def stat_object(self, _bucket, _key):
            return types.SimpleNamespace(size=len(self.stored))

        def fput_object(self, _bucket, _key, path):
            self.uploads += 1
            self.stored = Path(path).read_bytes()

        def get_object(self, _bucket, _key):
            return Response(self.stored)

    client = Client()
    table_stats = {
        "biosample_set": {
            "path": source,
            "size_bytes": source.stat().st_size,
            "chunked": False,
        }
    }

    digests = ingest_lib.upload_files(
        client, "bucket", table_stats, "unique/prefix", ".parquet", True, True
    )

    assert client.uploads == 1
    assert digests == {"biosample_set": hashlib.sha256(source.read_bytes()).hexdigest()}


def test_stored_digest_verification_requires_replacement(parquet_dir):
    with pytest.raises(ValueError, match="requires forced"):
        ingest_lib.upload_files(
            object(), "bucket", {}, "unique/prefix", ".parquet", False, True
        )


def test_verification_mismatch_exits_nonzero(parquet_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_dataset, "initialize", lambda: ("spark", "minio"))
    monkeypatch.setattr(
        ingest_dataset,
        "upload_files",
        lambda *args, **kwargs: {"biosample_set": "a" * 64},
    )
    monkeypatch.setattr(ingest_dataset, "run_ingest", lambda *args: "spark")
    monkeypatch.setattr(
        ingest_dataset,
        "verify_ingest",
        lambda *args, **kwargs: {
            "verified": False,
            "namespace": "nmdc.nmdc_metadata_staging_20260819",
            "tables": [{"table": "biosample_set", "status": "mismatch"}],
        },
    )
    outcome = tmp_path / "mismatch.json"

    assert ingest_dataset.run(
        _args(parquet_dir, outcome, execute_staging=True)
    ) == 1
    assert json.loads(outcome.read_text())["status"] == "failed"


def test_ingest_failure_is_sanitized_in_outcome(parquet_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_dataset, "initialize", lambda: ("spark", "minio"))
    monkeypatch.setattr(
        ingest_dataset,
        "upload_files",
        lambda *args, **kwargs: {"biosample_set": "a" * 64},
    )

    def fail(*args):
        raise RuntimeError("secret-bearing provider diagnostic")

    monkeypatch.setattr(ingest_dataset, "run_ingest", fail)
    outcome = tmp_path / "failed.json"

    assert ingest_dataset.run(
        _args(parquet_dir, outcome, execute_staging=True)
    ) == 1
    serialized = outcome.read_text(encoding="utf-8")
    assert "secret-bearing" not in serialized
    document = json.loads(serialized)
    assert document["failed_phase"] == "ingest"
    assert document["error_type"] == "RuntimeError"


def test_partial_upload_failure_is_recorded_without_starting_ingest(
    parquet_dir, tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(ingest_dataset, "initialize", lambda: ("spark", "minio"))

    def fail_upload(*args, **kwargs):
        raise OSError("second object failed after the first upload")

    monkeypatch.setattr(ingest_dataset, "upload_files", fail_upload)
    monkeypatch.setattr(
        ingest_dataset, "run_ingest", lambda *args: calls.append("ingest")
    )
    outcome = tmp_path / "partial-upload.json"

    assert ingest_dataset.run(
        _args(parquet_dir, outcome, execute_staging=True)
    ) == 1
    assert calls == []
    document = json.loads(outcome.read_text(encoding="utf-8"))
    assert document["failed_phase"] == "upload"
    assert document["error_type"] == "OSError"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"staging_namespace": "nmdc.other"}, "exactly match"),
        ({"bronze_prefix": "../canonical"}, "unsafe path segment"),
        ({"progress_key": "elsewhere/progress.jsonl"}, "children"),
        ({"tenant": "nmdc;drop"}, "safe SQL identifier"),
        ({"bucket": "CDM_LAKE"}, "safe S3 bucket name"),
    ],
)
def test_unsafe_targets_are_rejected_before_execution(parquet_dir, changes, message):
    with pytest.raises(ingest_dataset.ConfigurationError, match=message):
        ingest_dataset.run(_args(parquet_dir, **changes))


def test_mixed_source_directory_is_rejected(parquet_dir):
    (parquet_dir / "legacy.tsv").write_text("id\n1\n", encoding="utf-8")

    with pytest.raises(ingest_dataset.ConfigurationError, match="mixed"):
        ingest_dataset.run(_args(parquet_dir))


def test_uppercase_parquet_extension_is_rejected(tmp_path):
    (tmp_path / "biosample_set.PARQUET").write_bytes(b"PAR1")

    with pytest.raises(ingest_dataset.ConfigurationError, match="lowercase .parquet"):
        ingest_dataset.run(_args(tmp_path))


def test_outcome_is_immutable(parquet_dir, tmp_path, monkeypatch):
    outcome = tmp_path / "outcome.json"
    outcome.write_text("existing", encoding="utf-8")
    monkeypatch.setattr(ingest_dataset, "initialize", lambda: ("spark", "minio"))

    with pytest.raises(ingest_dataset.ConfigurationError, match="already exists"):
        ingest_dataset.run(_args(parquet_dir, outcome, execute_staging=True))
