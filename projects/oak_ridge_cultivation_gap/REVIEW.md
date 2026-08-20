---
reviewer: BERIL Automated Review (Claude, claude-sonnet-4-5@20250929)
date: 2026-05-08
project: oak_ridge_cultivation_gap
---

# Review: What Metabolic Functions Does the Cultured Collection Miss at Oak Ridge?

## Summary

This project delivers a rigorous quantitative comparison of metabolic functions between 3,110 cultured ENIGMA isolates and 2,279 subsurface MAGs, producing the first per-function "cultivation-coverage" table for a well-characterized subsurface system. The work demonstrates massive functional asymmetry (78% of KOs significantly biased), identifies Wood-Ljungdahl carbon fixation as the clearest cultivation gap, and validates the porewater-bias signature across subsurface lithologies. The REPORT is well-written, the statistical methods are sound, and the findings are properly contextualized with recent literature.

However, the project has a **critical reproducibility gap**: all eight notebooks contain zero saved outputs. A reader cannot verify the reported statistics, inspect intermediate results, or assess figure quality without re-running the entire pipeline — which requires Spark access and 6+ hours of runtime. This contradicts best practices for computational reproducibility and significantly limits the project's value as a reference for future BERDL work.

## Methodology

### Strengths

- **Clear research question**: The hypothesis framework (H1 depletion, H2 enrichment, H0 null) is testable and grounded in specific literature predictions.
- **Sound statistical approach**: Fisher's exact test with Benjamini-Hochberg FDR correction is appropriate for this binary presence/absence comparison. Effect sizes reported as log2 odds ratios with prevalence fractions.
- **Literature-grounded marker dictionary**: Ten categories (36 KOs) spanning Wood-Ljungdahl, sulfate reduction, denitrification, motility, aerobic respiration, etc., with specific literature citations for each prediction.
- **Transparent cohort pivot**: The shift from CORAL ORFRC-specific MAGs to pan-subsurface MAGs is clearly documented in RESEARCH_PLAN v2, with rationale (inaccessible assembly FASTAs) and implications (broader generalizability, loss of site-specificity) explained.
- **Avoids known pitfalls**: Uses GCF/GCA accessions for pangenome linkage (NB06), avoiding the strain-name collision pitfall documented in `docs/pitfalls.md`.

### Weaknesses

- **MAG cohort is pan-subsurface, not ORFRC-specific**: The pivoted analysis compares ENIGMA isolates (predominantly ORFRC) against 2,279 global subsurface MAGs from `kbase_ke_pangenome`. This answers a *different* question than the title implies ("at Oak Ridge" → "in subsurface environments generally"). The limitation is acknowledged in REPORT, but the README and title retain the Oak Ridge framing, which may mislead casual readers.
- **Genome size confounding**: The 4-fold genome size difference (5.8 Mbp cultured vs 1.5 Mbp MAGs) is the dominant driver of the bias distribution. The REPORT discusses this clearly, but the analysis does not include a genome-size-normalized comparison (e.g., restricting to size-matched phyla) to isolate cultivation selection from genome streamlining effects. This is flagged as a future direction but would strengthen the current findings.
- **Annotation method differences**: Cultured genomes use ENIGMA Genome Depot annotations (pipeline unknown), MAGs use bakta via `kbase_ke_pangenome`. Systematic sensitivity differences could introduce bias. NB06 aims to cross-validate via eggNOG but this notebook has no outputs, so concordance is not verifiable.

## Code Quality

### Strengths

- **SQL queries are correct**: NB03 properly joins `browser_gene` → `browser_protein` → `browser_protein_kegg_orthologs` → `browser_kegg_ortholog`, avoiding the common pitfall of missing `browser_gene.protein_id` linkage.
- **Reusable module**: `src/cultivation_bias.py` packages the statistical framework as a callable function with clear docstring, enabling future projects to apply the same diagnostic.
- **Appropriate statistical methods**: Fisher's exact test for 2×2 contingency tables, BH-FDR correction for multiple testing, log2 ratios with pseudocounts to handle zeros.
- **Clear notebook organization**: Each notebook has a defined scope (NB03: cultured profiles, NB04: statistical comparison, NB05: taxonomy, NB06: cross-validation, NB07: module packaging, NB08: synthesis).

### Weaknesses

- **Fragile taxonomy parsing (NB05)**: The `extract_phylum()` function attempts to handle both ENIGMA taxon names (simple strings like "Pseudomonas fluorescens") and GTDB taxonomy strings (format: `d__Bacteria;p__Proteobacteria;...`), but the fallback logic (`return s.split(';')[0] if ';' in s else s`) produces inconsistent results. For ENIGMA strain names without semicolons, this returns the entire string as "phylum," which is incorrect. This likely explains the "MAG-only phyla" result not being computable (NB05 cell 11 prints "taxonomy parsing may need adjustment").
- **Incomplete error handling**: NB06 and NB08 check for file existence (`if mag_ko_path.exists()`) before proceeding, but do not fail gracefully when upstream data is missing — they simply print "Waiting for NB04 results" and continue. A reader re-running the pipeline would not realize these steps were skipped until inspecting outputs.
- **Hardcoded batch size (NB06 cell 5)**: `cluster_ids[:50]` limits the cross-validation query to 50 clusters, but the comment says "batch" without explaining why batching is needed or how to process remaining clusters. This suggests the cross-validation is incomplete.

## Reproducibility

### Critical Gap: No Saved Notebook Outputs

All eight notebooks (`01_mag_extraction.ipynb` through `08_synthesis.ipynb`) have **zero cells with saved outputs**. Checking the `outputs` arrays in each notebook reveals completely empty output blocks for every cell. This means:

- **Figures are not embedded**: The README references `figures/synthesis_panel.png` and the REPORT describes it as "Distribution of per-KO cultivation bias, marker category comparison, and prevalence scatter," but a reader inspecting NB08 cannot see this figure or verify it matches the description.
- **Statistical results are not visible**: NB04 reports "8,482 (78.2%) show statistically significant prevalence differences" in the REPORT, but the notebook itself shows no printed output confirming this number. A reviewer cannot verify the calculation without re-running Spark queries.
- **Intermediate validation is missing**: NB06 is titled "Cross-validation" and should show eggNOG concordance metrics, but without saved outputs, there is no evidence this validation was actually performed.
- **Taxonomy analysis is unverifiable**: NB05 should show phylum composition tables and CPR representation, but the notebook is a code-only skeleton.

**Impact**: This is the single most serious gap in the project. Computational reproducibility requires that notebooks be "run once, read many times." The current state forces every reader to re-execute the entire pipeline (NB03 requires Spark, NB02 was planned for CTS, total runtime ~2-7 hours per README) just to verify basic claims. This is especially problematic for the cross-validation notebook (NB06), which is the primary defense against annotation-method bias but provides no evidence of its results.

**Recommended fix**: Re-run all notebooks and commit them with saved outputs. For notebooks requiring Spark (NB03, NB06), save outputs *before* exiting the JupyterHub session. Use `jupyter nbconvert --execute --to notebook --inplace` to ensure outputs are captured.

### Missing Reproduction Guide

The README includes a "Reproduction" section, but it lacks critical details:

