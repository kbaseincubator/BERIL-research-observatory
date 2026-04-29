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

### Methodology — tree-aware metrics (added in Phase 1B post-NB08c)

- **Sankoff, D. (1975).** "Minimal mutation trees of sequences." *SIAM Journal on Applied Mathematics* 28(1):35–42. doi:10.1137/0128004.

  *Project context*: original Sankoff parsimony algorithm for character-state minimization on phylogenetic trees. NB08c uses the binary-trait special case (Fitch-Hartigan) on the GTDB-r214 tree for HGT-vs-vertical discrimination.

- **Fitch, W.M. (1971).** "Toward defining the course of evolution: minimum change for a specific tree topology." *Systematic Zoology* 20(4):406–416.

  *Project context*: Fitch's algorithm for binary-trait parsimony — the form actually implemented in NB08c (post-order intersection / union counting).

- **Mirkin, B.G., Fenner, T.I., Galperin, M.Y., Koonin, E.V. (2003).** "Algorithms for computing parsimonious evolutionary scenarios for genome evolution, the last universal common ancestor and dominance of horizontal gene transfer in the evolution of prokaryotes." *BMC Evolutionary Biology* 3:2. doi:10.1186/1471-2148-3-2.

  *Project context*: the canonical reference for parsimony-based HGT inference at the genome scale. Justifies the tree-aware metric choice (M15) and provides a precedent for using parsimony as an HGT proxy at large scale where full DTL reconciliation is infeasible.

- **Soucy, S.M., Huang, J., Gogarten, J.P. (2015).** "Horizontal gene transfer: building the web of life." *Nature Reviews Genetics* 16(8):472–482. doi:10.1038/nrg3962.

  *Project context*: review of HGT depth distribution. *Already cited* — moved here for visibility under the methodology section. Informs the Phase 1B interpretation of the cross-rank consumer-z trend (vertical at deep ranks, weakens at class) and the order-rank anomaly investigation.

- **Csurös, M. (2010).** "Count: evolutionary analysis of phylogenetic profiles with parsimony and likelihood." *Bioinformatics* 26(15):1910–1912. doi:10.1093/bioinformatics/btq315.

  *Project context*: the Count software implements parsimony + likelihood-based ancestral state reconstruction at large scale. Reference implementation that justifies the lightweight Fitch approach in NB08c at GTDB scale.

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

- **Phillips, G., et al. (2012).** "Phylogenomics of Prokaryotic Ribosomal Proteins." *PLoS ONE* 7(5):e36972. doi:10.1371/journal.pone.0036972. PMID:22615862.

  *Project context*: bacterial ribosomal proteins show low paralogy (geometric mean 1.02 paralogs per r-protein vs 1.63 for other universal genes) due to dosage balance. Cited at Phase 2 atlas synthesis (REPORT v1.8) — the M22 finding that tRNA-synth has low recent-acquisition (24.7%) extends Phillips' low-paralogy-under-dosage-constraint result to acquisition timing.

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

## Phase 2 hypothesis-test literature (added v2.2)

- **Marrakchi, H., Lanéelle, M.A., Daffé, M. (2014).** "Mycolic acids: structures, biosynthesis, and beyond." *Chemistry & Biology* 21(1):67–85. doi:10.1016/j.chembiol.2013.11.011. PMID:24374164.

  *Project context*: review of mycolic-acid biosynthesis pathway and biology. Cited at Phase 2 NB12 (REPORT v2.2) — supports the Mycobacteriaceae × mycolic-acid Innovator-Isolated H1 SUPPORTED finding. Marrakchi et al. document the mycolic-acid pathway as a major and specific lipid component of the mycobacterial cell envelope, essential for survival of *Mycobacterium* (causative agents of tuberculosis and leprosy). The autocatalytic cell-envelope-coupled biosynthesis explains the Innovator-Isolated phenotype recovered by NB12: high producer score (lineage-specific paralog expansion, including the *M. tuberculosis* PE/PPE family) + low participation (zero ancient or older-class gain events; cell-envelope coupling prevents cross-phylum HGT).

