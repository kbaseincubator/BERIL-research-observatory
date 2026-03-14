# Research Plan: Truly Dark Genes — What Remains Unknown After Modern Annotation?

## Research Question

Among bacterial genes that resist functional annotation by both the Fitness Browser's original pipeline AND bakta v1.12.0 (current UniProt/Pfam/AMR), what structural, evolutionary, and phenotypic properties distinguish them from "annotation-lag" genes, and can we prioritize a tractable subset for experimental characterization?

## Hypothesis

- **H0**: Truly dark genes are a random subset of hypothetical proteins — they differ from annotation-lag genes only in database coverage (i.e., bakta's reference databases just haven't caught up to them yet).
- **H1**: Truly dark genes are structurally and evolutionarily distinct — they are shorter, more divergent, less conserved, more taxonomically restricted, and enriched in specific organisms or conditions — representing genuinely novel biology rather than annotation lag.

### Secondary Hypotheses

- **H2**: Truly dark genes with strong fitness phenotypes (|fitness| >= 2 or essential) are enriched in stress conditions (metals, oxidative) relative to annotation-lag genes, suggesting they encode novel stress response mechanisms.
- **H3**: Truly dark genes are enriched in accessory genomes (species-specific or strain-variable), consistent with rapid evolution or recent horizontal acquisition outpacing annotation databases.
- **H4**: Despite lacking bakta product descriptions, many truly dark genes have partial clues (UniRef50 links, Pfam HMMER hits, ICA module membership) that can narrow functional hypotheses when combined.

## Literature Context

The concept of "hypothetical proteins" in bacterial genomes is well-studied. Key context:

1. **Annotation lag is the dominant source of "unknown" genes**: Modern re-annotation tools consistently reduce the fraction of hypothetical proteins. The `functional_dark_matter` NB12 showed 83.7% of FB dark genes gain bakta annotations — consistent with the field's understanding that most "hypotheticals" reflect outdated reference databases, not truly novel proteins.

2. **Truly novel proteins exist but are rare**: ORFan genes (genes with no detectable homologs) constitute 10-30% of bacterial genomes in early studies, but this fraction shrinks as databases grow. The ~6,400 truly dark genes (~2.8% of FB genes) are in the expected range for genuinely novel sequences.

3. **Fitness data provides unique leverage**: RB-TnSeq fitness data (Wetmore et al. 2015, Price et al. 2018) can identify biologically important genes regardless of annotation status. The Fitness Browser's 27M measurements across 7,552 conditions provide phenotypic anchors for genes that resist sequence-based annotation.

4. **Multiple annotation sources reduce false negatives**: bakta (Schwengers et al. 2021) and eggNOG-mapper (Cantalapiedra et al. 2021) use complementary strategies (UniProt PSC vs. orthologous group transfer). Genes that resist both represent the hardest annotation cases.

## Approach

### Phase 1: Census and Characterization (NB01-NB02)

Define the truly dark gene set and characterize its properties relative to annotation-lag genes.

**Truly dark definition**: Genes in the `bakta_dark_gene_annotations.tsv` with `bakta_reclassified = False` AND bakta `product = "hypothetical protein"`. This gives ~6,427 genes across the 39,532 linked dark genes.

**Also consider**: The 17,479 dark genes NOT linked to the pangenome (no `gene_cluster_id`). These could not be assessed by bakta because they lack pangenome cluster representatives. Their darkness status is unknown — characterize separately.

Compare truly dark vs annotation-lag genes on:
- **Sequence properties**: Gene length, GC content (from FB gene table)
- **Conservation**: Core vs accessory vs novel classification (from pangenome link)
- **Taxonomic breadth**: Ortholog group size, number of species with orthologs
- **Organism distribution**: Are truly dark genes concentrated in specific organisms?
- **Condition enrichment**: What conditions show strongest fitness effects for truly dark genes?
- **Essentiality**: Fraction essential (from `essential_genome` project)
- **Module membership**: Fraction in ICA fitness modules (from `fitness_modules` project)

### Phase 2: Sparse Annotation Mining (NB03)

Even "hypothetical" bakta annotations carry partial information:
- **UniRef50 links**: 79.2% of all bakta annotations have UniRef50. What fraction of truly dark genes have UniRef50 despite lacking a product description?
- **Pfam HMMER hits**: bakta runs Pfam on hypotheticals — do any truly dark genes have Pfam domain hits from `bakta_pfam_domains`?
- **eggNOG residual**: Do eggNOG annotations provide any signal (COG category, KEGG) for truly dark genes that bakta missed?
- **UniParc/IPS membership**: Track how many have ANY database cross-reference in `bakta_db_xrefs`

