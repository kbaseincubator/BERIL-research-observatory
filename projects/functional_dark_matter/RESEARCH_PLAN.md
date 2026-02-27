# Research Plan: Functional Dark Matter — Experimentally Prioritized Novel Genetic Systems

## Research Question

Across 48 bacteria with genome-wide fitness data, which genes of unknown function have strong, reproducible fitness phenotypes, and can we use biogeographic patterns, pathway gap analysis, and cross-organism fitness concordance — building on existing function predictions, conservation analyses, and ICA modules — to further characterize their likely functions and prioritize them for experimental follow-up?

## Relationship to Prior Work

This project explicitly builds on four completed observatory projects rather than re-deriving their results:

| Prior Project | What It Produced | How This Project Uses It |
|---|---|---|
| `fitness_modules` | 1,116 ICA modules across 32 organisms; **6,691 function predictions** for hypothetical proteins | Loaded directly — module membership and predictions are input, not re-derived |
| `essential_genome` | 17,222 ortholog families; 859 universally essential families; **1,382 function predictions** for hypothetical essentials; 7,084 orphan essential genes (58.7% hypothetical) | Essential genes are a separate dark matter class; existing predictions loaded |
| `conservation_vs_fitness` | 177,863 gene-to-cluster links (44 organisms, 94.2% median coverage); conservation classification | FB-pangenome link table is the backbone for pangenome queries |
| `module_conservation` | Module genes are 86% core; 48 accessory modules identified | Conservation patterns are input context |

**What this project adds that is genuinely new:**
1. **Unified dark gene catalog** integrating all prior data products into one table
2. **GapMind pathway gap-filling** — do dark genes fill missing steps in nearly-complete metabolic pathways?
3. **Cross-organism fitness concordance** — do orthologs of the same dark gene show concordant phenotypes across organisms?
4. **Pangenome-wide phylogenetic distribution** — how widespread is each dark gene family across all 27,690 species (beyond the 48 FB organisms)?
5. **Biogeographic analysis** — within-species carrier vs non-carrier environmental comparisons using AlphaEarth and NCBI metadata
6. **Lab-field concordance** — do genes important under metal stress in the lab appear in genomes from contaminated sites?
7. **NMDC independent environmental validation** — supplementary community-level corroboration
8. **Integrated experimental prioritization** — ranked candidate list combining all evidence layers

## Hypothesis

- **H0**: Genes annotated as "hypothetical" or "uncharacterized" with strong fitness effects are functionally random — their fitness phenotypes, conservation patterns, and environmental distributions are indistinguishable from annotated genes.
- **H1**: Functional dark matter genes form coherent groups: they cluster into co-regulated modules with annotated genes, show non-random phylogenetic distributions, and their pangenome conservation and biogeographic patterns correlate with the environmental conditions under which they show fitness effects.

### Sub-hypotheses

- **H1a (Functional coherence)**: Dark genes with strong fitness effects are enriched in ICA fitness modules alongside annotated genes, enabling guilt-by-association function prediction. *(Partially addressed by `fitness_modules` — this project quantifies coverage and tests on the full dark gene set.)*
- **H1b (Conservation signal)**: Dark genes important under stress conditions are more likely to be accessory (environment-specific) than dark genes important for carbon/nitrogen metabolism (which should be more core).
- **H1c (Cross-organism concordance)**: Dark gene families with orthologs in multiple FB organisms show concordant fitness phenotypes across organisms (same condition classes cause fitness defects). The pre-computed `specog` table provides per-OG condition-level fitness summaries.
- **H1d (Biogeographic pattern)**: For accessory dark genes, genomes carrying the gene come from environments that match the lab conditions where the gene shows fitness effects (e.g., genes important under metal stress are enriched in genomes from contaminated sites).
- **H1e (Pathway integration)**: Some dark genes fill "steps_missing" gaps in otherwise-complete GapMind pathways, suggesting they encode novel enzymes for known metabolic functions. GapMind `score_category` uses a four-level hierarchy: `likely_complete` > `steps_missing_low` > `steps_missing_medium` > `not_present`; multiple rows per genome-pathway pair must be aggregated (MAX score) before interpreting gaps.

