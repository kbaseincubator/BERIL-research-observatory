# Research Plan: Counter Ion Effects on Metal Fitness Measurements

## Research Question

When bacteria are exposed to metal salts (e.g., CoCl₂, NiCl₂, CuCl₂), how much of the observed fitness effect is caused by the metal cation versus the counter anion? Specifically, does the chloride delivered by metal chloride salts at high concentrations confound the metal fitness signal in the Fitness Browser, and does correcting for this change the conclusions of the Metal Fitness Atlas?

## Hypothesis

- **H0**: Counter ions contribute negligibly to the fitness effects observed in metal stress experiments. The genes identified as "metal-important" in the Metal Fitness Atlas are genuinely metal-responsive, and removing chloride-responsive genes does not meaningfully change the atlas conclusions (core enrichment, conserved families, cross-species patterns).

- **H1**: Chloride counter ions contribute a significant confounding signal to metal fitness profiles, with three testable predictions:

### Sub-hypotheses

- **H1a (Chloride contamination)**: For organisms with both NaCl and metal-chloride experiments, a significant fraction (>20%) of genes classified as "metal-important" also show fitness defects under NaCl stress alone, indicating chloride/osmotic confounding rather than metal-specific toxicity.

- **H1b (Dose-dependent confounding)**: The overlap between metal-important and NaCl-important genes scales with effective Cl⁻ concentration — higher for cobalt chloride (40–500 mM Cl⁻ in DvH) than for copper chloride (0.2 mM Cl⁻).

- **H1c (Atlas robustness)**: After removing chloride-responsive genes from the metal-important set, the core genome enrichment pattern (87.4% core, OR=2.08 in the original atlas) either:
  - **Weakens significantly** → the chloride signature inflated apparent core enrichment (chloride/osmotic stress genes tend to be core because they involve cell envelope and general stress response)
  - **Remains robust** → the core enrichment is a genuine metal biology finding independent of counter ion effects

- **H1d (Anion-specific signatures)**: Genes important for metals delivered as oxyanions (CrO₄²⁻, MoO₄²⁻, SeO₄²⁻, WO₄²⁻ — with Na⁺ as counter cation) show a different functional profile than genes important for metals delivered as chloride salts (CoCl₂, NiCl₂, CuCl₂ — with Cl⁻ as counter anion), even after controlling for metal identity.

## Literature Context

Counter ion effects on metal toxicity are a known but rarely controlled-for confound in microbiology:

- **Danilova et al. (2020)** directly compared copper and zinc in sulfate vs chloride forms on bacterial biofilms (*S. pyogenes*, *E. coli*). At 0.5 M, copper sulfate inhibited *E. coli* biofilm 5.6x while copper chloride inhibited only 2.2x — a 2.5-fold difference attributable to the counter ion. PMID: 32986214.

- **Price et al. (2018)** established the Fitness Browser with RB-TnSeq across 32 bacteria under thousands of conditions including metals, but did not discuss counter ion confounding. The experimental design used whatever salt was standard in the field (typically chlorides for divalent metals). PMID: 29769716.

- **Our Metal Fitness Atlas** (this observatory) found that metal-important genes are 87.4% core (OR=2.08), driven by core cellular processes vulnerable to metal disruption (cell envelope, DNA repair, central metabolism). These same processes are also vulnerable to osmotic/chloride stress — raising the question of whether the core enrichment partly reflects chloride rather than metal effects.

- The **general stress response** literature in bacteria documents substantial overlap between osmotic stress and metal stress responses (e.g., RpoS regulon, envelope stress response), but no study has systematically quantified this overlap using genome-wide fitness data.

**Gap**: No study has tested whether counter ions from metal salts confound genome-wide fitness measurements, despite the Fitness Browser containing experiments where Cl⁻ concentrations from metal salts reach 500 mM. This project fills that gap.

## Data Sources

### Fitness Browser (`kescience_fitnessbrowser`)

**NaCl/Sodium Chloride experiments** (controls):

| Organism | NaCl Conc (mM) | # Exps | Also Has Metal Chloride Exps? |
|----------|---------------|--------|-------------------------------|
| DvH | 62.5, 125 | 6 | Yes (Co, Ni, Cu, Fe, Mn, Hg, Al) |
| MR1 | 250, 350 | 2 | Yes (Cu, Ni, Co, Al, Zn) |
| Btheta | 350 | 1 | Yes (Cu, Ni, Co, Al, Zn) |
| Caulo | 100 | 2 | Yes (Cu, Ni, Co, Al) |
| Cup4G11 | 300 | 2 | Yes (Cu, Ni, Co, Al, Zn) |
| Koxy | 1000 | 2 | Yes (Cu, Ni, Co, Al) |
| SB2B | 500, 600, 700 | 3 | Yes (Cu, Ni, Co, Al, Zn) |
| Pedo557 | 300 | 2 | Yes (Cu, Ni, Co, Al, Zn) |
| Phaeo | 600, 700, 800 | 4 | Yes (Cu, Ni, Co, Al, Zn) |
| Korea | 100, 200 | 2 | Yes (Cu, Ni, Co, Al) |
| Cola | 750, 1000 | 4 | Yes (Cu, Ni, Co, Al, Zn) |
| Dino | 600 | 2 | Yes (Cu, Ni, Co, Al, Zn) |
| Ponti | 500, 750 | 4 | Yes (Cu, Ni, Co) |
| BFirm | 200 | 1 | Yes (Zn) |
| psRCH2 | 200, 400 | 3 | Yes (Cu-chloride AND Cu-sulfate, Ni, Co, Fe, Zn) |
| pseudo3_N2E3 | 500 | 1 | Yes (Cu, Ni, Co, Al) |
| SynE | 0.5–250 (dose-response) | 12 | Yes (Zn-sulfate only) |
| Keio | 750 | 1 | No cached metal matrix (but has metal exps) |
| Kang | 500 | 1 | No cached metal matrix (but has metal exps) |

**Metal experiments**: 559 experiments from `metal_experiments.csv` (metal_fitness_atlas project).

**psRCH2 copper comparison**: This organism uniquely has copper tested as both CuCl₂ (3 exps, anaerobic) and CuSO₄ (3 exps, aerobic) — the only within-organism, within-metal counter ion comparison.

### Reusable Data from Prior Projects

| Source | Asset | Use |
|--------|-------|-----|
| `metal_fitness_atlas` | `data/metal_experiments.csv` | Metal experiment classification |
| `metal_fitness_atlas` | `data/metal_fitness_scores.csv` | Per-gene metal fitness summaries |
| `metal_fitness_atlas` | `data/metal_important_genes.csv` | Genes with metal fitness defects |
| `metal_fitness_atlas` | `data/metal_conservation_stats.csv` | Core fraction by metal |
| `metal_fitness_atlas` | `data/conserved_metal_families.csv` | Cross-species metal gene families |
| `fitness_modules` | `data/matrices/{org}_fitness_matrix.csv` | Full fitness matrices (includes NaCl exps) |
| `fitness_modules` | `data/annotations/{org}_experiments.csv` | Experiment metadata |
| `conservation_vs_fitness` | `data/fb_pangenome_link.tsv` | FB-to-pangenome gene mapping |

## Effective Chloride Concentrations

A key motivating observation: the chloride delivered by metal chloride salts can far exceed the baseline media chloride (~17 mM for DvH MoYLS4).

| Metal Salt (DvH) | Metal Conc | Valence | Effective Cl⁻ | Ratio to Baseline |
|-------------------|------------|---------|---------------|-------------------|
| CoCl₂ | 250 mM | 2+ | **500 mM** | **~30x** |
| CoCl₂ | 100 mM | 2+ | **200 mM** | **~12x** |
| MnCl₂ | 100 mM | 2+ | **200 mM** | **~12x** |
| AlCl₃ | 10 mM | 3+ | **30 mM** | ~2x |
| HgCl₂ | 10 mM | 2+ | 20 mM | ~1x |
| NiCl₂ | 1.5 mM | 2+ | 3 mM | negligible |
| CuCl₂ | 0.1 mM | 2+ | 0.2 mM | negligible |

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_fitnessbrowser.experiment` | Identify NaCl experiments | ~7.5K | Filter by condition_1 for Sodium Chloride |

**Note**: All analysis uses cached fitness matrices from `fitness_modules/data/matrices/` and experiment annotations from `fitness_modules/data/annotations/`. No Spark queries are needed — the cached matrices already contain NaCl experiment columns alongside metal experiment columns.

### Performance Plan
- **Tier**: Fully local — all data from cached CSVs (no Spark required)
- **Estimated complexity**: Low (pandas operations on matrices of ~3K genes × ~200 experiments)
- **Known pitfalls**: All FB columns are strings (CAST required); fitness matrices are pre-cast to float

## Analysis Plan

### Notebook 1: NaCl Experiment Identification and Fitness Extraction
- **Goal**: Identify all NaCl stress experiments across FB organisms, extract fitness profiles, and build an "NaCl fitness signature" per organism
- **Method**:
  1. Scan cached experiment annotations for Sodium Chloride experiments
  2. Extract NaCl fitness vectors from cached fitness matrices
  3. For each organism, identify NaCl-important genes (fit < -1, |t| > 4)
  4. Compute effective Cl⁻ concentrations for all metal chloride experiments
- **Expected output**: `data/nacl_experiments.csv`, `data/nacl_important_genes.csv`, `data/effective_chloride_concentrations.csv`

### Notebook 2: Metal-NaCl Fitness Overlap Analysis
- **Goal**: Test H1a — quantify gene overlap between metal-important and NaCl-important gene sets
- **Method**:
  1. For each organism with both NaCl and metal data, compute Jaccard overlap between metal-important and NaCl-important gene sets
  2. Fisher exact test: are metal-important genes enriched among NaCl-important genes?
  3. Compute Pearson/Spearman correlation between NaCl fitness profiles and each metal fitness profile
  4. Stratify by metal: do high-Cl⁻ metals (Co, Mn at >100 mM) show more overlap with NaCl than low-Cl⁻ metals (Cu, Ni at <2 mM)?
  5. Heatmap of per-organism, per-metal overlap with NaCl
- **Expected output**: `data/metal_nacl_overlap.csv`, `figures/nacl_metal_overlap_heatmap.png`, `figures/cl_concentration_vs_overlap.png`
- **Statistical tests**: Fisher exact per organism × metal; Spearman correlation of Cl⁻ concentration vs overlap; meta-analysis across organisms

### Notebook 3: Profile Correlation and Decomposition
- **Goal**: Test H1b — decompose metal fitness profiles into chloride and metal-specific components
- **Method**:
  1. For DvH (richest data: 6 NaCl exps + 13 metals), compute pairwise Pearson correlation between the NaCl mean fitness profile and each metal mean fitness profile
  2. Partial correlation: for each metal fitness profile, compute correlation with other metals after regressing out NaCl — isolates metal-specific signal
  3. For each metal-important gene, classify as:
     - **Chloride-shared**: also NaCl-important (fit < -1 under NaCl)
     - **Metal-specific**: metal-important but NOT NaCl-important
     - **General stress**: important under both NaCl AND multiple non-chloride conditions
  4. Functional enrichment (COG categories) of chloride-shared vs metal-specific genes
- **Expected output**: `data/gene_classification_chloride_vs_metal.csv`, `figures/correlation_nacl_vs_metals.png`, `figures/gene_venn_chloride_metal.png`

### Notebook 4: Chloride-Corrected Metal Atlas
- **Goal**: Test H1c — re-analyze the Metal Fitness Atlas after removing chloride-responsive genes
- **Method**:
  1. Remove chloride-shared genes from the metal-important set
  2. Re-compute core genome enrichment with metal-specific genes only
  3. Compare original atlas OR (2.08) vs corrected OR
  4. Re-analyze per-metal conservation patterns — do the rankings change?
  5. Re-analyze conserved metal families — how many survive after chloride correction?
- **Expected output**: `data/corrected_metal_conservation.csv`, `figures/atlas_original_vs_corrected.png`

### Notebook 5: psRCH2 Counter Ion Comparison
- **Goal**: Direct within-organism comparison of CuCl₂ vs CuSO₄ fitness profiles
- **Method**:
  1. Extract psRCH2 fitness vectors for CuCl₂ (3 exps, anaerobic) and CuSO₄ (3 exps, aerobic)
  2. Correlate the two profiles — if counter ion doesn't matter, they should correlate strongly (allowing for aerobic/anaerobic differences)
  3. Identify genes differentially affected by CuCl₂ vs CuSO₄
  4. Check: are CuCl₂-specific genes also NaCl-important in psRCH2? (psRCH2 has NaCl exps at 200, 400 mM)
  5. **Caveat**: aerobic/anaerobic confound makes this comparison suggestive, not definitive
- **Expected output**: `data/psrch2_cucl2_vs_cuso4.csv`, `figures/psrch2_copper_comparison.png`

### Notebook 6: Cross-Metal Anion Signature Analysis
- **Goal**: Test H1d — compare functional signatures of chloride-delivered vs oxyanion-delivered metals
- **Method**:
  1. Group metals by anion: chloride (Co, Ni, Cu, Al, Fe, Mn, Hg, Cd) vs oxyanion (Cr, Mo, Se, W) vs sulfate (Zn) vs acetate (U)
  2. For each group, compute the aggregated set of important genes
  3. Enrichment analysis: are chloride-group genes enriched in osmotic/envelope functions? Are oxyanion-group genes enriched in different pathways?
  4. Gene overlap network: visualize which metals share gene sets and whether grouping follows anion or metal chemistry
- **Expected output**: `data/anion_group_signatures.csv`, `figures/anion_group_gene_overlap.png`

### Notebook 7: Summary and Synthesis
- **Goal**: Generate publication-quality summary figures
- **Expected output**: Key figures combining results from NB02-06

## Expected Outcomes

- **If H1 supported**: A substantial fraction of "metal fitness genes" are actually chloride/osmotic stress genes. The corrected atlas shows a weaker (but potentially still significant) core enrichment. High-Cl⁻ metals like cobalt are most affected. The 1,182 conserved metal families need to be re-evaluated — some will turn out to be conserved chloride/osmotic families. This would be an important methodological finding for the RB-TnSeq field.

- **If H0 not rejected**: Counter ions contribute negligibly, validating the metal fitness atlas conclusions. The NaCl and metal gene sets are largely non-overlapping, meaning metal-specific toxicity dominates even at high Cl⁻ concentrations. This is itself valuable — it demonstrates the robustness of the atlas findings.

- **Potential confounders**:
  - NaCl concentrations in the FB experiments (62.5–1000 mM) may not match the effective Cl⁻ from metal salts — dose-response nonlinearity
  - NaCl provides both Na⁺ and Cl⁻; metal chlorides provide metal²⁺ and Cl⁻ — the osmotic vs ionic effects are different
  - Some "chloride-shared" genes may be genuinely dual-function (required for both metal and osmotic stress)
  - The psRCH2 CuCl₂ vs CuSO₄ comparison is confounded by aerobic/anaerobic growth

## Key References

1. Danilova TA et al. (2020). "Inhibitory Effect of Copper and Zinc Ions on the Growth of Streptococcus pyogenes and Escherichia coli Biofilms." *Bull Exp Biol Med* 169:648-652. PMID: 32986214.
2. Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509. PMID: 29769716.
3. Dehal P (2026). "Pan-Bacterial Metal Fitness Atlas." BERIL Research Observatory, `projects/metal_fitness_atlas/`.
4. Wetmore KM et al. (2015). "Rapid quantification of mutant fitness in diverse bacteria by sequencing randomly bar-coded transposons." *mBio* 6:e00306-15. PMID: 25968644.
5. Trotter VV et al. (2023). "Large-scale genetic characterization of DvH." *Front Microbiol* 14:1095132. PMID: 37065130.
6. Pal C et al. (2014). "BacMet: antibacterial biocide and metal resistance genes database." *Nucleic Acids Res* 42:D617-D624. PMID: 24304895.

## Revision History
- **v2** (2026-02-22): Analysis complete. H1b (dose-dependent chloride confounding) rejected — zinc sulfate (0 mM Cl⁻) shows higher NaCl overlap than most chloride metals. The ~40% overlap reflects shared stress biology, not counter ion contamination. H1c result: core enrichment is robust after correction (essential metals show STRONGER enrichment). Dropped NB06 (anion signatures) and NB07 (summary) as the main findings are clear from NB01-05.
- **v1** (2026-02-22): Initial plan

## Authors
- Paramvir Dehal (https://orcid.org/0000-0002-3495-1240), Lawrence Berkeley National Laboratory, US Department of Energy
