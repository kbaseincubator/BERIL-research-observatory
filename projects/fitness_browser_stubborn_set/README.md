# Fitness Browser Stubborn Set — Strong Phenotypes, No Price-2018 Re-annotation

## Research Question

Among Fitness Browser genes with strong, specific fitness phenotypes that were NOT re-annotated by Price et al. (2018), can BERDL-native evidence distinguish genes where an improved annotation is plausible from genes where existing evidence is genuinely insufficient?

## Status

In Progress — research plan created, awaiting analysis.

## Overview

Price et al. (2018) used genome-wide mutant fitness data to propose improved annotations for bacterial genes of unknown function. The paper formally re-annotated 456 genes (transporters + catabolism enzymes); the curator-accumulated `kescience_fitnessbrowser.reannotation` table in BERDL has grown to **1,762 gene assignments across 36 organisms**. But many additional genes satisfy Price's own specific-phenotype significance thresholds (`|fit| > 1`, `|t| > 5`, condition-specificity tests) and yet received no re-annotation.

This project reconstructs the curator decision boundary. We define a candidate pool using the specific-phenotype criterion, subtract the reannotation set to form a "stubborn set," score each stubborn gene against the evidence sources the FEBA pipeline itself uses (conserved cofitness, ortholog phenotype agreement, TIGRFam/Pfam, KEGG, SEED, MetaCyc), and partition the stubborn set into **improvable-now** vs. **unresolvable-from-evidence** buckets — using only BERDL-native data, no new compute.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, thresholds, query strategy
- [Report](REPORT.md) — findings, interpretation (TBD)
- [References](references.md) — Price 2018 + Fitness Browser documentation
- Notebooks: [notebooks/](notebooks/)
- Data artifacts: [data/](data/) (gitignored)
- Figures: [figures/](figures/)

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

Will include:
- Prerequisites: BERDL access (`KBASE_AUTH_TOKEN`), `.venv-berdl` + proxy chain for local Spark Connect, or a BERDL JupyterHub session.
- Step-by-step: run `01_candidate_pool_and_stubborn_set.ipynb` → `02_evidence_scoring.ipynb` → `03_partition_and_characterization.ipynb` → `04_spot_check.ipynb`.
- Expected runtime: moderate — primary cost is the specific-phenotype groupBy over `genefitness` (27M rows).

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
