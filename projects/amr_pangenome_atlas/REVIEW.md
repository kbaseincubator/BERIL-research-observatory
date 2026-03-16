---
reviewer: BERIL Automated Review
date: 2026-03-15
project: amr_pangenome_atlas
---

# Review: Pan-Bacterial AMR Gene Landscape

## Summary

This is a mature, well-executed project that delivers a pangenome-scale survey of antimicrobial resistance genes across 27,690 bacterial species. The study integrates the `bakta_amr` table (83,008 AMRFinderPlus hits) with pangenome conservation flags, GTDB taxonomy, NCBI isolation metadata, AlphaEarth environmental embeddings, and Fitness Browser fitness scores — a genuinely multi-dimensional analysis. All six stated hypotheses are tested with appropriate statistical methods, the notebooks are fully executed with saved outputs, and the README → RESEARCH_PLAN → notebooks → REPORT documentation chain is coherent and complete. The central finding — a clear intrinsic-versus-acquired AMR dichotomy expressed at pan-bacterial scale, with beta-lactamases sitting 2.2× above the core genome baseline while mobile resistance elements are entirely accessory — is scientifically novel and well-supported. The main areas for improvement are minor: one potential classification issue in NB05, a modest gap in figure coverage for the fitness analysis (NB06), and a few places where the REPORT could be tightened with effect-size summaries and explicit cross-notebook citation.

---

## Methodology

**Research question clarity**: All six hypotheses in RESEARCH_PLAN.md are specific and testable. H1–H6 are independently addressable from available BERDL tables, and the analysis plan maps each hypothesis to concrete SQL queries and statistical tests. This is exemplary hypothesis-driven design.

**Approach soundness**: Each analytical step is appropriate for the data:
- H1 uses chi-squared + Wilcoxon signed-rank on paired species data, avoiding Simpson's paradox by controlling for species composition.
- H2 uses within-phylum Spearman correlations (10 phyla tested separately), correctly separating phylogenetic structure from pangenome openness effects.
- H3 uses COG category enrichment against an 86M-cluster baseline, not just internal AMR proportions — this is the right denominator.
- H4 uses Kruskal-Wallis (appropriate for non-normal multi-group comparison) then Spearman for the continuous AlphaEarth diversity predictor.
- H6 uses DIAMOND at 100% identity to link AMR clusters to Fitness Browser genes, which is methodologically conservative and appropriate for measuring known-gene fitness effects.

**Data sources**: All source tables are explicitly named (database + table name) and row counts are stated. The provenance chain from `bakta_amr` → `gene_cluster` → `bakta_annotations` → `eggnog_mapper_annotations` is transparent.

**One methodological concern**: NB05 classifies species by majority-vote over NCBI `isolation_source` strings (27 keywords → 7 broad categories). The keyword list covers the obvious cases, but "Other/Unclassified" environment accounts for ~38% of species-level classification. The REPORT acknowledges sampling bias but does not quantify how many of the 14,723 AMR-carrying species are in the "Other/Unclassified" bin. If clinical species are over-represented in the unclassified remainder, the 2.7× AMR enrichment in clinical versus soil could be modestly inflated. A brief sensitivity analysis (e.g., restricting to the 5 well-classified categories) would strengthen the claim.

**Reproducibility**: Excellent. The README contains a `## Reproduction` section listing all seven notebooks in run order, flagging which ones require a live Spark session and which can run locally from cached CSVs. Expected runtimes are given. A `requirements.txt` lists pinned minimum versions of all five dependencies. A researcher could reproduce this analysis on any BERDL JupyterHub node without additional instructions.

---

## Code Quality

**SQL correctness**: Queries are well-formed throughout. Joins use appropriate keys (`cluster_id`, `species_id`, `genome_id`) and filter conditions are applied before aggregation. The incremental approach — dump a manageable AMR-joined table in NB01, then join from the cached CSV in downstream notebooks — is architecturally sound and avoids redundant 132M-row scans.

**Pitfall adherence**: The project demonstrates strong awareness of documented BERDL pitfalls:
- `ncbi_env` is queried in EAV format and correctly pivoted in NB05 (`attribute = 'isolation_source'`).
- Species IDs with `--` delimiter are handled via exact equality joins, not string splitting.
- Large cross-joins (AMR × AlphaEarth embeddings at 2,684 species × 64 dimensions) are chunked to stay within gRPC message limits.
- The COG enrichment baseline in NB04 correctly queries the full `bakta_annotations` table rather than materializing a second large join.

**Statistical methods**: All tests are appropriate for the data type and distribution (non-parametric tests for skewed AMR count distributions, chi-squared for categorical conservation class comparisons). Effect sizes (odds ratios, Spearman ρ) are reported alongside p-values throughout. Multiple hypothesis testing is not formally corrected, but the p-values across all main tests are so extreme (many < 1e-100) that Bonferroni correction would not change the conclusions — this could be noted explicitly in the REPORT.

**Notebook organization**: All seven notebooks follow a clean setup → query → analysis → visualization structure. Cell count is lean (2–9 cells per notebook), which keeps logic focused. NB07's synthesis is appropriately brief, delegating detail to earlier notebooks.

**Minor code issue**: In NB06, the DIAMOND-based linking logic filters `percent_identity = 100` to find AMR cluster representatives in the FB link table. This is correct for avoiding false matches, but the 100%-identity threshold may miss closely related homologs (e.g., variants differing by a single synonymous substitution). The REPORT correctly frames this as a conservative estimate, but the threshold choice deserves a one-line comment in the code cell.

---

## Findings Assessment

