"""
Rank every non-reannotated FB gene in the 35 curated organisms by primary
phenotype evidence — no learned model, no thresholding, just direct
primary-fitness ranking with specific-phenotype as the leading sort key.

Sort order (descending):
  1. in_specificphenotype     (binary; specific-phenotype genes first —
                                Price's curators paid most attention to these)
  2. max_abs_fit * max_abs_t   (signal-to-noise weighted phenotype magnitude)

Output: data/ranked_genes.parquet — full ranked list, one row per gene,
all primary features carried through. NB02 walks this top-down.
"""
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

FEATURES_PATH = PROJECT_DATA / "gene_evidence_features.parquet"
OUT_PATH = PROJECT_DATA / "ranked_genes.parquet"


def main() -> None:
    df = pd.read_parquet(FEATURES_PATH)
    print(f"All FB genes with fitness data: {len(df):,}")

    # Restrict to the 35 organisms with at least one reannotation —
    # the others may be uncurated rather than reviewed-and-skipped.
    curated_orgs = sorted(df.loc[df.is_reannotated == 1, "orgId"].unique())
    df = df[df.orgId.isin(curated_orgs)].copy()
    print(f"After restriction to {len(curated_orgs)} curated orgs: {len(df):,}")

    # Drop reannotated genes — they're already done
    df = df[df.is_reannotated == 0].copy()
    print(f"After dropping reannotated: {len(df):,}")

    # Compose the rank score
    df["fit_x_t"] = df["max_abs_fit"].astype(float) * df["max_abs_t"].astype(float)
    df = df.sort_values(
        ["in_specificphenotype", "fit_x_t"],
        ascending=[False, False],
    ).reset_index(drop=True)
    df["rank"] = np.arange(1, len(df) + 1)

    # Quick sanity output
    print(f"Top 5 by rank:")
    cols = ["rank", "orgId", "locusId", "in_specificphenotype",
            "max_abs_fit", "max_abs_t", "fit_x_t", "gene_desc"]
    print(df[cols].head(5).to_string(index=False))
    print(f"\nDistribution of in_specificphenotype:")
    print(df["in_specificphenotype"].value_counts().to_string())

    df.to_parquet(OUT_PATH, index=False)
    print(f"\nWrote {OUT_PATH}  ({len(df):,} rows, {OUT_PATH.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
