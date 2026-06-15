"""Walk the BERDL Lakehouse, build a per-table catalog with topic tags.

Outputs:
  data/table_topic_map.csv     — one row per accessible table
  data/tenant_to_agency.csv    — curated tenant → agency/program mapping

Run from project root or from the project directory; output path is resolved
relative to the project's `data/` folder.

Schema fetch is parallelized with a ThreadPoolExecutor (default 16 workers) —
empirically about 5× faster than serial on this Spark Connect endpoint.
"""

from __future__ import annotations

import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from berdl_notebook_utils import get_databases, get_table_schema, get_tables

from .topic_tags import TENANT_TO_AGENCY, tag_table, tenant_of


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _fetch_schema(db: str, table: str) -> tuple[str, str, list[str], list[str]]:
    """Return (db, table, column_names, column_types). Empty lists on failure."""
    try:
        schema = get_table_schema(db, table, detailed=True, return_json=False)
    except Exception:  # noqa: BLE001 — surface as empty schema, keep going
        return db, table, [], []
    cols = [c["name"] for c in schema]
    types = [c["dataType"] for c in schema]
    return db, table, cols, types


def walk_inventory(max_workers: int = 16) -> list[dict]:
    """Walk every accessible database; return one record per table.

    Filters out database names containing '.' — the Spark Connect catalog
    exposes the same Delta tables under both `namespace.name` (dotted) and
    legacy `namespace_name` (underscored) forms. Keeping only the underscored
    form deduplicates ~1900 phantom tables and aligns with `tenant_of()`,
    which splits on `_`.
    """
    t0 = time.time()
    dbs_all = get_databases(return_json=False)
    dbs = [d for d in dbs_all if "." not in d]
    dropped = len(dbs_all) - len(dbs)
    print(
        f"  {len(dbs)} accessible databases ({time.time() - t0:.1f}s) "
        f"[dropped {dropped} dotted-namespace duplicates]"
    )

    # Build (db, table) work list.
    pairs: list[tuple[str, str]] = []
    for db in dbs:
        try:
            tables = get_tables(db, return_json=False)
        except Exception as e:  # noqa: BLE001
            print(f"  ! get_tables({db}) failed: {e}")
            continue
        pairs.extend((db, t) for t in tables)
    print(f"  {len(pairs)} (db, table) pairs total ({time.time() - t0:.1f}s)")

    # Parallelize schema fetches.
    records: list[dict] = []
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_fetch_schema, db, tbl) for db, tbl in pairs]
        done = 0
        for f in as_completed(futures):
            db, tbl, cols, types = f.result()
            tenant = tenant_of(db)
            primary, secondary = tag_table(db, tbl, cols)
            agency_info = TENANT_TO_AGENCY.get(tenant, {})
            records.append(
                {
                    "tenant": tenant,
                    "agency": agency_info.get("agency", "Unknown"),
                    "program": agency_info.get("program", "Unknown"),
                    "primary_funder": agency_info.get("primary_funder", "Unknown"),
                    "database": db,
                    "table": tbl,
                    "primary_topic": primary,
                    "secondary_topics": "|".join(secondary),
                    "n_columns": len(cols),
                    "column_names": "|".join(cols[:50]),  # cap to keep CSV readable
                    "has_more_columns": len(cols) > 50,
                }
            )
            done += 1
            if done % 100 == 0:
                print(f"  schemas fetched: {done}/{len(pairs)} ({time.time() - t1:.1f}s elapsed)")
    print(f"  schema walk complete: {len(records)} rows in {time.time() - t1:.1f}s")
    return records


def write_table_topic_map(records: list[dict], path: Path | None = None) -> Path:
    if path is None:
        path = DATA_DIR / "table_topic_map.csv"
    records.sort(key=lambda r: (r["tenant"], r["database"], r["table"]))
    fields = list(records[0].keys())
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(records)
    return path


def write_tenant_to_agency(path: Path | None = None) -> Path:
    if path is None:
        path = DATA_DIR / "tenant_to_agency.csv"
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tenant", "agency", "program", "primary_funder"])
        for tenant, info in sorted(TENANT_TO_AGENCY.items()):
            w.writerow([tenant, info["agency"], info["program"], info["primary_funder"]])
    return path


def main() -> None:
    print("[build_inventory] walking BERDL …")
    records = walk_inventory()
    p1 = write_table_topic_map(records)
    p2 = write_tenant_to_agency()
    print(f"[build_inventory] wrote {p1} ({len(records)} rows)")
    print(f"[build_inventory] wrote {p2}")


if __name__ == "__main__":
    main()
