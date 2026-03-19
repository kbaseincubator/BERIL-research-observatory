# Research Plan: CF Protective Microbiome Formulation Design

## Research Question

Can we build a multi-criterion framework that explains measured *P. aeruginosa* PA14 inhibition from metabolic competition, growth kinetics, and patient ecology data, and use it to design and rank optimal 1–5 organism commensal formulations for competitive exclusion in CF lungs?

## Hypotheses

- **H0**: PA14 inhibition by commensals is not predictable from metabolic overlap, growth kinetics, or patient ecology — it is driven entirely by strain-specific direct antagonism (bacteriocins, contact-dependent killing, etc.).
- **H1 (Metabolic competition)**: Isolates whose carbon utilization profiles overlap more with PA14's preferred substrates (proline, histidine, ornithine, glutamate, aspartate, arginine) show greater PA14 inhibition. Growth *rate* on shared substrates is a stronger predictor than growth *yield*.
- **H2 (Complementary coverage)**: Multi-organism formulations whose members collectively cover PA14's carbon niche while minimizing internal metabolic overlap outperform random or redundant combinations of the same size.
- **H3 (Engraftability)**: Species that are prevalent (>50% of patients) and metabolically active (high metaRS/metaG CPM ratio) in patient microbiomes are better formulation candidates than rare or dormant species.
- **H4 (Prebiotic boost)**: Carbon sources that support commensal growth but not PA14 (candidates: threonine, methionine, serine, glycine — all <0.07 OD for PA14) can serve as selective prebiotics, providing a biomass advantage before niche competition begins.

## Literature Context

*To be populated by /literature-review — key topics:*
- Competitive exclusion in CF lung microbiome (Filkins & O'Toole 2015, Caverly et al. 2019)
- Metabolic niche partitioning in polymicrobial communities
- Probiotic approaches for respiratory infections
- *P. aeruginosa* amino acid catabolism (SCFM composition, Palmer et al. 2007)
- RB-TnSeq essentiality under nutrient limitation (Fitness Browser methodology)
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

### Notebook 07: Genomic Context & Extension (if time permits)

**Goal**: Extend metabolic predictions beyond the 22 tested carbon sources using genomic data.

**Analysis**:
- Link isolate reference genomes (`dim_isolate.closest_genome_reference`) to pangenome GapMind pathways
- Compare GapMind predictions vs observed growth: how well do genomic predictions match lab data?
- For isolates lacking growth curves, use GapMind as a proxy for metabolic capability
- Explore PROTECT genomedepot annotations for top formulation candidates
- BacDive cross-validation for species with literature utilization data

**Expected output**: Extended metabolic predictions, GapMind vs observed concordance statistics

## Expected Outcomes

- **If H1 supported**: Metabolic overlap is a design principle — formulations can be rationally designed from carbon utilization data. Growth rate adds predictive power beyond yield.
- **If H0 not rejected**: Inhibition is dominated by direct antagonism — screen for bacteriocin/T6SS genes in genomic data, pivot to a genomics-first approach.
- **If H2 supported**: Complementary formulations outperform — the "eat their lunch" design theory is validated, and we have ranked formulations ready for mouse testing.
- **If H4 supported**: Specific prebiotics (likely among threonine, methionine, serine, glycine) provide selective advantage — synbiotic design is feasible.
- **Potential confounders**: Strain-specific effects within species, condition-dependent inhibition (gain/OD settings), growth medium differences between assays and lung environment.

## Revision History
- **v1** (2026-03-19): Initial plan — integrates 23 experimental tables with BERDL resources for multi-criterion formulation scoring

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931) — U.C. Berkeley / Lawrence Berkeley National Laboratory
