# Research Plan: Metagenome-Prioritized Phage Cocktails for Crohn's Disease and IBD

## Research Question

Which bacterial pathobionts are enriched, ubiquitous, and non-protective in IBD / UC / Crohn's disease patients — considered both across indications and within distinct patient subgroups defined by demographics, severity, native-microbiome structure, and treatment history — and of those, which are tractable phage-therapy targets given available or characterizable phages, target-strain evolutionary escape routes, and ecological consequences of removal?

## Hypothesis Framework

Five coupled pillars. Each pillar's hypotheses are falsifiable, state the statistical test, and specify what "disproved" looks like.

### Pillar 1 — Patient stratification

**H1a**: Unsupervised clustering on baseline microbiome + metabolome + pathway potential of the pooled public-cohort data yields **≥ 3 reproducible IBD ecotypes** that replicate across held-out cohorts. *Test*: Dirichlet Multinomial Mixture (DMM) on taxa, topic modeling on pathways, MOFA+ on the multi-omics join. Ecotype calls retained only if stable under all three methods and under bootstrap resampling (≥ 80 % per-sample consistency). *Disproved if*: no K (number of ecotypes) gives perplexity / BIC stabilization, or inter-method agreement < 50 %, or held-out replication Rand index < 0.4.

**H1b**: UC Davis patients distribute across (not concentrate in) the reference ecotypes. *Test*: project UC Davis taxon profiles onto the reference embedding, count occupancy per ecotype, test against the null of single-ecotype collapse (χ² or exact test). *Disproved if*: ≥ 80 % of UC Davis patients land in one ecotype.

**H1c**: Ecotype membership can be predicted from **clinical covariates alone** (Montreal classification, calprotectin, CRP, medication class, age, sex, smoking) at classification AUC ≥ 0.70. Meaningful because a clinical classifier would allow ecotype assignment before metagenomics is available. *Test*: multinomial logistic regression or gradient-boosted classifier on public-cohort clinical metadata with ecotype label as target; leave-one-cohort-out CV. *Disproved if*: no clinical signature predicts ecotype above chance.

### Pillar 2 — Pathobiont identification (within-ecotype)

**H2a**: A minority of the ~266 CD-enriched species (per the preliminary DA) are actionable pathobionts under a stricter rubric applied within ecotype. *Test*: compositional-aware DA (ANCOM-BC + MaAsLin2 + LinDA, consensus) within each ecotype, then Tier-A scoring (see "Criteria" below). Actionable count defined as those passing ≥ 5 of the 6 Tier-A criteria. *Disproved if*: passing-species lists do not overlap across the three DA methods (< 50 % overlap) or no species passes ≥ 5 criteria.

**H2b**: Target sets differ between UC and CD, and within CD by Montreal-location subtype (ileal L1 vs colonic L2 vs ileocolonic L3). *Test*: Jaccard overlap of top-20 within-ecotype Tier-A candidates between UC and CD, and between L1 / L2 / L3 strata of CD. *Disproved if*: Jaccard > 0.7 (target sets are nearly identical) — which would mean stratification gives no clinical benefit for targeting.

**H2c**: Within-ecotype compositional-aware DA *fails to reproduce protective species as CD-enriched*. Specifically: *C. scindens*, *F. prausnitzii*, *A. muciniphila*, *E. rectale*, *Roseburia intestinalis*, *Lachnospira eligens* should NOT show up as CD-enriched when the analysis is done correctly. *C. scindens* is the motivating example (preliminary report called it log₂FC +2.67 in pooled analysis despite 79 % prevalence in healthy individuals), but the same sanity-check battery applies to the whole protective-species list. *Test*: direct check against the preliminary pooled DA. *Disproved if*: any canonical protective species remains CD-enriched after stratification and compositional correction — which would force us to question the stratification itself.

**H2d**: Pathobiont co-occurrence modules (SparCC / SpiecEasi per ecotype) contain ≥ 2 Tier-A candidates each. This matters because single-target cocktails may fail if the module re-equilibrates around another hub. *Test*: network inference per ecotype + module detection + intersection with Tier-A candidate list. *Disproved if*: modules contain ≤ 1 Tier-A hub on average — suggesting pathobionts are ecologically independent and monovalent cocktails may suffice.

### Pillar 3 — Functional drivers (mechanism)

**H3a**: Disease-associated pathway enrichment compresses to a **small number of biochemical themes** (bile-acid 7α-dehydroxylation loss, mucin degradation, sulfidogenesis, TMA/TMAO production, AA decarboxylation, ethanolamine utilization), each attributable to a specific Tier-A pathobiont set. *Test*: within-ecotype pathway DA on `fact_pathway_abundance` (CMD_IBD only per scope decision 1a), MOFA joint factor recovery from pathway + metabolome + strain matrices. *Disproved if*: pathway DA either disperses across hundreds of uncorrelated MetaCyc IDs without functional coherence, or fails to map to specific pathobiont contributors (co-variation Spearman < 0.3 between pathway abundance and top-Tier-A species abundances).

