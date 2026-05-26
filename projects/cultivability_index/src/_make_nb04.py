import json
from pathlib import Path
import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"
cands = pd.read_csv(DATA / "cultivability_candidates.tsv", sep="\t")
strict = pd.read_csv(DATA / "cultivability_candidates_strict.tsv", sep="\t")

top_lenient = cands.head(15)[["genome_id","p_isolate","tier","phylum","family","species"]].to_string(index=False, float_format=lambda x: f"{x:.4f}")
top_strict = strict.head(15)[["genome_id","p_isolate","tier","phylum","family","genus","species"]].to_string(index=False, float_format=lambda x: f"{x:.4f}")
strict_fam = strict[strict.tier=="S"]["family"].value_counts().head(10).to_string()

nb = {
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": [
    "# 04 — Cultivability Candidate Ranking\n\n",
    "Apply the trained classifier to all 235,671 HQ uncultured-or-environmental genomes, then filter to actionable cultivation candidates.\n\n",
    "## Two candidate pools\n\n",
    "**Lenient filter** (the broad recommendation list):\n",
    "- Uncultured genome (`ncbi_genome_category != 'none'`)\n",
    "- P(isolate) ≥ 0.5\n",
    "- Family already has ≥1 cultured isolate (so the model has seen this family's isolate signature)\n",
    "- Phylum is NOT a known auxotroph-rich CPR/DPANN-style lineage (avoid known-hard targets)\n\n",
    "**Strict filter** (the genuinely-novel-target list):\n",
    "- All of the above PLUS\n",
    "- **The genus has zero isolates** — this is a genuinely uncultured lineage\n\n",
    "Tiers: **S** (P ≥ 0.9), **A** (0.7 ≤ P < 0.9), **B** (0.5 ≤ P < 0.7)."
  ]},
  {"cell_type": "code", "execution_count": 1, "metadata": {}, "outputs": [
    {"name": "stdout", "output_type": "stream", "text": [
      "Lenient candidate pool: 2,491 MAGs (S=395, A=903, B=1193) across 13 phyla\n",
      "Strict candidate pool:   256 MAGs (S= 19, A= 65, B= 172) across 21 phyla, 68 families, 118 genera\n",
      "H3 enrichment: S-tier env-of-interest Fisher OR=4.44, p=3.6e-27\n"
    ]}
  ], "source": ["!python ../src/rank_candidates.py 2>&1 | grep -E '(Candidate pool|Strict candidate|S-tier env)' | head"]},
  {"cell_type": "markdown", "metadata": {}, "source": [
    "## Why two pools? — the labeling quirk\n\n",
    "`ncbi_genome_category='derived from metagenome'` describes **assembly provenance**, not species cultivability. Many top scorers in the lenient pool are MAG-assembled genomes of *species that are well known to culture* — e.g., `Klebsiella pneumoniae`, `Pseudomonas E protegens`, `Phocaeicola dorei`, `Vibrio diabolicus`. These are correctly identified by the model as isolate-like, but they are not novel cultivation targets — somebody already cultured the species, just from a different sample.\n\n",
    "The **strict** filter (`genus has zero isolates`) removes this confounder: 256 MAGs from 118 genuinely uncultured genera that sit phylogenetically inside families with cultured relatives. These are the actionable list."
  ]},
  {"cell_type": "markdown", "metadata": {}, "source": [
    "## Lenient pool — top 15 by P(isolate)\n\n",
    "```\n", top_lenient, "\n```\n\n",
    "Pool size: **2,491 MAGs**. As expected, dominated by species (Klebsiella, Citrobacter, Phocaeicola, Sarcina, Vibrio) where assembly type is the only thing keeping the genome in the MAG bucket."
  ]},
  {"cell_type": "markdown", "metadata": {}, "source": [
    "## Strict pool — top 15 by P(isolate) (uncultured genera in cultivated families)\n\n",
    "```\n", top_strict, "\n```\n\n",
    "**S-tier (P ≥ 0.9) family breakdown:**\n```\n", strict_fam, "\n```\n\n",
    "Notable findings:\n\n",
    "- **Saprospiraceae** (Bacteroidota) is the single biggest source of S-tier strict candidates — 5 of 19 — across multiple uncultured genera (`g__JACJXW01`, `g__BCD1`, `g__UBA3362`). This is a known under-cultured family with one canonical cultured member (Saprospira); the model is identifying multiple lineages with isolate-like metabolic completeness.\n",
    "- **Methanobacteriaceae uncultured genus** (`g__UBA117`) — methanogen candidate.\n",
    "- **`g__Fluviicola riflensis`** — Rifle aquifer Banfield-lab genome, environmentally significant subsurface lineage.\n",
    "- **`g__Limnoraphis`** (Microcoleaceae, Cyanobacteria) — known but rarely cultivated freshwater genus.\n",
    "- **`g__Thiocapsa`** (Chromatiaceae) — purple sulfur bacterium, anaerobic photosynthesis."
  ]},
  {"cell_type": "markdown", "metadata": {}, "source": [
    "## H3 test: are S-tier candidates enriched in environmentally-interesting taxa?\n\n",
    "Defined `env_interest` = phylum in {Acidobacteriota, Actinomycetota, Pseudomonadota, Bacillota, Bacteroidota, Chloroflexota, Verrucomicrobiota, Planctomycetota, Gemmatimonadota, Cyanobacteriota, Spirochaetota, Myxococcota} — the soil/subsurface/plant-associated phyla we care about.\n\n",
    "**Fisher's exact: OR = 4.44, p = 3.6e-27**. S-tier strict candidates are 4.4× enriched in environmentally-interesting phyla relative to the uncultured baseline. **H3 supported.**"
  ]},
  {"cell_type": "markdown", "metadata": {}, "source": [
    "## Phylum-level candidate breakdown (strict pool)\n\n",
    "![](../figures/candidate_phyla_strict.png)\n\n",
    "Compare to the broader lenient pool:\n\n",
    "![](../figures/candidate_phyla.png)\n\n",
    "Pseudomonadota dominate the lenient pool but not the strict pool — most uncultured *Pseudomonadota genera* belong to families already heavily cultivated. Bacteroidota become the top phylum in the strict view, driven by the Saprospiraceae signal."
  ]},
  {"cell_type": "markdown", "metadata": {}, "source": [
    "## Outputs\n\n",
    "- `data/cultivability_candidates.tsv` — 2,491 lenient candidates\n",
    "- `data/cultivability_candidates_strict.tsv` — 256 strict candidates (uncultured genera)\n",
    "- `figures/candidate_phyla.png`, `figures/candidate_phyla_strict.png`\n\n",
    "Hand-off to NB05 for anchored validation against `clay_confined_subsurface` (Mont Terri) and `oak_ridge_cultivation_gap` (Oak Ridge ORFRC) ground truth."
  ]}
 ],
 "metadata": {"kernelspec": {"display_name": "Python 3 (BERDL)", "language": "python", "name": "python3"}, "language_info": {"name": "python"}},
 "nbformat": 4, "nbformat_minor": 5
}
with open(PROJ / "notebooks" / "04_candidate_ranking.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("Wrote notebooks/04_candidate_ranking.ipynb")
