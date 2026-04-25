# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # NB01 — Ranking the candidate pool
#
# This notebook shows the two ranking tracks used by the project. Both are
# produced by **scripts** in `notebooks/`; this notebook only reads the
# existing parquet outputs to display them.
#
# - **Priority queue** (`01_rank_genes.py`): direct primary-fitness rank
#   of all 137,798 non-reannotated genes in the 35 curated organisms.
#   Sort: `(in_specificphenotype DESC, max_abs_fit*max_abs_t DESC)`.
#   This is the curator-handoff track — top-of-queue is most curator-like.
# - **Random sample** (`01b_sample_random_genes.py`): uniform random
#   subsample of 5,000 genes from the same pool. Used to build a representative
#   negative-training-set, since the priority queue is biased toward strong
#   evidence.

# %%
from pathlib import Path
import pandas as pd

REPO_ROOT = Path.cwd().resolve()
while REPO_ROOT.name and not (REPO_ROOT / ".venv-berdl").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent
DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

# %% [markdown]
# ## Priority queue — 137,798 non-reannotated genes ranked by primary fitness

# %%
ranked = pd.read_parquet(DATA / "ranked_genes.parquet")
print(f"Total ranked genes: {len(ranked):,}")
print(f"Specific-phenotype genes (in_specificphenotype=1): {(ranked.in_specificphenotype == 1).sum():,}")
print(f"\nTop 10 of priority queue:")
ranked[["rank", "orgId", "locusId", "in_specificphenotype",
        "max_abs_fit", "max_abs_t", "fit_x_t", "gene_desc"]].head(10)

# %% [markdown]
# ## Random sample — 5,000 genes for the negative-training-set track

# %%
rand = pd.read_parquet(DATA / "random_sample_genes.parquet")
print(f"Random sample size: {len(rand):,}")
print(f"Random-sample specific-phenotype rate: {(rand.in_specificphenotype == 1).mean()*100:.1f}%")
print(f"Priority-queue specific-phenotype rate: {(ranked.in_specificphenotype == 1).mean()*100:.1f}%")
print(f"\nTop 10 of random order:")
rand[["rank", "orgId", "locusId", "in_specificphenotype",
      "max_abs_fit", "max_abs_t", "gene_desc"]].head(10)
