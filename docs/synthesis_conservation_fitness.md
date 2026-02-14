# Synthesis: Gene Conservation, Fitness, and the Architecture of Bacterial Genomes

## Overview

Four interconnected projects explored the relationship between gene fitness (from RB-TnSeq mutagenesis across 48 bacteria) and gene conservation (from pangenome analysis of 27,690 microbial species). Together, they reveal a nuanced picture: the core genome is not a static set of housekeeping genes but an active, trade-off-laden functional architecture maintained by natural selection against the cost of carrying it.

## The Projects

| Project | Question | Key Finding |
|---------|----------|-------------|
| [conservation_vs_fitness](../projects/conservation_vs_fitness/) | Are essential genes more conserved? | Yes — 86% core vs 81% for non-essential (OR=1.56, 18/33 significant) |
| [fitness_effects_conservation](../projects/fitness_effects_conservation/) | Is there a continuous fitness-conservation gradient? | Yes — essential (82% core) → neutral (66%), a 16pp gradient across 194K genes |
| [module_conservation](../projects/module_conservation/) | Are co-regulated fitness modules in the core genome? | Yes — module genes are 86% core (OR=1.46, p=1.6e-87) |
| [core_gene_tradeoffs](../projects/core_gene_tradeoffs/) | Why are core genes more burdensome? | Trade-off genes (both sick + beneficial) are 1.29x more likely core |

## The Central Narrative

### 1. More important genes are more conserved — but modestly

