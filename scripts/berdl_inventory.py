#!/usr/bin/env python3
"""Print BERDL inventory: tenant, database, table count, sample table names.

On-cluster: uses berdl_notebook_utils.get_db_structure() (access-aware,
filtered to what the authenticated user can see).
Off-cluster: falls back to SHOW DATABASES + SHOW TABLES IN <db> via the
local get_spark_session() drop-in (which auto-spawns the JH server).

Output is a markdown table grouped by tenant. Examples:

    python scripts/berdl_inventory.py                # auto-detect
    python scripts/berdl_inventory.py --sample 5     # show up to 5 table names
    python scripts/berdl_inventory.py --no-emoji     # plain text
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict


def _split_tenant(database: str) -> str:
    """Tenant = the prefix before the first underscore, or '(other)' if none."""
    return database.split("_", 1)[0] if "_" in database else "(other)"


def fetch_on_cluster() -> dict[str, list[str]]:
    """Use berdl_notebook_utils for access-aware discovery."""
    import berdl_notebook_utils

    structure = berdl_notebook_utils.get_db_structure(
        with_schema=False, return_json=False, filter_by_namespace=True
    )
    return {db: list(tables) for db, tables in structure.items()}


def fetch_off_cluster() -> dict[str, list[str]]:
    """Fall back to SHOW DATABASES + SHOW TABLES IN <db>. Auto-spawns JH server."""
    from get_spark_session import get_spark_session  # local drop-in

    spark = get_spark_session()
    db_rows = spark.sql("SHOW DATABASES").collect()
    databases = [row["namespace"] for row in db_rows]
    structure: dict[str, list[str]] = {}
    for db in databases:
        try:
            rows = spark.sql(f"SHOW TABLES IN `{db}`").collect()
            structure[db] = [row["tableName"] for row in rows]
        except Exception as exc:  # noqa: BLE001 — surface but continue
            print(f"# WARN: could not list tables for {db}: {exc}", file=sys.stderr)
            structure[db] = []
    return structure


def format_inventory(
    structure: dict[str, list[str]], sample: int = 3, emoji: bool = True
) -> str:
    """Render the inventory as a markdown report grouped by tenant."""
    if not structure:
        return "_No accessible databases. Check KBASE_AUTH_TOKEN and tenant membership._"

    by_tenant: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    for db, tables in structure.items():
        by_tenant[_split_tenant(db)].append((db, sorted(tables)))

    total_dbs = sum(len(v) for v in by_tenant.values())
    total_tables = sum(len(t) for v in by_tenant.values() for _, t in v)
    header_icon = "📦 " if emoji else ""
    section_icon = "🏷️  " if emoji else ""

    lines = [
        f"## {header_icon}BERDL Inventory",
        "",
        f"_{len(by_tenant)} tenants · {total_dbs} databases · {total_tables} tables_",
        "",
    ]

    for tenant in sorted(by_tenant):
        lines.append(f"### {section_icon}{tenant}")
        lines.append("")
        lines.append("| Database | # Tables | Sample table names |")
        lines.append("|----------|---------:|--------------------|")
        for db, tables in sorted(by_tenant[tenant]):
            n = len(tables)
            shown = tables[:sample]
            sample_str = ", ".join(f"`{t}`" for t in shown)
            if n > sample:
                sample_str += f", … (+{n - sample} more)"
            if not shown:
                sample_str = "_(empty or inaccessible)_"
            lines.append(f"| `{db}` | {n} | {sample_str} |")
        lines.append("")

    lines.append(
        "> Run `DESCRIBE EXTENDED <db>.<table>` for per-table comments / properties, "
        "`DESCRIBE DATABASE EXTENDED <db>` for a database description."
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--sample",
        type=int,
        default=3,
        help="Number of sample table names to show per database (default: 3).",
    )
    p.add_argument(
        "--no-emoji",
        action="store_true",
        help="Plain text output without emoji markers.",
    )
    p.add_argument(
        "--off-cluster",
        action="store_true",
        help="Force off-cluster path (skip the on-cluster import attempt).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    structure: dict[str, list[str]] | None = None
    if not args.off_cluster:
        try:
            structure = fetch_on_cluster()
        except ImportError:
            structure = None
    if structure is None:
        try:
            structure = fetch_off_cluster()
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to fetch inventory: {exc}", file=sys.stderr)
            return 1

    print(format_inventory(structure, sample=args.sample, emoji=not args.no_emoji))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
