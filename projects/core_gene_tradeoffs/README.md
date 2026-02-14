# Core Gene Paradox — Why Are Core Genes More Burdensome?

## Research Question

Why are core genome genes MORE likely to show positive fitness effects when deleted (burdensome) than accessory genes? What functions and conditions drive this, and what does it tell us about natural selection?

## Motivation

The `fitness_effects_conservation` project found that core genes are 1.3x more likely to be burdens than auxiliary genes (OR=0.77 for auxiliary vs core, p=5.5e-48) and that condition-specific fitness genes are more core (OR=1.78). This contradicts the "streamlining" model where accessory genes are metabolic burdens. This project dissects why.

**Key framing**: Lab conditions are an impoverished proxy for nature. A gene burdensome in LB may be essential in soil or biofilm. Genes that are simultaneously costly (lab) AND conserved (pangenome) are the strongest evidence for purifying selection — nature maintains them despite their cost.

## Key Findings

### The Burden Paradox Is Function-Specific

Not all functional categories show the paradox. Core genes are disproportionately burdensome in Protein Metabolism (+6.2pp), Motility (+7.8pp), and RNA Metabolism (+12.9pp). But Cell Wall reverses: non-core cell wall genes are MORE burdensome (-14.1pp).

### Trade-Off Genes Are Enriched in Core

25,271 genes (17.8%) are true trade-off genes — important (fit < -1) in some conditions, burdensome (fit > 1) in others. These are 1.29x more likely to be core (OR=1.29, p=1.2e-44). Core genes have more trade-offs because they participate in more pathways with condition-dependent costs and benefits.

### The Selection Signature Matrix

| | Conserved (core) | Dispensable (non-core) |
|---|---:|---:|
| **Costly (burden in lab)** | 28,017 | 5,526 |
| **Neutral (no burden)** | 86,761 | 21,886 |

- **Costly + Conserved** (28,017 genes): Natural selection maintains them despite lab-measured cost — they're essential in natural environments not captured by lab experiments
- **Costly + Dispensable** (5,526 genes): Candidates for ongoing gene loss — burdensome AND not universally conserved
- **Neutral + Conserved** (86,761): Classic housekeeping genes
- **Neutral + Dispensable** (21,886): Niche-specific genes

## Limitations

- Lab conditions capture only a fraction of the environmental conditions bacteria face in nature
- "Burden" (fit > 1) may reflect trade-offs rather than true dispensability
- The 90% identity threshold for DIAMOND matching may miss rapidly evolving genes
- Condition types in the FB are biased toward what's experimentally convenient, not what's ecologically relevant

## Project Structure

```
projects/core_gene_tradeoffs/
├── README.md
├── notebooks/
│   └── 01_burden_anatomy.ipynb   # Full analysis (6 sections)
└── figures/
    ├── burden_by_function.png
    ├── burden_by_condition.png
    ├── tradeoff_genes_conservation.png
    ├── specific_phenotype_conditions.png
    ├── motility_case_study.png
    └── selection_signature_matrix.png
```

## Reproduction

All local — no Spark needed. Requires data from `fitness_effects_conservation` and `conservation_vs_fitness` projects.

```bash
cd projects/core_gene_tradeoffs
jupyter nbconvert --execute notebooks/01_burden_anatomy.ipynb
```

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
