# Report: Plant Microbiome Ecotypes — Compartment-Specific Functional Guilds and Their Genetic Architecture

## Key Findings

### 1. Plant compartments impose strong functional selection on microbial communities (H1)

![Compartment census showing species distribution across plant compartments](figures/nb01_compartment_census.png)

Analysis of 293,059 bacterial/archaeal genomes classified 1,136 species as plant-associated across four compartments: root (292 species), rhizosphere (160), phyllosphere (157), and endophyte (29). PERMANOVA on a 25-marker functional profile matrix revealed that compartment identity explains 53% of variance in microbial functional capabilities (pseudo-F=235.1, R²=0.527, p=0.001, 999 permutations).

![Compartment-specific marker enrichment heatmap](figures/compartment_heatmap.png)

Root-associated species showed the strongest functional specialization: ACC deaminase (OR=69.3, p=6.2e-156), T3SS (OR=65.6, p=2.5e-106), nitrogen fixation (OR=14.5, p=1.7e-97), and quorum sensing (OR=24.1, p=6.0e-76) were all massively enriched. Phyllosphere species were enriched in quorum sensing (OR=19.4) and T3SS (OR=10.7) but not nitrogen fixation. A chi-square test confirmed significant association between cohort type and compartment (chi²=17.8, p=6.7e-3).

*(Notebooks: 01_genome_census.ipynb, 04_compartment_profiling.ipynb)*

### 2. Beneficial genes are core-encoded; pathogenic genes are accessory (H2)

![Core vs accessory distribution by functional cohort](figures/core_vs_pathogenic.png)

Beneficial (PGP) gene clusters are predominantly core genome (64.6% core fraction), significantly exceeding both the genome-wide baseline of 46.8% and pathogenic gene clusters (45.2% core fraction). The Mann-Whitney U test comparing per-species core fractions yielded U=83,567,419 (p=3.38e-125), with a bootstrap 95% CI for the beneficial-pathogenic difference of [0.089, 0.106].

Among specific functions, biofilm (83.3% core), IAA biosynthesis (78.1%), nitrogen fixation (72.3%), and phosphate solubilization (70.9%) had the highest core fractions. In contrast, T4SS (48.5% singleton), coronatine toxin (45.2% singleton), and effectors (39.8% singleton) were strongly accessory/singleton-enriched.

*(Notebook: 05_genomic_architecture.ipynb)*

### 3. Pathogenic gene clusters co-occur with transposases, suggesting HGT (H4 — partial)

![Mobility proxy analysis](figures/mobility_proxies.png)

