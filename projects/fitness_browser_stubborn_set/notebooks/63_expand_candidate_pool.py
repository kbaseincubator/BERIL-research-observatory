"""
Sample candidate genes for the explicit *stubborn-set* expansion track.

Filter (applied to ranked_genes.parquet pool of 137,798):
  KEEP rows where (n_strong_experiments >= 1) OR (in_specificphenotype == 1)

This is the Price-2018 strong-fitness threshold used in the original
RB-TnSeq calls — |fit| >= 2 AND |t| >= 5 in at least one condition, OR
flagged in the precomputed `specificphenotype` table. ~26,437 of 137,798
pool genes survive.

Why filter: the original v1 sample was uniform random over the full pool,
so 95% of resulting "negatives" had n_strong=0 and were "no fitness
signal therefore can't annotate" rather than the project's stated focus,
"strong fitness phenotype but stubbornly resistant to annotation." This
expansion is explicitly the latter cohort.

Excludes (to avoid duplicate work):
  - the 5,000 already in random_sample_genes.parquet (classified in v1)
  - the 1,762 in reannotation_set.parquet (gold-standard human_validated)

Output:
  data/random_sample_genes_expansion.parquet
  same schema as ranked_genes.parquet so dossier / batching pipelines
  consume it unchanged.

Usage:
  python notebooks/63_expand_candidate_pool.py --n 2000 --seed 20260430
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

RANKED = PROJECT_DATA / "ranked_genes.parquet"
EXISTING = PROJECT_DATA / "random_sample_genes.parquet"
REANN = PROJECT_DATA / "reannotation_set.parquet"
OUT = PROJECT_DATA / "random_sample_genes_expansion.parquet"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260430)
    args = parser.parse_args()

    pool = pd.read_parquet(RANKED)
    print(f"Pool: {len(pool):,} genes")

    # Apply Price-2018 strong-fitness threshold
    strong_mask = (pool["n_strong_experiments"] >= 1) | (pool["in_specificphenotype"] == 1)
    pool_strong = pool[strong_mask].reset_index(drop=True)
    print(f"After strong-signal filter (n_strong>=1 OR in_specphen==1): "
          f"{len(pool_strong):,}")

    excl = set()
    for p in (EXISTING, REANN):
        df = pd.read_parquet(p)
        excl |= set(zip(df["orgId"], df["locusId"]))
        print(f"  excluded {p.name}: {len(df):,} rows")
    print(f"Total exclusion set: {len(excl):,}")

    pool_strong["_key"] = list(zip(pool_strong["orgId"], pool_strong["locusId"]))
    avail = pool_strong[~pool_strong["_key"].isin(excl)].drop(columns=["_key"]).reset_index(drop=True)
    print(f"Available after exclusion: {len(avail):,}")

    n = min(args.n, len(avail))
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(len(avail))[:n]
    sample = avail.iloc[perm].copy().reset_index(drop=True)
    sample["rank"] = np.arange(1, len(sample) + 1)

    print(f"\nSampled {len(sample):,} (seed={args.seed})")
    print("Top 5 of random order:")
    print(sample[["rank", "orgId", "locusId", "max_abs_fit", "in_specificphenotype",
                  "gene_desc"]].head(5).to_string(index=False))

    sample.to_parquet(OUT, index=False)
    print(f"\nWrote {OUT}  ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
