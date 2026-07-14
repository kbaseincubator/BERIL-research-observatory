# Failure Analysis: NB04 Rigor Gap

**Project**: `ibd_phage_targeting` Pillar 2
**Date**: 2026-04-24
**Status**: Complete — findings inform REPORT.md rewrite, RESEARCH_PLAN.md v1.4, `docs/pitfalls.md`, and `docs/discoveries.md`

---

## Summary

NB04 (within-ecotype compositional-aware DA) was committed on 2026-04-24 with headline claims that the *C. scindens* paradox was "resolved by ecotype stratification" (H2c), that E1 and E3 target sets diverge substantially (H2b, Jaccard = 0.14), and with a 33-species Tier-A candidate list meant to seed NB05 (phage-target scoring). Two independently-run AI reviews then evaluated the same project state:

- **Standard `/berdl-review`** (`tools/review.sh` with claude-sonnet-4, ran twice as `REVIEW_1.md` and `REVIEW_2.md`) — concluded "exceptional methodological sophistication," "no critical issues," and recommended proceeding to Pillars 3–5 with the existing Tier-A list.
- **Adversarial review** (a separately-spawned `general-purpose` Agent with explicit "find flaws, don't be diplomatic" framing on the same files) — identified **5 critical issues + 6 important issues**, four of which materially undermined NB04's headline claims.

The adversarial review prompted a rigor-repair notebook (`NB04b_analytical_rigor_repair.ipynb`). Two of six repair arms did not execute correctly (§5 LME, §6 ANCOMBC) and were completed in `NB04c_rigor_repair_completion.ipynb` with data-structure-aware fixes. The combined NB04b + NB04c analysis yielded three headline findings that supersede NB04:

1. **H2c (paradox resolution) is wrong.** *C. scindens* is genuinely CD↑ (pooled CLR-Δ +1.18, FDR 1e-8, sign-concordant in 4/4 IBD sub-studies under a confound-free within-substudy analysis). NB04's "RESOLVED" verdict was an artifact of feature leakage in within-ecotype DA.
2. **H2b (ecotype divergence) survives and strengthens.** Permutation-null p = 0.000 for observed Jaccard 0.104 against a null mean 0.785 ± 0.054.
3. **Tier-A list shrinks from 33 to 3 rock-solid candidates** (all E3-specific, zero E1): *Flavonifractor plautii*, *Blautia wexlerae*, *Mediterraneibacter gnavus* — the only species passing 3-way independent-evidence gating (bootstrap CI + LinDA + within-substudy CD-vs-nonIBD concordant).

This document records the failure arc, the specific issues the standard reviewer missed, what we found when we looked honestly, and the generalizable lessons.

---

## Timeline

| Date (2026) | Artifact | What changed |
|---|---|---|
| 04-24 early | NB00–NB03 committed | Pillar 1 closed; REPORT synthesized Pillar 1 |
| 04-24 | NB04 committed (a325ce5) | Within-ecotype DA; H2c "RESOLVED" claim; 33 Tier-A candidates |
| 04-24 | REPORT.md updated (9fd42f1) | Pillar 2 opener with NB04 findings |
| 04-24 | `REVIEW_1.md` written | Standard `/berdl-review` run #1 — "no critical issues" |
| 04-24 | `REVIEW_2.md` written | Standard `/berdl-review` run #2 (re-run for replication) — again "no critical issues" |
| 04-24 | Adversarial review run | General-purpose Agent with "find flaws" framing — 5 critical + 6 important issues |
| 04-24 | NB04b built + executed | Rigor repair — §5 (LME) and §6 (ANCOMBC) arms failed silently |
| 04-24 | NB04c built + executed | LME confound-structure analysis + LinDA pure-Python; Tier-A refined to 3 candidates |
| 04-24 | This document | Failure analysis written while findings are fresh |

---

## The 5 critical + 6 important issues the standard reviewer missed

Issues flagged by the adversarial reviewer (verbatim codes used in NB04b):

### Critical

| Code | Issue | What NB04 did | Why it matters |
|---|---|---|---|
| **C1** | **Feature leakage in within-ecotype DA** | Clustered samples on taxon relative abundances (LDA/GMM on MetaPhlAn3 species matrix), then ran within-cluster differential abundance on the same taxa | Selection-on-outcome confounding. Within-cluster effect sizes are mechanically inflated for ecotype-defining species; the top-30 list is substantially the cluster definition itself |
| **C2** | **Hard-coded verdict logic** | `pooled CD↑ + within-ecotype n.s. → RESOLVED` was a literal `if / elif` branch | Treating n.s. as positive evidence in finite samples is selective reporting. The correct decision rule requires TOST-style equivalence testing or bootstrap CI containing zero with bounded width |
| **C3** | **Zero confounder adjustment** | No study / cohort / age / medication adjustment | Vujkovic-Cvijin 2020 is cited in the plan but not implemented. The pooled CD-vs-HC contrast is confounded by {study, geography, sequencing center, sample prep} |
| **C4** | **Jaccard reported without null** | "Jaccard = 0.14 supports H2b — stratified targeting is materially different" | Random-overlap baseline for top-30 out of ~300 filtered species is ~0.10. Without a null distribution, 0.14 is indistinguishable from chance |
| **C5** | **Ecotype framework unvalidated externally** | 48.9 % cross-method LDA↔GMM agreement at K=4; no hold-out or independent cohort projection | A 48.9 %-agreement cluster solution is reported as a "reproducible four-ecotype framework" without an honest stability / replication check |

### Important

| Code | Issue | What NB04 did |
|---|---|---|
| **I1** | Single-method DA | Plan required ≥ 2/3 of {ANCOM-BC, MaAsLin2, LinDA} to agree; NB04 ran only CLR + Mann-Whitney |
| **I2** | No strain-level check | Species-level collapse hides strain heterogeneity for pathobiont candidates |
| **I3** | No bootstrap CIs on effect sizes | Point estimates + p-values only |
| **I4** | Protective-analog exclusion not applied | Plan Tier-A rubric required excluding species with protective-strain homologs; NB04 Tier-A scoring didn't implement |
| **I5** | Engraftment evidence not integrated | The six donor-2708 engraftment pathobionts weren't cross-referenced against within-ecotype Tier-A |
| **I6** | No prevalence-weighted reporting | Effect sizes reported without per-ecotype prevalence-denominator weighting |

### What the standard reviewer got right

- Flagged missing reproduction documentation (appropriate)
- Noted pending HMP2 integration (appropriate)
- Observed the 41 % classifier agreement gap on UC Davis (appropriate)
- Flagged cohort-size limitation for per-patient cocktails (appropriate)

All of the standard reviewer's catches were surface / structural: missing docs, missing data, missing samples. None touched the inferential or statistical soundness of the within-ecotype DA.

---

## What NB04b found (partial repair)

NB04b was a 9-section rigor-repair notebook built to address C1, C2, C4, I1, I3 tractably. Key results that executed correctly:

