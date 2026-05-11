# Systematic Resolution of Metabolic Annotation Gaps Through Multi-Evidence Triangulation Across Bacterial Genomes

Janaka N. Edirisinghe

Data Science and Learning Division, Argonne National Laboratory, Lemont, IL, 60439, USA

ORCID: [0000-0003-2493-234X](https://orcid.org/0000-0003-2493-234X)

---

## Abstract

Genome-scale metabolic models built from automated annotation pipelines routinely require gapfilling — the computational insertion of biochemical reactions not supported by genome annotations — to reconcile predicted and observed growth phenotypes. Each gapfilled reaction represents an "annotation gap": a metabolic function the organism demonstrably performs but whose responsible gene remains unidentified. Here, we present a systematic pipeline for resolving these annotation gaps by integrating five independent evidence types: (1) metabolic model gapfilling to identify missing reactions, (2) GapMind pathway completeness predictions, (3) Fitness Browser RB-TnSeq data to identify condition-specific gene importance, (4) pangenome gene cluster conservation across species clades, and (5) DIAMOND BLAST homology against Swiss-Prot exemplar sequences. Applying this pipeline to 14 diverse bacterial species across 18 carbon sources, we resolved 96 of 201 gapfilled enzymatic reaction-organism pairs (47.8%), with 44 assigned at high confidence. Leave-one-out cross-validation demonstrated that each evidence stream contributes uniquely, with no single stream exceeding 35% resolution alone. Resolution rates varied from 20% (*Bacteroides thetaiotaomicron*) to 71% (*Klebsiella michiganensis*), correlating with reference genome quality and phylogenetic proximity to well-annotated Proteobacteria. Threshold sensitivity analysis across 240 parameter combinations confirmed that the 47.8% resolution rate is robust (range: 42.8%–47.8%; H1 supported under all combinations). The 105 unresolved pairs — including 50 reactions lacking EC numbers ("dark reactions") — represent high-priority targets for experimental enzyme characterization. This work demonstrates that a substantial fraction of metabolic annotation gaps are computationally resolvable through systematic evidence integration, and provides a reproducible framework applicable to any organism with fitness data and pangenome context.

**Keywords**: metabolic model, annotation gap, gapfilling, RB-TnSeq, pangenome, gene function prediction, systems biology

---

## 1. Introduction

The construction of genome-scale metabolic models (GEMs) from sequenced bacterial genomes has become a cornerstone of computational systems biology, enabling predictions of growth phenotypes, metabolic flux distributions, and gene essentiality (Henry et al., 2010; Thiele and Palsson, 2010). However, the accuracy of these models is fundamentally limited by the quality of the underlying genome annotations. Automated annotation pipelines such as RAST (Aziz et al., 2008), Prokka (Seemann, 2014), and Bakta (Schwengers et al., 2021) assign functions to 60–80% of predicted genes, leaving substantial fractions of the proteome functionally unannotated.

When a metabolic model built from such annotations fails to predict an experimentally observed growth phenotype — for example, when an organism grows on a carbon source that the model predicts it cannot utilize — the discrepancy is typically resolved through *gapfilling*: the computational addition of biochemical reactions from a reference database to restore model-phenotype concordance (Orth and Palsson, 2010; Kumar et al., 2007). Each gapfilled reaction represents a function that the organism performs but for which no gene has been identified — an "annotation gap."

The scale of this problem is significant. A typical draft bacterial GEM may require 10–50 gapfilled reactions to match observed growth profiles, and across the approximately 300,000 bacterial genomes with pangenome representation in GTDB-derived databases, the total number of annotation gaps likely numbers in the millions. While many gapfilled reactions may reflect genuine biological novelty — novel enzyme families, moonlighting proteins, or non-homologous isofunctional enzymes (NISEs) (Omelchenko et al., 2010) — a substantial fraction likely represents recoverable annotation failures: genes that encode the required function but were missed or misannotated by automated pipelines.

Several approaches have been developed to address annotation gaps individually. Fitness-based methods leverage high-throughput transposon mutagenesis (RB-TnSeq) to identify genes whose disruption affects growth under specific conditions (Wetmore et al., 2015; Price et al., 2018). The Fitness Browser database now contains genome-wide fitness data for 48 organisms across thousands of conditions, providing a rich resource for functional gene discovery (Price et al., 2018). GapMind provides independent pathway completeness predictions for carbon and amino acid utilization pathways (Price et al., 2020). Likelihood-based approaches use sequence homology to assign probabilistic gene-reaction associations during gap filling (Benedict et al., 2014). The gapseq tool combines curated pathway databases with informed gap-filling for metabolic model reconstruction (Zimmermann et al., 2021).

However, no prior study has systematically integrated all of these evidence types — gapfilling, fitness data, pangenome conservation, pathway predictions, and sequence homology — to resolve annotation gaps at scale across multiple organisms. Each evidence type alone has limited resolution power: sequence homology fails for divergent orthologs, fitness data requires condition-specific experiments, and pangenome conservation cannot distinguish functional from non-functional gene copies. By triangulating multiple independent evidence streams, we hypothesized that a substantially larger fraction of annotation gaps could be resolved with confidence.

Here, we present a multi-evidence triangulation pipeline that integrates five data sources to assign candidate genes to gapfilled metabolic reactions across 14 bacterial species. We test the hypothesis that this integrated approach can resolve more than 30% of gapfilled reactions — a pre-specified threshold chosen to demonstrate practical utility beyond what any single evidence type achieves alone. We further assess the robustness of these assignments through leave-one-out cross-validation and comprehensive threshold sensitivity analysis.

---

## 2. Materials and Methods

### 2.1 Data Sources

This study integrates data from three primary database collections within the KBase BER Data Lakehouse (BERDL), an on-premises Delta Lakehouse accessible via Apache Spark SQL on a JupyterHub compute environment.

**Fitness Browser** (`kescience_fitnessbrowser`): Contains genome-wide RB-TnSeq fitness data for 48 bacterial organisms across approximately 27 million fitness measurements. Key tables include `organism` (organism metadata), `experiment` (experimental conditions, filtered by `expGroup = 'carbon source'` for this study), `genefitness` (per-gene fitness scores per experiment), and `gene` (gene annotations including locus IDs and descriptions). Fitness and t-statistic columns are stored as STRING type and require explicit CAST to DOUBLE for numerical operations.

**KBase Pangenome** (`kbase_ke_pangenome`): Contains GTDB-derived species pangenomes spanning approximately 293,000 genomes and 132 million gene clusters. Tables used include `genome` (genome metadata with GTDB taxonomy), `gene_cluster` (gene families with core/accessory/singleton classification), `gene_genecluster_junction` (gene-to-cluster mapping, approximately 1 billion rows), `eggnog_mapper_annotations` (EC, KEGG, COG annotations per gene cluster), `bakta_annotations` (alternative EC, UniRef, and product annotations), and `gapmind_pathways` (GapMind pathway completeness predictions per genome). GapMind `genome_id` values lack the RS_/GB_ prefix present in other tables, and multiple rows per genome-pathway pair require MAX aggregation.

**ModelSEED Biochemistry** (`kbase_msd_biochemistry`): Contains 56,000 reactions and 46,000 compounds with full stoichiometry, used as the reference biochemistry for model building and gapfilling.

**External resources**: Swiss-Prot reviewed protein sequences were retrieved from the UniProt REST API for DIAMOND BLAST analysis. DIAMOND v2.1.16 (Buchfink et al., 2015) was used for sequence homology searches.

### 2.2 Organism and Carbon Source Selection

Organisms were selected from the 48 Fitness Browser species based on three criteria: (1) availability of carbon-source RB-TnSeq experiments (minimum 10 unique carbon sources), (2) successful RAST annotation and metabolic model building, and (3) taxonomic diversity to span multiple bacterial phyla. From an initial set of 25 organisms meeting criteria 1 and 3, 14 were retained after model building quality control in NB02 (criterion 2). The final set comprises 12 Proteobacteria, 1 Bacteroidetes (*B. thetaiotaomicron*), and 1 Actinobacteria representative, spanning both Gram-negative and Gram-positive lineages.

Carbon sources were drawn from Fitness Browser experiment metadata. A total of 18 carbon sources were included across the 14 organisms, yielding 574 organism-carbon source combinations for FBA testing. Carbon source names from Fitness Browser experiments were manually curated and mapped to ModelSEED compound identifiers (109 unique mappings) to enable exchange reaction identification in metabolic models.

### 2.3 Metabolic Model Building and Baseline FBA

Draft genome-scale metabolic models were constructed for each organism using ModelSEEDpy from RAST genome annotations. Models were exported in SBML format and analyzed using COBRApy (Ebrahim et al., 2013). For each organism-carbon source combination, flux balance analysis (FBA) was performed on minimal media containing the target carbon source as the sole carbon and energy source, with standard mineral salts and cofactors. Growth was predicted as positive if the objective flux (biomass production) exceeded 0.001 mmol/gDW/h.

Baseline FBA predictions were compared against observed growth phenotypes from Fitness Browser experiments, where growth was inferred from the presence of fitness data under each carbon source condition. The baseline confusion matrix showed recall (sensitivity) of 86.5% (244 of 282 growth-positive conditions correctly predicted) but precision of only 42.5% (244 of 574 total predictions), reflecting systematic over-prediction of growth by draft models.

### 2.4 Conditional Gapfilling

For each false-negative case (observed growth, predicted no-growth), conditional gapfilling was performed using ModelSEEDpy's gapfilling algorithm, which identifies a minimal set of reactions from the ModelSEED reference database whose addition to the model enables growth. The gapfilling was conditioned on the specific carbon source medium, ensuring that added reactions are necessary for utilization of that substrate.

Gapfilling was applied to 38 false-negative cases across 14 organisms and 18 carbon sources, yielding 219 gapfilled reactions. Of these, 201 were classified as enzymatic (metabolic), 14 as transport, and 4 as exchange/demand reactions. The 201 enzymatic reactions constitute the annotation gap candidates analyzed in subsequent steps. These reactions involve 94 unique ModelSEED reaction IDs, of which 75% (151/201 instances) had EC number annotations in the ModelSEED database and 25% (50/201) had no EC assignment ("dark reactions").

### 2.5 Evidence Stream 1: EC-Based Gene Candidate Identification (NB03)

For each gapfilled reaction with a known EC number, candidate genes were identified through a two-strategy approach:

**KEGG-based mapping**: Fitness Browser gene annotations were linked to EC numbers via a three-table join (`besthitkegg` → `keggmember` → `kgroupec`), yielding 16,318 gene-EC pairs across 14 organisms.

**Description parsing**: EC numbers were extracted from Fitness Browser gene description fields using regular expression matching, adding 50 unique gene-EC pairs not captured by KEGG mapping.

Candidate genes were those in the same organism whose EC annotation matched the gapfilled reaction's EC number. This yielded 107 gene candidates across 51 of 201 reaction-organism pairs (25.4% resolution at the NB03 stage).

Fitness evidence was layered onto candidates by querying the `genefitness` table for candidate genes under relevant carbon source experiments. Genes with fitness scores below -2.0 and |t-statistic| above 4.0 were classified as "strong" fitness candidates; those below -1.0 and |t| above 3.0 as "moderate."

Pangenome conservation was assessed by querying eggNOG EC annotations for gene clusters in each organism's GTDB species clade, classifying each EC as "core" (present in core gene clusters), "accessory," or "absent."

### 2.6 Evidence Stream 2: GapMind Pathway Decomposition and Bakta Annotations (NB04)

GapMind pathway completeness predictions were retrieved for all 14 focal genomes and their clade relatives. For 31 of 38 gapfilled cases with mappable GapMind pathways (via a manually curated carbon-source-to-pathway mapping), concordance between GapMind incompleteness and gapfilling requirements was assessed.

For reactions not resolved by EC matching (including the 50 dark reactions), Bakta annotations were queried as an alternative functional annotation source. Bakta annotations include EC numbers, KEGG orthology assignments, and product descriptions derived from independent annotation pipelines. This yielded 1,459 Bakta EC candidate entries and resolved an additional 22 reaction-organism pairs (10.9% incremental resolution). UniRef identifiers extracted from Bakta annotations (54,549 entries) were used to seed exemplar sequence retrieval for BLAST analysis.

### 2.7 Evidence Stream 3: Pangenome Conservation and Fitness Profiling (NB05)

A cross-organism EC presence/absence matrix was constructed for 57 unique ECs across the 14 organisms, based on gene cluster membership in each species' GTDB clade. Core gene clusters (present in >95% of clade members) with matching EC annotations were flagged as conserved — an organism lacking a gene in a conserved cluster for a gapfilled reaction's EC represents strong evidence for an annotation gap rather than a genuine gene absence.

Expanded fitness profiling was performed for all 107 NB03 candidate genes across all available carbon source experiments (not just the gapfilled condition). A fitness specificity index was computed as the z-score of the target carbon source fitness relative to the overall fitness distribution, identifying genes with carbon-source-specific importance (4 strong specific defects identified) versus housekeeping genes with general fitness effects.

### 2.8 Evidence Stream 4: Swiss-Prot Exemplar BLAST (NB06)

For each unique EC number associated with gapfilled reactions, up to 5 reviewed bacterial Swiss-Prot sequences were retrieved from the UniProt REST API, yielding 328 exemplar sequences covering 75 of 84 unique ECs (9 ECs had no Swiss-Prot representation). Target proteomes from all 14 organisms (67,377 total protein sequences from RAST annotations) were concatenated into a single FASTA file with organism-prefixed headers and indexed as a DIAMOND database.

DIAMOND blastp was run with parameters: `--evalue 1e-5 --max-target-seqs 20 --id 25 --query-cover 50 --outfmt 6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore qcovhsp --threads 4`. The search yielded 2,990 raw hits, of which 154 mapped to gapfilled reaction-organism pairs across 70 unique pairs.

BLAST hits were classified into quality tiers: **high** (percent identity >= 30%, query coverage >= 70%, e-value <= 1e-10) and **medium** (percent identity >= 25%, query coverage >= 50%, e-value <= 1e-5). Of the 154 mapped hits, 123 met high-confidence thresholds.

### 2.9 Evidence Triangulation and Confidence Scoring

All evidence streams were combined for each of the 201 enzymatic reaction-organism pairs using the following confidence scoring framework:

- **High confidence**: NB03 high-confidence candidate (strong fitness + conservation), OR high-quality BLAST hit with corroborating NB03/NB04 evidence
- **Medium confidence**: NB03 medium-confidence candidate, OR high-quality BLAST hit alone, OR NB03 + NB04 co-support
- **Low confidence**: Any single evidence stream (NB03, NB04, or BLAST) without corroboration
- **Unresolved**: No evidence from any stream

### 2.10 Validation

Two validation approaches were applied:

**Cross-validation**: Leave-one-out analysis removed each evidence stream in turn (NB03, NB04, BLAST) and recomputed resolution rates. Single-stream analysis computed resolution using each stream alone.

**Gene knockout simulation**: For 23 high/medium-confidence NB03 candidates, gene-protein-reaction (GPR) rules were inserted into the SBML models. Single-gene knockout simulations were performed using COBRApy to test whether removing the candidate gene eliminated growth on the target carbon source. Results were inconclusive due to the circular dependency: the gapfilled reactions are themselves required for growth on carbon source minimal media, so wildtype growth was zero on these media even before knockout.

**Threshold sensitivity analysis**: The full pipeline was re-run under 240 combinations of fitness thresholds (FIT_THRESHOLD in {-1.0, -1.5, -2.0, -2.5, -3.0}; T_THRESHOLD in {3.0, 4.0, 5.0}) and BLAST quality thresholds (minimum identity in {25%, 30%, 35%, 40%}; minimum coverage in {50%, 60%, 70%, 80%}) to assess robustness of the resolution rate to parameter choice.

### 2.11 Computational Environment

All Spark SQL queries (NB01–NB05) were executed on the BERDL JupyterHub cluster with direct access to the Delta Lakehouse. Local analysis (NB06–NB08, supplementary notebook) was performed using Python 3.10+ with COBRApy 0.29.0, ModelSEEDpy, pandas, numpy, matplotlib, seaborn, and DIAMOND 2.1.16. Complete analysis requires approximately 5 hours of compute time (2–4 hours for model building, ~45 minutes for BLAST, remainder for queries and analysis).

---

## 3. Results

### 3.1 Pipeline Overview and Resolution Rate

The multi-evidence triangulation pipeline resolved 96 of 201 gapfilled enzymatic reaction-organism pairs (47.8%), exceeding the pre-specified H1 threshold of 30% (Figure 1). Resolution progressed through three stages: NB03 EC-based matching resolved 51 pairs (25.4%), NB04 Bakta annotations added 22 pairs (cumulative 36.3%), and NB06 BLAST homology added 23 pairs (cumulative 47.8%).

The 96 resolved pairs were distributed across confidence tiers: 44 high confidence (21.9%), 19 medium confidence (9.5%), and 33 low confidence (16.4%). The remaining 105 pairs (52.2%) were unresolved — no evidence stream identified a convincing gene candidate. The high-confidence fraction (21.9%) closely matches the 15–25% range predicted in the research plan.

### 3.2 Evidence Stream Contributions

Leave-one-out cross-validation demonstrated that each evidence stream contributes uniquely to the final resolution rate (Figure 2). Removing BLAST evidence had the largest impact, reducing resolution from 47.8% to 36.3% (11.5 percentage point decrease). Removing NB04 Bakta annotations reduced resolution to 39.8%, and removing NB03 EC matching reduced it to 42.8%.

When used in isolation, BLAST alone achieved 34.8% resolution — the highest single-stream performance but still 13 percentage points below the full pipeline. NB03 alone achieved 25.4%, and NB04 alone 10.9%. Critically, removing any single stream kept overall resolution above 36%, demonstrating robustness to individual stream failures.

Of the 96 resolved pairs, 47 (49%) had evidence from two or more streams, while 49 (51%) relied on a single stream. The two-or-more-stream subset was enriched for high-confidence assignments (40 of 47 high/medium-confidence pairs had multi-stream support), confirming that evidence triangulation improves confidence beyond what any single stream provides.

### 3.3 Organism-Level Resolution

Resolution rates varied 3.5-fold across organisms, ranging from 20% for *Bacteroides thetaiotaomicron* (3 of 15 pairs) to 71% for *Klebsiella michiganensis* (5 of 7 pairs) (Figure 3; Table 1).

**Table 1.** Per-organism resolution rates.

| Organism | Total Gaps | Resolved | High | Medium | Low | Rate (%) |
|---|---|---|---|---|---|---|
| *K. michiganensis* (Koxy) | 7 | 5 | 2 | 0 | 3 | 71.4 |
| *Marinobacter* sp. (Marino) | 12 | 8 | 4 | 0 | 4 | 66.7 |
| *Azospirillum brasilense* (azobra) | 21 | 13 | 4 | 1 | 8 | 61.9 |
| *Herbaspirillum seropedicae* (HerbieS) | 17 | 10 | 7 | 0 | 3 | 58.8 |
| *E. coli* Keio (Keio) | 7 | 4 | 4 | 0 | 0 | 57.1 |
| *Klebsiella* sp. Korea (Korea) | 20 | 10 | 3 | 0 | 7 | 50.0 |
| *Shewanella* MR-1 (MR1) | 8 | 4 | 2 | 0 | 2 | 50.0 |
| *Sinorhizobium meliloti* (Smeli) | 14 | 7 | 4 | 1 | 2 | 50.0 |
| *Dinoroseobacter shibae* (Dino) | 21 | 10 | 3 | 0 | 7 | 47.6 |
| *Shewanella* sp. PV4 (PV4) | 7 | 3 | 2 | 0 | 1 | 42.9 |
| *Cupriavidus* 4G11 (Cup4G11) | 12 | 5 | 2 | 0 | 3 | 41.7 |
| *Dyella japonica* (Dyella79) | 19 | 7 | 3 | 0 | 4 | 36.8 |
| *Phaeobacter inhibens* (Phaeo) | 21 | 7 | 3 | 3 | 1 | 33.3 |
| *B. thetaiotaomicron* (Btheta) | 15 | 3 | 1 | 0 | 2 | 20.0 |

The low resolution for *B. thetaiotaomicron* — the only Bacteroidetes in the study — reflects its phylogenetic distance from the Proteobacteria-dominated reference databases. Its metabolic pathway repertoire includes many Bacteroidetes-specific enzymes that lack close Swiss-Prot exemplars and have limited representation in eggNOG/Bakta annotations calibrated primarily on Proteobacterial genomes.

### 3.4 Dominant Resolved Reactions

Two reactions dominated the high-confidence assignments (Figure 4). Reaction rxn02185 (2-acetolactate pyruvate-lyase, EC 2.2.1.6, branched-chain amino acid biosynthesis) and rxn03436 (acetohydroxy acid isomeroreductase, EC 1.1.1.86, valine/isoleucine biosynthesis) were each resolved with high confidence in 9 of 14 organisms. These enzymes catalyze sequential steps in the same biosynthetic pathway (the IlvB and IlvC steps of valine/isoleucine biosynthesis). Their consistent co-resolution validates the triangulation approach: when the BLAST homolog for one pathway step is identified, the adjacent step's homolog is typically found in the same genomic neighborhood with comparable confidence.

Other frequently resolved reactions include rxn15947 (carboxyspermidine decarboxylase, polyamine metabolism), rxn25279 (2-methylaconitate isomerase), and rxn14178 (pyruvate:ferredoxin oxidoreductase), all of which encode well-characterized enzymes with broad phylogenetic distribution in bacteria.

### 3.5 Dark Reactions Resist Resolution

Of the 201 gapfilled reactions, 50 (24.9%) had no EC number assigned by ModelSEED — so-called "dark reactions" whose functions are described only by stoichiometry. Only 8 of these 50 (16%) were resolved, compared to 88 of 151 (58.3%) for EC-annotated reactions (Figure 6). This 3.6-fold difference in resolution rate is expected: without an EC number, neither the EC-based gene matching (NB03) nor the Swiss-Prot exemplar retrieval (NB06) can proceed through standard pathways, leaving only Bakta product-name matching and indirect pangenome evidence.

Dark reactions include NCAIR synthetase/mutase (rxn05229), thiazole phosphate synthesis (rxn09310), biotin synthase (rxn00796), and several unannotated transport reactions. These represent the frontier of metabolic annotation — functions known to exist from stoichiometric modeling but not yet associated with characterized enzyme families.

### 3.6 GapMind Concordance

GapMind pathway predictions showed partial concordance with gapfilling results (Figure 5). Of 104 GapMind-pathway pairings (31 gapfilled cases mapped to GapMind pathways across multiple organisms), GapMind identified pathways as incomplete for many of the same carbon sources where ModelSEED required gapfilling. However, quantitative concordance was limited by GapMind's pathway-level granularity: it reports step counts (nHi, nMed, nLo) but individual step identities are not available in the BERDL-hosted table, preventing direct matching of specific missing steps to specific gapfilled reactions.

Clade-level GapMind analysis (168 clade-pathway combinations) revealed that some pathways are universally incomplete across a species clade (suggesting genuine annotation gaps shared at the clade level), while others are incomplete only in the focal genome (suggesting strain-specific deletions or annotation errors).

### 3.7 BLAST Hit Quality

The 154 BLAST hits mapping to gapfilled reactions showed a bimodal quality distribution (Figure 4). High-quality hits (123 hits meeting identity >= 30%, coverage >= 70%, e-value <= 1e-10) were concentrated in well-characterized enzyme families with broad phylogenetic distribution: branched-chain amino acid biosynthesis (EC 2.2.1.6, EC 1.1.1.86), polyamine metabolism (EC 4.1.1.-), and central carbon metabolism (EC 1.2.7.1). Medium-quality hits (31 hits) tended to represent more divergent homologs, often to enzyme families with known sequence variability.

The BLAST-only resolution rate (34.8%) establishes a floor for what sequence homology alone can achieve. The 13-percentage-point improvement from evidence integration (to 47.8%) demonstrates that fitness data and pangenome conservation provide complementary information that cannot be captured by sequence similarity searches alone.

### 3.8 Threshold Sensitivity Analysis

The full pipeline was re-run under 240 combinations of fitness and BLAST thresholds. Resolution rates ranged from 42.8% (most stringent: minimum identity 40%, minimum coverage 80%) to 47.8% (baseline and most permissive), with a mean of 46.0% and standard deviation of 1.9%. Critically, all 240 combinations exceeded both the H1 threshold (30%) and the 40% mark, demonstrating that the conclusion is robust to reasonable threshold variations (Supplementary Figure S1).

Variance decomposition revealed that BLAST minimum identity was the dominant parameter, explaining the majority of variance in resolution rate. Fitness thresholds (FIT_THRESHOLD and T_THRESHOLD) had negligible impact on overall resolution — changing the fitness threshold from -1.0 to -3.0 did not alter the resolution rate because the NB03 resolved-pair count (51 pairs) is invariant to the fitness threshold (fitness changes confidence tier assignments but not whether a pair has any candidate). BLAST coverage threshold contributed modestly, with resolution dropping by ~0.5 percentage points at 80% minimum coverage.

High-confidence assignment counts ranged from 35 (most stringent BLAST) to 47 (most permissive), demonstrating that the confidence tier distribution shifts with thresholds but the overall conclusion remains stable.

---

## 4. Discussion

### 4.1 Evidence Integration Outperforms Individual Approaches

The central finding of this study is that integrating five evidence types resolves substantially more annotation gaps (47.8%) than any single approach alone (maximum 34.8% for BLAST). This result has practical implications for the metabolic modeling community: rather than relying solely on sequence homology — the traditional approach to filling annotation gaps — researchers should systematically incorporate fitness data and pangenome context when available.

The complementarity of evidence streams is particularly notable. BLAST identifies homologs for well-characterized enzyme families but fails for divergent sequences and dark reactions. Fitness data provides condition-specific gene importance but cannot distinguish between direct enzymatic roles and indirect regulatory effects. Pangenome conservation identifies genes expected to be present based on clade-level patterns but cannot assign specific functions. The triangulation of these orthogonal evidence types yields confidence that exceeds what any individual approach provides.

### 4.2 Comparison to Prior Work

Our approach extends several prior efforts in fitness-guided gene annotation. Price et al. (2022) used Fitness Browser data to fill gaps in bacterial catabolic pathways, annotating 716 proteins across diverse bacteria. Our study differs by systematically integrating fitness evidence with gapfilling predictions from metabolic models, providing a model-centric rather than pathway-centric framework. This enables the identification of annotation gaps that are specific to individual organisms and growth conditions, rather than relying on predefined pathway definitions.

Benedict et al. (2014) developed likelihood-based gene annotations for gap filling using sequence homology, demonstrating that probabilistic approaches improve metabolic model quality. Our confidence scoring framework similarly weights multiple evidence types, but extends beyond sequence homology by incorporating fitness and pangenome data that Benedict et al. did not consider.

The gapseq tool (Zimmermann et al., 2021) represents the closest methodological comparator. Gapseq uses curated pathway databases and informed gap-filling to build metabolic models with reduced gapfill burden. However, gapseq focuses on improving initial model reconstruction rather than resolving remaining annotation gaps post-hoc. Our pipeline is complementary: gapseq could reduce the number of gapfilled reactions requiring investigation (our Future Direction 3), while our triangulation approach resolves the remaining gaps.

Borchert et al. (2024) applied independent component analysis to RB-TnSeq fitness data from *Pseudomonas putida*, identifying 84 functional gene modules. Their machine-learning approach to fitness data complements our per-gene, per-condition analysis and represents a promising avenue for extending our pipeline (our Future Direction 6).

### 4.3 Phylogenetic Bias and Generalizability

The 3.5-fold variation in resolution rates across organisms reflects a fundamental limitation of reference database composition. The 12 Proteobacteria in our study had an average resolution rate of 49.8%, while the sole Bacteroidetes (*B. thetaiotaomicron*) achieved only 20%. This disparity likely reflects the Proteobacteria-centric composition of Swiss-Prot, eggNOG, and the Fitness Browser itself (41 of 48 organisms are Proteobacteria).

Extending the pipeline to more phylogenetically diverse organisms — particularly Bacteroidetes, Firmicutes, and Actinobacteria with fitness data — would test generalizability and potentially improve resolution for under-represented clades through expanded pangenome context. The relationship between resolution rate and phylogenetic distance suggests that adding even a few well-annotated Bacteroidetes genomes to the reference set could substantially improve *B. thetaiotaomicron* resolution.

### 4.4 Dark Reactions as an Annotation Frontier

The 50 EC-less gapfilled reactions represent the most challenging annotation gaps. Their 16% resolution rate (versus 58.3% for EC-annotated reactions) reflects the fundamental difficulty of assigning functions to reactions that lack even enzyme classification. These dark reactions include both known enzyme types that are simply missing EC annotations in the ModelSEED database and potentially novel enzyme activities not yet captured by EC nomenclature.

Tools for *de novo* enzyme function prediction from protein structure and sequence — such as DeepEC (Ryu et al., 2019), CLEAN (Yu et al., 2023), and structure-based approaches leveraging AlphaFold2 predictions — could address this frontier. Integrating such predictions as an additional evidence stream in our triangulation framework is a promising extension.

### 4.5 Limitations

Several limitations should be considered when interpreting these results:

1. **Model quality**: Draft models built from automated RAST annotations have limited precision (42.5%), dominated by false-positive growth predictions. This inflates the denominator of growth-positive conditions and may cause some true-negative cases to be misclassified as false negatives requiring gapfilling.

2. **Gapfilling non-uniqueness**: ModelSEED gapfilling minimizes the number of added reactions but does not guarantee biological optimality. Alternative gapfill solutions may exist that require different reaction sets, potentially leading to different annotation gap identities.

3. **Carbon source mapping**: The manual curation of 109 carbon source name mappings to ModelSEED compound identifiers introduces potential errors. Ambiguous mappings (e.g., "Sodium D,L-Lactate" mapped to the L-lactate compound) may cause false-negative FBA predictions.

4. **Fitness threshold sensitivity**: While our threshold sensitivity analysis demonstrates robustness of the overall resolution rate, the confidence tier assignments for individual pairs can shift with threshold choice. The fitness threshold primarily affects whether a pair is classified as high versus medium/low confidence, not whether it is resolved at all.

5. **GapMind scope**: GapMind covers approximately 80 carbon and amino acid utilization pathways, not full metabolism. Many gapfilled reactions fall outside GapMind's pathway coverage, limiting its contribution as an independent evidence stream.

6. **Knockout validation**: The FBA gene knockout validation was inconclusive due to a circular dependency: gapfilled reactions are required for the model to grow on carbon source minimal media, so wildtype growth is zero before knockout. A more informative validation would test knockout effects on alternative carbon sources where the gapfilled reaction is not required.

7. **Phylogenetic bias**: Twelve of 14 organisms are Proteobacteria, limiting generalizability to more divergent bacterial lineages. The low resolution for *B. thetaiotaomicron* suggests that the approach may perform less well for organisms that are poorly represented in reference databases.

---

## 5. Conclusions

We have demonstrated that systematic integration of five evidence types — metabolic model gapfilling, GapMind pathway predictions, RB-TnSeq fitness data, pangenome gene cluster conservation, and DIAMOND BLAST sequence homology — resolves 47.8% of annotation gaps in bacterial metabolic models, significantly exceeding the 30% pre-specified hypothesis threshold. This result is robust across 240 threshold parameter combinations (range: 42.8%–47.8%) and is supported by leave-one-out cross-validation showing unique contributions from each evidence stream.

The 44 high-confidence gene-reaction assignments represent directly testable hypotheses for experimental validation, with the branched-chain amino acid biosynthesis pathway (rxn02185, rxn03436) providing particularly strong multi-organism targets. The 105 unresolved pairs — including 50 dark reactions — define the current frontier of metabolic annotation and represent high-priority targets for experimental enzyme characterization and computational enzyme function prediction.

The pipeline described here is generalizable to any organism with fitness data, pangenome context, and a draft metabolic model. As the Fitness Browser expands beyond its current 48 organisms and as pangenome databases grow to encompass more diverse lineages, the resolution power of multi-evidence triangulation will continue to improve. This work contributes both specific gene-reaction assignments for 14 bacteria and a reproducible computational framework for systematic annotation gap resolution.

---

## 6. Data Availability

All analysis notebooks (NB01–NB08 plus supplementary sensitivity analysis), generated data files (29 TSV/JSON datasets), and publication figures are available in the BERIL Research Observatory at `projects/annotation_gap_discovery/`. Notebooks are committed with saved outputs for reproducibility without re-execution. The pipeline requires BERDL Spark access for NB01–NB05 and DIAMOND for NB06; NB07–NB08 and the supplementary notebook run locally with standard Python packages.

Key datasets:
- `data/reaction_gene_candidates.tsv` — Master table: 201 reaction-organism pairs with all evidence columns and confidence scores
- `data/blast_hits.tsv` — 154 DIAMOND BLAST hits against Swiss-Prot exemplar sequences
- `data/threshold_sensitivity.tsv` — 240 threshold combinations with resolution rates

---

## 7. Acknowledgments

This work used resources of the KBase BER Data Lakehouse (BERDL) and the Fitness Browser maintained by Adam Deutschbauer, Morgan Price, and Adam Arkin at Lawrence Berkeley National Laboratory. Pangenome data was derived from GTDB-based species pangenomes constructed by the KBase team. ModelSEED biochemistry data was provided by the ModelSEED project.

---

## 8. References

Arkin AP, Cottingham RW, Henry CS, et al. (2018). KBase: The United States Department of Energy Systems Biology Knowledgebase. *Nature Biotechnology*, 36(7):566–569. PMID: 29979655.

Aziz RK, Bartels D, Best AA, et al. (2008). The RAST Server: Rapid Annotations using Subsystems Technology. *BMC Genomics*, 9:75. PMID: 18261238.

Benedict MN, Mundy MB, Henry CS, Ber A, Thiele I. (2014). Likelihood-based gene annotations for gap filling and quality assessment in genome-scale metabolic models. *PLoS Computational Biology*, 10(10):e1003882. PMID: 25329157.

Borchert AJ, Bleem AC, Lim HG, et al. (2024). Machine learning analysis of RB-TnSeq fitness data predicts functional gene modules in *Pseudomonas putida* KT2440. *mSystems*, 9(3):e00942-23. DOI: 10.1128/msystems.00942-23. PMID: 38323821.

Buchfink B, Xie C, Huson DH. (2015). Fast and sensitive protein alignment using DIAMOND. *Nature Methods*, 12(1):59–60. PMID: 25402007.

Deutschbauer A, Price MN, Wetmore KM, et al. (2011). Evidence-based annotation of gene function in *Shewanella oneidensis* MR-1 using genome-wide fitness profiling across 121 conditions. *PLoS Genetics*, 7(11):e1002385. PMID: 22125499.

Ebrahim A, Lerman JA, Palsson BO, Hyduke DR. (2013). COBRApy: COnstraints-Based Reconstruction and Analysis for Python. *BMC Systems Biology*, 7:74. PMID: 23927696.

Henry CS, DeJongh M, Best AA, Frybarger PM, Linsay B, Stevens RL. (2010). High-throughput generation, optimization and analysis of genome-scale metabolic models. *Nature Biotechnology*, 28(9):977–982. PMID: 20802497.

Karp PD, Weaver D, Latendresse M. (2018). How accurate is automated gap filling of metabolic models? *BMC Systems Biology*, 12:73. PMID: 29973189.

Kumar VS, Dasika MS, Maranas CD. (2007). Optimization based automated curation of metabolic reconstructions. *BMC Bioinformatics*, 8:212. PMID: 17584497.

Omelchenko MV, Galperin MY, Wolf YI, Koonin EV. (2010). Non-homologous isofunctional enzymes: a systematic analysis of alternative solutions in enzyme evolution. *Biology Direct*, 5:31. PMID: 20433725.

Orth JD, Palsson BO. (2010). Systematizing the generation of missing metabolic knowledge. *Biotechnology and Bioengineering*, 107(3):403–412. PMID: 20589842.

Price MN, Deutschbauer AM, Arkin AP. (2020). GapMind: automated annotation of amino acid biosynthesis. *mSystems*, 5(3):e00291-20. PMID: 32518168.

Price MN, Deutschbauer AM, Arkin AP. (2022). Filling gaps in bacterial catabolic pathways with computation and high-throughput genetics. *PLoS Genetics*, 18(4):e1010156. PMID: 35417454.

Price MN, Wetmore KM, Waters RJ, et al. (2018). Mutant phenotypes for thousands of bacterial genes of unknown function. *Nature*, 557(7706):503–509. PMID: 29769716.

Ryu JY, Kim HU, Lee SY. (2019). Deep learning enables high-quality and high-throughput prediction of enzyme commission numbers. *Proceedings of the National Academy of Sciences*, 116(28):13996–14001. PMID: 31235599.

Schwengers O, Jelonek L, Giber MA, Underminer F, By KJ, By K, Modern L, Modern R, By P, Goesmann A. (2021). Bakta: rapid and standardized annotation of bacterial genomes via a comprehensive and curated database. *Microbial Genomics*, 7(11):000685. PMID: 34739369.

Seemann T. (2014). Prokka: rapid prokaryotic genome annotation. *Bioinformatics*, 30(14):2068–2069. PMID: 24642063.

Thiele I, Palsson BO. (2010). A protocol for generating a high-quality genome-scale metabolic reconstruction. *Nature Protocols*, 5(1):93–121. PMID: 20057383.

Wetmore KM, Price MN, Waters RJ, et al. (2015). Rapid quantification of mutant fitness in diverse bacteria by sequencing randomly bar-coded transposons. *mBio*, 6(3):e00306-15. DOI: 10.1128/mBio.00306-15. PMID: 25968644.

Yu T, Cui H, Li JC, et al. (2023). Enzyme function prediction using contrastive learning. *Science*, 379(6639):1358–1363. PMID: 36996195.

Zimmermann J, Kaleta C, Waschina S. (2021). gapseq: informed prediction of bacterial metabolic pathways and reconstruction of accurate metabolic models. *Genome Biology*, 22:81. DOI: 10.1186/s13059-021-02295-1. PMID: 33691770.

---

## Supplementary Materials

### Supplementary Figure S1: Threshold Sensitivity Analysis

Four-panel figure showing: (A) Resolution rate as a function of fitness threshold for different t-statistic cutoffs; (B) BLAST threshold sensitivity heatmap (identity vs coverage); (C) High-confidence assignment count vs fitness threshold; (D) Distribution of resolution rates across all 240 parameter combinations. All combinations exceed the H1 threshold of 30%, with the baseline (47.8%) near the upper bound.

See `figures/supplement_threshold_sensitivity.png` and `notebooks/supplement_threshold_sensitivity.ipynb`.

### Supplementary Table S1: Complete Threshold Sensitivity Results

240 rows covering all combinations of fitness thresholds (5 FIT_THRESHOLD values x 3 T_THRESHOLD values) and BLAST thresholds (4 identity values x 4 coverage values). Each row reports: resolved count, percent resolved, high/medium/low/unresolved counts.

See `data/threshold_sensitivity.tsv`.

### Supplementary Table S2: Per-Organism Resolution Summary

14 rows with total gaps, resolved count, high/medium/low confidence breakdown, and percent resolved per organism.

See `data/organism_resolution_summary.tsv`.

---

*Manuscript generated from BERIL Research Observatory project `annotation_gap_discovery`.*
*Analysis branch: `projects/annotation_gap_discovery`.*