## Foundational HGT methodology + complexity hypothesis (added v2.5)

- **Bansal, M.S., Alm, E.J., Kellis, M. (2012).** "Efficient algorithms for the reconciliation problem with gene duplication, horizontal transfer and loss." *Bioinformatics* 28(12):i283–i291. doi:10.1093/bioinformatics/bts225. PMID:22689773. PMC3371857.

  *Project context*: foundational DTL reconciliation algorithm framework. Cited at REPORT v2.5 — establishes the principled methodology against which our Sankoff parsimony approach is the lightweight tractable alternative at GTDB scale. Bansal et al. 2012 demonstrate up to 100,000-fold speed-up over prior DTL methods; per plan v2.6's Phase 3 reservation, AleRax/RangerDTL are available for sub-sample reconciliation but not at full GTDB scale (Phase 3 v2.11 reframe per M25 documents this constraint). Project methodology is therefore parsimony-based (Sankoff at scale), with DTL reconciliation reserved for Phase 4 P4-D3 deep-dive on the Mycobacteriaceae × mycolic-acid candidate set (deferred).

- **Burch, C.L., Romanchuk, A., Kelly, M., Wu, Y., Jones, C.D. (2023).** "Empirical Evidence That Complexity Limits Horizontal Gene Transfer." *Genome Biology and Evolution* 15(6):evad089. doi:10.1093/gbe/evad089. PMID:37232518. PMC10267694.

  *Project context*: empirical validation of the Jain 1999 complexity hypothesis using 74 prokaryotic genomes shotgun-libraries to *E. coli*. Three findings: (1) transferability declines as connectivity increases; (2) transferability declines as donor-recipient orthologs diverge; (3) the negative effect of divergence on transferability scales with connectivity. *Translational proteins span the widest connectivity range and show this effect most strongly.* Cited at REPORT v2.5 — directly supports NB11's H1 REFRAMED verdict (regulatory KOs *more clumped* than metabolic at small effect size, d=−0.21). Our GTDB-scale finding is the per-(clade × KO) instantiation of the per-(donor × E. coli) finding Burch et al. demonstrate empirically. Both find the predicted direction at sub-strong effect: the complexity hypothesis is real but its effect is small at the function-class level.

- **Ślesak, I., Ślesak, H. (2024).** "From cyanobacteria and cyanophages to chloroplasts: the fate of the genomes of oxyphototrophs and the genes encoding photosystem II proteins." *New Phytologist* 242(3):1055–1067. doi:10.1111/nph.19633. PMID:38439684.

  *Project context*: synonymous mutation rate analysis of psbA/psbD/psbO across cyanobacterial, chloroplast, and cyanophage genomes; psbA and psbD identified as ancient and conservative, arising early in the evolution of oxygenic photosynthesis. Cited at REPORT v2.5 — additional support for the Cyanobacteria-as-PSII-origin framing alongside Cardona et al. 2018. The conservatism of psbA/psbD across oxyphototroph lineages (low synonymous mutation rate, ancient origin) is consistent with NB16's donor-origin acquisition signature: Cyanobacteria's ancestor evolved the pathway; non-Cyano phyla received it via documented HGT.

- **Denise, R., Abby, S.S., Rocha, E.P.C. (2019).** "Diversification of the type IV filament superfamily into machines for adhesion, protein secretion, DNA uptake, and motility." *PLoS Biology* 17(7):e3000390. doi:10.1371/journal.pbio.3000390. PMID:31323028. PMC6668835.

  *Project context*: comparative genomics of the type IV filament (TFF) superfamily across Bacteria and Archaea. Key finding: *"systems encoded in fewer loci were more frequently exchanged between taxa. This may have contributed to their rapid evolution and spread."* Cited at REPORT v2.5 — provides a literature analog for the Phase 3 NB15 architectural-promiscuity finding. Denise et al. 2019's "fewer loci → more exchange" pattern is the genome-organization analog of our "more architectures per KO → more exchange" pattern. Both findings frame structural-organization simplicity as a driver of cross-clade flow at large evolutionary scales. Together they suggest that *modularity* — at either the locus-count or the architecture-count level — is the property that distinguishes mobile from constrained gene families.

## Phase 3 hypothesis-test literature (added v2.4)

- **Cardona, T., Sánchez-Baracaldo, P., Rutherford, A.W., Larkum, A.W. (2018).** "Early Archean origin of Photosystem II." *Geobiology* 17(2):127–150. doi:10.1111/gbi.12322. PMID:30411862. PMC6492235.

  *Project context*: phylogenomic + Bayesian relaxed molecular clock analysis showing that a homodimeric photosystem capable of water oxidation appeared in the early Archean ~1 Gyr before the most recent common ancestor of all described Cyanobacteria, and well before the diversification of anoxygenic photosynthetic bacteria. Cited at Phase 3 NB16 (REPORT v2.4) — supports the Cyanobacteria-as-PSII-origin framing recovered by NB16's acquisition-depth signature (Cyanobacteria PSII gains: 2.05% ancient vs 14.9% atlas-wide). The 7× lower ancient fraction in Cyanobacteria PSII is the donor-origin signature: Cyanobacteria's ancestor evolved PSII; non-Cyano phyla received PSII via HGT (those gains are ancient *for the recipient*, contributing to the high atlas-wide ancient %); Cyanobacteria themselves don't receive ancient cross-phylum PSII transfers because they're the source. Cardona et al. 2018 provides the temporal-and-phylogenetic anchor for this interpretation.

## Foundational HGT literature (added v2.3)

- **Lawrence, J.G., Ochman, H. (1998).** "Molecular archaeology of the Escherichia coli genome." *Proceedings of the National Academy of Sciences USA* 95(16):9413–9417. doi:10.1073/pnas.95.16.9413. PMID:9689094. PMC21352.

  *Project context*: foundational HGT-detection paper documenting that 755 of 4,288 ORFs (≈18% of the *E. coli* chromosome) were introduced via lateral transfer in ≥234 events since divergence from *Salmonella* 100 Myr ago. Composition-based codon-usage methodology (predates phylogenetic-tree-aware methods this project uses). Cited at REPORT v2.3 — establishes the historical methodology baseline against which our Sankoff-parsimony approach (M16, NB10) is the tree-aware successor. Lawrence & Ochman document HGT at single-organism scale; this project extends to the full GTDB tree.

- **Jain, R., Rivera, M.C., Lake, J.A. (1999).** "Horizontal gene transfer among genomes: the complexity hypothesis." *Proceedings of the National Academy of Sciences USA* 96(7):3801–3806. doi:10.1073/pnas.96.7.3801. PMID:10097118. PMC22375.

  *Project context*: the canonical reference for why regulatory ("informational") genes show *less* HGT than metabolic ("operational") genes — informational genes are typically members of large protein-protein-interaction systems, making horizontal transfer less probable. Cited at REPORT v2.3 — **NB11's T2 finding (regulatory KOs more phylogenetically clumped than metabolic, consumer z d=−0.211, p<10⁻¹⁵) is direction-consistent with the complexity hypothesis at small effect size.** The H1 REFRAMED verdict in NB11 is therefore not a contradiction of established literature but an extension: at GTDB scale across 6,524 KOs (regulatory + metabolic), the complexity-hypothesis effect is detectable but small (d ≈ 0.2) — meaningful at full-tree scale but below the strong-form d ≥ 0.3 threshold the project pre-registered for the asymmetry headline.

## Adversarial review 9 literature (added v3.5)

