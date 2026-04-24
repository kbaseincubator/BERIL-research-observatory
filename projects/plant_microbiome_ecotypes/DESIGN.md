# Plant Microbiome Ecotypes — Compartment-Specific Functional Guilds and Their Genetic Architecture

## Research Question

What is the genomic basis for plant-microbe associations across different plant compartments (rhizosphere, root, leaf/phyllosphere, endophyte)? Can we classify plant-associated microbial genera into beneficial, neutral, pathogenic, and dual-nature cohorts with mechanistic hypotheses, and identify which plant-interaction functions are associated with horizontal gene transfer vs. stable vertical inheritance?

## Hypotheses

**H0_phylo (Phylogenetic Null)**: Functional differences between plant-associated and non-plant species are explained by phylogenetic distance alone. Tested with genus-level fixed effects across all hypotheses.

**H1 (Compartment Specificity)**: Different plant compartments harbor microbial communities with distinct functional profiles. Rhizosphere species are enriched in nutrient acquisition (phosphate solubilization, siderophores, nitrogen fixation), while phyllosphere species are enriched in stress resistance and carbon storage pathways.
- *Go/no-go*: Requires >=30 species per compartment after NB01 census. Falls back to broad plant-vs-non-plant contrast if not met.

**H2 (Cohort Genetic Architecture)**: Beneficial functions (PGP genes) are predominantly core genome (>46.8% baseline), while pathogenicity determinants (T3SS, effectors) are more often accessory/singleton (<46.8% baseline).

**H3 (Metabolic Complementarity)**: Co-occurring plant-associated genera in NMDC soil communities show higher metabolic complementarity (GapMind pathway gap-filling) than random genus pairs, after controlling for phylogenetic distance.

**H4 (Mobility & Adaptation)**: Compartment-specific adaptation genes show higher singleton/accessory enrichment and more frequent co-occurrence with transposase/integrase gene clusters than matched-breadth housekeeping genes.

**H5 (Novel Interactions)**: Data-driven enrichment at the eggNOG OG level identifies gene families beyond known PGP/pathogenicity markers that distinguish plant-associated from non-plant species, surviving phylum-level fixed effects.

## Data Sources

| Source | Scale | Key Tables |
|--------|-------|------------|
| BERDL Pangenome | 293K genomes, 27.7K species | genome, gene_cluster, pangenome, gtdb_taxonomy |
| Bakta Annotations | 132M cluster reps | bakta_annotations, bakta_pfam_domains |
| eggNOG v6 | 93M annotations | eggnog_mapper_annotations |
| GapMind Pathways | 305M predictions | gapmind_pathways |
| GTDB Metadata | 293K genomes | gtdb_metadata (isolation_source) |
| NCBI Environment | 4.1M EAV rows | ncbi_env |
| BacDive | 97K strains | isolation, metabolite_utilization, sequence_info |
| NMDC | 6.4K samples | taxonomy_features, kraken_gold, study_table |

## Marker Gene Sets

### Beneficial / PGP
- **Nitrogen fixation**: nifH, nifD, nifK
- **ACC deaminase**: acdS
- **Phosphate solubilization**: pqqA-E
- **IAA biosynthesis**: ipdC
- **Hydrogen cyanide**: hcnA-C
- **Siderophores**: entA-F, pvdA/S
- **Acetoin/butanediol (ISR)**: budA-C, alsD/S
- **DAPG biocontrol**: phlA-D
- **Phenazine biocontrol**: phzA-G
- **Biofilm**: bcsA, pelA

### Pathogenic
- **T3SS**: hrcC/J/N/V, hrpA/B/L, sctC/J/N/V (+ Pfam PF00771, PF01313)
- **T4SS**: virB1-11, virD2/D4
- **T6SS**: tssB/C/E/F/G/H/K/M (+ Pfam PF05936/Hcp, PF05943/VgrG)
- **T2SS**: gspD/E/F
- **Coronatine toxin**: cmaA/B, cfa6/7
- **Cell wall degrading enzymes**: pelA-E, pehA (pectinase); celA/B (cellulase); Pfam PF00544, PF00150
- **Effectors/avirulence**: product keyword search

### Colonization
- **Flagella**: fliC, flgE, flhA
- **Chemotaxis**: cheA/W/R/Y
- **Quorum sensing**: luxI/R

## Methodological Safeguards

1. **Phylogenetic control**: Genus-level fixed effects in logistic regressions; shuffle environment labels within genera; report phylogeny vs. ecology variance decomposition
2. **NCBI sampling bias**: Use species-level prevalence (not genome counts); sensitivity analysis excluding top-3 most genome-rich species per compartment
3. **Multiple testing**: BH-FDR across all hypothesis-specific tests; pre-filter OGs to >= 5% prevalence
4. **Compartment classification quality**: Go/no-go checkpoint after NB01; report genus composition per compartment to detect bias
5. **Mobility proxy limitations**: Explicitly acknowledge indirect nature; compare multiple proxy signals (singleton enrichment, transposase co-occurrence, cross-species context variation)
6. **PGP-pathogen interaction caveats**: Dual-nature classification requires both PGP and pathogenicity markers in same species; co-occurrence patterns from NMDC metagenomes may reflect shared habitat rather than direct interaction

## Execution Deviations

The following planned safeguards were modified or deferred during execution:

1. **Phylogenetic control level**: Genus-level fixed effects were computationally intractable with 27K species. Phylum-level control (28 phyla) was used in NB03; family-level was attempted in NB08 but showed insufficient within-family variation. See REPORT.md Limitation #4.
2. **NB04 phylogenetic control**: Genus-level logistic regression in NB04 failed due to a code error. H1 compartment enrichments lack phylogenetic control beyond PERMANOVA.
3. **Three safeguards deferred**: (a) sensitivity excluding top-3 genome-rich species, (b) within-genus label shuffling, (c) phylogeny vs. ecology variance decomposition. These remain future work.
4. **NB08 added**: An adversarial revisions notebook (not in original plan) was added to address concerns about marker specificity, genome size confounding, negative controls, and HGT deep dive.

## Key Constraint

The GeNomad mobile element table is NOT in BERDL. Mobile element analysis uses proxies: singleton/accessory enrichment, transposase/integrase co-occurrence markers, and cross-species context variation (same OG core in species X but singleton in species Y).
