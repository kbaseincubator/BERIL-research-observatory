# ENIGMA Carbon Census 1

## Research Question
For 83 groundwater- and necromass-derived carbon compounds proposed for community
enrichment and isolate phenotyping, what is known about (1) their environmental
distribution, (2) the catabolic pathways that could utilize them, (3) the organisms
encoding those pathways, and (4) how those pathways co-occur within and across
organisms — and which ENIGMA isolates or environmentally observed organisms are
likely utilizers of each compound?

## Status
Completed — a tiered knowledge census of 83 ENIGMA Carbon Census compounds; ~89% (74/83) are organism-dark (no isolate utilizer call), with callable catabolism phylogenetically concentrated in Burkholderiales.

## Overview
The Carbon Census selected 83 compounds (59 from SSO groundwater, 24 from necromass)
spanning natural-product chemical classes (alkaloids, shikimates/phenylpropanoids,
terpenoids, fatty acids, polyketides). This project assembles a knowledge census
linking each compound to candidate degradation pathways, the organisms encoding them,
within/across-organism pathway co-occurrence, and predicted utilizers in the ENIGMA
isolate collection and environmental data — to guide enrichment design and
genetic-determinant discovery.

## Quick Links
- [Research Plan](RESEARCH_PLAN.md) — hypothesis, approach, query strategy
- [Report](REPORT.md) — findings, interpretation, supporting evidence

## Data Collections
PubChem (identity resolution); `kbase_ke_pangenome` (functional annotations);
`kescience_fitnessbrowser` (RB-TnSeq); `enigma_genome_depot_enigma` (isolate
catabolic annotations); `enigma` (SSO field 16S); `kbase.nmdc_arkin` +
`nmdc_metadata` (terrestrial/freshwater metagenome abundance + ENVO/GOLD labels);
`planetmicrobe.planetmicrobe` (marine abundance contrast); ModelSEED biochemistry.

## Input Data
- `user_data/Carbon_Census_Compound_Selections.xlsx` — 92 rows (83 selected),
  with `Unique ID` (Cc1_xx), name, NPC Pathway/Superclass/Class, source, MW, LogP,
  solubility, and supplier metadata.

## Reproduction
Prerequisites: on-cluster BERDL JupyterHub (Spark Connect) with `KBASE_AUTH_TOKEN`
in `../../.env`; Python deps in `requirements.txt`; internet for PubChem PUG-REST
(NB01, NB02c) and enviPath (NB02). Run notebooks in order
`00 → 01 → 02 → 02b → 02c → 03 → 04 → 05 → 05b → 06 → 07 → 07b → 08 → 09`; each is
built/executed by the matching `notebooks/build_nb*.py` (run from `notebooks/`).

Spark-vs-local requirements (lowers the barrier for off-cluster collaborators, who
can run the local stages while provisioning cluster access):
- **🌩 Spark Connect required:** NB03, NB04, NB05, NB06, NB07, NB07b, NB08.
- **💻 local / external-API only:** NB00, NB01, NB02, NB02b, NB02c, NB05b, NB09
  (NB05b and NB09 recompute from cached `data/*.tsv`; no Spark re-run).

Outputs land in `data/` and `figures/`; the master census table is
`data/census_master_summary.tsv`.

## Authors
- Adam Arkin (University of California, Berkeley; ORCID 0000-0002-4999-2931)
