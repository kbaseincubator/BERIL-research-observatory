# References — lanthanide_methylotrophy_atlas

## Primary biological references

- **Pol, A., Barends, T. R. M., Dietl, A., Khadem, A. F., Eygensteyn, J., Jetten, M. S. M., & Op den Camp, H. J. M. (2014).** Rare earth metals are essential for methanotrophic life in volcanic mudpots. *Environmental Microbiology*, 16(1), 255–264. — **Founding XoxF discovery paper.** Characterised the lanthanide-dependent methanol dehydrogenase in *Methylacidiphilum fumariolicum* SolV from a volcanic mudpot. Used by this project as the conceptual anchor for H1.
- **Skovran, E., & Martinez-Gomez, N. C. (2015).** Just add lanthanides. *Science*, 348(6237), 862–863. PMID: 25999489 — **"Lanthanide switch" review.** Established the model in which methylotrophs swap between Ca-dependent MxaF and REE-dependent XoxF based on lanthanide availability.
- **Cotruvo, J. A., Featherston, E. R., Mattocks, J. A., Ho, J. V., & Laremore, T. N. (2018).** Lanmodulin: a highly selective lanthanide-binding protein from a lanthanide-utilizing bacterium. *Journal of the American Chemical Society*, 140(44), 15056–15061. PMID: 30351909 — **Lanmodulin discovery paper.** Characterised the protein in *Methylobacterium extorquens* AM1; picomolar REE binding affinity. H3 derives the clade-restriction hypothesis from this paper.
- **Picone, N., & Op den Camp, H. J. M. (2019).** Role of rare earth elements in methanol oxidation. *Current Opinion in Chemical Biology*, 49, 39–44. PMID: 30308442 — **REE-dependent enzymes review.** Summarises the known XoxF distribution; explicitly notes that distribution beyond cultured methylotrophs is an open question that BERDL-scale data could address.
- **Chistoserdova, L. (2016).** Lanthanides: New life metals? *World Journal of Microbiology and Biotechnology*, 32(8), 138. PMID: 27357954 — **Methylotroph diversity review.** Hypothesised xoxF predominance over mxaF based on then-available genomes (~hundreds). This project tests the hypothesis at 293K-genome scale.

## Methodological references (BERDL infrastructure)

- **Parks, D. H., Chuvochina, M., Chaumeil, P. A., Rinke, C., Mussig, A. J., & Hugenholtz, P. (2022).** A complete domain-to-species taxonomy for Bacteria and Archaea. *Nature Biotechnology*, 38(9), 1079–1086. PMID: 32341564 — **GTDB r214 release.** Taxonomic backbone for all phylogenetic stratification (`gtdb_taxonomy_r214v1`).
- **Schwengers, O., Jelonek, L., Dieckmann, M. A., Beyvers, S., Blom, J., & Goesmann, A. (2021).** Bakta: rapid and standardized annotation of bacterial genomes via alignment-free sequence identification. *Microbial Genomics*, 7(11), 000685. PMID: 34739369 — **Bakta annotation pipeline.** Source of the `bakta_annotations.product` field; this project's NB01 calibration shows bakta product is the trustworthy source for Lanmodulin and XoxJ where eggNOG falls short.
- **Cantalapiedra, C. P., Hernández-Plaza, A., Letunic, I., Bork, P., & Huerta-Cepas, J. (2021).** eggNOG-mapper v2: functional annotation, orthology assignments, and domain prediction at the metagenomic scale. *Molecular Biology and Evolution*, 38(12), 5825–5829. PMID: 34597405 — **eggNOG-mapper.** Source of `KEGG_ko` calls (K00114 xoxF, K14028 mxaF, K06135-K06139 PQQ biosynthesis). Calibration finding: `Preferred_name='lanM'` produces 505 false positives in unrelated gut Bacillota — likely a propagated seed-ortholog mislabelling.
- **Arkin, A. P., Cottingham, R. W., Henry, C. S., Harris, N. L., Stevens, R. L., Maslov, S., et al. (2018).** KBase: The United States Department of Energy Systems Biology Knowledgebase. *Nature Biotechnology*, 36(7), 566–569. PMID: 29979655 — **KBase / BERDL platform.**

## Related BERDL projects

- **`projects/metal_fitness_atlas/`** (Dehal, complete) — Pan-bacterial metal fitness atlas covering Co, Ni, Cu, Zn, Al, Fe, W, Mo, Cr, U, Se, Mn, Hg, Cd. Explicitly identified REEs as the highest-priority untested critical mineral and proposed lanthanum/cerium chloride RB-TnSeq experiments. This project closes that gap on the genomic side.
- **`projects/amr_environmental_resistome/`** (Dehal, complete) — Methodology precedent for the bakta + ncbi_env + AlphaEarth + GTDB join pattern used in NB04.
- **`projects/metal_cross_resistance/`** (Dehal, complete) — Methodology precedent for cassette/multi-marker phylogenomic stratification.
