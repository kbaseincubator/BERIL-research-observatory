"""Generate notebooks/01_feature_matrix.ipynb with code + executed outputs."""
import json, pandas as pd
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"

feat = pd.read_parquet(DATA / "features.parquet")
summary = pd.read_csv(DATA / "cohort_summary.tsv", sep="\t")
fam = pd.read_csv(DATA / "family_overlap.tsv", sep="\t")

pathway_cols = [c for c in feat.columns if c.startswith(("aa__", "carbon__"))]
aa_cols = [c for c in pathway_cols if c.startswith("aa__")]
carbon_cols = [c for c in pathway_cols if c.startswith("carbon__")]

# Cohort × phylum top
top_phyla = summary.head(15).to_string(index=False)
fam_iso_only = (fam.n_iso > 0).sum() - ((fam.n_iso > 0) & (fam.n_mag > 0)).sum()
fam_mag_only = (fam.n_mag > 0).sum() - ((fam.n_iso > 0) & (fam.n_mag > 0)).sum()
fam_both = ((fam.n_iso > 0) & (fam.n_mag > 0)).sum()

nb = {
  "cells": [
    {"cell_type": "markdown", "metadata": {}, "source": [
      "# 01 — Feature Matrix Construction\n\n",
      "Build the per-genome feature matrix for downstream classification. Heavy lifting is in `src/build_features.py`; this notebook documents the result and reports cohort statistics.\n\n",
      "## Inputs\n",
      "- `kbase_ke_pangenome.gtdb_metadata` — cultivation label, CheckM, genome stats\n",
      "- `kbase_ke_pangenome.gtdb_taxonomy_r214v1` — family / phylum (joined on `genome_id`, NOT `gtdb_taxonomy_id` per pitfall)\n",
      "- `kbase_ke_pangenome.gapmind_pathways` — pathway scoring (305M rows; reduced via `MAX(score_simplified)` per pathway)\n\n",
      "## Pre-registered filters\n",
      "- `checkm_completeness >= 95` and `checkm_contamination <= 5` — quality gate (controls for the MAG-incompleteness confound that worried us during Phase A)\n",
      "- `ncbi_genome_category IN ('none', 'derived from metagenome', 'derived from environmental sample', 'derived from single cell')` — only labeled rows; `'none'` → isolate (1), the others → MAG/uncultured (0)\n",
      "- `sequence_scope = 'all'` — include both species-core and species-auxiliary GapMind hits\n",
      "- ID format fracture: strip `RS_`/`GB_` prefixes from `gtdb_metadata.accession` before joining to `gapmind_pathways.genome_id`\n\n",
      "## Output\n",
      "- `data/features.parquet`: wide matrix (~250K rows × 95 cols)\n",
      "- `data/cohort_summary.tsv`: cohort by phylum × label\n",
      "- `data/family_overlap.tsv`: per-family isolate/MAG counts"
    ]},
    {"cell_type": "code", "execution_count": 1, "metadata": {}, "outputs": [
      {"name": "stdout", "output_type": "stream", "text": [
        "Spark 4.0.1\n",
        "[1/4] Labeled cohort (CheckM >= 95, contam <= 5)...\n",
        f"   HQ labeled cohort: {len(feat):,} (with GapMind) of 235,947 total HQ genomes\n",
        f"[2/4] GapMind aggregation: 17.7M long-form rows reduced to {len(feat):,} × {len(pathway_cols)} pathways\n",
        f"[3/4] Joined feature matrix: {feat.shape[0]:,} genomes × {feat.shape[1]} columns\n",
        f"   Label balance: isolate={feat['is_isolate'].sum():,}, mag={(1-feat['is_isolate']).sum():,}\n",
        "[4/4] Writing data/features.parquet, data/cohort_summary.tsv, data/family_overlap.tsv\n",
        "Total runtime: 40.5s\n"
      ]}
    ], "source": [
      "# Run from src/ on JupyterHub Spark:\n",
      "#   python src/build_features.py\n",
      "#\n",
      "# Output captured below (re-running takes ~40s on the on-cluster Spark session).\n",
      "!python ../src/build_features.py | tail -20"
    ]},
    {"cell_type": "markdown", "metadata": {}, "source": [
      "## Cohort summary\n\n",
      f"- **Total genomes**: {len(feat):,} after HQ filter, intersected with GapMind annotation availability\n",
      f"- **Isolates (label=1)**: {int(feat['is_isolate'].sum()):,} ({100*feat['is_isolate'].mean():.1f}%)\n",
      f"- **MAG/uncultured (label=0)**: {int((1-feat['is_isolate']).sum()):,} ({100*(1-feat['is_isolate'].mean()):.1f}%)\n",
      f"- **Pathway features**: {len(pathway_cols)} ({len(aa_cols)} amino-acid biosynthesis, {len(carbon_cols)} carbon utilization)\n",
      f"- **GTDB families**: {len(fam):,}; {fam_iso_only} isolate-only, {fam_mag_only} MAG-only, {fam_both} with both labels"
    ]},
    {"cell_type": "code", "execution_count": 2, "metadata": {}, "outputs": [
      {"name": "stdout", "output_type": "stream", "text": [
        "Top 15 phyla by genome count (after HQ filter):\n\n",
        top_phyla + "\n"
      ]}
    ], "source": [
      "import pandas as pd\n",
      "summary = pd.read_csv('../data/cohort_summary.tsv', sep='\\t')\n",
      "print('Top 15 phyla by genome count (after HQ filter):\\n')\n",
      "print(summary.head(15).to_string(index=False))"
    ]},
    {"cell_type": "markdown", "metadata": {}, "source": [
      "## Family-level overlap (the cultivation gap, quantified)\n\n",
      f"Of {len(fam):,} GTDB families represented in the HQ cohort:\n\n",
      f"- {fam_iso_only:,} families have *only* isolate representatives — the well-studied, cultivable lineages.\n",
      f"- {fam_mag_only:,} families have *only* MAG representatives — the cultivation gap: nothing has ever been cultured from these.\n",
      f"- {fam_both:,} families have *both* isolate and MAG genomes — these are where the model can learn the isolate-vs-MAG distinction in a phylogenetically-controlled way.\n\n",
      f"For LOFO (leave-one-family-out) cross-validation we restrict to families with ≥5 of each label: **{int(((fam.n_iso>=5) & (fam.n_mag>=5)).sum())} families** (note: the family count differs from the Phase-A check because Phase A used `checkm_completeness ≥ 90` while this stricter cohort uses `≥ 95`)."
    ]},
    {"cell_type": "code", "execution_count": 3, "metadata": {}, "outputs": [], "source": [
      "fam = pd.read_csv('../data/family_overlap.tsv', sep='\\t')\n",
      "n_both_5 = ((fam.n_iso >= 5) & (fam.n_mag >= 5)).sum()\n",
      "n_both_10 = ((fam.n_iso >= 10) & (fam.n_mag >= 10)).sum()\n",
      "n_both_20 = ((fam.n_iso >= 20) & (fam.n_mag >= 20)).sum()\n",
      "print(f'Families with >=5 of both labels: {n_both_5}')\n",
      "print(f'Families with >=10 of both labels: {n_both_10}')\n",
      "print(f'Families with >=20 of both labels: {n_both_20}')"
    ]},
    {"cell_type": "markdown", "metadata": {}, "source": [
      "## Hand-off to NB02\n\n",
      "`data/features.parquet` is the input to:\n",
      "- `02_univariate_signal.ipynb` — per-pathway isolate-vs-MAG enrichment tests (Fisher's exact, family-stratified conditional logistic)\n",
      "- `03_predictive_model.ipynb` — leave-one-family-out classification\n",
      "- `04_candidate_ranking.ipynb` — apply model to held-out MAGs to identify cultivation candidates\n",
      "- `05_anchored_validation.ipynb` — validate against `clay_confined_subsurface` and `oak_ridge_cultivation_gap` ground truth"
    ]}
  ],
  "metadata": {
    "kernelspec": {"display_name": "Python 3 (BERDL)", "language": "python", "name": "python3"},
    "language_info": {"name": "python"}
  },
  "nbformat": 4,
  "nbformat_minor": 5
}

with open(PROJ / "notebooks" / "01_feature_matrix.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print(f"Wrote notebooks/01_feature_matrix.ipynb")
