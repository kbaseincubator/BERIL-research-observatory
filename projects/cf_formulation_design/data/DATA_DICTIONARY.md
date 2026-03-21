# Data Dictionary — CF Protective Microbiome Formulation Design

This document describes all TSV output files produced by the analysis notebooks
in the `projects/cf_formulation_design/` pipeline. Each section lists the source
notebook, row count, and per-column metadata (name, inferred type, description).

---

## isolate_master.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB01 — `01_data_integration_eda.ipynb` |
| **Rows** | 429 |
| **Description** | Master table of all PROTECT isolates with carbon utilization OD values, taxonomy, genome QC metrics, inhibition scores, and metabolic overlap with PA14. One row per isolate. |

| Column | Type | Description |
|--------|------|-------------|
| `asma_id` | string | Unique isolate identifier (e.g., ASMA-1046, APA20000) |
| `no_carbon` | float | OD600 on no-carbon control medium |
| `glucose` | float | OD600 on glucose as sole carbon source |
| `lactate` | float | OD600 on lactate as sole carbon source |
| `serine` | float | OD600 on serine as sole carbon source |
| `threonine` | float | OD600 on threonine as sole carbon source |
| `alanine` | float | OD600 on alanine as sole carbon source |
| `glycine` | float | OD600 on glycine as sole carbon source |
| `proline` | float | OD600 on proline as sole carbon source |
| `isoleucine` | float | OD600 on isoleucine as sole carbon source |
| `leucine` | float | OD600 on leucine as sole carbon source |
| `valine` | float | OD600 on valine as sole carbon source |
| `aspartate` | float | OD600 on aspartate as sole carbon source |
| `glutamate` | float | OD600 on glutamate as sole carbon source |
| `phenylalanine` | float | OD600 on phenylalanine as sole carbon source |
| `tryptophan` | float | OD600 on tryptophan as sole carbon source |
| `lysine` | float | OD600 on lysine as sole carbon source |
| `histidine` | float | OD600 on histidine as sole carbon source |
| `arginine` | float | OD600 on arginine as sole carbon source |
| `ornithine` | float | OD600 on ornithine as sole carbon source |
| `cystein` | float | OD600 on cysteine as sole carbon source |
| `methionine` | float | OD600 on methionine as sole carbon source |
| `domain` | string | Taxonomic domain (e.g., Bacteria) |
| `phylum` | string | Taxonomic phylum (e.g., Pseudomonadota, Bacillota) |
| `class` | string | Taxonomic class |
| `order` | string | Taxonomic order |
| `family` | string | Taxonomic family |
| `genus` | string | Taxonomic genus |
| `species` | string | Full species name from GTDB taxonomy |
| `closest_genome_reference` | string | NCBI RefSeq accession of closest reference genome |
| `closest_genome_ani` | float | Average nucleotide identity to closest reference (%) |
| `completeness_checkm2` | float | Genome completeness from CheckM2 (%) |
| `contamination_checkm2` | float | Genome contamination from CheckM2 (%) |
| `genome_size_mb` | float | Assembled genome size in megabases |
| `gc_content` | float | GC content of the genome (fraction) |
| `total_coding_sequences` | float | Total number of predicted coding sequences |
| `strain_group` | float/string | Strain group identifier (for P. aeruginosa) |
| `representative` | string | Representative isolate flag within strain group |
| `best_pct_inhibition` | float | Best (maximum) percent inhibition of PA14 across all conditions |
| `mean_pct_inhibition_all` | float | Mean percent inhibition of PA14 across all tested conditions |
| `n_conditions` | float | Number of experimental conditions in inhibition assay |
| `has_inhibition` | boolean | Whether this isolate has planktonic inhibition data |
| `has_growth_curves` | boolean | Whether this isolate has growth kinetic time-series data |
| `metabolic_overlap_pa14` | float | Weighted metabolic overlap score with PA14 carbon profile (0-1) |

---

## growth_parameters.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB02 — `02_growth_kinetics.ipynb` |
| **Rows** | 1,352 |
| **Description** | Fitted growth curve parameters for each isolate-substrate combination. Extracted from logistic model fits to OD time-series data (676,000 curve points across 32 isolates). |

