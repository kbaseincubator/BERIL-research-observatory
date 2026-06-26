# Research Plan: AlphaFold MSA Depth as a Lens on the Bacterial Annotation Gap

## Research Question

Does AlphaFold MSA depth predict functional annotation richness in the bacterial pangenome, and is structural novelty (low MSA depth) systematically enriched in accessory and singleton gene families relative to core genes?

## Background

AlphaFold's multiple sequence alignment (MSA) depth measures how many evolutionary homologs were available when predicting a protein's structure. High MSA depth indicates a protein is well-represented in sequence databases — it has many relatives across the tree of life, and its structure is likely well-characterized. Low MSA depth (< 10) indicates a structurally novel protein: few homologs exist, prediction confidence is lower, and functional annotation is typically absent.

The BERDL pangenome classifies every gene cluster as **core** (present in most species-clade genomes), **auxiliary/accessory** (present in some), or **singleton** (present in only one). A widely held assumption is that core genes are well-characterized while accessory genes harbor novelty. This project tests that assumption at the structural level, using MSA depth as an independent axis of novelty.

**Motivation from prior work:** `functional_dark_matter` (sequence annotation darkness) and `truly_dark_genes` (residual hypothetical genes after Bakta reannotation) both used sequence-level evidence. MSA depth is an orthogonal, structural axis — a gene can be sequence-annotated yet structurally dark, or hypothetical yet structurally well-characterized if homologs exist in other organisms.

**Critical data finding (pre-registration):** All 241,070,489 AlphaFold entries in BERDL are model_version = 6 — a single snapshot. The original research framing (version comparison over time) is not feasible. This plan pivots to the more tractable and scientifically richer question above.

## Hypotheses

- **H0 (null):** MSA depth is uncorrelated with pangenome core/accessory/singleton status and functional annotation richness.

- **H1:** Core gene clusters have significantly higher median MSA depth than accessory or singleton clusters. Rationale: universally conserved genes have more evolutionary relatives in sequence databases, yielding deeper MSAs.

- **H2:** Low MSA depth (< 10) is enriched in hypothetical proteins relative to annotated proteins. Rationale: structural and functional novelty are correlated — proteins that resist annotation also lack structural homologs.

- **H3:** Gene clusters with higher MSA depth have richer InterProScan domain annotations (more hits, more distinct IPR families). Rationale: domain recognition relies on profile databases built from characterized proteins; structurally novel proteins evade profile matching.

- **H4 ("paradox proteins"):** A non-trivial population of core gene clusters exists with low MSA depth (< 10) — universally conserved yet structurally uncharacterized. These represent the highest-priority targets for experimental structural characterization, as their conservation implies functional importance but their structural novelty means nothing is known about their mechanism.

## Data Sources

| Table | Rows | Role | Filter Strategy |
|---|---|---|---|
| `kbase_ke_pangenome.gene_cluster` | 132.5M | Core/accessory/singleton flag, protein sequence | Filter by `gtdb_species_clade_id` for species-level sampling |
| `kbase_ke_pangenome.bakta_annotations` | 132.5M | Annotation quality (hypothetical, EC, KEGG), UniRef100 bridge | Join on `gene_cluster_id` |
| `kescience_alphafold.alphafold_msa_depths` | 241M | MSA depth per UniProt accession | Lookup by stripped UniRef100 → UniProt accession |
| `kbase_ke_pangenome.interproscan_domains` | 833M | Domain annotation richness (Pfam, Gene3D, SUPERFAMILY, etc.) | Join on `gene_cluster_id`; aggregate count per cluster |

**Bridge:** `bakta_annotations.uniref100` → strip `"UniRef100_"` prefix → UniProt accession → `alphafold_msa_depths.uniprot_accession`

**Bridge coverage (confirmed):**
- 132.5M total gene clusters
- 61.5M (46.4%) have any UniRef100 ID in bakta_annotations
- 38.8M (29.3%) have a real UniProt accession (non-UPI prefix) → bridge to AlphaFold works
- 22.7M (17.1%) have UniParc-only IDs (UPI prefix) → no AlphaFold entry

## Query Strategy

### NB01 — MSA Depth × Core/Accessory/Singleton (Spark, JupyterHub)

Join `gene_cluster` × `bakta_annotations` × `alphafold_msa_depths` for all gene clusters with valid UniProt bridges. Aggregate to produce a per-cluster summary table:

