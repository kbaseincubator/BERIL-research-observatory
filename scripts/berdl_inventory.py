#!/usr/bin/env python3
"""Print BERDL inventory: tenant metadata, databases, table counts, sample tables.

This script runs in both BERDL environments — invocation is plain `python` in
either case:

    On-cluster (JupyterHub):
        python scripts/berdl_inventory.py
        # The JH kernel has all imports pre-installed.

    Off-cluster (local machine):
        source .venv-berdl/bin/activate
        python scripts/berdl_inventory.py
        # OR ad-hoc without venv activation:
        # uv run --with pyspark \\
        #   --with "spark_connect_remote @ git+https://github.com/BERDataLakehouse/spark_connect_remote.git" \\
        #   --with "berdl_remote @ git+https://github.com/BERDataLakehouse/berdl_remote.git" \\
        #   scripts/berdl_inventory.py

The script does NOT use a `uv run --script` shebang because uv would create an
isolated venv that excludes the JH kernel's `berdl_notebook_utils`, breaking
on-cluster invocation. Pure off-cluster CLIs that never need the JH kernel
(`run_sql.py`, `export_sql.py`) can use `uv run` safely.

On-cluster: uses berdl_notebook_utils for access-aware discovery and tenant
metadata (display name, description, website, organization, stewards, members).
Off-cluster: enumerates the registered Iceberg catalogs (via the
spark.sql.catalog.* config keys) and lists namespaces + tables in each, via
the local get_spark_session() drop-in (which auto-spawns the JH server).
Tenant metadata is unavailable off-cluster — fallback groups by the catalog
(the prefix before the first dot of each catalog.namespace identifier).

By default the script writes the full markdown report to `data/berdl_inventory.md`
(repo-root-relative) and prints a compact tenant-level summary to stdout. The
split exists because the Claude Code UI auto-collapses long bash output: a
short summary survives display and the full report stays in a stable file the
user can open in an editor regardless of how the chat surfaces stdout.

Examples:

    python scripts/berdl_inventory.py                # summary to stdout, full report to data/berdl_inventory.md
    python scripts/berdl_inventory.py --full         # print full report to stdout (still writes file unless --no-file)
    python scripts/berdl_inventory.py --no-file      # skip the file; only stdout (use with --full to restore legacy)
    python scripts/berdl_inventory.py --output PATH  # override the file path
    python scripts/berdl_inventory.py --sample 5     # show up to 5 table names per database (in the full report)
    python scripts/berdl_inventory.py --with-members # include steward / RW / RO lists in the full report
    python scripts/berdl_inventory.py --no-emoji     # plain text
    python scripts/berdl_inventory.py --refresh      # force a live refetch, rewrite the cache

The result is cached to `data/berdl_inventory_cache.json` (keyed by environment
+ auth-token fingerprint, 7-day TTL) and served before any Spark import, so a
hit costs milliseconds instead of minutes. A fetch in which any database failed
to list is reported as partial and is never cached — a transient auth error must
not pin a lossy inventory for the whole TTL.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import os
import socket
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger("berdl_inventory")

# Warnings here mean *databases or tables went missing* from the snapshot, which
# makes it unsafe to cache. berdl_notebook_utils.get_tables() swallows a
# per-database listing failure and returns [] ("Empty list on lookup failure
# (logged)"), so an auth blip on one namespace looks like an empty database
# rather than an error; the WARNING it logs is the only signal.
structure_logger = logging.getLogger("berdl_inventory.structure")

# Deliberately excludes the parent "berdl_inventory" logger, which carries
# tenant-metadata warnings (a failed get_tenant_detail costs a display name or a
# steward list, not a database). Those must not block caching: a tenant that
# consistently 403s for one user would otherwise disable their cache forever and
# restore the multi-minute startup this cache exists to avoid.
_WATCHED_LOGGERS = ("berdl_notebook_utils", "berdl_inventory.structure")

# Default location for the full markdown report. Resolved against the repo root
# (the parent of the scripts/ directory) so the path is stable regardless of
# the user's CWD when invoking the script.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUTPUT = _REPO_ROOT / "data" / "berdl_inventory.md"

_DEFAULT_CACHE = _REPO_ROOT / "data" / "berdl_inventory_cache.json"

# Default cache lifetime (days). Overridable via --ttl-days or the
# BERDL_INVENTORY_TTL_DAYS env var. The inventory (tenants, databases) changes
# on the order of days, so a week means the stale path is hit almost never.
_DEFAULT_TTL_DAYS = 7


def _now() -> datetime:
    """Current UTC time. Wrapped so tests can monkeypatch the clock."""
    return datetime.now(timezone.utc)


class _FailureWatcher(logging.Handler):
    """Counts warnings emitted during a fetch, and echoes them to stderr.

    Doubles as the display handler: attaching any handler to the watched
    loggers suppresses logging's lastResort stderr output, so this must print
    what it captures or the warnings would vanish.
    """

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        msg = record.getMessage()
        self.messages.append(msg)
        print(f"# WARN: {msg}", file=sys.stderr)

    @property
    def degraded(self) -> bool:
        return bool(self.messages)


@contextlib.contextmanager
def _watch_fetch_failures():
    """Watch the fetch for warnings that mean databases are missing.

    Conservative within that scope: any warning on a watched logger marks the
    fetch degraded, and a degraded snapshot is never cached. A false positive
    costs one uncached run (loud, on stderr); a false negative would pin partial
    data for the whole TTL.
    """
    watcher = _FailureWatcher()
    watched = [logging.getLogger(name) for name in _WATCHED_LOGGERS]
    for lg in watched:
        lg.addHandler(watcher)
    try:
        yield watcher
    finally:
        for lg in watched:
            lg.removeHandler(watcher)


def _resolve_ttl_days(cli_value: int | None) -> int:
    """CLI flag > $BERDL_INVENTORY_TTL_DAYS > default.

    A malformed env var must not take down the inventory: berdl_start shells
    out to this script on every startup, so an unparseable (or exported-but-
    empty) value falls back to the default with a warning rather than raising.
    """
    if cli_value is not None:
        return cli_value
    raw = os.environ.get("BERDL_INVENTORY_TTL_DAYS")
    if raw is None or not raw.strip():
        return _DEFAULT_TTL_DAYS
    try:
        return int(raw)
    except ValueError:
        print(
            f"# WARN: ignoring BERDL_INVENTORY_TTL_DAYS={raw!r} "
            f"(not an integer); using {_DEFAULT_TTL_DAYS} days.",
            file=sys.stderr,
        )
        return _DEFAULT_TTL_DAYS


def _token_fingerprint() -> str:
    """Stable, non-reversible fingerprint of KBASE_AUTH_TOKEN for the cache key.

    The inventory is access-aware (token-scoped), so a cache built under one
    token must not be served under another. We store only a short hash; the
    token itself never touches the cache file. Returns a sentinel when unset.
    """
    token = os.environ.get("KBASE_AUTH_TOKEN") or ""
    if not token:
        return "sha256:none"
    return "sha256:" + hashlib.sha256(token.encode()).hexdigest()[:12]


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
    is_member: bool = False
    is_steward: bool = False


@dataclass
class CacheEntry:
    """A cached inventory snapshot plus the provenance used to validate reuse."""

    environment: str
    token_fp: str
    fetched_at: datetime
    structure: dict[str, list[str]]
    tenants: list[TenantInfo]


def write_cache(path: Path, entry: CacheEntry) -> None:
    """Serialize a CacheEntry to JSON.

    Mirrors the timestamp.json idiom in scripts/build_data_cache.py: a small
    meta block (provenance for validation) plus the payload.
    """
    payload = {
        "meta": {
            "environment": entry.environment,
            "token_fp": entry.token_fp,
            "fetched_at": entry.fetched_at.isoformat(),
        },
        "structure": entry.structure,
        "tenants": [asdict(t) for t in entry.tenants],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def load_cache(path: Path) -> CacheEntry | None:
    """Load a CacheEntry, or None if the file is missing, corrupt, or malformed.

    Any failure is a cache miss, never a crash — the caller refetches.
    """
    try:
        payload = json.loads(path.read_text())
        meta = payload["meta"]
        fetched_at = datetime.fromisoformat(meta["fetched_at"])
        # A tz-naive timestamp parses cleanly but would raise TypeError when
        # subtracted from the aware _now() in _cache_is_fresh. Treat it as
        # malformed here so the "any failure is a miss" contract holds.
        if fetched_at.tzinfo is None:
            return None
        return CacheEntry(
            environment=meta["environment"],
            token_fp=meta["token_fp"],
            fetched_at=fetched_at,
            structure=payload["structure"],
            tenants=[TenantInfo(**t) for t in payload["tenants"]],
        )
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _cache_is_fresh(
    entry: CacheEntry, environment: str, token_fp: str, ttl_days: int, now: datetime
) -> bool:
    """True only if the cache matches the current context and is within TTL."""
    if entry.environment != environment or entry.token_fp != token_fp:
        return False
    return (now - entry.fetched_at) < timedelta(days=ttl_days)


def _format_age(delta: timedelta) -> str:
    """Human age in the largest natural unit; floors to at least 1 minute."""
    secs = int(delta.total_seconds())
    if secs < 3600:
        n, unit = max(1, secs // 60), "minute"
    elif secs < 86400:
        n, unit = secs // 3600, "hour"
    else:
        n, unit = secs // 86400, "day"
    return f"{n} {unit}{'s' if n != 1 else ''} ago"


def _banner(
    source: str,
    environment: str,
    fetched_at: datetime | None,
    now: datetime,
    emoji: bool,
) -> str:
    """One-line freshness banner prepended to both stdout and the .md report.

    source: 'cache' (hit), 'expired' (stale refetch), 'first' (no prior cache),
    'refresh' (--refresh), 'nocache' (--no-cache), or 'partial' (a live fetch
    that logged failures, so nothing was cached).
    """
    if source == "cache":
        assert fetched_at is not None
        icon = "📦 " if emoji else ""
        age = _format_age(now - fetched_at)
        stamp = fetched_at.strftime("%Y-%m-%d %H:%M UTC")
        return (
            f"_{icon}Cached {age} (fetched {stamp}, {environment}). "
            "Run `python scripts/berdl_inventory.py --refresh` to update._"
        )
    if source == "partial":
        icon = "⚠️  " if emoji else ""
        return (
            f"_{icon}Live inventory — **partial**: some databases failed to list "
            f"(see warnings above), so this run was **not cached** ({environment}). "
            "Re-run to retry._"
        )
    icon = "🔄 " if emoji else ""
    if source == "expired":
        return f"_{icon}Live inventory — cache expired, refetched just now ({environment})._"
    if source == "refresh":
        return f"_{icon}Live inventory — refreshed just now ({environment})._"
    if source == "nocache":
        return f"_{icon}Live inventory — cache bypassed via `--no-cache` ({environment})._"
    return f"_{icon}Live inventory — first run ({environment})._"


def _split_tenant_prefix(database: str) -> str:
    """Tenant key for an Iceberg ``catalog.namespace`` database identifier.

    Under Iceberg/Polaris every database is qualified as
    ``catalog.namespace`` (e.g. ``kbase.genomes``, ``kbase.ke_pangenome``) —
    the tenant is the catalog, i.e. everything before the first dot. Legacy
    flat Delta names (``kbase_genomes``) are dropped before they reach here
    (see ``_iceberg_only`` / ``fetch_off_cluster``), so there is no underscore
    fallback; a name with no dot is grouped under ``(other)``.
    """
    return database.split(".", 1)[0] if "." in database else "(other)"


def _iceberg_only(structure: dict[str, list[str]]) -> dict[str, list[str]]:
    """Keep only Iceberg (dotted ``catalog.namespace``) databases.

    The migration leaves legacy Delta databases registered as flat,
    underscore-only names (``kbase_genomes``) alongside their Iceberg twins
    (``kbase.genomes``). We surface only the Iceberg form; any identifier
    without a dot is a Delta/Hive database and is dropped.
    """
    return {db: tables for db, tables in structure.items() if "." in db}


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


def _enrich_tenant(t: object, get_tenant_detail) -> TenantInfo:  # noqa: ANN001
    """Build a TenantInfo from a list_tenants() entry, enriching via get_tenant_detail."""
    info = TenantInfo(
        name=getattr(t, "tenant_name", str(t)),
        display_name=getattr(t, "display_name", "") or "",
        description=getattr(t, "description", "") or "",
        website=getattr(t, "website", "") or "",
        organization=getattr(t, "organization", "") or "",
        is_member=bool(getattr(t, "is_member", False)),
        is_steward=bool(getattr(t, "is_steward", False)),
    )
    try:
        detail = get_tenant_detail(info.name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_tenant_detail(%s) failed: %s", info.name, exc)
        return info

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
    return info


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

    try:
        tenants = list_tenants()
    except Exception as exc:  # noqa: BLE001 — surface but don't crash
        structure_logger.warning("list_tenants() failed: %s", exc)
        return []
    if tenants is None:
        return []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=min(8, len(tenants))) as pool:
        futures = {
            pool.submit(_enrich_tenant, t, get_tenant_detail): t
            for t in tenants
        }
        out: list[TenantInfo] = [None] * len(tenants)  # type: ignore[list-item]
        tenant_order = {id(t): i for i, t in enumerate(tenants)}
        for future in as_completed(futures):
            t = futures[future]
            out[tenant_order[id(t)]] = future.result()
    return out


def fetch_off_cluster() -> dict[str, list[str]]:
    """Fall back to per-catalog SHOW NAMESPACES + SHOW TABLES. Auto-spawns JH server.

    With Polaris/Iceberg each tenant is a separate catalog, so SHOW DATABASES is
    insufficient.  We enumerate the registered Iceberg catalogs, then list
    namespaces and tables inside each one, returning ``catalog.namespace`` keys.
    """
    import re

    from get_spark_session import get_spark_session  # local drop-in

    spark = get_spark_session()

    # Discover catalogs via `SET`, not `SHOW CATALOGS`: over Spark Connect the
    # latter only returns catalogs the client session has already *touched*, so
    # it misses server-registered Iceberg catalogs. The reliable source is the
    # ``spark.sql.catalog.<name>`` config keys (sub-properties like ``.uri`` are
    # skipped by the anchored pattern). ``spark_catalog`` is the Hive/Delta
    # catalog and is excluded — its flat databases are the legacy form we drop.
    catalog_key = re.compile(r"^spark\.sql\.catalog\.([a-zA-Z_][a-zA-Z0-9_]*)$")
    catalogs = sorted(
        {
            m.group(1)
            for row in spark.sql("SET").collect()
            if (m := catalog_key.match(row["key"])) and m.group(1) != "spark_catalog"
        }
    )

    structure: dict[str, list[str]] = {}
    for catalog in catalogs:
        try:
            ns_rows = spark.sql(f"SHOW NAMESPACES IN {catalog}").collect()
            namespaces = [row[0] for row in ns_rows]
        except Exception as exc:  # noqa: BLE001
            structure_logger.warning("could not list namespaces in catalog %s: %s", catalog, exc)
            continue
        for ns in namespaces:
            qualified = f"{catalog}.{ns}"
            try:
                tbl_rows = spark.sql(f"SHOW TABLES IN {qualified}").collect()
                structure[qualified] = [row["tableName"] for row in tbl_rows]
            except Exception as exc:  # noqa: BLE001
                structure_logger.warning("could not list tables for %s: %s", qualified, exc)
                structure[qualified] = []
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
    # sandbox — contents are noise for orientation). Match via namespace_prefix
    # and the catalog (dot-split) fallback.
    hidden_prefixes = tuple(
        t.namespace_prefix
        for t in tenants
        if t.namespace_prefix and t.name in _HIDDEN_TENANTS
    )
    # Drop legacy Delta (flat) databases — surface only Iceberg catalog.namespace.
    structure = _iceberg_only(structure)
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
    # in. Split into "member but no DBs registered" vs "no membership" so the
    # footer doesn't mislabel tenants you can write to as inaccessible. Hidden
    # tenants (e.g. globalusers) are excluded from both lists.
    if tenants:
        rendered = set(by_tenant)
        member_no_dbs = sorted(
            t.name
            for t in tenants
            if t.name not in rendered
            and t.name not in _HIDDEN_TENANTS
            and (t.is_member or t.is_steward)
        )
        non_member = sorted(
            t.name
            for t in tenants
            if t.name not in rendered
            and t.name not in _HIDDEN_TENANTS
            and not (t.is_member or t.is_steward)
        )
        if member_no_dbs:
            lines.append(
                f"_Tenants you can access (no databases yet): {', '.join(member_no_dbs)}._"
            )
            lines.append("")
        if non_member:
            lines.append(
                f"_Other tenants in BERDL (no membership): {', '.join(non_member)}._"
            )
            lines.append("")

    lines.append(
        "> Run `DESCRIBE DATABASE EXTENDED <db>` for a database description, "
        "`DESCRIBE EXTENDED <db>.<table>` for table-level comments / properties."
    )
    return "\n".join(lines)


def format_summary(
    structure: dict[str, list[str]],
    tenants: list[TenantInfo] | None = None,
    full_report_path: str | None = None,
    emoji: bool = True,
) -> str:
    """Compact one-line-per-tenant summary for stdout.

    Short by design: the full per-database report goes to a file
    (``full_report_path``) so the chat UI doesn't collapse this to
    "+N lines (ctrl+o to expand)". The agent relays this verbatim and points
    the user to the file for details.
    """
    tenants = tenants or []

    hidden_prefixes = tuple(
        t.namespace_prefix
        for t in tenants
        if t.namespace_prefix and t.name in _HIDDEN_TENANTS
    )
    # Drop legacy Delta (flat) databases — surface only Iceberg catalog.namespace.
    structure = _iceberg_only(structure)
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
    visible_tenants = len(by_tenant)

    header_icon = "📦 " if emoji else ""

    lines = [
        f"## {header_icon}BERDL Inventory",
        "",
        f"_{visible_tenants} tenants · {total_dbs} databases · {total_tables} tables_",
        "",
        "| Tenant | Display name | # DBs | # Tables |",
        "|--------|--------------|------:|---------:|",
    ]

    for tenant_key in sorted(by_tenant):
        rows = by_tenant[tenant_key]
        info = tenant_meta.get(tenant_key)
        display = info.display_name if info and info.display_name else "—"
        n_dbs = len(rows)
        n_tables = sum(len(t) for _, t in rows)
        lines.append(f"| `{tenant_key}` | {display} | {n_dbs} | {n_tables} |")

    lines.append("")

    if tenants:
        rendered = set(by_tenant)
        member_no_dbs = sorted(
            t.name
            for t in tenants
            if t.name not in rendered
            and t.name not in _HIDDEN_TENANTS
            and (t.is_member or t.is_steward)
        )
        non_member = sorted(
            t.name
            for t in tenants
            if t.name not in rendered
            and t.name not in _HIDDEN_TENANTS
            and not (t.is_member or t.is_steward)
        )
        if member_no_dbs:
            lines.append(
                f"_Tenants you can access (no databases yet): {', '.join(member_no_dbs)}._"
            )
            lines.append("")
        if non_member:
            lines.append(
                f"_Other tenants in BERDL (no membership): {', '.join(non_member)}._"
            )
            lines.append("")

    if full_report_path:
        lines.append(
            f"> Full report (per-database tables, tenant metadata, members) saved to "
            f"`{full_report_path}`. Open it for details — the agent does not need to relay it."
        )
        lines.append("")

    lines.append(
        "<!-- AGENT: Paste this entire summary into your chat reply. Do NOT "
        "collapse it to a one-line totals sentence. The full per-database "
        "report lives at the path above; point the user there rather than "
        "trying to relay it. -->"
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--sample",
        type=int,
        default=3,
        help="Number of sample table names to show per database in the full report (default: 3).",
    )
    p.add_argument(
        "--with-members",
        action="store_true",
        help="Include steward / read-write / read-only member lists per tenant in the full report.",
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
    p.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=f"Where to write the full markdown report (default: {_DEFAULT_OUTPUT}).",
    )
    p.add_argument(
        "--no-file",
        action="store_true",
        help="Skip writing the full report to a file (only print to stdout).",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="Print the full report to stdout instead of the compact summary.",
    )
    p.add_argument(
        "--refresh",
        action="store_true",
        help="Force a live fetch and rewrite the cache, ignoring TTL and fingerprint.",
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the cache for read and write (one-shot live fetch).",
    )
    p.add_argument(
        "--ttl-days",
        type=int,
        default=None,
        help="Cache lifetime in days (default: 7, or $BERDL_INVENTORY_TTL_DAYS).",
    )
    p.add_argument(
        "--cache-path",
        type=Path,
        default=_DEFAULT_CACHE,
        help=f"Where the JSON inventory cache lives (default: {_DEFAULT_CACHE}).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    structure: dict[str, list[str]] | None = None
    tenants: list[TenantInfo] = []

    environment = (
        "off-cluster"
        if args.off_cluster
        else ("on-cluster" if _is_on_cluster() else "off-cluster")
    )
    token_fp = _token_fingerprint()
    ttl_days = _resolve_ttl_days(args.ttl_days)
    now = _now()

    # Was there a prior cache file? Drives the 'expired' vs 'first' banner on a miss.
    had_cache = args.cache_path.exists()
    banner_source: str | None = None
    banner_fetched_at: datetime | None = None

    # Cache gate — runs before any fetch so a hit never imports/spawns Spark.
    if not args.refresh and not args.no_cache:
        entry = load_cache(args.cache_path)
        if entry is not None and _cache_is_fresh(entry, environment, token_fp, ttl_days, now):
            structure = entry.structure
            tenants = entry.tenants
            banner_source = "cache"
            banner_fetched_at = entry.fetched_at

    # A live fetch is watched: a database whose listing fails is silently
    # recorded as empty (upstream logs and returns []), and caching that would
    # pin the loss for the whole TTL.
    failures: list[str] = []
    if structure is None:
        print(
            f"{'🔄  ' if not args.no_emoji else ''}"
            f"Fetching live inventory ({environment})...",
            flush=True,
        )
        with _watch_fetch_failures() as watcher:
            if not args.off_cluster:
                try:
                    structure = fetch_structure_on_cluster()
                    tenants = fetch_tenants_on_cluster()
                except ImportError:
                    if _is_on_cluster():
                        print(
                            "[berdl_inventory] On-cluster, but berdl_notebook_utils "
                            "is not importable in this Python. The JupyterHub kernel "
                            "has it pre-installed; an isolated venv (e.g. one started "
                            "by `uv run` or a private virtualenv) does not.\n\n"
                            "  → Re-run with the JH kernel's Python: "
                            "python scripts/berdl_inventory.py",
                            file=sys.stderr,
                        )
                        return 2
                    structure = None
            if structure is None:
                try:
                    structure = fetch_off_cluster()
                except ImportError as exc:
                    missing = str(exc).split("'")
                    mod = missing[1] if len(missing) > 1 else "a required module"
                    print(
                        f"[berdl_inventory] Off-cluster, but {mod} is not installed.\n\n"
                        "  → Activate the BERDL venv:\n"
                        "      source .venv-berdl/bin/activate\n"
                        "      python scripts/berdl_inventory.py\n\n"
                        "  → Or run ad-hoc with uv:\n"
                        "      uv run --with pyspark \\\n"
                        "        --with 'spark_connect_remote @ git+https://github.com/BERDataLakehouse/spark_connect_remote.git' \\\n"
                        "        --with 'berdl_remote @ git+https://github.com/BERDataLakehouse/berdl_remote.git' \\\n"
                        "        scripts/berdl_inventory.py\n\n"
                        "If you have not yet bootstrapped the venv, run "
                        "`bash scripts/bootstrap_client.sh` first.",
                        file=sys.stderr,
                    )
                    return 2
                except Exception as exc:  # noqa: BLE001
                    print(f"Failed to fetch inventory: {exc}", file=sys.stderr)
                    return 1
        failures = watcher.messages

    # On a miss we fetched live — stamp provenance and (unless suppressed) cache it.
    if banner_source is None:
        degraded = bool(failures)
        if degraded:
            banner_source = "partial"
        elif args.refresh:
            banner_source = "refresh"
        elif args.no_cache:
            banner_source = "nocache"
        else:
            banner_source = "expired" if had_cache else "first"

        if degraded:
            # Keep any existing cache: a good older snapshot beats a fresh
            # lossy one, and the next run retries the fetch.
            print(
                f"# WARN: {len(failures)} database(s) failed to list; "
                f"not caching this partial inventory.",
                file=sys.stderr,
            )
        elif not args.no_cache:
            try:
                write_cache(
                    args.cache_path,
                    CacheEntry(environment, token_fp, now, structure, tenants),
                )
            except OSError as exc:
                print(
                    f"# WARN: could not write cache to {args.cache_path}: {exc}",
                    file=sys.stderr,
                )

    banner = _banner(
        banner_source, environment, banner_fetched_at, now, emoji=not args.no_emoji
    )

    full_report = format_inventory(
        structure,
        tenants=tenants,
        sample=args.sample,
        emoji=not args.no_emoji,
        with_members=args.with_members,
    )
    full_report = f"{banner}\n\n{full_report}"

    written_path: Path | None = None
    if not args.no_file:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(full_report + "\n")
            written_path = args.output
        except OSError as exc:
            print(
                f"# WARN: could not write full report to {args.output}: {exc}",
                file=sys.stderr,
            )

    if args.full:
        print(full_report)
        if written_path is not None:
            print(f"\n_Full report also saved to `{written_path}`._")
    else:
        # Display path relative to repo root when possible — easier to copy/paste.
        display_path: str | None = None
        if written_path is not None:
            try:
                display_path = str(written_path.relative_to(_REPO_ROOT))
            except ValueError:
                display_path = str(written_path)
        summary = format_summary(
            structure,
            tenants=tenants,
            full_report_path=display_path,
            emoji=not args.no_emoji,
        )
        print(f"{banner}\n\n{summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
