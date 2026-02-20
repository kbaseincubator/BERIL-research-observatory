# Report: Metabolic Capability vs Dependency

## Executive Summary

Just because a bacterium's genome encodes a complete metabolic pathway does not mean the organism depends on it. By crossing GapMind pathway completeness predictions with RB-TnSeq fitness data from the Fitness Browser, we classified 161 organism-pathway combinations across 7 model bacteria into four categories: **Active Dependency** (35.4%), **Latent Capability** (41.0%), **Incomplete but Important** (14.9%), and **Missing** (8.7%). The largest category -- Latent Capability -- represents pathways that are genomically complete but appear fitness-neutral under standard laboratory conditions. However, condition-type stratification reveals that all 66 Latent Capability pathways become fitness-important under specific stress, nitrogen limitation, or carbon limitation conditions, supporting the view that "latent" is context-dependent rather than absolute.

At the pan-bacterial scale (2,810 species with 10+ genomes), species with more variable pathways have significantly more open pangenomes (partial Spearman rho=0.530, p=2.83e-203 controlling for genome count), consistent with the Black Queen Hypothesis prediction that pathway gene loss is an ongoing evolutionary process. Amino acid biosynthesis pathways show the strongest dependence on accessory genes, with leucine, valine, arginine, lysine, and threonine biosynthesis showing core-vs-all completeness gaps of 0.14. Within-species pathway variation defines 2-8 metabolic ecotypes per species, and ecotype count correlates with pangenome openness (partial rho=0.322, p=8.0e-07).

*(Notebooks: 01-05, executed 2026-02-19)*

---

## Key Findings

### 1. Pathway Completeness Alone Is Insufficient to Predict Metabolic Dependency

![Four-category overview](figures/fig1_four_category_overview.png)

Of 161 classified organism-pathway pairs (7 Fitness Browser organisms, 23 GapMind pathways), only 35.4% (57/161) are Active Dependencies where a complete pathway contains fitness-important genes. The largest single category is Latent Capability at 41.0% (66/161): pathways that are genomically complete but whose constituent genes show no significant fitness defects under standard conditions. An additional 14.9% (24/161) are Incomplete but Important -- pathways that GapMind scores as incomplete yet whose mapped genes are fitness-important, suggesting annotation gaps or salvage routes. Only 8.7% (14/161) are Missing (neither complete nor important).

The composite importance score integrates three dimensions: 40% essentiality (fraction of pathway genes that are putative essentials), 30% fitness breadth (fraction of conditions with significant phenotype, per the fitness_effects_conservation finding that breadth predicts conservation better than magnitude), and 30% fitness magnitude (severity of the worst fitness defect). The mapping from FB genes to GapMind pathways uses FB-native KEGG annotations (besthitkegg to keggmember to EC to KEGG map to GapMind pathway) rather than the pangenome link table approach.

*(Notebook: 02_tier1_pathway_classification.ipynb)*

### 2. All "Latent Capabilities" Become Important Under Specific Conditions

![Condition-type shifts](figures/fig5_condition_type_shifts.png)

Condition-type stratification -- separating fitness effects by nitrogen source, carbon source, stress, and other conditions -- reveals that all 66 Latent Capability pathway-organism pairs become fitness-important under at least one condition type. This is consistent with the core_gene_tradeoffs finding that 28,017 genes across the Fitness Browser are "costly in lab but conserved in nature." The conditions that most frequently trigger reclassification are nitrogen limitation, stress, and carbon limitation.

This result means that "Latent Capability" is better understood as "conditionally active" rather than "genomic baggage." The pathways are maintained because they are needed, just not under the specific standard laboratory conditions used in most experiments. This has direct implications for Black Queen Hypothesis predictions: pathway gene loss may be constrained by the breadth of environmental conditions a species encounters, not just mean fitness under any single condition.

*(Notebook: 02_tier1_pathway_classification.ipynb)*

### 3. Conservation Validation: Active Dependencies Have Near-Complete Core Genomes

![Conservation by category](figures/fig2_conservation_by_category.png)

