# Dark Matter Genes: The Unknown 37%

## Research Question

What are the gene clusters with COG category "S" (Function unknown) actually doing?

The COG analysis revealed that novel genes are enriched in S-category (+1.64% enrichment, 69% consistency across species). These are genuinely unknown proteins - the "dark matter" of bacterial genomes. This project investigates:

1. **Scale**: How many gene clusters have unknown function across the pangenome?
2. **Distribution**: Are S-category genes uniformly distributed, or do some species/phyla have more?
3. **Co-occurrence**: Do S-genes appear alongside defense (V) or mobile (L) elements?
4. **Families**: Can we identify recurring "dark matter families" that span multiple species?

## Hypotheses

**H1**: S-category genes are enriched in singletons because they represent recent, lineage-specific innovations that haven't been characterized yet.

**H2**: S-category genes will co-occur with L (mobile) and V (defense) categories, suggesting they may be part of mobile genetic elements or novel defense systems.

**H3**: Some "unknown" proteins will form cross-species families, suggesting they're not actually novel - just understudied.

## Methods

- Query BERDL for COG category distributions
- Analyze S-category enrichment by core/auxiliary/singleton status
- Look for composite COG categories involving S (e.g., "SV", "LS")
- Examine phylum-specific patterns
- Identify the most common S-category gene clusters

## Data Sources

- `kbase_ke_pangenome.gene_cluster` - 132M gene clusters
- `kbase_ke_pangenome.eggnog_mapper_annotations` - 93M functional annotations
- `kbase_ke_pangenome.gene_genecluster_junction` - Gene-to-cluster links

## Preliminary Findings (from COG Analysis)

From the multi-species COG analysis (32 species, 9 phyla):

| Metric | Value |
|--------|-------|
| S enrichment in novel genes | +1.64% |
| Consistency across species | 69% (22/32 species) |
| Rank among enriched categories | 3rd (after L and V) |

The pattern L > V > S (mobile elements > defense > unknown) suggests a biological connection:
- Mobile elements carry defense cargo
- Defense systems evolve rapidly under phage pressure
- The most divergent defense components lose annotation → become "S"

See `INTERPRETATION.md` for extended analysis of what this pattern means.

## Project Structure

```
dark_matter_genes/
├── README.md                    # This file
├── INTERPRETATION.md            # Extended analysis and hypotheses
├── notebooks/
│   └── 01_dark_matter_exploration.ipynb  # Main analysis notebook
├── data/                        # Generated data (gitignored)
└── figures/                     # Generated figures
```

## Status

**In Progress** - Notebook created, awaiting execution on Spark-connected environment
