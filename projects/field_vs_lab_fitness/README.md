# Field vs Lab Gene Importance in *Desulfovibrio vulgaris* Hildenborough

## Research Question

Which genes matter for survival under environmentally-realistic conditions but appear dispensable in the lab, and vice versa? Do field-relevant fitness effects predict pangenome conservation better than lab-only effects?

## Status

Completed -- field-stress genes are modestly more conserved (83.6% core) than the 76.3% baseline, but condition type is a weak predictor of conservation overall. Antibiotic and metal resistance genes are the least conserved, consistent with accessory-genome-encoded adaptive traits.

## Overview

DvH has 757 RB-TnSeq experiments spanning environmentally-relevant stresses (uranium, mercury, nitrate, sulfate reduction) and standard lab conditions (antibiotics, rich media). This project classifies these experiments by ecological relevance and tests whether genes important under field-relevant conditions show different pangenome conservation patterns than genes important under lab-only conditions. It builds on `conservation_vs_fitness` (FB-pangenome link, essential genes) and `fitness_modules` (ICA modules, condition activity scores).

Key results: field-stress and field-core genes are significantly enriched in the core genome (OR=1.58 and 1.46, FDR q<0.03), but fitness magnitude matters more than condition type for overall prediction (10-fold CV-AUC 0.52-0.55 for field/lab fitness vs 0.65 with gene length). Antibiotic and heavy-metal resistance genes trend below baseline (73% and 71% core vs 76%). Module-level analysis identifies 21 "ecological" modules (0.98 core fraction) and 9 "lab" modules (0.52 core fraction). ENIGMA CORAL database contains no DvH data. See [REPORT.md](REPORT.md) for full findings and interpretation.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Hypothesis, approach, query strategy, analysis plan
- [Report](REPORT.md) -- Findings, interpretation, literature context, supporting evidence
- [References](references.md) -- Cited literature

## Data Sources

| Asset | Location | What it provides |
|-------|----------|-----------------|
| DvH pangenome link | `projects/conservation_vs_fitness/data/fb_pangenome_link.tsv` | 3,206 gene-to-cluster links with core/aux/singleton status |
| DvH essential genes | `projects/conservation_vs_fitness/data/essential_genes.tsv` | 678 essential, 2,725 non-essential genes |
| DvH fitness matrix | `projects/fitness_modules/data/matrices/DvH_fitness_matrix.csv` | 2,741 genes x 757 experiments |
| DvH experiment metadata | `projects/fitness_modules/data/annotations/DvH_experiments.csv` | Condition descriptions, groups, media |
| DvH ICA modules | `projects/fitness_modules/data/modules/DvH_gene_membership.csv` | 52 modules, gene membership |
| DvH module annotations | `projects/fitness_modules/data/modules/DvH_module_annotations.csv` | Module functional enrichments |
| DvH module conditions | `projects/fitness_modules/data/modules/DvH_module_conditions.csv` | Module-condition activity scores |
| SEED annotations | `projects/conservation_vs_fitness/data/seed_annotations.tsv` | Functional annotations |

## Project Structure

```
projects/field_vs_lab_fitness/
├── README.md
├── RESEARCH_PLAN.md
├── REPORT.md
├── references.md
├── notebooks/
│   ├── 01_enigma_discovery.ipynb          # Discover ENIGMA CORAL tables (Spark)
│   ├── 02_condition_classification.ipynb  # Classify 757 experiments (local)
│   ├── 03_fitness_conservation.ipynb      # Field vs lab x conservation (local)
│   └── 04_module_analysis.ipynb           # Module-level analysis (local)
├── data/                                  # Extracted/processed data
├── figures/                               # Key visualizations
└── requirements.txt
```

## Reproduction

**Prerequisites:**
- Python 3.10+ with pandas, numpy, matplotlib, seaborn, scipy, scikit-learn
- BERDL Spark Connect for NB01 (or JupyterHub)
- All other data already cached from upstream projects

**Running the pipeline:**

```bash
cd projects/field_vs_lab_fitness
pip install -r requirements.txt

# Step 1: ENIGMA discovery (Spark -- already run, results in NB01 summary)
# Step 2-4: Local analysis
jupyter nbconvert --to notebook --execute --inplace notebooks/02_condition_classification.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_fitness_conservation.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/04_module_analysis.ipynb
```

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory

## References

- Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509. PMID: 29769716
- Trotter VV et al. (2023). "Large-scale genetic characterization of the model sulfate-reducing bacterium, *Desulfovibrio vulgaris* Hildenborough." *Front Microbiol* 14:1095132. PMID: 37065130
- Rosconi F et al. (2022). "A bacterial pan-genome makes gene essentiality strain-dependent and evolvable." *Nat Microbiol* 7:1580-1592. PMID: 36097170
- Lee SA et al. (2015). "General and condition-specific essential functions of *Pseudomonas aeruginosa*." *Proc Natl Acad Sci USA* 112:5189-5194. PMID: 25848053
- Akusobi C et al. (2025). "Transposon-sequencing across multiple *Mycobacterium abscessus* isolates reveals significant functional genomic diversity among strains." *mBio* 16:e02488-24. PMID: 39745363
- Shi W et al. (2021). "Genetic basis of chromate adaptation and the role of pre-existing genetic divergence." *mSystems* 6:e00351-21. PMID: 34061571
- Huang Z et al. (2022). "Genomic analysis reveals high intra-species diversity of *Shewanella algae*." *Microb Genom* 8:000786. PMID: 35143386
- Borchert AJ et al. (2019). "Modular fitness landscapes reveal parallels between independent biological systems." *Nat Ecol Evol* 3:1233-1242
