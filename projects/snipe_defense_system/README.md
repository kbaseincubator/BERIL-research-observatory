# SNIPE Defense System: Prevalence and Taxonomic Distribution in the BERDL Pangenome

## Research Question

How prevalent are SNIPE (Surface-associated Nuclease Inhibiting Phage Entry) homologues across the 293K-genome BERDL pangenome, and does their taxonomic distribution, environmental context, or pangenome status (core vs. accessory) reveal ecological patterns of phage defense?

## Status

Complete — All 4 notebooks executed. See [REPORT.md](REPORT.md) for findings.

## Overview

SNIPE is a recently characterized bacterial antiphage defense system (Saxton et al. 2026, *Nature*) that constitutively localizes to the inner membrane and cleaves phage DNA during genome injection. It achieves self/non-self discrimination through spatial organization — targeting DNA passing through the phage injection machinery (ManYZ/TMP complex) — rather than sequence-based recognition. Over 500 SNIPE homologues have been identified across diverse bacterial phyla.

SNIPE is defined by two signature domains: **DUF4041** (PF13250 / [IPR025280](https://www.ebi.ac.uk/interpro/entry/InterPro/IPR025280/), binds phage tape measure proteins and incoming DNA) and a **GIY-YIG clan nuclease** (PF13455 / Mug113, cleaves phage DNA). Some homologues also carry alternative membrane-anchoring domains (DivIVA-like, type III secretion ATPase-like) instead of transmembrane helices.

This project uses three complementary data sources to survey SNIPE:

1. **BERDL Pangenome** (293K genomes, 93M eggNOG annotations with Pfam domains) — survey prevalence, taxonomic distribution, core vs. accessory status, and environmental niches via AlphaEarth embeddings
2. **PhageFoundry genome browsers** (4 species: *Acinetobacter*, *Klebsiella*, *P. aeruginosa*, *P. viridiflava*) — search for SNIPE in phage-therapy-relevant pathogens and assess defense gene context
3. **NMDC metagenomes** (5,456 samples with DUF4041 annotations) — examine SNIPE prevalence in environmental metagenomes and their ecosystem distribution

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — Hypothesis, approach, query strategy, analysis plan
- [Report](REPORT.md) — Findings, interpretation, supporting evidence (pending)

## Key Domains

| Domain | Pfam | InterPro | Clan | Role in SNIPE |
|--------|------|----------|------|---------------|
| DUF4041 / T5orf172 | PF13250 | [IPR025280](https://www.ebi.ac.uk/interpro/entry/InterPro/IPR025280/) | — | Binds phage TMP and incoming DNA |
| Mug113 (GIY-YIG superfamily) | PF13455 | — | CL0418 (GIY-YIG) | Nuclease — cleaves phage DNA |
| DivIVA | PF02977 | — | — | Alternative membrane anchor (subset of homologues) |

**Note**: The paper describes the nuclease as "GIY-YIG" at the superfamily level. At the Pfam family level, the SNIPE nuclease is PF13455 (Mug113), not PF01541 (canonical GIY-YIG). Both belong to clan CL0418.

## References

- Saxton DS, DeWeirdt PC, Doering CR, Roney IJ, Laub MT. A membrane-bound nuclease directly cleaves phage DNA during genome injection. *Nature*. 2026 Feb 25. [DOI: 10.1038/s41586-026-10207-1](https://doi.org/10.1038/s41586-026-10207-1). PMID: [41741653](https://pubmed.ncbi.nlm.nih.gov/41741653/)

## Reproduction

**Prerequisites**: Python 3.10+, pandas, numpy, matplotlib, seaborn, scipy. BERDL Spark Connect or REST API access for data extraction.

```bash
cd projects/snipe_defense_system
pip install -r requirements.txt

# Step 1: Extract SNIPE domain hits from BERDL (requires BERDL access)
jupyter nbconvert --to notebook --execute --inplace notebooks/01_extract_snipe_domains.ipynb

# Step 2: Taxonomic and pangenome analysis (local, from cached data)
jupyter nbconvert --to notebook --execute --inplace notebooks/02_taxonomic_distribution.ipynb

# Step 3: Environmental niche analysis (local, from cached data)
jupyter nbconvert --to notebook --execute --inplace notebooks/03_environmental_analysis.ipynb

# Step 4: PhageFoundry + NMDC metagenome analysis (requires BERDL + NMDC access)
jupyter nbconvert --to notebook --execute --inplace notebooks/04_phage_databases.ipynb
```

## Future Work

- [Fitness Data Curation Plan](PLAN_fitness_data_curation.md) — Extract and analyze ManXYZ and SNIPE knockout fitness data from *Methanococcus maripaludis* JJ (129 experiments) and *E. coli* K-12 (168 experiments)

## Authors

- **Chris Mungall** — Lawrence Berkeley National Laboratory
