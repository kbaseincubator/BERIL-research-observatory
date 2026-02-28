# Review: BacDive Metal Validation (Revision 2)

**Reviewer**: Automated BERIL Reviewer
**Date**: 2026-02-28
**Verdict**: ACCEPT WITH REVISIONS

## Summary

This project provides a large-scale validation of the Metal Fitness Atlas's genome-based metal tolerance predictions against BacDive isolation environment metadata (97K strains, 25K with isolation data). All five issues flagged as Critical or Important in the prior two reviews are now resolved: match rates are correct, species counts are correct, the n=10 vs n=31 discrepancy is documented, the Cohen's d formula is stated, and Table 1 is fully populated. Three minor issues remain: the phylum-stratified results table still contains "—" placeholders for sample sizes, the hardcoded absolute path in NB01 persists, and README.md still omits the inconclusive utilization direction.

## Prior Issues Status

| Issue | Severity | Description | Status |
|-------|----------|-------------|--------|
| C1 | Critical | Match rate reported as 34.5% instead of 43.4% | FIXED — REPORT.md and README.md both correctly state 43.4%; 34.5% is correctly identified as the exact-match-only rate |
| C2 | Critical | Unique GTDB species count stated as 5,523 instead of 6,426 | FIXED — REPORT.md Bridge Summary reads 6,426, confirmed by NB01 cell-7 output |
| C3 | Critical | n=31 (plan) vs n=10 (actual) inconsistency unexplained; power threshold cited for wrong n | FIXED — REPORT.md Finding 5 explicitly states only 10 of 31 heavy metal strains matched; minimum detectable d correctly stated as 0.93, matching NB02 cell-4 |
| I1 | Important | Host-associated result (d=+0.14) contradicts H1d prediction without discussion | FIXED — REPORT.md contains dedicated paragraph explaining genome-size confounding via Pseudomonadota pathogen overrepresentation |
| I2 | Important | Power threshold stated as d=0.90 in REPORT but notebook computed d=0.93 | FIXED — REPORT.md Finding 5 now reads "approximately d=0.93" matching NB02 cell-4 exactly |
| I3 | Important | Cohen's d pooled-SD formula undocumented | FIXED — REPORT.md Finding 1 now states: "Cohen's d is computed as (mean_group - mean_baseline) / pooled_SD, where pooled_SD = sqrt((SD_group² + SD_baseline²) / 2)" |
| m1 | Minor | GCA bridge not implemented but not acknowledged as deviation from plan | FIXED — REPORT.md Limitations notes species-level matching was used and GCA accession matching "would improve coverage" |
| m2 | Minor | Median and mean columns in Table 1 are "—" placeholders | FIXED — all values now populated and verified against NB02 cell-6 output (see verification below) |
| m3 | Minor | Inconclusive utilization finding direction not flagged in README | NOT FIXED — README.md status line still omits the d=-0.57, p=0.14 utilization result |
| m4 | Minor | No "does not require JupyterHub" note in NB01/NB02 | NOT FIXED — no header note added (low priority; acceptable) |
| m5 | Minor | Hardcoded absolute path in NB01 cell-1 | NOT FIXED — MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory' still present |

**Table 1 verification (NB02 cell-6 vs REPORT.md):**

| Environment | NB02 median | REPORT median | NB02 mean | REPORT mean | NB02 delta | REPORT delta |
|-------------|-------------|---------------|-----------|-------------|------------|--------------|
| Heavy metal | 0.2396 | 0.240 | 0.2355 | 0.236 | +0.0528 | +0.053 |
| Waste/sludge | 0.2188 | 0.219 | 0.2177 | 0.218 | +0.0319 | +0.032 |
| All contamination | 0.2148 | 0.215 | 0.2114 | 0.211 | +0.0280 | +0.028 |
| Industrial | 0.1987 | 0.199 | 0.2023 | 0.202 | +0.0119 | +0.012 |
| Host-associated | 0.1940 | 0.194 | 0.2009 | 0.201 | +0.0071 | +0.007 |

All REPORT values match NB02 output to 3 significant figures. No discrepancies.

## Remaining Issues

### Critical

None.

### Important

None.

### Minor

**m3 (carried from prior review). README.md omits the inconclusive metal utilization direction.**

README.md status line reads: "heavy metal contamination isolates have significantly higher metal tolerance scores (d=+1.00, p=0.006). Signal is dose-dependent..." with no mention of the metal utilization phenotype analysis. NB03 finds d=-0.57, p=0.14 (n=24), which is directionally opposite to H1e and explicitly exploratory. REPORT.md handles this correctly, but README.md gives an exclusively positive summary to readers who do not open the report.

Fix: Add one sentence to README.md, e.g., "Metal utilization phenotype validation was inconclusive (n=24 matched records, p=0.14)."

**m5 (carried from prior review). Hardcoded absolute path in NB01 cell-1.**

NB01 cell-1 contains `MAIN_REPO = '/home/psdehal/pangenome_science/BERIL-research-observatory'`. Any user who clones the repository to a different location will get a FileNotFoundError when loading BacDive data and metal atlas scores. This was flagged in the prior review and was not addressed.

Fix: Replace with a relative path, e.g., `MAIN_REPO = os.path.abspath(os.path.join(PROJ, '..', '..', '..'))`, or make it configurable via `os.environ.get('BERIL_REPO', ...)`. Add a one-line note to README.md if an environment variable approach is used.

**Phylum-stratified results table has "—" for sample size columns.**

REPORT.md Section "Results / Phylum-Stratified Results" shows "—" for n(contam) and n(env) in all four rows of the table. NB02 cell-9 prints these values explicitly: Pseudomonadota (contam=85, env=5,655), Actinomycetota (contam=62, env=772), Bacillota (contam=19, env=492), Bacteroidota (contam=5, env=156). This is the same class of issue as the previously fixed m2: the table was populated for the main environment comparisons but not for the phylum-stratified table.

Fix: Populate the n(contam) and n(env) columns in the phylum-stratified results table using the values from NB02 cell-9.

## Scientific Assessment

The project makes a credible and novel contribution: the first large-scale cross-database validation of a genome-based metal tolerance prediction method against real isolation ecology (n=42,227 matched strains, 6,426 unique GTDB species). The central finding is statistically robust — the dose-response gradient (heavy metal d=+1.00 > waste/sludge d=+0.57 > all contamination d=+0.43 > industrial d=+0.20) is pre-registered in RESEARCH_PLAN.md v2 and confirmed by NB02 outputs for all four comparisons. The phylum-stratified analysis appropriately identifies that the signal holds within Pseudomonadota and Actinomycetota but is absent in Bacillota (p=0.285) and Bacteroidota (p=0.456), with the dual biological and statistical-power explanation being appropriately cautious. The explanation of the host-associated result (d=+0.14, contradicting H1d) as genome-size confounding via Pseudomonadota pathogen overrepresentation is scientifically coherent. The primary outstanding scientific concern is that the heavy metal group effect size (d=+0.996) is reported as "+1.00" throughout — this rounding is technically defensible but slightly obscures that the result only barely clears the pre-computed detection threshold of d=0.93. The Limitations section acknowledges this honestly. One issue not discussed is that the "Industrial" BacDive category likely aggregates mechanistically dissimilar environments (metal smelting, food fermentation, wastewater treatment), which would attenuate the industrial effect size estimate (d=+0.20) and may explain its relatively weak signal; this would strengthen rather than undermine the central conclusion but is worth noting as a limitation.

## Reproducibility

The project meets observatory reproducibility standards for committed outputs. All three notebooks have saved outputs, all five expected data files and three figures are present, and requirements.txt covers the necessary dependencies. The pipeline requires no Spark and can be reproduced locally from the committed data files in data/bacdive_ingest/ and projects/metal_fitness_atlas/data/. The RESEARCH_PLAN.md revision history documents pre-registration of the power analysis and phylum stratification in v2, which is good scientific practice. The one persistent reproducibility barrier is the hardcoded absolute path in NB01 cell-1 (MAIN_REPO = '/home/psdehal/...'), which will fail on any other machine. Until this is fixed, the notebook cannot be re-executed by an independent reviewer without manually editing cell-1. This is the only remaining obstacle to full reproducibility.