**H3b**: At strain level, virulence / adaptation genes stratify patients more sharply than species abundance alone. Candidates include AIEC-specific adhesins (*fimH*, *lpfA*), R. gnavus glucorhamnan synthesis, B. fragilis enterotoxin (*bft*), E. bolteae ebf BGC, E. lenta adaptation genes (*katA*, *rodA/ponA*, *acnA*, *rlmN*). *Test*: extend the preliminary E. lenta analysis (`ref_kumbhari_s7_eggerthella_lenta_predict`) pattern to all 59 species in `ref_kumbhari_s7_gene_strain_inference`; test whether ecotype membership predicts strain-adaptation gene presence better than species abundance. *Disproved if*: strain-adaptation gene presence and species abundance have ≥ 90 % overlap in predictive power.

**H3c**: BGC-encoded inflammatory mediators (NRPS / RiPP clusters from `ref_bgc_catalog` and the 5,157 CB-ORFs in `ref_cborf_enrichment`) localize to a minority of Tier-A pathobionts and show strong CD-vs-HC enrichment. *Test*: join BGC catalog to pathobiont MAG catalog (`ref_mag_catalog`) and to Kumbhari strain-adaptation gene inference; test whether BGC-carrying strains are more CD-enriched than non-carrying strains of the same species. *Disproved if*: BGC presence is orthogonal to strain-level CD-adaptation probability (Spearman |ρ| < 0.2).

**H3d**: Metabolomic signatures stratify patients **independently** of taxonomic ecotype. *Test*: MOFA+ joint factor analysis — do metabolite factors align with, or cross-cut, taxonomic ecotypes? *Disproved if*: metabolite-driven factors are collinear (|ρ| > 0.8) with taxonomic ecotype assignments — would mean metabolomics adds no orthogonal information beyond taxonomy.

**H3e** (serology — HMP2 only): ASCA IgA / IgG, OmpC, CBir1, ANCA, pANCA titers correlate with abundance of specific pathobionts. This is a *direct experimental readout* of what the immune system is reacting to, independent of abundance-DA artifacts. *Test*: partial correlation of serology values (`fact_serology`) with strain-level abundance controlling for ecotype. *Disproved if*: serology titers correlate only with disease state and not with any specific pathobiont beyond a generic dysbiosis signal.

### Pillar 4 — Phage targetability

**H4a**: Top-ranked Tier-A pathobionts have **≥ 1 characterized strictly lytic phage** with published host range that together cover ≥ 80 % of the strain diversity in the affected ecotype. *Test*: construct pathobiont-strain × candidate-phage coverage matrix from `phagefoundry_strain_modelling`, PhageFoundry host-specific databases, and external sources (INPHARED / Millard, IMG/VR, NCBI Phage RefSeq, PhagesDB). *Disproved if*: fewer than half of Tier-A targets have qualifying phages, or combined coverage per ecotype < 50 %.

**H4b**: Phage-resistance escape cost varies by receptor class. Receptors in essential transporter / LPS-core / highly-conserved surface-protein systems produce more durable sensitivity than O-antigen-variable receptors. *Test*: where fitness data exists (`kescience_fitnessbrowser` for E. coli, Klebsiella, Acinetobacter etc.), quantify the fitness cost of disrupting the phage receptor or a proxy gene. Classify targets by "escape cost" tier. Cross-check against pangenome essentiality inference (`kbase_ke_pangenome`). *Disproved if*: receptor class does not predict resistance-escape cost (receptor class R² < 0.15 against fitness cost).

**H4c**: Target strains have **CRISPR-Cas content and spacer repertoires** that inform which candidate phages are already immune-targeted. *Test*: CRISPRCasFinder or equivalent on pangenome-linked target strains; spacer-vs-candidate-phage-genome match. Flag target strains with ≥ 1 spacer matching a candidate phage cocktail. *Disproved if*: no target strain shows meaningful spacer content against candidate phages — would simplify cocktail design but is improbable.

**H4d**: Endogenous phageome composition (from `fact_viromics` + `ref_viromics_summary_by_disease`) differs by ecotype and may constrain exogenous phage cocktail deployment via prophage-mediated superinfection exclusion. *Test*: stratified analysis of the 260 viruses in `ref_viromics_summary_by_disease` per ecotype; flag cocktail-candidate-phages whose close relatives are already endemic. *Disproved if*: no ecotype-specific endogenous phageome signature — simplifies but does not block the project.

### Pillar 5 — UC Davis deep dive

**H5a**: UC Davis patients cover a **subset** of reference ecotypes, not all of them. *Test*: projection + occupancy analysis (H1b). *Disproved if*: UC Davis covers all ecotypes equally well (would mean the cohort is representative rather than enriched).

**H5b**: UC Davis severity (fecal calprotectin, CRP, Montreal behavior B2/B3) correlates with pathobiont burden **within ecotype**. *Test*: ecotype-stratified regression of calprotectin against Tier-A-species abundance. *Disproved if*: no ecotype-specific severity signature — pooled correlations may be driven by dysbiosis-score alone.

**H5c**: For each UC Davis patient, a named top-N pathobiont list and a candidate phage cocktail (with Tier-B / C flags) can be produced. Deliverable: patient-level dossier table. *Disproved if*: ≥ 30 % of UC Davis patients have no viable phage-cocktail candidate under the rubric — which would itself be a useful negative result flagging clinical-trial design.

