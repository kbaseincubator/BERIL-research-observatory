# Research Plan: Lignin Enrichment and Ecological Memory in Microbial Communities

## Research Question
Does sequential enrichment on lignin, with or without labile carbon, produce distinct bacterial and fungal community structures — and does the carbon history of Round 1 create ecological memory that shapes community assembly in Round 2?

## Statistical Limitations and Framing

This study has n=3 biological replicates per group (21 samples total). This constrains statistical power and shapes the analytical approach throughout:

- **Pairwise permutation floor**: Standard PERMANOVA comparing two groups of n=3 has only 20 possible permutations, making p < 0.05 unachievable. We address this by (a) using a factorial PERMANOVA on Round 2 groups (n=12 total, thousands of permutations), and (b) reporting effect sizes (R²) alongside permutation p-values for all pairwise contrasts.
- **Study framing**: This study is **hypothesis-generating** for effects tested at n=3 vs n=3, and **confirmatory** for effects tested using the factorial design (n=12) or pooled contrasts (n=9+). We emphasize effect sizes and biological patterns over p-value thresholds throughout.
- **Contrast hierarchy**:
  - *Primary (confirmatory)*: Round 2 factorial effects (H2, H3) tested with n=12; Base vs enriched (H1) tested with n=9.
  - *Secondary (exploratory)*: Round 1 pairwise comparisons (n=3 vs n=3); individual group contrasts.
- **Effect size calibration**: With n=3 per group, the expected PERMANOVA R² under the null is ~0.20 for a two-group comparison. Only R² substantially exceeding this baseline should be interpreted as biologically meaningful.

## Hypotheses

### H1: Lignin enrichment restructures the community
- **H0**: Community composition after lignin enrichment is indistinguishable from the base community.
- **H1**: Lignin enrichment selects for a distinct community enriched in known lignin-degrading taxa (e.g., *Sphingomonas*, *Rhodococcus*, *Pseudomonas*, *Streptomyces* for bacteria; white-rot and soft-rot fungi for ITS).
- **Test**: PERMANOVA on Base vs Round 1 groups (Groups 1, 2, 3; n=9).

### H2: Labile carbon modulates the lignin-enriched community
- **H0**: Adding labile carbon to lignin has no effect on community composition relative to lignin alone.
- **H1**: Labile carbon supplementation shifts the community — potentially by supporting non-lignolytic taxa that co-metabolize lignin breakdown products or by enabling priming effects that enhance lignin degradation.
- **Test (primary)**: Labile_Carbon main effect in Round 2 factorial PERMANOVA (Groups 4-7; n=12).
- **Test (secondary, exploratory)**: Group 2 vs 3 pairwise (n=3 vs n=3; effect-size focus).

### H3: Enrichment history creates ecological memory
- **H0**: Round 2 community composition depends only on the Round 2 carbon source, not on Round 1 history.
- **H1**: Communities with different Round 1 histories (lignin vs lignin+LC) assemble differently in Round 2 even when grown on the same carbon source.
- **Test**: Round1_History main effect in Round 2 factorial PERMANOVA (Groups 4-7; n=12).
- **Supplementary**: Pairwise effect sizes for Groups 4 vs 5 (same R2, different history) and Groups 6 vs 7 (same R2, different history).

### H4: Bacteria and fungi respond differently
- **H0**: 16S and ITS community shifts are concordant across all conditions.
- **H1**: Bacterial and fungal communities show different sensitivities to lignin vs labile carbon, reflecting their distinct roles in lignocellulose decomposition.
- **Test**: Per-group concordance comparison (Procrustes M² per group, co-inertia analysis) rather than global Mantel test. The question is *where* 16S and ITS diverge, not whether they are globally correlated.

### H5: Serial passaging reduces diversity
- **H0**: Alpha diversity is maintained across enrichment rounds.
- **H1**: Sequential enrichment on a recalcitrant substrate (lignin) leads to progressive diversity loss, with Round 2 communities less diverse than Round 1, which are less diverse than the base.
- **Test**: Kruskal-Wallis across Base / Round 1 / Round 2 (pooled by round, n=3 / 6 / 12).

## Literature Context
*To be expanded with `/literature-review` before analysis begins. Specifically:*
- Expected effect sizes for lignin enrichment experiments (to calibrate power expectations)
- Existing evidence for ecological memory in microbial enrichment cultures
- Methodological recommendations for small-sample amplicon studies (n < 5)
- Known lignin-degrading taxa and functional guilds (bacteria and fungi)

