# References — Genomic Signatures of Clay-Confined Deep-Subsurface Life

**Searched**: 2026-04-30
**Sources**: PubMed (primary), bioRxiv, Google Scholar, citation snowball via PubMed `find_related_articles`. PaperBLAST attempted but unavailable; results below come from the discovery + full-text pipeline.
**Review depth**: Standard (32 papers ranked, top 6 read in full)
**Query terms**: "Opalinus Clay" OR bentonite OR "deep subsurface" OR "deep biosphere" combined with microbiome / "sulfate reduc*" / "iron reduc*" / hydrogenase / "nuclear waste"; "Black Queen Hypothesis" OR "genome streamlining" with subsurface OR oligotrophy; "Oak Ridge" subsurface; organism filters: Desulfosporosinus, Desulfovibrio, Geobacter, Pelosinus, Sporomusa, Methanobacterium.

---

## Synthesis (for Literature Context in RESEARCH_PLAN.md)

Deep-subsurface clay environments — exemplified by the Opalinus Clay candidate host rock at Mont Terri, MX-80/Wyoming bentonite engineered barriers, Olkiluoto crystalline bedrock, and the saturated clay zones at Oak Ridge — host microbial communities whose composition and metabolism diverge sharply from surface soil. The emerging consensus (Beaver & Neufeld 2024) holds that deep terrestrial subsurface life is anaerobic, chemolithoautotrophic, and predominantly H₂-driven, with the reductive acetyl-CoA (Wood–Ljungdahl) pathway as the dominant carbon-fixation route. Hydrogenase content increases quantitatively with depth (Beaver & Neufeld 2024, citing 2.3 km vs 0.6/1.5 km borehole comparisons), and the canonical genomic signature is **self-sufficiency, not streamlining**: *Candidatus* Desulforudis audaxviator carries full N-fixation, amino-acid biosynthesis, and carbon-fixation in a single genome (Becraft 2021); cumulative reviews (Beaver & Neufeld 2024; Gregory 2024) emphasize biosynthetic autonomy as the adaptation, while streamlining only appears in some niches like freshwater nitrifiers (Podowski 2022) or extreme acidophiles (Cortez 2022). At Mont Terri, in-situ H₂ injection drove a minimalistic hydrogen-driven food web in Opalinus porewater dominated by autotrophic Desulfobulbaceae and Rhodospirillaceae expressing the complete Wood–Ljungdahl pathway, group 1 [NiFe]-hydrogenase, and dissimilatory sulfate reduction (Sat-AprAB-DsrAB) (Bagnoud 2015, 2016) — three MAGs recurred across seven independent boreholes, providing direct evidence of an indigenous Opalinus core community. Crucially, **rock-attached and porewater communities differ qualitatively**: Mitzscherling et al. (2023) showed that Opalinus Clay rock-bound communities are dominated by iron-reducing *Geobacter* and *Geothrix* (4.3–10.2%) tracking pyrite content (r=0.84), with sulfate reducers <0.2%. Compacted bentonite interiors are largely dormant *Bacillus* spores (Engel 2019, Beaver 2024); active SRB lineages (*Desulfosporosinus*, *Desulfotomaculum*) live at the bentonite–groundwater interface. Cultured isolates from these systems — *Desulfosporosinus hippei*, *Sporomusa* MT-2.99, novel *Paenibacillus* spp. (Hilpmann 2023; Moll 2017; Lutke 2013) — carry the predicted dissimilatory anaerobic respiration toolkit, and comparative genomics of subsurface aquifer Firmicutes such as *Pelosinus* HCF1 confirms versatile [NiFe]/[FeFe]-hydrogenase complements coupled to dissimilatory nitrate, Cr(VI), and Fe(III) reduction (Beller 2012; Mosher 2012; Ray 2018). At Oak Ridge, ENIGMA-led work (Ning 2024) frames subsurface community assembly under contamination stress as predominantly stochastic, with the SSO clay-sediment grid reflecting plume-driven redox zonation (the BERIL `enigma_sso_asv_ecology` project). Together, this body of work predicts that BERDL's ~56 cultured clay-isolated genomes — likely biased toward cultivable porewater organisms rather than rock-attached or compacted-clay-interior taxa — should show enrichment of dissimilatory anaerobic respiration markers and biosynthetic self-sufficiency relative to surface soil baselines, and that within the clay cohort, deep-confined isolates (Opalinus borehole, bentonite, deep ENIGMA) should diverge from shallow agricultural-clay isolates (Coalvale, Cerrado) primarily along a depth/redox axis rather than a clay-texture axis.