```python
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()

gc = spark.table("kbase_ke_pangenome.gene_cluster").select(
    "gene_cluster_id", "gtdb_species_clade_id",
    "is_core", "is_auxiliary", "is_singleton"
)

bakta = spark.table("kbase_ke_pangenome.bakta_annotations").select(
    "gene_cluster_id", "hypothetical", "ec", "kegg_orthology_id", "uniref100"
).filter("uniref100 IS NOT NULL AND uniref100 NOT LIKE 'UniRef100_UPI%'")

from pyspark.sql.functions import regexp_replace, col
bakta = bakta.withColumn(
    "uniprot_accession",
    regexp_replace(col("uniref100"), "UniRef100_", "")
)

msa = spark.table("kescience_alphafold.alphafold_msa_depths").select(
    "uniprot_accession", "msa_depth"
)

result = (gc
    .join(bakta, on="gene_cluster_id", how="inner")
    .join(msa, on="uniprot_accession", how="inner")
)

# Aggregate: per gene_cluster_id summary
summary = result.groupBy(
    "gene_cluster_id", "gtdb_species_clade_id",
    "is_core", "is_auxiliary", "is_singleton",
    "hypothetical", "ec", "kegg_orthology_id"
).agg({"msa_depth": "first"})

summary.write.csv("s3a://cdm-lake/.../alphafold_msa_annotation/data/gc_msa_summary.csv",
                  header=True, mode="overwrite")
```

**Expected output:** ~38M rows → aggregate by core/accessory/singleton for statistics (~small final CSV).

### NB02 — Domain Annotation Richness (Spark, JupyterHub)

Count InterProScan domain hits per gene cluster; join to NB01 result:

```python
ipr = spark.table("kbase_ke_pangenome.interproscan_domains").select(
    "gene_cluster_id", "analysis", "ipr_acc"
)

domain_counts = ipr.groupBy("gene_cluster_id").agg(
    count("*").alias("n_domain_hits"),
    countDistinct("ipr_acc").alias("n_distinct_ipr")
)
```

Join domain_counts to NB01 summary by `gene_cluster_id`. Export aggregated result.

### NB03 — Statistical Analysis (local, from cached CSVs)

- Mann-Whitney U tests: MSA depth distributions across core / auxiliary / singleton
- Spearman correlation: MSA depth vs. n_domain_hits
- Fisher's exact: low-MSA-depth (< 10) enrichment in hypothetical vs. annotated
- All tests with Benjamini-Hochberg FDR correction
- Figures: violin plots, scatter plots, enrichment bars

### NB04 — Paradox Proteins (local, from cached CSVs)

- Filter: is_core = True AND msa_depth < 10
- Characterize: what are these genes? (COG category, EC, product name, species distribution)
- Rank by: conservation breadth × (1 / msa_depth) → experimental priority score
- Output: ranked candidate table for structural biology follow-up

## Performance Plan

- **Tier:** JupyterHub Spark (NB01, NB02); local Python (NB03, NB04)
- **Key risk:** 132M × 132M join on `gene_cluster_id` is large — partition by `gtdb_species_clade_id` if needed, or use broadcast join for the smaller bakta table after filtering to UniProt-only rows (~39M)
- **Caching:** Write NB01+NB02 outputs to MinIO as CSV; NB03+NB04 read from local copies
- **Known pitfalls:**
  - `interproscan_domains` has 833M rows — always aggregate in Spark before collecting
  - UniRef100 UPI-prefixed IDs do not map to AlphaFold — filter these before joining (confirmed: 22.7M rows to exclude)
  - `is_core`, `is_auxiliary`, `is_singleton` are string "True"/"False" in gene_cluster table — cast to boolean before filtering
  - Cross-database joins (kbase_ke_pangenome × kescience_alphafold) fail via REST API — use Spark only

## Expected Outcomes

| Hypothesis | If supported | If not supported |
|---|---|---|
| H1 | Core gene MSA depth > accessory > singleton (gradient) | No gradient — MSA depth is independent of conservation |
| H2 | Hypothetical proteins skewed toward low MSA depth | Annotation gap is not structurally correlated |
| H3 | MSA depth positively correlated with domain hit count | Domain annotations are insensitive to structural novelty |
| H4 | > 100K core gene clusters with msa_depth < 10 | Paradox proteins are rare or absent |

**If H1–H3 all supported:** Strong evidence that MSA depth is a structural surrogate for annotation quality, and that the core/accessory split maps onto a structural knowledge gradient.

**If H4 supported:** Produces an actionable priority list for the structural biology community — proteins that are functionally important (inferred from conservation) but structurally uncharacterized.

## Potential Confounders

- **Taxonomic sampling bias:** The 293K genomes are not phylogenetically balanced. Overrepresented taxa (e.g., Pseudomonas, E. coli) may inflate core gene counts and pull MSA depth statistics.
- **AlphaFold database coverage:** Not all proteins in the pangenome have AlphaFold entries. The 29.3% with real UniProt IDs may be a biased subset (better-characterized organisms).
- **Bakta annotation version:** bakta_annotations reflects a single annotation run; newer databases may reclassify some hypothetical genes.
- **Gene cluster representative bias:** MSA depth is looked up for the cluster representative sequence only — within-cluster sequence diversity is ignored.

## Revision History

- **v1** (2026-05-06): Initial plan. Pivoted from model-version comparison (infeasible — all entries are version 6) to MSA depth × pangenome annotation quality analysis. Bridge validation confirmed: 38.8M gene clusters have UniProt accessions linkable to AlphaFold.

## Authors

- Gazi S. Mahmud | ORCID: 0009-0006-4046-889X | Lawrence Berkeley National Laboratory
