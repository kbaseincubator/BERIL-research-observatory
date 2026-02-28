# Metal-Specific vs General Stress Genes in the Metal Fitness Atlas

## Research Question
Among the 12,838 metal-important genes identified by the Metal Fitness Atlas, which are specifically required for metal tolerance vs general stress survival — and do the metal-specific genes show the expected accessory-genome enrichment?

## Status
Completed — 54% of metal-important genes are metal-specific (sick rate <5% under non-metal conditions), but these remain 88% core-enriched. The core genome robustness model holds even after controlling for specificity. YebC is the most metal-specific novel candidate (58%).

## Overview
The Metal Fitness Atlas found that metal-important genes are 87.4% core (OR=2.08), the opposite of the expected accessory enrichment for metal resistance. This project tests whether the core enrichment is driven by general stress genes (cell envelope, DNA repair) that are needed for many stresses, not just metals. By comparing each metal-important gene's fitness across all 5,945 non-metal experiments in the Fitness Browser, we classify genes as metal-specific, shared-stress, or generally sick. If metal-specific genes are accessory-enriched, this resolves the paradox and identifies the true metal resistance determinants.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, analysis strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Reproduction
### Prerequisites
- Python 3.11+ with packages in `requirements.txt`
- Prior project cached data (see RESEARCH_PLAN.md for full list)

### Running the Pipeline
All notebooks run locally (no Spark required):
```bash
pip install -r requirements.txt
cd notebooks/
jupyter nbconvert --to notebook --execute --inplace 01_experiment_classification.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_gene_specificity.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_conservation_analysis.ipynb
jupyter nbconvert --to notebook --execute --inplace 04_functional_enrichment.ipynb
```

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy
