# Research Plan: Truly Dark Genes — What Remains Unknown After Modern Annotation?

## Research Question

Among bacterial genes that resist functional annotation by both the Fitness Browser's original pipeline AND bakta v1.12.0 (current UniProt/Pfam/AMR), what structural, evolutionary, and phenotypic properties distinguish them from "annotation-lag" genes, and can we prioritize a tractable subset for experimental characterization?

## Hypothesis

- **H0**: Truly dark genes are a random subset of hypothetical proteins — they differ from annotation-lag genes only in database coverage (i.e., bakta's reference databases just haven't caught up to them yet).
- **H1**: Truly dark genes are structurally and evolutionarily distinct — they are shorter, more divergent, less conserved, more taxonomically restricted, and enriched in specific organisms or conditions — representing genuinely novel biology rather than annotation lag.

### Secondary Hypotheses

- **H2**: Truly dark genes with strong fitness phenotypes (|fitness| >= 2 or essential) are enriched in stress conditions (metals, oxidative) relative to annotation-lag genes with equivalent fitness effects, suggesting they encode novel stress response mechanisms. Enrichment baseline: condition-class distribution of annotation-lag genes with |fitness| >= 2.
- **H3**: Truly dark genes are enriched in accessory genomes (species-specific or strain-variable), consistent with rapid evolution or recent horizontal acquisition outpacing annotation databases. Test HGT specifically via GC content deviation from host genome mean and proximity to mobile genetic elements (transposases, integrases).
- **H4**: Despite lacking bakta product descriptions, many truly dark genes have partial clues (UniRef50 links, Pfam HMMER hits, ICA module membership) that can narrow functional hypotheses when combined.

## Literature Context

The concept of "hypothetical proteins" in bacterial genomes is well-studied. Key context:

1. **Annotation lag is the dominant source of "unknown" genes**: Modern re-annotation tools consistently reduce the fraction of hypothetical proteins. The `functional_dark_matter` NB12 showed 83.7% of FB dark genes gain bakta annotations — consistent with the field's understanding that most "hypotheticals" reflect outdated reference databases, not truly novel proteins.

2. **Truly novel proteins exist but are rare**: ORFan genes (genes with no detectable homologs) constitute 10-30% of bacterial genomes in early studies, but this fraction shrinks as databases grow. The ~6,400 truly dark genes (~2.8% of FB genes) are in the expected range for genuinely novel sequences.

3. **Fitness data provides unique leverage**: RB-TnSeq fitness data (Wetmore et al. 2015, Price et al. 2018) can identify biologically important genes regardless of annotation status. The Fitness Browser's 27M measurements across 7,552 conditions provide phenotypic anchors for genes that resist sequence-based annotation.

4. **Multiple annotation sources reduce false negatives**: bakta (Schwengers et al. 2021) and eggNOG-mapper (Cantalapiedra et al. 2021) use complementary strategies (UniProt PSC vs. orthologous group transfer). Genes that resist both represent the hardest annotation cases.

5. **Structure prediction as a frontier**: AlphaFold2 and ESMFold can now predict structures for proteins with no detectable sequence homologs, enabling remote homology detection via Foldseek. This is a natural next step for truly dark genes but is out of scope for this project (flagged for future work).

## Approach

### Data Reuse Strategy

This project builds directly on `functional_dark_matter` outputs. To avoid re-derivation:
- **Census and bakta status**: Load from `functional_dark_matter/data/bakta_dark_gene_annotations.tsv` and `updated_darkness_tiers.tsv` (NB12 outputs)
- **Concordance**: Filter existing `functional_dark_matter/data/concordance_scores.tsv` and `concordance_detailed.tsv` (NB02 outputs) to truly-dark subset
- **Condition enrichment and essentiality**: Filter existing census data; do not re-query FB
- **New Spark queries (NB02)**: Only for data NOT captured by parent project — specifically bakta_pfam_domains, bakta_db_xrefs, and eggnog_mapper_annotations for the truly dark gene clusters

### Phase 1: Census and Characterization (NB01)

Define the truly dark gene set and characterize its properties relative to annotation-lag genes.

**Truly dark definition**: Genes in `bakta_dark_gene_annotations.tsv` with `bakta_reclassified = False` AND bakta `product = "hypothetical protein"`. This gives ~6,427 genes across the 39,532 linked dark genes.

**Sub-stratification**: Among truly dark genes, distinguish:
- Truly dark with DUF-only Pfam hits (structural class known, function unknown)
- Truly dark with non-DUF Pfam hits (some functional signal)
- Truly dark with no Pfam hits at all (deepest darkness)

**Short ORF filtering**: Flag genes < 150 bp as potential spurious gene calls. Report count and exclude from statistical comparisons (or analyze separately).