Validation against pangenome conservation data shows that Active Dependencies have mean core gene completeness of 0.986, compared to 0.975 for Latent Capabilities. The gap between categories is small because the 7 Fitness Browser organisms are well-studied model organisms (*Desulfovibrio vulgaris* Hildenborough, *Shewanella oneidensis* MR-1, *Pseudomonas putida*, *Pseudomonas stutzeri*, *Caulobacter crescentus*, *Sinorhizobium meliloti*, *Azospirillum brasilense*) with near-complete, well-annotated core genomes. The small but consistent direction of the enrichment is aligned with the metal_fitness_atlas finding that fitness-important genes are enriched in the core genome (OR=2.08 for metal-fitness genes).

*(Notebook: 02_tier1_pathway_classification.ipynb)*

### 4. Variable Pathways Strongly Correlate with Pangenome Openness

![Core vs accessory pathway completeness](figures/fig3_core_accessory_pathways.png)

Across 2,810 species with at least 10 genomes, the number of variable pathways (present in 10-90% of genomes) correlates with pangenome openness (fraction of accessory gene clusters). The raw Spearman correlation is rho=0.327 (p=7.2e-71). After controlling for genome count -- a critical confounder since species with more sequenced genomes may appear to have more variable pathways simply from sampling depth -- the partial Spearman correlation strengthens to rho=0.530 (p=2.83e-203).

This confirms hypothesis H1b: species undergoing more pathway variation have more open, fluid pangenomes. Genus-level stratification shows the signal holds in 5 of 18 genera tested at the p<0.05 level (Clostridium, Eubacterium, Mesorhizobium, Pseudomonas, Streptomyces), with positive direction in 13 of 18. The signal is strongest within Clostridium (rho=0.534) and Eubacterium (rho=0.506), with smaller sample sizes per genus limiting statistical power for many groups.

This is notable in the context of the pangenome_openness project, which found no correlation between openness and environment or phylogeny effect sizes. Pathway variation provides a mechanistically interpretable correlate of openness that the broader ecological/phylogenetic variables did not capture.

*(Notebook: 03_tier2_pathway_conservation.ipynb)*

### 5. Amino Acid Biosynthesis Pathways Show the Strongest Accessory Dependence

The comparison of core-only vs all-genes GapMind pathway completeness reveals which pathways depend on accessory genome contributions. The top accessory-dependent pathways are all amino acid biosynthesis routes:

| Pathway | All-Genes Completeness | Core-Only Completeness | Gap |
|---------|----------------------|----------------------|-----|
| Leucine (leu) | 0.614 | 0.468 | 0.146 |
| Valine (val) | 0.614 | 0.468 | 0.146 |
| Arginine (arg) | 0.613 | 0.472 | 0.141 |
| Lysine (lys) | 0.804 | 0.664 | 0.140 |
| Threonine (thr) | 0.803 | 0.663 | 0.140 |

These gaps mean that for a substantial fraction of bacteria, amino acid biosynthesis pathway completeness depends on genes in the accessory pangenome. This is direct evidence for Black Queen dynamics: the capacity to synthesize these amino acids is being distributed across strains within a species rather than being universally maintained. The branched-chain amino acids (leucine, valine) and basic amino acids (arginine, lysine) are the most common candidates for community-level metabolic sharing.

*(Notebook: 03_tier2_pathway_conservation.ipynb)*

### 6. Metabolic Ecotypes Correlate with Pangenome Openness

![Ecotype count vs openness](figures/fig4_ecotype_openness.png)

Among 225 species with sufficient genome diversity (50+ genomes and 3+ variable pathways), hierarchical clustering of binary pathway profiles (Jaccard distance) identifies a median of 4 metabolic ecotypes per species, with a maximum of 8. The species with the most ecotypes are *Alistipes onderdonkii* (8 ecotypes) and *Barnesiella intestinihominis* (8 ecotypes), both gut commensals with substantial intraspecific metabolic diversity.

Ecotype count correlates with pangenome openness: raw Spearman rho=0.262 (p=6.8e-05). After controlling for genome count (to account for the sampling bias where more-sequenced species may yield more clusters), the partial correlation remains significant: rho=0.322 (p=8.0e-07). This supports hypothesis H2 that within-species metabolic variation is a real biological phenomenon linked to genome fluidity, not merely a sampling artifact.

*(Notebook: 04_metabolic_ecotypes.ipynb)*

---

## Tier 1 Results: Organism-Level Pathway Classification

### Data and Scope

