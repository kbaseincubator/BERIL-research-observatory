# References — metagenomic_environment_prediction

## Primary data sources

- **Salazar G, et al.** SPIRE: a Searchable, Planetary-scale mIcrobiome REsource. *Nucleic Acids Research* (2023). Database: [spire.embl.de](https://spire.embl.de)
  - Used for: SPIRE MAG coordinates, genome metadata, eggnog KO annotations (download endpoints)

- **Arkin AP, et al.** (2018). KBase: The United States Department of Energy Systems Biology Knowledgebase. *Nature Biotechnology*, 36, 566–569. DOI: 10.1038/nbt.4163
  - Used for: `kescience_mgnify` Spark tables (MGnify genome and gene eggnog data)

- **Tóth G, et al.** (2025). Global soil toxic metal exceedance probabilities from LUCAS soil survey. *Science*.
  - Used for: CSU metal mobility fractions (PF1_As/Cd/Cr/Cu/Hg/Pb) as environmental targets

- **Poggio L, et al.** (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. *SOIL*, 7, 217–240. DOI: 10.5194/soil-7-217-2021
  - Used for: SoilGrids pH, organic carbon density, clay content (SPIRE M2/M3 features)

## Metal resistance genes in soil metagenomes

- **Liu Y, et al.** (2024). Organic fertilization co-selects genetically linked antibiotic and metal(loid) resistance genes in global soil microbiome. *Nature Communications*, 15, 5095. DOI: 10.1038/s41467-024-49165-5
  - Used for: community-level co-selection context; metal resistance gene patterns in global soil

- **Liang H, et al.** (2024). Vertical migration of bacteria bearing antibiotic resistance genes and heavy metal resistance genes through a soil profile as affected by manure. *Biology and Fertility of Soils*. DOI: 10.1007/s00374-024-01878-x
  - Used for: soil physicochemistry as the dominant driver of metal resistance gene distribution over genome content alone

- **Wang L, et al.** (2025). Metagenomic insights into the characteristics and co-migration of antibiotic resistome and metal(loid) resistance genes in urban landfill soil and groundwater. *Environmental Research*. DOI: 10.1016/j.envres.2025.122285
  - Used for: metal resistance gene co-migration context in soil-groundwater systems

## Parent project

- **comprehensive_metal_ecology** (P1): Genus-level PGLS of metal-gene density against niche breadth (β=−0.021) — the signal this project attempts to extend to MAG level. See `projects/comprehensive_metal_ecology/REPORT.md`.