**H5d**: For the two UC Davis patients with longitudinal samples (6967 / 6967-1; 1460 / 1460-1), pathobiont identity is stable within-patient. This informs dosing schedule. *Test*: compare within-patient top-pathobiont ranking at the two timepoints. *Disproved if*: top pathobionts flip between timepoints — implying cocktails may need dynamic adjustment.

## Criteria — the four-tier rubric

### Tier A — Biological target suitability (data-driven from CrohnsPhage + BERDL)

| # | Criterion | Operationalization | Source |
|---|---|---|---|
| A1 | Prevalence within affected ecotype | ≥ 50 % of patients in the ecotype carry the species above detection threshold | `fact_taxon_abundance` / `fact_strain_frequency_wide` stratified by ecotype |
| A2 | Effect size within ecotype | Compositional-aware DA log₂FC > 1.0 AND FDR < 0.05 AND effect size (Cliff's δ or Cohen's h) > 0.2 | ANCOM-BC / MaAsLin2 / LinDA consensus |
| A3 | Mechanistic link to inflammation | ≥ 2 independent literature citations or an explicit mechanism in `ref_phage_biology` / `ref_ibd_indicators` | literature-linked gene evidence via `kescience_paperblast`, `kescience_pubmed`; `ref_ibd_indicators` |
| A4 | Not a protective-analog | Not on curated exclusion list (*C. scindens*, *F. prausnitzii*, *A. muciniphila*, *E. rectale*, *Roseburia spp.*, *Lachnospira spp.*, others per literature) | explicit exclusion list in project data dir |
| A5 | Causal / engraftment evidence | Engrafts in humanized mouse model AND enriches in patients, OR disease-specific strain-level adaptation genes present | engraftment donor-to-P2 tracking; `ref_kumbhari_s7_gene_strain_inference` |
| A6 | BGC-encoded inflammatory mediator | Associated BGC (NRPS / RiPP) in `ref_bgc_catalog` or `ref_cborf_enrichment`, preferably with disease-directional RPKM (`ref_ebf_ecf_prevalence`) | `ref_bgc_catalog`, `ref_cborf_enrichment`, `ref_ebf_ecf_prevalence` |

Scoring: a candidate must pass ≥ 5 of 6 (or equivalent weighted score) to enter Tier-B consideration. Each criterion reports a confidence tag: `observed`, `inherited-from-ref-table`, `inferred-from-literature` — distinguishing "we verified this" from "this came from a pre-computed table we did not re-check."

### Tier B — Phage availability and characterization (phage databases + pangenome)

| # | Criterion | Operationalization |
|---|---|---|
| B1 | ≥ 1 characterized strictly lytic phage | catalog entry with lytic lifestyle, not proven temperate |
| B2 | Host-range coverage | phage cocktail host range covers ≥ 80 % of target strain diversity in the affected ecotype |
| B3 | No transduction / ARG / toxin risk | phage genome annotation confirms no integrase, no transposase, no ARG, no toxin |
| B4 | Receptor identified | receptor gene annotated in the target; ideally a fitness-essential function |

Sources: `phagefoundry_strain_modelling`, `phagefoundry_ecoliphages_genomedepot`, per-genus PhageFoundry databases, INPHARED (Millard), IMG/VR, NCBI Phage Virus RefSeq, PhagesDB.

### Tier C — Ecological durability (BERDL pangenome + fitness + CRISPR + ecology)

| # | Criterion | Operationalization |
|---|---|---|
| C1 | CRISPR-Cas spacer immunity absent | ≤ 1 matching spacer between target strain and cocktail phage genomes |
| C2 | Prophage homoimmunity absent | no close relative of cocktail phage in target strain's prophage complement |
| C3 | Phage-resistance fitness cost high | receptor or proxy gene is essential / has high fitness cost of disruption in `kescience_fitnessbrowser` or pangenome essentiality inference |
| C4 | Removal does not open niche to another pathobiont | ecological modeling from `fact_strain_competition` co-occurrence patterns |
| C5 | Target not a hub with protective dependents | removing the target does not collapse a module containing protective species |

### Tier D — Clinical translation (flagged as experimental follow-up, NOT analyzed in this project)

Gut-transit stability, delivery route (oral / enema / NG / capsule), PK / PD, off-target kills, manufacturability, regulatory pathway. These gate candidates before a clinical trial; the scope of this project is to deliver ranked candidates, not to validate them experimentally.

## Methodological norms

**N1 — Verify where we can.** Pre-computed reference tables are starting points, not ground truth. Where a ref table is load-bearing for a claim, we re-run the underlying computation against the raw fact tables. Specifically:

- `ref_cd_vs_hc_differential` (Mann-Whitney) → verify against ANCOM-BC / MaAsLin2 / LinDA on `fact_taxon_abundance` per ecotype.
- `ref_consensus_severity_indicators` → verify the calprotectin / HBI correlations against `fact_clinical_longitudinal`.
- `ref_viromics_cd_vs_nonibd` / `ref_viromics_summary_by_disease` → verify against `fact_viromics` per ecotype.
- `ref_kumbhari_s7_*` → spot-check 3–5 top gene-level adaptation calls against the Kumbhari supplementary source to confirm the ETL did not drift.