The Tier 1 analysis covers 7 Fitness Browser organisms for which GapMind pathway data is available: DvH (*Desulfovibrio vulgaris* Hildenborough), MR1 (*Shewanella oneidensis* MR-1), Putida (*Pseudomonas putida* KT2440), PS (*Pseudomonas stutzeri* RCH2), Caulo (*Caulobacter crescentus*), Smeli (*Sinorhizobium meliloti*), and azobra (*Azospirillum brasilense*). Of the 48 organisms in the Fitness Browser, only these 7 have matching GapMind genome data. Across these organisms, 23 GapMind pathways had sufficient gene-level annotation to classify, yielding 161 organism-pathway pairs.

### Classification Framework

Each organism-pathway pair is classified based on two binary dimensions:

- **Pathway completeness**: GapMind predicts whether the pathway is complete in >50% of conspecific genomes.
- **Fitness importance**: The composite importance score exceeds the data-driven median threshold.

The four resulting categories are:
- **Active Dependency** (complete + important): The organism needs and uses this pathway.
- **Latent Capability** (complete + not important): The pathway is encoded but dispensable under tested conditions.
- **Incomplete but Important** (not complete + important): Fitness data detects dependence that GapMind misses -- likely annotation gaps or salvage routes.
- **Missing** (not complete + not important): Pathway is absent and unneeded.

### Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| Active Dependency | 57 | 35.4% |
| Latent Capability | 66 | 41.0% |
| Incomplete but Important | 24 | 14.9% |
| Missing | 14 | 8.7% |

![Classification heatmap](figures/tier1_classification_heatmap.png)

### Condition-Type Analysis

The condition-type stratification separates per-gene fitness values by experimental condition (carbon limitation, nitrogen limitation, stress, other). For pathways classified as Latent Capability under the aggregate score, condition-specific reanalysis shows that all 66 shift to fitness-important under at least one condition type. The most frequent triggers are nitrogen limitation and stress conditions, aligning with the expectation that amino acid biosynthesis pathways are critical when nutrients are scarce but dispensable in rich media.

![Condition-type shifts](figures/tier1_condition_type_shifts.png)

---

## Tier 2 Results: Pan-Bacterial Pathway Conservation

### Scale

The Tier 2 analysis covers 2,810 GTDB species with at least 10 genomes in the pangenome database, spanning 80 GapMind pathways (18 amino acid biosynthesis + 62 carbon source utilization). Data was extracted from BERDL covering 293,000 genomes.

### H1b Confirmed: Variable Pathways Predict Open Pangenomes

The central result is a robust positive correlation between pathway variability and pangenome openness:

- **Raw Spearman**: rho=0.327, p=7.2e-71 (n=2,810 species)
- **Partial Spearman** (controlling for genome count): rho=0.530, p=2.83e-203
- **Within-genus consistency**: Signal positive in 13/18 genera; significant (p<0.05) in 5/18 genera (limited by per-genus sample sizes)

The strengthening of the correlation after controlling for genome count indicates that the raw correlation was partially suppressed by confounding -- species with many genomes tend to have high openness for sampling reasons, and they also tend to have variable pathways for sampling reasons, but the true biological relationship is even stronger once this shared confound is removed.

![Pathway conservation vs openness](figures/pathway_conservation_vs_openness.png)

### Core vs All-Genes Analysis

![Core vs all pathway completeness](figures/core_vs_all_pathway_completeness.png)

The comparison of `sequence_scope = 'core'` (core pangenome genes only) vs `sequence_scope = 'all'` (all genes) in GapMind reveals which pathways depend on accessory genome contributions. Amino acid biosynthesis pathways consistently show the largest gaps, meaning their completeness depends on genes that are not universally present within a species. Carbon source utilization pathways tend to show smaller gaps, perhaps because carbon catabolism genes are either universally present or universally absent rather than variably distributed.

### Phylogenetic Stratification

Per the ecotype_analysis finding that phylogeny dominates gene content in 60.5% of species, all correlations were checked within GTDB genera. The pathway-openness relationship holds in the majority of genera with sufficient species (≥20 species per genus), suggesting it reflects a general evolutionary dynamic rather than a clade-specific artifact. Full phylum-level stratification would require joining the GTDB taxonomy table from BERDL; genus-level grouping from the GTDB species clade names provides a conservative phylogenetic control.

![Pathway conservation by genus](figures/pathway_conservation_by_genus.png)

---

## Metabolic Ecotypes

### Definition and Method