| Column | Type | Description |
|--------|------|-------------|
| `asma_id` | string | Unique isolate identifier |
| `condition` | string | Carbon source / substrate name (e.g., Alanine, Glucose) |
| `K` | float | Carrying capacity — maximum OD from logistic fit |
| `mu_max` | float | Maximum specific growth rate (OD/hour) |
| `lag` | float | Lag phase duration (hours) before exponential growth begins |
| `auc` | float | Area under the growth curve (integrated OD over time) |
| `assay` | string | Assay type (e.g., "Single carbon") |

---

## kinetic_advantage.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB02 — `02_growth_kinetics.ipynb` |
| **Rows** | 654 |
| **Description** | Per-substrate kinetic advantage of each commensal isolate relative to PA14. Ratios >1 indicate the commensal outperforms PA14 on that metric; <1 indicates PA14 advantage. |

| Column | Type | Description |
|--------|------|-------------|
| `asma_id` | string | Unique isolate identifier |
| `condition` | string | Carbon source / substrate name |
| `mu_max_comm` | float | Commensal maximum growth rate on this substrate |
| `mu_max_pa14` | float | PA14 maximum growth rate on this substrate |
| `K_comm` | float | Commensal carrying capacity on this substrate |
| `K_pa14` | float | PA14 carrying capacity on this substrate |
| `lag_comm` | float | Commensal lag phase duration (hours) |
| `lag_pa14` | float | PA14 lag phase duration (hours) |
| `rate_advantage` | float | Ratio of commensal to PA14 growth rate (mu_max_comm / mu_max_pa14) |
| `lag_advantage` | float | Difference in lag time (lag_pa14 - lag_comm); positive = commensal starts first |
| `capacity_advantage` | float | Ratio of commensal to PA14 carrying capacity (K_comm / K_pa14) |
| `auc_advantage` | float | Ratio of commensal to PA14 area under curve (auc_comm / auc_pa14) |
| `species` | string | Species name of the commensal isolate |
| `genus` | string | Genus name of the commensal isolate |

---

## isolate_kinetic_summary.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB02 — `02_growth_kinetics.ipynb` |
| **Rows** | 31 |
| **Description** | Per-isolate summary of kinetic advantage metrics, averaged across all tested substrates. One row per commensal isolate with growth curve data. |

| Column | Type | Description |
|--------|------|-------------|
| `asma_id` | string | Unique isolate identifier |
| `mean_rate_advantage` | float | Mean growth rate advantage across all substrates (ratio vs PA14) |
| `mean_lag_advantage` | float | Mean lag time advantage across all substrates (hours; positive = commensal starts first) |
| `mean_auc_advantage` | float | Mean AUC advantage across all substrates (ratio vs PA14) |
| `n_faster` | integer | Number of substrates on which the commensal has a higher growth rate than PA14 |
| `n_substrates` | integer | Total number of substrates tested for this isolate |
| `species` | string | Species name of the commensal isolate |

---

## single_isolate_scores.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB03 — `03_explaining_inhibition.ipynb` |
| **Rows** | 429 |
| **Description** | Per-isolate composite scoring table combining metabolic, inhibition, and safety information. Extends isolate_master with normalized scores for formulation optimization. One row per isolate. |

| Column | Type | Description |
|--------|------|-------------|
| `asma_id` | string | Unique isolate identifier |
| `no_carbon` through `methionine` | float | OD600 values for each of 21 carbon sources (same as isolate_master) |
| `domain` through `species` | string | Full taxonomic lineage (same as isolate_master) |
| `closest_genome_reference` | string | NCBI RefSeq accession of closest reference genome |
| `closest_genome_ani` | float | ANI to closest reference (%) |
| `completeness_checkm2` | float | CheckM2 completeness (%) |
| `contamination_checkm2` | float | CheckM2 contamination (%) |
| `genome_size_mb` | float | Genome size in megabases |
| `gc_content` | float | GC content (fraction) |
| `total_coding_sequences` | float | Number of predicted CDS |
| `strain_group` | float/string | Strain group identifier |
| `representative` | string | Representative isolate flag |
| `best_pct_inhibition` | float | Best percent inhibition of PA14 |
| `mean_pct_inhibition_all` | float | Mean percent inhibition across conditions |
| `n_conditions` | float | Number of inhibition assay conditions |
| `has_inhibition` | boolean | Whether isolate has inhibition data |
| `has_growth_curves` | boolean | Whether isolate has growth curve data |
| `metabolic_overlap_pa14` | float | Weighted metabolic overlap with PA14 (0-1) |
| `metabolic_score` | float | Normalized metabolic competition score (0-1) |
| `inhibition_score` | float | Normalized inhibition score (0-1) |
| `is_safe` | boolean | Whether the isolate passes safety filters |
| `composite_score` | float | Weighted composite of metabolic and inhibition scores |