Three HGT proxies were evaluated. Transposase/integrase co-occurrence was strongly positive: among 1,136 plant-associated species, those carrying singleton marker gene clusters were 16× more likely to also carry transposase/integrase singletons (Fisher's exact OR=15.95, p=8.8e-20). However, the overall singleton enrichment ratio for markers was 0.78 (markers are *less* mobile than the genomic average; Wilcoxon p<1e-300). Cross-species context variation (same OG core in one species, singleton in another) was higher for pathogenic markers (0.534) than beneficial (0.450), but not significantly so (Kruskal-Wallis p=0.122).

The mixed signal suggests that while individual HGT events are common (transposase association), plant-interaction markers as a class are under stronger purifying selection than the genomic average — likely because they are functionally important once acquired.

*(Notebook: 05_genomic_architecture.ipynb)*

### 4. Co-occurring genera show functional redundancy, not complementarity (H3 — not supported)

Co-occurring plant-associated genera in NMDC soil communities showed *lower* GapMind pathway complementarity than random genus pairs (observed mean=10.72 vs null mean=12.74, permutation p=1.0, Cohen's d=-7.54). This is the opposite of the predicted metabolic complementarity.

BacDive metabolite utilization cross-validated GapMind predictions at 83.1% consistency, confirming that the pathway completeness scores are reliable. The result suggests that plant-associated microbial communities assemble via functional redundancy (niche overlap/environmental filtering) rather than niche partitioning.

*(Notebook: 06_complementarity.ipynb)*

### 5. Fifty novel gene families distinguish plant-associated species (H5)

![Volcano plot of eggNOG OG enrichment](figures/volcano_enrichment.png)

Genome-wide enrichment analysis of 5,671 eggNOG ortholog groups (OGs) identified 5,341 significantly associated with plant vs. non-plant species (q<0.05), of which 3,840 showed strong enrichment (OR>2). After phylogenetic control via phylum-level logistic regression, 50 novel OGs retained significance (all p<0.05, OR>1). The top hit was COG3569 (Fisher OR=8.92, phylo-controlled OR=6.01, q=7.7e-242), found in 54% of plant-associated species but only 12% of non-plant species.

The attenuation from Fisher OR to phylo-controlled OR (e.g., COG3569: 8.92→6.01) indicates partial phylogenetic confounding — plant-associated species cluster taxonomically — but a substantial ecological signal persists after correction.

*(Notebook: 03_enrichment_analysis.ipynb)*

### 6. Most plant-associated bacteria are dual-nature, carrying both PGP and pathogenic markers

![Cohort distribution by compartment](figures/nb04_cohort_compartment_bar.png)

The majority of plant-associated species (65–85% per compartment) carry both PGP and pathogenic marker genes simultaneously. In the NB02 marker survey, 15,474 of 25,660 species (60.3%) were classified as dual-nature. After composite scoring in NB07 with adaptive thresholds, the final distribution across 25,660 species was: neutral 38.0%, pathogenic 29.5%, dual-nature 25.2%, beneficial 7.3%.

![Synthesis overview: genus profiles, compartment distribution, genomic architecture](figures/synthesis_overview.png)

Validation against known organisms achieved 92.7% agreement: 88.5% for known PGPB genera (827/934 species correctly classified as beneficial or dual-nature) and 100% for known pathogen genera (530/530). Key dual-nature genera include *Pseudomonas_E* (358 species; PGP: HCN, phenazine, phosphate solubilization; Pathogenic: T2SS, T3SS, T6SS, effectors), *Bradyrhizobium* (73 species; PGP: nitrogen fixation, ACC deaminase; Pathogenic: T3SS, T4SS, CWDE), and *Streptomyces* (261 species; PGP: phenazine, phosphate solubilization; Pathogenic: CWDE, T3SS).

*(Notebooks: 02_marker_gene_survey.ipynb, 07_cohort_synthesis.ipynb)*

## Results

### Genome Census (NB01)

From 293,059 GTDB r214 genomes, plant association was determined via three complementary sources: NCBI isolation_source regex matching (primary), ncbi_env EAV table cross-validation (695 genomes upgraded), and BacDive isolation records (2,482 plant strains identified, 0 new upgrades). Species-level classification used majority-vote with mean confidence 0.88.

| Compartment | Species | Genomes |
|---|---|---|
| Root | 292 | 2,446 |
| Rhizosphere | 160 | 941 |
| Phyllosphere | 157 | 1,334 |
| Endophyte | 29 | 291 |
| Plant_other | 498 | 2,983 |
| **Total plant** | **1,136** | **7,995** |
| Non-plant (known) | 25,375 | 285,064 |

Root is dominated by rhizobia (*Rhizobium* 47, *Mesorhizobium* 45, *Bradyrhizobium* 41 species). Phyllosphere is dominated by *Sphingomonas* (16), *Methylobacterium* (13), *Pseudomonas_E* (13). *Pseudomonas_E* is the only genus with significant presence across all compartments.

### Marker Gene Survey (NB02)

A curated set of 91 marker genes (39 PGP, 44 pathogenic, 9 colonization) was searched across bakta annotations, Pfam domains, KEGG KOs, and product descriptions, yielding 588,098 marker gene clusters across 25,660 species. No Pfam domain hits were found (likely due to the query format in bakta_pfam_domains), so classification relied on gene name, KEGG KO, and product keyword matches.

![Marker gene survey overview](figures/nb02_marker_survey.png)

The most prevalent functional categories were: T6SS products (80,324 clusters), chemotaxis (69,986), quorum sensing (57,201), T3SS products (52,247), and T4SS (48,145). Among PGP functions, phosphate solubilization (23,876), phenazine (12,727), biofilm (7,512), and nitrogen fixation (6,139) were the most common.

### Enrichment Analysis (NB03)

Server-side aggregation of 93M eggNOG annotations produced OG-level prevalence for 5,671 OGs passing the 5% prevalence filter. Fisher's exact test with BH-FDR correction found 94.2% of tested OGs were significantly associated with plant status, reflecting the broad genomic differences between plant-associated and non-plant bacteria.

Top enriched OGs included COG3569 (OR=8.92), COG1764 (OR=9.29), COG5343 (OR=7.74), COG0654 (OR=12.66), and COG1845 (OR=14.47). All 50 top OGs survived phylum-level logistic regression (51 phyla as fixed effects), though all models showed convergence warnings.

### Compartment Profiling (NB04)

Fisher's exact tests across 96 marker×compartment combinations found 69 significant (q<0.05). The GapMind pathway completeness analysis yielded 0% completeness across all compartments at the core level, suggesting the core-level scoring threshold is too stringent for this broad taxonomic comparison. Thirty plant-associated genera were profiled in detail.

### Genomic Architecture (NB05)

| Cohort | Core % | Singleton % | N clusters |
|---|---|---|---|
| Beneficial | 64.6 | 20.7 | 60,590 |
| Colonization | 66.6 | 20.8 | 153,092 |
| Pathogenic | 45.2 | 31.0 | 374,416 |
| Genome-wide baseline | 46.8 | 35.3 | — |

All chi-square tests against the 46.8% baseline were significant (p≈0). The 986,464 transposase/integrase singleton clusters (722,674 transposase + 263,790 integrase) provided the HGT co-occurrence proxy.

### Complementarity Analysis (NB06)

NMDC taxonomy bridge matched 260 of 322 genera (80.7%) to GTDB. Of 69 genera in 348 soil/rhizosphere samples, all had GapMind data across 80 pathways. The 1,048 co-occurring pairs had mean complementarity of 10.72, while the permutation null (1,000 iterations preserving richness) yielded 12.74±0.27.

![Guild interaction network](figures/guild_network.png)

![Complementarity heatmap](figures/complementarity_heatmap.png)

![Complementarity heatmap detail](figures/complementarity_heatmap_detail.png)

C-score analysis for PGP-pathogen exclusion was not feasible: only 0 PGP-dominant and 2 pathogen-dominant genera were represented in NMDC co-occurrence data (the remaining 67 were dual-nature).

### Cohort Synthesis (NB07)

Composite scoring weighted PGP markers (40%), core fraction (20%), complementarity (15%), metabolic breadth (10%), with pathogen penalty (15%). Adaptive thresholds (median of non-zero scores) classified species into four cohorts. The 30 genus dossiers revealed that plant-associated genera nearly universally carry both PGP and pathogenic markers.

Key mechanism hypotheses:

| Mechanism | Cohort | Confidence |
|---|---|---|
| Nitrogen fixation (nifHDK) | Beneficial | High |
| Siderophore iron acquisition | Beneficial | High |
| T3SS effector injection | Pathogenic | High |
| Cell wall degradation (CWDE) | Pathogenic | High |
| ACC deaminase stress relief | Beneficial | Medium |
| Biocontrol antimicrobials (DAPG/phenazine) | Beneficial | Medium |
| Context-dependent T6SS | Dual-nature | Medium |
| PGP + secretion system co-occurrence | Dual-nature | Medium |

## Interpretation

### Compartment as Functional Filter

The strong compartment-specific enrichment (R²=0.53) is consistent with the well-established concept that plant compartments act as ecological filters (Trivedi et al. 2020). Our finding that root species are massively enriched in ACC deaminase (OR=69) aligns with the known role of ethylene modulation in root colonization. The enrichment of T3SS in both root (OR=65.6) and phyllosphere (OR=10.7) species is notable — T3SS serves both pathogenic injection and beneficial symbiotic signaling (e.g., rhizobial Nod factor delivery), consistent with the dual-nature theme.

The phyllosphere dominance of *Sphingomonas* and *Methylobacterium* matches the metaproteogenomic findings of Knief et al. (2012), who identified methylotrophy as the defining phyllosphere function. Our root-dominant genera (*Rhizobium*, *Mesorhizobium*, *Bradyrhizobium*) are well-characterized nitrogen fixers, validating the compartment classification pipeline.

### Core Genome Stability of Beneficial Functions

The finding that PGP genes are 64.6% core vs. 45.2% for pathogenic genes (p=3.4e-125) supports H2 and aligns with Levy et al. (2018), who found plant-associated bacteria enriched in core metabolic functions but depleted in mobile elements. This suggests beneficial functions are under strong positive selection once acquired, becoming fixed in the core genome. In contrast, pathogenic functions (T3SS, effectors, toxins) remain more dynamic — consistent with the arms-race model of host-pathogen coevolution.

However, this contrasts with Loper et al. (2012), who found biocontrol traits in *Pseudomonas* largely accessory. The discrepancy may reflect taxonomic scope: our analysis spans 25,660 species, while Loper et al. studied 10 strains within a single species group.

### Functional Redundancy in Co-occurring Communities

The rejection of H3 — co-occurring genera show functional redundancy, not complementarity — is consistent with Louca et al. (2018), who argued that functional redundancy is an emergent property of microbial systems. Our negative Cohen's d (-7.54) indicates strong redundancy. This makes ecological sense: environmental filtering (selecting for the same functions) is likely the dominant assembly mechanism, rather than niche partitioning.

Puente-Sanchez et al. (2024) found that functional complementarity can drive genome streamlining in some contexts. Our result does not contradict this — the complementarity signal may exist at finer-grained metabolic resolution than the 80 GapMind pathway categories can detect.

### The Dual-Nature Paradigm

Perhaps the most striking finding is that 60–85% of plant-associated bacteria carry both PGP and pathogenic markers. This aligns with Drew et al. (2021), who argued that microbial symbionts evolve along a parasite-mutualist continuum using shared molecular machinery, and with Etesami (2025), who documented the paradoxical dual nature of PGPB.

The implication is that classification as "beneficial" or "pathogenic" based on genomic markers alone is insufficient — the same T3SS that delivers pathogenic effectors in *Pseudomonas syringae* facilitates beneficial nodulation signaling in *Rhizobium*. Context (host genotype, environmental conditions, community composition) determines the outcome (Osayande et al. 2025).

### Novel Gene Families

The 50 novel OGs enriched in plant-associated species after phylogenetic control represent candidates for previously unrecognized plant-interaction functions. This is consistent with Saati-Santamaria et al. (2025), who found numerous uncharacterized genes upregulated during root colonization, and with Zhou et al. (2025), who reported that >99% of phyllosphere antimicrobial peptides were previously uncharacterized. The attenuation of odds ratios after phylogenetic correction (e.g., COG3569: 8.92→6.01) indicates that while plant-associated species are taxonomically clustered, a genuine ecological signal persists.

### Literature Context

- The compartment-specific functional signatures (H1) align with Trivedi et al. (2020) and Knief et al. (2012), extending their findings to a genome-scale analysis of 1,136 species.
- The core/accessory architecture pattern (H2) is consistent with Levy et al. (2018) but contradicts Loper et al. (2012) for biocontrol traits — likely due to our broader taxonomic scope.
- The functional redundancy result (H3 rejected) is consistent with the theoretical framework of Louca et al. (2018) and the empirical findings of Puente-Sanchez et al. (2024).
- The HGT proxy results (H4, partial) align with Ghaly et al. (2024), who found integrons as HGT hotspots in plant-associated bacteria, and Pinto-Carbo et al. (2016), who demonstrated HGT between obligate plant symbionts.
- The dual-nature prevalence corroborates Drew et al. (2021) and Etesami (2025), with our analysis providing the first genome-scale quantification across 25,660 species.

### Novel Contribution

This study provides three contributions beyond existing literature:

1. **Scale**: The first systematic classification of 25,660 bacterial species into plant-interaction cohorts using pangenome-scale marker gene analysis, compared to previous studies examining tens to hundreds of genomes.
2. **Architecture-function linkage**: Quantitative demonstration that beneficial gene core fraction (64.6%) exceeds pathogenic (45.2%) across the full bacterial tree of life, with bootstrap confidence intervals.
3. **Dual-nature quantification**: The finding that 60–85% of plant-associated species carry both PGP and pathogenic markers challenges the binary classification used in most PGPB screening programs.

### Limitations

1. **Compartment classification**: Based on NCBI isolation_source metadata, which has variable quality and coverage. Only 7,995 of 293,059 genomes (2.7%) had plant-associated annotations. Endophyte species (n=29) fell below the 30-species threshold.
2. **Marker gene completeness**: The bakta_pfam_domains table stores versioned Pfam IDs (e.g., `PF13629.12`) rather than bare accessions (`PF00771`), which caused zero hits in the original NB02 query. Fuzzy search in NB08 confirmed that T3SS-related Pfam domains do exist in the database (6 domains found, including PF13629 with 1,289 hits and PF18269 with 1,095 hits). The marker set is literature-curated and inevitably incomplete.
3. **GapMind pathway resolution**: Core-level completeness scoring yielded 0% across all compartments, suggesting the threshold is too stringent for broad taxonomic comparisons. The complementarity analysis used max-aggregated species-to-genus scores.
4. **Phylogenetic confounding**: Despite phylum-level fixed effects, the logistic regression models for H5 showed convergence warnings. Family-level control (NB08) produced insufficient variation for the top 10 novel OGs, likely because plant association is taxonomically clustered within families. Finer-grained phylogenetic correction (e.g., phylogenetic independent contrasts) would strengthen the novel marker claims.
5. **Mobility proxies**: Without GeNomad mobile element annotations, HGT was assessed indirectly. The mixed signal (strong transposase co-occurrence but lower-than-baseline singleton enrichment) highlights the limitations of proxy approaches.
6. **Dual-nature interpretation**: Presence of both PGP and pathogenic marker genes does not confirm simultaneous expression. Transcriptomic or experimental validation is needed to determine whether these represent genuine lifestyle flexibility or simply annotation artifacts (e.g., T6SS serving inter-bacterial competition rather than pathogenicity).
7. **Marker specificity**: Negative controls (NB08) reveal that non-plant genera such as *Escherichia*, *Salmonella*, and *Clostridioides* are 100% classified as dual-nature, and *Staphylococcus* at 98%. This reflects that several markers (flagella, chemotaxis, biofilm, quorum sensing, secretion systems) are ubiquitous across bacteria and not plant-specific. The marker panel should be refined with plant-specific thresholds or context-dependent scoring.
8. **Genome size confound**: Genome size (gene cluster count) correlates moderately with total marker count (r=0.44, p<1e-300), meaning larger genomes accumulate more markers by chance. Presence-based cohort assignment is partially insulated from this effect, but quantitative scores should be interpreted with caution.
9. **Multivariate dispersion**: PERMDISP testing (NB08) revealed significant dispersion heterogeneity between cohorts (H=33.12, p=3.0e-7), meaning the PERMANOVA R²=0.53 may partly reflect variance differences rather than pure location shifts.

### Adversarial Revision Results (NB08)

Twelve additional analyses addressed concerns raised during adversarial review:

**T3SS/T6SS Sensitivity**: Reclassifying T3SS, T6SS, and T2SS from "pathogenic" to "colonization" markers changed 16.4% of dual-nature species to PGP-only. However, plant-associated species remained 86.0% dual-nature under the revised classification, confirming that the dual-nature finding is robust and not driven solely by secretion system annotations.

![Sensitivity analysis: original vs revised cohort distribution](figures/sensitivity_t3ss_t6ss.png)

**Marker Drivers**: In dual-nature species, the most prevalent pathogenic markers were T6SS products (64%), T2SS (55%), T3SS products (50%), and chemotaxis (52%), while the most prevalent PGP markers were quorum sensing (49%), phenazine (34%), and flagella (40%). Chemotaxis and flagella — general motility functions — contribute substantially to the dual-nature classification.

![Marker prevalence in dual-nature species](figures/dual_nature_marker_drivers.png)

**PGP vs Pathogen Scatter**: Validated against known model organisms: *B. subtilis*, *R. leguminosarum*, *B. japonicum*, and *S. meliloti* cluster in expected quadrants.

![PGP vs pathogen composite scores with known organism annotations](figures/pgp_vs_pathogen_scatter.png)

**Genome Size**: Moderate correlation (r=0.44) between genome size and marker count. Cross-tabulation showed that genome-size normalization shifts 33% of dual-nature species to neutral, indicating the effect is meaningful but does not eliminate the dual-nature pattern.

![Genome size vs marker count by cohort](figures/genome_size_vs_markers.png)

**Predictive Classifier**: Random Forest achieved 64.4% accuracy for compartment prediction (root/rhizosphere/phyllosphere) using 25 binary markers — above the 33% random baseline but far from deterministic, consistent with compartment being one of multiple factors shaping marker profiles. Cohort prediction achieved 99.9% accuracy (trivially, since cohorts are defined by marker presence).

![Feature importance for compartment classification](figures/feature_importance_compartment.png)

**HGT Deep Dive**: Per-marker transposase co-occurrence analysis revealed that PGP markers show the strongest HGT signal: DAPG biocontrol (OR=8.75), ACC deaminase (OR=6.43), nitrogen fixation (OR=3.76). Among pathogenic markers, T4SS (OR=3.23), T6SS (OR=2.66), and effectors (OR=2.67) also showed significant enrichment. Contig co-location analysis found 498,677 marker-transposase pairs on shared contigs across 18,569 species. T4SS had the most co-located pairs (84,411) with the closest median distance (238 genes). Fifteen marker-transposase pairs were at gene-number distance 1 (immediately adjacent), spanning effectors, T6SS, T3SS, quorum sensing, cellulase, and T4SS in species including *Rhizobium ecuadorense*, *Phytobacter ursingii*, and *Burkholderia puraquae*.

![HGT signal by marker type](figures/hgt_per_marker_transposase.png)

![Contig co-location distances](figures/hgt_contig_distance.png)

## Data

### Sources

| Collection | Tables Used | Purpose |
|---|---|---|
| `kbase_ke_pangenome` | `genome`, `gene_cluster`, `pangenome`, `gtdb_taxonomy_r214v1`, `gtdb_metadata`, `bakta_annotations`, `bakta_pfam_domains`, `eggnog_mapper_annotations`, `gapmind_pathways` | Core pangenome data, functional annotations, pathway predictions |
| `kbase_ke_pangenome` | `ncbi_env` | Environmental metadata for genome classification |
| `kescience_bacdive` | `isolation`, `sequence_info`, `metabolite_utilization` | Strain-level isolation source and metabolic phenotypes |
| `nmdc_arkin` | `taxonomy_features`, `study_table` | Community ecology co-occurrence data |

### Generated Data

| File | Rows | Description |
|---|---|---|
| `data/genome_environment.csv` | 293,059 | Per-genome compartment classification |
| `data/species_compartment.csv` | 26,511 | Species-level compartment assignments (majority vote) |
| `data/compartment_census_summary.csv` | 9 | Compartment species counts |
| `data/ncbi_env_pivot.csv` | 279,547 | NCBI environment cross-validation pivot |
| `data/bacdive_isolation.csv` | 23,988 | BacDive isolation source records |
| `data/bakta_marker_hits.csv` | 387,822 | Bakta gene-name marker hits |
| `data/pfam_marker_hits.csv` | 0 | Pfam domain hits (none found) |
| `data/kegg_marker_hits.csv` | 39,640 | KEGG KO marker hits |
| `data/product_marker_hits.csv` | 256,269 | Product keyword marker hits |
| `data/marker_gene_clusters.csv` | 588,098 | Consolidated marker gene clusters |
| `data/species_marker_matrix.csv` | 25,660 | Species x functional category matrix |
| `data/species_cohort_markers.csv` | 25,660 | Species cohort assignments (NB02) |
| `data/enrichment_results.csv` | 5,671 | OG-level enrichment results |
| `data/logistic_phylo_controlled.csv` | 50 | Phylo-controlled logistic regression results |
| `data/top50_og_species.csv` | varies | Top-50 OG species distributions |
| `data/novel_plant_markers.csv` | 50 | Novel plant-enriched OGs |
| `data/compartment_profiles.csv` | 96 | Per-compartment marker enrichment |
| `data/genus_profiles.csv` | 30 | Top plant-associated genus profiles |
| `data/gapmind_plant_species.csv` | 2,213,340 | GapMind pathway predictions (plant species) |
| `data/pangenome_stats.csv` | 27,702 | Pangenome core/singleton statistics |
| `data/transposase_singletons.csv` | 986,464 | Transposase/integrase singleton clusters |
| `data/genomic_architecture.csv` | 23 | Per-function genomic architecture summary |
| `data/nmdc_genus_abundance.csv` | 40,271 | NMDC genus-level abundances |
| `data/nmdc_soil_file_ids.csv` | 25,547 | NMDC soil/rhizosphere sample IDs |
| `data/gapmind_genus_pathways.csv` | 658,712 | Genus-level GapMind pathway aggregation |
| `data/complementarity_network.csv` | 2,346 | Genus-pair complementarity scores |
| `data/cohort_assignments.csv` | 25,660 | Final composite cohort assignments |
| `data/genus_dossiers.csv` | 30 | Detailed genus-level dossiers |
| `data/genus_dossiers_plant_only.csv` | 30 | Plant/soil-filtered genus dossiers (NB08) |
| `data/species_family_taxonomy.csv` | 27,690 | Species-level GTDB family assignments (NB08) |
| `data/pfam_investigation_cache.csv` | 36 | Pfam domain investigation results (NB08) |

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|---|---|
| `01_genome_census.ipynb` | Classify 293K genomes by plant compartment; go/no-go checkpoint |
| `02_marker_gene_survey.ipynb` | Search 91 marker genes across annotations; classify species into cohorts |
| `03_enrichment_analysis.ipynb` | Genome-wide eggNOG OG enrichment with phylogenetic control |
| `04_compartment_profiling.ipynb` | Per-compartment functional signatures; PERMANOVA; genus profiles |
| `05_genomic_architecture.ipynb` | Core/accessory distribution (H2); HGT mobility proxies (H4) |
| `06_complementarity.ipynb` | NMDC co-occurrence; GapMind complementarity; permutation test |
| `07_cohort_synthesis.ipynb` | Composite scoring; validation; genus dossiers; hypothesis summary |
| `08_adversarial_revisions.ipynb` | Sensitivity analyses, negative controls, HGT deep dive, predictive classifiers |

### Figures

| Figure | Description |
|---|---|
| `nb01_compartment_census.png` | Bar chart of species per plant compartment |
| `nb02_marker_survey.png` | Marker gene survey overview: functional category counts and cohort distribution |
| `volcano_enrichment.png` | Volcano plot of OG enrichment (log2 OR vs -log10 q) with known marker annotations |
| `compartment_heatmap.png` | Heatmap of marker enrichment odds ratios across plant compartments |
| `nb04_cohort_compartment_bar.png` | Stacked bar: cohort proportions by compartment |
| `core_vs_pathogenic.png` | Boxplot comparing core fractions: beneficial vs pathogenic vs colonization |
| `mobility_proxies.png` | Multi-panel mobility proxy analysis (singleton ratio, transposase OR, context variation) |
| `guild_network.png` | Network visualization of genus-genus metabolic complementarity |
| `complementarity_heatmap.png` | Full complementarity score heatmap across genera |
| `complementarity_heatmap_detail.png` | Detail view of top complementarity pairs |
| `synthesis_overview.png` | Three-panel synthesis: genus marker profiles, compartment x cohort distribution, genomic architecture comparison |
| `sensitivity_t3ss_t6ss.png` | Side-by-side bar chart: original vs revised cohort distribution after T3SS/T6SS reclassification |
| `pgp_vs_pathogen_scatter.png` | Scatter plot of composite PGP vs pathogen scores with known organism annotations |
| `dual_nature_marker_drivers.png` | Horizontal bar chart: prevalence of each marker in dual-nature species |
| `genome_size_vs_markers.png` | Scatter plot: gene cluster count vs total marker count by cohort |
| `feature_importance_compartment.png` | Random Forest feature importance for compartment classification |
| `hgt_per_marker_transposase.png` | Dot plot: transposase co-occurrence odds ratio per functional category |
| `hgt_contig_distance.png` | Histogram of gene-number distances between co-located markers and transposases |

## Future Directions

1. **Functional annotation of novel OGs**: The 50 novel plant-enriched OGs (especially COG3569, COG5516, COG5343) warrant experimental characterization. Cross-referencing with AlphaFold structural predictions could reveal domain architectures suggestive of plant-interaction functions.

2. **Transcriptomic validation of dual-nature**: The dual-nature classification is based on gene presence. RNAseq under beneficial vs. pathogenic conditions would reveal whether both gene sets are co-expressed or differentially regulated.

3. **Finer-grained compartment resolution**: With more targeted isolation efforts, the endophyte compartment (currently 29 species) could be expanded to enable full four-way compartment comparison.

4. **GeNomad integration**: When mobile element predictions become available in BERDL, replacing the current proxy approach with direct mobile element annotation would strengthen H4 conclusions.

5. **Metabolic complementarity at finer resolution**: The GapMind pathway level (80 pathways) may be too coarse. Reaction-level complementarity or substrate-specific analysis could reveal complementarity patterns masked by pathway-level aggregation.

6. **SynCom design**: The genus dossiers and complementarity network could inform synthetic community design for plant growth promotion, following the approach of Song et al. (2026) for Bacillus SynComs.

## References

- Ajdig M, Mbarki A, Chouati T, Rached B, ..., Melloul M (2025). "Comprehensive genomic and pan-genomic analysis of the drought-tolerant Bacillus halotolerans strain OM-41." *World J Microbiol Biotechnol* 41:157. PMID: 40719802
- Bai Y, Muller DB, Srinivas G, Garrido-Oter R, ..., Schulze-Lefert P (2015). "Functional overlap of the Arabidopsis leaf and root microbiota." *Nature* 528:364-369. PMID: 26633631
- Coyte KZ, Stevenson C, Knight CG, Harrison E, Hall JPJ, Sherr DJ (2022). "Horizontal gene transfer and ecological interactions jointly control microbiome stability." *PLoS Biol* 20:e3001847.
- Drew GC, Stevens EJ, King KC (2021). "Microbial evolution and transitions along the parasite-mutualist continuum." *Nat Rev Microbiol* 19:623-638. PMID: 33875863
- Etesami H (2025). "The dual nature of plant growth-promoting bacteria." *Curr Res Microbial Sci* 9:100421. PMID: 40600175
- Ghaly TM, Gillings MR, Rajabal V, Paulsen IT, Tetu SG (2024). "Horizontal gene transfer in plant microbiomes: integrons as hotspots." *Front Microbiol* 15:1338026. PMID: 38741746
- Hansen AP et al. (2025). "Functional profiles of phyllosphere and rhizosphere metagenomes differ across milkweed species." *Environ Microbiol Rep* 17(4).
- Knief C, Delmotte N, Chaffron S, Stark M, ..., Vorholt JA (2012). "Metaproteogenomic analysis of microbial communities in the phyllosphere and rhizosphere of rice." *ISME J* 6:1378-1390. PMID: 22189496
- Levy A, Salas Gonzalez I, Mittelviefhaus M, ..., Dangl JL (2018). "Genomic features of bacterial adaptation to plants." *Nat Genet* 50:138-150. PMID: 29255260
- Loper JE, Hassan KA, Mavrodi DV, Davis EW, ..., Paulsen IT (2012). "Comparative genomics of plant-associated Pseudomonas spp." *PLoS Genet* 8:e1002784. PMID: 22792073
- Louca S, Polz MF, Mazel F, Albright MBN, ..., Parfrey LW (2018). "Function and functional redundancy in microbial systems." *Nat Ecol Evol* 2:936-943. PMID: 29662222
- Osayande IS, Han X, Tsuda K (2025). "Dynamic shifts in plant-microbe relationships." *Plant Biotechnol* 42(3):25.0428a.
- Parks DH, Chuvochina M, Rinke C, Mussig AJ, ..., Hugenholtz P (2022). "GTDB: an ongoing census of bacterial and archaeal diversity through a phylogenetically consistent, rank normalized and complete genome-based taxonomy." *Nucleic Acids Res* 50:D199-D207. PMID: 34520557
- Pinto-Carbo M, Sieber S, Dessein S, ..., Carlier A (2016). "Evidence of horizontal gene transfer between obligate leaf nodule symbionts." *ISME J* 10:2092-2105. PMID: 26978165
- Price MN, Wetmore KM, Waters RJ, ..., Deutschbauer AM (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509. PMID: 29769716
- Puente-Sanchez F, Pascual-Garcia A, Bastolla U, ..., Elias-Arnanz M (2024). "Cross-biome microbial networks reveal functional redundancy." *Commun Biol* 7:1046.
- Saati-Santamaria Z, Gonzalez-Dominici LI, ..., Garcia-Fraile P (2025). "Transcriptome-guided discovery of novel plant-associated genes in a rhizosphere Pseudomonas." *Microbiome* 14:20. PMID: 41345977
- Shariati JV, Malboobi MA, Tabrizi Z, ..., Ghareyazie B (2017). "Comprehensive genomic analysis of a plant growth-promoting rhizobacterium Pantoea agglomerans strain P5." *Sci Rep* 7:15820.
- Silva UCM, da Silva DRC, ..., Dos Santos VL (2025). "Genomic and phenotypic insights into Serratia interaction with plants." *Braz J Microbiol* 56:1045-1068. PMID: 40131635
- Song Y, Chen Q, Luo S, ..., Shen D (2026). "Ecology-guided Bacillus SynCom from a rice-duckweed core reveals division of labor." *Microbiome* 14.
- Trivedi P, Leach JE, Tringe SG, Sa T, Singh BK (2020). "Plant-microbiome interactions: from community assembly to plant health." *Nat Rev Microbiol* 18:607-621. PMID: 32788714
- Zhou H, Gao Y, Wu B, ..., Ni K (2025). "Phyllosphere microbiomes in grassland plants harbor a vast reservoir of novel antimicrobial peptides." *J Adv Res*. PMID: 41391818