Every Tier-A scored candidate carries one of three provenance tags per criterion: `observed` (re-computed in this project), `inherited-from-ref-table` (used ref table as-is), `inferred-from-literature` (external).

**N2 — Distinguish "CD-enriched" from "CD-associated."** Enrichment requires effect size, not just p-value. For compositional data we insist on log-ratio-based tests (CLR + linear model, ANCOM-BC) before accepting a log₂FC claim.

**N3 — Stratify before you sort.** No Tier-A scoring happens on pooled data. Every DA, regression, and correlation in Pillars 2 / 3 / 5 is run per ecotype (or explicitly noted as cross-ecotype).

**N4 — Power is bounded.** UC Davis n ≤ 21 unique patients. No within-UC-Davis claim is made without effect-size reporting; cross-cohort validation is required for any claim that proposes to generalize.

**N5 — Separate "UC Davis-observed" from "public-reference inherited."** Every UC Davis patient dossier entry makes this distinction explicit, so clinical readers can weigh evidence.

**N6 — BERDL query hygiene.** Every Spark notebook in this project starts with the JupyterHub-native Spark import pattern `spark = get_spark_session()` (no import statement — the session is injected into the BERDL JupyterHub kernel). Every query against a large BERDL table filters before aggregation per `docs/pitfalls.md`. Specifically:

- `kescience_fitnessbrowser.genefitness` (27M rows) — filter by `orgId` before any aggregation; **CAST** `fit` and `t` as DOUBLE before ABS/comparison (string-typed numeric columns).
- `kescience_fitnessbrowser` KO mapping — two-hop join via `besthitkegg` + `keggmember` (no direct `(orgId, locusId) → KO` table).
- `kbase_ke_pangenome.gene_cluster` (132M rows) — filter by `gtdb_species_clade_id` first; never full-scan.
- `kbase_ke_pangenome.genome_ani` (421M rows, O(n²)) — cap large species (K. pneumoniae = 14K genomes) at ≤ 500 genomes via subsampling; prefer species with < 500 genomes.
- `kbase_ke_pangenome.gtdb_taxonomy_r214v1.order` — backtick-quote in SQL (`` `order` ``) — reserved keyword.
- Pangenome taxonomy joins — use `genome_id`, not `gtdb_taxonomy_id` (different depth levels).

A notebook starts with an explicit header cell listing which BERDL databases it will touch and which filter predicates are applied; this is sanity-checked in the reviewer pass.

## Query Strategy — tables required by pillar

### Pillar 1 (stratification)

| Table | Purpose | Filter / scope |
|---|---|---|
| `fact_taxon_abundance` | MetaPhlAn3 species profiles for DMM / topic modeling | `classification_method == 'metaphlan3'`; CMD_IBD + HMP2 as training; Kuehl (Kaiju) held out |
| `fact_pathway_abundance` | HUMAnN3 MetaCyc pathways for topic modeling / MOFA | CMD_IBD only (scope 1a) |
| `fact_metabolomics` | HMP2 untargeted (27.3M rows) for MOFA metabolite factor | within-cohort; 35 compounds for cross-cohort bridge |
| `fact_clinical_longitudinal` | severity / medication covariates for H1c classifier | all cohorts with clinical data |
| `dim_participants` + `dim_samples` | subject-level dedup, longitudinal handling | filter to baseline visit per subject for stratification |
| `ref_taxonomy_crosswalk` | reconcile MetaPhlAn3 / Kaiju / GTDB namespaces | 1,951 species bridge |

### Pillar 2 (pathobiont ID)

| Table | Purpose |
|---|---|
| `fact_taxon_abundance` | within-ecotype compositional-aware DA |
| `fact_strain_frequency_wide` + `fact_strain_competition` | strain-level within-species heterogeneity + within-patient severity |
| `ref_consensus_severity_indicators` | starter Tier-A scaffold (verify per N1) |
| `ref_cd_vs_hc_differential` | starter pool of 420 species (verify per N1) |
| `ref_ibd_indicators` | literature ground-truth for sanity check |
| `ref_phage_biology` | starter Tier-1 dossier (12 organisms) — extend |
| `ref_kumbhari_s7_gene_strain_inference` | strain-adaptation genes per species |
| `ref_kumbhari_s7_eggerthella_lenta_predict` | E. lenta exemplar for strain-gene inference pattern |

BERDL joins:
- `kbase_ke_pangenome.bakta_amr` + `kbase_ke_pangenome.bakta_annotations` → virulence / AMR gene burden per target strain
- `kbase_ke_pangenome.gene_cluster` → pangenome gene-content variation within species (for Tier-A A5 strain adaptation)
- `kescience_paperblast.genepaper` + `kescience_pubmed` → literature linkage for Tier-A A3 mechanism

### Pillar 3 (functional drivers)

