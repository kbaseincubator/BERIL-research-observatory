# Report: Core Gene Paradox -- Why Are Core Genes More Burdensome?

## Key Findings

### The Burden Paradox Is Function-Specific

Not all functional categories show the paradox. Core genes are disproportionately burdensome in Protein Metabolism (+6.2pp), Motility (+7.8pp), and RNA Metabolism (+12.9pp). But Cell Wall reverses: non-core cell wall genes are MORE burdensome (-14.1pp).

### Trade-Off Genes Are Enriched in Core

25,271 genes (17.8%) are true trade-off genes -- important (fit < -1) in some conditions, burdensome (fit > 1) in others. These are 1.29x more likely to be core (OR=1.29, p=1.2e-44). Core genes have more trade-offs because they participate in more pathways with condition-dependent costs and benefits.

### The Selection Signature Matrix

| | Conserved (core) | Dispensable (non-core) |
|---|---:|---:|
| **Costly (burden in lab)** | 28,017 | 5,526 |
| **Neutral (no burden)** | 86,761 | 21,886 |

- **Costly + Conserved** (28,017 genes): Natural selection maintains them despite lab-measured cost -- they're essential in natural environments not captured by lab experiments
- **Costly + Dispensable** (5,526 genes): Candidates for ongoing gene loss -- burdensome AND not universally conserved
- **Neutral + Conserved** (86,761): Classic housekeeping genes
- **Neutral + Dispensable** (21,886): Niche-specific genes

## Interpretation

The burden paradox resolves when we recognize that lab conditions are an impoverished proxy for nature. Core genes are more burdensome in the lab because they encode functions (motility, ribosomal components, RNA metabolism) that are energetically expensive but essential in natural environments. The 28,017 costly-but-conserved genes are the strongest evidence for purifying selection maintaining genes despite their metabolic cost. The function-specific pattern makes biological sense: flagella are expensive but essential for chemotaxis; ribosomal components are costly but required for rapid growth responses.

## Limitations

- Lab conditions capture only a fraction of the environmental conditions bacteria face in nature
- "Burden" (fit > 1) may reflect trade-offs rather than true dispensability
- The 90% identity threshold for DIAMOND matching may miss rapidly evolving genes
- Condition types in the FB are biased toward what's experimentally convenient, not what's ecologically relevant

## Supporting Evidence

| Type | Path | Description |
|------|------|-------------|
| Notebook | `notebooks/01_burden_anatomy.ipynb` | Full analysis (6 sections) |
| Figure | `figures/burden_by_function.png` | Burden excess by functional category |
| Figure | `figures/burden_by_condition.png` | Burden patterns by condition type |
| Figure | `figures/tradeoff_genes_conservation.png` | Trade-off gene conservation enrichment |
| Figure | `figures/specific_phenotype_conditions.png` | Specific phenotype conditions |
| Figure | `figures/motility_case_study.png` | Motility case study |
| Figure | `figures/selection_signature_matrix.png` | Selection signature matrix |

## Revision History

- **v1** (2026-02): Migrated from README.md