---

## Themes

### Theme 1: Opalinus Clay (Mont Terri) microbiology

The most directly relevant body of work for our anchor cohort. Mont Terri Underground Rock Laboratory in NW Switzerland is the canonical Opalinus Clay study site for nuclear-waste-repository microbiology.

- **Bagnoud et al. (2016)** [PMID 27739431, PMC5067608] — In-situ H₂ injection at Mont Terri BRC-3 borehole (300 m depth, 500+ days). 22 high-quality MAGs covering >83% of community. Sulfate-reducing regime established by ~150 days. **Desulfobulbaceae c16a** expressed complete Wood–Ljungdahl + group 1 [NiFe]-hydrogenase + Sat/AprAB/DsrAB (full dissimilatory sulfate reduction). **Rhodospirillaceae c57** expressed Calvin-cycle + group 1 [NiFe]-hydrogenase + dissimilatory sulfite reductase. Three MAGs (Desulfobulbaceae c16a, Rhodospirillaceae c57, Peptococcaceae c8a) detected in 7 independent boreholes including anoxically drilled BHT-1 — strong indigeneity evidence. *FULL TEXT READ.*

- **Bagnoud et al. (2015)** [PMID 26542073] — Characterizes the simple, autotrophy-anchored microbial food web (sulfate reducers, autotrophs, fermenters) in Mont Terri Opalinus Clay borehole water. Foundation for the Bagnoud 2016 H₂-injection follow-up.

- **Mitzscherling et al. (2023)** [PMID 37642485, PMC10333725] — Two anoxic Opalinus drill cores (BMA-3 sandy facies, BMA-4 shaly facies). **Iron-reducing bacteria dominate rock-attached communities** (4.3–10.2%, *Geobacter* and *Geothrix*); pyrite content correlates strongly with IRB (r=0.84). Sulfate reducers <0.2% on rock surfaces. Adjacent Passwang limestone is 31% archaeal (methanogens). Rock-attached vs porewater communities differ qualitatively — porewater is SRB-dominated (matching Bagnoud), rock surface is IRB-dominated. Illite content correlates with Proteobacteria (r=0.90), Bacteroidota (r=0.85), Actinobacteria (r=0.85). *FULL TEXT READ.* **Critical implication**: BERDL's cultured clay isolates likely reflect the porewater fraction; BERDL is unlikely to contain rock-attached MAGs.

- **Moll et al. (2017)** [PMID 28390020] — Characterization of *Sporomusa* sp. MT-2.99 isolated from Mont Terri Opalinus Clay, with focus on plutonium speciation. Direct cultured-isolate genome target.

- **Lutke et al. (2013)** [PMID 23508301] — Novel *Paenibacillus* isolate from Mont Terri Opalinus Clay; uranium(VI) speciation. Direct cultured-isolate target.

### Theme 2: Bentonite engineered barriers

Repository-relevant clay engineered barriers; commercial MX-80 Wyoming and Bavarian bentonites studied at Grimsel (Switzerland), Mont Terri, and Canadian URLs.

- **Engel et al. (2019)** [PMID 31852805, PMC6920512] — MX-80 bentonite at Grimsel URL, two compaction densities (1.25, 1.50 g/cm³), 13 months exposure. **Bentonite interiors dominated by *Bacillus* spp.**, likely as inactive spores or relic DNA — independent of compaction density. **Pseudomonas** dominates module surfaces (case/filters, 5.6–44.7% in outer bentonite) but drops to ~2.8% in inner 1A and undetectable in inner 2A. **Desulfosporosinus/Desulfotomaculum** SRBs in borehole fluid only — sharply reduced toward bentonite interior. PLFA confirms low cellular abundances (~10⁶ cells/g). *FULL TEXT READ.*