- **Williams, T.A., Davin, A.A., Szánthó, L.L., Stamatakis, A., Wahl, N.A., Woodcroft, B.J., Soo, R.M., Eme, L., Sheridan, P.O., Gubry-Rangin, C., Spang, A., Hugenholtz, P., Szöllősi, G.J. (2024).** "Phylogenetic reconciliation: making the most of genomes to understand microbial ecology and evolution." *The ISME Journal* 18(1):wrae129. doi:10.1093/ismejo/wrae129. PMID:39001714.

  *Project context*: comprehensive review of modern phylogenetic reconciliation methods for microbial ecology and evolution. Documents recent computational advances making reconciliation feasible at hundreds-of-species scale, including ancestral gene content inference, species-tree rooting, and ecological-metadata integration. Cited at REPORT v3.5 (REVIEW_9 response) — provides the modern methodology baseline against which the project's Sankoff parsimony approximation should be compared. The project's "DTL doesn't scale to GTDB" framing is qualified by Williams 2024: principled DTL methods are scaling, just not yet to the full 18,989-leaf tree the project uses. Future cross-validation against representative GTDB subsets remains a defensible direction.

- **López Sánchez, A., Scholz, G.E., Stadler, P.F., Lafond, M. (2026).** "From Small Parsimony to Horizontal Gene Transfer: Inferring Horizontal Transfer and Gene Loss for Single-Origin Characters." *Journal of Computational Biology* 33(4):535-557. doi:10.1177/15578666261426009. PMID:41955011.

  *Project context*: presents a Sankoff-Rousseau-like algorithm for HGT inference using KEGG functions on bacterial species — **directly parallel methodology** to the project's M22 framework. Models small-parsimony-with-loss-and-transfer scenarios with user-defined penalization for losses vs transfers. The paper's case study on bacterial species + KEGG functions demonstrates that the approach is computationally tractable. Cited at REPORT v3.5 — represents a direct methodology peer to compare against. The project's M22 implementation is independent but conceptually similar; future work should benchmark M22 outputs against López Sánchez 2026's algorithm on a shared bacterial-KEGG substrate to assess methodological concordance.

- **Gisriel, C.J., Bryant, D.A., Brudvig, G.W., Cardona, T. (2023).** "Molecular diversity and evolution of far-red light-acclimated photosystem I." *Frontiers in Plant Science* 14:1289199. doi:10.3389/fpls.2023.1289199. PMID:38053766.

  *Project context*: phylogenetic analysis of FaRLiP (far-red light photoacclimation) photosystem I subunits across cyanobacteria. Documents that the order Nodosilineales (including Synechococcus sp. PCC 7335) could have obtained FaRLiP via horizontal gene transfer, with FaRLiP-specific PSI subunits arising relatively late in cyanobacterial evolution. Cited at REPORT v3.5 — qualifies the Cardona 2018 PSII donor-origin framing the project uses for NB16. The project's NB16 finding is about photosystem **II** at class rank, where the donor-origin framing holds (PSII evolved ~1 Gyr before Cyanobacteria diversified per Cardona 2018). Gisriel 2023 documents that photosystem **I** FaRLiP variants — a niche photosystem subset — can undergo within-Cyanobacteria HGT. The two findings are consistent: PSII core machinery is class-defining and donor-origin; FaRLiP variants of PSI are recent and HGT-mobile within Cyanobacteria. Adds nuance to the "Cyanobacteria photosystem evolution is purely vertical" oversimplification.

## Phase 4 adversarial review 8 literature (added v3.1)

- **Liu, J., Mawhorter, R., Liu, N., Libeskind-Hadas, R., Wu, Y.-C. (2021).** "Maximum parsimony reconciliation in the DTLOR model." *BMC Bioinformatics* 22(Suppl 10):394. doi:10.1186/s12859-021-04290-6. PMID:34348661.

  *Project context*: introduces the DTLOR model (Duplication-Transfer-Loss-Origination-Rearrangement) extending standard DTL to handle two events common in microbial evolution: gene origin from outside the sampled species tree, and rearrangement of gene syntenic regions. Cited at REPORT v3.1 (REVIEW_8 response) — represents the modern DTL reconciliation methodology that the project's Sankoff parsimony approximation does NOT engage with. The project's defensible position is that Sankoff parsimony is computationally tractable at full GTDB scale (17M gain events on 18,989-leaf tree) where exact DTL methods are not; Liu et al. 2021 DTLOR remains a future cross-validation target on a representative GTDB subset.

