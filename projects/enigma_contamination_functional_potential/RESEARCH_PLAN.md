# Research Plan: Contamination Gradient vs Functional Potential in ENIGMA Communities

## Research Question

Do high-contamination Oak Ridge groundwater communities show enrichment for taxa with higher inferred stress-related functional potential compared with low-contamination communities?

## Hypothesis

- **H0**: After controlling for sampling depth and site structure, contamination level is not associated with inferred stress-related functional potential in community composition.
- **H1**: Higher contamination is associated with higher inferred stress-related functional potential in community composition.

## Literature Context

Prior BERIL work established that ENIGMA CORAL supports field ecology analysis and that several genera correlate with uranium abundance (`projects/lab_field_ecology/`). This project extends from genus-abundance correlation to functional inference by mapping taxa observed across contamination gradients to functional annotations in BERDL pangenome resources.

## Approach

1. Build a contamination-indexed sample set from ENIGMA geochemistry.
2. Build community composition matrices for overlapping samples.
3. Map ENIGMA taxa to BERDL pangenome taxa (NCBI taxid and/or normalized taxon name).
4. Summarize stress-relevant functional annotation signals per taxon.
5. Aggregate functional potential per sample and test association with contamination.
6. Run sensitivity checks for mapping ambiguity and low-abundance taxa.

## Data Sources

| Source | Table/File | Purpose |
|---|---|---|
| ENIGMA geochemistry | `enigma_coral.ddt_brick0000010` | Per-sample contaminant concentrations (uranium + co-metals) |
| ENIGMA community counts | `enigma_coral.ddt_brick0000459` | Community abundance matrix |
| ENIGMA taxonomy mapping | `enigma_coral.ddt_brick0000454` | ASV-to-taxon linkage |
| ENIGMA sample metadata | `enigma_coral.sdt_sample`, `enigma_coral.sdt_community`, `enigma_coral.sdt_location` | Site/sample joins and location covariates |
| Pangenome taxonomy | `kbase_ke_pangenome.gtdb_taxonomy_r214v1`, `kbase_ke_pangenome.gtdb_species_clade`, `kbase_ke_pangenome.genome` | Taxonomic bridge into functional annotations |
| Pangenome function | `kbase_ke_pangenome.eggnog_mapper_annotations` (+ cluster linkage tables as needed) | Functional potential features |

## Query Strategy

### NB01: ENIGMA Extraction and QC (Spark)

- Reproduce overlap extraction pattern used in prior ENIGMA projects.
- Validate current row counts and key join cardinalities.
- Produce clean exports:
  - `data/geochemistry_sample_matrix.tsv`
  - `data/community_taxon_counts.tsv`
  - `data/sample_location_metadata.tsv`

### NB02: Taxonomy Bridge and Functional Feature Build (Spark)

- Build taxon bridge from ENIGMA taxa to pangenome taxa.
- Start with conservative mappings (exact or high-confidence normalized matches).
- Create per-taxon feature table with stress-relevant annotation summaries.
- Export:
  - `data/taxon_bridge.tsv`
  - `data/taxon_functional_features.tsv`

### NB03: Functional Potential vs Contamination (Local/Spark)

- Define contamination index (e.g., uranium z-score, or PCA over metal concentrations).
- Compute site-level weighted functional potential scores from community abundances.
- Fit models:
  - rank correlation
  - robust linear model (with covariates where available)
  - permutation test for label robustness
- Export:
  - `data/site_functional_scores.tsv`
  - `data/model_results.tsv`

## Analysis Plan

### Notebook 01: `01_enigma_extraction_qc.ipynb`
- **Goal**: verify ENIGMA joins and extract analysis-ready site/taxon matrices.
- **Expected output**: overlap sample inventory and contamination variables.

### Notebook 02: `02_taxonomy_bridge_functional_features.ipynb`
- **Goal**: map ENIGMA taxa to pangenome and build annotation-derived stress features.
- **Expected output**: taxon bridge diagnostics and feature table.

### Notebook 03: `03_contamination_functional_models.ipynb`
- **Goal**: test H0/H1 with contamination-functional association models.
- **Expected output**: effect sizes, significance, and diagnostic plots.

## Expected Outcomes

- **If H1 supported**: contaminated sites are functionally shifted toward stress-related signatures.
- **If H0 not rejected**: contamination may structure taxonomy without detectable functional-shift signal under current mapping resolution.
- **Potential confounders**: sparse taxonomy resolution, compositional effects, incomplete taxon-to-pangenome mapping, temporal heterogeneity.

## Known Risks and Mitigations

- **Risk**: ENIGMA taxon labels may not map cleanly to pangenome entities.
  - **Mitigation**: enforce confidence tiers; run analyses on strict and relaxed mapping sets.
- **Risk**: string-typed numeric fields in ENIGMA bricks.
  - **Mitigation**: explicit CAST in Spark SQL; log parsing failure rates.
- **Risk**: sparse/zero-inflated abundance vectors.
  - **Mitigation**: prevalence filtering and compositional robustness checks.

## Revision History

- **v1 (2026-02-15)**: Initial plan for ENIGMA contamination-functional potential project.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) -- Lawrence Berkeley National Laboratory
