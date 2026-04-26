# References — Gene Function Ecological Agora

Literature cited in `RESEARCH_PLAN.md`, `DESIGN_NOTES.md`, and `REPORT.md` to date. New entries are added as later phases generate findings that warrant additional literature comparison.

## Phase 1A literature (current)

### Methodological anchor

- **Alm, E.J., Huang, K., Arkin, A.P. (2006).** "The evolution of two-component systems in bacteria reveals different strategies for niche adaptation." *PLoS Computational Biology* 2(11):e143. doi:10.1371/journal.pcbi.0020143. PMC1630713.

  *Project context*: original producer/consumer asymmetry on TCS histidine kinases across 207 prokaryotic genomes; the back-test target. Phase 1A confirmed the v2 plan's substrate hierarchy: Alm 2006's family-level paralog signal is not detectable at UniRef50 sequence-cluster resolution. Reproduction is pre-registered at Phase 2 (KO) and Phase 3 (Pfam architecture).

### HGT depth and ecology

- **Smillie, C.S., Smith, M.B., Friedman, J., Cordero, O.X., David, L.A., Alm, E.J. (2011).** "Ecology drives a global network of gene exchange connecting the human microbiome." *Nature* 480(7376):241–244. doi:10.1038/nature10571.

  *Project context*: documents within-phylum HGT in the gut microbiome at intense rates relative to cross-phylum events. Informs the Phase 1A interpretation of the cross-rank consumer-z trend (vertical at deep ranks, weakens at class) and the M1 revision (rank-stratified parent ranks for the consumer null).

- **Forsberg, K.J., Reyes, A., Wang, B., Selleck, E.M., Sommer, M.O.A., Dantas, G. (2012).** "The shared antibiotic resistome of soil bacteria and human pathogens." *Science* 337(6098):1107–1111. doi:10.1126/science.1220761.

  *Project context*: documents AMR HGT primarily within proteobacteria. Informs the Phase 1A finding that AMR consumer z is strongly clumped at parent-phylum (intra-phylum HGT masked by parent-phylum anchor) — motivates M1.

- **Soucy, S.M., Huang, J., Gogarten, J.P. (2015).** "Horizontal gene transfer: building the web of life." *Nature Reviews Genetics* 16(8):472–482. doi:10.1038/nrg3962.

  *Project context*: review of HGT depth distribution; foundational background for the rank-stratified atlas framing.

- **Hooper, S.D., Mavromatis, K., Kyrpides, N.C. (2007).** "Microbial co-habitation and lateral gene transfer: what transposases can tell us." *Genome Biology* 9(2):R45.

  *Project context*: HGT bias toward specific function classes; informs the Phase 2 regulatory-vs-metabolic test design.

- **Sichert, A., Cordero, O.X. (2021).** "Polysaccharide-Bacteria Interactions From the Lens of Evolutionary Ecology." *Frontiers in Microbiology* 12:705082. doi:10.3389/fmicb.2021.705082. PMC8531407.

  *Project context*: surfaced by `ADVERSARIAL_REVIEW_1.md` bio-claim verification (added in v2.3). Reviews polysaccharide degradation system distribution: most systems exhibit taxonomic clustering at the family level, but cross-phylum HGT is documented for specific substrate specializations. **Phase 1B Bacteroidota PUL hypothesis context**: PUL CAZymes are the canonical example of family-level clustering with documented cross-phylum HGT to gut Firmicutes (Smillie 2011, supported by Sichert & Cordero 2021). This is the literature anchor for the Phase 1B pre-registered hypothesis (Bacteroidota → Innovator-Exchange on PUL CAZymes).

- **Bonomo, R.A. (2017).** "β-Lactamases: a focus on current challenges." *Cold Spring Harbor Perspectives in Medicine* 7(1):a025239.

  *Project context*: documents cross-phylum spread of β-lactamase families (TEM, CTX-M, NDM, OXA-48). Phase 1B HIGH 1: these families anchor the known-HGT positive control set for the consumer null.

### Mechanism of family expansion

- **Treangen, T.J., Rocha, E.P.C. (2011).** "Horizontal transfer, not duplication, drives the expansion of protein families in prokaryotes." *PLoS Genetics* 7(1):e1001284. doi:10.1371/journal.pgen.1001284. PMC3029252.

  *Project context*: re-frames paralog-count signals as HGT signals at long timescales. Important for Phase 1B / 2 / 3 interpretation: high producer score in a clade may reflect HGT acquisition rather than de novo duplication.

### Atlas-style framing

- **Puigbò, P., Wolf, Y.I., Koonin, E.V. (2010).** "The tree and net components of prokaryote evolution." *Genome Biology and Evolution* 2:745–756. doi:10.1093/gbe/evq062. PMC2997564.

  *Project context*: foundational atlas-style framing for the bacterial tree-vs-network duality; conceptual backdrop for the Producer × Participation framing.

- **Popa, O., Hazkani-Covo, E., Landan, G., Martin, W., Dagan, T. (2011).** "Directed networks reveal genomic barriers and DNA repair bypasses to lateral gene transfer among prokaryotes." *Genome Research* 21(4):599–609.

  *Project context*: directed-network methodology for HGT inference; informs the directed clade-to-clade flow graph deliverable at Phase 4.

