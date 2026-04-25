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
# # NB02 — Dossier demo
#
# Shows what the per-gene evidence dossier looks like — the input the LLM
# subagents reason over. The dossier is built lazily by
# `notebooks/dossier.py::build_dossier(orgId, locusId)` from 13 indexed
# parquet files. This notebook just imports the module and renders 3
# example dossiers.

# %%
import sys
from pathlib import Path

REPO_ROOT = Path.cwd().resolve()
while REPO_ROOT.name and not (REPO_ROOT / ".venv-berdl").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent
NB_DIR = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "notebooks"
sys.path.insert(0, str(NB_DIR))
import dossier as dossier_mod

from IPython.display import Markdown

# %% [markdown]
# ## Example 1 — top-of-queue gene (rank 1)
#
# `pseudo6_N2E2::Pf6N2E2_1442` — labeled "Transcriptional regulators of
# sugar metabolism", specifically sick on D-Mannose and D-Glucosamine.

# %%
d = dossier_mod.build_dossier("pseudo6_N2E2", "Pf6N2E2_1442")
Markdown(dossier_mod.dossier_to_markdown(d))

# %% [markdown]
# ## Example 2 — a clear "improvable_correction"
#
# `WCS417::GFF4430` — existing label was "chemotaxis protein CheY" but
# the evidence (specific phenotype on glucose, cofitness with sugar
# transporters, SwissProt hit) supports GltR-2 glucose response regulator
# instead. This is the kind of correction the LLM agent identified.

# %%
d = dossier_mod.build_dossier("WCS417", "GFF4430")
Markdown(dossier_mod.dossier_to_markdown(d))

# %% [markdown]
# ## Example 3 — a recalcitrant gene
#
# `Marino::GFF3111` — strong specific phenotype on ionic liquids
# (1-ethyl-3-methylimidazolium acetate) but only TPR repeat domains, no
# specific cofit partners or operon context. The LLM marked this
# recalcitrant — strong phenotype but evidence too thin to assign a
# specific function.

# %%
d = dossier_mod.build_dossier("Marino", "GFF3111")
Markdown(dossier_mod.dossier_to_markdown(d))
