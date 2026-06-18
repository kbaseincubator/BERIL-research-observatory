# Fw300 Metabolic Consistency

This project integrated exometabolomic, gene fitness, utilization, and computational pathway data to validate the metabolic phenotype of *Pseudomonas fluorescens* FW300-N2E3, a groundwater bacterium from the Oak Ridge Field Research Center. The key finding was that tryptophan represents a biologically meaningful production-vs-utilization discordance: the organism secretes tryptophan and can grow on it, yet the species cannot catabolize it, suggesting overflow metabolism that fuels cross-feeding with auxotrophic community members rather than self-utilization. Across testable metabolites, genome-scale exometabolomic predictions achieved 94% concordance with fitness and pathway databases, validating the consistency of modern metabolic measurements while revealing the ecological strategy underlying amino acid overflow in subsurface environments.

## Key findings

- Only 21 of 58 WoM metabolites could be tested against any other database and just 3 achieved four-way coverage, so the untested 64% may harbor additional discordances. *(confidence: high)*
- Only tryptophan reaches high confidence for a genuine production-vs-utilization discordance, since other BacDive discordances rest on small per-strain samples. *(confidence: high)*
- WoM exometabolomics was measured on rich R2A medium while Fitness Browser fitness used minimal single C/N-source media, so condition-dependent profiles mean some WoM metabolites may only be produced on rich media. *(confidence: medium)*
- Metabolite production and utilization measure fundamentally different capabilities, so a bacterium can secrete a metabolite for ecological purposes without being able to catabolize it for energy. *(confidence: high)*
- The fitness genes shared across all metabolite conditions are essential amino acid biosynthesis enzymes representing housekeeping fitness rather than substrate-specific catabolism. *(confidence: high)*
- This project is the first to systematically compare Web of Microbes exometabolomic profiles with Fitness Browser gene fitness data, despite both datasets coming from the same ENIGMA/Arkin Lab research program. *(confidence: medium)*
- Tryptophan secretion by FW300-N2E3, a prototroph that cannot re-assimilate it, is a hallmark of cross-feeding potential that could supply essential amino acids to auxotrophic community members. *(confidence: medium)*
- Across 21 produced metabolites with matching Fitness Browser experiments, FW300-N2E3 showed significant fitness effects for 601 unique genes and 4,764 total significant gene-condition hits. *(confidence: high)*
- Across the testable metabolites produced by Pseudomonas FW300-N2E3, exometabolomic, fitness, utilization, and pathway databases agree at a 0.94 mean concordance score, with no fully discordant metabolites. *(confidence: high)*
- All 13 GapMind-matched metabolites had complete predicted pathways for FW300-N2E3 and all showed growth in Fitness Browser experiments, validating GapMind pathway prediction accuracy for this organism. *(confidence: high)*
- FW300-N2E3 produces tryptophan and grows on it as a sole carbon source while no BacDive P. fluorescens strain can catabolize it, marking the strongest biologically meaningful production-vs-utilization discordance, consistent with overflow metabolism for cross-feeding or signaling. *(confidence: high)*
- Malate, arginine, and valine reached the gold standard of four-way consistency, being produced, grown on, species-utilized, and computationally complete across all four databases. *(confidence: high)*
- Metabolites produced by FW300-N2E3 are utilized at the species baseline rate, with a binomial test showing no significant difference between produced-metabolite utilization (3/7) and the P. fluorescens baseline (22/80). *(confidence: medium)*
- The tryptophan overflow finding could parameterize a community metabolic model predicting cross-feeding between FW300-N2E3 and known tryptophan auxotrophs in the Oak Ridge groundwater community. *(confidence: medium)*
- Using chemical identifiers such as InChIKey and CHEBI instead of name matching could expand the WoM-BacDive metabolite overlap beyond the current 8 metabolites. *(confidence: medium)*

## Topics

- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/fw300_metabolic_consistency/REPORT.md)
