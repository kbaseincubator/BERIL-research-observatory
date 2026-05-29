#!/usr/bin/env python3
"""Discover BERDL tenants, databases, tables, and schemas into a UI snapshot."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://hub.berdl.kbase.us/apis/mcp"

TENANT_NAMES = {
    "kbase": "KBase",
    "kescience": "KE Science",
    "enigma": "ENIGMA",
    "nmdc": "NMDC",
    "phagefoundry": "PhageFoundry",
    "planetmicrobe": "PlanetMicrobe",
    "protect": "PROTECT",
    "globalusers": "Development/Test",
}

USER_FACING_DATABASE_IDS = {
    "arkinlab_dbcan",
    "arkinlab_microbeatlas",
    "arkinlab_mobilome",
    "bervodata_chess",
    "bervodata_fao_soils",
    "bervodata_hwsd2",
    "enigma_coral",
    "enigma_genome_depot_enigma",
    "kbase_all_the_bacteria",
    "kbase_genomes",
    "kbase_ke_pangenome",
    "kbase_msd_biochemistry",
    "kbase_ontology_source",
    "kbase_phenotype",
    "kbase_uniprot",
    "kbase_uniref100",
    "kbase_uniref50",
    "kbase_uniref90",
    "kescience_alphafold",
    "kescience_bacdive",
    "kescience_fitnessbrowser",
    "kescience_interpro",
    "kescience_mgnify",
    "kescience_paperblast",
    "kescience_pdb",
    "kescience_pubmed",
    "kescience_webofmicrobes",
    "msyscolo_grow",
    "netl_pw_dna",
    "nmdc_arkin",
    "nmdc_metadata",
    "nmdc_ncbi_biosamples",
    "nmdc_results",
    "pangenome_bakta",
    "phagefoundry_acinetobacter_genome_browser",
    "phagefoundry_ecoliphages_genomedepot",
    "phagefoundry_ecoliphagesgenomedepot",
    "phagefoundry_klebsiella_genome_browser_genomedepot",
    "phagefoundry_paeruginosa_genome_browser",
    "phagefoundry_pviridiflava_genome_browser",
    "phagefoundry_strain_modelling",
    "planetmicrobe_planetmicrobe",
    "planetmicrobe_planetmicrobe_raw",
    "plantmicrobeinterfaces_gtdb_mapping",
    "protect_genomedepot",
    "protect_integration",
    "protect_mind",
    "usgs_produced_waters",
}


def read_auth_token(env_path: Path | None = None) -> str | None:
    """Read KBASE_AUTH_TOKEN from environment or a simple .env file."""
    if os.environ.get("KBASE_AUTH_TOKEN"):
        return os.environ["KBASE_AUTH_TOKEN"]
    env_path = env_path or Path(".env")
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "KBASE_AUTH_TOKEN":
            return value.strip().strip('"').strip("'")
    return None


def _post_json(url: str, token: str, payload: dict[str, Any], timeout: float) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("invalid JSON response") from exc


def _load_berdl_helpers() -> Any | None:
    """Returns berdl_notebook_utils on-cluster, None off-cluster."""
    try:
        import berdl_notebook_utils
        return berdl_notebook_utils
    except ImportError:
        return None


def discover_collections(
    *,
    max_databases: int | None = None,
    include_schemas: bool = True,
    token: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Discover databases, tables, and schemas.

    Uses berdl_notebook_utils on-cluster (access-aware).
    Falls back to the REST API when berdl_notebook_utils is unavailable (off-cluster).
    """
    helpers = _load_berdl_helpers()

    if helpers is not None:
        def _get_databases():
            return _extract_databases(helpers.get_databases())

        def _get_tables(db_id):
            return _extract_tables(helpers.get_tables(db_id))

        def _get_schema(db_id, table_name):
            return _extract_columns(helpers.get_table_schema(db_id, table_name))

        discovery_method = "berdl_notebook_utils"
        source_url = "berdl-notebook-utils"
    else:
        if not token:
            raise RuntimeError(
                "berdl_notebook_utils is not available. "
                "Set KBASE_AUTH_TOKEN for off-cluster REST discovery."
            )
        base_url = base_url.rstrip("/")

        def _get_databases():
            return _extract_databases(
                _post_json(
                    f"{base_url}/delta/databases/list", token,
                    {"use_hms": True, "filter_by_namespace": True}, timeout,
                )
            )

        def _get_tables(db_id):
            return _extract_tables(
                _post_json(
                    f"{base_url}/delta/databases/tables/list", token,
                    {"database": db_id, "use_hms": True}, timeout,
                )
            )

        def _get_schema(db_id, table_name):
            return _extract_columns(
                _post_json(
                    f"{base_url}/delta/databases/tables/schema", token,
                    {"database": db_id, "table": table_name}, timeout,
                )
            )

        discovery_method = "rest"
        source_url = base_url

    databases = sorted(_get_databases(), key=lambda item: item["id"])
    if max_databases is not None:
        databases = databases[:max_databases]

    tenants: dict[str, dict[str, Any]] = {}
    for database in databases:
        tenant_id = database.get("tenant_id") or infer_tenant_id(database["id"])
        tenant = tenants.setdefault(
            tenant_id,
            {
                "id": tenant_id,
                "name": TENANT_NAMES.get(tenant_id, tenant_id.replace("_", " ").title()),
                "collections": [],
            },
        )
        collection = {
            "id": database["id"],
            "name": database.get("name") or title_from_id(database["id"]),
            "description": database.get("description", ""),
            "provider": database.get("provider"),
            "tables": [],
            "discovery_errors": [],
        }
        try:
            tables = _get_tables(database["id"])
        except Exception as exc:
            collection["discovery_errors"].append(
                f"table list failed: {_format_error(exc)}"
            )
            tables = []

        for table in tables:
            table_record = {
                "name": table["name"],
                "description": table.get("description", ""),
                "row_count": table.get("row_count"),
                "columns": [],
            }
            if not include_schemas:
                collection["tables"].append(table_record)
                continue
            try:
                table_record["columns"] = _get_schema(database["id"], table["name"])
            except Exception as exc:
                collection["discovery_errors"].append(
                    f"{table['name']} schema failed: {_format_error(exc)}"
                )
            collection["tables"].append(table_record)

        tenant["collections"].append(collection)

    return {
        "schema_version": 1,
        "source_url": source_url,
        "discovery_method": discovery_method,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "tenants": list(tenants.values()),
    }