Key background:
- Lignin is the most abundant aromatic polymer in nature, and its degradation is primarily initiated by fungal peroxidases and laccases, with bacterial enzymes (DyP-type peroxidases, laccases, beta-etherases) playing secondary roles.
- The "priming effect" — where labile carbon addition stimulates decomposition of recalcitrant organic matter — is well-documented in soil ecology but mechanistically poorly understood at the community level.
- Ecological memory in microbial communities (the influence of past conditions on present community assembly) has been demonstrated in soil mesocosms and bioreactors but rarely with controlled sequential enrichment designs.
- Sequential enrichment/passaging experiments are a powerful tool for studying community assembly rules, but most have focused on simple carbon sources rather than complex polymers like lignin.

## Data Sources

### User-provided data
| Data | Format | Location | Samples |
|------|--------|----------|---------|
| 16S amplicon reads | fastq.gz | `user_data/16S/` | 21 samples |
| ITS amplicon reads | fastq.gz | `user_data/ITS/` | 21 samples |
| Sample metadata | TSV | `user_data/sample_metadata.tsv` | 21 rows |

### Reference databases (to be downloaded)
| Database | Version | Purpose |
|----------|---------|---------|
| SILVA | 138.2 (or latest) | 16S taxonomy assignment |
| UNITE | Latest | ITS taxonomy assignment |

### Technical metadata (to be provided by user)
- DNA extraction batch assignments (all samples same batch?)
- Library preparation batch and protocol
- Sequencing run(s) and lane assignments
- Primer sequences used for 16S and ITS

## Pre-registered Bioinformatics Decisions

These decisions are specified before data analysis to prevent post-hoc optimization:

| Decision | Choice | Justification |
|----------|--------|---------------|
| Feature type | ASVs (DADA2) | Higher resolution than 97% OTUs; preferred for community-level analysis. If DADA2 unavailable, fall back to 97% OTUs via vsearch. |
| Rarefaction | Rarefy to minimum sample depth for diversity metrics; use unrarefied counts with CLR for differential abundance | Follows Weiss et al. 2017 recommendation; rarefaction protects alpha/beta diversity metrics from depth bias while CLR handles compositionality for DA. |
| Prevalence filter | Retain ASVs present in ≥ 2 of 21 samples | Removes singleton ASVs that inflate beta diversity noise without discarding low-abundance but consistent taxa. |
| Abundance filter | Retain ASVs with ≥ 10 total reads across all samples | Removes likely sequencing artifacts. |
| Chimera removal | DADA2 internal (removeBimeraDenovo) or vsearch --uchime_denovo | Standard for each pipeline. |
| Taxonomy confidence | Assign taxonomy at ≥ 80% bootstrap confidence (SILVA/UNITE naive Bayes) | Standard threshold; assignments below this reported as unclassified at that rank. |
| Multiple testing | BH-FDR correction within each analysis notebook; primary contrasts reported separately from exploratory | Prevents inflating family-wise error across the full contrast set. |

## Query Strategy

This project uses user-provided amplicon data, not BERDL lakehouse queries. BERDL integration is possible for cross-referencing identified taxa against the pangenome database, but the primary analysis is amplicon-based.

### BERDL Cross-references (post-analysis, conditional)
**Trigger**: Pursue BERDL cross-referencing only if ≥ 3 genera are consistently enriched by lignin across replicates AND have species-level representation in `kbase_ke_pangenome`.

**Scope** (genus-to-species resolution caveat acknowledged):
- Map lignin-enriched genera to `kbase_ke_pangenome` to check for lignin-degradation gene annotations (DyP peroxidases, laccases, beta-etherases, aromatic ring cleavage pathways)
- Check GapMind pathway completeness for aromatic compound catabolism in enriched taxa
- Cross-reference with Fitness Browser for aromatic compound fitness data (vanillate, benzoate, catechol experiments)

**Limitation**: 16S/ITS amplicons resolve to genus level at best. Pangenome data is species-level. Cross-references are indicative, not definitive.

## Analysis Plan

### NB00: Setup and Quality Control
- **Goal**: Inspect raw reads, determine paired-end vs single-end, check for primers/adapters, assess read quality
- **Tools**: fastp (QC reports), file inspection
- **Expected output**: QC summary, sample manifest mapping filenames to groups
- **Sanity check**: Verify all 21 samples have adequate read depth; flag any samples with < 1,000 reads

### NB01: Read Processing
- **Goal**: Process raw reads into ASV feature tables with taxonomy
- **Tools**: cutadapt (primer removal), DADA2 (denoising), SILVA/UNITE (taxonomy)
- **Pipeline**:
  1. Primer removal with cutadapt (if primers detected in NB00)
  2. Quality filtering and denoising with DADA2
  3. Chimera removal (DADA2 removeBimeraDenovo)
  4. Taxonomy assignment: naive Bayes classifier against SILVA 138.2 (16S) and UNITE (ITS)
  5. Build phylogenetic tree of 16S ASVs (for Faith's PD and UniFrac)
- **Expected output**: ASV feature tables, taxonomy assignments, representative sequences, phylogenetic tree (16S)
- **Fallback**: If DADA2/R unavailable, use vsearch for 97% OTU clustering
- **Pre-registered filters applied**: prevalence ≥ 2 samples, abundance ≥ 10 total reads

### NB02: Community Composition Overview and Replicate Consistency
- **Goal**: Visualize taxonomic composition and verify replicate consistency before group comparisons
- **Sanity checks** (before proceeding to NB03-NB06):
  - Dendrogram of all 21 samples (Bray-Curtis) colored by group — verify within-group replicates cluster together
  - PERMDISP within groups — flag any group with anomalously high dispersion
  - Identify and flag outlier replicates (samples more similar to another group than their own)
- **Composition**: Taxonomy bar plots at phylum and genus level for all 7 groups (16S and ITS separately)
- **Rarefaction**: Rarefaction curves to assess sequencing depth adequacy and determine rarefaction depth
- **Expected output**: Taxonomy bar plots, rarefaction curves, relative abundance tables, replicate consistency report

### NB03: Alpha Diversity
- **Goal**: Compare within-sample diversity across groups and enrichment stages
- **Metrics**: Observed ASVs, Shannon, Simpson, Chao1, Pielou's evenness, Faith's PD (16S only)
- **Computed on**: Rarefied counts (depth determined in NB02)
- **Statistics**: Kruskal-Wallis (omnibus), Dunn's test (pairwise, BH-FDR)
- **Planned contrasts** (ordered by priority):
  1. *Primary*: Base vs all enriched (n=3 vs n=18; enrichment effect — H1/H5)
  2. *Primary*: Base vs Round 1 vs Round 2 pooled (n=3 / 6 / 12; passage effect — H5)
  3. *Primary*: Labile carbon effect in Round 2 (n=6 vs n=6, pooled across histories — H2)
  4. *Secondary*: Group 2 vs Group 3 (n=3 vs n=3; Round 1 labile carbon — H2, exploratory)
  5. *Secondary*: History effect in Round 2 (n=6 vs n=6, pooled across R2 conditions — H3)
- **Expected output**: Diversity boxplots with effect sizes, statistical test tables, figures

### NB04: Beta Diversity and Ordination
- **Goal**: Compare community-level compositional differences and test experimental factors
- **Distances**: Bray-Curtis, Jaccard, Aitchison (Euclidean on CLR-transformed), weighted/unweighted UniFrac (16S only)
- **Ordination**: PCoA and NMDS on Bray-Curtis and Aitchison distances
- **PERMANOVA models** (three-tier structure):

  | Model | Samples | Formula | Tests | Power |
  |-------|---------|---------|-------|-------|
  | M1: Base vs Round 1 | Groups 1, 2, 3 (n=9) | `dist ~ Group` | H1 (enrichment), H2 at R1 | Moderate |
  | M2: Round 2 factorial | Groups 4, 5, 6, 7 (n=12) | `dist ~ R1_History * R2_LabileC` | H2 at R2, H3 (memory), interaction | Good |
  | M3: Full trajectory | All 7 groups (n=21) | `dist ~ Group` | Overall group effect | Good |

- **Effect sizes**: Report PERMANOVA R² for every test, with null-expectation calibration (expected R² under null ≈ 1/(n_groups)).
- **PERMDISP**: Test homogeneity of dispersions for each model. If heterogeneous, use pooled-residual permutation with caution and note the violation.
- **Pairwise contrasts**: Report R² and permutation p-values for all group pairs; interpret as exploratory for n=3 vs n=3 comparisons.
- **Batch effects**: If technical metadata reveals batch structure, include batch as a covariate or blocking factor in PERMANOVA.
- **16S-ITS concordance (H4)**: Per-group Procrustes M² (do 16S and ITS agree *within each group*?), co-inertia analysis as a more powerful global test than Mantel.
- **Expected output**: Ordination plots, PERMANOVA tables with R², distance heatmaps, concordance analysis, figures

### NB05: Differential Abundance
- **Goal**: Identify taxa enriched or depleted by specific conditions
- **Method**: CLR transformation + Wilcoxon tests (ALDEx2-style Monte Carlo from Dirichlet posterior)
- **Approach**: Two-tier testing to manage multiple testing burden:
  1. **Targeted (pre-specified lignolytic genera)**: Test a pre-registered list of ~15-20 genera with known lignin/aromatic degradation roles. Lower multiple testing penalty, results are confirmatory.
  2. **Untargeted (all ASVs)**: Full differential abundance across all ASVs. Results are exploratory; report effect sizes (CLR difference) alongside p-values.
- **Key contrasts**:
  1. *Primary*: Base vs Lignin (Group 1 vs 2) — what does lignin select for?
  2. *Primary*: Labile carbon effect pooled across Round 2 (Groups 4+5 vs 6+7, n=6 vs 6)
  3. *Secondary*: Lignin vs Lignin+LC at Round 1 (Group 2 vs 3, n=3 vs 3, exploratory)
  4. *Secondary*: History effect pooled across Round 2 conditions (Groups 4+6 vs 5+7, n=6 vs 6)
- **Visualization**: Volcano plots, heatmaps of significant taxa, genus-level summaries
- **Cross-kingdom**: Compare lignin-responsive taxa between 16S and ITS — do the same conditions select similar functional guilds?
- **Expected output**: Significant taxa tables with effect sizes, volcano plots, heatmaps

### NB06: Enrichment History and Ecological Memory
- **Goal**: Directly test whether Round 1 carbon history shapes Round 2 outcomes
- **Analyses**:
  - **Convergence/divergence**: Bray-Curtis distances between groups sharing Round 2 conditions — do Groups 4 and 5 converge (deterministic assembly) or remain distinct (ecological memory)?
  - **Trajectory analysis**: Track community composition through Base → R1 → R2 in ordination space; do communities follow parallel or divergent paths?
  - **Shared vs unique ASVs**: Across the enrichment trajectory (Base → R1 → R2). Which ASVs persist through both rounds vs. appear only in Round 2?
  - **History-indicator taxa**: Rather than formal indicator species analysis (underpowered at n=3), use a presence/absence criterion: ASVs found in all 3 replicates of one history but 0/3 replicates of the other. This is a robust signal at n=3.
  - **Functional inference**: For history-indicator taxa, check known metabolic capabilities (literature + optional BERDL cross-reference)
- **Expected output**: Trajectory plots, convergence/divergence metrics, history-indicator taxa lists

### NB07: Synthesis
- **Goal**: Integrate findings across all notebooks, create summary figures
- **Expected output**: Summary ordination panel (16S + ITS side by side), key findings table per hypothesis, draft REPORT.md via `/synthesize`

## Expected Outcomes

### If H1 supported (lignin restructures community):
Lignin enrichment should select for genera with known aromatic catabolism capabilities. For bacteria: *Sphingomonas*, *Pseudomonas*, *Rhodococcus*, *Streptomyces*, *Caulobacter*. For fungi: Basidiomycota white-rot taxa, Ascomycota soft-rot taxa. The base community should be clearly separated in ordination space.

### If H2 supported (labile carbon modulates):
Labile carbon addition could either (a) support additional taxa that co-metabolize lignin breakdown products (priming → more diverse community) or (b) allow fast-growing copiotrophic taxa to dominate, suppressing specialist lignin degraders (competitive exclusion → different dominant taxa). The direction of the effect is an empirical question.

### If H3 supported (ecological memory):
The Round 2 factorial PERMANOVA would show a significant Round1_History main effect, indicating that communities with different Round 1 exposure assemble differently even under the same Round 2 conditions. This would demonstrate path-dependent community assembly on lignin.

### If H0 not rejected for H3:
Round 2 communities with the same carbon source would converge regardless of Round 1 history. This would suggest that lignin is a strong enough selective filter to override community history — a "deterministic assembly" result. This is itself an interesting finding.

### Potential confounders:
- Stochastic variation in the base community inoculum across replicates
- Bottle effects during enrichment
- DNA extraction bias between bacteria and fungi
- PCR amplification bias (16S vs ITS primer specificity)
- Sequencing depth variation across samples
- Batch effects in extraction, library prep, or sequencing (to be assessed with technical metadata)

## Revision History
- **v1** (2026-05-07): Initial plan
- **v2** (2026-05-07): Revised after PLAN_REVIEW_1. Added: statistical limitations section, pre-registered bioinformatics decisions, nested factorial PERMANOVA design, Aitchison distance and UniFrac, replicate consistency checks, effect-size-focused reporting, co-inertia analysis for H4, presence/absence indicator approach for H3, targeted vs untargeted DA tiers, BERDL cross-referencing trigger criteria, technical metadata requirements.

## Authors
- Markus de Raad (LBNL) — ORCID: [0000-0001-8263-9198](https://orcid.org/0000-0001-8263-9198)
