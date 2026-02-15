# Lab Fitness Predicts Field Ecology at Oak Ridge

## Research Question

Do lab-measured fitness effects under contaminant stress predict the field abundance of Fitness Browser organisms across Oak Ridge groundwater sites with varying geochemistry?

## Status

Completed -- 14 of 26 FB genera detected at Oak Ridge across 108 sites. Genus abundance correlates with uranium for 5 of 11 tested genera after FDR correction (2 positive, 3 negative). Lab metal tolerance shows a suggestive but non-significant trend (rho=0.50, p=0.095). Community composition shifts with contamination, but the relationship between lab fitness and field ecology is more complex than simple tolerance metrics capture. See [REPORT.md](REPORT.md) for full findings.

## Overview

The ENIGMA CORAL database contains 108 groundwater samples from Oak Ridge FRC with both geochemistry measurements (uranium, chromium, nickel, zinc, iron) and 16S amplicon community composition. Several Fitness Browser organisms are detected in these communities (*Pseudomonas*, *Desulfovibrio*, *Sphingomonas*, *Caulobacter*). This project bridges lab-measured fitness (Fitness Browser, 48 organisms) with real field ecology (ENIGMA CORAL, 108 sites) by testing whether organisms that tolerate metals in the lab are more abundant at contaminated field sites. See [REPORT.md](REPORT.md) for full findings and interpretation.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) -- Hypothesis, approach, analysis plan
- [Report](REPORT.md) -- Findings, interpretation, literature context

## Data Sources

| Asset | Source | What it provides |
|-------|--------|-----------------|
| ENIGMA geochemistry | `enigma_coral.ddt_brick0000010` | Metal concentrations (uranium, Cr, Ni, Zn, Fe) per sample |
| ENIGMA community | `enigma_coral.ddt_brick0000459` | ASV counts per community (868K rows) |
| ENIGMA ASV taxonomy | `enigma_coral.ddt_brick0000454` | ASV to genus mapping (627K rows) |
| ENIGMA samples | `enigma_coral.sdt_sample` + `sdt_community` | Sample to location links |
| FB fitness stats | `fitness_effects_conservation/data/fitness_stats.tsv` | Per-gene fitness across 43 organisms |
| FB experiment metadata | `fitness_modules/data/annotations/*.csv` | Condition descriptions |
| FB organism mapping | `conservation_vs_fitness/data/organism_mapping.tsv` | FB orgId to species |
| FB pangenome link | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Gene to core/accessory |

## Project Structure

```
projects/lab_field_ecology/
├── README.md
├── RESEARCH_PLAN.md
├── REPORT.md
├── notebooks/
│   ├── 01_extract_enigma.ipynb       # Extract geochemistry + community (Spark)
│   ├── 02_genus_abundance.ipynb      # Build genus x site matrix (local)
│   └── 03_fitness_vs_field.ipynb     # Correlate lab fitness with field (local)
├── data/
├── figures/
└── requirements.txt
```

## Reproduction

**Prerequisites:** Python 3.10+, pandas, numpy, matplotlib, seaborn, scipy, statsmodels. Spark Connect for NB01.

```bash
cd projects/lab_field_ecology
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/01_extract_enigma.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_genus_abundance.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_fitness_vs_field.ipynb
```

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
