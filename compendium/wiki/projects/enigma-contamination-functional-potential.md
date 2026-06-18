# Enigma Contamination Functional Potential

This project tested whether metal contamination gradients in Oak Ridge subsurface communities produce detectable shifts in inferred stress-response functional potential at genus taxonomic resolution. Predeclared confirmatory tests found no significant monotonic relationship between contamination and defense-gene functional diversity, though exploratory coverage-adjusted models hinted at positive associations that weakened under multiple-testing correction. The null result is consistent with literature showing pronounced compositional turnover alongside modest functional-diversity changes, pointing to either functional redundancy across contamination gradients or contamination effects too fine-scale (species/strain/pathway level) for the present genus-level COG mapping.

## Key findings

- A majority of observed genera (862 of 1,392) were unmapped to the current pangenome bridge, and the COG-fraction proxies are coarse summaries rather than curated resistance pathways. *(confidence: high)*
- ENIGMA taxonomy table ddt_brick0000454 provides labels only through Genus, so true species-level bridge testing is not possible and genus-level mapping may mask strain-level adaptation. *(confidence: high)*
- The main interpretive risk is that readers may over-weight statistically significant exploratory adjusted-model estimates shown alongside the null confirmatory endpoint. *(confidence: medium)*
- Contamination gradients in this ENIGMA subset did not translate into a robust community-level shift in inferred stress functional potential at genus resolution, compatible with functionally redundant or too fine-scale taxonomic turnover. *(confidence: medium)*
- The null confirmatory result is consistent with prior Oak Ridge studies reporting pronounced contamination-linked compositional shifts alongside only modest functional-diversity decline. *(confidence: medium)*
- The project contributes a reproducible ENIGMA-to-BERDL functional inference workflow with independent strict-versus-relaxed feature construction, mapped-coverage diagnostics, and a species-proxy unique-clade sensitivity mode. *(confidence: high)*
- Exploratory coverage-adjusted models showed the strongest positive defense associations with contamination, but these attenuated under global multiple-testing control. *(confidence: medium)*
- Predeclared confirmatory Spearman tests of site defense score against the contamination index remained non-significant in both genus-level mapping modes (relaxed rho = 0.0587, q = 0.862; strict rho = 0.0682, q = 0.849). *(confidence: high)*
- Re-testing the confirmatory endpoint under four contamination-index variants, including uranium-only, left all results non-significant after FDR correction. *(confidence: high)*
- Restricting to a species-proxy mode of genera mapping to a single GTDB clade sharply reduced mean mapped abundance fraction (0.031 vs 0.343) and left the defense trend positive but non-significant. *(confidence: medium)*
- The composite contamination index built from eight metal columns via per-metal log1p z-scoring was broad but right-skewed across the 108 samples (median -0.271, max 3.836). *(confidence: high)*
- Within-fraction Spearman tests for defense were non-significant across both micron filters, indicating no robustly reproducible monotonic defense signal inside individual community-fraction strata. *(confidence: high)*
- Increasing taxonomic resolution via a species- or strain-level bridge from metagenomic or higher-resolution ENIGMA taxonomy could quantify inference gains over the genus and species-proxy modes. *(confidence: medium)*
- Replacing coarse COG-fraction proxies with curated metal-stress gene sets and pathway-level summaries could expose pathway-specific metal-response signals diluted by genus-level COG aggregation. *(confidence: medium)*

## Topics

- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Enigma Coral](../data/enigma-coral.md)
- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/enigma_contamination_functional_potential/REPORT.md)