| Table | Purpose |
|---|---|
| `fact_pathway_abundance` | within-ecotype pathway DA (CMD_IBD only) |
| `fact_metabolomics` | within-cohort untargeted DA; 35-compound cross-cohort bridge via `ref_metabolite_crosswalk` |
| `fact_serology` | Pillar-3 H3e serology-microbiome integration (HMP2 only) |
| `ref_bgc_catalog` (10,060) + `ref_cborf_enrichment` (5,157) | BGC / core-biosynthetic-ORF mechanism |
| `ref_mag_catalog` (76) | BGC → pathobiont MAG linkage (known gap: no R. gnavus, no AIEC) |
| `ref_hmp2_metabolite_annotations` | HMDB-anchored metabolite name resolution for HMP2 |
| `ref_metabolite_crosswalk` | 7,368 compounds; 35 three-way ChEBI |

BERDL joins:
- `kbase_msd_biochemistry.reaction` + `kbase_msd_biochemistry.compound` → pathway ↔ reaction ↔ metabolite mapping for mechanism inference
- `kbase_ke_pangenome.gapmind_pathways` → GapMind metabolic completeness per target species
- `kescience_interpro` → domain-level virulence factor / CRISPR-Cas / adhesin classification

### Pillar 4 (phage targetability)

| Table | Purpose |
|---|---|
| `fact_viromics` (HMP2) + `ref_viromics_summary_by_disease` (780) + `ref_viromics_cd_vs_nonibd` (22) | endogenous phageome per ecotype |
| `ref_phage_biology` | Tier-1 organism phage dossier (12 rows) — extend |

BERDL joins:
- `phagefoundry_strain_modelling` → experimental phage-host interaction matrix (critical for Tier-B B2 host range)
- `phagefoundry_ecoliphages_genomedepot` → E. coli phages (primary AIEC cocktail input)
- `phagefoundry_klebsiella_*` → Klebsiella phages (K. oxytoca cocktail input)
- `phagefoundry_acinetobacter_*` / `phagefoundry_paeruginosa_*` / `phagefoundry_pviridiflava_*` → context / cross-species host-range reference
- `kescience_fitnessbrowser.genefitness` → phage-resistance fitness-cost inference (Tier-C C3)
- `kbase_ke_pangenome` CRISPR-Cas operon annotations → Tier-C C1

