# Executive Summary — Metagenome-Prioritized Phage Cocktails for Crohn's Disease

**Project**: `ibd_phage_targeting` (BERIL Research Observatory)
**Status**: Pillars 1–5 substantially closed — per-patient cocktail drafts for all 23 UC Davis CD patients (NB15) + patient 6967 longitudinal E1→E3 drift validation + state-dependent dosing rule + clinical-translation workflow (NB16). NB17 cross-cutting synthesis remains.
**Date**: 2026-04-25
**Authors**: Adam Arkin (LBNL / UC Berkeley), with collaborators (Kuehl/Dave labs, Kumbhari et al.)

## What this project does, in one sentence

Given metagenomic data on a Crohn's disease patient, this project produces a **per-patient ranked list of bacterial pathobionts to target with phage therapy**, plus a **specific phage cocktail recommendation** when phages are available, plus **alternative therapeutic options** when phages are not.

## Why this matters for clinical translation

CD is heterogeneous: a single cohort-level "CD pathobiont list" mismatches individual patients. We show that:

1. CD patients fall into **four reproducible microbiome subtypes (ecotypes)** — E0 (healthy commensal), E1 (Bacteroides2 transitional, the dominant CD ecotype), E2 (Prevotella), and E3 (severe Bacteroides-expanded). UC Davis patients distribute as 27 % E0 / 42 % E1 / 0 % E2 / 31 % E3.
2. **Each ecotype carries a distinct pathobiont module** — phage cocktails designed against the pooled-cohort top-pathobiont list will mismatch ~58 % of UC Davis patients (anyone not in E1).
3. **Patient-level ecotype assignment requires metagenomics, not clinical covariates** — a classifier on age + sex + IBD status achieved 41 % patient-level agreement vs metagenomic projection. No shortcut to genomic stool typing.
4. **Pure phage cocktails are structurally infeasible for the dominant E1 ecotype** — the 5-species E1 pathobiont module includes 2 species (*H. hathewayi*, *F. plautii*) for which no lytic phages exist in any current database. **Hybrid 3-strategy cocktails are required**.

## The six actionable pathobiont targets

After rigorous compositional differential abundance (within-IBD-substudy meta on 4 IBD cohorts; HMP2 external replication at 88 % sign-concordance), six species emerge as **actionable Tier-A targets**:

| Pathobiont | Tier-A score | Mechanism | Phage availability | Bile-acid coupling cost | Recommendation |
|---|---:|---|---|---|---|
| ***H. hathewayi*** | 4.0 | Species-abundance + within-carrier metabolic shift | **GAP** (no known phages) | Low | **External DB query priority** (INPHARED, IMG/VR); fallback: GAG-degrading enzyme inhibitors |
| ***M. gnavus*** | 3.8 | Mucin-glucorhamnan production (Henke 2019) | Temperate-only (6 phages) | Low | Lytic-locked phage engineering OR biochemical glucorhamnan-synthesis target |
| ***E. coli* (AIEC)** | 3.6 | Iron acquisition (Yersiniabactin/Enterobactin/Colibactin) | **Tier-1 clinical** (EcoActive) | Low | **5-phage cocktail**: DIJ07_P2 + LF73_P1 + AL505_Ev3 + 55989_P2 + LF110_P2 (95 % strain coverage of 188 PhageFoundry-tested E. coli strains); requires AIEC strain-resolution diagnostic |
| ***E. lenta*** | 3.3 | Drug metabolism (Cgr2 cardiac glycoside reductase, Koppel 2018) | Tier-2 (PMBT5 siphovirus) | Moderate | PMBT5 phage; co-monitor BA pool |
| ***F. plautii*** | 3.3 | Bile-acid 7α-dehydroxylation | **GAP** (not in databases) | **HIGHEST** | **DEPRIORITIZE phage targeting**; co-administer UDCA / bile-acid-binding agent |
| ***E. bolteae*** | 2.8 | Mixed | Tier-2 (PMBT24 Kielviridae) | Moderate | PMBT24 phage; co-monitor BA pool |

## Per-patient cocktail framework — 4 design categories

**14 of 23 UC Davis patients (61 %) have concrete phage cocktail drafts.**

| Category | Cocktail strategy |
|---|---|
| **Active disease + multiple targets (E1)** — high priority | Hybrid 3-strategy cocktail: direct phages for E. coli (if present) + E. bolteae + E. lenta; alternatives for H. hathewayi (enzyme inhibitors) + F. plautii (BA-binding co-therapy) |
| **Active disease + few targets (E0)** | Limited cocktail; consider non-phage strategies given E0's lower pathobiont burden |
| **Quiescent disease (low calprotectin)** | Reserve cocktail for flares; calprotectin + ecotype-state monitoring |
| **Mixed ecotype (longitudinal drift)** | State-dependent dosing — rebalance per-visit ecotype. Patient 6967 (NB16) shows clear E1→E3 drift with *M. gnavus* 14× expansion as dominant signature; cocktail Jaccard 0.60 between visits. Drop F. plautii on E1→E3; consider E. coli on E3→E1; universal Tier-1 trio (M. gnavus + H. hathewayi + E. lenta) is the cocktail backbone across both ecotypes. |

## Three biological narratives that guide cocktail design

The project produced two cross-corroborated mechanism narratives across 6 independent evidence streams each:

1. **Iron acquisition is an *E. coli* (AIEC subset) phenomenon, not a community-wide CD signature.** Yersiniabactin + Enterobactin + Colibactin biosynthetic gene clusters are concentrated in *E. coli* genomes (54 iron-MIBiG matches; 0 in the other 5 actionable Tier-A core). Pathway-level iron/heme acquisition is the dominant CD-up MetaCyc theme (OR=8.1, FDR=7×10⁻⁶). **Implication**: target AIEC subset specifically; standard *E. coli* targeting will miss the actual pathobiont strain.

2. **Bile-acid 7α-dehydroxylation is a coupled multi-species mechanism.** *F. plautii* / *E. lenta* / *E. bolteae* show a substrate-product signature in patient stool: negative correlation with primary tauro-conjugated bile acids, positive with secondary unconjugated bile acids (lithocholate, deoxycholate). **Implication**: depleting these species (especially *F. plautii*) shifts the bile-acid pool toward inflammatory primary forms — must co-administer UDCA or bile-acid-binding agent if phage targeting these species.

3. **Multiple per-modality CD signatures collapse into a single principal axis.** A canonical correlation analysis on HMP2 paired metagenomics + metabolomics yields one factor (CC1, r=0.96) that captures ALL 6 actionable Tier-A pathobionts (CD-positive) + ecotype-defining commensals (CD-negative) + urobilin loss + polyamine elevation + long-chain PUFA elevation + secondary-bile-acid depletion + fatty-acid-amide elevation. **Implication**: CD biology at the gut-microbiome level is one disease axis with multiple molecular manifestations, not a many-axis manifold. Treatment-response monitoring can use any of these markers as a proxy for the underlying state.

## Clinical-translation roadmap

**Immediate (current cohort)**:
- Per-patient cocktail drafts for 23 UC Davis patients (NB15 output)
- F. plautii BA-coupling-cost annotation per actionable target (deprioritization rule)
- 4-category patient stratification (Active+many, Active+few, Quiescent, Mixed)
- **State-dependent dosing rule established (NB16)** — 5 concrete recommendations including 3-6 month ecotype re-test, F. plautii E1-specific / E. coli E3-specific inclusion, universal Tier-1 trio as cocktail backbone, and **clinical workflow** (initial visit + follow-up calp/qPCR + ecotype-shift decision tree)

**Near-term (6–12 months)**:
- **External DB queries (INPHARED + IMG/VR)** for *H. hathewayi*, *M. gnavus* lytic alternatives, *F. plautii* phages — closes the structural Pillar-4 gap before clinical translation
- **AIEC strain-resolution diagnostic** for the 8 / 23 patients carrying *E. coli* (pks-island + Yersiniabactin + Enterobactin gene-presence detection via PCR or amplicon panel)
- ***M. gnavus* qPCR validation as cheap clinical proxy** for ecotype-state monitoring (NB16 hypothesis: 5-fold change triggers full ecotype re-test, avoiding routine metagenomics) — needs prospective cohort with paired qPCR + metagenomics across timepoints

**Mid-term (12–24 months)**:
- **Targeted qPCR ecotype panel** — 4–6 species (*F. prausnitzii*, *P. copri*, *P. vulgatus*, *B. fragilis*, *M. gnavus*) for rapid clinical ecotype assignment without full metagenomics
- **Per-patient bile-acid panel** for F. plautii BA-cost monitoring
- **Multi-cohort serology meta-analysis** to firm up the H3e signals (anti-microbial antibody × pathobiont abundance correlations marginal in HMP2 alone)
- **Expanded longitudinal sampling** beyond patient 6967 to validate state-dependent dosing rule across more ecotype-drift trajectories

**Long-term (24+ months)**:
- **Clinical pilot** of hybrid 3-strategy cocktails in UC Davis CD cohort (per-ecotype + per-patient + state-dependent dosing per NB16 workflow)
- **Lytic-locked phage engineering** for *M. gnavus* if natural lytic phages remain unavailable
- **GAG-degrading enzyme inhibitor** screening for *H. hathewayi* (alternative to phage)

