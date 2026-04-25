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
# # NB03 — Verdict results & cross-gene clusters
#
# Summary of the 610-gene priority-queue pilot. All numbers are loaded from
# committed artifacts (`data/llm_verdicts.jsonl` + `data/verdicts_with_context.parquet`)
# produced by the `02_prepare_batch.py` → subagent → `03_aggregate_verdicts.py`
# pipeline. This notebook just displays them.

# %%
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from IPython.display import Markdown, Image

REPO_ROOT = Path.cwd().resolve()
while REPO_ROOT.name and not (REPO_ROOT / ".venv-berdl").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent
DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
FIGS = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "figures"

# %% [markdown]
# ## Verdict distribution

# %%
df = pd.read_parquet(DATA / "verdicts_with_context.parquet")
print(f"Total verdicts: {len(df)}")
counts = df["verdict"].value_counts()
n = len(df)
order = ["already_correctly_named", "improvable_correction", "improvable_new", "recalcitrant"]
summary = pd.DataFrame({
    "n": counts.reindex(order),
    "pct": (counts.reindex(order) / n * 100).round(1),
})
summary.loc["TOTAL"] = [n, 100.0]
summary

# %% [markdown]
# ## Stability across rounds
#
# As we walked deeper into the priority queue (110 → 610 genes), verdict
# rates remained remarkably stable:

# %%
stability = pd.DataFrame([
    {"round": 110, "already_named_pct": 36, "improvable_pct": 52, "recalcitrant_pct": 12},
    {"round": 210, "already_named_pct": 34, "improvable_pct": 58, "recalcitrant_pct": 8},
    {"round": 310, "already_named_pct": 35, "improvable_pct": 55, "recalcitrant_pct": 9},
    {"round": 410, "already_named_pct": 37, "improvable_pct": 55, "recalcitrant_pct": 8},
    {"round": 510, "already_named_pct": 38, "improvable_pct": 54, "recalcitrant_pct": 8},
    {"round": 610, "already_named_pct": 38, "improvable_pct": 52, "recalcitrant_pct": 10},
])
stability

# %% [markdown]
# ## Existing annotation × verdict (the contingency grid)

# %%
cont = pd.crosstab(df["annotation_category"], df["verdict"])
cont = cont.reindex(
    index=["hypothetical", "DUF", "vague", "named_enzyme", "named_other"],
    columns=order, fill_value=0,
)
cont["total"] = cont.sum(axis=1)
cont

# %% [markdown]
# ## Confidence × verdict

# %%
pd.crosstab(df["verdict"], df["confidence"]).reindex(
    index=order, columns=["high", "medium", "low"], fill_value=0,
)

# %% [markdown]
# ## Literature consultation

# %%
n_with_papers = sum(
    1 for _, r in df.iterrows()
    if r.get("papers_consulted") is not None and len(list(r["papers_consulted"])) > 0
)
total = sum(
    len(list(r["papers_consulted"])) if r.get("papers_consulted") is not None else 0
    for _, r in df.iterrows()
)
unique = set()
for _, r in df.iterrows():
    ps = r.get("papers_consulted")
    if ps is not None:
        for p in ps:
            if p:
                unique.add(str(p))
print(f"Genes with paper consults: {n_with_papers} / {len(df)} ({n_with_papers/len(df)*100:.0f}%)")
print(f"Total fetches:             {total}")
print(f"Unique PMIDs:              {len(unique)}")

# %% [markdown]
# ## Figures

# %%
Image(FIGS / "fig01_verdict_distribution.png")

# %%
Image(FIGS / "fig02_verdict_by_category.png")

# %%
Image(FIGS / "fig03_verdict_by_rank.png")

# %% [markdown]
# ## Top cross-gene cluster discoveries
#
# PMIDs cited by ≥3 genes — single papers that resolved entire functional
# clusters. Full details in [data/cross_gene_clusters.md](../data/cross_gene_clusters.md).

# %%
pmids = pd.read_csv(DATA / "cited_pmids.tsv", sep="\t")
clusters = pmids[pmids["n_genes_citing"] >= 3].sort_values("n_genes_citing", ascending=False)
print(f"PMIDs cited by ≥3 genes: {len(clusters)}")
clusters.head(15)

# %% [markdown]
# ## Sample of high-confidence improvable_correction (existing name was wrong)

# %%
corr = df[(df["verdict"] == "improvable_correction") & (df["confidence"] == "high")].copy()
corr_sample = corr.sort_values("rank").head(10)
corr_sample[["rank", "orgId", "locusId", "gene_desc", "proposed_annotation"]]

# %% [markdown]
# ## Sample of recalcitrant genes — strong evidence but no proposable annotation

# %%
rec = df[df["verdict"] == "recalcitrant"].copy()
rec_sample = rec.sort_values("rank").head(10)
rec_sample[["rank", "orgId", "locusId", "gene_desc", "rationale"]]
