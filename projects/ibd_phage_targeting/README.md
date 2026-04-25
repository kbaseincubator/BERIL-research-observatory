# Metagenome-Prioritized Phage Cocktails for Crohn's Disease and IBD

## Research Question

Which bacterial pathobionts are **enriched, ubiquitous, and non-protective** in IBD, UC, and Crohn's disease patients — considered both across indications and **within distinct patient subgroups** defined by demographics, severity, native-microbiome structure, and treatment history — and of those pathobionts, which are **tractable phage-therapy targets** given the available (or characterizable) phages, their host range, the evolutionary escape routes their target strains have available, and the ecological consequences of removing them?

Three coupled deliverables:

1. **Patient stratification**: a reproducible ecotype framework trained on public cohorts that each UC Davis patient can be assigned to, with ecotype-specific pathobiont signatures.
2. **Pathobiont target atlas**: a scored list of candidate targets per ecotype (and per UC-Davis patient), ranked against an explicit biological / phage-availability / ecological-durability rubric.
3. **Per-patient cocktail drafts**: for each of the ~21 unique UC Davis patients, a proposed phage cocktail with candidate phages, strain-coverage evidence, Tier-B/C flags, and confidence notes.

## Status

**In Progress** — Pillar 1 closed; Pillar 2 rigor-repaired (RESEARCH_PLAN v1.4). Next milestone: NB05 Tier-A scoring on the rigor-controlled Tier-A input set.

- ✅ NB00 data audit + compositional-DA proof of concept (norm N1 justified)
- ✅ NB01 + NB01b ecotype training (K=4 consensus from cross-method ARI + parsimony):
  - **E0 (n=3,604)** — diverse healthy commensal (*F. prausnitzii* / *R. bromii* / *B. uniformis*); **66.8 % of HC**
  - **E1 (n=2,601)** — Bacteroides2 transitional disease/metabolic; 48 % CD, 58 % UC, 100 % T1D, 97 % T2D
  - **E2 (n=920)** — *Prevotella copri* enterotype; 16.9 % HC, almost no disease
  - **E3 (n=1,364)** — severe Bacteroides/fragilis-expanded; 50 % CD, 40 % UC, 67 % IBD acute, 38 % CDI
  - Reusable `data/species_synonymy.tsv` (2,417 aliases → 1,848 canonical species, GTDB r214+ renames)
  - Bootstrap ARI stability: median 0.160 (range 0.129–0.169) — marginally stable; external MGnify replication pending
- ✅ NB02 UC Davis projection (Kuehl_WGS Kaiju → K=4 via LDA primary / GMM advisory): **E0 27 %, E1 42 %, E2 0 %, E3 31 %**; χ² vs uniform p = 0.019 → **H1b supported**. Patient 6967 shows longitudinal E1 ↔ E3 shift — first H5d signal.
- ✅ NB03 clinical-covariate classifier (H1c): macro AUC 0.799 (minimal) / 0.810 (extended) on pooled CMD — passes the 0.70 threshold on paper. **But only 41 % agreement with NB02 on UC Davis patients**. Revised: clinical features separate HC vs IBD trivially but *not* IBD ecotypes; metagenomics remains required.
- ⚠️ **NB04 superseded** — within-ecotype DA committed (a325ce5) but retracted after adversarial review caught feature-leakage and confounder-non-adjustment issues that the standard `/berdl-review` missed twice. See `FAILURE_ANALYSIS.md`.
- ✅ **NB04b → c → d → e → f → g → h — Pillar 2 rigor-repair + strengthening pipeline** (seven notebooks):
  - NB04b: bootstrap CIs, leakage-bound sensitivity (E1 Jaccard 0.230, E3 0.064 vs >0.5 threshold → leakage dominates NB04), LOO refit (*C. scindens* CD↑ in both E1 and E3 under LOO), Jaccard permutation null (observed 0.104 vs null 0.785 → **H2b supported, empirical p = 0.000**), ecotype bootstrap stability (ARI 0.16)
  - NB04c: proper substudy resolution (51 sub-studies, 80.8 % coverage) + documented cMD substudy-nesting unidentifiability + confound-free within-IBD-substudy CD-vs-nonIBD meta (recovers canonical CD signature) + LinDA in pure Python
  - NB04d: formalized rigor-controlled stopping rule for NB05 — E1 PROCEED, E3 PROCEED WITH CAVEAT
  - NB04e: **within-ecotype × within-substudy meta** — E1 Tier-A **51 candidates** (meta-viable, 2 sub-studies, 100 % sign concord), E3 Tier-A **40 provisional candidates** (single-study HallAB_2017)
  - Plus 5 engraftment-confirmed cross-ecotype pathobionts (*M. gnavus*, *E. lenta*, *E. coli*, *E. bolteae*, *H. hathewayi*) under NB04c §3 confound-free contrast
  - **H2c retracted** (no paradox — *C. scindens* is CD↑ under confound-free design)
  - NB04f LOSO stability (mean ARI 0.113) — documents real cross-study ecotype variance (bootstrap ARI masked this); some sub-studies fit the framework well (LifeLinesDeep 85 % agreement), others poorly (AsnicarF 38 %).
  - NB04g pathway-feature K=4 refit on 3,145 CMD_IBD HUMAnN3 pathway samples — PARTIAL (ARI 0.113, E1 65 % agreement) — ecotype structure is mixed ecological + taxonomic.
  - **NB04h HMP_2019_ibdmdb external replication** via `curatedMetagenomicData` v3.18 — 1,627 samples projected, 80 % at posterior > 0.70; subject-level χ² p = 0.016 (ecotype stratifies CD/UC/nonIBD); **E1 Tier-A 88.2 % sign-concordant (45/51)**. **Pillar 2 operationally externally validated.**
