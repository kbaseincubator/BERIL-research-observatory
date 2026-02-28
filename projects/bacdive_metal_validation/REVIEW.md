# Review: BacDive Metal Validation

**Reviewer**: Automated BERIL Reviewer
**Date**: 2026-02-28
**Verdict**: ACCEPT WITH REVISIONS

## Summary

This project validates the Metal Fitness Atlas's genome-based metal tolerance scores against BacDive isolation environment metadata at scale (97K strains, 25K with isolation data). The central finding — that heavy metal contamination isolates score d=+0.996 (p=0.006) above the environmental baseline — is confirmed in notebook outputs and represents a genuinely novel cross-database ecological validation. However, REPORT.md contains several numerical inconsistencies relative to notebook outputs that must be corrected before the report is considered accurate, most notably an incorrect match rate percentage (34.5% vs the actual 43.4%) and a mismatch between the pre-matching n=31 heavy metal group size cited in RESEARCH_PLAN.md/README.md and the post-matching n=10 actually used in all statistics.

## Strengths

1. **Main numerical claim verified**: The headline result (d=+1.00, p=0.006 for heavy metal contamination isolates) is confirmed by notebook `02_environment_metal_scores.ipynb` cell-6 output, which shows d=+0.996, p=5.84e-03 — legitimate rounding to d=+1.00, p=0.006.

2. **Dose-response gradient is robust and pre-registered**: The four-level gradient (heavy metal d=+1.00 > waste/sludge d=+0.57 > contamination d=+0.43 > industrial d=+0.20) matches H1b-H1c exactly as planned in RESEARCH_PLAN.md v2 and is confirmed by notebook cell-6 outputs for all four comparisons.

3. **Phylum-stratified analysis is executed correctly and well-interpreted**: Notebook `02_environment_metal_scores.ipynb` cell-9 confirms Pseudomonadota (delta=+0.040, p=0.000) and Actinomycetota (delta=+0.035, p=0.000) but not Bacillota (delta=-0.012, p=0.285) or Bacteroidota (delta=-0.008, p=0.456), and REPORT.md reproduces these numbers faithfully. The dual explanation offered (real biology vs. statistical power) is appropriately cautious.

4. **Power analysis is included and interpretively honest**: The power analysis in NB02 cell-4 correctly identifies that n=10 gives a minimum detectable effect of d=0.93, and REPORT finding 5 explicitly acknowledges the group is "at the detection limit." This is good scientific practice for a small-n result.

5. **Cross-project integration is appropriate**: The project correctly references metal_fitness_atlas (upstream data source), metal_specificity (88% core finding), and lab_field_ecology (rho=0.50, p=0.095 prior) without duplicating their analyses. The interpretation of how core metal genes can still produce between-species variation is scientifically coherent.

6. **Observatory standards mostly met**: Three notebooks with saved outputs are committed; all expected figures are present (`bridge_summary.png`, `metal_score_by_environment.png`, `utilization_vs_score.png`); `requirements.txt` covers all dependencies; RESEARCH_PLAN.md has a revision history; README.md has a Reproduction section.

## Issues

### Critical

**C1. Match rate percentage is wrong in REPORT.md and README.md.**

REPORT.md Bridge Summary table states "Matched to pangenome species: 42,227 (34.5%)". README.md also states "34.5%". The notebook output (NB01 cell-7) clearly prints: "Total matched: 42227 / 97334 strains (43.4%)". The 34.5% figure is actually the exact-match-only rate (33,535 / 97,334 = 34.45%), which the notebook separately reports. REPORT.md appears to have mistakenly used the exact-match-only percentage as the total match rate. This error propagates to the Abstract-equivalent text in README.md.

**Fix**: Change "34.5%" to "43.4%" in both REPORT.md and README.md. Add a clarifying note that 34.5% is the exact-match-only rate and 8.9% represents base-name matches.

**C2. Unique GTDB species count is inconsistent between REPORT.md and notebook.**

REPORT.md states "Unique GTDB species linked: 5,523". NB01 cell-7 output states "Unique GTDB species matched: 6426". NB01 cell-10 output does not separately report unique species. The 5,523 figure in REPORT.md has no traceable origin in the notebook outputs.

**Fix**: Verify the correct value from `data/matched_strains.csv` (e.g., `matched_strains['gtdb_species_clade_id'].nunique()`) and correct REPORT.md accordingly. If 5,523 reflects a later filtering step (e.g., strains with isolation data), this must be stated explicitly.

**C3. Heavy metal group n=31 vs n=10 is inconsistently described across documents.**

RESEARCH_PLAN.md H1a states "(BacDive cat3=#Heavy metal, n=31)". README.md states "heavy metal contamination isolates have significantly higher metal tolerance scores (d=+1.00, p=0.006)" without disclosing that only n=10 of those 31 BacDive strains matched to pangenome species. The REPORT.md table correctly shows n=10 but never explains the discrepancy with the n=31 cited in the plan. The power analysis in REPORT finding 5 states "minimum detectable effect size at 80% power is approximately d=0.90" — but the notebook computed this for n=10 (giving d_min=0.93), not n=31 (which would give approximately d=0.90). The REPORT appears to have used a pre-matching n=31 for the stated power threshold while reporting statistics based on the post-matching n=10.

**Fix**: Add a sentence to REPORT.md Section 5 (Power Analysis) explicitly stating: "Of 31 BacDive heavy metal contamination strains, only 10 matched to GTDB pangenome species by name; all statistics use this post-matching n=10." Correct the stated minimum detectable d from 0.90 to 0.93 (the value computed by the notebook for n=10), or recompute and show for both n=10 and n=31.

### Important

**I1. Host-associated group effect direction contradicts H1d without explanation.**

RESEARCH_PLAN.md H1d states: "Host-associated bacteria have *lower* metal scores than free-living environmental bacteria." However, REPORT.md Table 1 reports host-associated d=+0.14 (p<0.0001), meaning host-associated bacteria score *higher* than the environmental baseline, the opposite of the prediction. NB02 cell-6 confirms this: host median 0.1940 vs environmental median 0.1869, delta=+0.0071. The REPORT.md does not discuss this result anywhere in the Interpretation section. This is a falsified sub-hypothesis that warrants explicit discussion — it may reflect BacDive sampling bias toward clinical host-associated isolates that are well-characterized (and thus better-represented in GTDB) or a genuine biological signal.

**Fix**: Add a paragraph to REPORT.md Interpretation section addressing the unexpected direction of the host-associated result and its implications for H1d.

**I2. Power analysis mismatch between REPORT text and notebook output.**

REPORT.md finding 5 states "minimum detectable effect size at 80% power is approximately d=0.90." The notebook cell-4 output states: "Minimum detectable effect (Cohen's d) at 80% power: 0.93." The difference is small but consequential because the headline d=0.996 barely exceeds 0.93 (it exceeds by 0.07 SDs) and the REPORT's stated 0.90 threshold makes the result appear more comfortably powered than it is.

**Fix**: Correct to d=0.93 (as computed in notebook cell-4) or explain the source of 0.90.

**I3. Cohen's d computation uses pooled SD, not environmental SD — this should be documented.**

NB02 cell-6 computes Cohen's d as `(group.mean() - env_baseline.mean()) / pooled_std` where `pooled_std = sqrt((group.std()**2 + env_baseline.std()**2) / 2)`. For the heavy metal group (n=10), the pooled SD is strongly influenced by the very small group, potentially inflating or deflating the estimate relative to using the environmental SD alone. The REPORT does not specify which Cohen's d formula was used. For Mann-Whitney tests with highly unequal group sizes, rank-biserial correlation is the preferred effect size; or Glass's delta (using only the control SD) would be more interpretable.

**Fix**: Add a methods note in REPORT.md specifying the pooled-SD Cohen's d formula. Consider adding rank-biserial correlation as a supplementary effect size for the heavy metal comparison.

### Minor

**m1. RESEARCH_PLAN.md lists "GCA accession-based matching" as the primary approach** in the Query Strategy section, but the actual implemented approach uses species name matching (no GCA join was performed). The plan describes a `kbase_ke_pangenome.genome` query that was not executed. This is not a scientific error — species name matching is a valid alternative — but the discrepancy between planned and executed bridge strategy is not acknowledged in the REPORT.md Limitations section.

**Fix**: Add a sentence to REPORT.md Limitations noting that the GCA accession-based bridge was not implemented; species name matching was used instead, which has both advantages (does not require Spark) and disadvantages (GTDB/LPSN naming divergence inflates the unmatched fraction).

**m2. REPORT.md Results table shows blank median and mean columns** for all environment groups ("—" placeholders). These values are computed in NB02 cell-6 (e.g., environmental median=0.1869, heavy metal median=0.2396) and should be filled in for completeness and for readers who want to verify claims without running notebooks.

**Fix**: Populate the Median Score and Mean Score columns in REPORT.md Table 1 using the values from NB02 cell-6 output.

**m3. NB03 metal utilization result (d=-0.57) is surprising and unreported in README.**

Notebook NB03 cell-4 finds that positive metal utilizers have *lower* metal tolerance scores than negative utilizers (d=-0.57, p=0.14). While correctly flagged as underpowered and exploratory in REPORT.md, the README.md status line does not mention this or qualify the main finding. For a reader checking only the README, the unexpected negative-direction utilization result is invisible.

**Fix**: Minor — optionally add one sentence to README status about the inconclusive utilization finding, or leave as-is given its exploratory nature and lack of significance.

**m4. No note in NB01 or NB02 indicating whether BERDL JupyterHub access is required.**

PROJECT.md standards specify that Spark-dependent notebooks must include a header note "Requires BERDL JupyterHub." NB01 and NB02 both run locally (no Spark), which is correct and their README documents it. However, neither notebook has the header note stating it does not require JupyterHub — this is fine but inconsistent with the standard for the opposite case. No action strictly required.

## Scientific Assessment

The project makes a credible and novel contribution: it provides the first large-scale validation of a genome-based metal tolerance prediction method against real isolation ecology data. The statistical findings for the primary hypothesis (H1a/H1b/H1c) are solid — the dose-response gradient across contamination categories is both pre-registered and confirmed with appropriate non-parametric tests and phylum stratification. The phylogenetic confounding analysis is methodologically appropriate and its partial results (signal within Pseudomonadota and Actinomycetota but not Bacillota or Bacteroidota) are interpreted with appropriate nuance. The key limitation — that n=10 heavy metal isolates matched to pangenome species places the result near the detection threshold — is acknowledged. The conceptual bridge between this project's "between-species" signal and metal_specificity's "within-species" core gene finding is scientifically coherent. The main weakness is that BacDive's isolation environment categories conflate mechanistically distinct environments (e.g., "Industrial" includes both metal smelting sites and fermentation facilities), and the paper does not discuss this as a potential source of attenuation in the observed effect sizes. The unexpected positive direction of the host-associated result (d=+0.14, H1d predicted negative) is a finding of genuine biological interest that is entirely absent from the Interpretation section.

## Reproducibility

The project meets observatory reproducibility standards for data and code. All three notebooks have saved outputs. All five expected data files (`bacdive_pangenome_bridge.csv`, `matched_strains.csv`, `environment_metal_scores.csv`, `phylum_stratified_tests.csv`, `metal_utilization_validation.csv`) and three figures are present. The `requirements.txt` covers all six dependencies correctly. Notebook execution order is documented in README.md and the bridge data from NB01 correctly flows into NB02 and NB03. The pipeline requires no Spark and can be reproduced locally. The absolute path hardcoded in NB01 (`MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory'`) will break for any other user cloning the repository; this should be made relative or configurable. The RESEARCH_PLAN.md revision history shows appropriate pre-registration of the power analysis and phylum stratification (v2, 2026-02-28). Despite the numerical inconsistencies in REPORT.md identified above, the underlying analysis in the notebooks is internally consistent and the corrected values are straightforward to recover from notebook outputs.