**Unlinked dark genes**: The 17,479 dark genes NOT linked to the pangenome cannot be assessed by bakta. NB01 will report their organism distribution, fitness phenotype summary, and gene length distribution. NB06 will discuss what fraction of truly dark biology they might represent.

Compare truly dark vs annotation-lag genes on:
- **Sequence properties**: Gene length (using `ABS(CAST(end AS INT) - CAST(begin AS INT))`), GC content
- **Conservation**: Core vs accessory vs novel classification (from pangenome link)
- **Taxonomic breadth**: Ortholog group size, number of species with orthologs
- **Organism distribution**: Are truly dark genes concentrated in specific organisms?
- **Condition enrichment**: What conditions show strongest fitness effects? (baseline: annotation-lag condition distribution)
- **Essentiality**: Fraction essential (from `essential_genome` project)
- **Module membership**: Fraction in ICA fitness modules (from `fitness_modules` project)
- **GC deviation**: Difference from host genome mean GC (HGT indicator for H3)

**Statistical framework**: Mann-Whitney U tests for continuous variables (length, GC, GC deviation), Fisher's exact or chi-squared for categorical (conservation class, essentiality, module membership). Benjamini-Hochberg FDR correction across all comparisons. Report both p-values and effect sizes (Cohen's d for continuous, odds ratios for categorical). Pre-registered minimum meaningful effect size: Cohen's d >= 0.2 or OR >= 1.5.

### Phase 2: Spark Data Enrichment (NB02)

Query BERDL for data not already captured by the parent project:
- **Pfam HMMER hits** from `bakta_pfam_domains` for truly dark gene clusters (~6,400 clusters → estimated ~500-1,000 Pfam hits, since bakta only runs HMMER on hypotheticals)
- **Database cross-references** from `bakta_db_xrefs` (~28K rows expected at ~4.3 xrefs/cluster)
- **eggNOG annotations** from `eggnog_mapper_annotations` (join on `query_name` = gene_cluster_id) for any residual COG/KEGG signal
- **Gene properties** (length, GC, scaffold position) from FB `gene` table for truly dark + annotation-lag genes

**Query approach**: Create Spark temp views with gene_cluster_id lists and JOIN (not IN clauses — 6,400 IDs is too many for IN). Use `SET spark.sql.autoBroadcastJoinThreshold = -1` if joining against large tables.

### Phase 3: Sparse Annotation Mining (NB03)

Build a "clue matrix" for each truly dark gene: which partial annotations exist?
- **UniRef50 links**: Present despite "hypothetical" product?
- **Pfam HMMER hits**: DUF domains vs non-DUF domains
- **eggNOG residual**: COG category, KEGG, description from eggNOG where bakta has nothing
- **Database cross-references**: SO terms, UniRef, any external DB links
- **ICA module membership**: Module function provides guilt-by-association context

Cluster genes by clue profile. Validate that clue combinations are informative by testing whether genes with more clues have higher cross-organism concordance rates.

### Phase 4: Cross-Organism Concordance (NB04)

**Reuse existing data**: Filter `functional_dark_matter/data/concordance_scores.tsv` to the truly dark subset rather than re-computing concordance from scratch.

**Coverage note**: Ortholog data covers only 32 of 48 FB organisms (BBH computed for ICA organisms only). Truly dark genes from the remaining 16 organisms will lack concordance data — report this gap.

Compare concordance rates: truly dark vs annotation-lag vs annotated genes. Use the parent project's condition-class overlap rates as the null model for expected concordance by chance.

**Cofitness threshold for operon proxy**: |r| >= 0.3 (consistent with `fitness_modules` project).

### Phase 5: Genomic Context Analysis (NB05)

Analyze the genomic neighborhood of truly dark genes:
- Operon membership via cofitness (|r| >= 0.3 with adjacent genes)
- Proximity to mobile elements (transposases, integrases — check bakta annotations of flanking genes)
- ICA module context: what annotated genes share the module?
- GC content deviation from host genome as HGT indicator (for H3)

### Phase 6: Experimental Prioritization (NB06)

Rank truly dark genes for experimental follow-up using:
1. **Fitness importance**: Strong phenotype (|fitness| >= 2) or essential
2. **Cross-organism concordance**: Conserved phenotype across species
3. **Sparse annotation clues**: UniRef50, Pfam, module context narrow the hypothesis
4. **Tractability**: Organism has good genetics, condition is reproducible
5. **Conservation**: Core genes affect more organisms

Produce a ranked list of ~50-100 top candidates with:
- Specific experimental predictions (which condition, expected phenotype)
- Functional hypotheses from sparse annotations and genomic context
- Suggested experimental approaches (growth assays, structure prediction via AlphaFold/ESMFold, pulldowns)