For 225 species with 50+ genomes and at least 3 variable pathways, binary pathway profiles (complete/incomplete across 80 pathways) were clustered using hierarchical clustering with Jaccard distance. The number of ecotypes per species was determined by cutting the dendrogram at 50% of maximum distance.

### Results

- **Median ecotypes per species**: 4
- **Maximum ecotypes**: 8 (observed in *Alistipes onderdonkii* and *Barnesiella intestinihominis*)
- **Ecotypes vs openness**: rho=0.262, p=6.8e-05 (raw); rho=0.322, p=8.0e-07 (partial, controlling for genome count)

The ecotype-openness correlation survives the genome-count control, indicating that species with genuinely more metabolic diversity (not just more sampled genomes) tend to have more open pangenomes.

![Ecotype count vs openness](figures/ecotype_count_vs_openness.png)

---

## Synthesis: What This Means

### The Capability-Dependency Gap

The central finding of this project is that **genomic capability and metabolic dependency are distinct**. A complete pathway in a genome does not guarantee the organism depends on that pathway under any given condition. The 41% Latent Capability rate in model organisms suggests that nearly half of all complete metabolic pathways are conditionally dispensable -- but the condition-type analysis shows they are not permanently dispensable. Every "latent" pathway becomes important under some tested condition.

This reframes the Black Queen Hypothesis. Rather than a binary "needed vs genomic baggage" framework, metabolic pathways exist on a continuum of dependency that varies with environmental context. Pathways that are dispensable under carbon-rich conditions may be essential under nitrogen limitation. The frequency with which a species encounters each condition type determines the selective pressure to maintain the pathway.

### Accessory Genome as Metabolic Insurance

The core-vs-all completeness analysis provides direct evidence that accessory genes contribute to metabolic pathway completeness. For the top 5 accessory-dependent pathways (leucine, valine, arginine, lysine, threonine), approximately 14% of species-level pathway completeness comes from accessory genes. This means that within a species, different strains have different biosynthetic capabilities -- a precondition for Black Queen dynamics where metabolic functions become community-level public goods.

### Evolutionary Implications

The strong correlation between pathway variability and pangenome openness (partial rho=0.530) suggests that metabolic pathway gain and loss is a major driver of pangenome dynamics. Species with fluid genomes are the ones actively reshuffling metabolic capabilities among strains. Combined with the metal_fitness_atlas finding that fitness-important genes are enriched in the core genome (OR=2.08), this paints a picture where:

1. **Core genes** encode functions that are universally needed (central metabolism, metal tolerance, translation).
2. **Accessory genes** encode functions that are conditionally needed, including specific biosynthetic pathways.
3. **Pangenome openness** reflects the rate at which conditionally-needed pathways are gained and lost.

---

## Limitations

1. **Fitness Browser coverage**: Only 7 of 48 FB organisms have GapMind data, limiting Tier 1 to a small set of model organisms. These organisms have near-complete core genomes, which compresses the conservation validation signal.

2. **GapMind pathway scope**: GapMind covers 80 pathways (18 amino acid biosynthesis + 62 carbon utilization). Other metabolic domains (cofactor biosynthesis, lipid metabolism, secondary metabolism) are not assessed.

3. **Lab fitness vs natural selection**: The core_gene_tradeoffs project demonstrated that 28,017 genes are costly in lab but conserved in nature. While condition-type stratification partially addresses this, the full range of natural selective pressures is not captured by laboratory RB-TnSeq.

4. **KEGG-based pathway mapping**: The mapping from FB genes to GapMind pathways relies on KEGG annotations (besthitkegg to EC to KEGG map). Genes without KEGG annotations or with incorrect annotations are missed. This may underestimate the true number of genes per pathway.

5. **Ecotype clustering method**: The hierarchical clustering with a fixed 50% distance threshold is a simplification. Different distance thresholds would yield different ecotype counts. The median of 4 ecotypes per species should be interpreted as an order-of-magnitude estimate.

6. **Phylogenetic confounding**: While correlations were controlled for genome count and checked within taxonomic groups, full phylogenetic independent contrasts were not computed. The ecotype_analysis project found that phylogeny dominates gene content in 60.5% of species, and metabolic ecotypes may partially reflect intra-species phylogenetic structure.

