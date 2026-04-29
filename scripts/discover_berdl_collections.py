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
DEFAULT_SPARK_HOST = "metrics.berdl.kbase.us"
DEFAULT_SPARK_PORT = 443

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


def discover_collections(
    token: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Discover databases and schemas from BERDL REST endpoints."""
    base_url = base_url.rstrip("/")
    databases = _extract_databases(
        _post_json(
            f"{base_url}/delta/databases/list",
            token,
            {"use_hms": True, "filter_by_namespace": True},
            timeout,
        )
    )

    tenants: dict[str, dict[str, Any]] = {}
    for database in sorted(databases, key=lambda item: item["id"]):
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
            tables = _extract_tables(
                _post_json(
                    f"{base_url}/delta/databases/tables/list",
                    token,
                    {"database": database["id"], "use_hms": True},
                    timeout,
                )
            )
        except RuntimeError as exc:
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
            try:
                schema_payload = _post_json(
                    f"{base_url}/delta/databases/tables/schema",
                    token,
                    {"database": database["id"], "table": table["name"]},
                    timeout,
                )
                table_record["columns"] = _extract_columns(schema_payload)
            except RuntimeError as exc:
                collection["discovery_errors"].append(
                    f"{table['name']} schema failed: {_format_error(exc)}"
                )
            collection["tables"].append(table_record)

        tenant["collections"].append(collection)

    return {
        "schema_version": 1,
        "source_url": base_url,
        "discovery_method": "rest",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "tenants": list(tenants.values()),
    }


def discover_collections_from_spark(
    *,
    berdl_proxy: bool = True,
    ensure_hub: bool = True,
    host_template: str = DEFAULT_SPARK_HOST,
    port: int = DEFAULT_SPARK_PORT,
    max_databases: int | None = None,
    include_schemas: bool = True,
) -> dict[str, Any]:
    """Discover BERDL databases through Spark SQL metadata commands."""
    try:
        from get_spark_session import get_spark_session
    except Exception as exc:  # pragma: no cover - exercised by CLI environment
        raise RuntimeError(
            "Cannot import get_spark_session. Run scripts/bootstrap_client.sh first."
        ) from exc

    spark = get_spark_session(
        app_name="berdl-collection-discovery",
        berdl_proxy=berdl_proxy,
        ensure_hub=ensure_hub,
        host_template=host_template,
        port=port,
    )
    database_ids = sorted(
        {
            database_id
            for row in spark.sql("SHOW DATABASES").collect()
            if (database_id := _spark_database_name(row))
        }
    )
    if max_databases is not None:
        database_ids = database_ids[:max_databases]

    tenants: dict[str, dict[str, Any]] = {}
    for database_id in database_ids:
        tenant_id = infer_tenant_id(database_id)
        tenant = tenants.setdefault(
            tenant_id,
            {
                "id": tenant_id,
                "name": TENANT_NAMES.get(tenant_id, title_from_id(tenant_id)),
                "collections": [],
            },
        )
        collection = {
            "id": database_id,
            "name": title_from_id(database_id),
            "description": "",
            "provider": tenant["name"],
            "tables": [],
            "discovery_errors": [],
        }
        try:
            table_rows = spark.sql(
                f"SHOW TABLES IN {_quote_identifier(database_id)}"
            ).collect()
            tables = sorted(
                {
                    table_name
                    for row in table_rows
                    if (table_name := _spark_table_name(row))
                }
            )
        except Exception as exc:  # pragma: no cover - depends on live BERDL state
            collection["discovery_errors"].append(
                f"table list failed: {_format_error(exc)}"
            )
            tables = []

        for table_name in tables:
            table_record = {
                "name": table_name,
                "description": "",
                "row_count": None,
                "columns": [],
            }
            if not include_schemas:
                collection["tables"].append(table_record)
                continue
            try:
                schema_rows = spark.sql(
                    "DESCRIBE TABLE "
                    f"{_quote_identifier(database_id)}.{_quote_identifier(table_name)}"
                ).collect()
                table_record["columns"] = _extract_spark_describe_columns(schema_rows)
            except Exception as exc:  # pragma: no cover - depends on live BERDL state
                collection["discovery_errors"].append(
                    f"{table_name} schema failed: {_format_error(exc)}"
                )
            collection["tables"].append(table_record)

        tenant["collections"].append(collection)

    return {
        "schema_version": 1,
        "source_url": f"berdl-spark-connect://{host_template}:{port}",
        "discovery_method": "spark_sql",
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


def _quote_identifier(identifier: str) -> str:
    return f"`{identifier.replace('`', '``')}`"


def _format_error(exc: Exception, max_length: int = 500) -> str:
    text = " ".join(str(exc).split())
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def _spark_row_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "asDict"):
        return row.asDict(recursive=True)
    if isinstance(row, dict):
        return row
    return {}


def _spark_database_name(row: Any) -> str | None:
    data = _spark_row_dict(row)
    value = (
        data.get("namespace")
        or data.get("databaseName")
        or data.get("database")
        or data.get("name")
    )
    return str(value) if value else None


def _spark_table_name(row: Any) -> str | None:
    data = _spark_row_dict(row)
    if data.get("isTemporary"):
        return None
    value = data.get("tableName") or data.get("tableName".lower()) or data.get("table")
    return str(value) if value else None


def _extract_spark_describe_columns(rows: list[Any]) -> list[dict[str, str | None]]:
    columns = []
    for row in rows:
        data = _spark_row_dict(row)
        column_name = data.get("col_name") or data.get("column_name") or data.get("name")
        if not column_name:
            continue
        column_name = str(column_name).strip()
        if not column_name or column_name.startswith("#"):
            continue
        columns.append(
            {
                "name": column_name,
                "data_type": str(data.get("data_type") or data.get("type") or ""),
                "description": data.get("comment") or data.get("description"),
            }
        )
    return columns


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


def _extract_databases(payload: Any) -> list[dict[str, Any]]:
    items = _first_list(payload, ("databases", "database", "data", "result", "items"))
    databases = []
    for item in items:
        if isinstance(item, str):
            databases.append({"id": item})
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
        if not isinstance(item, dict):
            continue
        column_name = item.get("name") or item.get("column") or item.get("column_name")
        if not column_name:
            continue
        columns.append(
            {
                "name": str(column_name),
                "data_type": str(item.get("type") or item.get("data_type") or ""),
                "description": item.get("description"),
            }
        )
    return columns


def _first_list(payload: Any, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _first_list(value, keys)
            if nested:
                return nested
    return []


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
        help="BERDL MCP base URL.",
    )
    parser.add_argument(
        "--source",
        choices=("rest", "spark"),
        default="rest",
        help="Discovery backend. Use spark for live BERDL JupyterHub metadata.",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--spark-host",
        default=DEFAULT_SPARK_HOST,
        help="Spark Connect host template for --source spark.",
    )
    parser.add_argument(
        "--spark-port",
        type=int,
        default=DEFAULT_SPARK_PORT,
        help="Spark Connect port for --source spark.",
    )
    parser.add_argument(
        "--no-berdl-proxy",
        action="store_true",
        help="Do not apply local BERDL proxy defaults for --source spark.",
    )
    parser.add_argument(
        "--no-ensure-hub",
        action="store_true",
        help="Skip berdl-remote login/spawn checks for --source spark.",
    )
    parser.add_argument(
        "--max-databases",
        type=int,
        help="Optional debugging cap on discovered databases.",
    )
    parser.add_argument(
        "--skip-schemas",
        action="store_true",
        help="For --source spark, collect databases and tables but skip DESCRIBE TABLE.",
    )
    parser.add_argument(
        "--include-non-user-facing",
        action="store_true",
        help="Keep every discovered namespace instead of the curated user-facing set.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Optional .env path containing KBASE_AUTH_TOKEN.",
    )
    args = parser.parse_args(argv)

    token = read_auth_token(args.env_file)
    if not token:
        print(
            "KBASE_AUTH_TOKEN is required in the environment or .env file.",
            file=sys.stderr,
        )
        return 2

    if args.source == "spark":
        snapshot = discover_collections_from_spark(
            berdl_proxy=not args.no_berdl_proxy,
            ensure_hub=not args.no_ensure_hub,
            host_template=args.spark_host,
            port=args.spark_port,
            max_databases=args.max_databases,
            include_schemas=not args.skip_schemas,
        )
    else:
        snapshot = discover_collections(token, args.base_url, args.timeout)
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
