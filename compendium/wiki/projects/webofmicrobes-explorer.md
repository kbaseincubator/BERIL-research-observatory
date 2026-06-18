# Webofmicrobes Explorer

This project explored whether metabolites produced by soil and groundwater bacteria (tracked in the Web of Microbes exometabolomics database) could be linked to gene fitness data and pangenome context, testing the hypothesis that what organisms produce metabolically predicts which genes they require. The analysis demonstrated that cross-collection links are real and actionable—19 metabolites produced by Pseudomonas strains correspond directly to compounds tested in fitness experiments, and all WoM organism genera have pangenome representations available—but revealed that the 2018 WoM snapshot lacks consumption data, limiting tests of whether consumed metabolites predict gene essentiality.

## Key findings

- Despite E. coli Keio being one of the richest Fitness Browser organisms, the WoM snapshot holds only 12 observations for E. coli BW25113 focused narrowly on sulfur and cysteine metabolism. *(confidence: high)*
- Formula-only metabolite matches to ModelSEED are inherently ambiguous and provide candidate sets for manual curation rather than definitive compound identifications. *(confidence: high)*
- The 2018 WoM snapshot records no consumption (decrease) action for any organism, so it captures only what organisms produce and cannot test whether consumed metabolites predict gene essentiality. *(confidence: high)*
- Obtaining the current GNPS2 or Northen lab WoM dataset (including the de Raad et al. 2022 NLDM 110-organism panel) would resolve the no-consumption limitation and increase the organism count several-fold. *(confidence: medium)*
- The hypothesis that WoM provides actionable cross-collection links is partially supported, with real connections to Fitness Browser, ModelSEED, and the pangenome offset by the absence of consumption data and a small single-laboratory dataset. *(confidence: high)*
- Every WoM organism genus has corresponding pangenome species clades in BERDL, making gene-cluster, conservation, and functional-annotation context available for future genome-content versus metabolite-output analyses. *(confidence: medium)*
- For Pseudomonas FW300-N2E3, curated matching identified 19 metabolites the organism produces in WoM that the Fitness Browser also tests as carbon or nitrogen sources, of which 5 are de novo products and 14 are amplified metabolites. *(confidence: high)*
- Only 26.8% of identified WoM metabolites (69 compounds) have definitive 1:1 ModelSEED links by exact name match, while an additional 41.6% match by molecular formula alone at an average of 8.4 ModelSEED molecules per formula. *(confidence: high)*
- The 2018 Web of Microbes snapshot encodes metabolite observations with four distinct action semantics in which 'E' (emerged/de novo production) and 'I' (increased/amplification) are mutually exclusive across all 10,744 observations. *(confidence: high)*
- The 2018 WoM snapshot tracks 589 metabolites across 37 organisms in five ENIGMA-funded projects, but 332 (56.4%) of the metabolites remain unidentified with an "Unk_" prefix. *(confidence: high)*
- The fraction of metabolite changes representing de novo production versus amplification varies roughly 2-fold across ENIGMA isolates in R2A medium, defining a 15-32% "metabolic novelty rate" as a potential phenotype. *(confidence: medium)*
- Two WoM Pseudomonas ENIGMA groundwater isolates map directly to Fitness Browser strains (pseudo3_N2E3 and pseudo13_GW456_L13), each with over 5,000 genes and more than 100 fitness experiments, plus a same-strain E. coli and a genus-level Synechococcus match. *(confidence: high)*
- Testing whether organisms with higher de novo production ratios have more open pangenomes or more accessory genes is a promising next analysis linking metabolic novelty to genome content. *(confidence: medium)*
- The WoM-to-GapMind link is currently blocked by a naming-convention mismatch, and building a GapMind pathway-to-substrate/product metabolite lookup table would unblock pathway-level integration. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/webofmicrobes_explorer/REPORT.md)