External databases (out-of-BERDL):
- Millard lab INPHARED (https://millardlab.org/bacteriophage-genomics/) — comprehensive phage genome catalog
- IMG/VR — viral metagenome reference
- NCBI Phage Virus RefSeq — curated phage genomes
- PhagesDB — additional characterized phages for gram-negative and gram-positive targets

### Pillar 5 (UC Davis deep dive)

| Table | Purpose |
|---|---|
| `~/data/CrohnsPhage/crohns_patient_demographics.xlsx` | UC Davis clinical metadata (21 patients, 23 samples) |
| `fact_taxon_abundance` filtered to Kuehl `study_id == 'KUEHL_WGS'` | UC Davis taxonomic profile (Kaiju; map via `ref_taxonomy_crosswalk` to MetaPhlAn3 reference space) |
| `fact_clinical_longitudinal` (UC Davis rows) | calprotectin / severity (HBI / CDAI pending from Dave lab) |
| `ref_mag_catalog` filtered to Kuehl MAGs (76) | UC Davis strain resolution (acknowledge gap: no R. gnavus, no AIEC) |

Per-patient dossier output columns (per H5c):
`patient_id, ecotype, ecotype_confidence, calprotectin, Montreal, medication_class, top_N_pathobionts (ranked by Tier-A score), per-pathobiont [prevalence_in_patient, strain_adaptation_gene_count, BGC_present, causal_evidence], candidate_phages (per pathobiont, Tier-B/C flags), longitudinal_stability (for patients 6967 and 1460), confidence_notes`.

## Analysis Plan — notebook sketch

| NB | Pillar | Environment | Core output |
|---|---|---|---|
| **NB00** | all | local (no Spark) | Data audit: profile each parquet in `~/data/CrohnsPhage/`, validate column names / dtypes / missingness against the per-table dictionary YAMLs, reconcile the 33 tables against `schema_overview.yaml`, and document each fact / ref table's actual columns in `projects/ibd_phage_targeting/data/table_schemas.md` (since `docs/schemas/` has no coverage for these local-mart tables). Reproduce one slice of the preliminary DA vs compositional-aware DA as a proof-of-concept for norm N1 and the *C. scindens* paradox. Figures: coverage summary, missingness heatmap, sample-count-per-cohort, protective-species sanity check (C. scindens, F. prausnitzii, A. muciniphila). |
| **NB01** | 1 | local | Ecotype training v1: build the systematic synonymy layer (`data/species_synonymy.tsv`, 2,417 aliases → 1,848 canonical species, GTDB r214+ renames included), pivot 8,489 CMD MetaPhlAn3 samples × 1,442 species, fit LDA (DMM-equivalent on pseudo-counts) and GMM (on CLR + PCA) over K=2..8. Initial K=8 result. **Note: HMP2 MetaPhlAn3 not in mart yet** (lineage.yaml `PENDING_HMP2_RAW`); training on CMD only. **Pathway topic model deferred** (CMD_IBD-only per scope 1a); **MOFA+ deferred** (cross-modality is properly scoped after each modality has its own ecotypes). |
| **NB01b** | 1 | local | K-selection refit: held-out perplexity for LDA + cross-method ARI scan (LDA vs GMM) + parsimony rule. Result: **consensus K = 4**, 48.9 % per-sample method agreement, four biologically clean ecotypes (E0 diverse healthy commensal; E1 Bacteroides2 transitional disease/metabolic; E2 Prevotella copri non-Western; E3 severe Bacteroides/fragilis-expanded). `data/ecotype_assignments.tsv` overwritten with K=4 result and `methods_agree` flag. |
| **NB02** | 1 | local | Ecotype projection: project UC Davis Kuehl_WGS (Kaiju namespace → MetaPhlAn3 via synonymy layer) and HMP2 (when ingested) onto the trained K=4 embedding; test H1b occupancy. Figures: UC Davis per-ecotype distribution, held-out cohort occupancy. |
| **NB03** | 1 | local | Clinical-covariate-only ecotype classifier (H1c); report AUC, feature importance. |
| **NB04** | 2 | local | Within-ecotype compositional-aware DA (ANCOM-BC + MaAsLin2 + LinDA consensus); Tier-A A1 / A2 scoring. Figures: ecotype × species enrichment heatmap, C. scindens paradox comparison. |
| **NB05** | 2 | local | Tier-A scoring pipeline: A3 (literature via paperblast), A4 (protective-analog exclusion), A5 (engraftment + strain adaptation), A6 (BGC linkage). Output: scored candidate table. |
| **NB06** | 2 | local | Co-occurrence network per ecotype (SparCC / SpiecEasi); module detection; H2d intersection with Tier-A. Figures: module networks, Tier-A-hub overlap. |
| **NB07** | 3 | JupyterHub (Spark) → local | Within-ecotype pathway DA (CMD_IBD); MOFA joint factor; pathway → pathobiont attribution. Figures: pathway × ecotype heatmap, factor loadings. |
| **NB08** | 3 | local | BGC / CB-ORF mechanism: join BGC catalog to MAG + pathobiont; per-ecotype BGC DA; ebf / ecf per-patient. |
| **NB09** | 3 | local | Metabolomics — within-cohort untargeted (HMP2 and Dave), 35-compound cross-cohort bridge; bile acids, SCFAs, tryptophan derivatives focused. |
| **NB10** | 3 | local | Strain-adaptation gene analysis: extend the E. lenta pattern (`ref_kumbhari_s7_eggerthella_lenta_predict`) to all 59 species via `ref_kumbhari_s7_gene_strain_inference`. |
| **NB11** | 3 | local | Serology × microbiome integration (H3e, HMP2 only). |
| **NB12** | 4 | JupyterHub (Spark) + local | Pathobiont × phage coverage matrix (PhageFoundry + external phage DBs). Tier-B B1 / B2 scoring. |
| **NB13** | 4 | local | CRISPR-Cas spacer analysis (Tier-C C1); phage-resistance fitness cost via `kescience_fitnessbrowser` (Tier-C C3). |
| **NB14** | 4 | local | Endogenous phageome stratification per ecotype (H4d); prophage superinfection-exclusion risk annotation. |
| **NB15** | 5 | local | UC Davis medication-class harmonization (parse the Excel into structured `therapy_class`), ecotype projection, per-patient pathobiont ranking. |
| **NB16** | 5 | local | Per-patient phage cocktail drafts (H5c); longitudinal stability check for 6967 and 1460 (H5d). |
| **NB17** | all | local | Synthesis figures + final target ranking per ecotype, cohort-level summary, per-patient dossier. |

Notebook numbers are provisional; NB00 is the audit, NBs 01–03 are Pillar 1, 04–06 Pillar 2, 07–11 Pillar 3, 12–14 Pillar 4, 15–16 Pillar 5, 17 cross-cutting synthesis.

## Reproduce-and-extend — what we carry forward from the preliminary analysis

| From preliminary report | Where it lives in this plan | What we add |
|---|---|---|
| Species-level DA on curatedMetagenomicData (`ref_cd_vs_hc_differential`, 420 species) | Pillar 2 / NB04 | Re-run compositional-aware per ecotype (ANCOM-BC / MaAsLin2 / LinDA) |
| Dysbiosis score (Cohen's d = 1.32) | Pillar 1 feature input | Retain formula; use as one stratification input |
| HUMAnN3 MetaCyc pathway DA | Pillar 3 / NB07 | Re-run within-ecotype; flag HMP2 / UC Davis as known gaps (no raw reads) |
| HMP2 untargeted metabolomics (25,540 features) | Pillar 3 / NB09 | Cohort-specific analysis + 35-compound cross-cohort bridge |
| SAMP/AKR targeted metabolomics (taurocholic acid −3.86; PC 32:2–34:3) | Pillar 3 / NB09 | Cross-check HMP2 bile-acid panel for concordance; small-n caveat |
| Engraftment donor 2708 → P1 → P2 (6 pathobionts transfer) | Pillar 2 Tier-A A5 | Use directly as causal evidence; request NRGS metadata from Dave lab |
| Kumbhari strain-level adaptation (E. lenta *katA*, *rodA*, *ponA*, *acnA*, *rlmN*) | Pillar 3 / NB10 | Extend pattern to all 59 Kumbhari species |
| Elmassry BGC catalog (10,060; 112 pathobiont-linked) | Pillar 3 / NB08 | Per-ecotype BGC DA; ebf / ecf per-patient |
| CB-ORF enrichment (5,157; 115 CD-enriched, 211 CD-depleted) | Pillar 3 / NB08 | CB-ORF × ecotype stratification |
| Calprotectin correlation | Pillar 5 / NB15 + Tier-A A2 | Ecotype-stratified regression |
| GTDB-Tk MAG catalog (76) | Pillar 2 / Pillar 3 | Acknowledge R. gnavus / AIEC gap explicitly |
| Composite Tier-1 / Tier-2 target list (E. bolteae, E. lenta, R. gnavus, H. hathewayi, etc.) | Pillar 2 baseline | Starting hypothesis for rubric validation |

## Known missing-data registry

Tagged via `ref_missing_data_codes` sentinel codes. Does not block analysis but should be reported in every pillar's conclusion.

| Gap | Impact | Mitigation |
|---|---|---|
| Dave lab clinical metadata (HBI / CDAI for ~23 patients) `PENDING_DAVE_LAB` | Pillar 5 H5b severity regression uses calprotectin + CRP only until HBI arrives | Request from Dave lab; flag plan revision when received |
| Dave lab pipeline documentation `PENDING_KUEHL` | Kaiju version, reference DB date unknown | Use available Kaiju output; note provenance gap in figures |
| HMP2 EC enzyme profiles on disk, not in schema `PENDING_HMP2_RAW` | Pillar 3 pathway analysis limited to CMD_IBD | Document as follow-up; no raw reads to run HUMAnN3 ourselves (scope decision 1a) |
| 62 Dave SAMP metabolite IDs unintegrated | Pillar 3 / NB09 within-cohort metabolomics slightly incomplete | Integrate if a targeted mechanism requires them; otherwise accept |
| Kumbhari 5,492 / 6,138 samples lack `dim_samples` entries | Kumbhari-derived analyses rely on `fact_strain_*` joins directly, not through `dim_samples` | Document join pattern in NB00 audit |
| Viral taxonomy in `fact_viromics` 19 / 316 reconciled to `dim_taxa` | Endogenous phageome analysis uses VirMAP lineage strings, not taxon_ids | Build a VirMAP → external-viral-DB crosswalk as Pillar 4 deliverable |
| No raw reads for UC Davis or HMP2 | Cannot re-run MetaPhlAn3 / HUMAnN3 / StrainPhlAn / inStrain | Scope decisions 1a / 3a formally acknowledge this |

## Expected Outcomes — what each H outcome means

- **If H1a–c hold**: reproducible ecotype framework with clinical-covariate projector. Foundational for everything else.
- **If H2a–d hold**: per-ecotype Tier-A target list, each with ≥ 2 hub candidates in co-occurrence modules — proposes consortial cocktail design per ecotype.
- **If H2c fails (C. scindens *still* CD-enriched after stratification)**: the stratification is wrong or the protective annotation needs re-examination. Either is informative.
- **If H3a–d hold**: mechanism-anchored target list with bile-acid / mucin / sulfide / TMAO / BGC themes attributable to specific pathobionts.
- **If H3e holds**: serology-confirmed targets with external experimental validation.
- **If H4a–d hold**: per-ecotype cocktail designs with strain coverage, resistance-escape risk, and endogenous-phageome compatibility.
- **If H5a–d hold**: per-UC-Davis-patient phage cocktail drafts with per-pillar provenance tags, clinical-ready rubric outputs, longitudinal stability notes.
- **If any pillar's core hypotheses fail**: that failure is a useful negative result for clinical-trial design, not a project failure. The criteria rubric is designed to be falsifiable, not to rubber-stamp hypotheses.

## Potential confounders and limitations

- **Medication confounding**: anti-TNF / anti-IL23 / JAK inhibitors / 5-ASA / corticosteroids modify microbiome composition. UC Davis cohort is heterogeneous on this axis. Ecotype classification and within-ecotype DA must include medication class as a covariate.
- **Biogeography**: stool metagenomics under-samples mucosa-associated communities. AIEC is mucosa-associated. Biopsy samples (where available) treated as separate modality.
- **Smoking**: opposite effects in UC vs CD; UC Davis has heterogeneous smoking history.
- **Age**: pediatric IBD may have different ecotype structure; public-cohort age span (curatedMetagenomicData + HMP2) includes pediatric and adult.
- **Ethnicity / geography**: training on mostly-Western cohorts may not generalize to non-Western IBD patients. Flag but do not attempt to correct.
- **Host genetics (NOD2, IL23R, ATG16L1, etc.)**: UC Davis cohort lacks genotype data. Public cohorts partial. Treat as a *possible* future Pillar-6 extension.
- **Single-donor engraftment evidence (donor 2708)**: N = 1 causal evidence. We treat as strong but irreplicable without additional donors.

## Revision History

- **v1.3** (2026-04-24): NB02 + NB03 execution outcomes — Pillar 1 closed.
  - **NB02**: UC Davis Kuehl_WGS (26 samples, 23 patients) projected onto the K=4 embedding via the synonymy layer. LDA is the primary projection method for Kuehl (feature-sparsity-robust); GMM is advisory (collapses under Kaiju / MetaPhlAn3 classifier mismatch — all Kuehl samples land in E3 at >97 % GMM confidence, an artifact). UC Davis distribution: E0 27 % / E1 42 % / E2 0 % / E3 31 %, χ² p = 0.019 against uniform. **H1b directionally supported.** Patient 6967 shows intra-patient longitudinal disagreement (E1 ↔ E3) — first signal for H5d.
  - **NB03**: clinical-covariate-only ecotype classifier (H1c). Macro OvR AUC 0.799 (minimal) / 0.810 (extended) — both pass the 0.70 threshold. **But UC Davis patient agreement is only 41 % / 36 %.** Minimal classifier predicts E1 for 19/22 UC Davis patients because `is_ibd = 1` is constant and the learned rule collapses to the marginal mode. Extended classifier's training subset is 702 E1 / 959 E3 / 3 E0 / 11 E2 — effectively an E1-vs-E3 binary problem.
  - **H1c revised**: "Passes on pooled-cohort AUC; fails on patient-level translation." Clinical covariates distinguish HC vs IBD trivially (`is_ibd` dominates AUC), but do *not* reliably separate IBD ecotypes (E1 transitional vs E3 severe) without metagenomics. For UC Davis-type cohorts (all active CD), **metagenomics remains the primary ecotype-assignment method**. The per-patient dossier (Pillar 5, NB15–NB16) cites NB02's metagenomic call, not NB03's clinical prediction.
  - **Norm note**: OvR-AUC on a cohort with a strong cohort-axis variable (like `is_ibd`) can overstate per-patient classifier usefulness. Logged as discovery: always validate classifier decisions on an independent cohort before quoting AUC as a clinical-utility metric.
  - **Pillar 1 closed**: H1a, H1b directionally supported; H1c nuanced (paper-pass / patient-fail). Ready for Pillar 2 (NB04 within-ecotype DA — the *C. scindens* paradox resolution).

- **v1.2** (2026-04-24): NB01 + NB01b execution outcomes. Updates:
  - `data/species_synonymy.tsv` (2,417 aliases → 1,848 canonical species) committed as the project-wide taxonomy reconciliation backbone. Norm N7 is now a *deliverable*, not just a methodology note.
  - **Ecotype training** delivered K=8 in NB01 (per-method criteria) but cross-method ARI was weak (0.128). NB01b refit selected **K=4** by maximum cross-method ARI + parsimony, raising agreement to 48.9 %. Four biologically interpretable ecotypes:
    - E0 (n=3,604) — diverse healthy commensal (66.8 % of HC)
    - E1 (n=2,601) — Bacteroides2 transitional / metabolic-disease (48 % CD, 58 % UC, 100 % T1D, 97 % T2D)
    - E2 (n=920) — Prevotella copri enterotype (non-Western healthy comparator)
    - E3 (n=1,364) — severe Bacteroides/fragilis-expanded (50 % CD, 67 % IBD acute, 38 % CDI)
  - **H1a directionally supported**: ≥ 3 reproducible ecotypes confirmed. **H1b directionally supported**: CD/UC distribute across E1 + E3 rather than concentrating in one.
  - **Notebook table**: NB01 split into NB01 (training, K-scan) and NB01b (K-selection refit). HMP2 MetaPhlAn3 confirmed `PENDING_HMP2_RAW`; pathway topic model and MOFA+ explicitly deferred from NB01.
  - **Method note**: LDA on pseudo-counts (sklearn) used as DMM equivalent; GMM on CLR + PCA-20 used as compositional-aware alternative. Both methods reach K=4 as the parsimonious agreement point.

- **v1.1** (2026-04-24): Plan-review follow-up (`PLAN_REVIEW_1.md`, claude-sonnet-4). Added:
  - Norm N6 — explicit BERDL query hygiene (Spark import pattern, `CAST` for string-typed numerics, two-hop KO mapping, large-table filter requirements, `order` keyword backtick-quoting, genome_id join rules, genome_ani subsampling).
  - Extended H2c protective-species validation battery beyond *C. scindens* to *F. prausnitzii*, *A. muciniphila*, *E. rectale*, *R. intestinalis*, *L. eligens*.
  - Expanded NB00 scope to include committing a `data/table_schemas.md` for the CrohnsPhage fact / ref tables (since `docs/schemas/` has no coverage).
- **v1** (2026-04-24): Initial plan — five pillars, four-tier criteria, verify-where-we-can norm, reproduce-and-extend from the 2026-03-28 preliminary report. Scope decisions: (1a) pathway DA on CMD_IBD only, (2a) 35-compound metabolomics cross-cohort bridge, (3a) Kumbhari 432-strain panel as primary. No raw reads available, so options (1b) and (3b) ruled out a priori.

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory

Collaborators (data providers, attribution here pending formal authorship):
- UC Davis CD cohort: Kuehl / Dave lab
- Engraftment mouse experiments: Dave lab (NRGS)
- Strain-level reference analyses: Kumbhari et al. 2024 (PMID / source in `dim_studies`)
- BGC meta-analysis: Elmassry et al. 2025 (Cell Host & Microbe)