**Cross-validation**: Check annotation-lag genes' bakta descriptions against their fitness phenotypes. Identify cases where bakta annotation contradicts fitness data (potential mis-annotations).

**Unlinked dark genes**: Discuss the 17,479 unlinked genes — what fraction might be truly dark, and how does their exclusion affect the candidate list?

**Future work**: Flag top candidates for AlphaFold2/ESMFold structure prediction and Foldseek remote homology search as a natural follow-up project.

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_fitnessbrowser.gene` | Gene properties (length, GC) | 228K | Filter to dark gene orgId/locusId pairs |
| `kescience_fitnessbrowser.ortholog` | Cross-organism orthologs | ~1.15M (32 orgs) | Filter to truly dark locusIds |
| `kbase_ke_pangenome.bakta_annotations` | Bakta annotations for truly dark clusters | ~6K | Filter by gene_cluster_id |
| `kbase_ke_pangenome.bakta_pfam_domains` | Pfam hits for truly dark genes | ~500-1K | Filter by gene_cluster_id via temp view JOIN |
| `kbase_ke_pangenome.bakta_db_xrefs` | Database cross-references | ~28K | Filter by gene_cluster_id via temp view JOIN |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | eggNOG residual annotations | ~6K | JOIN on query_name = gene_cluster_id |
| `kbase_ke_pangenome.gene_cluster` | Conservation status | ~6K | Filter by gene_cluster_id |

### Key Queries

1. **Retrieve gene properties for truly dark genes**:
```sql
SELECT g.orgId, g.locusId, g.scaffoldId, g.begin, g.end, g.strand,
       ABS(CAST(g.end AS INT) - CAST(g.begin AS INT)) AS gene_length,
       g.GC
FROM kescience_fitnessbrowser.gene g
WHERE g.orgId IN ({org_list}) AND g.locusId IN ({locus_list})
```

2. **Get Pfam hits for truly dark gene clusters** (temp view JOIN):
```sql
CREATE OR REPLACE TEMP VIEW truly_dark_ids AS
SELECT gene_cluster_id FROM truly_dark_clusters;

SELECT p.gene_cluster_id, p.pfam_id, p.pfam_name, p.score, p.evalue
FROM kbase_ke_pangenome.bakta_pfam_domains p
JOIN truly_dark_ids t ON p.gene_cluster_id = t.gene_cluster_id
```

3. **Get database cross-references** (temp view JOIN, large table):
```sql
SELECT d.gene_cluster_id, d.db, d.accession
FROM kbase_ke_pangenome.bakta_db_xrefs d
JOIN truly_dark_ids t ON d.gene_cluster_id = t.gene_cluster_id
```

4. **Get eggNOG residual annotations**:
```sql
SELECT e.query_name AS gene_cluster_id, e.seed_ortholog, e.cog_category,
       e.kegg_ko, e.kegg_pathway, e.description