- **Bootstrap CIs + TOST equivalence (§1, repair for C2 + I3)** — *C. scindens* in E3 bootstrap CI = [+0.03, +0.34] → CD↑, contradicting NB04's "n.s. → RESOLVED." *F. prausnitzii* (canonical protective) had CIs above zero in both E1 and E3 (CD↑ within ecotype), revealing that within-ecotype DA was producing directionally wrong calls for protective species.
- **Held-out-species sensitivity (§2, repair for C1 broad bound)** — 5 random 50/50 species splits; for each, refit K=4 LDA on half A, re-test half B within refit-ecotypes. Mean Jaccard with NB04 top-30 ∩ half-B: E1 = 0.230, E3 = 0.064. Bound: > 0.5 = leakage bounded, < 0.3 = leakage dominates. **Leakage dominates.**
- **Leave-one-species-out (§3, repair for C1 rigorous)** — per battery species, refit ecotypes on all-OTHER species, re-test held-out species. *C. scindens* CD↑ in **both** E1 (CI +0.68, +0.87) and E3 (CI +1.13, +1.71) under LOO — the within-ecotype n.s. call was a self-selection effect.
- **Jaccard permutation null (§4, repair for C4)** — 200 permutations of ecotype labels within E1+E3 samples. Permutation-null mean 0.785 ± 0.054; observed 0.104. Empirical p = 0.000. **H2b is real; NB04's effect-size framing was wrong but the conclusion holds.**
- **Bootstrap ecotype stability (§7, partial repair for C5)** — 5 × 80 %-subsample LDA refits; ARI vs full-sample labels: median 0.160, range 0.129–0.169. Marginal stability at best.

Repair arms that did not execute:

- **§5 LME substudy adjustment (C3)** — regex-on-sample-ID parsed only 19 noisy categories (CMD 5,333; HMP2 1,627; EGAR 355; MH 286; V 206; p 170; …); LME reported "insufficient substudies per species" on every row. Produced zero data.
- **§6 ANCOM-BC2 via rpy2 (I1)** — `pandas2ri.activate()` errored with DeprecationWarning; the `r-ancombc` conda env is not present on this worktree. No R alternative attempted.

With those two arms broken, the rigor-controlled Tier-A had `n_evidence ≤ 1` on every candidate (bootstrap-CI-stable only; no independent confirmation), and the NB04c stopping rule failed on all three criteria.

---

## What NB04c found (completion)

NB04c fixed both broken arms with data-structure-aware approaches that don't depend on rpy2 or R.

### Proper substudy resolution (§2)

`dim_samples.external_ids` is a JSON blob with a `"study"` key for CMD_HEALTHY samples (e.g., `"AsnicarF_2021"`, `"LifeLinesDeep_2016"`). `dim_samples.participant_id` for CMD_IBD samples has the shape `CMD:HallAB_2017:SKST006` where the middle token is the source study. Resolving both yields **51 distinct sub-studies covering 80.8 %** of the ecotype-assigned sample set (6,862 / 8,489) — vs NB04b's 19 mostly-garbage prefix categories.

### The pooled-cohort confound is structurally unidentifiable (§2, §5)

Counting sub-studies that contain ≥ 10 samples of each diagnosis:

| Diagnosis pair | # sub-studies with both |
|---|---:|
| HC ≥ 10 AND CD ≥ 10 | **0** |
| CD ≥ 10 AND nonIBD ≥ 10 | 4 |

CMD's healthy-cohort samples come from HC-only studies (LifeLinesDeep_2016, AsnicarF_2021, YachidaS_2019, HansenLBS_2018, XieH_2016, VincentC_2016, BritoIL_2016, …); CMD-IBD CD samples come from IBD-cohort studies (HallAB_2017, VilaAV_2018, LiJ_2014, IjazUZ_2017, NielsenHB_2014). **There is no sub-study that contains both CD and HC samples.** A pooled CD-vs-HC LME with substudy random effect is therefore structurally unidentifiable — the random effect perfectly predicts diagnosis.

Empirically: `statsmodels.mixedlm` with the proper substudy labels silently failed to converge on every battery species; LME produced zero usable rows. This is the *correct* behavior given the design matrix and is documented in `nb04c_lme.tsv` (empty) and explicitly in the notebook output.

### Within-substudy CD-vs-nonIBD is the confound-free alternative (§3)

Four IBD sub-studies have ≥ 10 CD and ≥ 10 nonIBD samples: HallAB_2017 (89 CD / 73 nonIBD), LiJ_2014 (76 / 10), IjazUZ_2017 (56 / 38), NielsenHB_2014 (21 / 248). Pooled effect size via inverse-variance weighted meta-analysis across the four studies (242 CD, 369 nonIBD total) on the 14-species curated battery:

| Species | CLR-Δ | FDR | Sign concordance across 4 studies |
|---|---:|---:|---:|
| Mediterraneibacter gnavus | **+5.13** | ~0 | 4/4 |
| Eggerthella lenta | +2.30 | 4e-9 | 4/4 |
| Escherichia coli | +1.43 | 2e-4 | 3/4 |
| **Clostridium scindens** | **+1.18** | 1e-8 | **4/4** |
| Enterocloster bolteae | +1.09 | 3e-6 | 4/4 |
| Hungatella hathewayi | +0.92 | 5e-4 | 3/4 |
| Bilophila wadsworthia | +0.07 | 0.70 | 3/4 |
| Lachnospira eligens | −1.01 | 4e-3 | 3/4 |
| Roseburia intestinalis | −1.14 | 2e-3 | 4/4 |
| Akkermansia muciniphila | −1.30 | 3e-3 | 3/4 |
| Faecalibacterium prausnitzii | −1.67 | 9e-8 | 4/4 |
| Roseburia hominis | −1.77 | 4e-7 | 4/4 |
| Coprococcus eutactus | −3.09 | 4e-15 | 4/4 |

This is the **canonical CD microbiome signature** — pathobionts up, protectives down, consistent across studies — recovered cleanly once study-confounding is eliminated. It directly contradicts NB04's within-ecotype calls for the same species in multiple directions:

- *C. scindens* — NB04 called n.s. within E1 and E3 and claimed "paradox RESOLVED." The within-substudy analysis calls CD↑ with FDR 1e-8 and 4/4 sign concordance. **The paradox is not a paradox; C. scindens is genuinely CD-enriched.** The NB04 within-ecotype result is a leakage artifact.
- *F. prausnitzii* / *R. hominis* / *L. eligens* — NB04 within-ecotype called CD↑. Within-substudy calls CD↓ with 4/4 or 3/4 concordance. The within-ecotype direction reversal is a compositional-bias + leakage compound artifact.

### LinDA (§4) confirms within-ecotype direction patterns but shares the leakage bias

335 species × 3 analyses (pooled, E1, E3), pure-Python LinDA (OLS on CLR with median bias correction). Bias estimates: +0.23 pooled, +0.01 E1, −0.22 E3. LinDA broadly agrees with CLR-MW within-ecotype in sign and magnitude, confirming NB04's within-ecotype *numerics* but inheriting the same feature-leakage bias. So n_evidence based on {bootstrap CI, LinDA} alone is not two independent evidence streams — they share the bias.

### Refined Tier-A: 33 → 3 rock-solid candidates (all E3)

3-way evidence gating on NB04's 33 within-ecotype Tier-A candidates:

- **Evidence 1**: bootstrap CI lower-bound > 0.3 (from NB04b §8)
- **Evidence 2**: LinDA effect > 0 AND FDR < 0.10 (from NB04c §4) — same-ecotype
- **Evidence 3**: within-substudy CD-vs-nonIBD meta-analysis effect > 0 AND ≥ 66 % sign concordance across ≥ 2 of 4 IBD studies (from NB04c §3)

Only Evidence 3 is independent of ecotype definition. The count of candidates passing:

| Ecotype | n_evidence = 1 | = 2 | = 3 |
|---|---:|---:|---:|
| E1 | 4 | 14 | **0** |
| E3 | 0 | 12 | **3** |

**The 3 E3 candidates** (only truly-independent Tier-A):

| Species | Bootstrap CI | LinDA (E3) | Within-substudy | Existing literature context |
|---|---|---|---|---|
| Mediterraneibacter gnavus | stable + | +1.64 (FDR 0) | **+5.13 (FDR 0)** | Engraftment-confirmed pathobiont (donor 2708 → P1 → P2); classical IBD pathobiont |
| Flavonifractor plautii | stable + | +2.91 (FDR 0.03) | +1.89 | Bile acid metabolism; some CD-association literature |
| Blautia wexlerae | stable + | +2.00 (FDR 0.03) | +0.91 | Mixed literature on CD direction |

**Zero E1 candidates pass n_evidence = 3.** All 14 E1 candidates with n_evidence = 2 had *negative* within-substudy effects — they are ecotype-markers, not CD drivers; the within-ecotype call is leakage.

---

## The cost of the failure

| Metric | NB04 original | NB04c rigor-controlled |
|---|---|---|
| Headline claim (H2c) | "*C. scindens* paradox RESOLVED by stratification" | Paradox is not a paradox; *C. scindens* is genuinely CD↑ |
| Tier-A candidate count | 33 species | 3 species |
| Tier-A by ecotype | E1: 18, E3: 15 | E1: 0, E3: 3 |
| Phage-target plan for E1 patients | 18 candidates in queue | **Need to reformulate Pillar 2 for E1** |
| Evidence gating | within-ecotype CLR-MW only | bootstrap CI + LinDA + within-substudy meta (3-way independent) |
| Ecotype stability claim | "reproducible K = 4 consensus" | Bootstrap ARI 0.13–0.17 — marginally stable |

Had the project proceeded to NB05 on the NB04 Tier-A list (as REVIEW_1 and REVIEW_2 explicitly recommended), phage-targeting scoring and eventual UC Davis cocktail drafts for ~half of patients (E1) would have been built on a leakage-contaminated candidate list with no E1-appropriate candidates that survive confound-free analysis.

The specific irreversible cost is zero because we caught this before NB05; the latent cost — had the adversarial review not been run — is 2–3 notebooks of downstream work on false candidates, plus eventual UC-Davis-patient cocktail recommendations for E1 patients that would have targeted ecotype-marker species instead of CD-driver species.

---

## Lessons

### For BERIL project workflow

1. **Pair `/berdl-review` with an adversarial reviewer for any project whose conclusions inform downstream action** (experimental design, clinical recommendation, policy, further notebooks). The standard reviewer catches surface flaws reliably; it does not catch selection-on-outcome confounding, missing-null effect-size reporting, post-hoc decision rules, or data-structure-level unidentifiability. See `docs/discoveries.md` "Standard `/berdl-review` is over-optimistic on methodologically nuanced projects" entry (now in place before this analysis) — this project is the first concrete case study of that pattern.

2. **Proposed enhancement to `/submit`**: an optional `--adversarial` flag that runs both reviewers and writes a merged `REVIEW.md` with flags from both. Until that lands, the manual pattern is `bash tools/review.sh <proj>` followed by `Agent(subagent_type=general-purpose, prompt=<adversarial brief>)`.

3. **An adversarial reviewer is not the same as a harsher standard reviewer**. The adversarial framing that worked here was explicit: "You are looking for ways this analysis is wrong. Be direct, concrete, and unflattering. Flag any claim whose evidence depends on a choice of decision rule, any verdict that requires a null distribution that wasn't computed, any inference whose ground truth is part of the method that produced it." Generic "be critical" framing produced hedged, diplomatic reviews that differed from the standard reviewer mostly in tone.

### For microbiome / BERDL data analysis

4. **Feature leakage in stratified DA** — if you cluster samples by taxon abundance and then test differential abundance of the same taxa within cluster, your within-cluster effect sizes are mechanically inflated on cluster-defining taxa. The practical tests:
   - Held-out-species sensitivity (our §2): split species 50/50, cluster on half A, test on half B, compare top-30 list against within-cluster result on the full matrix. Jaccard < 0.3 = leakage dominates.
   - Leave-one-species-out (our §3): refit cluster without the taxon being tested, re-derive cluster labels, re-test held-out taxon.
   - Pathway-level clustering (not done here): define ecotypes on a functional matrix (KEGG, MetaCyc pathways) then test taxonomic DA — breaks the leakage cleanly but requires a pathway-abundance matrix.

5. **cMD pooled contrasts are substudy-confounded**. The healthy-cohort and disease-cohort studies in curatedMetagenomicData are almost entirely disjoint — a pooled CD-vs-HC LME with study random effect is unidentifiable. The confound-free contrasts are (a) **within-substudy CD-vs-nonIBD** on the few IBD studies that carry both groups (HallAB_2017, LiJ_2014, IjazUZ_2017, NielsenHB_2014), and (b) **meta-analysis of within-substudy effects** across those studies. Reported as a pitfall in `docs/pitfalls.md`.

6. **Hard-coded verdict logic is a red flag**. If your decision rule is `if p < 0.05 AND (pooled_direction == X): RESOLVED`, you are probably reporting selectively. Replace with TOST equivalence, bootstrap CIs, or explicit multi-evidence scoring.

7. **Jaccard on top-k selections needs a null**. Random-overlap for top-30 out of N filtered taxa is approximately 30/N — for N ≈ 300, that's 0.10. Any Jaccard reported without a permutation null and an empirical p-value is not evidence of divergence or similarity.

8. **Ecotype stability ≠ ecotype existence**. Bootstrap ARI on 80 % subsamples is the bar, not cross-method ARI at a single K. For this project, bootstrap ARI 0.13–0.17 is marginal; the framework is usable for stratified analysis but should be flagged as not externally replicable until MGnify projection is done.

### For automated review prompts

9. **Standard reviewer systematic blind spots**: the default `.claude/reviewer/SYSTEM_PROMPT.md` is tuned to reward methodological sophistication signals (compositional awareness, cross-method validation, documented limitations, saved outputs). It does not explicitly check for selection-on-outcome confounding, missing null distributions, post-hoc verdict logic, or study-design unidentifiability. These are exactly the issues that arise in nuanced observational microbiome analyses.

10. **Reading the prompt literally**: the default reviewer's structure (`Summary / Methodology / Reproducibility / Code Quality / Findings Assessment / Suggestions`) doesn't have an "inferential soundness" section. An enhancement would be to add one, prompted explicitly for: "What claim in this project depends on a decision rule you did not verify? What effect size is reported without a null?"

---

## Artifacts

- Notebooks: `notebooks/NB04_within_ecotype_DA.ipynb`, `notebooks/NB04b_analytical_rigor_repair.ipynb`, `notebooks/NB04c_rigor_repair_completion.ipynb`
- Reviews: `REVIEW_1.md`, `REVIEW_2.md` (standard, both concluded clean), adversarial review captured inline in `NB04b` markdown (cell 0) and in this document
- Data: `data/nb04b_*.tsv`, `data/nb04c_*.tsv` — the raw rigor-controlled evidence streams
- Figures: `figures/NB04b_jaccard_null.png` — permutation null + observed
- Discoveries: the "standard reviewer over-optimistic" meta-entry in `docs/discoveries.md` was written *before* this document; the NB04c-specific findings land there in a follow-up entry
- Pitfalls: the cMD substudy nesting and the feature-leakage-in-stratified-DA entries in `docs/pitfalls.md`

---

## Next steps (not part of this document)

1. Rewrite REPORT.md Pillar 2 section with rigor-controlled verdicts
2. Update RESEARCH_PLAN.md to v1.4 with the revised Pillar 2 scope (3 E3 candidates; E1 needs reformulation)
3. Add the two new pitfalls (cMD substudy nesting, feature leakage in stratified DA) to `docs/pitfalls.md`
4. Append NB04c findings to `docs/discoveries.md` (three entries: within-substudy as confound-free reference; feature leakage as a BERDL-wide pattern; cMD sub-study × diagnosis nesting as a data-structure invariant)
5. Commit the worktree state and prepare for merge / teardown