def write_snapshot_atomic(snapshot: dict[str, Any], output: Path) -> None:
    """Write JSON snapshot atomically to avoid partial config files."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        delete=False,
    ) as handle:
        json.dump(snapshot, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    Path(temp_name).replace(output)


def filter_user_facing_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Keep the current curated set of user-facing BERDL databases."""
    filtered = dict(snapshot)
    filtered_tenants = []
    for tenant in snapshot.get("tenants", []):
        collections = [
            collection
            for collection in tenant.get("collections", [])
            if collection.get("id") in USER_FACING_DATABASE_IDS
        ]
        if not collections:
            continue
        tenant_record = dict(tenant)
        tenant_record["collections"] = collections
        filtered_tenants.append(tenant_record)
    filtered["tenants"] = filtered_tenants
    filtered["visibility_filter"] = "user_facing_v1"
    filtered["visibility_filter_note"] = (
        "Excludes test, demo, startup, default, globalusers, personal u_*__*, "
        "and uncategorized namespaces until curated."
    )
    return filtered


def infer_tenant_id(database_id: str) -> str:
    """Infer tenant from BERDL database naming conventions."""
    if database_id.startswith("u_") and "__" in database_id:
        return database_id.split("__", 1)[0]
    if database_id.startswith("kbase_"):
        return "kbase"
    if database_id.startswith("kescience_"):
        return "kescience"
    return database_id.split("_", 1)[0]


def title_from_id(database_id: str) -> str:
    return database_id.replace("_", " ").title()


def _format_error(exc: Exception, max_length: int = 500) -> str:
    text = " ".join(str(exc).split())
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def _extract_databases(payload: Any) -> list[dict[str, Any]]:
    items = _first_list(payload, ("databases", "database", "data", "result", "items"))
    databases = []
    for item in items:
        if isinstance(item, str):
            databases.append({"id": item})
            continue
        if isinstance(item, tuple):
            database_id = item[0] if item else None
            if database_id:
                databases.append(
                    {
                        "id": str(database_id),
                        "name": str(item[1]) if len(item) > 1 and item[1] else None,
                        "description": str(item[2]) if len(item) > 2 and item[2] else "",
                        "provider": None,
                        "tenant_id": None,
                    }
                )
            continue
        if not isinstance(item, dict):
            continue
        database_id = (
            item.get("database")
            or item.get("database_name")
            or item.get("name")
            or item.get("id")
            or item.get("namespace")
        )
        if not database_id:
            continue
        databases.append(
            {
                "id": str(database_id),
                "name": item.get("display_name") or item.get("label"),
                "description": item.get("description") or "",
                "provider": item.get("provider"),
                "tenant_id": item.get("tenant") or item.get("tenant_id"),
            }
        )
    return databases


