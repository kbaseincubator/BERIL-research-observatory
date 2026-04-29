"""Tests for BERDL collection discovery snapshot script."""

import importlib.util
import json
from pathlib import Path


def _load_script_module():
    repo = Path(__file__).resolve().parents[2]
    path = repo / "scripts" / "discover_berdl_collections.py"
    spec = importlib.util.spec_from_file_location("discover_berdl_collections", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_missing_auth_returns_clear_failure(tmp_path, monkeypatch, capsys):
    module = _load_script_module()
    monkeypatch.delenv("KBASE_AUTH_TOKEN", raising=False)

    code = module.main(["--env-file", str(tmp_path / "missing.env")])

    assert code == 2
    assert "KBASE_AUTH_TOKEN is required" in capsys.readouterr().err


def test_discovery_groups_databases_and_keeps_schema_errors(monkeypatch):
    module = _load_script_module()

    def fake_post_json(url, token, payload, timeout):
        if url.endswith("/delta/databases/list"):
            return {"databases": ["kbase_ke_pangenome"]}
        if url.endswith("/delta/databases/tables/list"):
            return {"tables": ["genome", "broken_table"]}
        if payload["table"] == "broken_table":
            raise RuntimeError("schema timeout")
        return {
            "columns": [
                {
                    "name": "genome_id",
                    "type": "string",
                    "description": "Genome identifier.",
                }
            ]
        }

    monkeypatch.setattr(module, "_post_json", fake_post_json)

    snapshot = module.discover_collections("token", "https://example.test/apis/mcp")

    assert snapshot["tenants"][0]["id"] == "kbase"
    collection = snapshot["tenants"][0]["collections"][0]
    assert collection["id"] == "kbase_ke_pangenome"
    assert collection["tables"][0]["columns"][0]["name"] == "genome_id"
    assert "broken_table schema failed" in collection["discovery_errors"][0]


def test_write_snapshot_atomic(tmp_path):
    module = _load_script_module()
    output = tmp_path / "snapshot.json"

    module.write_snapshot_atomic({"tenants": []}, output)

    assert json.loads(output.read_text()) == {"tenants": []}


def test_filter_user_facing_snapshot_removes_scratch_namespaces():
    module = _load_script_module()
    snapshot = {
        "tenants": [
            {
                "id": "kbase",
                "collections": [
                    {"id": "kbase_genomes"},
                    {"id": "kbase_refseq_taxon_api"},
                ],
            },
            {
                "id": "globalusers",
                "collections": [{"id": "globalusers_demo_test"}],
            },
        ]
    }

    filtered = module.filter_user_facing_snapshot(snapshot)

    assert filtered["visibility_filter"] == "user_facing_v1"
    assert filtered["tenants"] == [
        {"id": "kbase", "collections": [{"id": "kbase_genomes"}]}
    ]
