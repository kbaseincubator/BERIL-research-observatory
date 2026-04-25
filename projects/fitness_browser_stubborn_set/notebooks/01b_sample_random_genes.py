"""
Random sample of FB genes for the negative-training-set track.

Sample frame: the same 137,798 non-reannotated genes in the 35 curated
organisms used for the priority-queue track. Sampling is uniform random
without replacement — produces a representative cross-section of the
"genes a human curator could have looked at but didn't update," not just
the strongest-phenotype top of the queue.

The output parquet has the same schema as `ranked_genes.parquet` so the
existing `02_prepare_batch.py` / dossier / subagent workflow can consume
it unchanged. The `rank` column here is the random-shuffle order (1..N).

Usage:
    python projects/fitness_browser_stubborn_set/notebooks/01b_sample_random_genes.py \
        --n 5000 --seed 20260425
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

RANKED_PATH = PROJECT_DATA / "ranked_genes.parquet"
OUT_PATH = PROJECT_DATA / "random_sample_genes.parquet"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5000,
                        help="number of random samples (default 5000)")
    parser.add_argument("--seed", type=int, default=20260425,
                        help="random seed for reproducibility")
    args = parser.parse_args()

    df = pd.read_parquet(RANKED_PATH)
    print(f"Pool: {len(df):,} non-reannotated genes in 35 curated orgs")

    if args.n > len(df):
        print(f"Requested {args.n} but pool is {len(df)}; sampling all without replacement")
        args.n = len(df)

    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(len(df))[: args.n]
    sample = df.iloc[perm].copy().reset_index(drop=True)
    sample["rank"] = np.arange(1, len(sample) + 1)

    print(f"Sampled {len(sample):,} genes (seed={args.seed})")
    print("Top 5 of random order:")
    print(sample[["rank", "orgId", "locusId", "max_abs_fit", "in_specificphenotype",
                  "gene_desc"]].head(5).to_string(index=False))

    sample.to_parquet(OUT_PATH, index=False)
    print(f"\nWrote {OUT_PATH}  ({OUT_PATH.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
