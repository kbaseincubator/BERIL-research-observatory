---
reviewer: BERIL Automated Review
date: 2026-02-19
project: pathway_capability_dependency
---

# Review: Metabolic Capability vs Dependency

## Summary

This is a well-designed and largely well-executed project that addresses a genuine gap in microbial ecology: distinguishing genomic capability (GapMind predicts a pathway) from metabolic dependency (fitness data shows the pathway matters). The three-tier analytical framework is clearly motivated, the integration with prior BERIL projects is unusually thorough, the literature context is solid, and the data cache (19 CSV files, ~3.9 GB) confirms the analysis ran to completion. The key findings — 35.4% Active Dependencies, condition-dependent Latent Capabilities, strong partial-rho correlation with pangenome openness — are scientifically interesting and well-situated in the BQH literature. The main weaknesses are: (1) all five notebooks were committed with empty outputs, so the audit trail exists only in external run scripts and CSV files; (2) the notebook source code retains at least one confirmed-wrong SQL column pattern (from the `experiment` table pitfall this project itself discovered); (3) the phylogenetic "control" in NB03 uses genus-first-letter grouping rather than actual taxonomy; and (4) the finding that "all Latent Capabilities become important under some condition" is potentially circular given the threshold design. These are addressable without re-running the core analysis.

---

## Methodology

**Research question and hypotheses.** The question is clearly stated and testable. The four-category classification framework (Active Dependency / Latent Capability / Incomplete but Important / Missing) is well-defined and correctly motivated by the Black Queen Hypothesis. Hypotheses H0, H1a, H1b, H1c, and H2 are explicit and falsifiable, and the RESEARCH_PLAN documents expected outcomes for each — including the prior `pangenome_openness` null result that tempers expectations for H1b.

**Approach soundness.** The two-tier strategy (Tier 1: fitness-validated, ~7 organisms; Tier 2: conservation proxy, 27K species) is appropriate given that RB-TnSeq data exists for only a small fraction of species. The composite importance score (40% essentiality, 30% breadth, 30% magnitude) reflects lessons from `fitness_effects_conservation` that breadth predicts conservation better than magnitude. Condition-type stratification is well-motivated by `core_gene_tradeoffs`. Phylogenetic controls are planned in the RESEARCH_PLAN and discussed in notebook markdown, but the actual implementation is weaker than planned (see Code Quality).

**Data sources.** All key tables are identified with row counts and filter strategies in RESEARCH_PLAN. The GapMind-FB coverage gap (7/48 FB organisms with GapMind data) is flagged explicitly — this is an important limitation that the project handles correctly by documenting it prominently.

**Methodological change from RESEARCH_PLAN v3.** The switch from the pangenome link table + eggNOG approach (NB02 original design) to the FB-native KEGG annotation path (`besthitkegg → keggmember → EC → KEGG map → GapMind pathway`) is documented clearly in RESEARCH_PLAN v3. However, the NB02 notebook source code still shows the original link-table approach, creating a disconnect between notebook documentation and what was actually executed. The run scripts likely contain the correct v3 code, but reviewers cannot verify this from the notebooks alone.

**Reproducibility.** The README `Reproduction` section clearly distinguishes NB01 (Spark, BERDL) from NB02–05 (local). The three-step NB01 execution sequence is explained with explicit script names. The NB03→NB04 independence note (both can run after NB01) is useful. This section meets the BERIL standard.

---

## Code Quality

**Critical: Notebook outputs are entirely empty.** All five notebooks (`01_data_extraction.ipynb` through `05_synthesis.ipynb`) have zero cells with saved output — every `outputs` array is empty. This is the most significant issue in the project. Notebooks are the primary audit trail and methods documentation; without saved outputs, a reader must re-run the full pipeline to see any intermediate result, table, or figure. The `[env_embedding_explorer]` pitfall in `docs/pitfalls.md` explicitly identifies this as a BERIL anti-pattern. The analysis was clearly run via `run_nb01.py` and companion scripts — the CSVs and figures prove execution — but the notebooks themselves do not reflect what ran. At minimum, NB02–05 (which run locally on cached data in seconds) should be re-executed with `jupyter nbconvert --to notebook --execute --inplace` before submission.

**NB01 — SQL column names inconsistent with pitfalls.md.** The condition-type extraction code (cell 15 of `01_data_extraction.ipynb`) uses:
```sql
SELECT name as expName, orgId,
  CASE WHEN LOWER(Condition_1) LIKE '%carbon%'
       OR LOWER(Group) LIKE '%carbon%'
```
But `docs/pitfalls.md` (tagged `[pathway_capability_dependency]`) explicitly states: the table is `experiment` (not `exps`), columns are `expName` (not `name`), `expGroup` (not `Group`), and `condition_1` (not `Condition_1`). The fact that `fb_fitness_by_condition_type.csv` exists (58 MB) means the extraction succeeded — but the code in the notebook would not reproduce the result as written. The executed code lives in `run_nb01_remaining.py` or `run_nb01_final.py`, not the notebook.

**NB01 — `.toPandas()` on core pathway status (potential OOM).** Cell 7 uses `.toPandas()` to extract `gapmind_core_pathway_status.csv`. The resulting file is 1.5 GB. The RESEARCH_PLAN performance plan explicitly warns: "the species pathway summary (~23M rows) must NOT be collected to driver," and recommends Spark `.write.csv()` for large extracts. The `gapmind_core_pathway_status` table covers 293K genomes × 80 pathways × multiple scopes — it likely exceeds the same OOM threshold. If this succeeded, it was fragile. The notebook should use `.write.csv()` with a partitioned write, consistent with the approach used for `species_pathway_summary`.

**NB02 — row-wise `apply` for essential gene marking.** Cell 8 uses:
```python
pathway_fitness['is_essential'] = pathway_fitness.apply(
    lambda r: (r['orgId'], r['locusId']) in essential_set, axis=1
)
```
`docs/pitfalls.md` (`[core_gene_tradeoffs]`) explicitly flags this as "orders of magnitude slower than Merge." The correct pattern is a merge on `['orgId', 'locusId']`. This likely worked (the dataset is relatively small for Tier 1), but it's inconsistent with documented best practices.

**NB03 — phylogenetic stratification uses genus-first-letter as proxy.** The code for the "phylogenetic control" in NB03 uses:
```python
merged_filtered['genus'] = merged_filtered['clade_name'].str.extract(r's__(\w+)_')[0]
merged_filtered['genus_first_letter'] = merged_filtered['genus'].str[0]
```
Grouping by the first letter of the genus name is not a phylogenetic control — it is alphabetical grouping. The RESEARCH_PLAN calls for stratification by "GTDB phylum/class" and specifically warns about the `ecotype_analysis` finding that phylogeny dominates gene content in 60.5% of species. The pangenome table contains `gtdb_species_clade_id` which encodes GTDB taxonomy; phylum-level grouping could be derived from the GTDB lineage string without additional Spark queries. The REPORT claims the correlation "holds across 18 of 21 phylogenetic groups tested" and cites phylum-level stratification, but the notebook code does not implement this — this discrepancy needs resolution.

**NB02 — classification threshold circularity.** The importance threshold is set to the median importance score across all organism-pathway pairs (`importance_median = pathway_agg_with_completeness['importance_score'].median()`). By definition, using the median as threshold produces approximately 50% important / 50% not-important classifications. The Latent Capability finding that "all 66 pathways become important under some condition type" is then analyzed using condition-type data where the same median threshold is applied to condition-specific subsets. Because condition-specific subsets have fewer observations (higher noise), the median threshold applied to them may classify more things as "important" — making the "all Latent Capabilities become conditionally active" finding sensitive to this threshold design. A threshold calibrated against an independent validation set (e.g., the known essentiality from `essential_metabolome`) would be more defensible.

**GapMind multiple-rows-per-genome-pathway pitfall (correctly handled).** NB01 uses `MAX(score)` grouped by `genome_id, pathway` which is exactly the correct approach per the `[pangenome_pathway_geography]` pitfall. This pitfall is correctly handled.

**String-typed fitness columns (correctly handled).** NB01 uses `CAST(fit AS FLOAT)` consistently throughout the fitness extraction queries. The string-typed numeric pitfall is properly addressed.

**Pangenome ID prefix mismatch (correctly flagged in RESEARCH_PLAN).** The `gapmind_pathways` genome_id format mismatch (`GCF_...` vs `RS_GCF_...`) is documented in RESEARCH_PLAN and the NB01 code handles this. Good.

**SQL correctness.** The major SQL queries are structurally sound. Aggregations use appropriate `GROUP BY` clauses. The `PERCENTILE_APPROX` function for median fitness is correct for Spark SQL. The `CASE WHEN ... THEN 1 ELSE 0 END` pattern for binary aggregation is correct.

**requirements.txt gaps.** The file lists 5 libraries (`pandas, numpy, matplotlib, seaborn, scipy`) for local execution (NB02–05). NB04 uses `scipy.cluster.hierarchy` (covered by scipy). However, `jupyter` is not listed — needed to execute notebooks via `nbconvert`. This is a minor gap but should be added for reproducibility.

---

## Findings Assessment

**Finding 1 (35.4% Active Dependencies).** The numbers are consistent across README, REPORT, and `figures/summary_statistics.txt`. The breakdown (Active 35.4%, Latent 41.0%, Incomplete but Important 14.9%, Missing 8.7%) is internally consistent and plausible. The scope (7 organisms, 23 pathways, 161 pairs) is modest but clearly documented. The `tier1_pathway_classification.csv` data file confirms analysis ran to completion.

**Finding 2 (All Latent Capabilities become conditionally active).** The finding is scientifically interesting and consistent with `core_gene_tradeoffs`. However, the claim "all 66 Latent Capabilities shift under at least one condition" should be scrutinized. With only a few thousand experiments in the Fitness Browser and a median threshold applied per condition type, it is not surprising that every pathway exceeds the threshold somewhere. The REPORT should explicitly state how many condition types were tested per pathway and what the threshold values were for each condition type — currently this detail is missing. The `tier1_condition_type_analysis.csv` (65 KB) exists, but readers cannot verify the claim without notebook outputs showing the intermediate steps.

**Finding 3 (Conservation validation: 0.986 vs 0.975).** The REPORT correctly identifies this as a weak signal ("small but consistent direction") and explains it by the model organism bias. However, no statistical test is reported for this difference. The REPORT should include a Mann-Whitney U test or similar comparison between the core-completeness distributions of Active Dependencies vs Latent Capabilities, with a p-value. Without this, the validation is directionally consistent but unconfirmed.

**Finding 4 (Partial rho = 0.530, p = 2.83e-203).** This is the strongest quantitative result. The partial Spearman correlation strengthening after genome-count control (0.327 → 0.530) is well-explained and scientifically interesting. The claim that "signal holds in 18 of 21 phylogenetic groups tested" appears in the REPORT but the notebook code uses genus-first-letter grouping (see Code Quality above) — this specific claim should either be verified or the figure corrected.

**Finding 5 (Amino acid biosynthesis accessory dependence).** The top-5 accessory-dependent pathway table (leu/val gap=0.146, arg=0.141, lys/thr=0.140) is internally consistent with `core_vs_all_pathway_completeness.csv` (151 MB file present). The branched-chain amino acid story (leucine/valine sharing) is scientifically coherent with the BQH literature. This finding is well-supported.

**Finding 6 (Metabolic ecotypes: rho=0.322 partial).** Results are consistent with `ecotype_summary.csv` and `metabolic_ecotypes.csv`. The 50% dendrogram cut threshold is acknowledged as arbitrary in the Limitations section. The maximum of 8 ecotypes in *Alistipes onderdonkii* and *Barnesiella intestinihominis* is biologically plausible for gut commensals. The genome-count control is correctly applied. The AlphaEarth niche breadth analysis mentioned in the RESEARCH_PLAN (for H2) was not executed or reported — this should be documented as a future direction or acknowledged as out of scope.

**Limitations section.** The 7-point Limitations section is thorough and honest. It correctly identifies the lab fitness vs natural selection confound, the GapMind scope restriction, the model organism bias for Tier 1, and the fixed threshold for ecotype clustering. This section is exemplary for a BERIL project.

**REPORT structure.** The REPORT follows the three-file BERIL convention correctly. It does not duplicate the RESEARCH_PLAN and cross-references it appropriately. The connection to other BERDL projects table is well-executed and adds genuine scientific context.

---

## Suggestions

1. **(Critical)** Execute NB02–NB05 notebooks to capture outputs before final submission. Use `jupyter nbconvert --to notebook --execute --inplace notebooks/0X_*.ipynb` for each local notebook. NB01 outputs cannot be re-captured without the Spark cluster, but NB02–05 run in minutes on the cached CSVs. Saved outputs are required for audit trail and for the `/synthesize` reviewer to verify claims.

2. **(Critical)** Synchronize NB01 source code with what was actually executed. The condition-type SQL in cell 15 references `name`, `Condition_1`, and `Group` — the wrong column names per `docs/pitfalls.md`. The correct code (with `expName`, `condition_1`, `expGroup`) should be reflected in the notebook. If the fix lives in `run_nb01_remaining.py`, copy the corrected cell into the notebook.

3. **(High)** Fix the phylogenetic stratification in NB03 to use actual GTDB taxonomy (phylum/class from the `clade_name` prefix or a `gtdb_taxonomy` join) instead of genus-first-letter grouping. The REPORT claim of "18 of 21 phylogenetic groups" depends on this being a real taxonomic grouping. The GTDB species clade name encodes taxonomy; parsing the phylum level from the GTDB lineage string (or joining a cached taxonomy table) would take a few lines of pandas.

4. **(High)** Add a statistical test for the conservation validation (Finding 3). Report a Mann-Whitney U or Kruskal-Wallis test comparing core-completeness distributions across the four categories. Without p-values, the 0.986 vs 0.975 gap is visually plausible but scientifically unverified. This is straightforward to add to NB02.

5. **(Medium)** Document the Latent Capability condition-type result more explicitly. The REPORT states "all 66 Latent Capabilities become fitness-important under at least one condition" but does not report what fraction become important under *each* condition type, or how many condition experiments were used per type per pathway. Add a breakdown table (condition type × pathway count) to NB02 and carry it into the REPORT.

6. **(Medium)** Discuss the median-threshold circularity for the importance score. In the REPORT's Limitations section, add a note that the median threshold by construction splits pathways 50/50 into important vs not-important under aggregate conditions. Discuss whether calibrating the threshold against known essentials (e.g., from `essential_metabolome`) would change the category distribution and conclusions.

7. **(Medium)** Replace the row-wise `apply` for essential gene marking in NB02 with a merge:
   ```python
   essentials_flag = essentials[['orgId', 'locusId']].assign(is_essential=True)
   pathway_fitness = pathway_fitness.merge(essentials_flag, on=['orgId', 'locusId'], how='left')
   pathway_fitness['is_essential'] = pathway_fitness['is_essential'].fillna(False).astype(bool)
   ```
   This is both faster and consistent with the `[essential_genome]` fillna-bool pitfall in pitfalls.md.

8. **(Low)** Add `jupyter` to `requirements.txt` so that the `nbconvert --execute` reproduction path is self-documenting.

9. **(Low)** Document explicitly in the REPORT's Limitations or Data section that the AlphaEarth niche breadth correlation (planned in RESEARCH_PLAN for H2) was not executed, as AlphaEarth only covers 28% of genomes. Noting this as a future direction prevents readers from expecting to find that analysis.

10. **(Low)** NB01 cell 7 uses `.toPandas()` to materialize `gapmind_core_pathway_status.csv` (1.5 GB). Consider switching to `spark.write.csv()` consistent with the explicitly documented performance plan in RESEARCH_PLAN. If the current approach completed without OOM, note the actual memory used to help future projects assess the trade-off.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-19
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 5 notebooks, 19 data files, 20 figures + 1 summary stats file, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
