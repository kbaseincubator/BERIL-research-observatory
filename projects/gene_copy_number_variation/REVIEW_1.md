---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-5)
date: 2026-07-07
project: gene_copy_number_variation
---

# Review: Gene Copy Number Variation Across Pangenome Functional Categories

## Summary

This project delivers a rigorous, well-executed test of the dosage-balance hypothesis in bacterial pangenomes at unprecedented scale. The central finding — that adaptive gene clusters show 8.14× higher copy number variation than housekeeping clusters across 24 species and 5 phyla (p = 5.96×10⁻⁸, 24/24 species direction-consistent) — is statistically compelling and biologically interpretable. The core/accessory interaction analysis (NB04) adds important mechanistic depth, demonstrating that the class effect concentrates in accessory clusters rather than being a genome-wide property. The methodology is sound, the statistical analysis is appropriate and well-controlled (paired Wilcoxon, BH-FDR correction), and the research plan documents a thoughtful progression from pilot to scale-up with transparent metric refinement.

**However, the project has a critical reproducibility gap**: Notebook 02 contains zero saved outputs (0/12 cells), and the other notebooks are only partially executed (7/16, 9/18, 9/17, 6/10 cells with outputs). While the data artifacts exist in `data/` and figures exist in `figures/`, a reader cannot see the analysis progression without re-running ~80 minutes of Spark queries. The README's Reproduction section is marked "TBD" and there is no `requirements.txt`. These gaps prevent the project from meeting BERIL's reproducibility standard as written, despite the underlying science being strong.

## Methodology

### Research Question and Approach

The research question is clearly stated, testable, and addresses a genuine gap: existing pangenome studies focus on presence/absence, not within-genome copy number. The hypothesis structure (H0 vs H1a/b/c) is well-formed with pre-registered success criteria. The operationalization — cluster-carrier-weighted multi-copy rate rather than binary "any multi-copy" flags — is methodologically sound and well-justified by the pilot results (NB01 binary metric gave only 1.4× effect; NB01b weighted metric gave 3.3×).

The query strategy is appropriate for billion-row tables: per-species iteration over the 3-way `gene × gene_genecluster_junction × gene_cluster` join, with Spark-side aggregation before collection. The species selection (50–249 genomes each, stratified across 5 phyla) balances statistical power with computational feasibility.

**Plan revision transparency**: The RESEARCH_PLAN.md documents two revisions (v1 → v2 after pilot), including the decision to relax the magnitude threshold from 3× to 2× and to reclassify COG categories J and C from housekeeping to "mixed" based on known paralog cases (rRNA operons, ribosomal protein duplicates, cytochrome paralogs). This is excellent practice — the plan shows the reasoning, not just the final choice.

### Data Sources

Data sources are clearly identified: all tables come from `kbase_ke_pangenome`, with explicit column usage documented. The table list in RESEARCH_PLAN.md includes row counts and filter strategies. The generated data files are well-documented in REPORT.md with row counts and descriptions.

**One namespace issue**: The project uses the underscore-form `kbase_ke_pangenome` instead of the dotted `kbase.ke_pangenome`. This is correct for the current Delta-to-Iceberg migration state (as noted in `docs/pitfalls.md`), but the project should verify that the collection has not migrated since execution. The extraction script and all notebooks consistently use the underscore form, so there is no internal inconsistency.

### Reproducibility — Critical Gaps

**Notebook outputs (major gap)**: 
- `01_pilot_exploration.ipynb`: 7/16 cells with outputs
- `01b_pilot_refined_metrics.ipynb`: 9/18 cells with outputs
- `02_multi_species_scale.ipynb`: **0/12 cells with outputs**
- `03_statistical_analysis.ipynb`: 9/17 cells with outputs
- `04_core_accessory_interaction.ipynb`: 6/10 cells with outputs

Notebook 02 in particular has no saved outputs at all. The REPORT states that "the extraction itself moved to `src/extract_multi_species.py`", which is documented in the project's `memories/pitfalls.md` as a workaround for `nbconvert --execute` fragility. This is a reasonable technical choice, but NB02 should still contain outputs showing the concatenation of per-species CSVs and basic sanity checks — even if the extraction ran externally, the notebook is the natural place to document what was loaded and verified.

**Impact**: A reader opening the notebooks sees mostly empty output cells and must either trust the figures/data files or re-run 80 minutes of Spark queries to verify the pipeline. This falls short of BERIL's "notebooks with saved outputs" standard.

**Figures**: The `figures/` directory contains 5 PNG files corresponding to the figures cited in REPORT.md. This is good coverage across the analysis stages (pilot binary, pilot refined, species-level rates, phylum comparison, core/accessory interaction).

**Dependencies**: No `requirements.txt` or `environment.yml` exists. The notebooks import `berdl_notebook_utils`, `pandas`, `numpy`, `matplotlib`, `scipy`, and `statsmodels`, but versions are not pinned. For a project relying on statistical tests (Wilcoxon, BH-FDR), version differences could affect p-values.

**Reproduction guide**: The README's Reproduction section is marked "TBD — add prerequisites and step-by-step instructions after analysis is complete." The analysis *is* complete (REPORT drafted, status = "awaiting review"), so this section should have been filled. A reader does not know:
- Which notebooks need Spark vs can run locally
- How to invoke `src/extract_multi_species.py` (arguments? expected runtime?)
- Whether `data/per_species/*.csv` files must be regenerated or are committed

**Recommendation**: Before `/submit`, the author should:
1. Re-run all notebooks with `jupyter nbconvert --execute --inplace` (or equivalent) to populate outputs, OR document in README why outputs are omitted and assert that figures/data files are the canonical artifacts
2. Fill the README Reproduction section with a step-by-step guide
3. Add a `requirements.txt` with pinned versions of scipy, statsmodels, matplotlib, pandas, numpy
4. For NB02, add at least a few cells with outputs showing the concatenation and sanity checks of the per-species CSVs

## Code Quality

### SQL and Spark Usage

The SQL queries are correct and efficient. The per-species 3-way join is filtered on both `genome.gtdb_species_clade_id` and `gene_cluster.gtdb_species_clade_id` (cell-5 of NB01, lines 10–13 of `src/extract_multi_species.py`), which is the recommended pattern from `docs/pitfalls.md` for billion-row joins. Aggregation happens in Spark before `.toPandas()` collection, avoiding memory issues.

The use of a standalone resumable Python script (`src/extract_multi_species.py`) for the 24-species extraction is a good engineering choice and directly addresses the pitfall documented in `memories/pitfalls.md`. The script has:
- Incremental per-species CSV output (resumable)
- Skip-if-exists logic
- Streaming progress via `print(..., flush=True)`
- Clear error handling

**Minor SQL note**: The script uses `COALESCE(COG_category, '_missing')` (line 39) to handle unannotated clusters. This is fine, but NB03 then filters to single-letter COGs excluding `'-'`, which means `'_missing'` rows are dropped. The two representations are inconsistent but don't cause errors.

### Statistical Methods

The statistical methods are appropriate and well-executed:

- **Paired Wilcoxon signed-rank test** (NB03, cell-6): Correct choice for testing within-species adaptive > housekeeping with 24 paired observations. One-sided alternative is justified by the directional hypothesis.
- **BH-FDR correction** (NB03, cell-10): Applied to the 8 pairwise tests (F,H) × (L,V,M,K). All 8 tests remain significant at FDR < 0.05, with the smallest adjusted p = 4.8×10⁻⁷.
- **Effect size reporting**: The report gives median ratio (8.14×), range across phyla (4× to 15.4×), and per-COG medians. This is more informative than p-values alone.
- **Phylum stratification** (NB03, cell-8): The per-phylum summary table shows 5/5 phyla direction-consistent. With only 4–5 species per phylum, individual phylum-level tests would be underpowered, so reporting direction and effect size without claiming phylum-level significance is the right call.

**Core/accessory interaction** (NB04): The 2×2 design (class × core-status) is clean, and all four one-sided Wilcoxon tests are reported. The finding that adaptive-core (0.06%) is only 2× housekeeping-core (0.03%) while adaptive-accessory (1.55%) is 25× adaptive-core is the most interesting result in the project and is well-supported.

### Pitfall Awareness

The project documents and addresses several pitfalls:

- **Project-specific pitfall** (`memories/pitfalls.md`): The fragility of `jupyter nbconvert --execute` for long Spark jobs is documented with the observed failure mode (notebook file not updated, only intermediate CSV survived) and the fix (standalone script with per-species incremental output). This is a high-quality pitfall capture.
- **Namespace convention** (from `docs/pitfalls.md`): The project uses `kbase_ke_pangenome` (underscore form) consistently, which is correct for the current migration state. The code would need updating if the collection migrates to Iceberg.
- **Weighted metrics**: The plan revision (v2) explicitly documents the switch from binary "any multi-copy" to cluster-carrier-weighted rate after the pilot showed the binary metric was too coarse. This shows awareness of the rare-event nature of paralog expansion.

**One missed pitfall**: The extraction script and notebooks do not verify that the namespace form is still correct. A `SHOW TABLES IN kbase_ke_pangenome` sanity check at the top of NB01 would catch a post-migration namespace change. This is a minor issue since the artifacts exist and are dated 2026-07-07, implying recent successful execution.

### Notebook Organization

Notebooks are logically organized with clear headers, markdown cells explaining each step, and incremental artifact saving. The progression (NB01 pilot → NB01b refined metrics → NB02 scale-up manifest → NB03 statistical tests → NB04 interaction) is easy to follow. Code is readable with meaningful variable names (`HOUSEKEEPING`, `ADAPTIVE`, `species_class`, `wide`).

**One organizational note**: NB02's extraction logic moved to `src/extract_multi_species.py`, but NB02 itself is not re-purposed to document the script invocation or show concatenation outputs. The notebook is effectively a stub. Either (a) NB02 should import and call the extraction function with outputs shown, or (b) the README should note that NB02's extraction step is externalized and point to the script.

## Findings Assessment

### Are Conclusions Supported?

**H1a (housekeeping fixed)**: Species-level median housekeeping rate = 0.047%, with F = 0.062% and H = 0.041%. This is 2–3 orders of magnitude below the ~5% pseudogene/rare-variant rate expected under neutral drift (REPORT line 73). The claim that housekeeping clusters are "near-uniformly single-copy" is supported.

**H1b (adaptive variable)**: COG L (replication/recombination/repair) has species-level median 1.12%, which is 24× the housekeeping median. V, M, K are lower (0.11–0.12%) but still 2–3× housekeeping. The dominance of L is consistent with L containing transposases and IS elements (cited: Sotiropoulos 2026, Jespersen 2024). Supported.

**H1c (cross-phylum consistency)**: 24/24 species show adaptive > housekeeping; 5/5 phyla show this in 100% of their species. Effect size varies 4-fold (Campylobacterota 4.0× vs Pseudomonadota 15.4×), which is interpretable as accessory-genome diversity differences. Supported.

**H4 (core-accessory interaction)**: Adaptive-accessory (1.55%) is 25× adaptive-core (0.06%), and adaptive-core is only 2× housekeeping-core. The claim that "the class effect is not primarily about which genes tolerate paralogy at fixation, it is about which clusters get to expand into paralog territory in the first place" (REPORT line 77) is directly supported by the 2×2 breakdown in NB04.

**Literature alignment**: The REPORT cites Pushker 2004, Gevers 2004, Elliott 2013, and Sotiropoulos 2026 appropriately. The claim of novelty (first pangenome-scale test across phyla; first demonstration of class × status interaction) is plausible and not contradicted by the cited literature.

### Limitations Acknowledged?

The REPORT's Limitations section (lines 95–100) is thorough and honest:

- **90% AAI clustering ceiling**: Recent paralogs (<10% divergence) are merged; ancient paralogs (>10%) are split. This is inherent to the motupan clustering and acknowledged.
- **Assembly fragmentation**: Contig-level artifacts can inflate or deflate copy counts. The recommendation to condition on `checkm_completeness` for a robustness pass is good.
- **Species selection bias**: 24 species oversamples clinically important taxa; leaves out CPR, Patescibacteria, Spirochaetota, archaea. The Spirochaetota pilot (*Borreliella burgdorferi*) was flagged as an outlier due to multi-partite genome structure.
- **Coarse class partition**: Housekeeping = {F, H} is only ~5% of clusters; adaptive = {L, V, M, K} is ~15%. The effect is real for tested rows but extrapolation to "all bacterial genes" is not automatic.
- **No direct test for positive selection**: The observations are consistent with purifying selection on housekeeping OR neutral tolerance for adaptive OR mechanistic bias (proximity to mobile elements). Distinguishing these requires dN/dS and mobile-element context data.

These are all legitimate limitations and none are showstoppers. The only additional limitation I would flag is the lack of a within-genome copy-number distribution analysis (the current metric is per-cluster-per-genome counts aggregated across genomes). Future Direction #4 (lines 158–159) already notes this.

### Incomplete Analysis?

The analysis is complete as scoped. All pre-registered hypotheses (H1a/b/c, H4) are tested with appropriate statistics. The figures cited in the REPORT exist in `figures/`. The data files cited exist in `data/`. The Future Directions section (lines 154–160) identifies logical next steps (IS-element decomposition, high-quality-genome robustness, 100+ species scale-up, within-species CV, fitness data cross-reference) but does not leave any current analysis "to be filled."

**One gap**: The README's "Quick Links" section points to "TBD" for both Research Plan and Report, but both files exist and are complete. This is a documentation gap, not an analysis gap.

### Visualizations

The 5 figures are clear, properly labeled, and support the claims:

- `pilot_cog_copy_distribution.png`: Bar chart of % multi-copy by COG, color-coded by class. Shows L as the top category.
- `pilot_refined_cog_metrics.png`: Per-phylum housekeeping vs adaptive bars with pooled ratio. Shows 5/5 phyla direction-consistent.
- `cog_species_rates.png`: Boxplots of species-level rates per COG. Shows F and H (red) at the bottom, L (green) at the top.
- `class_vs_phylum.png`: Phylum-level bars with per-species points overlaid. Shows effect size variation across phyla.
- `core_accessory_interaction.png`: 2×2 boxplots (class × core-status). Clearly shows the interaction.

All figures have axis labels, titles, legends, and grid lines. Color choices are consistent (red = housekeeping, green = adaptive). No issues.

## Discoveries / Performance Notes Assessment

### Discoveries (REPORT lines 44–48)

**Discovery 1**: "The dosage-constraint × selection story is largely encoded in the core/accessory split, not the COG label."

- **Supported**: NB04 shows adaptive-core (0.06%) is only 2× housekeeping-core (0.03%), while adaptive-accessory (1.55%) is 5× housekeeping-accessory (0.29%). The 8× species-level effect collapses to 2× within core.
- **Scope claim**: "Any future BERIL project analyzing copy number should stratify by `is_core` before drawing conclusions about functional constraint."
- **Assessment**: Appropriate scope. This is a methodological lesson for future pangenome copy-number work.
- **Suggested refinement**: Could add "in bacterial pangenomes" to clarify that the claim is not being extended to eukaryotic paralogy.

**Discovery 2**: "Category J (translation) behaves as 'mixed', not housekeeping, at species scale."

- **Supported**: NB01 pilot showed J at 2.07% multi-copy, 5th out of 21 categories, driven by ribosomal protein paralogs, tRNA duplications, rRNA operon multiplicity. The decision to reclassify J from housekeeping to mixed is documented in the plan revision.
- **Scope claim**: Implicit — applies to BERDL pangenome projects using COG functional categories.
- **Assessment**: Accurate. This is a BERDL-specific calibration rather than a universal biological claim, which is appropriate.
- **Suggested refinement**: Could note that the "classic textbook 'informational vs operational' divide" is an oversimplification for bacterial pangenome work — J's behavior is intermediate, not strictly dosage-constrained.

**Discovery 3**: "Weighted metrics matter for rare-event functional analysis."

- **Supported**: Binary "any multi-copy in ≥1 genome" gave 1.4× effect (NB01); weighted multi-copy rate gave 3.3× (NB01b) and 8.1× at scale (NB03).
- **Scope claim**: Implicit — applies to pangenome functional analyses where the signal is concentrated in rare clusters.
- **Assessment**: Accurate. The binary flag is dominated by singletons with one accidental multi-copy event.
- **Suggested refinement**: Could generalize to "rare-event enrichment analyses" beyond just copy number — the same issue affects any binary presence/absence flag where the signal is in the degree, not the presence.

All three discoveries are supported by the analysis, scoped appropriately, and are genuinely load-bearing for future work. No speculative or redundant entries.

### Performance Notes (REPORT lines 50–52)

**Note 1**: "Per-species iteration on the 3-way join took 140–290 s per species on 50–250-genome species (median ~200 s). For 24 species this is ~80 min total; scaling to 100+ species should use CTS batch processing."

- **Supported**: The `src/extract_multi_species.py` output shows timestamps consistent with ~200 s/species. The recommendation to use CTS for 100+ species is reasonable.
- **Assessment**: Accurate. This is useful calibration for Future Direction #3 (scale to 100+ species).

**Note 2**: "`jupyter nbconvert --execute` is fragile for long-running Spark jobs."

- **Supported**: Documented in `memories/pitfalls.md` with the observed failure mode and fix.
- **Assessment**: Accurate and already captured as a project-specific pitfall. This note is redundant with the pitfall memo but does no harm.

## Suggestions

### Critical (Must Address Before Approval)

1. **Populate notebook outputs**. Either re-run all notebooks with outputs saved, or document in README that outputs are intentionally omitted and that figures/data files are the canonical artifacts. Notebook 02 in particular should show at least the concatenation step and sanity checks, even if the extraction ran externally.

2. **Complete the README Reproduction section**. Include:
   - Prerequisites (Python packages, Spark session, BERDL access)
   - Step-by-step instructions for each notebook
   - Which notebooks need Spark vs run locally
   - How to invoke `src/extract_multi_species.py` (arguments, expected runtime)
   - Whether `data/per_species/*.csv` files should be regenerated or are committed

3. **Add a `requirements.txt`** with pinned versions of scipy, statsmodels, matplotlib, pandas, numpy. For a project relying on statistical tests, version reproducibility matters.

4. **Fix README Quick Links**. Change "TBD" to actual file links: `[Research Plan](RESEARCH_PLAN.md)` and `[Report](REPORT.md)`.

### High Priority (Strongly Recommended)

5. **Add a namespace sanity check** to NB01 or the extraction script. A simple `spark.sql("SHOW TABLES IN kbase_ke_pangenome LIKE 'gene'").count() > 0` at the top would verify that the underscore form is still valid post-migration.

6. **Cross-reference the discoveries** in REPORT.md back to specific notebook cells or figures. For example, Discovery 1 could cite "NB04 cell-6, Figure 5" to make the tie explicit.

7. **Clarify NB02's role** in the README. Either document that NB02's extraction is externalized to `src/extract_multi_species.py`, or re-purpose NB02 to import the script's output and show sanity checks.

### Nice to Have (Optional Improvements)

8. **Add a data dictionary** to the README or REPORT describing the columns in `data/multi_species_copy_stats.csv` and other key outputs. "What is `total_carrier_genomes` vs `n_clusters`?" is not immediately obvious to a new reader.

9. **Consider archiving the pilot** (NB01) as a separate artifact or appendix. The main pipeline is NB01b → NB02 → NB03 → NB04; NB01's binary metric is superseded. Keeping it is fine for transparency, but a note in the README that "NB01 is pilot; NB01b is the refined pilot used for scale-up decisions" would help readers navigate.

10. **Add a "How to Cite" section** to the README with a suggested citation format, including ORCID for Justin Reese.

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-5)
- **Date**: 2026-07-07
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, references.md, 5 notebooks (01, 01b, 02, 03, 04), 1 script (src/extract_multi_species.py), memories/pitfalls.md, docs/pitfalls.md, 5 figures, 10 data files
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.

<!-- report_hash: sha256:db9c89bfc570082e1360a1e48b741c7237246f236a90b7a256e990944b980199 -->
