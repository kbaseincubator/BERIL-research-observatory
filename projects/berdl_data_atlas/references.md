# References

This is a meta-atlas project: the references are canonical citations for the
**BERDL data systems** being catalogued and for the cross-tenant join paths
sample-validated in the atlas (UC1). Not biological-hypothesis references.

## Primary BERDL data-source citations

### Pangenome / genome reference
- **Arkin, A.P. et al. (2018).** "KBase: The United States Department of Energy Systems Biology Knowledgebase." *Nature Biotechnology* 36, 566–569. PMID: 29979655. — KBase platform; underlies `kbase_ke_pangenome` and all `kbase_*` collections.
- **Schmidt, T.S.B. et al. (2023).** "SPIRE: a Searchable, Planetary-scale Index of Metagenomic data and Reference genome assemblies." *NAR* 52, D777–D783. PMID: 37994744. — SPIRE MAG catalog (`refdata_spire`).
- **GTDB:** Parks, D.H. et al. (2022). "GTDB: an ongoing census of bacterial and archaeal diversity through a phylogenetically consistent, rank normalized and complete genome-based taxonomy." *NAR* 50, D785–D794. PMID: 34520557. — GTDB taxonomy used in `kbase_ke_pangenome.gtdb_*` and refdata.

### Phenotype / fitness
- **Price, M.N. et al. (2018).** "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557, 503–509. PMID: 29769710. — FitnessBrowser (`kescience_fitnessbrowser`) primary citation. Used by 35 / 66 BERIL projects.
- **Söhngen, C. et al. (2014).** "BacDive — The Bacterial Diversity Metadatabase." *NAR* 42, D592–D599. PMID: 24214959. — BacDive (`kescience_bacdive`).

### Protein reference / structure
- **UniProt Consortium (2023).** "UniProt: the Universal Protein Knowledgebase in 2023." *NAR* 51, D523–D531. PMID: 36408920. — `refdata_uniprot`.
- **Jumper, J. et al. (2021).** "Highly accurate protein structure prediction with AlphaFold." *Nature* 596, 583–589. PMID: 34265844. — AlphaFold method (`kescience_alphafold`).
- **Tunyasuvunakool, K. et al. (2021).** "Highly accurate protein structure prediction for the human proteome." *Nature* 596, 590–596. PMID: 34293799. — AlphaFold proteome-scale release.
- **Berman, H.M. et al. (2000).** "The Protein Data Bank." *NAR* 28, 235–242. PMID: 10592235. — PDB (`refdata_pdb`, `kescience_pdb`).

### Environmental / multi-omics
- **Eloe-Fadrosh, E.A. et al. (2022).** "The National Microbiome Data Collaborative Data Portal: an integrated multi-omics microbiome data resource." *NAR* 50, D828–D836. PMID: 34850110. — NMDC (`nmdc_metadata`, `nmdc_arkin`).
- **Hurwitz, B.L. et al. (2020).** "Planet Microbe: a platform for marine microbiology to discover and analyze interconnected 'omics and environmental data." *NAR* 49, D792–D802. PMID: 33010169. — Planet Microbe (`planetmicrobe_planetmicrobe`).
- **Mouw, K. et al.** USGS Produced Waters Database. — `usgs_produced_waters`.

### Phage / viral catalogs
- **Camargo, A.P. et al. (2024).** "IMG/VR v4: an expanded database of uncultivated virus genomes." *NAR* 52, D741–D747. PMID: 37855702. — `refdata_jgi_virus.imgvr_*`.
- **DOE BRaVE Phage Foundry program** — program-internal documentation for the per-host genome browsers (`phagefoundry_*`).

### Biochemistry / reactions
- **Henry, C.S. et al. (2010).** "High-throughput generation, optimization and analysis of genome-scale metabolic models." *Nature Biotechnology* 28, 977–982. PMID: 20802497. — ModelSEED (`kbase_msd_biochemistry`).
- **Bansal, P. et al. (2022).** "Rhea, the reaction knowledgebase in 2022." *NAR* 50, D693–D700. PMID: 34755880. — Rhea (`nmdc_arkin.rhea_*`).

### Literature
- **PaperBLAST:** Price, M.N. and Arkin, A.P. (2017). "PaperBLAST: Text Mining Papers for Information about Homologs." *mSystems* 2, e00039-17. PMID: 28845458. — `kescience_paperblast`.

### Cross-tenant validation precedent

The atlas's most-used realized bridge (`kbase × kescience`, 36 BERIL projects) operationalizes the FitnessBrowser-pangenome cross-reference of Price et al. (2018) at lakehouse scale. UC1's validated SwissProt-best-hit → AlphaFold path is the BERDL realization of the structure-function inference loop opened by Jumper et al. (2021).
