# Research Plan: The 5,526 Costly + Dispensable Genes

## Research Question

What characterizes genes that are simultaneously burdensome (fitness improves when deleted, max_fit > 1) and not conserved (in the accessory/singleton pangenome)? Are they mobile elements, recent acquisitions, degraded pathways, or something else?

## Hypotheses

- **H1**: Costly + dispensable genes are enriched in mobile genetic element functions (transposases, phage, defense systems) relative to costly + conserved genes.
- **H2**: Costly + dispensable genes have narrower ortholog breadth (present in fewer organisms) than costly + conserved genes, consistent with recent acquisition.
- **H3**: Costly + dispensable genes are shorter, less annotated, and more likely singletons than costly + conserved genes.
- **H4**: Specific functional categories (defense, mobile elements, secondary metabolism) are overrepresented among costly + dispensable genes.

- **H0**: Costly + dispensable genes have the same functional profile, ortholog breadth, and gene properties as costly + conserved genes. The burden + dispensability combination is random with respect to gene function and evolutionary history.

## Literature Context

The concept of "costly + dispensable" genes connects to several lines of research. The Black Queen Hypothesis (Morris et al. 2012) predicts that costly functions are lost when they can be provided by community members. The Selfish Genetic Element framework predicts that mobile elements impose fitness costs on their host. Plague et al. (2017) showed that insertion sequences in *Methylobacterium* accumulate in genes under relaxed selection. Our prior work (core_gene_tradeoffs) established that 23.6% of genes with fitness data are burdensome (max_fit > 1) and that burdensome genes are paradoxically MORE likely to be core (OR=1.29), creating the selection signature matrix analyzed here.

## Query Strategy

All data is pre-cached from upstream projects. No Spark queries needed.

| Asset | Source | Rows | Key columns |
|-------|--------|------|-------------|
| `fitness_stats.tsv` | fitness_effects_conservation | ~142K | orgId, locusId, max_fit, min_fit, n_sick, n_beneficial |
| `fb_pangenome_link.tsv` | conservation_vs_fitness | 177K | orgId, locusId, is_core, is_auxiliary, is_singleton |
| `essential_genes.tsv` | conservation_vs_fitness | 153K | orgId, locusId, gene_length, desc, is_essential |
| `seed_annotations.tsv` | conservation_vs_fitness | 125K | orgId, locusId, seed_desc |
| `seed_hierarchy.tsv` | conservation_vs_fitness | 5.7K | seed_desc, toplevel, category, subsystem |
| `kegg_annotations.tsv` | conservation_vs_fitness | 73K | orgId, locusId, kgroup, kegg_desc |
| `all_ortholog_groups.csv` | essential_genome | 179K | OG_id, orgId, locusId |
| `specific_phenotypes.tsv` | fitness_effects_conservation | varies | orgId, locusId, n_specific_phenotypes |

## Analysis Plan

### NB01: Define Quadrants
Reconstruct the 2x2 selection signature matrix (costly/neutral x core/dispensable) from cached data. Verify counts match the established 28,017 / 5,526 / 86,761 / 21,886. Export `data/gene_quadrants.tsv`.

### NB02: Functional Characterization
Compare functional profiles across quadrants using SEED and KEGG annotations. Fisher exact tests with BH-FDR correction for enrichment of each functional category in costly+dispensable vs costly+conserved. Keyword search for mobile element signatures in gene descriptions.

### NB03: Evolutionary Context
Test whether costly+dispensable genes are recent acquisitions by examining ortholog breadth (number of organisms sharing the ortholog group), singleton enrichment, gene length distributions, orphan gene fraction (no ortholog group), and per-organism variation.

## Known Pitfalls

- is_core/is_auxiliary in fb_pangenome_link.tsv are strings ('True'/'False') -- use `.map({'True': True, 'False': False}).astype(bool)`
- Essential genes have no fitness data and should NOT appear in this analysis
- `fillna(False)` produces object dtype -- must `.astype(bool)` after
- The `gene` column in essential_genes.tsv has mixed types -- use `dtype={'gene': str}`