- ✅ **NB05 Tier-A scoring (A3–A6)**: 71 unique rigor-controlled candidates scored; **6 actionable** (total ≥ 2.5/4.0): *H. hathewayi* (4.0), *M. gnavus* (3.8), *E. coli* (3.6; Colibactin+Yersiniabactin+Enterobactin MIBiG matches), *E. lenta* (3.3), *F. plautii* (3.3), *E. bolteae* (2.8). 9 Tier-B sub-threshold candidates (incl. *S. salivarius* with Salivaricin MIBiG matches).
- ✅ **NB06 co-occurrence networks (H2d test) — Pillar 2 fully closed**: CLR+Spearman+Louvain per E1/E3 × {all, CD} subnet. **4-5 of 6 actionable Tier-A co-cluster in a single "pathobiont module" per subnet** → multi-target cocktails ecologically appropriate. *F. plautii* E1-only, *E. coli* E3-only ecotype-specific module membership. Hand-off to Pillar 4/5 includes per-candidate ecotype-specific module assignment.
- ✅ **NB07a — Pillar 3 opener: pathway DA + H3a v1.7 three-clause falsifiability**. Within-IBD-substudy CD-vs-nonIBD meta on `fact_pathway_abundance` (3 robust + 1 boundary substudy per N15 re-verification). **H3a PARTIALLY SUPPORTED (2/3 clauses)**: (a) 52 CD-up pathways pass FDR<0.10 + |effect|>0.5 with permutation null mean 0.077 — strong CD signal; (c) 137 pathway-pathobiont pairs with |ρ_meta|>0.4 (max 0.797 vs null 0.18); top hits all *E. coli* pathways recapitulating known AIEC biology (glyoxylate cycle, propanediol biosynthesis, heme biosynthesis ↔ Yersiniabactin, allantoin, AST arginine degradation). (b) failed-but-degenerate: only 3 of 52 CD-up pathways fall in the 7 a-priori categories (44/409 background) — test underpowered, not a fundamental refutation; cMD unstratified-pathway DA captures broader bacterial-fitness-in-inflamed-gut signal not concentrated in classical IBD categories. NB07b stratified-pathway analysis is the natural next test.
- ✅ **NB07 v1.8 H3a (b) retest — MetaCyc class hierarchy + Fisher per-theme enrichment**. Replaced v1.7's regex-on-pathway-names approach with structured class assignments from ModelSEEDDatabase MetaCyc_Pathways.tbl (90 % coverage of 575 HUMAnN3 IDs). 12 IBD themes (added iron/heme, fat metabolism, anaerobic respiration, purine recycling, aromatic AA / chorismate to v1.7's 7). Per-theme Fisher's exact (CD-up × in-theme) with BH-FDR. **v1.8 cohort-level H3a (b) verdict: SUPPORTED — iron/heme acquisition is the dominant CD-up theme (OR=8.1, FDR=7e-6; 15 of 52 CD-up pathways in this theme vs 4 expected by chance).** Per-species: *H. hathewayi* shows 2 supported themes — purine/pyrimidine recycling (OR=4.9) + TMA/choline (OR=9.3). Four-way convergence: NB05 *E. coli* Yersiniabactin/Enterobactin MIBiG + NB07a heme-biosynthesis attribution + v1.8 iron-theme enrichment + AIEC literature → iron acquisition is the dominant CD pathobiont specialization. The v1.7 → v1.8 reversal is itself a methodological lesson (norm N17): prefer curator-validated ontology / class hierarchy over name-pattern regex for pathway categorization.
- ✅ **NB07b — stratified-pathway DA per Tier-A-core species (H3a (b) species-resolved retest)**. Per Tier-A-core species: stratified pathways via synonymy → 10%-prevalence → within-IBD-substudy CD-vs-nonIBD meta. **H3a (b) NOT SUPPORTED at species-resolved level either** — but for **structural** reasons (7 a-priori IBD categories are sparse in per-species pathway repertoires; ≤ 4 background pathways in 7-cat set per species), not fundamental biological refutation. New biology revealed: *H. hathewayi* shows coherent within-carrier biosynthesis-up / sugar-degradation-down CD shift (33 passing pathways); *E. coli* shows within-carrier per-pathway CD-DOWN (consistent with AIEC-specialized subset losing peripheral metabolic capabilities — interpretation supported by NB05 §5g Yersiniabactin/Colibactin findings). Other 4 Tier-A core species show small within-carrier shifts → their CD signal is mostly carriage prevalence, not metabolic shift; strain-level (NB10) and BGC-level (NB08) are natural follow-ups.
- ✅ **NB07c — module-anchor commensal × pathobiont metabolic coupling (H3a-new)**. CD-specific module anchors from NB06: E1_CD module 0 (anchors *A. caccae*, *B. nordii*, *Clostridiales bacterium 1_7_47FAA*; pathobionts *H. hathewayi*, *F. plautii*, *E. bolteae*, *E. lenta*, *M. gnavus*); E3_CD module 1 (anchors 2 oral *Actinomyces*, *L. longoviformis*; pathobionts *E. lenta*, *H. hathewayi*, *E. coli*, *M. gnavus*). Within-IBD-substudy Spearman ρ + iron-pathway triple correlation. **H3a-new PARTIAL**: ***A. caccae* × pathobiont coupling clean in E1_CD** (ρ=+0.39 with *E. bolteae*, +0.33 *H. hathewayi*, +0.31 *M. gnavus*, +0.29 *F. plautii*; all 100 % sign-concordant); E3_CD weaker (only Lactonifactor × *E. lenta* +0.27). Iron-pathway co-variation **dominated by *E. coli*** (mean ρ=+0.45 vs +0.13 for *A. caccae*) → narrows v1.8 iron-theme to AIEC-specific. ***B. nordii* × *M. gnavus* / *F. plautii* NEGATIVE coupling** (−0.21, −0.20) → niche competition. **Pillar-4 cocktail-design implication**: targeting pathobionts may incidentally reduce butyrate-producer *A. caccae* through loss of substrate; NB05 Tier-A scoring needs a "metabolic-coupling-cost" annotation.
- ✅ **NB08a — BGC × pathobiont enrichment (H3c, genomic mechanism layer)**. Per Tier-A core × `ref_bgc_catalog` (Elmassry 2025, 10,060 BGCs across 6,221 species-annotated entries) Fisher exact theme enrichment + CB-ORF CD-vs-HC enrichment + ebf/ecf cohort meta. **H3c PARTIALLY SUPPORTED**: 3 of 4 BGC-themes enriched in Tier-A core (iron_siderophore OR=44.4 FDR 7e-56; genotoxin_microcin OR=234 FDR 3e-35; NRPS_PKS_hybrid OR=1.5 FDR 0.04). ***E. coli*** **alone among Tier-A core carries the iron+genotoxin BGC signature** (54 iron MIBiG: 19 Yersiniabactin + 16 Enterobactin + 19 siderophore-class; 25 genotoxin: 8 Colibactin + 15 Microcin B17). Other 5 Tier-A core in MIBiG dark matter but with substantial non-MIBiG BGC content (E. lenta 41, M. gnavus 58, E. bolteae 18). 5/6 Tier-A core have CD-up CB-ORF rates above background (14–82 % vs 2.5 %); E. lenta is exception (CB-ORFs 54 % CD-DOWN, consistent with Koppel 2018 non-BGC drug-metabolism mechanism). **ebf/ecf RPKM CD-up across 4 cohorts at p<1e-31** — replicates Elmassry 2025 cleanly. **Five-line iron-acquisition convergence narrative now established**: NB05 §5g + NB07a §c + NB07 v1.8 §9 + NB07c §2 + NB08a §2 — five independent evidence streams converging on AIEC iron-acquisition as the dominant CD-pathobiont specialization mechanism.
- ⏳ NB05–NB17 per plan; HMP2 ingestion (`PENDING_HMP2_RAW`) is the primary unblock for E3 replication