FROM kbase_ke_pangenome.eggnog_mapper_annotations e
JOIN truly_dark_ids t ON e.query_name = t.gene_cluster_id
```

### Performance Plan

- **Tier**: JupyterHub (NB02 for Spark queries), local (NB01, NB03-NB06 for analysis)
- **Estimated complexity**: Moderate — most queries filter to ~6,400 gene clusters
- **Known pitfalls**:
  - String-typed numeric columns in FB (CAST before comparison)
  - Gene clusters are species-specific (no cross-species cluster ID comparison)
  - `bakta_db_xrefs` is large (572M rows) — use temp view JOIN, not IN clause
  - `eggnog_mapper_annotations` uses `query_name` as the cluster ID column, not `gene_cluster_id`
  - Disable auto-broadcast for large table joins: `SET spark.sql.autoBroadcastJoinThreshold = -1`

## Analysis Plan

### Notebook 1: Truly Dark Census (NB01)
- **Goal**: Define the truly dark gene set, compare properties to annotation-lag genes
- **Input**: `functional_dark_matter/data/bakta_dark_gene_annotations.tsv`, `dark_gene_census_full.tsv`, `updated_darkness_tiers.tsv`
- **Analysis**: Split linked dark genes into truly-dark (6,427) vs annotation-lag (33,105). Sub-stratify by Pfam status (no Pfam / DUF-only / non-DUF). Flag short ORFs (< 150 bp). Compare length, GC, conservation, organism distribution, essentiality, module membership. Report unlinked dark genes (17,479) separately.
- **Statistics**: Mann-Whitney U (continuous), Fisher's exact (categorical), BH-FDR correction, effect sizes (Cohen's d, OR)
- **Expected output**: `data/truly_dark_genes.tsv`, `data/annotation_lag_genes.tsv`, `data/unlinked_dark_genes.tsv`, comparison figures
- **Environment**: Local pandas (data files from parent project)

### Notebook 2: Spark Data Enrichment (NB02)
- **Goal**: Retrieve Pfam, db_xrefs, eggNOG, and gene properties from BERDL for truly dark genes
- **Input**: `data/truly_dark_genes.tsv` (gene_cluster_ids)
- **Analysis**: Spark temp view JOINs against bakta_pfam_domains, bakta_db_xrefs, eggnog_mapper_annotations, FB gene table
- **Expected output**: `data/truly_dark_pfam.tsv`, `data/truly_dark_xrefs.tsv`, `data/truly_dark_eggnog.tsv`, `data/gene_properties.tsv`
- **Environment**: JupyterHub Spark

### Notebook 3: Sparse Annotation Mining (NB03)
- **Goal**: Build "clue matrix" from partial annotations
- **Input**: Pfam, xref, UniRef50, eggNOG, module data for truly dark genes
- **Analysis**: For each truly dark gene, catalog all available clues. Cluster genes by clue profile. Validate: do genes with more clues show higher concordance?
- **Expected output**: `data/truly_dark_clue_matrix.tsv`, clue coverage figures

### Notebook 4: Cross-Organism Concordance (NB04)
- **Goal**: Test if truly dark orthologs show concordant fitness phenotypes
- **Input**: `functional_dark_matter/data/concordance_scores.tsv` filtered to truly dark genes
- **Analysis**: Filter existing concordance to truly dark subset (32 organisms only). Compare concordance rates: truly dark vs annotation-lag vs annotated. Null model: condition-class overlap rates.
- **Expected output**: `data/concordance_truly_dark.tsv`, concordance comparison figures

### Notebook 5: Genomic Context (NB05)
- **Goal**: Analyze operonic and functional context of truly dark genes
- **Input**: Gene positions, cofitness data (|r| >= 0.3 threshold), module membership, bakta annotations of neighbors
- **Analysis**: Identify operon membership, mobile element proximity (transposases/integrases in flanking genes), ICA module context. GC deviation analysis for HGT signal.
- **Expected output**: `data/genomic_context.tsv`, context summary figures

### Notebook 6: Experimental Prioritization (NB06)
- **Goal**: Rank truly dark genes for experimental follow-up
- **Input**: All data from NB01-NB05
- **Analysis**: Multi-criteria scoring (fitness, concordance, clues, tractability, conservation). Cross-validate against annotation-lag genes. Discuss unlinked dark gene gap.
- **Expected output**: `data/prioritized_truly_dark_candidates.tsv`, top-50 candidate table, summary figures

## Expected Outcomes

- **If H1 supported**: Truly dark genes are a structurally distinct class — shorter, more divergent, taxonomically restricted — representing genuinely novel biology. The ~50 top candidates would be high-confidence targets for experimental characterization, potentially revealing new protein families.

- **If H0 not rejected**: Truly dark genes are similar to annotation-lag genes in all measured properties, suggesting they will eventually be annotated as databases grow. The project would still provide value by identifying the most important among them for fitness-guided experimental annotation.

- **Either way**: The project produces a tractable, prioritized list of the most important genuinely unknown genes in the Fitness Browser — a significant reduction from the original 57,011 to ~50-100 actionable candidates.

## Potential Confounders

- **Pangenome linkage bias**: 17,479 dark genes lack pangenome links and could not be assessed by bakta. These are disproportionately from organisms with poor genome assemblies and may contain additional truly dark genes.
- **Bakta annotation quality**: Some bakta "hypothetical protein" calls may be false negatives — genes that have known functions but didn't match bakta's PSC database. This would overcount truly dark genes.
- **Fitness measurement artifacts**: Some fitness effects may be polar effects or insertion artifacts rather than genuine gene function. Cross-organism concordance helps control for this.
- **Gene length bias**: Short genes are harder to annotate (fewer domains, fewer homologs) AND harder to measure fitness for (fewer TA sites for RB-TnSeq). Mitigation: stratify comparisons by gene length bins, flag short ORFs (< 150 bp), and report effect sizes within length-matched subsets.
- **Ortholog coverage**: BBH orthologs are only available for 32 of 48 FB organisms. Truly dark genes from the remaining 16 organisms will lack concordance data.

## Revision History

- **v1** (2026-03-14): Initial plan, forked from functional_dark_matter NB12 insights
- **v2** (2026-03-14): Addressed plan review: added data reuse strategy, statistical framework (BH-FDR, effect sizes), short ORF filtering, DUF sub-stratification, GC deviation for HGT, eggNOG table, temp view JOIN strategy, 32-organism ortholog coverage gap, structure prediction as future work

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory
