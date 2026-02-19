# Discoveries Log

Running log of insights discovered during science projects. Tag each with `[project_name]`.

Periodically refactor stable insights into the appropriate structured doc (schema.md, pitfalls.md, performance.md).

---

## 2026-01

### [ecotype_analysis] Environment vs Phylogeny: Phylogeny usually dominates

Analysis of 172 species with sufficient data showed:
- Median partial correlation for environment effect: 0.0025
- Median partial correlation for phylogeny effect: 0.0143
- Phylogeny dominates in 60.5% of species
- Environment dominates in 39.5% of species

No significant difference between "environmental" bacteria (where lat/lon is meaningful) and host-associated bacteria (p=0.66).

### [ecotype_analysis] ANI extraction requires per-species iteration

Attempting to query ANI for all 13K+ genomes in a single IN clause fails/times out. Must iterate over species and query ANI for each species separately. See `docs/performance.md` for pattern.

### [pangenome_openness] Pangenome table has pre-computed stats

The `pangenome` table already contains `no_core`, `no_aux_genome`, `no_singleton_gene_clusters`, `no_gene_clusters` - no need to compute from gene_cluster table.

### [pangenome_openness] No correlation between openness and env/phylo effects

Tested whether open pangenomes (low core fraction) show different patterns. Results:
- rho=-0.05, p=0.54 for environment effect
- rho=0.03, p=0.73 for phylogeny effect
- No significant relationship found

### [integrity_checks] 12 orphan pangenomes are symbionts

The 12 pangenomes without matching species clades are mostly obligate symbionts:
- Portiera aleyrodidarum (whitefly symbiont)
- Profftella armatura (psyllid symbiont)
- Various uncultivated lineages (UBA, TMED, SCGC prefixes)

These are valid pangenomes but filtered from species metadata due to single-genome status.

### [cog_analysis] Universal functional partitioning in bacterial pangenomes

Analysis of 32 species across 9 phyla (357,623 genes) reveals a remarkably consistent "two-speed genome":

**Novel/singleton genes consistently enriched in:**
- L (Mobile elements): +10.88% enrichment, 100% consistency across species - STRONGEST SIGNAL
- V (Defense mechanisms): +2.83% enrichment, 100% consistency
- S (Unknown function): +1.64% enrichment, 69% consistency

**Core genes consistently enriched in:**
- J (Translation): -4.65% enrichment, 97% consistency - STRONGEST DEPLETION
- F (Nucleotide metabolism): -2.09% enrichment, 100% consistency
- H (Coenzyme metabolism): -2.06% enrichment, 97% consistency
- E (Amino acid metabolism): -1.81% enrichment, 81% consistency
- C (Energy production): -1.75% enrichment, 88% consistency

**Biological implications:**
- Core genes = ancient, conserved "metabolic engine" (translation, energy, biosynthesis)
- Novel genes = recent acquisitions for ecological adaptation (mobile elements, defense, niche-specific)
- Horizontal gene transfer (HGT) is the primary innovation mechanism, not vertical inheritance
- The massive L enrichment (+10.88%) suggests most genomic novelty comes from mobile elements
- Patterns hold universally across bacterial phyla, suggesting deep evolutionary constraint

**Hypothesis validation:** All 8 predictions from initial N. gonorrhoeae analysis confirmed across 32 species.

This represents a fundamental organizing principle of bacterial pangenome structure.

### [cog_analysis] Composite COG categories are biologically meaningful

Multi-function genes with composite COG assignments (e.g., "LV" = mobile+defense, "EGP" = amino acid+carb+inorganic ion) are not annotation artifacts:

- LV (mobile+defense): +0.34% enrichment, 76% consistency
- Suggests functional modules like "mobile defense islands"
- Should not be filtered out as noise - they represent genuine multi-functional genes

## 2026-02

### [aromatic_catabolism_network] Aromatic catabolism requires 7× more support genes than pathway genes

The β-ketoadipate pathway in ADP1 has 8 core genes, but 51 genes total show quinate-specific growth defects — a 7:1 support-to-pathway ratio. The support genes organize into 3 biochemically rational subsystems: Complex I (21 genes, NADH reoxidation), iron acquisition (7 genes, Fe²⁺ for ring-cleavage dioxygenase), and PQQ biosynthesis (2 genes, cofactor for quinate dehydrogenase). This quantifies a general principle: the metabolic infrastructure required to run a pathway dwarfs the pathway itself.

### [aromatic_catabolism_network] FBA models miss 59% of condition-specific essential genes

Of the 51 quinate-specific genes, 30 (59%) have no FBA reaction mappings — PQQ biosynthesis, iron acquisition, transcriptional regulators, and respiratory chain components are invisible to the metabolic model. For Complex I specifically, FBA predicts 1.76× higher flux on aromatics but 0% essentiality, because FBA's linear programming cannot represent the threshold effect of losing a single subunit from a multi-subunit complex.

### [aromatic_catabolism_network] Complex I dependency is on NADH flux, not aromatic chemistry

Cross-species ortholog-transferred fitness data shows Complex I defects are largest on acetate (-1.55 vs background) and succinate (-1.39), not aromatics. ADP1's quinate-specificity likely reflects an alternative NADH dehydrogenase (NDH-2) that compensates on lower-NADH-flux substrates. The "aromatic support network" is really a "high-NADH-flux bottleneck network."

### [aromatic_catabolism_network] Two DUF proteins are candidate Complex I accessory factors

ACIAD3137 (UPF0234/YitK) and ACIAD2176 (DUF2280) correlate at r > 0.98 with Complex I genes across 8 growth conditions. Both lack FBA reaction mappings and have no assigned metabolic function. Their near-perfect co-fitness with the nuo operon suggests physical or regulatory association with Complex I.

### [adp1_deletion_phenotypes] ADP1 phenotype landscape is a continuum, not discrete modules

Hierarchical clustering of 2,034 genes by their 8-condition growth profiles produces an optimal K=3 with silhouette=0.24 — no discrete functional modules. The phenotype landscape is a gradient, with one exception: 24 genes form a tight quinate-specific module (the aromatic degradation pathway). Gene essentiality varies continuously across conditions, supporting the Guzman et al. (2018) "adaptive flexibility" framework.

### [fitness_modules] ICA reliably decomposes fitness data into biologically coherent modules

Robust ICA (30-50 FastICA runs + DBSCAN clustering) consistently finds 17-52 stable modules per organism across 32 bacteria. 94.2% of modules show significantly elevated within-module cofitness (Mann-Whitney U, p < 0.05; mean |r| = 0.34 vs background 0.12). Genomic adjacency enrichment averages 22.7× across organisms, confirming modules capture operon-like co-regulated gene groups.

### [fitness_modules] Membership thresholding is the critical parameter, not ICA itself

The initial D'Agostino K² normality-based thresholding gave 100-280 genes per module — biologically meaningless. The ICA components themselves were fine; the problem was deciding which genes "belong" to each module. Switching to an absolute weight threshold (|Pearson r| ≥ 0.3 with module profile, max 50 genes) reduced modules to 5-50 genes and dramatically improved all validation metrics:
- Cofitness enrichment: 59% → 94.2%
- Within-module |r|: 0.047 → 0.34 (mean across 32 organisms)
- Modules became biologically coherent (22.7× genomic adjacency enrichment)

### [fitness_modules] Organisms with <200 experiments still produce valid modules

Caulo (198 experiments) showed the weakest signal in the pilot (2.9x correlation enrichment vs 31x for DvH), but organisms down to 104 experiments (Ponti) still produced stable modules. The key is capping components at 40% of experiments — higher ratios cause FastICA convergence failures and extreme slowness.

### [fitness_modules] Fitness Browser schema documentation has inaccuracies

Several table schemas differ from the documented schema:
- `keggmember` uses `keggOrg`/`keggId` (not `orgId`/`locusId`) — must join through `besthitkegg`
- `kgroupec` uses `ecnum` (not `ec`)
- `seedclass` has `orgId, locusId, type, num` (not subsystem/category hierarchy)
- `fitbyexp_*` tables are long format (not pre-pivoted as documented)

### [fitness_modules] Spark is accessible from CLI via berdl_notebook_utils

`from berdl_notebook_utils.setup_spark_session import get_spark_session` works from regular Python scripts on JupyterHub — not just notebook kernels. This enables running full analysis pipelines from the command line without `jupyter nbconvert`. The auto-import in `/configs/ipython_startup/00-notebookutils.py` only affects notebook kernels.

### [fitness_modules] Pan-bacterial module families exist across diverse phyla

Cross-organism module alignment using BBH ortholog fingerprints revealed 156 module families spanning 2+ organisms. The largest family spans 21 of 32 organisms across Proteobacteria, Bacteroidetes, Firmicutes, and Archaea — evidence of deeply conserved fitness regulons. 28 families span 5+ organisms.

This required using orthologs from ALL organisms in the analysis — an initial run using only 5-organism orthologs found just 27 families with no family spanning more than 4 organisms. The ortholog graph density is critical.

### [fitness_modules] Ortholog scope dramatically affects cross-organism analysis

Using BBH pairs from 5 organisms (10K pairs, 1,861 OGs) vs all 32 organisms (1.15M pairs, 13,402 OGs) produced radically different results:
- Module families: 27 → 156 (6x)
- Families spanning 5+ orgs: 0 → 28
- Family-backed predictions: 31 (4%) → 493 (56%)

Lesson: always extract orthologs for ALL organisms in the analysis, not just a pilot subset. The ortholog graph is not additive — adding organisms creates new transitive connections.

### [fitness_modules] PFam domains are essential for module enrichment — KEGG KOs are too fine-grained

The initial enrichment pipeline (KEGG + SEED + TIGRFam, min_annotated=3) annotated only 8.2% of modules (92/1,116). Root cause: KEGG KO groups average ~1.2 genes per term, so modules with 5-50 members almost never have 3+ genes sharing the same KO. Adding PFam domains (which have 814 terms with 2+ genes vs TIGRFam's 88) and lowering the overlap threshold to 2 increased annotation to 79.7% (890/1,116). PFam is the dominant annotation source — it provides domain-level functional labels that match module granularity.

Impact on downstream analysis:
- Predictions: 878 → 6,691 (7.6×), now covering all 32 organisms
- Annotated families: 32 → 145 out of 156 (93%)
- Three organisms (Caulo, Methanococcus_S2, Korea) went from 0 enrichments to 24-29 enriched modules

### [fitness_modules] Module-ICA is complementary to sequence-based methods, not competitive

Held-out KO prediction benchmark across 32 organisms showed ortholog transfer dominates at gene-level function prediction (95.8% precision, 91.2% coverage), while Module-ICA has <1% precision at the KO level. This is expected and informative, not a failure: modules capture **process-level co-regulation** (validated by 94.2% cofitness enrichment and 22.7× adjacency enrichment), not specific molecular function. An ABC transporter module correctly groups binding, permease, and ATPase subunits — but each has a different KO. The right framing for module-based predictions is "involved in [biological process]" not "has function [specific KO]."

### [fitness_modules] Enrichment min_annotated threshold must match annotation granularity

The min_annotated parameter (minimum overlapping genes to test for enrichment) must be calibrated to the annotation database's granularity. For gene-specific annotations (KEGG KOs: ~1 gene/term), min_annotated=3 eliminates nearly all tests. For domain-level annotations (PFam: many genes share domains), min_annotated=2 works well with FDR correction. Fisher's exact test handles small counts correctly — the statistical validity comes from FDR correction across all tests, not from requiring large overlaps per test.

### [conservation_vs_fitness] Essential genes are modestly enriched in core pangenome clusters

Across 33 diverse bacteria, putative essential genes (no transposon insertions in RB-TnSeq) are 86.1% core vs 81.2% for non-essential genes (median OR=1.56, 18/33 significant after BH-FDR). The enrichment is real but modest — most genes in well-characterized bacteria are core regardless of essentiality. The signal is strongest in organisms with larger clades (more genomes = more reliable core classification).

### [conservation_vs_fitness] Essential-core genes are functionally distinct from essential-auxiliary

Essential genes that map to core clusters are 41.9% enzymes and only 13.0% hypothetical — they are the well-characterized metabolic backbone (ribosomes, DNA replication, cell wall, cofactor biosynthesis). Essential-auxiliary genes (essential but not in all strains) are only 13.4% enzymes and 38.2% hypothetical. Essential-unmapped genes (strain-specific, no pangenome match) are 44.7% hypothetical — prime targets for functional discovery.

### [conservation_vs_fitness] SEED functional categories distinguish essential from non-essential

Essential-core genes are enriched in Protein Metabolism (+13.7 pp vs non-essential), Cofactors/Vitamins (+6.2 pp), Cell Wall (+3.9 pp). They are depleted in Carbohydrates (-7.9 pp), Amino Acids (-5.6 pp), Membrane Transport (-4.0 pp) — functions that are conditionally important rather than universally essential. This aligns with Rosconi et al. (2022) who found pan-genome composition influences essentiality in *S. pneumoniae*.

### [conservation_vs_fitness] FB aaseqs download uses different locus tags than the gene table for some organisms

The Fitness Browser aaseqs file (fit.genomics.lbl.gov/cgi_data/aaseqs) uses RefSeq-style locus tags (e.g., ABZR86_RS*) for some organisms, while the FB `gene` table uses the original annotation locus tags (e.g., N515DRAFT_*). This caused a complete join failure for Dyella79 (0% merge rate). Only 1 of 34 organisms was affected, but any pipeline joining aaseqs-derived data with gene table data should verify locus tag consistency.

### [fitness_effects_conservation] Fitness importance and pangenome conservation form a continuous gradient

Across 194,216 protein-coding genes in 43 bacteria, there is a clear 16-percentage-point gradient from essential genes (82% core) to always-neutral genes (66% core). The same pattern holds when binning by strongest negative fitness effect (min_fit < -3 → 78% core vs min_fit near 0 → 66%) and by fitness breadth (important in 20+ conditions → 79% core vs 0 conditions → 66%). This establishes that the essentiality-conservation link from `conservation_vs_fitness` is not binary but quantitative.

### [fitness_effects_conservation] Core genes are MORE likely to be burdens, not less

Counter to the expectation that accessory genes impose a carrying cost, core genes are more likely to show positive fitness effects when deleted (24.4% ever beneficial vs 19.9% for auxiliary; OR=0.77 for auxiliary vs core, p=5.5e-48). Core genes participate in more pathways and trade-off situations — they help in some conditions but cost in others. This challenges the "streamlining" model where accessory genes are metabolic burdens.

### [fitness_effects_conservation] Condition-specific fitness genes are more core, not more accessory

Genes with strong condition-specific phenotypes (from the FB `specificphenotype` table) are 77.3% core vs 70.3% for genes without specific phenotypes (OR=1.78, p=1.8e-97). This contradicts the intuition that condition-specific fitness = niche-specific genes = accessory genome. Instead, core genes are more likely to have detectable condition-specific effects because they are embedded in well-characterized, essential pathways.

### [module_conservation] Fitness modules are enriched in core genome genes

ICA fitness modules (co-regulated gene groups) are 86.0% core vs 81.5% baseline across 29 organisms (Fisher OR=1.46, p=1.6e-87; per-organism paired Wilcoxon p=1.0e-03, 22/29 organisms show enrichment). 59% of modules are >90% core genes. Co-regulated fitness response units are preferentially embedded in the conserved genome — the core genome is not just structurally conserved but functionally coherent at the module level.

### [module_conservation] Module family breadth does NOT predict conservation

Surprisingly, module families spanning more organisms do not have higher core fractions (Spearman rho=-0.01, p=0.914). The baseline core rate (~82%) is so high that there is no room for a gradient — families are nearly all core regardless of breadth. This is a ceiling effect, not evidence against the conservation-function relationship.

### [module_conservation] Essential genes are absent from ICA modules

0 essential genes appear in any of the 1,116 fitness modules across 32 organisms. ICA decomposes fitness variation, so genes with no fitness data (essential = no transposon insertions) are invisible to it. This means fitness modules capture only the non-essential portion of the genome's functional architecture.

### [core_gene_tradeoffs] Trade-off genes are enriched in the core genome

25,271 genes (17.8%) are true trade-offs — important (fit < -1) in some conditions, burdensome (fit > 1) in others. These are 1.29x more likely to be core (OR=1.29, p=1.2e-44). Core genes have more trade-offs because they participate in more pathways with condition-dependent costs and benefits. This explains why core genes are simultaneously more burdensome AND more essential than accessory genes.

### [core_gene_tradeoffs] The burden paradox is function-specific, not universal

The core-burden paradox is driven by specific functional categories: RNA Metabolism (+12.9pp), Motility/Chemotaxis (+7.8pp), Protein Metabolism (+6.2pp) all show core genes as more burdensome. But Cell Wall reverses: non-core cell wall genes are MORE burdensome (-14.1pp). The paradox is not a uniform property of the core genome but reflects the trade-off architecture of specific functional systems.

### [core_gene_tradeoffs] 28,017 "costly + conserved" genes = natural selection signature

Genes that are both burdensome in the lab AND core in the pangenome represent the strongest evidence for purifying selection in natural environments. They're costly to maintain, yet every strain keeps them — nature requires them in conditions not captured by the lab. By contrast, 5,526 genes are costly + dispensable (candidates for ongoing gene loss), and 21,886 are neutral + dispensable (niche-specific).

### [essential_genome] 15 gene families are essential in ALL 48 bacteria

Cross-organism essential gene analysis across 48 diverse bacteria (221,005 genes, 17,222 ortholog families) reveals 15 families that are essential in every organism: ribosomal proteins (rpsC, rplW, rplK, rplB, rplA, rplF, rps11, rpsJ, rpsI, rpsM), chaperonin (groEL), CTP synthase (pyrG), translation elongation factor G (fusA), valyl-tRNA synthetase (valS), and geranyltranstransferase (SelGGPS). These represent the irreducible essential core of bacterial life.

### [essential_genome] Only 5% of ortholog families are universally essential

Of 17,222 ortholog families across 48 bacteria, only 859 (5.0%) are universally essential — essential in every organism where the family has members. 4,799 families (27.9%) are variably essential (essential in some organisms, non-essential in others), and 11,564 (67.1%) are never essential. Variable essentiality (the majority of essential families) demonstrates that genomic context profoundly shapes which genes an organism requires for viability.

### [essential_genome] Orphan essential genes are 58.7% hypothetical — top functional discovery targets

7,084 essential genes have no orthologs in any other FB organism. Of these, 58.7% are annotated as hypothetical proteins — the least characterized yet most functionally important genes in each organism. By contrast, universally essential genes are only 8.2% hypothetical. The orphan essentials are prime candidates for novel biology.

### [essential_genome] Universally essential families are overwhelmingly core in the pangenome

Universally essential genes are 91.7% core vs 80.7% for non-essential genes. 71% of universally essential families are 100% core across all genomes in their species. Orphan essentials (no orthologs) are only 49.5% core — they are strain-specific essential functions that haven't been conserved across species.

### [essential_genome] Module transfer predicts function for 1,382 hypothetical essential genes

By finding non-essential orthologs that participate in ICA fitness modules, we generated 1,382 function predictions for hypothetical essential genes across 48 organisms. All predictions are backed by cross-organism module family conservation. This demonstrates that module context from non-essential orthologs can illuminate the function of essential genes that are invisible to fitness-based methods.

### [ecotype_env_reanalysis] Clinical sampling bias does NOT explain weak environment-gene content signal

The `env_embedding_explorer` project showed that human-associated samples dampen AlphaEarth geographic signal (2.0x vs 3.4x for environmental). We hypothesized this bias explained the weak environment effect in the ecotype analysis (median partial correlation 0.003). However, stratifying 213 species by dominant environment type (47% human-associated, 21% environmental) shows the opposite: human-associated species have *higher* partial correlations (median 0.084) than environmental species (0.051). Mann-Whitney p=0.83. The original conclusion — phylogeny dominates — holds regardless of sample environment. The geographic signal in embeddings and the environment-gene content relationship are distinct phenomena.

### [ecotype_env_reanalysis] 47% of ecotype species are human-associated by genome-level classification

Using isolation_source harmonization (12 categories from 5,774 values), 106/224 species in the ecotype analysis are majority human-associated (gut + clinical). Only 47/224 (21%) are majority environmental (Soil, Marine, Freshwater, Extreme, Plant). This is a more systematic classification than the original manual species-level categorization, and confirms the clinical bias but shows it doesn't confound the ecotype results.

### [env_embedding_explorer] AlphaEarth embeddings encode geographic signal, but strength depends on sample type

Environmental samples (Soil, Marine, Freshwater, Extreme, Plant) show a 3.4x ratio in embedding cosine distance between nearby (<100 km, mean=0.27) and far (>10K km, mean=0.90) genome pairs. Human-associated samples (gut, clinical) show only a 2.0x ratio (0.37 vs 0.75). Hospitals worldwide have similar satellite imagery (urban built environment), so human-associated genomes have more homogeneous embeddings regardless of geography. The pooled "All samples" curve (2.0x ratio) is dominated by the 38% human-associated fraction and substantially underestimates the true geographic signal in the embeddings.

**Implication**: Any analysis using AlphaEarth embeddings as environment proxies should stratify by sample type, or at minimum exclude human-associated samples. The weak environment signal found in `ecotype_analysis` (median partial correlation 0.0025) may be partially explained by this clinical bias.

### [env_embedding_explorer] 38% of AlphaEarth genomes are human-associated — strong clinical sampling bias

Of 83,287 genomes with AlphaEarth embeddings, 38% are human-associated (clinical 20%, gut 16%, other 2%). Environmental categories are much smaller (soil 7%, marine 7%, freshwater 7%). This reflects NCBI's bias toward pathogen sequencing — clinical isolates have good geographic metadata from epidemiological tracking, which is why they disproportionately have embeddings.

### [env_embedding_explorer] 36% of AlphaEarth coordinates may be institutional addresses, but some are legitimate field sites

30,469 genomes (36.6%) cluster at coordinates with >50 genomes of >10 species. However, several flagged locations are legitimate DOE/research field sites: Rifle, CO (1,883 genomes, DOE IFRC), Saanich Inlet (1,529, oceanographic time series), Siberian soda lakes (812, extremophile campaigns). The heuristic needs refinement — checking isolation_source homogeneity at each location would better distinguish field sites from institutional addresses.

### [env_embedding_explorer] 4.6% of AlphaEarth genomes have NaN embedding dimensions

3,838 of 83,287 genomes have NaN in at least one of the 64 embedding dimensions. The cause is unclear — possibly missing satellite imagery at those coordinates, or coordinates that fall outside satellite coverage (polar regions, ocean). These must be filtered before any embedding-based analysis.

### [enigma_contamination_functional_potential] Primary contamination-functional tests are null, but defense signal appears in coverage-aware sensitivity models

In the ENIGMA contamination-functional project (108 overlap samples), primary univariate associations were non-significant across defense, stress, metabolism, and mobilome outcomes in both mapping modes. However, after adding mapped-coverage-aware sensitivity models, contamination-defense association became significant (coverage-adjusted OLS contamination p = 3.98e-4 relaxed, 3.54e-3 strict; high-coverage subset Spearman p = 0.0207 relaxed, 0.0098 strict). This indicates the strongest signal is conditional on mapping coverage/model specification rather than broad across all outcomes.

### [enigma_contamination_functional_potential] Independent strict vs relaxed feature construction materially changes mode-specific outputs

When strict and relaxed mapping modes were computed independently in NB02 (instead of reusing strict outputs), 1,140 of 1,590 genus-feature pairs differed between modes (~71.7%), and site stress scores differed for all 108 samples. Strict-vs-relaxed sensitivity is therefore analytically meaningful and should not be approximated by copied feature tables.

### [enigma_contamination_functional_potential] Species-proxy bridge is currently coverage-limited under genus-only ENIGMA taxonomy

`enigma_coral.ddt_brick0000454` currently provides taxonomy through `Genus` (no species/strain rows). A species-proxy mode (`species_proxy_unique_genus`) that keeps only unique genus->single GTDB clade mappings retained 150 genera, but mapped abundance collapsed to mean 0.031 (vs 0.343 in strict/relaxed genus modes). In this low-coverage regime, defense trend was positive (rho=0.169) but non-significant (p=0.081), indicating that true species-level gains likely require higher-resolution ENIGMA taxonomy or metagenomic mapping.

### [enigma_contamination_functional_potential] Confirmatory defense tests remain null after global FDR; strongest signal remains exploratory and coverage-dependent

After adding explicit confirmatory vs exploratory labels in NB03 and applying global BH-FDR across all reported p-values, confirmatory defense Spearman tests in genus-level modes remained null (p=0.546/0.483; q=0.862/0.849). The strongest surviving signal was exploratory: relaxed coverage-adjusted defense model retained q=0.046, while strict and other sensitivity signals attenuated above q<0.1. Interpretation should therefore prioritize null confirmatory evidence and frame positive results as exploratory.

### [enigma_contamination_functional_potential] Confirmatory null is robust to contamination-index choice

Re-testing confirmatory defense endpoint under four index constructions (all-metals composite, uranium-only, top-3 variance metals, PCA-PC1) did not produce significant confirmatory associations after FDR correction (all q=0.546 across 8 confirmatory-variant tests). This indicates the null confirmatory result is not an artifact of one specific contamination-index formulation.

---

### [pangenome_pathway_geography] Ecological niche breadth strongly predicts metabolic pathway diversity

Analysis of 1,872 bacterial species with complete pangenome, GapMind pathway, and AlphaEarth embedding data reveals:

**H1: Pangenome openness → pathway completeness** (r=0.107, p=3.6e-6)
- Weak but significant positive correlation
- Open pangenomes (high accessory/core ratio) have slightly more complete pathways
- Stronger relationship with pathway VARIABILITY (std dev): r=0.066, p=0.004
- Suggests accessory genes enable metabolic heterogeneity within species

**H2: Niche breadth → pathway completeness** (r=0.392, p=7.1e-70) — STRONGEST SIGNAL
- Moderate positive correlation using AlphaEarth embedding diversity
- Embedding variance (ecological diversity) has even stronger effect: r=0.412, p=1.8e-77
- Geographic distance alone: r=0.360, p=1.8e-58 (weaker than embedding-based metrics)
- Species with broader ecological niches require more complete metabolic toolkits

**H3: Pangenome openness → niche breadth** (r=0.324, p=5.6e-47)
- Moderate positive correlation
- Open pangenomes correlate with broader ecological niches
- Core fraction shows strong NEGATIVE correlation with niche breadth: r=-0.445, p=1.4e-91
- Pangenome flexibility enables adaptation to diverse environments

**Key insight**: AlphaEarth embedding diversity is a better predictor of metabolic completeness than geography alone. The embeddings capture ecological context (soil vs marine vs clinical), not just geographic distance. This explains why embedding variance (r=0.412) outperforms geographic range (r=0.360) in predicting pathway completeness.

**Data coverage limitation**: Only 6.8% of species (1,872/27,690) have sufficient AlphaEarth coverage (≥5 genomes with embeddings). This is due to missing lat/lon metadata for most NCBI genomes, especially clinical isolates.

---

## Template

```markdown
### [project_name] Brief title

Description of what was discovered, why it matters, and any implications
for future analyses.
```
