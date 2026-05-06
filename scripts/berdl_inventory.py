#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyspark",
#   "spark_connect_remote @ git+https://github.com/BERDataLakehouse/spark_connect_remote.git",
#   "berdl_remote @ git+https://github.com/BERDataLakehouse/berdl_remote.git",
# ]
# ///
"""Print BERDL inventory: tenant metadata, databases, table counts, sample tables.

On-cluster: uses berdl_notebook_utils for access-aware discovery and tenant
metadata (display name, description, website, organization, stewards, members).
Off-cluster: falls back to SHOW DATABASES + SHOW TABLES IN <db> via the local
get_spark_session() drop-in (which auto-spawns the JH server). Tenant metadata
is unavailable off-cluster — fallback groups by the prefix before the first
underscore.

Off-cluster invocation: `uv run scripts/berdl_inventory.py` — uv resolves the
PEP 723 dependencies above into an isolated cache, no manual venv activation
required. On-cluster, the BERDL JupyterHub kernel already has all imports;
just run with the kernel's Python: `python scripts/berdl_inventory.py`.

Output is a markdown report grouped by tenant. Examples:

    uv run scripts/berdl_inventory.py                # auto-detect
    uv run scripts/berdl_inventory.py --sample 5     # show up to 5 table names
    uv run scripts/berdl_inventory.py --with-members # include steward / RW / RO lists
    uv run scripts/berdl_inventory.py --no-emoji     # plain text
"""

from __future__ import annotations

import argparse
import socket
import sys
from collections import defaultdict
from dataclasses import dataclass, field


# Tenants that exist but should never appear in the user-facing inventory —
# 'globalusers' is a shared sandbox space whose contents tend to be noise for
# orientation. Filtered from both the database listing and the "other tenants"
# footer.
_HIDDEN_TENANTS = frozenset({"globalusers"})


@dataclass
class TenantInfo:
    """Metadata for a single tenant — populated on-cluster from berdl_notebook_utils."""

    name: str
    display_name: str = ""
    description: str = ""
    website: str = ""
    organization: str = ""
    namespace_prefix: str = ""
    stewards: list[str] = field(default_factory=list)
    members_rw: list[str] = field(default_factory=list)
    members_ro: list[str] = field(default_factory=list)


def _split_tenant_prefix(database: str) -> str:
    """Fallback tenant key when no metadata is available."""
    return database.split("_", 1)[0] if "_" in database else "(other)"


