# Research Plan: Functional Dark Matter — Experimentally Prioritized Novel Genetic Systems

## Research Question

Across 48 bacteria with genome-wide fitness data, which genes of unknown function have strong, reproducible fitness phenotypes, and can we use cross-organism conservation, co-regulation modules, pangenome distribution, and biogeographic patterns to characterize their likely functions and prioritize them for experimental follow-up?

## Hypothesis

- **H0**: Genes annotated as "hypothetical" or "uncharacterized" with strong fitness effects are functionally random — their fitness phenotypes, conservation patterns, and environmental distributions are indistinguishable from annotated genes.
- **H1**: Functional dark matter genes form coherent groups: they cluster into co-regulated modules with annotated genes, show non-random phylogenetic distributions, and their pangenome conservation and biogeographic patterns correlate with the environmental conditions under which they show fitness effects.

### Sub-hypotheses

- **H1a (Functional coherence)**: Dark genes with strong fitness effects are enriched in ICA fitness modules alongside annotated genes, enabling guilt-by-association function prediction.
- **H1b (Conservation signal)**: Dark genes important under stress conditions are more likely to be accessory (environment-specific) than dark genes important for carbon/nitrogen metabolism (which should be more core).
- **H1c (Cross-organism conservation)**: Dark gene families with orthologs in multiple FB organisms show concordant fitness phenotypes across organisms (same condition classes cause fitness defects).
- **H1d (Biogeographic pattern)**: For accessory dark genes, genomes carrying the gene come from environments that match the lab conditions where the gene shows fitness effects (e.g., genes important under metal stress are enriched in genomes from contaminated sites).
- **H1e (Pathway integration)**: Some dark genes fill "steps_missing" gaps in otherwise-complete GapMind pathways, suggesting they encode novel enzymes for known metabolic functions.

## Literature Context

The "hypothetical protein" problem is one of microbiology's persistent gaps: ~25-40% of genes in typical bacterial genomes lack functional annotation despite decades of sequencing. The Fitness Browser (Price et al., 2018, Nature) provides genome-wide mutant fitness data for 48 bacteria under thousands of conditions — an unparalleled experimental resource for assigning function to unknown genes. Previous work has used cofitness (Bitbol & Bhatt, 2020) and ICA decomposition (Sastry et al., 2019, iModulon) to infer gene function from fitness data, but no systematic cross-organism census of "dark matter with fitness evidence" has been attempted at the scale enabled by BERDL's integrated pangenome, fitness, and environmental data.

Key references:
- Price et al. (2018) Nature 557:503–509 — Fitness Browser source data
- Wetmore et al. (2015) mBio — RB-TnSeq method
- Deutschbauer et al. (2014) — High-throughput gene function prediction
- Price et al. (2024) mSystems — Fitness Browser comprehensive update
- Bitbol & Bhatt (2020) — Cofitness for function prediction
- Sastry et al. (2019) Nature Communications — iModulons

## Approach

### Phase 1: Dark Matter Census (NB01-NB02)

**Goal**: Catalog all genes of unknown function with strong fitness phenotypes across 48 FB organisms.

1. Extract all FB genes with their descriptions and annotations
2. Classify annotation status:
   - **Hypothetical**: desc contains "hypothetical protein" or is empty
   - **DUF**: desc contains "DUF" (domain of unknown function)
   - **Uncharacterized**: desc contains "uncharacterized" or "unknown"
   - **Partial**: has domain hits (PFam/TIGRFam) but no full functional annotation
   - **Annotated**: has a clear functional description (control group)
3. For dark genes, extract fitness profiles: conditions where |fit| > 1 and |t| > 3
4. Identify "high-value dark genes": those with specific phenotypes (from `specificphenotype` table)
5. Integrate with existing data products:
   - `fb_pangenome_link.tsv` for conservation status
   - Fitness module membership (from `fitness_modules` project)
   - Essential gene families (from `essential_genome` project)

### Phase 2: Functional Inference (NB03)

**Goal**: Use co-regulation, domain structure, and pathway context to generate function hypotheses.

1. **Module guilt-by-association**: For dark genes in ICA modules, annotate the module's top functional enrichments (SEED, KEGG). If a dark gene is in a module dominated by "iron transport" genes, it's likely involved in iron transport.
2. **Co-fitness network**: For dark genes not in modules, find top co-fitness partners. What annotated genes do they correlate with?
3. **Domain-based inference**: From `genedomain` table, extract PFam/TIGRFam/CDD hits for dark genes. Partial domain annotation (e.g., "membrane protein" or "ATPase domain") constrains function even without full annotation.
4. **GapMind pathway gaps**: For species with incomplete but nearly-complete GapMind pathways, check if dark genes map to the missing steps.
5. **Cross-organism concordance**: For dark gene ortholog families, do they show the same condition-class phenotypes across organisms? Concordant phenotypes strengthen functional inference.

### Phase 3: Conservation & Phylogenetic Distribution (NB04)