## Literature Context

The "hypothetical protein" problem is one of microbiology's persistent gaps: ~25-40% of genes in typical bacterial genomes lack functional annotation despite decades of sequencing. The Fitness Browser (Price et al., 2018, Nature) provides genome-wide mutant fitness data for 48 bacteria under thousands of conditions — an unparalleled experimental resource for assigning function to unknown genes.

Previous work in this observatory used ICA decomposition to build fitness modules and predict function for 6,691 hypothetical proteins (`fitness_modules`), identified 859 universally essential gene families with 1,382 predictions for hypothetical essentials (`essential_genome`), and established gene-level links between Fitness Browser organisms and the BERDL pangenome (`conservation_vs_fitness`). What has NOT been attempted is: (a) a unified analysis combining all these evidence layers, (b) biogeographic analysis of dark gene carriers using environmental metadata, or (c) an experimentally actionable prioritization of candidates for characterization.

Key references:
- Price et al. (2018) Nature 557:503–509 — Fitness Browser source data
- Wetmore et al. (2015) mBio — RB-TnSeq method
- Deutschbauer et al. (2014) — High-throughput gene function prediction
- Price et al. (2024) mSystems — Fitness Browser comprehensive update
- Bitbol & Bhatt (2020) — Cofitness for function prediction
- Sastry et al. (2019) Nature Communications — iModulons

## Approach

### Phase 1: Integration & Census (NB01)

**Goal**: Build a unified dark gene table by loading and merging all existing data products, then characterizing the full dark gene landscape.

**What is loaded (not re-derived):**
1. All FB genes (`gene` table, 228K) — classify annotation status:
   - **Hypothetical**: desc contains "hypothetical protein" or is empty/null
   - **DUF**: desc contains "DUF" (domain of unknown function)
   - **Uncharacterized**: desc contains "uncharacterized" or "unknown"
   - **Partial**: has domain hits (PFam/TIGRFam in `genedomain`) but no full functional annotation
   - **Annotated**: clear functional description (control group)
2. **Essential gene classification** from `essential_genome`: load orphan essentials (7,084 genes, 58.7% hypothetical) as a separate dark matter class. These have zero rows in `genefitness` (no viable mutants) and would be missed by fitness-effect filters alone.
3. **Fitness phenotype summary** per dark gene: from `specificphenotype` (38K entries) and `genefitness` (conditions where |fit| > 1 and |t| > 3, with CAST to float)
4. **Condition-class characterization**: join `genefitness` → `experiment` to tag each fitness effect with its experiment group (stress, carbon source, nitrogen source, etc.) — this is the foundation for lab-field concordance in NB04
5. **Pangenome conservation** from `fb_pangenome_link.tsv` (177,863 links): core/accessory/singleton status per gene
6. **Module membership** from `fitness_modules` project: which ICA module each gene belongs to, and the module's existing function prediction (6,691 predictions)
7. **Ortholog families** from `essential_genome` project: 17,222 ortholog groups, essentiality classification
8. **Co-fitness top partners** from `cofit` table: for dark genes NOT in any ICA module, load top 5 co-fitness partners with their annotations — provides functional context for the ~40% of dark genes outside modules
9. **Domain annotations** from `genedomain`: PFam, TIGRFam, CDD hits that provide partial structural clues even for "hypothetical" genes

**Output**: `data/dark_genes_integrated.tsv` — unified table (~54K dark genes, ~3,700 with strong fitness effects, plus ~4,100 hypothetical essentials) with all cross-references.

### Phase 2: New Inference Layers (NB02)

**Goal**: Apply inference methods not covered by prior projects.

1. **GapMind pathway gap-filling**:
   - For the ~44 FB-linked species, query `gapmind_pathways` filtered by those species' genome IDs (not a full 305M-row scan)
   - Aggregate multiple rows per genome-pathway pair using MAX score (per the `score_category` hierarchy: `likely_complete` > `steps_missing_low` > `steps_missing_medium` > `not_present`)
   - Use two-stage aggregation: genome-pathway → species-pathway
   - Identify pathways scored as `steps_missing_low` (nearly complete) and check if dark genes from those species could fill the missing enzymatic steps
   - Match via EC numbers, KEGG reactions, or PFAM domains between dark gene annotations and missing pathway steps

2. **Cross-organism fitness concordance**:
   - For dark gene ortholog families (from `essential_genome` ortholog groups) present in 3+ FB organisms, build a "family fitness fingerprint": condition-class × organism matrix of fitness effects
   - Use the pre-computed `specog` table (specific phenotypes by ortholog group) which already has `minFit`/`maxFit`/`minT`/`maxT` per OG × condition — avoids re-querying 27M genefitness rows
   - Test concordance: do orthologs of the same dark gene show fitness effects under the same condition classes?
   - Concordant families get higher confidence for functional inference

3. **Pangenome-wide phylogenetic distribution**:
   - For dark gene families, extract eggNOG OG identifiers from `eggnog_mapper_annotations` (via `fb_pangenome_link` → `gene_cluster_id` → `query_name`)
   - Create a temp view of target OG IDs and JOIN against `eggnog_mapper_annotations` to find all clusters across 27,690 species sharing the same OG
   - Map to taxonomy via `gene_cluster.gtdb_species_clade_id` → `gtdb_species_clade` → `gtdb_taxonomy_r214v1`
   - Compute phylogenetic breadth: number of phyla, orders, families, species carrying each dark gene family
   - Classify as: clade-restricted (one phylum) vs widespread (3+ phyla)

**Output**: `data/gapmind_gap_candidates.tsv`, `data/concordance_scores.tsv`, `data/phylogenetic_breadth.tsv`

### Phase 3: Biogeographic Analysis (NB03)

**Goal**: Determine whether the environmental distribution of dark gene carriers shows non-random patterns, and whether those patterns match lab fitness conditions.

1. **Geographic distribution of carriers**:
   - For each dark gene family (from NB02 phylogenetic distribution), identify all pangenome species carrying related clusters
   - For genomes in those species, extract:
     - AlphaEarth embeddings (83K genomes, 28% coverage — safe to collect via `.toPandas()`)
     - NCBI isolation source categories from `ncbi_env` (EAV format — pivot by `harmonized_name` for key attributes)
     - Geographic coordinates from `gtdb_metadata.ncbi_lat_lon`

2. **Within-species carrier vs non-carrier test** (strongest test — controls for phylogeny):
   - For accessory dark genes, within each species that has the gene in some but not all genomes:
     - Compare AlphaEarth embedding distributions between carriers and non-carriers
     - Compare NCBI isolation source category frequencies
     - Use permutation tests or Mann-Whitney U for significance
   - Report N genomes with metadata / N total for every comparison

3. **Environmental characterization summary**:
   - Cluster carrier genomes by AlphaEarth embedding space (UMAP + HDBSCAN)
   - Summarize NCBI isolation source categories per dark gene family
   - Flag dark gene families with strong environmental signals

**Output**: `data/biogeographic_profiles.tsv`, `data/carrier_noncarrier_tests.tsv`

### Phase 4: Lab-Field Concordance & NMDC Validation (NB04)

**Goal**: Test whether dark genes' lab fitness conditions match the environmental contexts where they appear in nature.

1. **Pre-registered condition-environment mapping** (define BEFORE looking at biogeographic data):

   | FB Experiment Group | Environmental Category | NCBI/AlphaEarth Signal |
   |---|---|---|
   | Metal stress (Cr, Ni, Zn, U, Cu) | Contaminated sites | ncbi_env "contaminated", lat/lon near industrial sites |
   | Carbon source utilization | Carbon-rich environments | ncbi_env "soil", "sediment", DOC-rich |
   | Nitrogen source | Nitrogen-variable environments | ncbi_env "agricultural", nitrogen-related |
   | Osmotic/salt stress | Marine/saline | ncbi_env "marine", "saline", "brackish" |
   | Temperature stress | Extreme thermal | ncbi_env "hot spring", "permafrost" |
   | pH stress | pH-extreme environments | ncbi_env "acidic", "alkaline" |
   | Oxidative stress | Oxic/anoxic transitions | ncbi_env "sediment", redox gradients |

2. **Concordance test**: For each dark gene family with both (a) condition-specific fitness effects and (b) environmental metadata for carriers:
   - Is the carrier environmental profile enriched for the predicted environment category?
   - Fisher's exact test per family, BH-FDR correction across all families

3. **NMDC independent validation** (supplementary — community-level, not gene-level):
   - For taxa carrying dark genes, check abundance in NMDC `taxonomy_features` (6,365 samples, 3,493 taxa — CLR-transformed wide matrix; resolve taxon IDs via `taxonomy_dim`/`taxstring_lookup`)
   - Correlate with NMDC `abiotic_features` (22 environmental measurements per sample)
   - Use NMDC `trait_features` (92 community-level functional traits) for functional context
   - Frame as "consistent with" or "independently corroborated by" — never causal
   - Report concordance rate and note genus-level resolution limitation

**Output**: `data/lab_field_concordance.tsv`, `data/nmdc_validation.tsv`

### Phase 5: Prioritization & Synthesis (NB05)

**Goal**: Produce a ranked candidate list for experimental characterization.

Scoring dimensions (each 0-1, weighted):
1. **Fitness importance** (0.25): max |fitness| across conditions, number of specific phenotypes, essentiality status
2. **Cross-organism conservation** (0.20): number of FB organisms with ortholog, fitness concordance score from NB02
3. **Functional inference quality** (0.20): module membership with prediction, co-fitness with annotated genes, domain clues, GapMind gap-filling evidence
4. **Pangenome distribution** (0.15): phylogenetic breadth (from NB02), core vs accessory classification
5. **Biogeographic signal** (0.10): strength of environmental pattern (from NB03), lab-field concordance score (from NB04)
6. **Experimental tractability** (0.10): in genetically tractable FB organism, not essential (can knock out), has characterized co-fitness partners

Output: Top 50-100 candidates with:
- Gene IDs across all organisms carrying orthologs
- Best functional hypothesis with evidence type and confidence
- Suggested experimental approach (which organism, which conditions)
- Environmental context summary
- All prior project cross-references (module ID, ortholog family, conservation class)

## Data Sources

### Tables Required

| Table | Database | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|---|
| `gene` | fitnessbrowser | Gene descriptions, coordinates | 228K | Full scan (small) |
| `genefitness` | fitnessbrowser | Fitness scores | 27M | Filter by orgId |
| `specificphenotype` | fitnessbrowser | Strong condition-specific effects | 38K | Full scan |
| `specog` | fitnessbrowser | Per-OG condition fitness summaries | varies | Filter by ogId |
| `experiment` | fitnessbrowser | Condition metadata | 7.5K | Full scan |
| `cofit` | fitnessbrowser | Co-fitness partners | 13.6M | Filter by orgId + locusId |
| `ortholog` | fitnessbrowser | Cross-organism BBH | ~1.2M | Filter by orgId |
| `genedomain` | fitnessbrowser | Domain annotations | millions | Filter by orgId |
| `seedannotation` | fitnessbrowser | SEED functional annotations | 177K | Filter by orgId |
| `organism` | fitnessbrowser | Organism metadata | 48 | Full scan |
| `gene_cluster` | pangenome | Core/accessory/singleton | 132M | Filter by species via temp view |
| `eggnog_mapper_annotations` | pangenome | Functional annotations (eggNOG OGs) | 93M | Filter by query_name via temp view of target OGs |
| `genome` | pangenome | Genome-species mapping | 293K | Full scan (small) |
| `gtdb_species_clade` | pangenome | Species taxonomy | 27.7K | Full scan (small) |
| `gtdb_taxonomy_r214v1` | pangenome | Taxonomy hierarchy | 293K | Full scan (small) |
| `gtdb_metadata` | pangenome | Lat/lon, isolation source | 293K | Full scan (small) |
| `ncbi_env` | pangenome | Environmental metadata (EAV) | 4.1M | Filter by accession |
| `alphaearth_embeddings_all_years` | pangenome | Environmental embeddings | 83K | Full scan (small) |
| `gapmind_pathways` | pangenome | Pathway predictions | 305M | Filter by genome_id for FB-linked species |
| `taxonomy_features` | nmdc_arkin | Community taxonomy profiles | 6.4K samples | Full scan (wide: 3,493 cols) |
| `taxonomy_dim` | nmdc_arkin | Taxon ID resolution | varies | Full scan |
| `abiotic_features` | nmdc_arkin | Environmental measurements | 6.4K samples | Full scan |
| `trait_features` | nmdc_arkin | Community trait scores | 6.4K samples | Full scan |

### Existing Data Products (loaded, not re-derived)

| Source Project | File | What It Provides |
|---|---|---|
| `conservation_vs_fitness` | `data/fb_pangenome_link.tsv` | 177,863 gene-to-cluster links (44 organisms, 94.2% median coverage) |
| `conservation_vs_fitness` | `data/organism_mapping.tsv` | FB orgId → GTDB species clade mapping |
| `fitness_modules` | module membership TSVs | 1,116 ICA modules across 32 organisms |
| `fitness_modules` | function predictions | 6,691 predictions for hypothetical proteins (guilt-by-association) |
| `essential_genome` | ortholog families | 17,222 ortholog groups, essentiality classification, 1,382 function predictions |

## Query Strategy

### Spark Session

On BERDL JupyterHub notebooks (no import needed — injected by kernel):
```python
spark = get_spark_session()
```

### Performance Plan
- **Tier**: Direct Spark on BERDL JupyterHub (required for large joins)
- **Estimated complexity**: Moderate-High (multi-table joins across FB + pangenome)
- **Known pitfalls**:
  - FB values are all strings — CAST to FLOAT/INT before numeric comparisons
  - Gene cluster IDs are species-specific — cannot compare across species; use eggNOG OGs for cross-species
  - Essential genes have zero rows in `genefitness` — must load separately from `essential_genome`
  - AlphaEarth covers only 28% of genomes — report coverage with every claim
  - `ncbi_env` is EAV format — pivot by `harmonized_name` before use
  - `gapmind_pathways` has multiple rows per genome-pathway pair — aggregate with MAX score before interpreting
  - Large IN clauses with species IDs containing `--` — use temp views and JOINs instead
  - Billion-row table joins — use BROADCAST hints for small lookup tables (per `cofitness_coinheritance` pitfall)
  - PySpark cannot infer numpy `str_` types — cast to native Python `str` before `createDataFrame()`
  - Singletons are a subset of auxiliary in pangenome schema (`is_auxiliary` and `is_singleton` can both be true)

### Key Queries

1. **NB01 — Census integration**: Load FB `gene` + `specificphenotype` + `genedomain` + `experiment` (all small-medium). Load `cofit` filtered per organism for non-module dark genes (top 5 partners). Merge with existing TSVs from prior projects.
2. **NB02 — GapMind gaps**: Filter `gapmind_pathways` by genome IDs from FB-linked species (temp view JOIN, not full scan). Two-stage aggregation: MAX score per genome-pathway, then species-level summary.
3. **NB02 — Phylogenetic breadth**: Extract eggNOG OG IDs for dark gene clusters → temp view → JOIN `eggnog_mapper_annotations` (93M) filtered by those OGs → map to taxonomy.
4. **NB03 — Biogeographic extraction**: For carrier species from NB02, JOIN `genome` → `alphaearth_embeddings` + `ncbi_env` + `gtdb_metadata`.
5. **NB04 — NMDC validation**: Load NMDC `taxonomy_features` (wide, 6.4K rows) + `abiotic_features` + `trait_features` locally. Resolve taxon IDs via `taxonomy_dim`. Match to carrier taxa by genus.