**H1 (Conservation)**: Finding fully supported. The OR=0.494 and paired Wilcoxon p=1.1e-130 across 4,252 species constitute very strong evidence. The mechanism-level breakdown (beta-lactamases 54.9% core vs. regulatory genes 6.5% core) adds important nuance and is the project's most interesting sub-finding.

**H2 (Phylogenetic Distribution)**: Finding well-supported. The Gammaproteobacteria concentration (45% of all AMR clusters) and near-zero global openness correlation (ρ=0.006) vs. significant within-phylum correlations cleanly partition phylogenetic signal from ecological signal.

**H3 (Functional Context)**: COG V enrichment (7.05×) validates the AMRFinderPlus annotations as bona fide defense genes, not annotation noise. COG P enrichment (1.93×) for inorganic ion transport is an interesting secondary finding; the identification of mercury/arsenic resistance families as drivers is a concrete, checkable claim. Partially supports the original hypothesis (enrichment near defense/transport, but no spatial co-localization analysis was attempted).

**H4 (Environmental Signal)**: Finding strongly supported. The Kruskal-Wallis result (H=440, p=7.0e-93) and the AlphaEarth niche-breadth predictor (ρ=0.466) are independent lines of evidence converging on the same conclusion. The additional finding that clinical AMR is *less* core (30.8%) than soil AMR (58.1%) is particularly strong — it distinguishes the mechanism (horizontal acquisition) from a simpler confound (clinical genomes having larger accessory genomes in general).

**H5 (Annotation Depth)**: Zero Pfam coverage for AMR clusters is a notable empirical finding, not just an absence of dark matter. The REPORT's explanation (non-overlapping HMM databases) is plausible and worth flagging as a downstream consequence: structural annotation pipelines that rely on Pfam hits will systematically miss this class of genes.

**H6 (Fitness Cost)**: The finding (AMR genes slightly *less* costly than baseline, p=3.7e-6) is reported accurately, but the REPORT's interpretation deserves one additional sentence: the Fitness Browser organisms skew toward environmental isolates where intrinsic resistance genes predominate; the result may not generalize to recently acquired mobile resistance elements in clinical strains. This limitation is hinted at but not stated explicitly.

**Incomplete or placeholder content**: None found. All analysis sections in REPORT.md are fully written; no "TODO" or placeholder cells exist in any notebook.

**Figures and labeled axes**: All 17 figures are present. Axis labels and legends appear in figure-generating code cells. The synthesis figure (fig1_amr_overview.png) covers conservation class, species distribution, top genes, and mechanism breakdown — a reasonable four-panel overview. One gap: NB06 (fitness analysis) has no standalone figure file; the fitness distribution is only described in text output. Adding a `amr_fitness_by_mechanism.png` would give this analysis the same visual documentation as the other five hypotheses.

---

## Suggestions

1. **(Critical) Add fitness distribution figure for NB06.** The fitness analysis is one of the most interesting hypotheses, but it is the only one without a saved PNG in `figures/`. Add a box plot or violin plot of fitness scores grouped by AMR mechanism (or conservation class) and save it as `figures/amr_fitness_by_mechanism.png`. This also means NB07's synthesis figure could reference it.

2. **(Important) Quantify the "Other/Unclassified" environment bin in NB05.** Add a one-cell summary showing how many of the 14,723 AMR-carrying species fall into each classification category, including the unclassified remainder. If >30% are unclassified, note this in the REPORT and consider a brief sensitivity test (e.g., restrict the Kruskal-Wallis to the 5 best-covered categories).

3. **(Important) Add an explicit note on the NB06 100%-identity threshold.** A comment in the DIAMOND-linking cell explaining why 100% identity was chosen (conservative, avoids paralog confusion) and what fraction of AMR cluster representatives went unmatched would improve transparency. Add one sentence to the REPORT acknowledging this may undercount fitness effects for closely related gene variants.

4. **(Moderate) Note the absence of multiple-testing correction in the REPORT.** The six hypotheses involve many individual tests. The REPORT should include one sentence explaining why Bonferroni or FDR correction was not applied — the p-values are so extreme for the primary tests that correction does not change conclusions, and the supplementary per-gene tests are exploratory.

5. **(Moderate) Clarify the mechanism classification method in REPORT.md.** The "Other/Unclassified" category at 22.2% is large. A footnote or REPORT paragraph explaining that classification uses AMRFinderPlus `subclass` and `class` fields (not CARD ARO ontology) would contextualize the gap. Suggest CARD mapping as a specific next step with an estimated feasibility note (the `bakta_db_xrefs` table contains cross-references that may already include CARD identifiers).

6. **(Moderate) Cross-reference notebooks in the REPORT.** REPORT.md currently presents findings without citing which notebook produced each result. Adding brief parenthetical references (e.g., "NB02, Fig. amr_conservation_per_species.png") would make the document easier to navigate and validate.

7. **(Minor) Add a `data/README.md` describing all 10 CSV output files.** Each file's row count, column semantics, and the notebook that produced it are currently implicit. A brief data dictionary would help future users who want to work from the cached CSVs without re-running Spark queries.

8. **(Minor) Consider adding `spark_connect_remote` and `berdl_remote` to `requirements.txt`.** These packages are required for the Spark-dependent notebooks (NB01–NB06) but are currently omitted. Including them with a comment (`# required for Spark Connect; install from internal PyPI`) would prevent confusing import errors for new users following the reproduction guide.

---

## Review Metadata

- **Reviewer**: BERIL Automated Review
- **Date**: 2026-03-15
- **Scope**: README.md, RESEARCH_PLAN.md, REPORT.md, 7 notebooks (all with saved outputs), 10 data files, 17 figures, requirements.txt, docs/pitfalls.md
- **Note**: This review was generated by an AI system. It should be treated as advisory input, not a definitive assessment.