- **Kundu, S., Bansal, M.S. (2018).** "On the impact of uncertain gene tree rooting on duplication-transfer-loss reconciliation." *BMC Bioinformatics* 19(Suppl 9):290. doi:10.1186/s12859-018-2269-0. PMID:30367593.

  *Project context*: documents that a large fraction of gene trees have multiple optimal rootings, and quantifies which aspects of DTL reconciliation are conserved across rootings on 4,500+ gene families from 100 species. Cited at REPORT v3.1 — directly applicable to project's Sankoff parsimony pipeline which lacks rooting-uncertainty quantification. Honest reportable limit: the M22 acquisition-depth attribution does not propagate gene-tree-rooting uncertainty into per-event uncertainty bounds.

- **Benzerara, K., et al. (2026).** "Intracellular amorphous calcium carbonate biomineralization in methanotrophic gammaproteobacteria was acquired by horizontal gene transfer from cyanobacteria." *Environmental Microbiology* 28(3):e70270. doi:10.1111/1462-2920.70270.

  *Project context*: provides direct phylogenetic evidence of recent Cyanobacteria → Gammaproteobacteria HGT for the *ccyA* gene (calcium carbonate biomineralization). Cited at REPORT v3.1 — independent example of Cyanobacteria functioning as HGT *donor* clade at recent ranks, supporting the project's NB16 interpretive framework that Cyanobacteria's role in PSII evolution is donor-origin (low ancient acquisition fraction within Cyanobacteria; PSII ancient *for recipient* phyla but not for the source). Validates the environmental-co-occurrence-drives-HGT framing.

- **Yu, J., et al. (2025).** "Characterization of two novel species of the genus Flagellimonas reveals the key role of vertical inheritance in the evolution of alginate utilization loci." *Microbiology Spectrum* 13(4):e00917-25. doi:10.1128/spectrum.00917-25.

  *Project context*: documents that vertical inheritance (not HGT) dominates Bacteroidota alginate utilization locus (AUL) evolution at the *Flagellimonas* genus level, with structural simplification of AUL leading to reduced alginate-degradation ability. Cited at REPORT v3.1 — *complicates* the simple "PUL = HGT-mediated" framing the project has implicitly carried since the v1 plan. The Phase 1B Bacteroidota PUL verdict (falsified at deep-rank absolute-zero criterion; recovered as small consumer-z signal at d=0.15 via Sankoff diagnostic NB08c) is *consistent* with Yu et al. 2025: within-Bacteroidota PUL evolution is more vertical than horizontal at fine taxonomic resolution. The project's Phase 1B "qualified pass" framing is honest; Yu et al. 2025 supports rather than contradicts that framing.

## Update protocol

- **Phase 1B**: add references substantiating Bacteroidota PUL Innovator-Exchange test; add literature on CAZyme HGT specifically. *(closed)*
- **Phase 2**: add full TCS biology (Galperin — already cited), mycolic-acid pathway literature (Marrakchi 2014 ✓ added at v2.2; Bhatt 2007 deferred), KEGG BRITE methods. *(NB12 result supported via Marrakchi 2014 at v2.2)*
- **Phase 3**: add Pfam architecture literature, AleRax / DTL-recon references, photosystem-II HGT literature (Cardona 2018, Soo 2019).
- **Phase 4**: add cross-resolution synthesis precedents, atlas-style review papers; environmental ecology HGT (Anantharaman 2016 if verified, Cordero & Polz 2014 if verified — REVIEW_5 S1 suggestion).