- **Engel et al. (2023)** [PMID 37772811, PMC10597416] — Stable microbial community in compacted bentonite after 5 years exposure to natural granitic groundwater (Grimsel MaCoTe). Long-term confirmation of Engel 2019 findings.

- **Beaver et al. (2021)** [PMID 34648720] — Cultivation + 16S of Tsukinuno bentonite, Opalinus Clay, and Canadian shield rock; identifies Desulfosporosinus-related SRB and aerobic heterotrophs as viable bentonite/clay microbiome members.

- **Beaver et al. (2024)** [PMID 38458234] — Time-series 16S + culture analysis of MX-80 bentonite at varying dry densities; Pseudomonas, Bacillus, Cupriavidus, Streptomyces, Desulfosporosinus dominance.

- **Gilmour et al. (2021)** [PMID 34958843] — MX-80 bentonite iron-reducing community survival under repository-relevant heat/water stress.

- **Matschiavelli et al. (2019)** [PMID 31369249] — One-year incubations of Bavarian bentonites at HLW-relevant temperatures; metabolic activity profiles of indigenous microbiome including SRBs.

- **Pedersen (2000)** [PMID 11123477] — Foundational study on SRB activity in compacted bentonite under HLW conditions. Key historical reference.

- **Pedersen (2009)** [PMID 20015208] — In-situ underground SRB activity in bentonite as a function of clay density; quantifies how compaction limits anaerobic respiration in repository buffers.

- **Stroes-Gascoyne et al. (1997)** [PMID 9476350] — Foundational Canadian URL study identifying microorganisms in compacted bentonite-sand buffer. Historical reference.

### Theme 3: Deep terrestrial subsurface synthesis & comparative genomics

Reviews and synthesis papers establishing the conceptual framework: anaerobic, autotrophic, H₂-driven; Wood–Ljungdahl pathway; self-sufficiency over streamlining.

- **Beaver & Neufeld (2024)** [PMID 38780093, PMC11170664] — Comprehensive review. Pseudomonadota dominate fluids with meteoric mixing; Bacillota dominate deeper isolated fluids (favor Wood–Ljungdahl, form spores). H₂-driven sulfate reduction, methanogenesis, homoacetogenesis dominant. **Hydrogenase content increases with depth** (2.3 km vs 0.6/1.5 km comparison). Reductive acetyl-CoA pathway is the prevailing carbon-fixation route. **Self-sufficiency is the canonical signature** — full amino-acid biosynthesis, N-fixation, C-fixation. Glycine-betaine osmoprotectants and metal-efflux transporters in saline zones. Lithology + water origin shape community structure more than depth alone. CPR/DPANN ultra-small genomes as episymbionts. *FULL TEXT READ.*

- **Bell et al. (2022)** [PMID 35173296, PMC9123182] — Olkiluoto crystalline bedrock SMTZ at 330–338 m. Active AOM by *Methanoperedens* (ANME-2d) confirmed by metaproteomics + δ¹³C-DIC isotopes. Multiheme cytochromes (28-heme MHC OmcX) + group 1a respiratory [NiFe]-hydrogenase + archaeal flagellin. Desulfobacterota with **YTD gene cluster** doing sulfur disproportionation. CPR/DPANN ultra-small genomes (0.6–1.7 Mbp) as episymbionts contributing fermentative C cycling. *FULL TEXT READ.*

- **Becraft et al. (2021)** [PMID 33824425, PMC8443664] — Single-cell genomics of *Ca. Desulforudis audaxviator* across continents. >99.2% ANI globally — evolutionary stasis. Full self-sufficiency (N-fix, amino-acid biosynthesis, C-fix) in single genome. Canonical reference for self-sufficiency hypothesis.

- **Pedersen et al. (2008)** [PMID 18432279] — Olkiluoto baseline survey of cultivable depth-stratified groundwater microbes (4–450 m). Foundational reference for deep biosphere SRB/IRB at the planned Finnish DGR.

- **Butterworth et al. (2023)** [PMID 37839067, PMC10577106] — Review of polyextremophiles relevant to GDF environments; surveys metabolic strategies under high T/pH/radiation/salinity.

- **Gregory et al. (2024)** [PMID 38216518, PMC10853057] — FEMS Reviews piece predicting microbial activity in EBS; integrates pH/T/radiation/salinity gradients in DGR.

- **Butler et al. (2010)** [PMID 20078895, PMC2825233] — Comparative genomics of six subsurface-relevant *Geobacter* genomes; cytochrome conservation and TCA features. Methodological template for our pangenome work.

- **Guo et al. (2021)** [PMID 34171987, PMC8235581] — Comparative genomics of subsurface *Desulfuromonas* Fe(III)-reducers; identifies cytochrome/chemotaxis differences across niches.

### Theme 4: Cultured-isolate physiology & genomics for BERDL organisms of interest

Direct genome/physiology characterization of organisms expected in BERDL's clay-isolated cohort.

- **Beller et al. (2012)** [PMID 23064329, PMC3536105] — *Pelosinus* sp. HCF1 (Hanford 100H aquifer). Genome encodes 2 [NiFe]- and 4 [FeFe]-hydrogenases, NarGHI nitrate reductase, NrfH/NrfA DNRA, NorCB NO reductase, ChrR/FerB-like Cr(VI)/Fe(III) reductase, methylmalonyl-CoA fermentation pathway. H₂ or lactate as sole donor for nitrate, Cr(VI), Fe(III) reduction. *FULL TEXT (ABSTRACT-ONLY) READ.* Direct comparator for BERDL's clay-isolated *Pelosinus*-related organisms.

- **Mosher et al. (2012)** [PMID 22267668, PMC3302606] — Pelosinus succession in lactate-amended Hanford 100H groundwater; metal-reducing dominance.

- **Ray et al. (2018)** [PMID 30174652, PMC6107796] — Novel *Pelosinus* isolate from Oak Ridge FRC, Fe(III)/Cr(VI) reduction. Direct ENIGMA + BERDL overlap.

- **Vandieken et al. (2017)** [PMID 28646634] — *Marinisporobacter balticus*, *Desulfosporosinus nitroreducens*, *Desulfosporosinus fructosivorans* spp. nov. from Baltic Sea subsurface sediments. New SRB isolates with H₂ as donor, broad acceptor range (SO₄/S₂O₃/sulfite/DMSO/S⁰).

- **Shelobolina et al. (2007)** [PMID 17220454] — Original isolation of *Geobacter pickeringii*, *G. argillaceus*, *Pelosinus fermentans* from subsurface kaolin (clay) lenses. Foundational for clay-confined isolate organism set.

- **Hilpmann et al. (2023)** [PMID 36889400] — *Desulfosporosinus hippei* DSM 8344 U(VI) reduction; relevant for bentonite/clay SRB radionuclide interactions.

### Theme 5: Oak Ridge ENIGMA SSO subsurface biogeochemistry

Context for the BERIL `enigma_sso_asv_ecology` companion project; helps frame how BERDL's clay-isolated genomes connect to in-situ community ecology.

- **Ning et al. (2024)** [PMID 38212658] — ENIGMA-led, Oak Ridge FRC groundwater study; quantifies stochastic vs deterministic assembly of subsurface microbiomes under contamination stress.

### Theme 6: Streamlining and Black Queen alternatives

Counterpoints to the self-sufficiency consensus; help frame H1 as a directional test.

- **Podowski et al. (2022)** [PMID 35435701, PMC9239080] — Genome streamlining in freshwater nitrifiers as oligotrophy adaptation. Relevant counterpoint.

- **Cortez et al. (2022)** [PMID 35387071, PMC8978632] — 260+ acidophile comparative genomics; streamlining as low-pH adaptation. Methodological template for testing streamlining at scale.