## Context

Based on prior work (see [Precision Phage Editing of CD Patient Microbiota, v2 report](https://genomics.lbl.gov/~aparkin/IBD/IBD_Comprehensive_Analysis_Report_v2.html), 2026-03-28), we have:

- An integrated data mart over **10,774 samples across 19 studies** (`~/data/CrohnsPhage`, v10, schema v2.4) — dim/fact/ref star schema with metabolomics, pathways, strains, viromics, serology, BGCs, clinical severity.
- A **22–23-sample UC Davis CD cohort** (21 unique patients, 2 longitudinal re-samples) with Montreal classification, fecal calprotectin (9 μg/g to >8,000 μg/g), CRP, and medication history.
- **Humanized-mouse engraftment data** from donor 2708 → P1 → P2 (strongest causal evidence available), already flagging six pathobionts that transfer faithfully (*R. gnavus*, *E. bolteae*, *E. coli*, *A. finegoldii*, *C. difficile*, *K. oxytoca*).
- A preliminary DA analysis (Mann-Whitney + BH-FDR) that surfaced 508 DA species but contains **known compositional and stratification artifacts** (e.g., *C. scindens* called CD-enriched despite being a well-documented protective species) that motivate a re-analysis under compositional-aware DA within patient ecotypes.

## Overview

Five analytical pillars:

1. **Patient stratification** — train reproducible ecotypes on curatedMetagenomicData + HMP2 (DMM / topic modeling / MOFA), project UC Davis onto them.
2. **Pathobiont identification** — compositional-aware within-ecotype differential abundance, scored against the Tier-A criteria rubric (prevalence, mechanism, ecotype-coherence, engraftment evidence, protective-analog exclusion, BGC-encoded inflammatory mediator).
3. **Functional drivers** — pathway, metabolite, and BGC / CB-ORF enrichment mapped to pathobiont contributors within ecotypes.
4. **Phage targetability** — coverage matrix against PhageFoundry + external phage databases, CRISPR-Cas spacer analysis, phage-resistance fitness cost inference.
5. **UC Davis deep dive** — per-patient ecotype assignment, pathobiont dossier, phage-cocktail draft, longitudinal within-patient stability.

A four-tier criteria rubric (Tier A — biological target suitability, Tier B — phage availability, Tier C — ecological durability, Tier D — clinical translation) gates candidates as they move from hypothesis to proposal. Tier D (PK, manufacturability, regulatory) is flagged as experimental follow-up, not analyzed in this project.

**Methodological norm — verify where we can**: pre-computed reference tables (`ref_consensus_severity_indicators`, `ref_cd_vs_hc_differential`, `ref_kumbhari_*`, `ref_viromics_*`) are treated as starting points. Where they are load-bearing for a claim, we re-run the underlying computation against the raw fact tables (compositional-aware DA, strain deconvolution, etc.) to distinguish "observed here" from "inherited from reference table." The *C. scindens* paradox is the canonical example of why.

## Data Collections

This project integrates data from:

- **`~/data/CrohnsPhage/`** — integrated mart (33 tables, schema v2.4). 7 BERDL-style "study" sources including curatedMetagenomicData, HMP2, Kuehl, Dave/SAMP/AKR mouse, Dave/NRGS FMT, Kumbhari/PRISM, Elmassry BGC catalog.
- **`kescience_mgnify`** — MGnify (EBI metagenomics) for independent IBD-cohort cross-validation.
- **`kbase_ke_pangenome`** — pangenome / AMR / GapMind / functional annotations for pathobiont strain heterogeneity and virulence-gene content.
- **`pangenome_bakta`** — Bakta-based pangenome slice (AMR / virulence gene cross-reference).
- **`kbase_genomes`** — protein sequences for structural receptor analysis.
- **`kescience_fitnessbrowser`** — gene fitness → phage-resistance fitness-cost inference for some target species.
- **`kbase_phenotype`** and **`kescience_bacdive`** — experimental and strain-phenotype data for target physiology.
- **`kescience_webofmicrobes`** — exometabolomics where available.
- **`kescience_paperblast`** + **`kescience_pubmed`** — literature-linked gene-function evidence for Tier-A scoring.
- **`kescience_interpro`** — domain-level virulence-factor classification (adhesins, toxins, secretion systems, CRISPR-Cas).
- **`kescience_alphafold`** + **`kescience_pdb`** — structural models for phage-receptor prediction.
- **`phagefoundry_*`** (five databases including `phagefoundry_strain_modelling` experimental phage-host pairings, `phagefoundry_ecoliphages_genomedepot`, `phagefoundry_klebsiella_*`, `phagefoundry_acinetobacter_*`, `phagefoundry_paeruginosa_*`, `phagefoundry_pviridiflava_*`) — phage host-range and sequence evidence.
- **`protect_genomedepot`** / **`protect_integration`** — pathogen genome browser context.
- **`arkinlab_microbeatlas`** — 464K 16S samples for prevalence / biogeography baseline.
- **`kbase_msd_biochemistry`** — ModelSEED reactions for pathway-level mechanism inference.
- **External phage databases** (out-of-BERDL): Millard lab INPHARED, IMG/VR, NCBI Phage Virus RefSeq, PhagesDB — needed for non-PhageFoundry hosts (*R. gnavus*, *E. bolteae*, *E. lenta*, *C. difficile*, *B. fragilis*).

## Quick Links

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, pillar structure, four-tier criteria, BERDL query strategy, per-pillar analysis sketch, known-missing registry, reproduce-and-extend table (v1.4 — NB04 rigor-repair arc documented)
- [Report](REPORT.md) — **interim synthesis** — Pillar 1 findings (ecotype framework, UC Davis projection, H1c classifier) + rigor-controlled Pillar 2 (Tier-A via within-ecotype × within-substudy meta); §5 opens with a retraction box for the superseded NB04 claims. Pillars 3–5 pending.
- [Failure Analysis](FAILURE_ANALYSIS.md) — full arc of the NB04 rigor gap: adversarial review findings, repair notebooks, quantified cost (Tier-A 33 → 3 rock-solid → 51 E1 + 40 E3 under confound-free meta), methodology lessons
- [References](references.md) — cited literature with PMIDs and project context

## Reproduction

*TBD — added after analysis is complete. Will cover: BERDL JupyterHub prerequisites, data-mart location, notebook execution order with runtime estimates, external-data dependencies (phage databases), and the medication-harmonization ETL step for the UC Davis cohort.*

## Authors

- Adam Arkin (ORCID: [0000-0002-4999-2931](https://orcid.org/0000-0002-4999-2931)), U.C. Berkeley / Lawrence Berkeley National Laboratory

Collaborators (data providers, named here for attribution; formal authorship TBD):
- UC Davis CD cohort: Kuehl / Dave lab teams (metadata pending)
- Engraftment mouse experiments: Dave lab (NRGS)
- Strain-level reference analyses: Kumbhari et al. 2024
- BGC meta-analysis: Elmassry et al. 2025