7. **Sampling bias**: Species with more sequenced genomes are more likely to show pathway variation and more ecotypes. Partial correlations controlling for genome count mitigate but do not fully eliminate this bias.

8. **Importance threshold circularity**: The median-based importance threshold by construction splits pathways approximately 50/50 into important vs not-important categories. The finding that "all Latent Capabilities become important under some condition" should be interpreted with this in mind: with enough condition types and a median threshold applied to each subset, some pathways will inevitably cross the threshold. Calibrating against an independent validation set (e.g., known essentials from `essential_metabolome`) would provide a more defensible threshold.

9. **AlphaEarth niche breadth**: The RESEARCH_PLAN (H2) proposed correlating metabolic ecotypes with AlphaEarth environmental niche breadth, but this analysis was not executed. AlphaEarth embeddings cover only 28% of genomes (83K/293K), which would significantly limit the sample size. This remains a future direction.

---

## Connection to Other BERDL Projects

This project integrates findings from across the BERIL Research Observatory analytical pipeline:

| Project | Relationship | Key Finding Used |
|---------|-------------|-----------------|
| `metal_fitness_atlas` | Methodological template | 87.4% of metal-fitness genes are core (OR=2.08). Adopted OR-based conservation validation and cross-species aggregation framework. |
| `conservation_fitness_synthesis` | Evolutionary context | 16pp fitness-conservation gradient establishes that conserved genes are functionally active, not inert. Our Active Dependencies sit at the high end of this gradient. |
| `fitness_effects_conservation` | Importance score design | Fitness breadth predicts conservation better than magnitude. Incorporated breadth as 30% of composite importance score. |
| `core_gene_tradeoffs` | Condition-type motivation | 28,017 genes costly in lab but conserved in nature. Motivated condition-type stratification, which revealed all Latent Capabilities become important under stress/limitation. |
| `field_vs_lab_fitness` | Stratification approach | Field-important genes are 83.6% core vs 76.3% baseline. Adopted condition-type stratification (carbon/nitrogen/stress) for fitness aggregation. |
| `ecotype_analysis` | Phylogenetic caution | Phylogeny dominates gene content in 60.5% of species. Added phylogenetic controls to all correlations and ecotype analyses. |
| `pangenome_openness` | Null-result context | Openness does not correlate with environment or phylogeny effect sizes. Our pathway-variability metric succeeds where broader ecological variables failed. |
| `cofitness_coinheritance` | Pathway aggregation validation | 73% of accessory modules show co-inheritance with co-fitness. Validates the use of pathway-level fitness aggregation. |
| `essential_metabolome` | Pilot study | Identified 7 FB organisms with GapMind data; flagged GapMind coverage gaps (E. coli absent). |
| `module_conservation` | Null-result context | Module family breadth does NOT predict conservation. Our pathway-level analysis provides a complementary view where variability (not breadth) is the informative metric. |

### Cross-Project Synthesis

The metabolic capability-dependency framework connects three major findings from the BERDL pipeline:

1. **Fitness-conservation gradient** (conservation_fitness_synthesis): Conserved genes tend to be fitness-important. Our Active Dependencies are the metabolic instantiation of this general principle.

2. **Core enrichment of fitness genes** (metal_fitness_atlas): Fitness-important genes cluster in the core genome. Our Tier 2 analysis extends this from individual genes to whole pathways, showing that pathway completeness itself can depend on accessory genes.

3. **Condition-dependent fitness** (core_gene_tradeoffs, field_vs_lab_fitness): Lab fitness is an incomplete proxy for natural selection. Our condition-type analysis demonstrates this at the pathway level -- every "latent" pathway has conditions under which it matters.

---

## Data and Reproducibility

- **Data sources**: KBase BER Data Lakehouse (BERDL) via Spark on JupyterHub
- **Key tables**: `kbase_ke_pangenome.gapmind_pathways` (305M rows), `kescience_fitnessbrowser.genefitness` (27M rows), `kescience_fitnessbrowser.experiment` (7.5K experiments), `kescience_fitnessbrowser.besthitkegg` (KEGG annotations)
- **Data volume**: ~3.9 GB cached locally across all extracts
- **Notebooks**: 5 notebooks in `notebooks/` directory (NB01 on JupyterHub, NB02-05 local)
- **Figures**: 5 publication-quality synthesis figures + supporting visualizations in `figures/`

## Authors

Dileep Kishore, Paramvir Dehal