**Goal**: Characterize the evolutionary context of each dark gene family.

1. **Pangenome conservation**: Via `fb_pangenome_link.tsv`, classify each dark gene as core, accessory, or singleton. Compare conservation patterns between condition classes (stress vs carbon vs nitrogen).
2. **Pangenome-wide distribution**: For dark gene families, use eggNOG orthologous groups or PFAM domains to find related clusters across all 27,690 species. How phylogenetically widespread is each family?
3. **Conservation vs fitness correlation**: Do dark genes with stronger fitness effects have higher or lower conservation? Previous projects found a U-shaped relationship: essential genes are core, but burdensome genes are also core.
4. **Ortholog family fitness profiles**: For dark gene families with orthologs in 3+ FB organisms, generate a "family fitness fingerprint" — conditions × organisms matrix of fitness effects.

### Phase 4: Biogeographic Analysis (NB05)

**Goal**: Determine whether the environmental distribution of dark gene carriers matches the lab conditions where they show fitness effects.

1. **Geographic distribution**: For each dark gene family, extract the genomes (across all pangenome species) that carry related clusters. Map their AlphaEarth embeddings, NCBI lat/lon, and isolation sources.
2. **Environmental characterization**: Cluster carrier genomes by:
   - AlphaEarth embedding space (64-dim satellite environmental features)
   - NCBI isolation source categories (harmonized from `ncbi_env`)
   - Geographic region
3. **Within-species carrier vs non-carrier test**: For accessory dark genes, compare the environmental metadata of genomes with vs without the gene within the same species. This is the strongest test because it controls for phylogeny.
4. **Lab-field concordance**: Map FB experiment groups to environmental categories:
   - Metal stress experiments → contaminated site metadata
   - Carbon source experiments → carbon-rich environment metadata
   - Osmotic/salt stress → marine/saline environments
   - Temperature stress → extreme environments
5. **NMDC independent validation**: For taxa carrying dark genes:
   - Check if they're enriched in NMDC samples with matching abiotic conditions
   - Use NMDC trait profiles to assess community-level functional context
   - Report concordance as "independently corroborated" (supplementary, not primary)

### Phase 5: Prioritization & Synthesis (NB06)

**Goal**: Produce a ranked candidate list for experimental characterization.

Scoring dimensions (each 0-1, weighted):
1. **Fitness importance** (0.25): max |fitness| across conditions, number of specific phenotypes
2. **Cross-organism conservation** (0.20): number of FB organisms with ortholog, concordance of fitness phenotypes
3. **Functional inference quality** (0.20): module membership, co-fitness with annotated genes, domain clues
4. **Pangenome distribution** (0.15): breadth across species, core vs accessory
5. **Biogeographic signal** (0.10): strength of environmental pattern, lab-field concordance
6. **Experimental tractability** (0.10): in genetically tractable organism, not essential (can knock out)

Output: Top 50-100 candidates with:
- Gene IDs across all organisms carrying orthologs
- Best functional hypothesis with evidence
- Suggested experimental approach
- Environmental context summary

## Data Sources

### Tables Required

| Table | Database | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|---|
| `gene` | fitnessbrowser | Gene descriptions, coordinates | 228K | Full scan (small) |
| `genefitness` | fitnessbrowser | Fitness scores | 27M | Filter by orgId |
| `specificphenotype` | fitnessbrowser | Strong condition-specific effects | 38K | Full scan |
| `experiment` | fitnessbrowser | Condition metadata | 7.5K | Full scan |
| `cofit` | fitnessbrowser | Co-fitness partners | 13.6M | Filter by orgId + locusId |
| `ortholog` | fitnessbrowser | Cross-organism BBH | ~1.2M | Filter by orgId |
| `genedomain` | fitnessbrowser | Domain annotations | millions | Filter by orgId |
| `seedannotation` | fitnessbrowser | SEED functional annotations | 177K | Filter by orgId |
| `organism` | fitnessbrowser | Organism metadata | 48 | Full scan |
| `gene_cluster` | pangenome | Core/accessory/singleton | 132M | Filter by species |
| `eggnog_mapper_annotations` | pangenome | Functional annotations | 93M | Filter by query_name |
| `genome` | pangenome | Genome-species mapping | 293K | Full scan |
| `gtdb_taxonomy_r214v1` | pangenome | Taxonomy hierarchy | 293K | Full scan |
| `ncbi_env` | pangenome | Environmental metadata | 4.1M | Filter by accession |
| `alphaearth_embeddings_all_years` | pangenome | Environmental embeddings | 83K | Full scan |
| `gapmind_pathways` | pangenome | Pathway predictions | 305M | Filter by genome_id |
| `taxonomy_features` | nmdc_arkin | Community taxonomy profiles | 6.4K samples | Full scan |
| `abiotic_features` | nmdc_arkin | Environmental measurements | 6.4K samples | Full scan |
| `trait_features` | nmdc_arkin | Community trait scores | 6.4K samples | Full scan |

### Existing Data Products

