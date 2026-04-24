# Metagenome-Prioritized Phage Cocktails for Crohn's Disease and IBD

## Research Question

Which bacterial pathobionts are **enriched, ubiquitous, and non-protective** in IBD, UC, and Crohn's disease patients — considered both across indications and **within distinct patient subgroups** defined by demographics, severity, native-microbiome structure, and treatment history — and of those pathobionts, which are **tractable phage-therapy targets** given the available (or characterizable) phages, their host range, the evolutionary escape routes their target strains have available, and the ecological consequences of removing them?

Three coupled deliverables:

1. **Patient stratification**: a reproducible ecotype framework trained on public cohorts that each UC Davis patient can be assigned to, with ecotype-specific pathobiont signatures.
2. **Pathobiont target atlas**: a scored list of candidate targets per ecotype (and per UC-Davis patient), ranked against an explicit biological / phage-availability / ecological-durability rubric.
3. **Per-patient cocktail drafts**: for each of the ~21 unique UC Davis patients, a proposed phage cocktail with candidate phages, strain-coverage evidence, Tier-B/C flags, and confidence notes.

## Status

**In Progress** — Pillar 1 ecotype framework delivered. Plan v1.2:

- ✅ NB00 data audit + compositional-DA proof of concept (norm N1 justified; *C. scindens* paradox reproduced and partially explained)
- ✅ NB01 + NB01b ecotype training (K=4 consensus from cross-method ARI + parsimony):
  - **E0 (n=3,604)** — diverse healthy commensal (*F. prausnitzii* / *R. bromii* / *B. uniformis*); **66.8 % of HC**
  - **E1 (n=2,601)** — Bacteroides2 transitional disease/metabolic; 48 % CD, 58 % UC, 100 % T1D, 97 % T2D
  - **E2 (n=920)** — *Prevotella copri* enterotype; 16.9 % HC, almost no disease
  - **E3 (n=1,364)** — severe Bacteroides/fragilis-expanded; 50 % CD, 40 % UC, 67 % IBD acute, 38 % CDI
  - Reusable `data/species_synonymy.tsv` (2,417 aliases → 1,848 canonical species, GTDB r214+ renames)
- ✅ NB02 UC Davis projection (Kuehl_WGS Kaiju → K=4 via LDA primary / GMM advisory): **E0 27 %, E1 42 %, E2 0 %, E3 31 %**; χ² vs uniform p = 0.019 → **H1b supported**. Patient 6967 shows longitudinal E1 ↔ E3 shift — first H5d signal.
- ✅ NB03 clinical-covariate classifier (H1c): macro AUC 0.799 (minimal) / 0.810 (extended) on pooled CMD — passes the 0.70 threshold on paper. **But only 41 % agreement with NB02 on UC Davis patients** — classifier collapses to "IBD → E1" because `is_ibd` dominates training. Revised: clinical features separate HC vs IBD trivially but *not* IBD ecotypes; metagenomics remains required for UC Davis-type patient assignment.
- ⏳ NB04 within-ecotype compositional DA (the *C. scindens* paradox resolution, H2c)
- ⏳ NB05–NB17 per the plan; HMP2 MetaPhlAn3 ingestion (`PENDING_HMP2_RAW`) will re-open an expanded NB02 projection when available

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

- [Research Plan](RESEARCH_PLAN.md) — hypotheses, pillar structure, four-tier criteria, BERDL query strategy, per-pillar analysis sketch, known-missing registry, reproduce-and-extend table
- [Report](REPORT.md) — **interim synthesis** — Pillar 1 findings (ecotype framework, UC Davis projection, H1c classifier), interpretation, literature context. Pillars 2–5 pending.
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