Build a "clue matrix" for each truly dark gene: which partial annotations exist, and can combinations narrow functional hypotheses?

### Phase 3: Cross-Organism Concordance (NB04)

For truly dark genes with orthologs across multiple FB organisms:
- Do orthologs show concordant fitness phenotypes (same conditions, same direction)?
- Concordant phenotypes in unrelated organisms strongly imply conserved function
- Compare concordance rates: truly dark vs annotation-lag vs annotated genes

### Phase 4: Genomic Context Analysis (NB05)

Analyze the genomic neighborhood of truly dark genes:
- Are they in operons with annotated genes? (use cofitness as a proxy for co-regulation)
- Are they near mobile elements (transposases, integrases)?
- Are they flanked by genes with known functions that suggest a pathway context?
- Use ICA module membership to identify functional context

### Phase 5: Experimental Prioritization (NB06)

Rank truly dark genes for experimental follow-up using:
1. **Fitness importance**: Strong phenotype (|fitness| >= 2) or essential
2. **Cross-organism concordance**: Conserved phenotype across species
3. **Sparse annotation clues**: UniRef50, Pfam, module context narrow the hypothesis
4. **Tractability**: Organism has good genetics, condition is reproducible
5. **Conservation**: Core genes affect more organisms

Produce a ranked list of ~50-100 top candidates with:
- Specific experimental predictions (which condition, expected phenotype)
- Functional hypotheses from sparse annotations and genomic context
- Suggested experimental approaches (growth assays, structure prediction, pulldowns)

### Phase 6: Cross-Validation with Annotation-Lag Genes (NB06 continued)

As a control, compare truly dark prioritization against the annotation-lag genes:
- Are annotation-lag genes' bakta descriptions consistent with their fitness phenotypes?
- This validates that bakta annotations are capturing real biology (not just database noise)
- Identify cases where bakta annotation contradicts fitness data — these may be mis-annotations

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_fitnessbrowser.gene` | Gene properties (length, GC, desc) | 228K | Filter to dark gene orgId/locusId pairs |
| `kescience_fitnessbrowser.fitbyexp_*` | Fitness scores per gene | Variable | Filter to truly dark genes |
| `kescience_fitnessbrowser.ortholog` | Cross-organism orthologs | ~500K | Filter to truly dark locusIds |
| `kbase_ke_pangenome.bakta_annotations` | Bakta annotations for truly dark clusters | ~6K | Filter by gene_cluster_id |
| `kbase_ke_pangenome.bakta_pfam_domains` | Pfam hits for truly dark genes | ~1K? | Filter by gene_cluster_id |
| `kbase_ke_pangenome.bakta_db_xrefs` | Database cross-references | ~10K? | Filter by gene_cluster_id |
| `kbase_ke_pangenome.gene_cluster` | Conservation status | ~6K | Filter by gene_cluster_id |

### Key Queries

1. **Retrieve gene properties for truly dark genes**:
```sql
SELECT g.orgId, g.locusId, g.scaffoldId, g.begin, g.end, g.strand,
       CAST(g.end AS INT) - CAST(g.begin AS INT) AS gene_length,
       g.GC, g.nTA