Across the full spectrum from essential genes (no viable transposon mutants) to always-neutral genes (no fitness effect in any condition), there is a clear gradient: more functionally important genes are more likely to be in the core genome (present in ≥95% of a species' strains).

| Fitness category | % Core |
|-----------------|-------:|
| Essential (no viable mutants) | 82% |
| Often sick (>10% of experiments) | 78% |
| Sometimes sick | 72% |
| Always neutral | 66% |

This gradient holds across 43 diverse bacteria. But the effect is modest — even "always neutral" genes are 66% core. Most genes in well-characterized bacteria are core regardless of their fitness importance.

### 2. The core genome is functionally active, not just conserved

A naive model might predict that core genes are "boring" housekeeping genes — always needed, never costly, functionally inert under lab conditions. The data shows the opposite:

- **Core genes are MORE likely to be burdens** (24.4% show positive fitness when deleted vs 19.9% for auxiliary)
- **Core genes have MORE condition-specific effects** (OR=1.78 for specific phenotype enrichment)
- **Core genes are MORE likely to be trade-off genes** — important in some conditions, costly in others (OR=1.29)

The core genome is the most functionally active part of the genome. Core genes participate in more pathways, interact with more conditions, and show both the strongest negative AND positive fitness effects.

### 3. The lab reveals cost; the pangenome reveals selection

This leads to the key insight: **lab conditions are an impoverished proxy for natural environments**.

A gene that shows positive fitness when deleted in LB (a "burden" in the lab) may be essential for survival in soil, biofilm, host tissue, or any of the thousands of conditions bacteria face in nature. The fact that such genes are conserved across ALL strains of a species — despite being costly — is evidence for strong purifying selection in natural environments that the lab doesn't capture.

We quantified this with a selection-signature matrix:

| | Conserved (core) | Dispensable (non-core) |
|---|---:|---:|
| **Costly in lab** | 28,017 | 5,526 |
| **Neutral in lab** | 86,761 | 21,886 |

The 28,017 **costly + conserved** genes are the strongest evidence for natural selection maintaining genes against their metabolic cost. The 5,526 **costly + dispensable** genes are candidates for ongoing gene loss — burdensome AND not universally conserved.

### 4. The burden paradox is function-specific

Not all functional categories contribute equally to the core-burden paradox:

**Core genes disproportionately burdensome in:**
- RNA Metabolism (+12.9pp vs non-core) — transcription machinery has condition-dependent costs
- Motility/Chemotaxis (+7.8pp) — flagella are energetically expensive, not always needed
- Protein Metabolism (+6.2pp) — ribosomal genes are costly in some conditions

**Paradox reversed in:**
- Cell Wall and Capsule (-14.1pp) — non-core cell wall genes are MORE burdensome, perhaps because they're recently acquired and poorly integrated

Motility is the clearest case study: flagellar genes are highly conserved (core), energetically expensive (burdensome when deleted in rich media), but essential for chemotaxis and colonization. The lab captures the cost; the pangenome captures the evolutionary importance.

### 5. Co-regulated gene modules are embedded in the core genome

ICA decomposition identified 1,116 co-regulated fitness modules across 32 organisms. These modules — groups of genes that respond coherently to experimental conditions — are enriched in core genes (86% core vs 81.5% baseline, OR=1.46, p=1.6e-87).

59% of modules are >90% core genes. The core genome is not just structurally conserved but functionally coherent at the module level — it contains coordinated response units, not just individual essential genes.

However, 48 modules are <50% core ("accessory modules"), representing co-regulated gene groups in the flexible genome. These may include horizontally transferred operons or niche-specific functional units.

### 6. Essential genes are the tip of the iceberg

Essential genes (no transposon insertions = lethal when deleted) are 82% core — the most conserved fitness category. But they represent only 18.5% of protein-coding genes. The essential-core genes are:

- 41.9% enzymes (vs 21.5% for non-essential)
- Enriched in Protein Metabolism, Cofactors/Vitamins, Cell Wall
- Only 13% hypothetical (vs 24.5% for non-essential)

The 1,965 strain-specific essential genes (essential but no pangenome match) are 44.7% hypothetical — prime targets for functional discovery. These may represent recently acquired essential functions or highly divergent variants of core genes.

## What We Didn't Find

- **Family breadth doesn't predict conservation**: Module families spanning more organisms don't have higher core fractions (rho=-0.01, p=0.91). The baseline core rate (~82%) creates a ceiling effect.
- **Accessory genes are NOT systematically burdensome**: The "streamlining" model predicts accessory genes should be costly to carry. Instead, accessory genes are LESS burdensome than core genes.
- **Condition-specific ≠ niche-specific**: Genes with strong condition-specific phenotypes are MORE likely core, not more accessory. Core genes simply have more detectable effects because they're in well-characterized pathways.

## Methods Summary

- **Link table**: DIAMOND blastp at ≥90% identity mapped 177,863 FB genes across 44 organisms to pangenome clusters
- **Essential gene definition**: Type=1 CDS with no entries in `genefitness` (upper bound on true essentiality)
- **Fitness profiles**: Per-gene summary statistics from 27M fitness measurements across ~7,500 experiments
- **Statistical tests**: Fisher's exact test with BH-FDR correction; Spearman correlations; paired Wilcoxon signed-rank
- **All analyses reproducible** from cached TSV files without Spark access (except initial data extraction)

## Data Scale

| Metric | Value |
|--------|-------|
| FB organisms | 48 (44 mapped, 33 in essential analysis) |
| Protein-coding genes | 194,216 |
| Gene-cluster links | 177,863 |
| Fitness measurements | 27,410,721 |
| Pangenome species | 27,690 |
| Pangenome clusters | 132.5M |
| ICA fitness modules | 1,116 across 32 organisms |
| Cross-organism module families | 156 |

## Open Questions

1. **The 5,526 costly + dispensable genes** — What are they? Mobile elements? Recently acquired genes on the way out? (HIGH priority, see [research ideas](research_ideas.md))
2. **Environmental context** — Do organisms from variable environments have more trade-off genes in their core? Connect to AlphaEarth embeddings.
3. **Cross-organism essential families** — Are there universally essential gene families across all 33 organisms?
4. **The 48 accessory modules** — What co-regulated functions live in the flexible genome?

## References

- Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509. PMID: 29769716
- Rosconi F et al. (2022). "A bacterial pan-genome makes gene essentiality strain-dependent and evolvable." *Nat Microbiol* 7:1580-1592. PMID: 36097170
- Hutchison CA 3rd et al. (2016). "Design and synthesis of a minimal bacterial genome." *Science* 351:aad6253. PMID: 27013737
- Goodall ECA et al. (2018). "The Essential Genome of Escherichia coli K-12." *mBio* 9:e02096-17. PMID: 29463657
