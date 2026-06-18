# Enigma Sso Asv Ecology

This project mapped the spatial structure of microbial communities across a 3×3 grid of sediment and groundwater wells at the Savannah River Site to infer the subsurface biogeochemistry governing a contamination plume. By integrating 16S community composition with functional inference of metabolic guilds, the team discovered that a contamination plume entering from the northeast dictates the entire spatial architecture of the subsurface—from the plume entry point (marked by iron oxidizers and nitrifiers) to the mixing zone (denitrification hotspot) to the anaerobic core—and that bacterial community similarity alone can reveal both the plume's flow path and the underlying redox ladder with remarkable precision at meter scale.

## Key findings

- All environmental inferences rest on community composition alone because SSO geochemistry has not been loaded into BERDL, so the plume model awaits geochemical confirmation. *(confidence: high)*
- Genus-level functional annotation covers only 21% of total reads, so process abundance estimates are lower bounds and the unclassified majority of reads could harbor additional functional capacity. *(confidence: high)*
- Only 5 of 9 wells have groundwater ASV data, missing the critical M5 denitrification hotspot and U3 plume entry, so those hotspot interpretations rest on sediment data alone. *(confidence: high)*
- All findings converge on a single model in which SSO community spatial structure is governed by a contamination plume entering from the northeast and flowing southwest through the saturated zone. *(confidence: medium)*
- The plume flow path is visible purely in Bray-Curtis community similarity, demonstrating that 16S community structure can map subsurface hydrology at meter scale. *(confidence: medium)*
- Genus-level functional inference maps biogeochemical processes onto the 3x3 grid in a spatial sequence that recapitulates the thermodynamic redox ladder expected along a contamination plume. *(confidence: medium)*
- Groundwater communities sampled 9 days apart show remarkable short-term stability, with sampling date explaining only 0.8% of variance versus 49.9% for well identity. *(confidence: high)*
- Groundwater is enriched in plume-adapted denitrifiers and iron oxidizers while sediment-attached anaerobes are depleted, indicating distinct planktonic versus attached communities rather than simple detachment. *(confidence: medium)*
- Guild co-occurrence analysis reveals a tight nitrifier-iron-oxidizer coupling and a denitrifier-syntroph mutual exclusion, providing a metabolic network topology that overlays the spatial redox gradient. *(confidence: medium)*
- PERMANOVA shows hydrogeological depth zone explains 27.5% of sediment community variance (p=0.0001) while well identity is not significant, so vertical zonation dominates over horizontal position. *(confidence: high)*
- Sediment microbial communities across the 9 SSO wells show significant distance-decay of similarity at meter scale, with community turnover aligned to the east-west axis rather than the hillslope. *(confidence: high)*
- Ten of twelve dominant phyla show significant depth associations that split into shallow-oxic-enriched and deep-anoxic-enriched groups, mirroring the subsurface redox gradient. *(confidence: high)*
- The central well M5 hosts the highest denitrification potential (7.7% Rhodanobacter), consistent with a plume mixing zone where nitrate-rich contaminated groundwater meets native organic carbon. *(confidence: medium)*
- Wells U3, M6, and L7 form a diagonal community-similarity corridor from the northeast to the southwest that aligns with the expected contamination-plume flow path from the uphill Area 3 source. *(confidence: high)*
- Loading the 221 registered SSO geochemistry samples into CORAL would enable direct correlation of community composition with measured environmental parameters and validate or refute the plume model. *(confidence: medium)*
- Shotgun metagenomics at the same spatial resolution would confirm the taxonomy-based functional inferences and capture the majority of reads lacking genus-level classification. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Subsurface Genomics](../topics/subsurface-genomics.md)

## Data

- [Enigma Coral](../data/enigma-coral.md)

## Authors

- [Adam P. Arkin](../authors/0000-0002-4999-2931.md)

[Open the full report →](../../../projects/enigma_sso_asv_ecology/REPORT.md)
