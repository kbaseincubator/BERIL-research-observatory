# Counter Ion Effects on Metal Fitness Measurements

## Research Question
When bacteria are exposed to metal salts (CoCl₂, NiCl₂, CuCl₂), how much of the observed fitness effect is caused by the metal cation versus the counter anion (chloride)? Does correcting for chloride confounding change the conclusions of the Pan-Bacterial Metal Fitness Atlas?

## Status
Completed — counter ions are NOT the primary confound. 39.8% of metal-important genes overlap with NaCl stress, but this reflects shared cellular vulnerability (not chloride from metal salts). Zinc sulfate (0 mM Cl⁻) shows higher overlap than most chloride metals. The Metal Fitness Atlas core enrichment is robust after correction. See [Report](REPORT.md) for full findings.

## Overview
The Fitness Browser's 559 metal experiments predominantly use chloride salts. At high concentrations (e.g., 250 mM CoCl₂ delivers 500 mM Cl⁻), the counter ion itself may cause significant fitness effects. This project leverages NaCl stress experiments available for 25 metal-tested organisms to decompose the metal fitness signal into a shared-stress component and a metal-specific component, then re-evaluates the Metal Fitness Atlas conclusions after correction. The key finding: the ~40% overlap is driven by shared stress biology (envelope damage, ion homeostasis), not counter ion contamination.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Sources
- `kescience_fitnessbrowser` — NaCl stress experiments (17+ organisms with both NaCl and metal data)
- `projects/metal_fitness_atlas/data/` — metal experiment classifications, fitness scores, conservation stats
- `projects/fitness_modules/data/matrices/` — cached full fitness matrices
- `projects/fitness_modules/data/annotations/` — experiment metadata
- `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` — FB-to-pangenome gene mapping
- `projects/essential_genome/data/all_seed_annotations.tsv` — SEED functional annotations

## Reproduction

### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- Access to prior project cached data (see Data Sources)

### Running the Pipeline
All notebooks run locally (no Spark required):
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_nacl_identification.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_metal_nacl_overlap.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_profile_decomposition.ipynb
jupyter nbconvert --to notebook --execute --inplace 04_corrected_atlas.ipynb
jupyter nbconvert --to notebook --execute --inplace 05_psrch2_comparison.ipynb
```
Notebooks must run in order. Full pipeline runs in under 1 minute.

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy
- Aindrila Mukhopadhyay (https://orcid.org/0000-0002-6513-7425), Lawrence Berkeley National Laboratory, US Department of Energy