| Source Project | File | What It Provides |
|---|---|---|
| `conservation_vs_fitness` | `data/fb_pangenome_link.tsv` | 177,863 gene-to-cluster links (44 organisms) |
| `conservation_vs_fitness` | `data/organism_mapping.tsv` | FB orgId → GTDB species clade mapping |
| `fitness_modules` | module membership files | 1,116 ICA modules across 32 organisms |
| `essential_genome` | ortholog families | 17,222 ortholog groups, essentiality classification |

## Query Strategy

### Performance Plan
- **Tier**: Direct Spark on BERDL JupyterHub (required for large joins)
- **Estimated complexity**: Moderate-High (multi-table joins across FB + pangenome)
- **Known pitfalls**:
  - FB values are all strings — CAST before numeric comparisons
  - Gene cluster IDs are species-specific — cannot compare across species
  - AlphaEarth covers only 28% of genomes
  - `ncbi_env` is EAV format — pivot before use
  - Large IN clauses with species IDs containing `--` — use temp views

### Key Queries

1. **Dark gene census** (NB01): Join `gene` + `genefitness` + `specificphenotype` + `genedomain` per organism
2. **Module integration** (NB02): Load fitness_modules outputs, match to dark gene list
3. **Pangenome conservation** (NB04): Join dark genes via `fb_pangenome_link` → `gene_cluster` → species distribution
4. **Biogeographic extraction** (NB05): For carrier species, join `genome` → `alphaearth_embeddings` + `ncbi_env`
5. **NMDC validation** (NB05): Match carrier taxa to NMDC `taxonomy_features` + `abiotic_features`

## Analysis Plan

### Notebook 1: Dark Matter Census
- **Goal**: Catalog all dark genes with fitness evidence
- **Expected output**: `data/dark_gene_census.tsv` — ~54K dark genes with annotation status, fitness summary, conservation class, essentiality, module membership
- **Key figures**: Annotation status breakdown, fitness effect distributions, organism-level dark fraction

### Notebook 2: Data Integration
- **Goal**: Merge FB data with pangenome links, modules, and essential gene data
- **Expected output**: `data/dark_genes_integrated.tsv` — enriched dark gene table with all cross-references
- **Key figures**: Coverage Venn diagram (linked × in-module × essential × has-ortholog)

### Notebook 3: Functional Inference
- **Goal**: Generate function hypotheses for dark genes via modules, co-fitness, domains, and pathway gaps
- **Expected output**: `data/function_predictions.tsv` — predicted functions with evidence type and confidence
- **Key figures**: Evidence source breakdown, prediction confidence distribution

### Notebook 4: Conservation & Phylogenetic Distribution
- **Goal**: Map dark gene families across the pangenome tree of life
- **Expected output**: `data/dark_gene_phylodist.tsv` — phylogenetic breadth per family
- **Key figures**: Phylogenetic heatmap, conservation vs fitness scatter, condition-class × conservation patterns

### Notebook 5: Biogeographic Analysis
- **Goal**: Environmental distribution of dark gene carriers and lab-field concordance
- **Expected output**: `data/biogeographic_profiles.tsv` — environmental metadata per dark gene family
- **Key figures**: AlphaEarth embedding PCA by carrier status, geographic maps, lab-field concordance matrix, NMDC validation plots

### Notebook 6: Prioritization & Synthesis
- **Goal**: Score and rank candidates for experimental characterization
- **Expected output**: `data/prioritized_candidates.tsv` — top 100 ranked candidates with full evidence dossiers
- **Key figures**: Score component breakdown, top-20 candidate summary cards

## Expected Outcomes

- **If H1 supported**: A ranked catalog of experimentally validated but functionally unknown gene families, each with functional hypotheses, conservation context, and environmental distribution — directly actionable for targeted characterization experiments.
- **If H0 not rejected**: Dark matter genes are truly random — their fitness phenotypes don't correlate with conservation, co-regulation, or environment. This would suggest these genes serve organism-specific, condition-specific roles with no generalizable biology. Even this is informative: it would mean gene function prediction requires organism-specific experimental approaches rather than comparative inference.
- **Potential confounders**:
  - Annotation bias: some "hypothetical" genes may have annotations in other databases not checked
  - Fitness noise: weak fitness effects may not replicate across experiments
  - Environmental metadata sparsity: AlphaEarth covers only 28%, NCBI env metadata is inconsistent
  - Taxonomy bridge limitations for NMDC validation (genus-level, not species)

## Integrity Safeguards

1. **Coverage reporting**: Every claim states N with data / N total
2. **Within-species comparisons** for biogeographic tests (controls for phylogeny)
3. **Multiple testing correction**: BH-FDR for all genome-wide tests
4. **Pre-registered condition-environment mapping** before looking at biogeographic data
5. **Null results reported honestly**: no environmental pattern is as informative as a positive pattern
6. **Independent validation**: NMDC data serves as held-out confirmation, not discovery

## Revision History
- **v1** (2025-02-25): Initial plan

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory
