# Research Plan: CF Protective Microbiome Formulation Design

## Research Question

Can we build a multi-criterion framework that explains measured *P. aeruginosa* PA14 inhibition from metabolic competition, growth kinetics, and patient ecology data, and use it to design and rank optimal 1–5 organism commensal formulations for competitive exclusion in CF lungs?

## Hypotheses

- **H0**: PA14 inhibition by commensals is not predictable from metabolic overlap, growth kinetics, or patient ecology — it is driven entirely by strain-specific direct antagonism (bacteriocins, contact-dependent killing, etc.).
- **H1 (Metabolic competition)**: Isolates whose carbon utilization profiles overlap more with PA14's preferred substrates (proline, histidine, ornithine, glutamate, aspartate, arginine) show greater PA14 inhibition. Growth *rate* on shared substrates is a stronger predictor than growth *yield*.
- **H2 (Complementary coverage)**: Multi-organism formulations whose members collectively cover PA14's carbon niche while minimizing internal metabolic overlap outperform random or redundant combinations of the same size.
- **H3 (Engraftability)**: Species that are prevalent (>50% of patients) and metabolically active (high metaRS/metaG CPM ratio) in patient microbiomes are better formulation candidates than rare or dormant species.
- **H4 (Prebiotic boost)**: Carbon sources that support commensal growth but not PA14 (candidates: threonine, methionine, serine, glycine — all <0.07 OD for PA14) can serve as selective prebiotics, providing a biomass advantage before niche competition begins.
- **H5 (Pangenome conservation)**: The metabolic competition properties of candidate commensals are conserved across their species pangenomes (GapMind pathway predictions), making formulation designs robust to strain variation. Alternatively, lung-associated isolates may be metabolically distinct from other members of the same species — adaptations that can be identified and exploited.
- **H6 (Lung adaptation)**: Commensal species with lung/respiratory-associated genomes in the pangenome show metabolic or genomic signatures (e.g., amino acid catabolism, biofilm, oxidative stress response) distinct from non-lung members of the same species/genus, and our PROTECT isolates cluster with the lung-adapted subpopulation.

## Literature Context

- **CF sputum metabolism**: Palmer et al. (2005, 2007) established amino acids as PA's primary carbon sources in CF sputum and developed SCFM (synthetic CF sputum medium).
- **Commensal airway protection**: Rigauts et al. (2022) showed Rothia mucilaginosa suppresses NF-κB inflammation in CF airways; Stubbendieck et al. (2023) identified R. dentocariosa peptidoglycan endopeptidase for colonization resistance.
- **Community ecology in CF**: Widder et al. (2022) identified 8 pulmotypes; Rogers et al. (2015) demonstrated PA–H. influenzae competitive exclusion.
- **Probiotic precedent**: Anderson et al. (2017) systematic review of CF probiotic trials; S. salivarius BLIS K12 (Tagg et al. 2025; Burton et al. 2011).
- **Regulatory**: Dreher (2017) FDA/CBER framework for live biotherapeutic products.
- **Pangenome-guided design**: Shao et al. (2026) used pangenome analysis for Bifidobacterium probiotic design.
- FDA regulatory precedent for live biotherapeutic products (LBPs)

## Data Sources

### User Experimental Data (`~/protect/gold/`)

| Table | Rows | Role in Analysis |
|-------|------|------------------|
| `dim_isolate` | 4,949 | Isolate catalog: 211 species, genome quality, taxonomy, strain groups, representative flags |
| `dim_patient_sample` | 175 | Patient metadata: CF/NCFB diagnosis, clinical status (A–D), culture microbiology |
| `dict_patient_status_codes` | 7 | Status codes: A=acute untreated, B=acute treated, C=end treatment, D=stable |
| `fact_inhibition_scores` | 722 | **Outcome variable**: mean % PA14 inhibition per isolate (220 isolates, 91 species) |
| `fact_carbon_utilization` | 826 | Endpoint OD on 21 carbon sources for 430 isolates + reporters |
| `fact_growth_curves_fitted` | 676,000 | Time-series growth kinetics (OD fits) for 32 isolates × 22 conditions × ~193 cycles |
| `fact_growth_curves_clean` | 267,305 | Cleaned raw growth curves |
| `fact_growth_curve` | 17,346 | Growth curve summary/metadata |
| `fact_pairwise_interaction` | 826 | Pairwise interaction effects on carbon sources |
| `fact_inhibition_control` | 826 | Control growth on carbon sources |
| `fact_competition_assay` | 1,584 | Raw competition assay (RFU): 29 ASMA isolates vs PA14/KP/AB reporters |
| `fact_pa_competitors` | 140 | Metagenomics-derived PA competition scores (40 species × 22 patients) |
| `dim_candidate_prebiotics` | 431 | Prebiotic candidates: gene-level enrichment scores (35 species × 20 samples) |
| `fact_abundance_species` | 25,058 | Species abundance (counts) per sample |
| `fact_abundance_species_stratified` | 13.8M | Stratified species abundance (gene-level) |
| `fact_abundance_genus` / `_stratified` | 12.7M | Genus-level abundance |
| `fact_metag_cpm` | 9,916 | Species DNA abundance (CPM) across samples |
| `fact_metars_cpm` | 9,916 | Species RNA activity (CPM) across samples |
| `fact_kegg_pathway` | 559,326 | KEGG pathway abundance per species per sample |
| `fact_species_kegg_pathway_cpm` | 1.1M | Species × KEGG pathway × sample (CPM normalized) |
| `fact_species_kegg_wol_cpm` | 1.2M | Species × KEGG pathway × sample (WoL taxonomy) |
| `bridge_isolate_metagenomics` | 186 | Links isolate taxa → metagenomic features (genus/species match) |

### BERDL Databases

| Database | Tables Used | Purpose |
|----------|-------------|---------|
| `protect_genomedepot` | `browser_genome`, `browser_gene_sampled`, `browser_strain`, `browser_taxon` | Deep annotation of PROTECT isolate genomes |
| `kbase_ke_pangenome` | `gapmind_pathways`, `genome`, `eggnog_mapper_annotations`, `gene_cluster` | GapMind metabolic predictions for isolate reference genomes (extends beyond 22 tested substrates) |
| `phagefoundry_paeruginosa_genome_browser` | KEGG pathways, genes, operons | PA14/PAO1 genome annotation, metabolic pathway detail |
| `kescience_bacdive` | `metabolite_utilization`, `isolation`, `physiology` | External validation: literature-curated utilization data for related species |
| `kbase_msd_biochemistry` | `reaction`, `molecule` | Stoichiometric context for metabolic competition modeling |
| `kescience_fitnessbrowser` | `organism`, `genefitness`, `experiment` | Gene essentiality under defined carbon/nitrogen conditions (check for Pseudomonas) |

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| All `~/protect/gold/*.parquet` | Core experimental data | 30M total | Load directly via pandas/pyarrow |
| `protect_genomedepot.browser_genome` | Isolate genome metadata | ~hundreds | Filter by ASMA-linked accessions |
| `kbase_ke_pangenome.gapmind_pathways` | Metabolic predictions | 305M | Filter by genome_id for isolate reference genomes |
| `phagefoundry_paeruginosa_genome_browser.browser_kegg_pathway` | PA pathway detail | varies | Full scan (PA-specific DB) |
| `kescience_bacdive.metabolite_utilization` | External utilization data | 988K | Filter by species matching our isolates |

### Performance Plan
- **Tier**: Local pandas for user data + on-cluster Spark for BERDL
- **Estimated complexity**: Moderate (local data is small; BERDL queries are targeted)
- **Known pitfalls**: GapMind genome IDs lack RS_/GB_ prefix; BacDive metabolite utilization has 4 values not 2; protect_genomedepot schema introspection times out

## Analysis Plan

### Notebook 01: Data Integration & Exploratory Data Analysis

**Goal**: Load, merge, and characterize all experimental data. Build the audience's understanding of what goes in.

**EDA deliverables**:
- Isolate catalog: species distribution, genome quality, strain group structure
- Patient cohort: CF vs NCFB, status distribution, pathogen colonization patterns
- Inhibition landscape: distribution of % inhibition, by species, by gain/OD condition
- Carbon utilization heatmap: isolates × carbon sources, with PA14 highlighted
- Data overlap Venn: which isolates have inhibition + carbon util + growth curves + metagenomics

**Expected output**: Summary statistics, merged master table (`data/isolate_master.tsv`), quality-filtered analysis cohort

### Notebook 02: Growth Kinetics Analysis

**Goal**: Extract growth parameters from fitted curves and use them as predictive features.

**EDA deliverables**:
- Growth curve gallery: representative curves per isolate × carbon source
- Parameter extraction: lag time (λ), max growth rate (μ_max), carrying capacity (K) per isolate × condition
- Comparison: PA14 vs commensals — who grows faster on which substrates?
- Kinetic advantage score: for each carbon source, ratio of commensal μ_max to PA14 μ_max

**Analysis**:
- Fit logistic/Gompertz models to `fact_growth_curves_fitted` to extract λ, μ_max, K
- Compute per-substrate kinetic advantage vs PA14
- Correlate kinetic parameters with endpoint OD from `fact_carbon_utilization` — do they add information?

**Expected output**: `data/growth_parameters.tsv` (isolate × condition × {lag, rate, capacity})

### Notebook 03: Explaining PA14 Inhibition — Single Organisms

**Goal**: Test H1 — does metabolic overlap with PA14 predict inhibition?

**EDA deliverables**:
- Scatter: metabolic overlap score vs % inhibition
- Scatter: growth rate advantage on PA-preferred substrates vs % inhibition
- Taxonomy breakdown: inhibition distributions by genus/species
- Residual analysis: what inhibition remains after accounting for metabolic overlap?

**Analysis**:
- Define metabolic overlap score: weighted sum of commensal growth on PA14's top substrates (weight = PA14 OD on that substrate)
- Define kinetic advantage score: mean(commensal μ_max / PA14 μ_max) across shared substrates (for the 32 isolates with growth curves)
- Regression: inhibition ~ metabolic_overlap + kinetic_advantage + genus + interactions
- Variance decomposition: how much inhibition is explained by metabolism vs taxonomy vs residual (direct antagonism)?
- Identify isolates with high inhibition but LOW metabolic overlap → candidate direct antagonists

**Expected output**: Model coefficients, R², feature importance; `data/single_isolate_scores.tsv`

### Notebook 04: Patient Ecology & Engraftability

**Goal**: Test H3 — which species are ubiquitous, active, and safe?

**EDA deliverables**:
- Species prevalence heatmap across patients (metaG)
- Activity ratio: metaRS CPM / metaG CPM per species — who is transcriptionally active vs dormant?
- Patient status effects: does pathogen load or clinical status change commensal composition?
- Bridge validation: how many isolate species map to metagenomic features?

**Analysis**:
- Compute per-species: prevalence (fraction of patients), mean abundance (CPM), activity ratio (metaRS/metaG)
- Define "engraftability score": prevalence × activity_ratio (species that are both common and active)
- Apply FDA safety filter: flag known opportunistic pathogens (Serratia, Citrobacter, Klebsiella, Enterococcus, etc.)
- Cross-reference `fact_pa_competitors` with engraftability — are the best metagenomics-derived PA competitors also engraftable?

**Expected output**: `data/species_engraftability.tsv`, safety-flagged species list

### Notebook 05: Formulation Optimization

**Goal**: Test H2 — design and rank optimal 1–5 organism formulations.

**EDA deliverables**:
- PA14 carbon niche visualization: which substrates, how much growth
- Candidate pool summary: after safety + engraftability filters, how many isolates remain?
- Example formulation walkthrough: show how scoring works for a specific 3-organism combo

**Analysis**:
- Multi-objective scoring function per formulation F = {isolate₁, ..., isolateₖ} (k ∈ 1..5):
  - **PA niche coverage**: fraction of PA14's usable carbon sources covered by at least one member
  - **Growth rate advantage**: mean kinetic advantage over PA14 on covered substrates
  - **Internal complementarity**: 1 − mean pairwise metabolic overlap among members
  - **Engraftability**: geometric mean of member engraftability scores
  - **Measured inhibition**: mean max % inhibition (where available)
  - **Safety**: binary — all members pass FDA filter
- Optimization approach:
  - For k=1: rank all safe isolates by combined score
  - For k=2..5: greedy set cover (add isolate that most improves the formulation) + local search
  - Verify top formulations against exhaustive enumeration for small candidate pools
- Sensitivity analysis: vary criterion weights, check stability of top formulations

**Expected output**: `data/formulations_ranked.tsv`, top 10 per size with full score breakdowns

### Notebook 06: Prebiotic Pairing

**Goal**: Test H4 — identify prebiotics that selectively boost probiotics over PA14.

**EDA deliverables**:
- Carbon source selectivity plot: commensal growth vs PA14 growth per substrate
- Prebiotic candidate matrix: which substrates benefit which formulation members?
- Cross-reference with `dim_candidate_prebiotics` enrichment scores

**Analysis**:
- For each carbon source, compute selectivity ratio: mean commensal OD / PA14 OD
- Best prebiotic candidates: high selectivity AND high absolute commensal growth
- For each top formulation from NB05, identify the best 1–2 prebiotics
- Check if prebiotic substrates overlap with KEGG pathways active in patient metagenomes (ecological plausibility)

**Expected output**: `data/prebiotic_pairings.tsv`, formulation + prebiotic recommendations

### Notebook 07: Pangenome Conservation & Lung Adaptation

**Goal**: Test H5 and H6 — are the metabolic properties of our commensals species-typical or lung-specific? Are there lung-associated genomes in the pangenome that reveal adaptation signatures?

**EDA deliverables**:
- Species-level GapMind pathway completeness for candidate commensal species
- Within-species pathway variation: how conserved are carbon/amino acid utilization pathways?
- Environmental source breakdown: how many genomes in each commensal's species clade are lung/respiratory-associated?
- Comparison: lung-associated vs non-lung genomes on metabolic pathway profiles

**Analysis**:
- Link isolate reference genomes (`dim_isolate.closest_genome_reference`) to pangenome via `kbase_ke_pangenome.genome` (strip RS_/GB_ prefix as needed)
- For each candidate commensal species:
  - Extract GapMind pathway predictions for ALL genomes in the species clade
  - Compute pathway conservation: fraction of genomes with complete/likely_complete for each pathway
  - Compare our PROTECT isolate's predicted pathways to the species distribution
- Query `ncbi_env` and `gtdb_metadata` for isolation source of genomes in commensal species clades
  - Identify lung/respiratory/sputum/oral isolates vs soil/water/gut/other
  - If lung genomes exist: compare their GapMind profiles, eggNOG annotations, and gene cluster content to non-lung genomes
  - Look for enriched COG categories, specific KEGG pathways, or accessory gene clusters unique to lung variants
- GapMind vs observed growth concordance: how well do pangenome predictions match our lab carbon utilization data?
- For isolates lacking growth curves, use GapMind as a proxy for metabolic capability

**Expected output**: `data/pangenome_conservation.tsv`, `data/lung_adaptation_signatures.tsv`, GapMind concordance statistics

### Notebook 05b: Formulation Optimization — Strict FDA Safety Filter

**Goal**: Re-run optimization with strict safety filter excluding all Pseudomonas, Enterobacteriaceae, and Staphylococcus. Compare permissive vs strict to show staged design decisions. Added species uniqueness constraint and scoring weight sensitivity analysis.

**Expected output**: `data/formulations_strict_safety.tsv`

### Notebook 08: Interaction Modeling

**Goal**: Detect and classify pairwise interactions (synergistic, additive, antagonistic) between consortium members from the competition assay data. Assess whether the additive scoring assumption in NB05 is valid.

**Key finding**: `fact_pairwise_interaction` proved identical to `fact_carbon_utilization`, limiting per-substrate co-culture analysis. RFU-based competition assay shows *N. mucosa* pairs are near-additive (mean synergy −5.8%, but +5.3% for N. mucosa specifically).

**Expected output**: `data/pairwise_synergy.tsv`

### Notebook 09: Genomic Carbon Source Extension

**Goal**: Identify prebiotic candidates beyond the 22 tested substrates using GapMind pathway predictions (80 pathways) and patient metatranscriptomics (220 KEGG pathways). Find carbon sources where commensals have complete pathways but PA14 does not.

**Key finding**: 6 sugar alcohol/pentose pathways (xylitol, myoinositol, xylose, arabinose, fucose, rhamnose) are 100% complete in commensals and 0% in PA14 — strong prebiotic candidates.

**Expected output**: `data/gapmind_pathway_comparison.tsv`, `data/kegg_expression_comparison.tsv`

### Notebook 10: PA Lung Adaptation

**Goal**: Characterize what makes lung/airway PA variants metabolically distinct from non-lung PA. Identify PA metabolic pathways associated with disease severity from patient metatranscriptomics.

**Key finding**: Lung PA loses sugar utilization pathways (sorbitol, mannitol, gluconate) — metabolic streamlining toward amino acid dependence. During acute exacerbation, PA massively downregulates biosynthetic pathways and upregulates phosphate transport.

**Expected output**: `data/pa_lung_vs_nonlung_pathways.tsv`, `data/pa_sick_vs_stable_pathways.tsv`, `data/pa_genome_sources.tsv`

### Notebook 11: Within-Lung PA Diversity & Formulation Robustness

**Goal**: Assess whether PA metabolic variation among lung isolates could cause differential formulation responses. Test whether amino acid catabolic pathways (our formulation targets) are invariant or variable across lung PA.

**Key finding**: Amino acid pathways 97.4% conserved across 1,796 lung PA genomes. Main variation (PC1=79%) is in carbon source pathways NOT targeted by our formulation. CF vs non-CF lung PA show zero amino acid differences. Formulation predicted equally effective across PA variants.

**Expected output**: `data/pa_target_robustness.tsv`

### Notebook 12: Genomic Growth Rate Prediction

**Goal**: Compute codon usage bias (CUB) of ribosomal proteins as a proxy for maximum growth rate potential. Compare PA vs formulation commensals.

**Key finding**: Cross-species CUB comparison is confounded by GC content variation (31–73%) and cannot reliably predict growth rate differences. Lab growth data remains ground truth. Within-PA strain variation (15 groups, 6.1–7.4 Mb) reflects accessory genome content affecting virulence/persistence, not amino acid growth rate.

**Expected output**: `data/codon_usage_bias.tsv`

## Outcomes (as observed)

- **H1 supported (partial)**: Metabolic overlap predicts inhibition (r=0.384, p=2.3e-6, R²=0.274; CV R²=0.145). Metabolic competition is a real mechanism but explains only 15–27% of variance. The strongest inhibitors combine metabolic competition with direct antagonism.
- **H0 partially rejected**: Direct antagonism contributes (genus adds 8.6% R²) but is not the sole mechanism. Dual-mechanism species (metabolic + direct) are the best formulation candidates.
- **H2 supported**: k=3 formulation achieves 100% PA niche coverage. Five-species core (*N. mucosa, S. salivarius, M. luteus, R. dentocariosa, G. sanguinis*) is robust across scoring weight variations.
- **H4 rejected for amino acids, supported genomically for sugar alcohols**: PA14 outgrows all commensals on all 22 tested substrates. GapMind identifies 6 untested sugar alcohol/pentose pathways (xylitol, myoinositol, xylose, arabinose, fucose, rhamnose) where commensals are complete and PA is absent.
- **H5 strongly supported**: 4/5 core species show >95% amino acid pathway conservation across 15–295 pangenome genomes. Formulation design is robust to strain variation.
- **H6 supported qualitatively**: *R. dentocariosa* (38%) and *N. mucosa* (33%) are disproportionately lung-associated. Lung PA shows metabolic streamlining (losing sugar pathways). 21 lung genomes found across commensal species.
- **Additional finding — PA formulation robustness**: PA amino acid catabolism is 97.4% conserved across 1,796 lung genomes. CF vs non-CF PA show zero amino acid differences. One formulation should work across PA variants. PA strain variation affects virulence/persistence, not the metabolic competition targets.
- **Confounders confirmed**: Planktonic assay limitations, sparse pairwise interaction data (8 comparisons), CUB confounded by GC content, `fact_pairwise_interaction` identical to `fact_carbon_utilization`.

## Revision History
- **v1** (2026-03-19): Initial plan — 7 notebooks integrating 23 experimental tables with BERDL for multi-criterion formulation scoring
- **v2** (2026-03-19): Added H5/H6 (pangenome conservation + lung adaptation). NB07 dedicated to pangenome, NB08 for genomic extension.
- **v3** (2026-03-19): NB01–NB07 executed. NB05b added (strict FDA safety filter with staged comparison). Key result: metabolic overlap r=0.384 (R²=0.274). Five-species FDA-safe formulation identified.
- **v4** (2026-03-19): NB08 repurposed from BacDive validation to interaction modeling (pairwise synergy/antagonism). NB09 added for genomic carbon source extension — discovered 6 sugar alcohol prebiotic candidates. NB10 added for PA lung adaptation analysis (6,760 PA genomes). NB11 added for within-lung PA diversity and formulation robustness (97.4% AA pathway conservation). NB12 added for codon usage bias growth rate prediction.
- **v5** (2026-03-19): Corrected CUB interpretation (GC-confounded). Corrected PA strain variation interpretation (accessory genome affects virulence not amino acid growth rate). Lab growth data confirmed as ground truth. Expected Outcomes updated to observed outcomes.

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931) — U.C. Berkeley / Lawrence Berkeley National Laboratory
