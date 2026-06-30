# Microbeatlas Metal Ecology

This project asked whether bacterial tolerance to multiple metal types shapes their ecological range across global environments. We integrated pangenome metal resistance annotations across 6,789 bacterial species with a global 16S survey of 464,000 samples and found that genera tolerating a diversity of metals—not just accumulating more metal resistance genes overall—are ecological generalists found across many environments, an association that persists even after controlling for phylogeny, genome size, and species richness. This is the first global-scale evidence linking the breadth of metal tolerance repertoires to microbial biogeographic range, suggesting that multi-metal stress environments select for metabolically versatile bacteria.

## Key findings

- Niche breadth here is a sequencing-effort proxy inferred from OTU detection, not confirmed ecological range, and genus-level aggregation can make a genus appear broad-niched because different species occupy different habitats rather than any single organism being a true generalist. *(confidence: high)*
- The archaeal PGLS is severely underpowered (n = 48 genera, 11% power at α = 0.05) and its non-significant positive result (β = +0.0145, p = 0.467) should not be interpreted as evidence against the association in archaea. *(confidence: high)*
- The cross-sectional observational design means the direction of the association cannot be established; it is equally consistent with metal diversity facilitating ecological generalism and with ecological generalism enabling metal gene acquisition. *(confidence: high)*
- Nitrification serves as a metabolic positive control with near-maximal phylogenetic signal (λ = 0.94 bacteria, 1.00 archaea), contrasting sharply with the intermediate signal of metal AMR and strengthening confidence in the analytical pipeline. *(confidence: high)*
- The positive association is consistent with a metabolic versatility hypothesis, in which broad metal tolerance is a proxy for overall environmental tolerance because multi-metal-stress environments are also chemically complex in other dimensions. *(confidence: medium)*
- This is the first analysis linking genus-level metal type diversity from pangenome AMR annotations across 6,789 species to global ecological niche breadth from a 464K-sample 16S atlas with phylogenetic control via PGLS. *(confidence: medium)*
- Across 606 bacterial genera, the number of distinct metal types resisted per genus is the only metal AMR predictor of ecological niche breadth that survives phylogenetic correction and Bonferroni correction (PGLS β = +0.021, p = 1.5×10⁻⁴). *(confidence: high)*
- Bacterial ecological niche breadth (Levins' B_std) is strongly phylogenetically conserved (Pagel's λ = 0.787), and habitat range is even more conserved (λ = 0.909). *(confidence: high)*
- In a three-covariate PGLS, metal type diversity remains independently significant (β = +0.022, p = 3.5×10⁻⁴) after simultaneously controlling for species richness and genome size, neither of which fully explains the association. *(confidence: high)*
- In the ENIGMA ORFRC field dataset (PRJNA1084851), contamination-plume wells FW215/FW216 host communities with higher community-weighted mean metal-type diversity, which increases with time after carbon amendment (Spearman ρ = +0.383, p < 0.0001). *(confidence: medium)*
- Independent validation in 1,624 BERDL groundwater samples confirms that genera with broader metal-type resistance repertoires are significantly more prevalent in groundwater (Spearman ρ = +0.112, p = 0.0019; Mann-Whitney p = 0.007). *(confidence: medium)*
- It is the breadth of the metal resistance repertoire, not its depth, that is associated with ecological versatility: total AMR gene cluster count and core AMR fraction do not predict niche breadth in PGLS models. *(confidence: high)*
- Metal AMR traits show intermediate, significantly non-zero phylogenetic signal (Pagel's λ = 0.26–0.44), with core resistance fraction more conserved than metal type diversity than cluster count, consistent with vertically inherited core resistance plus HGT-driven accessory expansion. *(confidence: high)*
- The metal type diversity effect on niche breadth remains significant after controlling for genome size (β = +0.022, p = 3.6×10⁻⁴), and is not an artefact of total genomic complexity. *(confidence: high)*
- A shortlist of eight high-priority broad-niche, multi-metal-resistant OTUs (e.g., Klebsiella, Enterococcus, Citrobacter, Pseudomonas) provides falsifiable predictions for controlled microcosm metal-stress experiments to test whether resistant taxa increase under metal stress. *(confidence: medium)*
- Estimating genus-level pangenome openness (accessory genome proportion) and testing it as a predictor of niche breadth could reveal whether a broad accessory genome is the underlying driver of both metal type diversity and ecological range. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Metal Resistance](../topics/metal-resistance.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Heather MacGregor](../authors/heather-macgregor.md)

[Open the full report →](../../../projects/microbeatlas_metal_ecology/REPORT.md)