def _is_on_cluster(host: str = "spark.berdl.kbase.us", port: int = 443, timeout: float = 2.0) -> bool:
    """Same connectivity probe scripts/detect_berdl_environment.py uses."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, OSError):
        return False


def fetch_structure_on_cluster() -> dict[str, list[str]]:
    """Use berdl_notebook_utils.get_db_structure for access-aware database+table listing."""
    import berdl_notebook_utils

    structure = berdl_notebook_utils.get_db_structure(
        with_schema=False, return_json=False, filter_by_namespace=True
    )
    return {db: list(tables) for db, tables in structure.items()}


def fetch_tenants_on_cluster() -> list[TenantInfo]:
    """Use berdl_notebook_utils.list_tenants + get_tenant_detail for tenant metadata.

    list_tenants() returns every tenant in the system as data; the inventory
    output stays access-aware because format_inventory only emits a section for
    a tenant whose namespace_prefix matches at least one database in the
    access-aware structure dict (filter_by_namespace=True at the database side).

    Note: show_my_tenants() is a *display* helper (prints + returns None), so
    it can't be used here. Returns [] if the helpers raise.
    """
    try:
        from berdl_notebook_utils import list_tenants, get_tenant_detail
    except ImportError:
        return []

    out: list[TenantInfo] = []
    try:
        tenants = list_tenants()
    except Exception as exc:  # noqa: BLE001 — surface but don't crash
        print(f"# WARN: list_tenants() failed: {exc}", file=sys.stderr)
        return []
    if tenants is None:
        return []

    for t in tenants:
        info = TenantInfo(
            name=getattr(t, "tenant_name", str(t)),
            display_name=getattr(t, "display_name", "") or "",
            description=getattr(t, "description", "") or "",
            website=getattr(t, "website", "") or "",
            organization=getattr(t, "organization", "") or "",
        )
        try:
            detail = get_tenant_detail(info.name)
        except Exception as exc:  # noqa: BLE001
            print(f"# WARN: get_tenant_detail({info.name}) failed: {exc}", file=sys.stderr)
            out.append(info)
            continue

        storage = getattr(detail, "storage_paths", None)
        if storage is not None:
            info.namespace_prefix = getattr(storage, "namespace_prefix", "") or ""

        info.stewards = sorted(
            getattr(s, "username", "") for s in getattr(detail, "stewards", []) or []
        )
        for m in getattr(detail, "members", []) or []:
            level = getattr(getattr(m, "access_level", None), "value", "")
            user = getattr(m, "username", "")
            if not user:
                continue
            if level == "read_write":
                info.members_rw.append(user)
            elif level == "read_only":
                info.members_ro.append(user)
        info.members_rw.sort()
        info.members_ro.sort()
        out.append(info)
    return out


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
        except Exception as exc:  # noqa: BLE001
            print(f"# WARN: could not list tables for {db}: {exc}", file=sys.stderr)
            structure[db] = []
    return structure


def assign_databases_to_tenants(
    structure: dict[str, list[str]], tenants: list[TenantInfo]
) -> dict[str, list[tuple[str, list[str]]]]:
    """Map each database to its tenant.

    Uses the tenant's namespace_prefix when available (longest match wins, so
    'kbase_dev_' beats 'kbase_'); falls back to the underscore-prefix heuristic
    for any database that doesn't match a known prefix.
    """
    by_tenant: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)

    # Sort tenants by prefix length (longest first) to handle nested prefixes correctly.
    prefixed = sorted(
        [t for t in tenants if t.namespace_prefix],
        key=lambda t: len(t.namespace_prefix),
        reverse=True,
    )

    for db, tables in structure.items():
        sorted_tables = sorted(tables)
        matched: str | None = None
        for t in prefixed:
            if db.startswith(t.namespace_prefix):
                matched = t.name
                break
        if matched is None:
            matched = _split_tenant_prefix(db)
        by_tenant[matched].append((db, sorted_tables))

    # Only tenants with at least one accessible database appear in the output —
    # showing tenants the user can't see anything in is noise, and the structure
    # dict is already filtered by access (filter_by_namespace=True on-cluster).
    return by_tenant


def format_inventory(
    structure: dict[str, list[str]],
    tenants: list[TenantInfo] | None = None,
    sample: int = 3,
    emoji: bool = True,
    with_members: bool = False,
) -> str:
    """Render the inventory as a markdown report grouped by tenant."""
    tenants = tenants or []

    # Drop databases whose tenant is in the hidden set (e.g. globalusers
    # sandbox — contents are noise for orientation). Match both via
    # namespace_prefix and the underscore-split fallback.
    hidden_prefixes = tuple(
        t.namespace_prefix
        for t in tenants
        if t.namespace_prefix and t.name in _HIDDEN_TENANTS
    )
    structure = {
        db: tables
        for db, tables in structure.items()
        if not (
            (hidden_prefixes and db.startswith(hidden_prefixes))
            or _split_tenant_prefix(db) in _HIDDEN_TENANTS
        )
    }

    by_tenant = assign_databases_to_tenants(structure, tenants)
    tenant_meta = {t.name: t for t in tenants}

    if not by_tenant:
        return (
            "_No accessible databases. Check KBASE_AUTH_TOKEN and tenant membership._"
        )

    total_dbs = sum(len(v) for v in by_tenant.values())
    total_tables = sum(len(t) for v in by_tenant.values() for _, t in v)
    visible_tenants = sum(1 for v in by_tenant.values() if v) or len(by_tenant)

    header_icon = "📦 " if emoji else ""
    section_icon = "🏷️  " if emoji else ""

    lines = [
        f"## {header_icon}BERDL Inventory",
        "",
        f"_{visible_tenants} tenants · {total_dbs} databases · {total_tables} tables_",
        "",
    ]

    for tenant_key in sorted(by_tenant):
        rows = by_tenant[tenant_key]
        info = tenant_meta.get(tenant_key)

        # Section header
        if info and info.display_name and info.display_name != info.name:
            lines.append(f"### {section_icon}{info.name} — {info.display_name}")
        else:
            lines.append(f"### {section_icon}{tenant_key}")
        lines.append("")

        # Tenant metadata block (only when we have it)
        if info:
            meta_lines = []
            if info.organization:
                meta_lines.append(f"- **Organization:** {info.organization}")
            if info.description:
                meta_lines.append(f"- **Description:** {info.description}")
            if info.website:
                meta_lines.append(f"- **Website:** {info.website}")
            if info.stewards:
                meta_lines.append(f"- **Stewards:** {', '.join(info.stewards)}")
            if with_members:
                if info.members_rw:
                    meta_lines.append(
                        f"- **Read-write members ({len(info.members_rw)}):** {', '.join(info.members_rw)}"
                    )
                if info.members_ro:
                    meta_lines.append(
                        f"- **Read-only members ({len(info.members_ro)}):** {', '.join(info.members_ro)}"
                    )
            elif info.members_rw or info.members_ro:
                meta_lines.append(
                    f"- **Members:** {len(info.members_rw)} read-write, "
                    f"{len(info.members_ro)} read-only "
                    "(use `--with-members` to list)"
                )
            if meta_lines:
                lines.extend(meta_lines)
                lines.append("")

        # Database table
        if rows:
            lines.append("| Database | # Tables | Sample table names |")
            lines.append("|----------|---------:|--------------------|")
            for db, tables in sorted(rows):
                n = len(tables)
                shown = tables[:sample]
                sample_str = ", ".join(f"`{t}`" for t in shown)
                if n > sample:
                    sample_str += f", … (+{n - sample} more)"
                if not shown:
                    sample_str = "_(empty or inaccessible)_"
                lines.append(f"| `{db}` | {n} | {sample_str} |")
        else:
            lines.append("_(no accessible databases in this tenant)_")
        lines.append("")

    # Brief footer: tenants in the system the user has no accessible databases
    # in. Hidden tenants (e.g. globalusers) are excluded from this list too.
    if tenants:
        rendered = set(by_tenant)
        other_names = sorted(
            t.name
            for t in tenants
            if t.name not in rendered and t.name not in _HIDDEN_TENANTS
        )
        if other_names:
            lines.append(
                f"_Other tenants in BERDL (no access): {', '.join(other_names)}._"
            )
            lines.append("")

    lines.append(
        "> Run `DESCRIBE DATABASE EXTENDED <db>` for a database description, "
        "`DESCRIBE EXTENDED <db>.<table>` for table-level comments / properties."
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
        "--with-members",
        action="store_true",
        help="Include steward / read-write / read-only member lists per tenant.",
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
    tenants: list[TenantInfo] = []

    if not args.off_cluster:
        try:
            structure = fetch_structure_on_cluster()
            tenants = fetch_tenants_on_cluster()
        except ImportError:
            # If we're on-cluster but berdl_notebook_utils isn't importable,
            # the user almost certainly invoked us under `uv run`, which
            # creates an isolated venv that doesn't include the JupyterHub
            # kernel's pre-installed packages. Falling through to the
            # off-cluster path here would silently produce broken output —
            # surface the real fix instead.
            if _is_on_cluster():
                print(
                    "[berdl_inventory] On-cluster, but berdl_notebook_utils "
                    "isn't importable in this Python. You're probably running "
                    "under `uv run`, which uses an isolated venv that doesn't "
                    "see the JupyterHub kernel's packages.\n\n"
                    "  → Re-run as: python scripts/berdl_inventory.py\n\n"
                    "Reserve `uv run` for off-cluster invocations only.",
                    file=sys.stderr,
                )
                return 2
            structure = None
    if structure is None:
        try:
            structure = fetch_off_cluster()
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to fetch inventory: {exc}", file=sys.stderr)
            return 1

    print(
        format_inventory(
            structure,
            tenants=tenants,
            sample=args.sample,
            emoji=not args.no_emoji,
            with_members=args.with_members,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