### Dosage constraint on housekeeping genes

- **Andersson, D.I. (2009).** "The biological cost of mutational antibiotic resistance: any practical conclusions?" *Current Opinion in Microbiology* 9(5):461–465.

  *Project context*: dosage cost on housekeeping genes; explains why ribosomal / tRNA-synthetase / RNAP core negative controls show negative producer z (M2 revision).

## Data substrate

- **Parks, D.H., Chuvochina, M., Rinke, C., Mussig, A.J., Chaumeil, P.A., Hugenholtz, P. (2022).** "GTDB: an ongoing census of bacterial and archaeal diversity through a phylogenetically consistent, rank normalized and complete genome-based taxonomy." *Nucleic Acids Research* 50(D1):D785–D794. doi:10.1093/nar/gkab776.

  *Project context*: GTDB r214 is the substrate. Used for taxonomy scaffold (`gtdb_taxonomy_r214v1`), species clade definition (`gtdb_species_clade`), and quality (`gtdb_metadata`).

- **Jones, P., Binns, D., Chang, H.Y., et al. (2014).** "InterProScan 5: genome-scale protein function classification." *Bioinformatics* 30(9):1236–1240. doi:10.1093/bioinformatics/btu031.

  *Project context*: InterProScan is the authoritative Pfam annotation source on BERDL via `kbase_ke_pangenome.interproscan_domains`. Phase 1A v2 substrate audit switched to it as primary control-detection source.

- **Cantalapiedra, C.P., Hernández-Plaza, A., Letunic, I., Bork, P., Huerta-Cepas, J. (2021).** "eggNOG-mapper v2: functional annotation, orthology assignments, and domain prediction at the metagenomic scale." *Molecular Biology and Evolution* 38(12):5825–5829. doi:10.1093/molbev/msab293.

  *Project context*: eggNOG-mapper provides KO, COG, KEGG_Pathway, BRITE annotations on `kbase_ke_pangenome.eggnog_mapper_annotations`. Used for KO-anchored function-class definitions in Phase 2.

- **Schwengers, O., Jelonek, L., Dieckmann, M.A., Beyvers, S., Blom, J., Goesmann, A. (2021).** "Bakta: rapid and standardized annotation of bacterial genomes via alignment-free sequence identification." *Microbial Genomics* 7(11):000685. doi:10.1099/mgen.0.000685.

  *Project context*: Bakta provides annotation tables on `kbase_ke_pangenome.bakta_*` including `bakta_db_xrefs` (UniRef50/90 mapping) and `bakta_amr` (AMR positive control source).

- **The UniProt Consortium (2023).** "UniProt: the universal protein knowledgebase in 2023." *Nucleic Acids Research* 51(D1):D523–D531.

  *Project context*: UniRef50 / UniRef90 cluster definitions used as the Phase 1 sequence-cluster substrate.

## Reserved for later phases

The following references will become relevant at Phases 1B / 2 / 3 / 4 and are anticipated but not yet cited in REPORT.md:

- **Coleman, G.A., et al. (2021).** "A rooted phylogeny resolves early bacterial evolution." *Science* 372(6542):eabe0511. — informs deep-rank validation when Phase 1B operates on the full GTDB tree.
- **Szöllősi, G.J., et al. (2013).** "Lateral gene transfer from the dead." *Systematic Biology* 62(3):386–397. — DTL reconciliation context for Phase 3 architectural deep-dive (sub-sample scope only).
- **Morel, B., Williams, T.A., Stamatakis, A., Szöllősi, G.J. (2024).** "AleRax: a tool for gene and species tree co-estimation and reconciliation." *Bioinformatics* 40(4):btae162. — held in reserve for Phase 3 principled subsample reconciliation.
- **Metcalf, J.A., et al. (2014).** "Antibacterial gene transfer across the tree of life." *eLife* 3:e04266. — pure-import-system control discussion for Phase 3.
- **Galperin, M.Y. (2018).** "What bacteria want." *Environmental Microbiology* 20(12):4221–4229. — TCS biology context for Phase 2/3 Alm 2006 reproduction.
- **Pang, T.Y., Lercher, M.J. (2017).** "Each of 3,323 metabolic innovations in the evolution of E. coli arose through the horizontal transfer of a single DNA segment." *PNAS* 114(7):1650–1655. — atlas-style precedent for metabolic-innovation analysis at Phase 2.

## Update protocol

- **Phase 1B**: add references substantiating Bacteroidota PUL Innovator-Exchange test; add literature on CAZyme HGT specifically.
- **Phase 2**: add full TCS biology (Galperin), mycolic-acid pathway literature (Marrakchi 2014, Bhatt 2007), KEGG BRITE methods.
- **Phase 3**: add Pfam architecture literature, AleRax / DTL-recon references, photosystem-II HGT literature (Cardona 2018, Soo 2019).
- **Phase 4**: add cross-resolution synthesis precedents, atlas-style review papers.
