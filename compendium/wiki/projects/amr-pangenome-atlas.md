# Amr Pangenome Atlas

This project catalogs antibiotic and metal-resistance genes across 14,723 bacterial species using uniform annotation (Bakta + AMRFinderPlus), revealing that resistance genes are universally depleted from bacterial core genomes (30.3% core vs 46.8% baseline) and concentrated in mobile, accessory elements. Most importantly, the study demonstrates a fundamental ecological split: clinical species harbor 2.7× more resistance than environmental species, but their resistance is predominantly acquired and mobile, whereas environmental species rely on intrinsic, chromosomally-conserved defenses—establishing the dichotomy between intrinsic and acquired resistance as a pan-bacterial pattern shaped by selective pressure and niche.

## Key findings

- AMR counts are inflated for human-associated species because genome databases over-represent clinical pathogens, a sampling bias that confounds clinical-versus-environmental comparisons. *(confidence: medium)*
- The keyword-based mechanism classification leaves 22% of AMR hits as Other/Unclassified, and AMRFinderPlus scope includes stress-response genes so the 83K hits are not all classical antibiotic resistance. *(confidence: medium)*
- This analysis quantifies the intrinsic-acquired AMR conservation dichotomy for the first time across 14,723 species simultaneously, establishing core-genome depletion (OR=0.49) as a universal bacterial pattern. *(confidence: medium)*
- AMR clusters are functionally enriched for COG V Defense mechanisms (7.05x) and COG P Inorganic ion transport (1.93x), reflecting genuine defense systems plus large mercury and arsenic resistance gene families. *(confidence: high)*
- AMR gene density is strongly phylogenetically structured, with Klebsiella leading at 206 AMR clusters per species and Gammaproteobacteria carrying 45% of all AMR clusters. *(confidence: high)*
- AMR genes are markedly depleted from the bacterial core genome, with only 30.3% core versus a 46.8% pangenome baseline (OR=0.49) and a 2.2x enrichment in the auxiliary genome. *(confidence: high)*
- AMR mechanisms split into a conservation dichotomy, with intrinsic beta-lactamases 54.9% core while regulatory genes (6.5% core) and known mobile elements such as blaTEM, tet(C), and ant(2'')-Ia are 0% core. *(confidence: high)*
- Across 178 AMR genes in 37 Fitness Browser organisms, AMR genes impose slightly less fitness cost than the non-AMR baseline (median fitness -0.007 vs -0.012) in standard lab conditions. *(confidence: medium)*
- AlphaEarth environmental-diversity embeddings strongly predict AMR count (Spearman rho=0.466), indicating that broader niche breadth enables accumulation of less-core resistance genes. *(confidence: high)*
- Heavy-metal resistance is a major component of the AMR census, with mercury resistance genes alone accounting for ~15,000 hits (18% of all AMR annotations) and arsenic resistance adding ~6,000 more. *(confidence: high)*
- Human/clinical species carry 2.7x more AMR (10.6 clusters per species) than environmental species, and their AMR is less core (30.8%) than soil (58.1%) or plant (63.1%) AMR. *(confidence: high)*
- The depletion of AMR genes from the core genome is consistent across species, with 63.7% of 4,252 tested species showing AMR less core than their own pangenome baseline. *(confidence: high)*
- Integrating NMDC/MGnify metagenomes could test whether the accessory AMR genes seen in isolate genomes are also prevalent in environmental community DNA. *(confidence: medium)*
- Replacing keyword-based mechanism classification with systematic CARD Antibiotic Resistance Ontology mapping could reduce the 22% Other/Unclassified category and provide ontology-based AMR classification. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/amr_pangenome_atlas/REPORT.md)
