"""Batch growth curve fitting across all ENIGMA growth bricks.

Reads each brick, fits every well, writes one parquet file per brick to the
output directory. Resumable: skips bricks whose output already exists. Run
directly or import `run_batch` from a notebook.

Usage:
    python -m batch_fit --out /path/to/data/growth_parameters [--limit N]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from curve_fitting import fit_curve, is_edge_well


# Base columns present in every growth brick
CORE_COLS = {
    "time_series_time_since_inoculation_hour": "t",
    "microplate_well_name": "well",
    "sdt_strain_name": "strain",
    "optical_density_dimensionless_unit": "od",
    "microplate_well_replicate_series_count_unit": "replicate",
}

# Optional columns — not all bricks have them; use per-brick schema check
OPTIONAL_COLS = {
    "microplate_well_media_name": "media",
    "context_media_sdt_condition_name": "media_cond",
    "molecule_from_list_context_media_addition_category_media_addition_1_sys_oterm_name": "molecule",
    "molecule_from_list_context_media_addition_category_media_addition_1_sys_oterm_id": "chebi",
    "microplate_well_concentration_context_media_addition_category_media_addition_1_millimolar": "conc_mM",
    "microplate_well_concentration_context_media_addition_category_media_addition_1_microgram_per_milliliter": "conc_ug_per_ml",
    "microplate_well_concentration_context_media_addition_category_media_addition_1_fold_concentration": "conc_fold",
    "microplate_well_ph_ph": "ph",
    "time_series_temperature_degree_celsius": "temperature_c",
}


def _get_brick_columns(spark, brick_id: str) -> set:
    table = f"enigma_coral.ddt_{brick_id.lower()}"
    rows = spark.sql(f"DESCRIBE {table}").collect()
    return {r[0] for r in rows}


def _build_select(spark, brick_id: str) -> str:
    """Build a SELECT with CORE columns + any available OPTIONAL columns, aliased."""
    present = _get_brick_columns(spark, brick_id)
    parts = []
    for src, alias in {**CORE_COLS, **OPTIONAL_COLS}.items():
        if src in present:
            parts.append(f"{src} AS {alias}")
        else:
            parts.append(f"NULL AS {alias}")
    return ", ".join(parts)


def fit_brick(spark, brick_id: str) -> pd.DataFrame:
    """Load a single brick, fit all wells, return per-well parameter frame."""
    table = f"enigma_coral.ddt_{brick_id.lower()}"
    sel = _build_select(spark, brick_id)
    rows = spark.sql(f"SELECT {sel} FROM {table}").collect()
    if not rows:
        return pd.DataFrame()
    pdf = pd.DataFrame([r.asDict() for r in rows])
    results = []
    # Use replicate as part of the curve key so duplicate wells don't collapse
    group_cols = ["well", "replicate"]
    for keys, g in pdf.groupby(group_cols, dropna=False):
        g = g.sort_values("t")
        if len(g) < 10:
            continue
        res = fit_curve(g["t"].values, g["od"].values)
        well, replicate = keys
        res["brick_id"] = brick_id
        res["well"] = well
        res["replicate"] = int(replicate) if pd.notna(replicate) else 0
        res["strain"] = g["strain"].dropna().iloc[0] if g["strain"].notna().any() else None
        # Carry metadata (take first non-null per group — should be constant within a well)
        for col in ["media", "media_cond", "molecule", "chebi", "conc_mM",
                     "conc_ug_per_ml", "conc_fold", "ph", "temperature_c"]:
            vals = g[col].dropna()
            res[col] = vals.iloc[0] if len(vals) else None
        res["edge_well"] = is_edge_well(well) if isinstance(well, str) else False
        results.append(res)
    return pd.DataFrame(results)


def list_growth_bricks(spark) -> list[str]:
    rows = spark.sql("""
        SELECT ddt_ndarray_id FROM enigma_coral.ddt_ndarray
        WHERE LOWER(ddt_ndarray_description) LIKE '%high throughput growth%'
        ORDER BY ddt_ndarray_id
    """).collect()
    return [r[0] for r in rows]


def run_batch(spark, out_dir: str, limit: int | None = None, force: bool = False) -> dict:
    """Fit all (or first `limit`) growth bricks, save per-brick parquets.

    Returns a dict of {brick_id: status} where status is 'done', 'skip', or 'error:<msg>'.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    bricks = list_growth_bricks(spark)
    if limit:
        bricks = bricks[:limit]
    status: dict[str, str] = {}
    t_start = time.time()
    for i, brick_id in enumerate(bricks, start=1):
        outfile = out_path / f"{brick_id}.parquet"
        if outfile.exists() and not force:
            status[brick_id] = "skip"
            continue
        t0 = time.time()
        try:
            params = fit_brick(spark, brick_id)
            if len(params) == 0:
                status[brick_id] = "empty"
                continue
            params.to_parquet(outfile, index=False)
            dt = time.time() - t0
            status[brick_id] = "done"
            elapsed = time.time() - t_start
            remain = (len(bricks) - i) * elapsed / max(i, 1)
            print(
                f"  [{i}/{len(bricks)}] {brick_id}: {len(params)} curves "
                f"({params['fit_ok'].sum()} ok) in {dt:.1f}s · elapsed {elapsed:.0f}s · "
                f"eta {remain:.0f}s",
                flush=True,
            )
        except Exception as exc:
            status[brick_id] = f"error:{type(exc).__name__}:{str(exc)[:200]}"
            print(f"  [{i}/{len(bricks)}] {brick_id}: ERROR {status[brick_id]}", flush=True)
    return status


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()
    status = run_batch(spark, args.out, limit=args.limit, force=args.force)
    n_done = sum(1 for v in status.values() if v == "done")
    n_skip = sum(1 for v in status.values() if v == "skip")
    n_err = sum(1 for v in status.values() if v.startswith("error"))
    print(f"\nBATCH COMPLETE: {n_done} done, {n_skip} skipped, {n_err} errors")
    if n_err:
        for b, s in status.items():
            if s.startswith("error"):
                print(f"  {b}: {s}")


if __name__ == "__main__":
    _main()