def _extract_tables(payload: Any) -> list[dict[str, Any]]:
    items = _first_list(payload, ("tables", "table", "data", "result", "items"))
    tables = []
    for item in items:
        if isinstance(item, str):
            tables.append({"name": item})
            continue
        if isinstance(item, tuple):
            table_name = item[0] if item else None
            if table_name:
                tables.append(
                    {
                        "name": str(table_name),
                        "description": str(item[1]) if len(item) > 1 and item[1] else "",
                        "row_count": item[2] if len(item) > 2 else None,
                    }
                )
            continue
        if not isinstance(item, dict):
            continue
        table_name = item.get("table") or item.get("table_name") or item.get("name")
        if not table_name:
            continue
        tables.append(
            {
                "name": str(table_name),
                "description": item.get("description") or "",
                "row_count": item.get("row_count") or item.get("rows"),
            }
        )
    return tables


def _extract_columns(payload: Any) -> list[dict[str, str | None]]:
    items = _first_list(payload, ("columns", "schema", "fields", "data", "result"))
    columns = []
    for item in items:
        if isinstance(item, str):
            columns.append({"name": item, "data_type": "", "description": None})
            continue
        if isinstance(item, tuple):
            column_name = item[0] if item else None
            if column_name:
                columns.append(
                    {
                        "name": str(column_name),
                        "data_type": str(item[1]) if len(item) > 1 and item[1] else "",
                        "description": str(item[2]) if len(item) > 2 and item[2] else None,
                    }
                )
            continue
        if not isinstance(item, dict):
            continue
        column_name = item.get("name") or item.get("column") or item.get("column_name")
        if not column_name:
            continue
        columns.append(
            {
                "name": str(column_name),
                "data_type": str(item.get("type") or item.get("data_type") or ""),
                "description": item.get("description") or item.get("comment"),
            }
        )
    return columns


def _first_list(payload: Any, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, tuple):
        return list(payload)
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    if _looks_like_record(payload):
        return [payload]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple)):
            return list(value)
        if isinstance(value, dict):
            nested = _first_list(value, keys)
            if nested:
                return nested
    if any(key in payload for key in keys):
        return [payload]
    for value in payload.values():
        if isinstance(value, dict):
            nested = _first_list(value, keys)
            if nested:
                return nested
    return []


def _looks_like_record(payload: dict[str, Any]) -> bool:
    record_keys = {
        "id",
        "name",
        "database_name",
        "namespace",
        "table_name",
        "column",
        "column_name",
        "type",
        "data_type",
    }
    if any(key in payload for key in record_keys):
        return True
    for key in ("database", "table"):
        if key in payload and not isinstance(payload[key], (dict, list, tuple)):
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ui/config/berdl_collections_snapshot.json"),
        help="Snapshot JSON output path.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="BERDL MCP base URL (used for off-cluster REST fallback).",
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0,
        help="REST request timeout in seconds (off-cluster only).",
    )
    parser.add_argument(
        "--max-databases",
        type=int,
        help="Optional debugging cap on discovered databases.",
    )
    parser.add_argument(
        "--skip-schemas",
        action="store_true",
        help="Collect databases and tables but skip schema discovery.",
    )
    parser.add_argument(
        "--include-non-user-facing",
        action="store_true",
        help="Keep every discovered namespace instead of the curated user-facing set.",
    )
    parser.add_argument(
        "--env-file", type=Path, default=Path(".env"),
        help="Path to .env file containing KBASE_AUTH_TOKEN (off-cluster fallback).",
    )
    args = parser.parse_args(argv)

    token = read_auth_token(args.env_file)
    try:
        snapshot = discover_collections(
            max_databases=args.max_databases,
            include_schemas=not args.skip_schemas,
            token=token,
            base_url=args.base_url,
            timeout=args.timeout,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not args.include_non_user_facing:
        snapshot = filter_user_facing_snapshot(snapshot)
    write_snapshot_atomic(snapshot, args.output)
    collection_count = sum(len(t["collections"]) for t in snapshot["tenants"])
    print(
        f"Wrote {collection_count} collections across "
        f"{len(snapshot['tenants'])} tenants to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