- **Props et al. (2019)** [PMID 30728279, PMC6365617] — Counterexample to streamlining: gene expansion and positive selection in oligotrophic nuclear-reactor cooling water. Directly informs the alternative hypothesis.

---

## Cited references (full bibliography)

Bagnoud A, Chourey K, Hettich RL, de Bruijn I, Andersson AF, Leupin OX, Schwyn B, Bernier-Latmani R. (2016). "Reconstructing a hydrogen-driven microbial metabolic network in Opalinus Clay rock." *Nat Commun* 7:12770. DOI: [10.1038/ncomms12770](https://doi.org/10.1038/ncomms12770). PMID: 27739431.

Bagnoud A, Leupin O, Schwyn B, Bernier-Latmani R. (2015). "Rates of microbial hydrogen oxidation and sulfate reduction in Opalinus Clay rock." *FEMS Microbiol Ecol* 91(11):fiv138. DOI: [10.1093/femsec/fiv138](https://doi.org/10.1093/femsec/fiv138). PMID: 26542073.

Beaver RC, Engel K, Binns A, Neufeld JD. (2021). "Microbiology of barrier component analogues of a deep geological repository." *Can J Microbiol* 67(11):825-839. DOI: [10.1139/cjm-2021-0225](https://doi.org/10.1139/cjm-2021-0225). PMID: 34648720.

Beaver RC, Neufeld JD. (2024). "Microbial ecology of the deep terrestrial subsurface." *ISME J* 18(1):wrae091. DOI: [10.1093/ismejo/wrae091](https://doi.org/10.1093/ismejo/wrae091). PMID: 38780093. PMCID: PMC11170664.

Beaver RC, Yarycky O, Engel K, Stuart S, Drago J, Schmid R, Neufeld JD. (2024). "Impact of dry density and incomplete saturation on microbial growth in bentonite clay used for nuclear waste storage." *J Appl Microbiol* 135(3):lxae053. DOI: [10.1093/jambio/lxae053](https://doi.org/10.1093/jambio/lxae053). PMID: 38458234.

Becraft ED, Lau Vetter MCY, Bezuidt OKI, Brown JM, Labonté JM, Kauneckaite-Griguole K, et al. (2021). "Evolutionary stasis of a deep subsurface microbial lineage." *ISME J* 15(10):2830-2842. DOI: [10.1038/s41396-021-00965-3](https://doi.org/10.1038/s41396-021-00965-3). PMID: 33824425. PMCID: PMC8443664.

Bell E, Lamminmäki T, Alneberg J, Andersson AF, Qian C, Xiong W, et al. (2022). "Active anaerobic methane oxidation and sulfur disproportionation in the deep terrestrial subsurface." *ISME J* 16(5):1583-1593. DOI: [10.1038/s41396-022-01207-w](https://doi.org/10.1038/s41396-022-01207-w). PMID: 35173296. PMCID: PMC9123182.

Beller HR, Han R, Karaoz U, Lim H, Brodie EL. (2012). "Genomic and physiological characterization of the chromate-reducing, aquifer-derived Firmicute *Pelosinus* sp. strain HCF1." *Appl Environ Microbiol* 78(24):8791-8800. DOI: [10.1128/AEM.02496-12](https://doi.org/10.1128/AEM.02496-12). PMID: 23064329. PMCID: PMC3536105.

Butler JE, Young ND, Lovley DR. (2010). "Evolution of electron transfer out of the cell: comparative genomics of six *Geobacter* genomes." *BMC Genomics* 11:40. DOI: [10.1186/1471-2164-11-40](https://doi.org/10.1186/1471-2164-11-40). PMID: 20078895. PMCID: PMC2825233.

Butterworth SJ, Renshaw JC, Morris K. (2023). "Extremophilic microbial metabolism and radioactive waste disposal." *Extremophiles* 27(3):27. DOI: [10.1007/s00792-023-01312-4](https://doi.org/10.1007/s00792-023-01312-4). PMID: 37839067. PMCID: PMC10577106.

Cortez D, Neira G, González C, Vergara E, Holmes DS. (2022). "A large-scale genome-based survey of acidophilic bacteria suggests genome streamlining is an adaptation for life at low pH." *Front Microbiol* 13:803241. DOI: [10.3389/fmicb.2022.803241](https://doi.org/10.3389/fmicb.2022.803241). PMID: 35387071. PMCID: PMC8978632.

Engel K, Coyotzi S, Vachon MA, McKelvie JR, Neufeld JD. (2019). "Stability of microbial community profiles associated with compacted bentonite from the Grimsel Underground Research Laboratory." *mSphere* 4(6):e00601-19. DOI: [10.1128/mSphere.00601-19](https://doi.org/10.1128/mSphere.00601-19). PMID: 31852805. PMCID: PMC6920512.

Engel K, Coyotzi S, Vachon MA, McKelvie JR, Neufeld JD. (2023). "Stable microbial community in compacted bentonite after 5 years of exposure to natural granitic groundwater." *mSphere* 8(5):e00048-23. DOI: [10.1128/msphere.00048-23](https://doi.org/10.1128/msphere.00048-23). PMID: 37772811. PMCID: PMC10597416.

Gilmour KA, Sangster M, Kellingray L, Williams S, Crampin H, Dotchev I, Pisani A, Pearson R, Cawthorn G, Wilson G. (2021). "Survival and activity of an indigenous iron-reducing microbial community from MX80 bentonite in high-pressure/saline conditions." *Sci Total Environ* 814:152660. DOI: [10.1016/j.scitotenv.2021.152660](https://doi.org/10.1016/j.scitotenv.2021.152660). PMID: 34958843.

Gregory SP, Henrys ST, Boylan AA, Vettese GF, Wilson MJ, Tracey J, Morris K, Pereira MR, Daniels P, Lloyd JR. (2024). "Radioactive waste microbiology: predicting microbial survival and activity in changing extreme environments." *FEMS Microbiol Rev* 48(1):fuae001. DOI: [10.1093/femsre/fuae001](https://doi.org/10.1093/femsre/fuae001). PMID: 38216518. PMCID: PMC10853057.

Guo Y, Aoyagi T, Inaba T, Sato Y, Habe H, Hori T. (2021). "Comparative insights into genome signatures of ferric iron oxide- and anode-stimulated *Desulfuromonas* spp. strains." *BMC Genomics* 22:475. DOI: [10.1186/s12864-021-07809-6](https://doi.org/10.1186/s12864-021-07809-6). PMID: 34171987. PMCID: PMC8235581.

Hilpmann S, Drobot B, Steudtner R, Bok F, Stumpf T, Cherkouk A. (2023). "Presence of uranium(V) during uranium(VI) reduction by *Desulfosporosinus hippei* DSM 8344." *Sci Total Environ* 875:162593. DOI: [10.1016/j.scitotenv.2023.162593](https://doi.org/10.1016/j.scitotenv.2023.162593). PMID: 36889400.

Lutke L, Moll H, Bachvarova V, Selenska-Pobell S, Bernhard G. (2013). "The U(VI) speciation influenced by a novel *Paenibacillus* isolate from Mont Terri Opalinus clay." *Dalton Trans* 42(18):6498-6504. DOI: [10.1039/c3dt33032j](https://doi.org/10.1039/c3dt33032j). PMID: 23508301.

Matschiavelli N, Steinbrück D, Sommer T, Brockmann S, Schmeide K, Cherkouk A. (2019). "The year-long development of microorganisms in uncompacted Bavarian bentonite slurries at 30°C and 60°C." *Environ Sci Technol* 53(17):10514-10524. DOI: [10.1021/acs.est.9b02670](https://doi.org/10.1021/acs.est.9b02670). PMID: 31369249.

Mitzscherling J, Genderjahn S, Schleicher AM, Bartholomäus A, Kallmeyer J, Wagner D. (2023). "Clay-associated microbial communities and their relevance for a nuclear waste repository in the Opalinus Clay rock formation." *MicrobiologyOpen* 12(4):e1370. DOI: [10.1002/mbo3.1370](https://doi.org/10.1002/mbo3.1370). PMID: 37642485. PMCID: PMC10333725.

Moll H, Bachvarova V, Lütke L, Selenska-Pobell S, Cherkouk A, Geißler A, Bernhard G. (2017). "Plutonium interaction studies with the Mont Terri Opalinus Clay isolate *Sporomusa* sp. MT-2.99." *Environ Sci Pollut Res* 24(11):10643-10654. DOI: [10.1007/s11356-017-8969-6](https://doi.org/10.1007/s11356-017-8969-6). PMID: 28390020.

Mosher JJ, Phelps TJ, Podar M, Hurt RA Jr, Campbell JH, Drake MM, et al. (2012). "Microbial community succession during lactate amendment and electron acceptor limitation reveals a predominance of metal-reducing *Pelosinus* spp." *Appl Environ Microbiol* 78(7):2082-2091. DOI: [10.1128/AEM.07165-11](https://doi.org/10.1128/AEM.07165-11). PMID: 22267668. PMCID: PMC3302606.

Ning D, Wang Y, Fan Y, Wang J, Van Nostrand JD, Wu L, et al. (2024). "Environmental stress mediates groundwater microbial community assembly." *Nat Microbiol* 9(2):490-501. DOI: [10.1038/s41564-023-01573-x](https://doi.org/10.1038/s41564-023-01573-x). PMID: 38212658.

Pedersen K. (2000). "Mixing and sulphate-reducing activity of bacteria in swelling, compacted bentonite clay under high-level radioactive waste repository conditions." *J Appl Microbiol* 89(6):1038-1046. DOI: [10.1046/j.1365-2672.2000.01212.x](https://doi.org/10.1046/j.1365-2672.2000.01212.x). PMID: 11123477.

Pedersen K. (2009). "Analysis of copper corrosion in compacted bentonite clay as a function of clay density and growth conditions for sulfate-reducing bacteria." *J Appl Microbiol* 108(3):1094-1104. DOI: [10.1111/j.1365-2672.2009.04629.x](https://doi.org/10.1111/j.1365-2672.2009.04629.x). PMID: 20015208.

Pedersen K, Arlinger J, Hallbeck A, Hallbeck L, Eriksson S, Johansson J. (2008). "Numbers, biomass and cultivable diversity of microbial populations relate to depth and borehole-specific conditions in groundwater from depths of 4-450 m in Olkiluoto, Finland." *ISME J* 2(7):760-775. DOI: [10.1038/ismej.2008.43](https://doi.org/10.1038/ismej.2008.43). PMID: 18432279.

Podowski JC, Paver SF, Newton RJ, Coleman ML. (2022). "Genome streamlining, proteorhodopsin, and organic nitrogen metabolism in freshwater nitrifiers." *mBio* 13(2):e02379-21. DOI: [10.1128/mbio.02379-21](https://doi.org/10.1128/mbio.02379-21). PMID: 35435701. PMCID: PMC9239080.

Props R, Monsieurs P, Vandamme P, Leys N, Denef VJ, Boon N. (2019). "Gene expansion and positive selection as bacterial adaptations to oligotrophic conditions." *mSphere* 4(1):e00011-19. DOI: [10.1128/mSphereDirect.00011-19](https://doi.org/10.1128/mSphereDirect.00011-19). PMID: 30728279. PMCID: PMC6365617.

Ray AE, Connon SA, Sheridan PP, Gilbreath J, Shields M, Newby DT, Fujita Y, Magnuson TS. (2018). "Metal transformation by a novel *Pelosinus* isolate from a subsurface environment." *Front Microbiol* 9:1689. DOI: [10.3389/fmicb.2018.01689](https://doi.org/10.3389/fmicb.2018.01689). PMID: 30174652. PMCID: PMC6107796.

Shelobolina ES, Nevin KP, Blakeney-Hayward JD, Johnsen CV, Plaia TW, Krader P, Woodard T, Holmes DE, Vanpraagh CG, Lovley DR. (2007). "*Geobacter pickeringii* sp. nov., *Geobacter argillaceus* sp. nov. and *Pelosinus fermentans* gen. nov., sp. nov., isolated from subsurface kaolin lenses." *Int J Syst Evol Microbiol* 57(Pt 1):126-135. DOI: [10.1099/ijs.0.64221-0](https://doi.org/10.1099/ijs.0.64221-0). PMID: 17220454.

Stroes-Gascoyne S, Pedersen K, Daumas S, Hamon CJ, Haveman SA, Delaney TL, Ekendahl S, Jahromi N, Arlinger J, Hallbeck L, Dekeyser K. (1997). "Occurrence and identification of microorganisms in compacted clay-based buffer material designed for use in a nuclear fuel waste disposal vault." *Can J Microbiol* 43(11):1133-1146. DOI: [10.1139/m97-162](https://doi.org/10.1139/m97-162). PMID: 9476350.

Vandieken V, Niemann H, Engelen B, Cypionka H. (2017). "*Marinisporobacter balticus* gen. nov., sp. nov., *Desulfosporosinus nitroreducens* sp. nov. and *Desulfosporosinus fructosivorans* sp. nov., new spore-forming bacteria isolated from subsurface sediments of the Baltic Sea." *Int J Syst Evol Microbiol* 67(6):1887-1893. DOI: [10.1099/ijsem.0.001883](https://doi.org/10.1099/ijsem.0.001883). PMID: 28646634.

---

## Relevance to BERDL collections

| Literature focus | BERDL table(s) to query | Specific opportunity |
|---|---|---|
| Wood–Ljungdahl as canonical deep-subsurface C-fix pathway | `kbase_ke_pangenome.eggnog_mapper_annotations` (KEGG K00198 acsA, K00194 acsB, K00197 acsC, K00193 cooS); `kbase_msd_biochemistry.reaction` | Test for full-pathway presence per genome in clay-isolated cohort vs soil baseline |
| Group 1 [NiFe]-hydrogenase as depth-enriched marker | `kbase_ke_pangenome.eggnog_mapper_annotations` (PFAM Hyd_Beta + Hyd_Small, KEGG K06281 hyaA / K06282 hyaB) | Quantify hydrogenase content per genome by depth class |
| Self-sufficiency vs streamlining | `kbase_ke_pangenome.gapmind_pathways` (amino acid biosynthesis pathway completeness); `gtdb_metadata` (genome size, GC%) | Test pathway completeness × genome size in deep-clay vs soil |
| Iron reduction (Geobacter/Geothrix dominance on rock surfaces) | `kbase_ke_pangenome.eggnog_mapper_annotations` (PFAM Cytochrom_NNT, KEGG K07811 omcS, K17324 mtrC); `kbase_genomes` cytochrome counts | Test if BERDL clay isolates carry rock-attached vs porewater signatures |
| SRB markers (dsrAB, aprAB, sat) | `kbase_ke_pangenome.eggnog_mapper_annotations` (KEGG K11180 dsrA, K11181 dsrB, K00394 aprA, K00395 aprB, K00958 sat) | Verify Bagnoud porewater signature in BERDL Mont Terri isolates |
| *Ca.* Desulforudis / self-sufficient bacteria | `kbase_ke_pangenome.gapmind_pathways` (full amino-acid + nitrogen biosynthesis); GapMind pathway-completeness vector per genome | Identify BERDL genomes matching the self-sufficiency profile |
| Mont Terri / Opalinus indigeneity (3 MAGs across 7 boreholes) | `kbase_ke_pangenome.genome` filtered on Opalinus biosamples | Cross-check whether BERDL's 8 Mont Terri genomes overlap the Bagnoud Desulfobulbaceae c16a / Rhodospirillaceae c57 / Peptococcaceae c8a lineages |
| Oak Ridge ENIGMA cross-link | `enigma_coral.sdt_strain` + `kbase_ke_pangenome.genome` | Test whether ENIGMA SSO cultured strains are pangenome-linkable; if so, expand the deep-clay cohort with Oak Ridge isolates |
