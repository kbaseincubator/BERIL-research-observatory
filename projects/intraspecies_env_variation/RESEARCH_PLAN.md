# Research Plan: Lanthanide Methylotrophy, B Vitamin Auxotrophy, and Intraspecies Environmental Variation

## Motivation

Lanthanide-dependent methanol oxidation via XoxF is a major discovery in C1 metabolism, but its genomic context within pangenomes remains underexplored. *Methylobacterium extorquens* AM1 (NCBI Taxonomy ID: 272630) is the model organism for this biology, carrying both XoxF (lanthanide-dependent) and MxaF (calcium-dependent) methanol dehydrogenases. A preliminary analysis of 150 methylotrophic species in BERDL showed that only 12 carry both enzymes, while the majority are mxaF-only — though this is partly an eggNOG annotation artifact where xoxF is misclassified as mxaF.

The B vitamin angle is new: if *M. extorquens* has incomplete B vitamin biosynthesis pathways, those auxotrophies directly constrain growth medium design. If B vitamin profiles differ between xoxF-carrying and mxaF-only strains, that connects rare earth element biology to vitamin metabolism — a testable lab hypothesis.

The broader intraspecies environmental variation question provides cross-database infrastructure: joining pangenome gene content to NCBI biosample metadata (within-tenant `ncbi_env` and cross-tenant `nmdc_ncbi_biosamples`). This demonstrates BERDL's multi-tenant architecture enabling analyses impossible with a single database.

## Hypotheses

### H1: M. extorquens B vitamin auxotrophy
*M. extorquens* AM1 is auxotrophic for one or more B vitamins (likely B12/cobalamin given its cobalt-dependent enzymology). Incomplete pathways should be detectable via missing KEGG orthologs in the pangenome eggNOG annotations.

### H2: xoxF and B vitamin co-variation
Across *Methylobacterium* species, xoxF-carrying strains may show different B vitamin biosynthesis profiles than mxaF-only strains, reflecting co-evolution of metal cofactor usage and vitamin requirements.

### H3: Environment-gene association
For species with strains from diverse environments, specific accessory gene clusters are significantly associated with isolation environment (soil vs clinical vs aquatic etc.), and these environment-associated genes are enriched for niche-relevant functions.

## Query Strategy

### Notebook 01: M. extorquens B vitamin + xoxF/mxaF case study

**Target tables**: `eggnog_mapper_annotations`, `gene_cluster`, `gtdb_species_clade`, `pangenome`

**B vitamin KEGG pathways to query**:
- B1 thiamine: ko00730 (thiC, thiD, thiE, thiG, thiL, thiM)
- B2 riboflavin: ko00740 (ribA, ribB, ribC, ribD, ribE, ribH)
- B6 pyridoxine: ko00750 (pdxA, pdxB, pdxJ, pdxH, pdxK)
- B7 biotin: ko00780 (bioA, bioB, bioC, bioD, bioF, bioH)
- B9 folate: ko00790 (folA, folB, folC, folE, folK, folP)
- B12 cobalamin: ko00860 (cobA-cobW, ~30 genes)

**MDH query**: Search for Preferred_name IN ('xoxF', 'mxaF', 'mxaI', 'exaA') plus KEGG_ko patterns K14028, K14029, K00114, and PFAMs LIKE '%PQQ%'. Cross-reference EC numbers (1.1.2.7 = mxaF canonical, 1.1.2.8 = broad PQQ MDH used for xoxF).

**Key join**: `eggnog_mapper_annotations.query_name = gene_cluster.gene_cluster_id` filtered by `gtdb_species_clade_id LIKE '%extorquens%'`

### Notebook 02: Environmental metadata exploration

**Target tables**: `genome`, `ncbi_env`, `nmdc_ncbi_biosamples.biosamples_flattened`, `nmdc_ncbi_biosamples.env_triads_flattened`

**EAV pivot pattern** (from temporal_core_dynamics):
```sql
SELECT g.genome_id, g.gtdb_species_clade_id,
    MAX(CASE WHEN ne.harmonized_name = 'isolation_source' THEN ne.content END) as isolation_source,
    MAX(CASE WHEN ne.harmonized_name = 'host' THEN ne.content END) as host,
    MAX(CASE WHEN ne.harmonized_name = 'geo_loc_name' THEN ne.content END) as geo_loc_name,
    MAX(CASE WHEN ne.harmonized_name = 'env_broad_scale' THEN ne.content END) as env_broad_scale
FROM kbase_ke_pangenome.genome g
JOIN kbase_ke_pangenome.ncbi_env ne ON g.ncbi_biosample_id = ne.accession
GROUP BY g.genome_id, g.gtdb_species_clade_id
```

**Cross-tenant join** (column names to be validated in notebook):
```sql
SELECT g.genome_id, et.*
FROM kbase_ke_pangenome.genome g
JOIN nmdc_ncbi_biosamples.env_triads_flattened et
    ON g.ncbi_biosample_id = et.accession
```

### Notebook 03: Gene-environment statistical association

**Target tables**: `gene`, `gene_genecluster_junction`, `gene_cluster`, `eggnog_mapper_annotations`

**Gene cluster presence query** (species-filtered, accessory only):
```sql
SELECT DISTINCT g.genome_id, gg.gene_cluster_id
FROM kbase_ke_pangenome.gene g
JOIN kbase_ke_pangenome.gene_genecluster_junction gg ON g.gene_id = gg.gene_id
JOIN kbase_ke_pangenome.gene_cluster gc ON gg.gene_cluster_id = gc.gene_cluster_id
WHERE gc.gtdb_species_clade_id = '{species_id}'
  AND gc.is_core = false
```

**Statistical methods**: Fisher's exact test (2 environment categories) or chi-squared (>2), Benjamini-Hochberg FDR correction, significance threshold q < 0.05.

## Expected Outputs

- Per-species tables of environment-associated gene clusters with functional annotations
- B vitamin biosynthesis completeness matrix for *M. extorquens* strains
- Volcano plots, COG enrichment charts, B vitamin pathway diagrams
- Testable prediction: specific B vitamin supplements needed for optimal *M. extorquens* growth