## Analysis Plan

### Notebook 1: Integration & Dark Matter Census
- **Goal**: Build unified dark gene table from existing data products + FB queries
- **Expected output**: `data/dark_genes_integrated.tsv` — ~54K dark genes (23.6% of 228K), of which ~3,700 have strong fitness effects (|fit|>2, |t|>4) plus ~4,100 hypothetical essentials. Each gene annotated with: annotation class, fitness summary, condition-class profile, conservation status, module membership + prediction, ortholog family, essentiality, top co-fitness partners, domain hits.
- **Key figures**: (1) Annotation status breakdown by organism, (2) fitness effect distribution for dark vs annotated genes, (3) coverage Venn diagram (has pangenome link × in module × has ortholog × is essential), (4) condition-class distribution for dark genes with strong phenotypes

### Notebook 2: GapMind Gaps, Cross-Organism Concordance & Phylogenetic Distribution
- **Goal**: Apply three new inference layers not covered by prior projects
- **Expected output**: `data/gapmind_gap_candidates.tsv` (dark genes filling pathway gaps), `data/concordance_scores.tsv` (family-level fitness concordance), `data/phylogenetic_breadth.tsv` (per-family taxonomic distribution)
- **Key figures**: (1) GapMind gap-filling examples, (2) concordance heatmap for top dark gene families, (3) phylogenetic breadth distribution (clade-restricted vs widespread)

### Notebook 3: Biogeographic Analysis
- **Goal**: Environmental distribution of dark gene carriers, within-species carrier vs non-carrier comparisons
- **Expected output**: `data/biogeographic_profiles.tsv`, `data/carrier_noncarrier_tests.tsv`
- **Key figures**: (1) AlphaEarth UMAP colored by carrier status for top dark gene families, (2) geographic maps of carriers, (3) NCBI isolation source breakdown, (4) within-species test results summary

### Notebook 4: Lab-Field Concordance & NMDC Validation
- **Goal**: Test whether lab fitness conditions predict field environmental distribution; supplementary NMDC validation
- **Expected output**: `data/lab_field_concordance.tsv`, `data/nmdc_validation.tsv`
- **Key figures**: (1) Lab-field concordance matrix (condition-class × environmental category), (2) concordance rate across dark gene families, (3) NMDC abiotic correlation plots for carrier taxa

### Notebook 5: Prioritization & Candidate Dossiers
- **Goal**: Score, rank, and produce experimental prioritization
- **Expected output**: `data/prioritized_candidates.tsv` — top 100 ranked candidates with full evidence
- **Key figures**: (1) Score component breakdown, (2) top-20 candidate summary cards, (3) organism distribution of top candidates, (4) recommended experiments by condition class

### Notebook 6: Robustness Checks & Controls
- **Goal**: Validate that scoring signals are robust and dark genes behave like real functional genes, not noise. Three controls: (1) H1b formal test — are stress-condition dark genes more accessory than carbon/nitrogen dark genes? (2) Dark-vs-annotated concordance null — do dark gene families achieve the same cross-organism concordance as annotated genes? (3) NMDC trait-condition validation — do dark gene carrier genera abundance correlate with matching community functional traits?
- **Expected output**: `data/h1b_test_results.tsv`, `data/annotated_control_concordance.tsv`, `data/nmdc_trait_validation.tsv`, `data/scoring_sensitivity_nb05.tsv`, `data/scoring_sensitivity_nb07.tsv`
- **Key figures**: (1) H1b formal test: stress vs carbon/nitrogen accessory rates, (2) dark vs annotated concordance distributions, (3) NMDC trait-condition correlation heatmap

### Notebook 7: Essential Dark Gene Prioritization
- **Goal**: Separately prioritize the 9,557 essential dark genes that are invisible to standard fitness scoring (zero genefitness rows). Uses gene neighbor analysis (5-gene window, same strand, ≤300 bp gap), domain annotations, ortholog conservation, phylogenetic breadth, and CRISPRi tractability to score essential genes on evidence available to them rather than penalizing them for lacking knockout fitness data.
- **Expected output**: `data/gene_neighbor_context.tsv` (57,011 dark gene neighbor profiles), `data/essential_dark_scored.tsv` (9,557 scored), `data/essential_prioritized_candidates.tsv` (top 50 with CRISPRi experiment designs)
- **Key figures**: (1) Gene neighbor analysis: annotated neighbor and operon partner rates, (2) essential dark gene score distributions, (3) top 20 essential candidates with score breakdown

### Notebook 8: Cross-Species Synteny & Co-fitness Validation
- **Goal**: Validate NB07's single-genome operon predictions using two independent methods: (1) cross-species synteny — is the dark/annotated gene neighborhood conserved across multiple FB organisms? (2) co-fitness — do predicted operon partners show correlated fitness profiles? Re-score all fitness-active and essential dark genes with new evidence.
- **Expected output**: `data/conserved_neighborhoods.tsv` (21,011 pairs), `data/cofit_validated_operons.tsv` (32,075 pairs), `data/improved_candidates.tsv` (300 re-scored top candidates), `data/experimental_roadmap.tsv` (31 organism priorities)
- **Key figures**: (1) Cross-species synteny conservation score distribution, (2) co-fitness validation: synteny vs cofit scatter, (3) evidence-weighted experimental roadmap

### Notebook 9: Final Synthesis — Darkness Spectrum, Covering Set & Action Plan
- **Goal**: Translate gene-level evidence into an experimental campaign: (1) classify all 57,011 dark genes into a "darkness spectrum" (T1 Void through T5 Dawn) based on 6 binary evidence flags, (2) select a minimum set of organisms via greedy weighted set-cover that covers 95% of total priority value, optimizing for tractability and phylogenetic diversity, (3) produce per-organism action plans classifying each gene as hypothesis-bearing (specific condition recommendation) or darkest (broad screen needed).
- **Expected output**: `data/dark_gene_census_full.tsv` (57,011 rows), `data/minimum_covering_set.tsv` (16,067 gene-to-organism assignments), `data/experimental_action_plan.tsv` (41 organisms with experiment types and conditions)
- **Key figures**: (1) Darkness tier distribution with evidence flag combinations, (2) set-cover diminishing returns curve with organism labels, (3) organism action plan heatmap with condition recommendations

## Expected Outcomes

- **If H1 supported**: A ranked catalog of experimentally validated but functionally unknown gene families, each with functional hypotheses, conservation context, and environmental distribution — directly actionable for targeted characterization experiments. The biogeographic analysis would reveal whether environmental selection pressures explain the maintenance of specific dark gene families.
- **If H0 not rejected**: Dark matter genes are truly random — their fitness phenotypes don't correlate with conservation, co-regulation, or environment. This would suggest these genes serve organism-specific, condition-specific roles with no generalizable biology. Even this is informative: it would mean gene function prediction requires organism-specific experimental approaches rather than comparative inference.
- **Mixed outcome (most likely)**: Some dark gene families show strong coherence (concordant phenotypes, environmental patterns, pathway integration) while others remain cryptic. The prioritized list would focus on the coherent families, while the cryptic ones highlight the limits of computational inference.
- **Potential confounders**:
  - Annotation bias: some "hypothetical" genes may have annotations in databases not checked (UniProt, InterPro)
  - Fitness noise: weak fitness effects may not replicate across experiments
  - Environmental metadata sparsity: AlphaEarth covers only 28%, NCBI env metadata is inconsistent
  - Taxonomy bridge limitations for NMDC validation (genus-level, not species)
  - GapMind pathway coverage limited to amino acid biosynthesis and carbon utilization — not all metabolic functions

## Integrity Safeguards

1. **Acknowledge prior work explicitly**: Module predictions and conservation analyses are loaded from prior projects, not re-derived
2. **Coverage reporting**: Every claim states N with data / N total
3. **Within-species comparisons** for biogeographic tests (controls for phylogeny)
4. **Multiple testing correction**: BH-FDR for all genome-wide tests
5. **Pre-registered condition-environment mapping** defined before looking at biogeographic data
6. **Null results reported honestly**: no environmental pattern is as informative as a positive pattern
7. **Independent validation**: NMDC data serves as held-out confirmation, not discovery
8. **GapMind aggregation**: MAX score per genome-pathway pair before interpreting completeness; use four-level score hierarchy

## Revision History
- **v1** (2026-02-25): Initial plan
- **v2** (2026-02-25): Restructured to build explicitly on prior projects (`fitness_modules`, `essential_genome`, `conservation_vs_fitness`, `module_conservation`). Reduced from 6 to 5 notebooks by consolidating census + integration. Incorporated plan review feedback: essential genes as separate dark class, GapMind score hierarchy, `specog` table for concordance, concrete pangenome-wide query strategy, Spark session pattern.
- **v3** (2026-02-26): Added NB08 (conserved gene neighborhoods, cofit-validated operons, improved prioritization). Cross-species synteny validation of NB07 operon predictions using ortholog group neighborhood conservation across 48 FB organisms. Cofit validation of non-essential operon pairs via tiered scoring (mutual top-5 through one-directional top-20). Re-scored all fitness-active (17,344) and essential (9,557) dark genes with new evidence. Evidence-weighted experimental roadmap incorporating synteny, cofit, and phylogenetic gap signals. Added Finding 12 to REPORT.md and updated limitations to explicitly compare methodology against DOOR/STRING/EFI-GNT standards.
- **v4** (2026-02-26): Added NB09 (final synthesis). Darkness spectrum classifies all 57,011 dark genes into 5 tiers (T1 Void through T5 Dawn) based on 6 binary evidence flags. Greedy weighted set-cover selects organisms covering 95% of priority value; MR-1 ranks first. Per-organism experimental action plans classify genes as hypothesis-bearing (specific condition recommendations) vs. darkest (broad screen). Added Finding 13 to REPORT.md, updated data/figure/notebook tables.
- **v5** (2026-02-26): Updated Analysis Plan to describe all 9 notebooks (NB06–NB09 were missing). Added NB06 (robustness checks), NB07 (essential gene prioritization), NB08 (cross-species synteny + cofit validation), NB09 (final synthesis) with goals, outputs, and figures. Rewrote REPORT.md Results section with narrative rationale explaining why each analysis step was needed and how it builds on the prior step. Added Experimental Recommendations section to REPORT.md as the front-and-center deliverable: top candidates with evidence rationale, top 5 organisms with selection justification, and a three-experiment starting campaign.
- **v6** (2026-02-27): Fixed 3 critical bugs and 1 moderate issue from automated review. (1) NB05 `score_pangenome()` breadth_class vocabulary mismatch — scoring function checked for `'widespread'`/`'clade-restricted'` strings that never existed in data (NB02 produces `'universal'`/`'pan-bacterial'`/`'multi-phylum'`/`'narrow'`); phylogenetic breadth sub-score was silently zeroed for all 17,344 genes. Fixed to match NB02 vocabulary. Score range shifted from 0.048–0.650 to 0.048–0.715. (2) NB09 `ORG_GENUS` hardcoded dict mapped only ~21 of 48 organisms; replaced with load from `organism_mapping.tsv` (covers 44/48) plus 4 manual fallbacks. Covering set now 42 organisms (28 genera) with correct genus-redundancy penalties. (3) Added `umap-learn>=0.5` to `requirements.txt`. (4) Removed `matplotlib.use('Agg')` and changed `plt.close()` to `plt.show()` in NB03–NB09 for inline figure rendering. All 7 notebooks re-executed; REPORT.md updated with corrected numbers.

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory
