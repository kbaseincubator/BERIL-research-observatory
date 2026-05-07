# Harvard Forest Long-Term Warming — DNA vs RNA Functional Response

## Research Question

After ~25 years of +5°C experimental soil warming at the Harvard Forest Barre Woods plot, does the functional transcript pool (metatranscriptome KO/Pfam composition) diverge from the genome pool (metagenome KO/Pfam composition) more strongly than expected from neutral community turnover, and which functional categories drive any divergence?

## Status

In Progress — research plan created, awaiting analysis.

## Overview

Tests three linked hypotheses on NMDC study `nmdc:sty-11-8ws97026` (Blanchard lab, Barre Woods, Harvard Forest, USA): (H1) the transcript-pool functional profile diverges more between heated and control than the genome-pool profile; (H2) carbon-degradation KOs are enriched in heated metatranscriptomes consistent with published respiration-acceleration findings; (H3) organic and mineral horizons respond differently to warming. Uses 42 biosamples × 5 omics layers from the `nmdc_metadata` and `nmdc_results` tables in BERDL.

## Data

- **Source**: NMDC study `nmdc:sty-11-8ws97026` ("Molecular mechanisms underlying changes in the temperature sensitive respiration response of forest soils to long-term experimental warming")
- **PI**: Jeffrey Blanchard, U. Massachusetts Amherst
- **Site**: Barre Woods, Petersham, MA, USA (42.481 °N, −72.178 °W)
- **Treatment**: Heated (+5°C, ~25 years) vs Control
- **Horizons**: Organic (0–0.02 m) vs Mineral (0.02–0.10 m)
- **Sample count**: 42 biosamples
- **Layers used**: metagenome KO/Pfam, metatranscriptome KO, kraken2 read taxonomy, GTDB MAG taxonomy, ChEBI metabolite identifications

All data accessed via Spark SQL against the BERDL Lakehouse `nmdc` tenant. **Excluded**: `nmdc_arkin` tables.

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence (after analysis)

## Reproduction

*TBD — add prerequisites and step-by-step instructions after analysis is complete.*

## Authors

- Chris Mungall, LBNL, ORCID [0000-0002-6601-2165](https://orcid.org/0000-0002-6601-2165)