## Methodology summary

- **Five analytical pillars** spanning patient stratification (ecotypes), pathobiont identification (Tier-A scoring), functional drivers (pathway/BGC/metabolomics/strain/serology), phage targetability (3-layer evidence stack), and per-patient cocktail design.
- **30 notebooks** with full saved outputs and reproducibility.
- **Confound-free within-IBD-substudy CD-vs-nonIBD meta-analysis** as the rigor-controlled DA design (resolves both feature leakage and substudy confounding).
- **Adversarial review** caught 5 critical + 6 important methodological issues in the original NB04 analysis that two standard reviews missed; a 7-notebook rigor-repair pipeline (NB04b–h) restored validity. **Adversarial review is now the recommended review pattern** for any methodologically-nuanced microbiome project.
- **Two cross-corroborated 6-line mechanism narratives** (iron-acquisition; bile-acid 7α-dehydroxylation) — each finding is supported across multiple analytical granularities (literature → pathway DA → species-correlation → genomic content → metabolite-level → in-vivo phageome). Convergence is the rigor signal.
- Per **plan v1.9 (no raw reads)**: data scope is fixed at precomputed mart tables + curatedMetagenomicData R-package fetches + BERDL precomputed collections. The project's findings are robust within this scope and require external DB queries (INPHARED, IMG/VR) only for the 3 gut-anaerobe phage-coverage gaps.

## Limitations (clinical context)

- **23-patient UC Davis cohort is small**. Per-patient cocktail recommendations are exemplars/templates, not statistically robust per-patient validation. Generalization requires multi-center validation.
- ***E. coli* AIEC carriage is only ~35 % of UC Davis patients** (8/23). The well-characterized AIEC literature emphasizes this species as the prototypical CD pathobiont, but the dominant pathobionts in this cohort are *H. hathewayi* (83 %) and *M. gnavus* (91 %) — both currently lacking lytic phages.
- **Pure phage cocktails are not feasible for the dominant E1 ecotype**. Hybrid 3-strategy cocktails (phages + alternatives + engineered solutions) are required. This is a **structural feature of gut-anaerobe phage availability**, not a project limitation per se.
- **No per-patient bile-acid measurements available**. F. plautii BA-coupling-cost annotation is ecotype-level, not per-patient — clinical translation requires per-patient bile-acid panels for monitoring.
- **No per-patient AIEC strain-resolution diagnostic in the current cohort**. Cocktail recommendations for the 8 E. coli-positive patients assume AIEC subset prevalence per Dogan 2014 / Dubinsky 2022 but cannot be patient-specifically validated without strain-resolution sequencing.
- **External cohort validation beyond HMP2 is limited**. Additional cMD sub-studies and non-Western IBD cohorts would strengthen the ecotype framework, particularly for E2 (Prevotella) which is absent in the active-disease UC Davis cohort.
- **Patient 6967 longitudinal E1→E3 drift is n=1**. NB16 quantified the trajectory (M. gnavus 14× expansion; cocktail Jaccard 0.60) and patient 1112 tech replicates (Spearman ρ=1.000) validate the technical-noise floor, but the state-dependent dosing rule is **a hypothesis derived from a single trajectory** — prospective validation requires an expanded longitudinal cohort with paired qPCR + metagenomics. **No timing information** between the 2 patient 6967 visits — duration of the E1→E3 drift is unknown.

## Cohort facts (UC Davis CD)

- **23 patients**, 21 unique individuals (2 longitudinal re-samples on patient 6967 only)
- Age 20–72 (median ~35); mixed sex
- All on first-line CD therapies (anti-TNF / anti-IL23 / steroid / 5-ASA / JAK-inhibitor / no-therapy)
- Calprotectin range 1–8000 μg/g (most either quiescent <50 or active >250)
- Montreal classification: predominantly L2/L3 ileocolonic disease

## Where to find more

- **Full report**: [REPORT.md](REPORT.md) — ~2,000 lines covering all 24 numbered Novel Contributions, 30 notebooks with outputs, 51 figures, 80+ data files, full literature context
- **Research plan + revisions**: [RESEARCH_PLAN.md](RESEARCH_PLAN.md) — v1.0 → v1.9 with all 17 plan norms and 4 adversarial-review iterations
- **Failure analysis**: [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md) — full arc of NB04 rigor failure → 7-notebook repair pipeline → externally-replicated Tier-A
- **References**: [references.md](references.md) — 47 cited papers with PMIDs and project-context annotations

---

*This executive summary is a clinical-collaborator-oriented digest of the full project deliverable. It distills the per-patient cocktail framework from the underlying technical work but is NOT a substitute for the methodology, limitations, and uncertainty quantification documented in REPORT.md.*