- **No step-by-step commands**: The README says "Run NB03 on JupyterHub (Spark)" but does not provide the Spark session setup command, cluster configuration, or expected runtime per-cell. A first-time BERDL user would not know how to obtain a Spark session or which kernel to select.
- **No local environment setup**: Step 3 says "Run NB04-NB08 locally" but does not specify how to install dependencies beyond `pip install -r requirements.txt`. The `requirements.txt` omits `berdl_notebook_utils`, which NB03 and NB06 import.
- **No data handoff instructions**: The README notes that NB03 exports `data/cultured_ko_profiles.tsv`, but does not explain how to transfer this file from JupyterHub to the local machine for NB04-08 consumption. Does the user need to download via Jupyter file browser? Use `scp`? MinIO?
- **MAG KO profiles unexplained**: The README states "MAG KO profiles are pre-extracted from `kbase_ke_pangenome.bakta_db_xrefs` (cached in `data/mag_ko_profiles.tsv`)" but does not provide the extraction query or script. The file exists in `data/`, but its provenance is unclear — was it generated by a missing notebook? A separate Spark script? This should be documented or included as a numbered notebook.

### Figures vs Expectations

The `figures/` directory contains three PNG files:
- `marker_category_bias.png` (130 KB)
- `synthesis_panel.png` (514 KB)
- `volcano_cultivation_bias.png` (606 KB)

The README "Key Output Files" section lists these three, which is good. However:
- NB05 generates `figures/phylum_comparison.png` and `figures/genome_size_distribution.png` (cells 7 and 9), but these files do not exist in `figures/`. This suggests NB05 was not successfully run to completion.
- NB04 generates `figures/marker_heatmap.png` (cell 13), also missing.

**Impact**: Moderate. The three core figures for the REPORT are present, but intermediate diagnostic plots are missing, making it harder to assess taxonomic bias and genome size distributions.

### Dependencies

The `requirements.txt` lists 8 packages (pandas, numpy, scipy, matplotlib, seaborn, statsmodels, scikit-learn, pyspark) but omits:
- `berdl_notebook_utils` — imported in NB03 and NB06
- Version pins for `berdl_notebook_utils` (is this a BERDL-internal package? where is it installed?)

A reader attempting to reproduce locally would encounter `ModuleNotFoundError: No module named 'berdl_notebook_utils'` immediately.

**Recommended fix**: Add `berdl_notebook_utils` to `requirements.txt` or document it as a JupyterHub-only dependency. Include a comment explaining that Spark-based notebooks (NB03, NB06) must run on JupyterHub, not locally.

## Findings Assessment

### Conclusions Are Well-Supported

The REPORT's key findings are backed by quantitative evidence from the generated data files:

1. **Massive functional asymmetry (78%)**: Verified by inspecting `data/ko_cultivation_coverage_full.tsv` (10,845 rows, `significant` column shows 8,482 TRUE values = 78.2%).
2. **Wood-Ljungdahl depletion**: `data/marker_cultivation_coverage.tsv` shows K00194, K00197, K00198 with log2_ratio of -3.76, -3.53, -3.85 respectively (mean -1.58 for the category), consistent with the REPORT's claim.
3. **Aerobic respiration enrichment**: marker_cultivation_coverage shows K02274, K02275, K02276 with log2_ratio of +7.78, +6.87, +7.22 (mean +7.29), matching the REPORT.
4. **Patescibacteria dominance in MAGs**: Verified by reading `data/pangenome_subsurface_mag_metadata.tsv` — filtering for `gtdb_taxonomy LIKE '%Patescibacteria%'` yields 911 of 2,425 rows (37.6%), close to the "approximately 40%" claim.

