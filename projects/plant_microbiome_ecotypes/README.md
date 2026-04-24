# Plant Microbiome Ecotypes

Compartment-specific functional guilds and their genetic architecture in plant-associated microbiomes.

## Research Question

What is the genomic basis for plant-microbe associations across different plant compartments (rhizosphere, root, phyllosphere, endophyte)? Can we classify plant-associated microbial genera into beneficial, neutral, pathogenic, and dual-nature cohorts with mechanistic hypotheses, and identify which plant-interaction functions are associated with horizontal gene transfer vs. stable vertical inheritance?

## Overview

This project classifies 293K bacterial/archaeal genomes across 27.7K species by plant compartment association (rhizosphere, root, phyllosphere, endophyte) and characterizes the genomic basis of plant-microbe interactions. Species are classified into beneficial (PGP), pathogenic, dual-nature, and neutral cohorts based on marker gene profiles, with analysis of genomic architecture (core vs. accessory), metabolic complementarity, and horizontal gene transfer signatures.

## Hypotheses

| ID | Hypothesis | Notebook | Status |
|----|-----------|----------|--------|
| H0 | Phylogenetic null — functional differences explained by phylogeny alone | All + cluster-robust | Partially rejected, three-tier: 3 species-level (N-fix, ACC deaminase, T3SS), 5 cassette-level (phenazine, CWDEs, phosphate-sol, effector cluster-robust sig but not species-level), 6 not robust |
| H1 | Compartment specificity — distinct functional profiles per plant compartment | NB04, NB14, db-RDA | Weakly supported — small location shift (db-RDA R²=0.060, p<0.001) plus significant dispersion (PERMDISP p<0.001); original R²=0.527 was a panel + sampling artifact |
| H2 | Beneficial genes are core, pathogenic genes are accessory | NB05, NB09 | Supported (p=3.4e-125) |
| H3 | Co-occurring genera show metabolic complementarity | NB06, NB14 | Not supported (small |d|≈0.4, redundancy direction robust; NB06's -7.54 was a Cohen d formula error) |
| H4 | Compartment-adaptation genes show HGT signatures | NB05, NB11 | Partially supported |
| H5 | Novel gene families distinguish plant-associated species | NB03, NB09, NB14 | Supported (reframed as "enriched gene families"; 48/50 OGs survive real per-species phylum+genome-size control at q<0.05) |
| H6 | Host specificity detectable from metadata + MGnify | NB10, NB11, NB13, full-18 host-subclade scan | Supported: 2 species pass both within- and across-species Bonferroni — *X. campestris* × Brassica (p=3.3e-11), *X. vasicola* × *Zea mays* (p=1.7e-10) — confirming canonical pathovar-host specializations |
| H7 | Within-species subclade segregation of plant-adaptation | NB12, NB13, full-65 scan | Weakly supported: 5/17 testable species pass Bonferroni-Fisher (3 also Cochran-valid: *X. vasicola*, *P. avellanae*, *X. campestris*); 47/65 candidate species lack phylo tree coverage |

## Notebooks

### Phase 1 (NB01–NB08)

| Notebook | Title | Compute | Description |
|----------|-------|---------|-------------|
| NB01 | Genome Census | Spark | Classify genomes by plant compartment; go/no-go checkpoint |
| NB02 | Marker Gene Survey | Spark | Search for PGP, pathogenicity, and colonization markers; classify species into cohorts |
| NB03 | Enrichment Analysis | Spark + local | Genome-wide eggNOG OG enrichment; volcano plot; phylogenetic control |
| NB04 | Compartment Profiling | Spark + local | Per-compartment functional signatures; GapMind pathways; PERMANOVA |
| NB05 | Genomic Architecture | Spark + local | Core/accessory distribution (H2); mobility proxies (H4) |
| NB06 | Complementarity | Spark + local | NMDC co-occurrence; GapMind gap-filling; PGP-pathogen interactions |
| NB07 | Cohort Synthesis | Local | Composite scoring; genus dossiers; hypothesis summary |
| NB08 | Adversarial Revisions | Spark + local | Sensitivity analyses, negative controls, HGT deep dive, predictive classifiers |

### Phase 2 (NB09–NB12)

| Notebook | Title | Compute | Description |
|----------|-------|---------|-------------|
| NB09 | Novel OG Annotation | Spark + local | Functional annotation of 50 plant-enriched OGs via InterProScan, GO, MetaCyc |
| NB10 | Refined Markers & Host Species | Spark + local | 17-marker panel with KEGG module gating; host species extraction |
| NB11 | MGnify Integration | Spark + local | Cross-validation with MGnify: mobilome, BGC, KEGG enrichment, host specificity |
| NB12 | Subclade Analysis | Spark + local | Within-species phylogenetic subclade clustering and plant-association mapping |

### Phase 2b (NB13–NB15) — Adversarial-review corrections

| Notebook | Title | Compute | Description |
|----------|-------|---------|-------------|
| NB13 | Validation, Pfam Recovery & Subclade Fix | Spark + local | Species-level confusion matrix (C3), versioned-Pfam LIKE query, NB12 genome ID fix (I6) |
| NB14 | Deferred Statistical Controls | Local | L1-regularized logit (C1), genome-size covariate (C4), within-genus shuffling, prevalence-weighted complementarity (I1) |
| NB15 | Final Synthesis | Local | Hypothesis verdict table and synthesis figure across H0–H7 |

## Key Outputs

| File | Description |
|------|-------------|
| `data/species_compartment.csv` | Species-level plant compartment assignments |
| `data/species_marker_matrix.csv` | Species × marker function presence/absence |
| `data/species_cohort_markers.csv` | PGP/pathogen/dual-nature/neutral cohort assignments |
| `data/enrichment_results.csv` | OG-level enrichment in plant-associated species |
| `data/novel_plant_markers.csv` | Novel gene families enriched in plant species |
| `data/compartment_profiles.csv` | Per-compartment marker enrichment results |
| `data/genomic_architecture.csv` | Core/accessory/singleton statistics by marker type |
| `data/complementarity_network.csv` | Genus-pair metabolic complementarity scores |
| `data/cohort_assignments.csv` | Final composite cohort assignments |
| `data/genus_dossiers.csv` | Detailed profiles for top 20-30 genera |

## Status

Phase 2b complete (NB01–NB15 + 4 follow-up scripts addressing all paired-adversarial-review findings) — see [Report](REPORT.md) for findings, [REVIEW_2.md](REVIEW_2.md) for standard review, and [REVIEW_2_ADVERSARIAL.md](REVIEW_2_ADVERSARIAL.md) for the paired adversarial review that prompted the final honesty revisions to §11. Phase 1 tested H0–H5 across 8 notebooks; Phase 2 (NB09–NB12) extended with novel OG annotation, refined marker panel, MGnify cross-validation, and within-species subclade analysis; Phase 2b (NB13–NB15) partially addressed adversarial-review issues and revealed new ones. Final status after adversarial reconciliation: **H1 weakened** (86% of original R² was a taxonomic-sampling artifact), **H3 still not supported** (d≈-0.4 after Cohen-formula correction; prior -7.54 was a formula error), **H7 weakly supported in 5/17 testable species** after full 65-species scan (X. vasicola, Mesorhizobium sp002294985, A. pusense, P. avellanae, X. campestris pass Bonferroni-Fisher; 3 also Cochran-valid). 47/65 candidate species lack phylo tree coverage in BERDL. **H6 supported** in 2/9 testable species — X. campestris segregates to Brassica (46/47 in best subclade) and X. vasicola to Zea mays (47/52), both canonical pathovar-host specializations, **H5 strengthened** (48/50 novel OGs survive real per-species phylum+genome-size control at q<0.05 — closed on 2026-04-25 using NB03's cached OG matrix, replacing the circular simulation the adversarial reviewer flagged), **H2 stands at phylum/genus scale**. Most marker signals are genus-scale not species-level. All five paired-adversarial-review issues closed on 2026-04-25: item 17 (real per-species C4), item 18 (cluster-robust GLM as PGLMM analogue for C1, three-tier marker verdict), item 19 (full 65-species H7 scan, 5/17 testable species significant), item 20 (db-RDA H1 location-vs-dispersion: location R²=0.060, dispersion confirmed), item 21 (bakta-vs-IPS Pfam audit: 12/22 marker Pfams silently missing from bakta_pfam_domains, project unaffected because NB10 uses InterProScan).

## Data Collections

This project uses data from the following BERDL collections:
- `kbase_ke_pangenome` — 293K genomes, pangenome gene clusters, bakta/eggNOG/GapMind annotations, InterProScan domains, phylogenetic trees
- `kescience_mgnify` — MGnify genome catalogue: 20K species across 4 biomes, mobilome, BGC, KEGG modules
- `kescience_bacdive` — BacDive strain isolation sources and metabolic phenotypes
- `nmdc_arkin` — NMDC community ecology taxonomy features

## Running

Notebooks require the BERDL JupyterHub environment with Spark access. Run in order (NB01-NB07); each notebook caches intermediate results to CSV so individual notebooks can be re-run independently after first execution.

## Prior Work Reused

- `pgp_pangenome_ecology`: Environment classification regex, PGP gene queries
- `nmdc_community_metabolic_ecology`: NMDC taxonomy bridge, GapMind community aggregation
- `phb_granule_ecology`: Environment harmonization patterns
- `prophage_ecology`: eggNOG-based mobile element proxy methodology

## Reproduction

1. Ensure access to the BERDL JupyterHub environment with Spark
2. Install dependencies: `pip install -r requirements.txt`
3. Run notebooks in order: NB01 through NB15
4. Each notebook caches intermediate results to `data/`; re-running individual notebooks after first execution is safe
5. NB08 (adversarial revisions) is optional but recommended for reproducing sensitivity analyses
6. NB09–NB12 (Phase 2) extend the analysis with InterProScan annotation, MGnify cross-validation, and subclade analysis
7. NB13–NB15 (Phase 2b) close adversarial-review gaps: species-level validation, Pfam LIKE-query recovery, subclade genome-ID fix, regularized phylogenetic control, and final hypothesis synthesis

## Authors

- Adam P. Arkin (ORCID: 0000-0002-4999-2931) — U.C. Berkeley / Lawrence Berkeley National Laboratory
