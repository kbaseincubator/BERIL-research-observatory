# Pgp Pangenome Ecology

This project characterized how plant-growth-promoting bacterial (PGPB) traits are distributed across 11,272 bacterial species, testing whether these traits spread through horizontal gene transfer, co-occur as functional modules, and show environmental selectivity. The most important finding is that the canonical PGPB phenotype is built around a tightly co-selected pqqC–acdS (phosphate solubilization and ethylene reduction) module that is predominantly core-genome inherited and strongly enriched in soil-associated species, not around nitrogen fixation, and that diazotrophs form a separate ecological guild entirely.

## Key findings

- Only 5.9% of species are classified soil/rhizosphere-dominant because ncbi_isolation_source is noisy and NCBI is biased toward clinical and host-associated isolates, so the reported soil enrichment effects are likely underestimates. *(confidence: high)*
- pqqD is an outlier to the vertical-inheritance pattern, with the lowest core fraction (55.5%) and highest singleton fraction (27.5%), suggesting it occasionally spreads horizontally as a standalone gene even though the functional pqqB–pqqC operon is predominantly core. *(confidence: medium)*
- The canonical PGPB phenotype is built around a tightly co-selected, rhizosphere-enriched, vertically inherited pqqC + acdS module that represents a stable specialized niche adaptation rather than a recently acquired multi-trait package. *(confidence: high)*
- The trp–ipdC association is not trp-specific but reflects general aromatic-amino-acid regulation, because the tyrosine negative control predicts ipdC at similar effect size (OR = 3.62), consistent with TyrR-mediated induction of ipdC by all three aromatic amino acids. *(confidence: medium)*
- Across 11,272 species carrying at least one PGP gene, plant growth-promoting traits co-occur non-randomly, with pqqC and acdS forming the strongest positive association (OR = 7.24) and an apparent coherent rhizosphere-effectiveness module. *(confidence: high)*
- All 13 PGP genes have significantly higher core fractions than the genome-wide baseline of 46.8%, with a mean accessory fraction of 29.7% versus 53.2% genome-wide, rejecting the hypothesis that PGP genes spread predominantly by horizontal gene transfer. *(confidence: high)*
- Contrary to naive expectation, nifH is significantly depleted in soil-classified species (OR = 0.60) because most database nitrogen fixers are aquatic/marine or host-associated rather than free-living soil diazotrophs. *(confidence: medium)*
- Nitrogen fixation (nifH) is negatively associated with the pqqC/acdS rhizosphere module, indicating that diazotrophs form an ecologically separate guild and that the classical PGPB suite is primarily a non-diazotrophic phenotype. *(confidence: high)*
- Pangenome openness (singleton fraction) correlates negatively with PGP gene richness (Spearman ρ = −0.195, p = 2.0e-97), so PGP-rich species have more closed pangenomes consistent with stable specialized niches rather than generalist HGT-driven acquisition. *(confidence: high)*
- Soil/rhizosphere environment strongly selects for acdS (7× more prevalent than other environments, OR = 7.02) and pqqC (OR = 2.90), with the acdS enrichment surviving phylum-level fixed effects and a strict rhizosphere-only sensitivity analysis. *(confidence: high)*
- The trp→ipdC positive coupling holds in non-soil species (OR = 3.56) but reverses within soil/rhizosphere species (OR = 0.30), possibly because soil PGPB obtain tryptophan from plant root exudates and relax selection on autonomous trp biosynthesis. *(confidence: low)*
- Tryptophan biosynthesis completeness significantly predicts ipdC presence (2.5% vs 0.9% in trp-incomplete species; Fisher OR = 2.81, logit OR = 2.81, 95% CI 1.97–4.01). *(confidence: medium)*
- Cross-referencing species carrying the pqqC + acdS + hcnC combination against commercially used inoculant strains could test whether this genomic signature predicts inoculant efficacy. *(confidence: medium)*
- Determining whether co-occurring pqqC and acdS are physically co-located on the same genomic island or operon would distinguish functional operon linkage from independent co-selection. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Priya Ranjan](../authors/0000-0002-0357-1939.md)

[Open the full report →](../../../projects/pgp_pangenome_ecology/REPORT.md)