The statistical methods (Fisher's exact, BH-FDR) are correctly applied per the code in NB04. The literature integration in the REPORT is strong, citing 13 recent papers (2012-2026) with DOIs and PMIDs.

### Limitations Are Clearly Acknowledged

The REPORT includes a comprehensive "Limitations" section addressing:
- MAG cohort is pan-subsurface, not ORFRC-specific
- MAG incompleteness inflates apparent gaps
- Genome size confounding
- KO annotation method differences
- Temporal and geographic mismatch

Each limitation is explained with its directional impact on findings (e.g., "MAG incompleteness makes the 813 'MAG-enriched' KOs a conservative estimate"). This demonstrates scientific rigor.

### Unexpected Results Are Interpreted

Two findings contradicted literature predictions:
1. **NiFe-hydrogenase enriched** (predicted depleted) — REPORT discusses this as either capturing hydrogenotrophic organisms better than expected, or KO assignment conflating different hydrogenase groups.
2. **Conjugation/MGE enriched** (predicted depleted) — REPORT explains the distinction between genomically-integrated machinery (retained) vs episomal MGEs (lost during cultivation).

Both interpretations are reasonable and suggest directions for follow-up (e.g., checking hydrogenase subgroup annotations, analyzing plasmid vs chromosomal gene distributions).

### Incomplete Analysis: Cross-Validation

NB06 ("Cross-validation with Pangenome & Literature") is intended to validate cultivation-bias signals using eggNOG annotations for 147 ENIGMA genomes. However:
- The notebook has no saved outputs, so Jaccard concordance is not reported.
- Cell 5 limits the query to 50 clusters (`cluster_ids[:50]`) with a comment "batch," suggesting the full 147-genome validation was not completed.
- The REPORT does not cite any cross-validation statistics — it jumps from the main results (NB04) directly to literature comparison without quantifying annotation agreement.

**Impact**: Moderate. The main findings are robust enough to stand without cross-validation (large effect sizes, clear literature alignment), but the lack of annotation concordance metrics leaves a methodological gap. If Genome Depot and eggNOG annotations systematically disagree on certain KO families, this could bias the cultivation-coverage table in unknown directions.

**Recommended fix**: Complete NB06 by removing the `[:50]` slice, running the full query, computing Jaccard concordance, and adding a paragraph to the REPORT: "Cross-validation using eggNOG annotations for 147 pangenome-linked genomes yielded X% Jaccard concordance, confirming that our Genome Depot KO profiles are reliable."

## Suggestions

### 1. **CRITICAL: Re-run all notebooks and save outputs** (Priority: HIGH)

All eight notebooks must be re-executed with outputs saved before this project can be considered reproducible. Without saved outputs, the notebooks are code templates, not computational records.

**Action**: For each notebook:
- NB03, NB06: Run on JupyterHub with Spark, save outputs before closing session
- NB04, NB05, NB07, NB08: Run locally, save outputs
- Commit the updated `.ipynb` files with `git add notebooks/*.ipynb && git commit -m "Add notebook outputs for reproducibility"`

**Verification**: After committing, run:
```bash
python3 -c "
import json, sys
for nb in ['01', '02', '03', '04', '05', '06', '07', '08']:
    cells = json.load(open(f'notebooks/{nb}_*.ipynb'))['cells']
    with_out = sum(1 for c in cells if c.get('outputs'))
    if with_out == 0:
        print(f'NB{nb}: FAIL (0 outputs)')
        sys.exit(1)
print('All notebooks have outputs: PASS')
"
```

### 2. **Add a detailed reproduction guide to README** (Priority: HIGH)

Expand the "Reproduction" section to include:

- **Spark setup**: Exact command to launch JupyterHub, kernel selection (`berdl-spark` or equivalent), and expected Spark UI URL for monitoring progress.
- **Local setup**: `pip install -r requirements.txt`, plus instructions to install `berdl_notebook_utils` (or note that NB03/NB06 require JupyterHub and cannot run locally).
- **Data handoff**: How to transfer `data/cultured_ko_profiles.tsv` from JupyterHub to local machine.
- **MAG KO profile provenance**: Document the Spark query used to generate `data/mag_ko_profiles.tsv`, or create a numbered notebook (e.g., NB02b) that extracts this file from `kbase_ke_pangenome.bakta_db_xrefs`.
- **Expected outputs**: For each notebook, list the expected output files (e.g., "NB03 produces `data/cultured_ko_profiles.tsv` and `data/cultured_genome_metadata.tsv`; NB04 produces `data/ko_cultivation_coverage_full.tsv` and `figures/volcano_cultivation_bias.png`").

**Example format**:
```markdown
## Reproduction

### Environment Setup

**JupyterHub (for NB03, NB06):**
1. Navigate to https://berdl.jupyterhub.example.com
2. Launch a `berdl-spark` kernel
3. Open `notebooks/03_cultured_ko_profiles.ipynb`
4. Run all cells (runtime ~15-30 min)
5. Download `data/cultured_ko_profiles.tsv` via Jupyter file browser

**Local (for NB04, NB05, NB07, NB08):**
1. Install dependencies: `pip install -r requirements.txt`
2. Place `data/cultured_ko_profiles.tsv` from NB03 into `data/` directory
3. Run notebooks in order: `jupyter nbconvert --execute notebooks/04_*.ipynb`

### Expected Outputs
- NB03: `cultured_ko_profiles.tsv`, `cultured_genome_metadata.tsv`
- NB04: `ko_cultivation_coverage_full.tsv`, `volcano_cultivation_bias.png`
- NB05: `phylum_comparison.png`
- ...
```

### 3. **Complete cross-validation (NB06)** (Priority: MEDIUM)

Remove the `[:50]` batch limit in NB06 cell 5, run the full 147-genome eggNOG concordance check, and report Jaccard similarity in the REPORT. If concordance is low (<0.7), investigate which KO families disagree and assess whether this affects marker dictionary results.

### 4. **Fix taxonomy parsing in NB05** (Priority: MEDIUM)

Rewrite the `extract_phylum()` function to handle ENIGMA and GTDB formats robustly:

```python
def extract_phylum(tax_str):
    if pd.isna(tax_str):
        return 'Unknown'
    s = str(tax_str)
    # GTDB format: d__Bacteria;p__Proteobacteria;...
    if ';p__' in s:
        for part in s.split(';'):
            if part.startswith('p__'):
                return part.replace('p__', '')
    # ENIGMA format: genus/species or higher-level taxon name
    # Look up a mapping or parse GTDB for linked genomes
    # For now, return first word (genus-level proxy)
    return s.split()[0]
```

Better yet, for cultured genomes, query `browser_taxon.taxonomy_id` and use NCBI taxonomy to get phylum unambiguously. For MAGs, parse `gtdb_taxonomy` directly.

### 5. **Add genome-size-normalized analysis** (Priority: LOW, marked as future work)

Create a new notebook (NB09) that:
- Filters to phyla present in both cohorts (e.g., Pseudomonadota, Bacteroidota)
- Size-matches genomes (e.g., only compare cultured genomes 1-2 Mbp vs MAGs 1-2 Mbp)
- Re-runs Fisher's exact test on this size-matched subset
- Reports how many KOs remain significantly biased after controlling for genome size

This would isolate "true cultivation selection" from "CPR genome streamlining" effects and strengthen the biological interpretation.

### 6. **Clarify Oak Ridge vs pan-subsurface framing** (Priority: LOW)

Either:
- **Option A**: Retitle the project to "What Metabolic Functions Does the Cultured Collection Miss in Subsurface Environments?" to match the actual MAG cohort, and update the README to emphasize generalizability.
- **Option B**: Revert to ORFRC-specific MAGs when assembly FASTAs become accessible (future work), and keep the current title.

The current mismatch between title ("at Oak Ridge") and cohort (global subsurface MAGs) may confuse readers who expect site-specific findings.

### 7. **Add missing figures or remove references** (Priority: LOW)

Either generate `phylum_comparison.png`, `genome_size_distribution.png`, and `marker_heatmap.png` by re-running NB04/NB05, or remove references to these figures from the notebook code if they are not essential to the REPORT.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review (Claude, claude-sonnet-4-5@20250929)
- **Date**: 2026-05-08
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 8 notebooks, 8 data files, 3 figures, 1 module, requirements.txt, pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
