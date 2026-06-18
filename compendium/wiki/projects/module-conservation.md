# Module Conservation

This project investigated whether co-regulated fitness modules—functionally coherent gene sets identified through independent component analysis of transposon insertion fitness data—preferentially locate within conserved core genome regions across 32 bacterial species. The key finding: fitness modules are significantly enriched in core genes (86% vs 81.5% baseline, OR=1.46, p=1.6e-87), confirming that co-regulated functional units cluster in the conserved genome rather than in lineage-specific accessory regions. However, the enrichment is modest in absolute terms because the baseline core rate is already very high, leaving limited room for a gradient.

## Key findings

- Because ICA requires fitness data, essential genes (which lack transposon insertions) are absent from all modules, so the analysis only covers the non-essential portion of the genome. *(confidence: high)*
- The 90% and 50% cutoffs used to classify modules as core, mixed, or accessory are convenient but not biologically motivated. *(confidence: medium)*
- The interpretation that accessory module families represent horizontally transferred functional units or niche-specific operons is speculative and not directly supported by the data. *(confidence: low)*
- The observed core enrichment is modest because the baseline core rate is already ~81.5%, imposing a ceiling effect that limits the maximum observable enrichment. *(confidence: high)*
- Three module organisms (Cola, Kang, SB2B) lack pangenome links because their species had too few genomes in GTDB for pangenome construction, restricting the analysis to a 29/32 organism subset. *(confidence: medium)*
- Conservation is a property of individual genes rather than of the cross-organism scope of their regulatory module. *(confidence: medium)*
- The core enrichment of fitness modules is statistically significant (OR=1.46, p=1.6e-87), confirming co-regulated functional units preferentially reside in the conserved genome. *(confidence: high)*
- The finding that 59% of fitness modules are >90% core extends the pangenomic concept of 'core' from individual genes to functionally coherent regulatory units. *(confidence: medium)*
- 38 module families have <50% core genes, representing co-regulated accessory gene modules conserved across organisms. *(confidence: medium)*
- ICA fitness module genes are enriched in the conserved core genome, at 86.0% core versus 81.5% for all genes (a +4.5 percentage-point shift). *(confidence: high)*
- Module families spanning more organisms do not have higher core fractions (Spearman rho=-0.01, p=0.914), a null result for the breadth-conservation hypothesis. *(confidence: high)*
- No essential genes appear in any ICA module, confirming that the modules only capture non-essential genes with measurable fitness variation from transposon insertions. *(confidence: high)*
- Of 974 modules with at least three mapped genes, 577 (59%) are core modules (>90% core genes), 349 (36%) are mixed, and 48 (5%) are accessory. *(confidence: high)*
- The median module is 93.4% core, indicating that most co-regulated fitness response units are embedded in the conserved genome. *(confidence: high)*
- A per-organism paired comparison of module versus baseline core fraction across the 29 organisms (e.g., paired Wilcoxon signed-rank test) would control for organism-level variation and provide a more robust enrichment test. *(confidence: medium)*
- Adding a chi-squared or Fisher's exact test on module versus non-module genes by core versus non-core would strengthen the central core-enrichment claim, which currently lacks a reported significance test in the notebook analysis. *(confidence: medium)*

## Topics

- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/module_conservation/REPORT.md)