FROM kescience_fitnessbrowser.gene g
WHERE g.orgId IN ({org_list}) AND g.locusId IN ({locus_list})
```

2. **Get Pfam hits for truly dark gene clusters**:
```sql
SELECT p.gene_cluster_id, p.pfam_id, p.pfam_name, p.score, p.evalue
FROM kbase_ke_pangenome.bakta_pfam_domains p
WHERE p.gene_cluster_id IN ({cluster_list})
```

3. **Get database cross-references for truly dark gene clusters**:
```sql
SELECT d.gene_cluster_id, d.db, d.accession
FROM kbase_ke_pangenome.bakta_db_xrefs d
WHERE d.gene_cluster_id IN ({cluster_list})
```

4. **Get conservation metrics for truly dark gene clusters**:
```sql
SELECT gc.gene_cluster_id, gc.no_genomes, gc.category
FROM kbase_ke_pangenome.gene_cluster gc
WHERE gc.gene_cluster_id IN ({cluster_list})
```

### Performance Plan

- **Tier**: JupyterHub (NB01-NB02 for Spark queries), local (NB03-NB06 for analysis)
- **Estimated complexity**: Moderate — most queries filter to ~6,400 gene clusters
- **Known pitfalls**:
  - String-typed numeric columns in FB (CAST before comparison)
  - Gene clusters are species-specific (no cross-species cluster ID comparison)
  - `bakta_db_xrefs` is large (572M rows) — must filter by gene_cluster_id, not scan

## Analysis Plan

### Notebook 1: Truly Dark Census (NB01)
- **Goal**: Define the truly dark gene set, compare properties to annotation-lag genes
- **Input**: `functional_dark_matter/data/bakta_dark_gene_annotations.tsv`, `dark_gene_census_full.tsv`, `updated_darkness_tiers.tsv`
- **Analysis**: Split linked dark genes into truly-dark (6,427) vs annotation-lag (33,105). Compare length, GC, conservation, organism distribution, essentiality, module membership.
- **Expected output**: `data/truly_dark_genes.tsv`, `data/annotation_lag_genes.tsv`, comparison figures
- **Environment**: Local pandas (data files from parent project)

### Notebook 2: Spark Data Enrichment (NB02)
- **Goal**: Retrieve additional data from BERDL for truly dark genes
- **Input**: `data/truly_dark_genes.tsv` (gene_cluster_ids)
- **Analysis**: Query bakta_pfam_domains, bakta_db_xrefs, gene properties, ortholog table for truly dark genes
- **Expected output**: `data/truly_dark_pfam.tsv`, `data/truly_dark_xrefs.tsv`, `data/truly_dark_orthologs.tsv`
- **Environment**: JupyterHub Spark

### Notebook 3: Sparse Annotation Mining (NB03)
- **Goal**: Build "clue matrix" from partial annotations
- **Input**: Pfam, xref, UniRef50, eggNOG, module data for truly dark genes
- **Analysis**: For each truly dark gene, catalog all available clues. Cluster genes by clue profile. Identify genes with combinable partial annotations.
- **Expected output**: `data/truly_dark_clue_matrix.tsv`, clue coverage figures

### Notebook 4: Cross-Organism Concordance (NB04)
- **Goal**: Test if truly dark orthologs show concordant fitness phenotypes
- **Input**: Ortholog table filtered to truly dark genes, fitness data
- **Analysis**: For each ortholog pair, correlate fitness profiles across shared conditions. Compare concordance: truly dark vs annotation-lag vs annotated.
- **Expected output**: `data/concordance_results.tsv`, concordance comparison figures

### Notebook 5: Genomic Context (NB05)
- **Goal**: Analyze operonic and functional context of truly dark genes
- **Input**: Gene positions, cofitness data, module membership, bakta annotations of neighbors
- **Analysis**: Identify truly dark genes in operons with annotated genes. Use ICA module context to infer function. Flag genes near mobile elements.
- **Expected output**: `data/genomic_context.tsv`, context summary figures

### Notebook 6: Experimental Prioritization (NB06)
- **Goal**: Rank truly dark genes for experimental follow-up
- **Input**: All data from NB01-NB05
- **Analysis**: Multi-criteria scoring (fitness importance, concordance, sparse clues, tractability, conservation). Produce ranked candidate list with functional hypotheses and experimental protocols.
- **Expected output**: `data/prioritized_truly_dark_candidates.tsv`, top-50 candidate table, summary figures

## Expected Outcomes

- **If H1 supported**: Truly dark genes are a structurally distinct class — shorter, more divergent, taxonomically restricted — representing genuinely novel biology. The ~50 top candidates would be high-confidence targets for experimental characterization, potentially revealing new protein families.

- **If H0 not rejected**: Truly dark genes are similar to annotation-lag genes in all measured properties, suggesting they will eventually be annotated as databases grow. The project would still provide value by identifying the most important among them for fitness-guided experimental annotation.

- **Either way**: The project produces a tractable, prioritized list of the most important genuinely unknown genes in the Fitness Browser — a significant reduction from the original 57,011 to ~50-100 actionable candidates.

## Potential Confounders

- **Pangenome linkage bias**: 17,479 dark genes lack pangenome links and could not be assessed by bakta. These are disproportionately from organisms with poor genome assemblies and may contain additional truly dark genes.
- **Bakta annotation quality**: Some bakta "hypothetical protein" calls may be false negatives — genes that have known functions but didn't match bakta's PSC database. This would overcount truly dark genes.
- **Fitness measurement artifacts**: Some fitness effects may be polar effects or insertion artifacts rather than genuine gene function. Cross-organism concordance helps control for this.
- **Gene length bias**: Short genes are harder to annotate (fewer domains, fewer homologs) AND harder to measure fitness for (fewer TA sites for RB-TnSeq). This confound must be addressed explicitly.

## Revision History

- **v1** (2026-03-14): Initial plan, forked from functional_dark_matter NB12 insights

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory
