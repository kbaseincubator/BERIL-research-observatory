---
reviewer: BERIL Automated Review
date: 2026-02-15
project: essential_genome
---

# Review: The Pan-Bacterial Essential Genome

## Summary

This is an ambitious and well-executed project that clusters essential genes across 48 Fitness Browser organisms into ortholog families and classifies them along a spectrum from universally essential to never essential, culminating in function predictions for uncharacterized essential genes via module transfer. The README is exceptionally thorough — with a clear research question, detailed methodology, well-contextualized findings, honest limitations, and strong literature integration. The analysis pipeline is cleanly structured (Spark extraction → local analysis across 3 notebooks) and produces meaningful biological insights, including the identification of 15 pan-bacterial essential families and 1,382 function predictions for hypothetical essentials. The main areas for improvement concern (1) over-merging of ortholog groups via connected components, which inflates some family classifications, (2) the use of `.py` scripts instead of `.ipynb` notebooks, which means there are no saved outputs to inspect without re-execution, and (3) a performance issue in NB02 where row-wise `.apply()` is used on a 221K-row DataFrame.

## Methodology

**Research question**: Clearly stated, multi-part, and testable. The three-way classification (universal / variable / never essential) is well-motivated, and the function prediction via module transfer is a creative integration of prior project results.

**Approach**: The five-step pipeline is logical and well-sequenced. Building on `conservation_vs_fitness` (pangenome links) and `fitness_modules` (ICA modules and module families) is a strength — this project synthesizes two prior analyses into a novel question.

**Data sources**: Clearly documented in a table in the README. Cross-project dependencies (link table, module membership, module families) are explicitly listed.

**Ortholog grouping method**: Connected components of the BBH graph is a standard approach, but it is susceptible to over-merging multi-domain proteins and large paralog families. This is acknowledged in the Limitations section, which is good. However, the impact is quantifiable and significant:

- 53 ortholog groups contain >200 genes; the largest (OG00019, LysR family regulators) has 2,320 genes across 48 organisms.
- OG00143 (beta-ketoacyl-ACP reductase, 1,280 genes across 46 organisms) is classified as "universally essential" — but with 1,280 genes in 46 organisms (~28 copies per organism), this is a large multi-copy family where at least one paralog per organism happens to be essential. The "universal essentiality" of the family is likely an artifact of over-merging distinct paralogs.
- 20 of 859 "universally essential" families have non-essential members in some organisms (i.e., an organism has both essential and non-essential members in the same OG), confirming that the connected-component approach merges paralogs.

This does not invalidate the core findings — the 15 families essential in all 48 organisms and the orphan essential analysis are robust — but the exact count of 859 universally essential families is likely an overestimate.

**Essential gene definition**: Well-documented. The README clearly states this is an upper bound (genes absent from `genefitness`), which matches the documented pitfall "FB Gene Table Has No Essentiality Flag" from `docs/pitfalls.md`. No gene-length filter is applied to remove short genes that may lack insertions by chance rather than essentiality; this is acknowledged in the Limitations but could materially affect the 18.6% essentiality rate.

**Reproducibility**: The reproduction section is clear, with step-by-step instructions distinguishing Spark-required steps from local steps. Dependencies on other projects are noted but there is no `requirements.txt` file listing Python package versions.

## Code Quality

**Overall structure**: Clean separation between Spark extraction (`src/extract_data.py`) and local analysis (three numbered scripts). The extraction script uses file-based caching (skip if output exists), which is good practice.

**Scripts instead of notebooks**: All three analysis "notebooks" are plain `.py` files, not `.ipynb` Jupyter notebooks. The README refers to them as "NB02", "NB03", "NB04" and the reproduction section uses `jupyter nbconvert --execute`, but the files are `02_essential_families.py`, `03_function_prediction.py`, `04_conservation_architecture.py`. This means:

- There are **no saved outputs** (no printed summaries, no intermediate tables, no inline figures). A reader must re-run the scripts to see any results.
- The figures directory has 3 PNG files, which provides some visual output, but the numerical results (counts, percentages, statistical tests) are only available by running the code.
- The README compensates by reporting key numbers in the "Key Findings" section, but the scripts themselves serve as "trust me" artifacts.

**SQL queries**: Correct use of `CAST(begin AS INT)` and `CAST(end AS INT)` in `extract_data.py`, consistent with the documented pitfall that all FB columns are strings. The `type = '1'` filter correctly uses string comparison. Queries properly filter by `orgId`.

**Performance concern in NB02** (line 66-67):
```python
essential['in_og'] = essential.apply(
    lambda r: (r['orgId'], str(r['locusId'])) in genes_in_ogs, axis=1
)
```
This is a row-wise `.apply()` on a 221,005-row DataFrame with a set membership test — exactly the pattern documented in `docs/pitfalls.md` as "Row-Wise Apply on Large DataFrames Is Orders of Magnitude Slower Than Merge." A merge-based approach would be substantially faster. The same pattern appears in NB03 (line 111-112) for the `ess_genes['og_id']` lookup.

**NB03 loop-based prediction**: The main prediction loop (lines 127-184) iterates row-by-row over targets and their ortholog group members. This is inherently serial and could be slow for large target sets, but given that only ~3,900 targets are involved, it's acceptable.

**Boolean handling**: Careful handling of the `is_essential` column throughout, with explicit `astype(str).str.strip().str.lower() == 'true'` conversion in each script. This is defensive but correct — TSV round-tripping can change boolean representations.

**Figures**: All three visualizations are well-constructed 4-panel figures with clear labels, appropriate color coding, sample sizes on bars, and statistical annotations where relevant. The heatmap (Figure 2) effectively communicates the ubiquity of essentiality for the top 40 families. The "Not present" (gray) cells in the heatmap correctly distinguish absence from non-essentiality.

**Pitfall awareness**: The project correctly handles the "essential genes are invisible in genefitness" pitfall, which is the foundation of the analysis. The string-typed column pitfall is handled with CAST. The "ortholog scope must match analysis scope" pitfall from fitness_modules is implicitly handled by extracting BBH pairs for all 48 organisms.

## Findings Assessment

**Conclusions supported by data**:
- The 15 pan-bacterial essential families (essential in all 48 organisms) are well-supported and the list (ribosomal proteins, groEL, fusA, pyrG, valS) is biologically plausible and consistent with literature.
- The conservation hierarchy (universally essential > variably essential > never essential > orphan essential for % core) is clearly demonstrated in Figure 3, Panel A.
- The high hypothetical fraction for orphan essentials (58.7%) vs universally essential families (8.2%) is a striking and well-documented finding.
- The 1,382 function predictions via module transfer are a novel contribution, though the confidence scoring (combining -log10(FDR) with log10(n_organisms)) is ad hoc and not validated.

**Potential concerns**:
- The claim of "859 universally essential families" is likely inflated by over-merged connected components. A family like OG00143 (1,280 genes, beta-ketoacyl-ACP reductase) is classified as universally essential, but with ~28 copies per organism, this reflects the near-certainty that at least one copy is essential in any organism — a different biological claim than a single-copy gene being essential everywhere. The 839 single-or-few-copy universally essential families are the more meaningful subset, but this distinction is not made.
- The rho=-0.123 correlation between essentiality penetrance and core fraction (Panel C, NB04) is described as "significant" but is extremely weak (R² ≈ 1.5%). The README describes this relationship honestly as "weak," which is appropriate.
- The README states the negative correlation means "families essential in more organisms tend to be core" — but the sign is negative, meaning higher essentiality penetrance correlates with *lower* core fraction. This warrants clarification; either the sign or the interpretation may be inverted.

**Limitations acknowledged**: Yes, thoroughly. Six specific limitations are listed, covering false positives in essentiality calling, BBH conservatism, connected-component over-merging, condition-dependent essentiality, taxonomic bias, and indirect function predictions. This is commendably honest.

**Literature integration**: Excellent. Six papers are cited in context with specific comparisons to the project's findings (e.g., comparing 859 families to Koonin's ~60 universally conserved proteins, noting the difference is due to stringency criteria). The references.md file has 9 proper citations with DOIs and PMIDs.

## Suggestions

1. **[Critical] Address over-merging in ortholog groups**: Either (a) add a maximum OG size filter (e.g., exclude OGs with >2× the number of organisms as a proxy for paralogy), (b) use single-linkage clustering with a similarity threshold rather than plain connected components, or (c) report universally essential family counts separately for single-copy (n_genes ≈ n_organisms) vs multi-copy (n_genes >> n_organisms) families. At minimum, add a sentence to the README noting how many of the 859 are single-copy families.

2. **[Important] Convert `.py` scripts to `.ipynb` notebooks (or save outputs)**: The current scripts produce no persisted outputs beyond data files and figures. Converting to Jupyter notebooks with saved cell outputs would let reviewers inspect intermediate results (family counts, top-N tables, statistical test results) without re-running the analysis. Alternatively, redirect stdout to log files during execution.

3. **[Important] Add a `requirements.txt`**: The README lists dependencies in prose but there is no machine-readable dependency file. Add `requirements.txt` with at minimum: `pandas`, `numpy`, `matplotlib`, `scipy`, `networkx`, `scikit-learn`.

4. **[Moderate] Replace row-wise `.apply()` with merge** in NB02 line 66 and NB03 line 111. This is a documented pitfall (`docs/pitfalls.md`: "Row-Wise Apply on Large DataFrames Is Orders of Magnitude Slower Than Merge") and would improve performance on the 221K-row essential genes DataFrame.

5. **[Moderate] Clarify the penetrance-conservation correlation sign**: The README states "families essential in more organisms tend to be core" but the correlation is rho=-0.123 (negative). If higher `frac_essential` correlates with lower `pct_core`, the interpretation needs revision. Or if the negative sign reflects the specific variables used, clarify the directionality explicitly.

6. **[Minor] Add gene length filter for essentiality**: Short genes (<300 bp) are more likely to lack transposon insertions by chance. Reporting how many putative essential genes are below this threshold, and optionally filtering them, would strengthen the essentiality calls.

7. **[Minor] Document cross-project data dependencies explicitly**: The project requires files from `conservation_vs_fitness/data/` (link table, organism mapping, pangenome metadata, SEED hierarchy, SEED annotations) and `fitness_modules/data/` (module membership, module annotations, module families). A checklist of required files would help reproduction.

8. **[Minor] Consider adding NB01 as a separate script**: The README references "NB01" findings (221,005 genes, 41,059 essential) but there is no NB01 script — these numbers come from `src/extract_data.py`. Either rename the README references to match the actual file, or create a `01_essential_landscape.py` that produces the organism-level summary statistics.

## Review Metadata
- **Reviewer**: BERIL Automated Review
- **Date**: 2026-02-15
- **Scope**: README.md, references.md, 1 extraction script (`src/extract_data.py`), 3 analysis scripts (`.py` format), 6 data files, 3 figures
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