---

## species_engraftability.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB04 — `04_patient_ecology.ipynb` |
| **Rows** | 134 |
| **Description** | Species-level engraftability scores derived from paired metagenomic (DNA) and metatranscriptomic (RNA) data across 175 CF/NCFB patient samples. Measures how prevalent and transcriptionally active each species is in patient airways. |

| Column | Type | Description |
|--------|------|-------------|
| `species` | string | Species name (GTDB taxonomy) |
| `prevalence_metag` | float | Fraction of patient metagenome samples in which the species is detected |
| `prevalence_metars` | float | Fraction of patient metatranscriptome samples in which the species is detected |
| `mean_cpm_metag` | float | Mean counts per million in metagenomic samples |
| `mean_cpm_metars` | float | Mean counts per million in metatranscriptomic samples |
| `activity_ratio` | float | Transcriptional engagement ratio (mean_cpm_metars / mean_cpm_metag) |
| `engraftability` | float | Composite engraftability score = prevalence x log(activity_ratio) |
| `is_safe` | boolean | Whether the species passes FDA safety filters |

---

## formulations_ranked.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB05 — `05_formulation_optimization.ipynb` |
| **Rows** | 22,389 |
| **Description** | All evaluated formulations (k=1 to 5 organisms) ranked by composite score under permissive safety filters. Includes niche coverage, complementarity, inhibition, and engraftability metrics. |

| Column | Type | Description |
|--------|------|-------------|
| `isolates` | string | Comma- or plus-delimited list of isolate IDs in the formulation |
| `k` | integer | Number of organisms in the formulation (1-5) |
| `niche_coverage` | float | Fraction of PA14-preferred substrates covered by at least one member (0-1) |
| `complementarity` | float | Metabolic dissimilarity among formulation members (1 = maximally complementary) |
| `mean_inhibition` | float | Mean percent inhibition of PA14 across formulation members |
| `geo_engraftability` | float | Geometric mean engraftability score across formulation members |
| `composite_score` | float | Weighted multi-criterion composite score |
| `species` | string | Species names of formulation members |

---

## formulations_strict_safety.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB05b — `05b_formulation_strict_safety.ipynb` |
| **Rows** | 146,379 |
| **Description** | All evaluated formulations ranked by composite score under strict safety filters (excluding all Pseudomonas, Enterobacteriaceae, and Staphylococcus). Includes exhaustive k=3 enumeration of all C(97,3) valid triples. Same schema as formulations_ranked.tsv. |

| Column | Type | Description |
|--------|------|-------------|
| `isolates` | string | Comma- or plus-delimited list of isolate IDs in the formulation |
| `k` | integer | Number of organisms in the formulation (1-5) |
| `niche_coverage` | float | Fraction of PA14-preferred substrates covered by at least one member (0-1) |
| `complementarity` | float | Metabolic dissimilarity among formulation members (1 = maximally complementary) |
| `mean_inhibition` | float | Mean percent inhibition of PA14 across formulation members |
| `geo_engraftability` | float | Geometric mean engraftability score across formulation members |
| `composite_score` | float | Weighted multi-criterion composite score |
| `species` | string | Species names of formulation members |

---

## prebiotic_pairings.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB06 — `06_prebiotic_pairing.ipynb` |
| **Rows** | 75 |
| **Description** | Top formulation members paired with candidate prebiotic substrates. Quantifies which substrates selectively benefit each commensal species relative to PA14, for formulations at various k sizes. |

| Column | Type | Description |
|--------|------|-------------|
| `formulation_k` | integer | Formulation size (k) from which the species was drawn |
| `formulation_score` | float | Composite score of the parent formulation |
| `species` | string | Commensal species name |
| `prebiotic` | string | Carbon source substrate being evaluated as prebiotic |
| `member_growth_on_prebiotic` | float | OD600 of the commensal on this substrate |
| `pa14_growth_on_prebiotic` | float | OD600 of PA14 on this substrate |
| `selectivity` | float | Selectivity ratio; higher = substrate favors commensal over PA14 |
| `prebiotic_advantage` | float | Absolute growth advantage (member OD - PA14 OD); positive = commensal grows more |

---

## carbon_selectivity.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB06 — `06_prebiotic_pairing.ipynb` |
| **Rows** | 20 |
| **Description** | Per-substrate selectivity analysis comparing PA14 growth to mean commensal growth across all 20 amino acid and sugar substrates. Identifies whether any substrate selectively feeds commensals over PA14. |

| Column | Type | Description |
|--------|------|-------------|
| *(index, unnamed)* | string | Substrate name (e.g., cystein, proline, glucose) |
| `pa14_od` | float | PA14 OD600 on this substrate |
| `commensal_mean_od` | float | Mean OD600 across all commensal isolates on this substrate |
| `selectivity_ratio` | float | Ratio indicating relative commensal advantage; values <1 mean PA14 outgrows commensals |
| `pa14_can_use` | boolean | Whether PA14 shows meaningful growth on this substrate (True/False) |
| `commensal_fraction_using` | float | Fraction of commensal isolates that show growth on this substrate |

---

## pangenome_conservation.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB07 — `07_pangenome_conservation.ipynb` |
| **Rows** | 400 |
| **Description** | GapMind metabolic pathway conservation across pangenome genomes for the 5 core formulation species. Quantifies how reliably each pathway is present across all available genomes per species, validating that measured metabolic capabilities are species-level traits. |

| Column | Type | Description |
|--------|------|-------------|
| `pathway` | string | GapMind metabolic pathway name (e.g., gly, leu, phe, chorismate, pro) |
| `metabolic_category` | string | Pathway category: "aa" (amino acid) or "carbon" |
| `n_genomes` | integer | Number of genomes examined for this pathway and species |
| `frac_complete` | float | Fraction of genomes with pathway scored as complete (0-1) |
| `frac_functional` | float | Fraction of genomes with pathway scored as functional (complete or partial) |
| `mean_score` | float | Mean GapMind pathway score across genomes (0-5 scale) |
| `species` | string | Species name (one of the 5 core formulation species) |
| `clade` | string | GTDB clade identifier for this species |

---

## isolation_sources.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB07 — `07_pangenome_conservation.ipynb` |
| **Rows** | 443 |
| **Description** | Environmental/clinical isolation source metadata for pangenome genomes of the 5 core formulation species. Used to assess lung tropism — whether each species is naturally found in respiratory environments. |

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | GTDB genome accession (e.g., GB_GCA_018373235.1) |
| `ncbi_biosample_id` | string | NCBI BioSample accession |
| `harmonized_name` | string | Standardized metadata field name (e.g., "isolation_source") |
| `content` | string | Free-text isolation source description (e.g., "infant feces", "respiratory", "bronchial washing") |
| `species` | string | Species name |
| `clade` | string | GTDB clade identifier |
| `category` | string | Harmonized source category: Lung/Respiratory, Oral, Other Clinical, Environmental, Other |

---

## lung_adaptation_signatures.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB07 — `07_pangenome_conservation.ipynb` |
| **Rows** | 15,760 |
| **Description** | Per-genome, per-pathway GapMind scores with lung/non-lung annotation. Used to identify metabolic pathway enrichment or depletion in lung-adapted strains compared to non-lung strains of the same species. |

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | Genome accession (prefix-stripped, e.g., GCF_007667085.1) |
| `pathway` | string | GapMind metabolic pathway name |
| `metabolic_category` | string | Pathway category: "carbon" or "aa" |
| `best_score` | integer | Best GapMind pathway score for this genome (0-5) |
| `is_lung` | boolean | Whether this genome was isolated from a lung/respiratory source |
| `species` | string | Species name |

---

## pairwise_synergy.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB08 — `08_interaction_modeling.ipynb` |
| **Rows** | 8 |
| **Description** | Pairwise interaction results from co-culture competition assays. Tests whether pairs of commensal isolates synergize, antagonize, or act additively when co-inoculated against PA14 at different cell densities. |

| Column | Type | Description |
|--------|------|-------------|
| `isolate_a` | string | First isolate ASMA ID in the pair |
| `isolate_b` | string | Second isolate ASMA ID in the pair |
| `od` | float | Total inoculation optical density (e.g., 0.0001, 0.001) |
| `pair_inh` | float | Percent inhibition of PA14 by the pair co-culture |
| `inh_a` | float | Percent inhibition by isolate A alone (at same density) |
| `inh_b` | float | Percent inhibition by isolate B alone (may be empty if not measured) |
| `expected_max` | float | Expected pair inhibition assuming max-of-singles model |
| `expected_mean` | float | Expected pair inhibition assuming mean-of-singles model |
| `synergy_vs_max` | float | Synergy score vs max model (pair_inh - expected_max); positive = synergistic |
| `synergy_vs_mean` | float | Synergy score vs mean model (pair_inh - expected_mean); positive = synergistic |
| `interaction_class` | string | Classified as "Synergistic", "Additive", or "Antagonistic" |

---

## gapmind_pathway_comparison.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB09 — `09_genomic_carbon_extension.ipynb` |
| **Rows** | 80 |
| **Description** | GapMind pathway completeness comparison between the 5 core commensal species and PA14. Identifies pathways complete in commensals but absent in PA14 — candidate genomic prebiotics. One row per pathway. |

| Column | Type | Description |
|--------|------|-------------|
| `pathway` | string | GapMind metabolic pathway name |
| `Gemella sanguinis` | float | Pathway completeness score for G. sanguinis (0-1) |
| `Micrococcus luteus` | float | Pathway completeness score for M. luteus (0-1) |
| `Neisseria mucosa` | float | Pathway completeness score for N. mucosa (0-1) |
| `Pseudomonas aeruginosa` | float | Pathway completeness score for P. aeruginosa (0-1) |
| `Rothia dentocariosa` | float | Pathway completeness score for R. dentocariosa (0-1) |
| `Streptococcus salivarius` | float | Pathway completeness score for S. salivarius (0-1) |
| `max_commensal` | float | Maximum completeness score among the 5 commensal species |
| `n_commensals_complete` | integer | Number of commensal species with the pathway scored as complete |
| `pa_complete` | float | PA14 pathway completeness score |
| `selectivity` | float | Difference: max_commensal - pa_complete; positive = commensal-selective |

---

## kegg_expression_comparison.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB09 — `09_genomic_carbon_extension.ipynb` |
| **Rows** | 252 |
| **Description** | KEGG pathway expression comparison between commensals and PA in patient metatranscriptomes. Identifies pathways with differential in vivo expression, supporting genomic prebiotic predictions with transcriptomic evidence. |

| Column | Type | Description |
|--------|------|-------------|
| `pathway` | string | KEGG pathway name and ID |
| `commensal_cpm` | float | Mean counts per million expression for commensal species |
| `pa_cpm` | float | Mean counts per million expression for P. aeruginosa |
| `selectivity` | float | Difference: commensal_cpm - pa_cpm; positive = commensal-enriched |
| `ratio` | float | Ratio of commensal to total expression (commensal_cpm / (commensal_cpm + pa_cpm)) |

---

## pa_lung_vs_nonlung_pathways.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB10 — `10_pa_lung_adaptation.ipynb` |
| **Rows** | 80 |
| **Description** | Comparison of GapMind pathway completeness between lung-derived and non-lung P. aeruginosa genomes. Identifies metabolic pathways that are gained or lost during lung adaptation — evidence of metabolic streamlining in the airway. |

| Column | Type | Description |
|--------|------|-------------|
| `pathway` | string | GapMind metabolic pathway name |
| `lung_mean` | float | Mean GapMind pathway score across lung/respiratory PA genomes |
| `nonlung_mean` | float | Mean GapMind pathway score across non-lung PA genomes |
| `diff` | float | Difference: lung_mean - nonlung_mean; negative = lost in lung PA |
| `p_value` | float | Statistical significance of the difference (Mann-Whitney U test) |
| `n_lung` | integer | Number of lung PA genomes in the comparison |
| `n_nonlung` | integer | Number of non-lung PA genomes in the comparison |
| `q_value` | float | FDR-corrected p-value (Benjamini-Hochberg) |

---

## pa_sick_vs_stable_pathways.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB10 — `10_pa_lung_adaptation.ipynb` |
| **Rows** | 207 |
| **Description** | KEGG pathway expression comparison between PA in acute exacerbation ("sick") vs clinically stable CF patients. Reveals which pathways PA up- or down-regulates during acute episodes, informing when competitive exclusion may be most effective. |

| Column | Type | Description |
|--------|------|-------------|
| `pathway` | string | KEGG pathway name and description |
| `sick_cpm` | float | Mean counts per million PA expression during acute exacerbation |
| `stable_cpm` | float | Mean counts per million PA expression during clinically stable periods |
| `log2fc` | float | Log2 fold change (sick / stable); negative = downregulated in sick |
| `total_cpm` | float | Total expression across both conditions (sick_cpm + stable_cpm) |

---

## pa_genome_sources.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB10 — `10_pa_lung_adaptation.ipynb` |
| **Rows** | 5,199 |
| **Description** | Isolation source metadata for all P. aeruginosa genomes in the BERDL pangenome with available metadata. Used to classify PA genomes as lung/respiratory vs other sources for the lung adaptation analysis. |

| Column | Type | Description |
|--------|------|-------------|
| `genome_id` | string | GTDB genome accession (e.g., RS_GCF_015265725.1) |
| `isolation_source` | string | Free-text isolation source description from NCBI (e.g., "blood", "trachea", "sputum") |
| `category` | string | Harmonized source category: Lung/Respiratory, CF, Other Clinical, Environmental, Other |

---

## pa_target_robustness.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB10 — `10_pa_lung_adaptation.ipynb` |
| **Rows** | 22 |
| **Description** | Conservation of formulation-targeted metabolic pathways across 1,796 lung P. aeruginosa genomes. Validates that the amino acid catabolic pathways targeted by the formulation are invariant across PA lung variants. |

| Column | Type | Description |
|--------|------|-------------|
| `pathway` | string | GapMind metabolic pathway name (amino acid or carbon source) |
| `n_genomes` | integer | Number of lung PA genomes assessed (1,796) |
| `pct_complete` | float | Percentage of genomes with pathway scored as complete |
| `pct_partial` | float | Percentage of genomes with pathway scored as partial |
| `pct_absent` | float | Percentage of genomes with pathway scored as absent |
| `mean_score` | float | Mean GapMind pathway score (0-5 scale) |
| `std_score` | float | Standard deviation of pathway scores across genomes |
| `type` | string | Pathway classification: "AA catabolism" or "Carbon source" |

---

## codon_usage_bias.tsv

| Property | Value |
|----------|-------|
| **Source Notebook** | NB12 — `12_codon_usage_bias.ipynb` |
| **Rows** | 6 |
| **Description** | Codon usage bias (CUB) analysis of ribosomal protein genes for PA14 and the 5 core commensal species. Higher CUB scores can indicate translational optimization for rapid growth, but cross-species comparisons are confounded by GC content variation (31-73%). |

| Column | Type | Description |
|--------|------|-------------|
| `n_codons` | integer | Total number of codons analyzed in ribosomal protein genes |
| `gc3` | float | GC content at third codon position (wobble position) |
| `cub_score` | float | Codon usage bias score (effective number of codons metric) |
| `species` | string | Species name (P. aeruginosa or one of 5 core commensals) |
| `n_genes` | integer | Number of ribosomal protein genes analyzed |
| `genome_size_mb` | float | Mean genome size in megabases (averaged across available genomes) |
| `total_cds` | float | Mean total coding sequences (averaged across available genomes) |
