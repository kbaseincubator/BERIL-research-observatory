# Fitness Effects Conservation

This project mapped the relationship between gene fitness effects and pangenome conservation across 43 bacterial species, testing whether genes with stronger phenotypic impacts are more likely to be retained in the shared core genome. The central finding is a robust positive gradient: essential genes are 82% core while neutral genes are 66% core, suggesting that selection drives core gene maintenance by preferentially preserving genes with stronger fitness effects. Surprisingly, core genes are more likely to be both beneficial and detrimental when deleted—not because they're neutral "housekeeping" genes, but because they're embedded in critical metabolic pathways and thus sensitive to perturbation in multiple conditions.

## Key findings

- Although the 16pp gradient is statistically robust, conservation is only weakly predicted by fitness importance, and single-gene-knockout measurements do not capture epistatic interactions. *(confidence: high)*
- The Fitness Browser covers only 43 bacteria, primarily Proteobacteria, limiting generalizability, and singleton/novel genes may appear neutral due to poor transposon coverage rather than true neutrality. *(confidence: medium)*
- Core genes are the most functionally active part of the genome, having the largest fitness effects in both directions because they are embedded in critical pathways, while accessory genes are functionally quieter under lab conditions. *(confidence: medium)*
- The empirical fitness-conservation gradient provides support for selection as a major driver of core gene maintenance, consistent with stronger purifying selection on core than accessory genes. *(confidence: medium)*
- The relationship between fitness importance and conservation is a continuous gradient across the full essential-to-neutral spectrum, not a binary essential/non-essential distinction. *(confidence: high)*
- Core and auxiliary genes have distinct fitness distributions, with core genes showing heavier tails in both the negative (important) and positive (burdensome) directions. *(confidence: high)*
- Core genes are MORE likely than auxiliary genes to show positive (beneficial-when-deleted) fitness effects (24.4% vs 19.9% ever beneficial; OR=0.77 for auxiliary vs core), contradicting the expectation that accessory genes are the costly burden. *(confidence: high)*
- Ephemeral niche genes (neutral overall but critical in one condition) account for 4,450 genes (2.7%) and are more common in core genes (3.0%) than in auxiliary (1.7%) or singleton (1.6%) genes. *(confidence: medium)*
- Genes important in more experimental conditions are more likely to be core, with conservation rising from 66% (0 experiments) to 79% (20+ experiments) and a significant breadth-conservation correlation (Spearman rho=0.086, p=8.1e-230). *(confidence: high)*
- Genes with strong condition-specific phenotypes are more likely core (77.3% vs 70.3%; OR=1.78, p=1.8e-97), contradicting the naive expectation that condition-specific genes would be accessory. *(confidence: high)*
- Novel (singleton) genes show near-zero mean fitness, suggesting they are largely invisible to lab-based fitness assays rather than systematically detrimental. *(confidence: medium)*
- A per-organism breakdown of the fitness magnitude gradient would reveal whether the conservation pattern is universal or driven by a subset of organisms, complementing the cross-organism Spearman correlations. *(confidence: low)*
- Because lab conditions miss many ecological niches, measuring gene fitness under more diverse, ecologically relevant conditions would test whether the weak lab-measured gradient strengthens under natural selection pressures. *(confidence: low)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/fitness_effects_conservation/REPORT.md)
