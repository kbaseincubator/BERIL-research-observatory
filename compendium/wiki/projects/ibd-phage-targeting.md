# Ibd Phage Targeting

This project set out to develop ecotype-stratified phage cocktails for Crohn's disease by (1) defining reproducible microbiome ecotypes from 8,489 metagenomic samples, (2) identifying ecotype-specific pathobiont targets, and (3) designing rationally optimized cocktails. The key finding: Crohn's patients distribute across four reproducible ecotypes with distinct pathobiont signatures, and cocktails designed at the cohort level will mismatch individual patients unless ecotype is known first. However, the two highest-priority targets (H. hathewayi and M. gnavus) have weak phage availability, necessitating hybrid approaches combining phages with non-phage alternatives for clinical translation.

## Key findings

- In pooled curatedMetagenomicData, healthy and Crohn's samples come from disjoint source studies, making a pooled case-vs-control mixed model structurally unidentifiable and forcing a within-substudy CD-vs-nonIBD design. *(confidence: high)*
- The E3-ecotype Tier-A target list rests on single-study evidence and should be treated as provisional until a cohort with sufficient E3 patients and both diagnosis groups becomes available. *(confidence: medium)*
- The two highest-priority Crohn's pathobiont targets, H. hathewayi and M. gnavus, have the weakest phage availability, creating a coverage gap for the most actionable species. *(confidence: high)*
- A single patient's ecotype can drift between E1 and E3 between visits, changing the optimal cocktail composition moderately (Jaccard 0.60) and motivating state-dependent cocktail re-design rather than a fixed prescription. *(confidence: medium)*
- No E1 Crohn's patient can be treated with a pure phage cocktail; only a hybrid combining phages with non-phage alternatives for the gap and temperate-only targets is feasible. *(confidence: medium)*
- Phage cocktails designed at the cohort level will mismatch individual IBD patients unless each patient's microbiome ecotype is determined first. *(confidence: high)*
- A confound-free within-substudy CD-vs-nonIBD meta-analysis across four IBD cohorts recovers the canonical Crohn's signature of pathobionts up and protective commensals down with strong sign concordance. *(confidence: high)*
- A greedy minimum-set-cover design over experimentally tested phage-strain susceptibility yields a 5-phage cocktail covering 94.7% of 188 E. coli strains in PhageFoundry. *(confidence: high)*
- Among the six actionable Tier-A pathobionts, only E. coli (the AIEC subset) carries the iron-siderophore and genotoxin biosynthetic gene-cluster signature, localizing iron-driven Crohn's biology to E. coli. *(confidence: high)*
- Clinical covariates separate healthy from IBD samples but cannot distinguish the transitional (E1) from severe (E3) IBD ecotypes, so metagenomics remains required for ecotype assignment. *(confidence: high)*
- The 23 UC Davis Crohn's patients distribute non-randomly across three ecotypes (none in the Prevotella E2), with active disease concentrated in the E1 and E3 ecotypes. *(confidence: high)*
- The Microviridae member Gokushovirus WZ-2015a is robustly depleted in Crohn's disease across multiple ecotypes, with the strongest signal in the transitional E1 ecotype. *(confidence: medium)*
- Tier-A pathobiont genomes are strongly enriched for iron-siderophore biosynthetic gene clusters, marking iron acquisition as a Crohn's pathobiont-defining genomic capability rather than only a cohort-level pathway signal. *(confidence: high)*
- Two independent clustering methods on 8,489 metagenomic samples converge on four reproducible IBD microbiome ecotypes (E0-E3) with K=4 selected by a cross-method ARI parsimony rule. *(confidence: high)*
- A taxonomy synonymy layer (NCBI taxid plus GTDB-version-aware rename table) is a reusable foundation that any multi-cohort microbiome project needs and that generalizes across studies. *(confidence: medium)*
- Querying external phage databases (INPHARED and IMG/VR) for gut-anaerobe phages could close the coverage gap for H. hathewayi, F. plautii, and M. gnavus and convert the hybrid framework into a pure-phage cocktail for some patients. *(confidence: medium)*

## Topics

- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Microbiome Engineering](../topics/microbiome-engineering.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)

## Data

- [Kbase Genomes](../data/kbase-genomes.md)
- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md)
- [Kbase Phenotype](../data/kbase-phenotype.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)
- [Phagefoundry](../data/phagefoundry.md)
- [Protect Genomedepot](../data/protect-genomedepot.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/ibd_phage_targeting/REPORT.md)
