---
reviewer: claude
model: claude-opus-4-6
reviewed_at: "2026-05-21T22:30:00Z"
review_type: project
---

# Review: CAZyme Pangenome Ecology

## Summary

This project asks whether CAZyme class composition differs across bacterial biomes (H1) and whether CAZyme density correlates with pangenome openness (H2), using 49K genomes from the MGnify catalog across 18 biomes. The analysis is well-executed at an impressive scale, with strong statistical controls (genome-size correction, within-phylum stratification, Isolate-vs-MAG bias checks). H1 is convincingly supported with massive effect sizes. H2 is appropriately characterized as weak, with transparent discussion of the genome_count confound. The GT/GH ratio as a novel ecological metric is an interesting emergent finding. The report is well-structured with proper literature context and honest limitations.

**Overall assessment**: Strong project ready for submission with minor issues.

## Suggestions

### Critical

*None.*

### Important

1. **Notebook reproducibility gap**: Only `01_data_extraction.ipynb` exists as a notebook file, but the RESEARCH_PLAN.md specifies 5 notebooks (NB01–NB05). The analysis for NB02–NB05 was performed inline during the conversation and results are preserved in data files and figures, but the notebooks themselves are not on disk. This means the analysis is not fully reproducible from notebooks alone. The REPORT.md references "inline analysis NB02", "inline analysis NB03", "inline analysis NB04" — these are not real notebook files. **Recommendation**: Either (a) create the missing notebooks with the analysis code that produced the data/figures, or (b) update the REPORT.md notebook provenance lines to accurately reflect that NB01 is the only notebook and the remaining analyses were performed interactively. Option (a) is preferred for reproducibility.

2. **Notebook has no saved outputs**: `01_data_extraction.ipynb` has zero cells with outputs (all `execution_count: None`). The notebook was written but appears not to have been executed with saved outputs. For reproducibility, notebooks should be committed with outputs so a reader can inspect intermediate results without re-running on the cluster.

3. **Missing `requirements.txt`**: No `requirements.txt` file exists. For reproducibility, the Python dependencies (pandas, numpy, matplotlib/seaborn, scipy) should be documented.

4. **Zebrafish-fecal biome missing from Results table**: The biome summary data has 18 biomes but the Results table in REPORT.md shows only 16 rows — `zebrafish-fecal` (n=67) and `maize-rhizosphere` (n=265) are missing. Update the table to include all 18 biomes for completeness.

### Nice-to-Have

5. **Effect size for H1**: The Kruskal-Wallis H statistics are reported but no standardized effect size measure (e.g., epsilon-squared or eta-squared) is given. With n=49K, even trivial differences would be significant. The 3–4× fold-change in GH counts is a strong practical effect, but a formal effect size metric would strengthen the claim. The report partially addresses this by noting fold-changes, which is reasonable.

6. **Pairwise post-hoc tests**: The RESEARCH_PLAN.md specified "Kruskal-Wallis + post-hoc Dunn's test" but only KW results appear in the report. Post-hoc tests would identify which specific biome pairs drive the overall effect. Not critical — the biome-level means in the table make the pattern clear — but would complete the planned analysis.

7. **PERMANOVA**: The RESEARCH_PLAN.md specifies "PERMANOVA on multivariate CAZy profiles" as part of NB02's goals. This was not reported. PERMANOVA would test whether the multivariate CAZy profile (all classes simultaneously) differs by biome, complementing the per-class KW tests.

8. **Pudlo et al. citation missing DOI**: The Pudlo et al. (2022) reference lacks a DOI link, unlike most other references.

9. **Discoveries section could be more concise**: The 4th bullet (genome_count confound) is more of a methodological limitation than a discovery. Consider moving it to limitations or rephrasing as a positive finding about the lineage-specific nature of the H2 signal.

## Checklist

| Item | Status |
|------|--------|
| Research question clearly stated | PASS |
| Hypotheses testable and tested | PASS |
| Data extraction documented | PASS |
| Statistical methods appropriate | PASS |
| Multiple testing correction applied | PASS |
| Confounders addressed | PASS (genome size, phylogeny, MAG bias) |
| Figures support findings | PASS (5 figures, all referenced inline) |
| Literature context provided | PASS (7 relevant papers) |
| Limitations honestly stated | PASS (6 limitations) |
| Data files present | PASS (6 TSV files, 69K total rows) |
| Notebooks present | PARTIAL (1 of 5 planned; see Important #1) |
| Notebook outputs saved | FAIL (see Important #2) |
| Future directions actionable | PASS |

## Verdict

The scientific content is solid — H1 is strongly supported with appropriate controls, H2 is honestly characterized as weak, and the GT/GH ratio is a genuinely interesting emergent finding. The main gap is reproducibility infrastructure: the missing notebooks (NB02–NB05), absent notebook outputs, and missing requirements.txt. These don't affect the scientific conclusions but limit a reader's ability to audit the analysis independently. Address the Important items (particularly #1 and #2) before final submission.

<!-- report_hash: sha256:097450fff38e2f0e3d93093a580c5c3407e2876e8df8d56ad6024f00d72694a1 -->
