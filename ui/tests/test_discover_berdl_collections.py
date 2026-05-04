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


def test_missing_helpers_returns_clear_failure(monkeypatch, capsys):
    module = _load_script_module()
    monkeypatch.setattr(
        module,
        "_load_berdl_helpers",
        lambda: (_ for _ in ()).throw(ImportError("missing helper")),
    )

    code = module.main([])

    assert code == 2
    assert "berdl_notebook_utils is required" in capsys.readouterr().err


def test_discovery_uses_berdl_helpers_and_groups_schema(monkeypatch):
    module = _load_script_module()
    calls = []

    class Helpers:
        @staticmethod
        def get_databases():
            calls.append(("get_databases",))
            return {"databases": ["kbase_ke_pangenome"]}

        @staticmethod
        def get_tables(database):
            calls.append(("get_tables", database))
            return {"tables": ["genome", "broken_table"]}

        @staticmethod
        def get_table_schema(database, table):
            calls.append(("get_table_schema", database, table))
            if table == "broken_table":
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

    monkeypatch.setattr(module, "_load_berdl_helpers", lambda: Helpers)

    snapshot = module.discover_collections(include_schemas=True)

    assert snapshot["discovery_method"] == "berdl_notebook_utils"
    assert snapshot["source_url"] == "berdl-notebook-utils"
    assert snapshot["tenants"][0]["id"] == "kbase"
    collection = snapshot["tenants"][0]["collections"][0]
    assert collection["id"] == "kbase_ke_pangenome"
    assert collection["tables"][0]["columns"][0]["name"] == "genome_id"
    assert "broken_table schema failed" in collection["discovery_errors"][0]
    assert calls == [
        ("get_databases",),
        ("get_tables", "kbase_ke_pangenome"),
        ("get_table_schema", "kbase_ke_pangenome", "genome"),
        ("get_table_schema", "kbase_ke_pangenome", "broken_table"),
    ]


def test_discovery_can_skip_schema_helpers(monkeypatch):
    module = _load_script_module()
    calls = []

    class Helpers:
        @staticmethod
        def get_databases():
            return [{"database": "kbase_ke_pangenome"}]

        @staticmethod
        def get_tables(database):
            calls.append(("get_tables", database))
            return [("genome", "Genome table.")]

        @staticmethod
        def get_table_schema(database, table):
            calls.append(("get_table_schema", database, table))
            return []

    monkeypatch.setattr(module, "_load_berdl_helpers", lambda: Helpers)

    snapshot = module.discover_collections(include_schemas=False)

    assert snapshot["tenants"][0]["collections"][0]["tables"] == [
        {
            "name": "genome",
            "description": "Genome table.",
            "row_count": None,
            "columns": [],
        }
    ]
    assert calls == [("get_tables", "kbase_ke_pangenome")]


def test_cli_default_writes_snapshot_without_auth_token(tmp_path, monkeypatch):
    module = _load_script_module()
    output = tmp_path / "snapshot.json"
    monkeypatch.delenv("KBASE_AUTH_TOKEN", raising=False)

    class Helpers:
        @staticmethod
        def get_databases():
            return ["kbase_genomes"]

        @staticmethod
        def get_tables(database):
            return ["genomes"]

        @staticmethod
        def get_table_schema(database, table):
            raise AssertionError("schemas should be skipped")

    monkeypatch.setattr(module, "_load_berdl_helpers", lambda: Helpers)

    code = module.main(["--output", str(output), "--skip-schemas"])

    assert code == 0
    snapshot = json.loads(output.read_text())
    assert snapshot["discovery_method"] == "berdl_notebook_utils"
    assert snapshot["tenants"][0]["collections"][0]["id"] == "kbase_genomes"


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
