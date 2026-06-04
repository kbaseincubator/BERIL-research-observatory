# References

## Caulobacter Δ*fur* permits Δ*lpxC* — published mechanism and surrounding literature

Searched: 2026-06-04. Sources: PubMed (10 targeted queries + 8 author-anchored), Google Scholar (4 broad queries), bioRxiv (via Scholar — direct API was returning unrelated content), PaperBLAST (`kescience_paperblast`, on-cluster).
Review depth: Standard. PubMed `find_related_articles` failed persistently (API_ERROR) — snowballing was supplemented through Google Scholar related-work, which recovered the same key items (Uchendu 2026 preprint, Olea-Ozuna 2024, Hummels 2024 commentary, Greenwich 2023 review).

> **Bottom line — the headline question is already answered in the published literature.** Zik et al. 2022 (Cell Reports, PMID 35649364) establishes that in *C. crescentus*, Δ*lpxC* tolerance requires **both** loss of *fur* **and** the presence of anionic sphingolipids — specifically **ceramide phosphoglycerate (CPG)** produced by the sphingolipid biosynthesis locus CCNA_01212/CCNA_01217–01223. **H3 (hopanoid substitution) is wrong; the correct substitute is anionic sphingolipids.** Δ*sspB* is part of the published mechanism, not a confound. The senior author K.R. Ryan is almost certainly the colleague (`krr@berkeley.edu`) who supplied the data — meaning this dataset is a *follow-up* layered on top of the published mechanism, not a fresh discovery.

The literature review's main contribution to this project is therefore to (a) refocus the analysis on what the new RNA-seq + OM proteome tell us *beyond* Zik 2022, and (b) supply the comparative-genomics context needed to ask why the other three lipid-A-loss-tolerant Gram-negatives (*A. baumannii*, *N. meningitidis*, *M. catarrhalis*) take different routes.

---

### Theme A — Caulobacter Δ*lpxC* viability mechanism (the keystone literature)

The Ryan/Klein-lab axis at Berkeley defines the published mechanism and its biochemistry. Read these first; everything else in this review is context.

1. **Zik JJ, Yoon SH, Guan Z, … Klein EA, Ryan KR.** (2022). "Caulobacter lipid A is conditionally dispensable in the absence of *fur* and in the presence of anionic sphingolipids." *Cell Reports* 39(11):110888. PMID 35649364. PMC9393093. DOI: 10.1016/j.celrep.2022.110888 — **the keystone paper.** Demonstrates that mutations in *fur* together with anionic sphingolipids (CPG) make lipid A dispensable; loss of *lpxC* or *ctpA* is tolerated only with both. Concludes "Fur-regulated processes (not iron status per se)" underlie viability. Identifies CCNA_01212, CCNA_01217-01219, *spt* (CCNA_01220), *acp* (CCNA_01221), *cerR* (CCNA_01222), *acps* (CCNA_01223), *bcerS* (CCNA_01212) as required for tolerance. Also: CCNA_03113 (LpxE-like) may substitute for LpxF in CPG processing. Suppressor mutations in *fur*, CCNA_00497, CCNA_01068 (*wbqA*), CCNA_01553, CCNA_03733 (*manC*-like) all relax LpxC essentiality.
2. **Zik JJ.** (2019). "Signal Transduction Mechanisms in *Caulobacter crescentus*" (PhD thesis, Berkeley). — earliest detailed write-up of the *fur*/*lpxC* suppression genetics, prior to the 2022 paper. Useful for unpublished detail and raw-strain history.
3. **Uchendu CG, Isom GL, Klein EA.** (2026, preprint). "Homologues of the inner-membrane LPS transport proteins are required for sphingolipid transport in *Caulobacter crescentus*." bioRxiv 2026.04.12.717747. DOI: 10.1101/2026.04.12.717747 — **the most recent follow-up.** Identifies an inner-membrane lipid transport complex (LPS-Tlc paralogs) required for CPG/sphingolipid transport in lipid-A-deficient *Caulobacter*. Strengthens the substitution model and gives candidate proteins likely to appear in the OM proteome.
4. **Dhakephalkar T, Guan Z, Klein EA.** (2025). "CpgD is a phosphoglycerate cytidylyltransferase required for ceramide diphosphoglycerate synthesis." Published version, with bioRxiv 2025.01.09.632243. PMID 39829823. PMC11741362. — defines CpgD as the cytidylyltransferase in CPG biosynthesis.
5. **Dhakephalkar T, Stukey GJ, Guan Z, Carman GM, Klein EA.** (2023). "Characterization of an evolutionarily distinct bacterial ceramide kinase from *Caulobacter crescentus*." *J Biol Chem* 299:104894. PMID 37286040. PMC10331486. — characterizes CpgB ceramide kinase (first step in CPG head-group biosynthesis).
6. **Olea-Ozuna RJ, Poggio S, … Geiger O.** (2020). "Five structural genes required for ceramide synthesis in *Caulobacter* and for bacterial survival." *Environ Microbiol* 23(5):2741. PMID 33063925. — establishes the ceramide/dihydroceramide biosynthetic pathway (incl. *spt*); sphingolipids required for stationary-phase survival and OM integrity.
7. **Olea-Ozuna RJ, Poggio S, … Geiger O.** (2024). "Genes required for phosphosphingolipid formation in *Caulobacter crescentus* contribute to bacterial virulence." *PLoS Pathog* 20(8):e1012401. PMID 39093898. PMC11324152. — extends the sphingolipid cluster to 11 genes; all required for membrane stability and polymyxin sensitivity.
8. **Hummels KR.** (2024). "mSphere of Influence: Celebrating exceptions to the rule of lipid A essentiality." *mSphere* 9(3):e00633-23. PMID 38421175. PMC10964400. — framing piece directly comparing the *Acinetobacter* (Boll lab, PG-remodeling route) and *Caulobacter* (Zik/Ryan, *fur* + sphingolipid route) cases. Useful comparative summary.
9. **Langklotz S, Schäkermann M, Narberhaus F.** (2011). "Control of LPS biosynthesis by FtsH-mediated proteolysis of LpxC is conserved in enterobacteria but not in all gram-negative bacteria." *J Bacteriol* 193(5):1090. PMID 21193611. PMC3067583. — shows FtsH-mediated LpxC proteolysis is NOT conserved in *C. crescentus*; relevant to whether LpxC accumulation/depletion dynamics differ.

### Theme B — ChvG-ChvI envelope stress (Hypothesis H1 anchor)

10. **Stein BJ, Fiebig A, Crosson S.** (2021). "The ChvG-ChvI and NtrY-NtrX Two-Component Systems Coordinately Regulate Growth of *Caulobacter crescentus*." *J Bacteriol* 203(15):e00199-21. PMID 34124942. PMC8351639. — defines the ChvI regulon in *Caulobacter*. (Already in the colleague's `clean/chvi_overexpression_regulon_stein_2021.csv`.)
11. **Quintero-Yanes A, Mayard A, Hallez R.** (2022). "The two-component system ChvGI maintains cell envelope homeostasis in *Caulobacter crescentus*." *PLoS Genet* 18(12):e1010465. PMID 36480504. PMC9731502. — independent ChvI regulon confirmation; OM/PG/IM targets. (Already in `clean/chvi_regulon_quintero_yanes_2022.csv`.)
12. **Greenwich JL, Heckel BC, Alakavuklar MA, Fuqua C.** (2023). "The ChvG-ChvI Regulatory Network: A Conserved Global Regulatory Circuit Among the Alphaproteobacteria with Pervasive Impacts on Host Interactions and Diverse Cellular Processes." *Annu Rev Microbiol* 77:339. PMID 37040790. — authoritative synthesis of ChvG-ChvI biology in alphaproteobacteria. Conceptual scaffold for H1.

Note from PaperBLAST: no snippet directly links ChvG-ChvI to the Δ*fur* Δ*lpxC* rescue in the Zik 2022 paper. H1 is plausible but not pre-established in the literature — it's an open question this data can address.

### Theme C — Caulobacter Fur regulon and iron biology (Hypothesis H2 anchor)

13. **Leaden L, Silva LG, … Marques MV.** (2018). "Iron Deficiency Generates Oxidative Stress and Activation of the SOS Response in *Caulobacter crescentus*." *Front Microbiol* 9:2014. PMID 30210482. PMC6120978. — RNA-seq of WT vs Δ*fur* under iron limitation: 256 up / 236 down DEGs. **Primary reference for the Caulobacter Fur regulon.** Not in `clean/` — author-provided DEG table referenced only by SRA SRP136695.
14. **da Silva Neto JF, Braz VS, Italiani VCS, Marques MV.** (2009). "Fur controls iron homeostasis and oxidative stress defense in the oligotrophic alpha-proteobacterium *Caulobacter crescentus*." *Nucleic Acids Res* 37(14):4812. PMID 19520766. — the earlier ChIP/microarray Caulobacter Fur regulon paper, frequently cited by the Klein/Ryan group.
15. **Dos Santos NM, Picinato BA, … Marques MV.** (2024). "Mapping the IscR regulon sheds light on the regulation of iron homeostasis in *Caulobacter*." *Front Microbiol* 15:1463854. PMID 39411446. PMC11475020. — IscR regulon (302 genes) with partial Fur overlap. Important for partitioning Fur-specific vs broader iron-regulon contributions.
16. **Hernandez-Ortiz S, Ok K, O'Halloran TV, Fiebig A, Crosson S.** (2025). "A co-conserved gene pair supports *Caulobacter* iron homeostasis during chelation stress." *J Bacteriol* 207(4):e00484-24. PMID 40084995. PMC12004947. — CciT (Fur-regulated TBDT) + CciO dioxygenase pair as core iron-acquisition module.
17. **de Castro Ferreira IG, Rodrigues MM, … Marques M.** (2016). "Role and regulation of ferritin-like proteins in iron homeostasis and oxidative stress survival of *Caulobacter crescentus*." *Biometals* 29(5):851. PMID 27484774. — Bfr/Dps ferritin regulation by Fur.
18. **Balhesteros H, Shipelskiy Y, … Marques MV, Klebba PE.** (2017). "TonB-Dependent Heme/Hemoglobin Utilization by *Caulobacter crescentus* HutA." *J Bacteriol* 199(6):e00723-16. PMID 28031282. PMC5331666. — Fur-regulated TBDTs (HutA et al.).
19. **Silva LG, Lorenzetti APR, … Marques MV.** (2019). "OxyR and the hydrogen peroxide stress response in *Caulobacter crescentus*." *Gene* 706:206. PMID 30880241. — OxyR/Fur cross-talk under H2O2.

### Theme D — Hopanoid biology in *Caulobacter* and alphaproteobacteria (Hypothesis H3 — superseded but biophysically relevant)

PaperBLAST returned **no hopanoid biosynthesis genes (*hpnH/hpnP/hpnG/shc*) annotated in Caulobacter** — H3 as originally framed (hopanoid substitution) is not supported by the literature, and the actual lipid substitute is anionic sphingolipid. These references are kept for biophysical context only.

20. **Belin BJ, Busset N, Giraud E, Molinaro A, Silipo A, Newman DK.** (2018). "Hopanoid lipids: from membranes to plant-bacteria interactions." *Nat Rev Microbiol* 16(5):304. PMID 29456243. PMC6087623. — *Nat Rev Microbiol* review of hopanoid biology and OM enrichment.
21. **Welander PV, Doughty DM, Wu CH, Mehay S, Newman DK.** (2012). "Identification and characterization of *Rhodopseudomonas palustris* TIE-1 hopanoid biosynthesis mutants." *Geobiology* 10(2):163. PMID 22221333. PMC3553210. — hopanoid-null α-proteobacterium has increased OM permeability.
22. **Tookmanian EM, Belin BJ, Saenz JP, Newman DK.** (2021). "The role of hopanoids in fortifying rhizobia against a changing climate." *Environ Microbiol* 23(6):2906. PMID 33989442.
23. **Pan H, Shim A, Lubin MB, Belin BJ.** (2024). "Hopanoid lipids promote Bradyrhizobium-soybean symbiosis." *mBio* 15(4):e02478-23. PMID 38445860. PMC11005386.

### Theme E — Cross-species lipid-A loss comparators (cross-organism arm of the project)

The colleague's question implicitly compares Caulobacter with the three other lipid-A-loss-tolerant Gram-negatives. None of them invokes Fur.

24. **Moffatt JH, Harper M, … Boyce JD.** (2010). "Colistin resistance in *Acinetobacter baumannii* is mediated by complete loss of lipopolysaccharide production." *Antimicrob Agents Chemother* 54(12):4971. PMID 20855724. PMC2981238. — original demonstration of LPS-null *A. baumannii* viability via *lpxA/lpxC/lpxD* mutations. **No Fur invoked.**
25. **Moffatt JH, Harper M, … Boyce JD.** (2011). "Insertion sequence ISAba11 is involved in colistin resistance and loss of lipopolysaccharide in *Acinetobacter baumannii*." *AAC* 55(6):3022. PMID 21402838. PMC3101452. — IS-driven *lpxA/lpxC* inactivation in clinical isolates.
26. **Kang KN, Kazi MI, … Boll JM.** (2021). "Septal Class A Penicillin-Binding Protein Activity and ld-Transpeptidases Mediate Selection of Colistin-Resistant LOS-Deficient *Acinetobacter baumannii*." *mBio* 12(1):e02185-20. PMID 33402533. PMC8545086. — *A. baumannii* uses PBP1A loss + LdtJ/LdtK PG-remodeling as the tolerance route — NOT Fur. Direct comparator that the Hummels 2024 commentary lines up against Caulobacter.
27. **Steeghs L, de Cock H, … van der Ley P.** (2001). "Outer membrane composition of a LPS-deficient *Neisseria meningitidis* mutant." *EMBO J* 20(24):6937. PMID 11742971. PMC125796. — canonical viable *lpxA*-null *N. meningitidis*; phospholipid remodeling; requirement for capsular polysaccharide. **No Fur.**
28. **van der Ley P, Steeghs L.** (2003). "Lessons from an LPS-deficient *Neisseria meningitidis* mutant." *J Endotoxin Res* 9(2):124. PMID 12803887. — companion review; notes reduced iron-limitation-inducible lipoproteins (the only oblique iron-connection in any of the three comparator species).
29. **Gao S, Peng D, … Gu XX.** (2008). "Identification of two late acyltransferase genes responsible for lipid A biosynthesis in *Moraxella catarrhalis*." *FEBS J* 275(20):5201. PMID 18795947. PMC2585779. — *lpxX/lpxL* late-acyltransferase mutants viable in *M. catarrhalis*. **No Fur.**
30. **Gao S, Ren D, Peng D, … Gu XX.** (2013). "Late acyltransferase genes *lpxX* and *lpxL* jointly contribute to the biological activities of *Moraxella catarrhalis*." *J Med Microbiol* 62(Pt 6):807. PMID 23475908. PMC3709554. — *lpxX lpxL* double mutant in *M. catarrhalis*.

### Theme F — ClpXP / SspB envelope connections (relevant because the strain carries Δ*sspB*)

31. **Flynn JM, Levchenko I, Sauer RT, Baker TA.** (2004). "Modulating substrate choice: the SspB adaptor delivers a regulator of the extracytoplasmic-stress response to the AAA+ protease ClpXP for degradation." *Genes Dev* 18(18):2292. DOI: 10.1101/gad.1240104 — SspB delivers RseA (anti-σE) to ClpXP; **directly couples SspB to envelope-stress (σE) signaling.** Important: this is *E. coli* — does the same logic apply in *Caulobacter*?
32. **Chowdhury T, Chien P, Ebrahim S, Sauer RT, Baker TA.** (2010). "Versatile modes of peptide recognition by the ClpX N domain mediate alternative adaptor-binding specificities in different bacterial species." *Protein Sci* 19(2):242. DOI: 10.1002/pro.306 — compares Caulobacter ClpX and SspB to E. coli; E. coli SspB can deliver substrates to Caulobacter ClpXP. Cross-species delivery is preserved.
33. **Bhat NH, Vass RH, Stoddard PR, Shin DK, Chien P.** (2013). "Identification of ClpP substrates in *Caulobacter crescentus* reveals a role for regulated proteolysis in bacterial development." *Mol Microbiol* 88(6):1083. PMID 23647068. — Caulobacter-direct ClpP substrate catalog (CtrA, GcrA, SocB, etc.); SspB is in the substrate set itself.

### Theme G — iModulons / ICA methodology (cross-reference for re-analysis tooling)

No published iModulon decomposition of *Caulobacter* exists. PRECISE-style ICA has been applied to *E. coli*, *S. enterica*, *S. aureus*, *B. subtilis*, *P. aeruginosa*, *M. tuberculosis*. This is a gap the BERDL Caulobacter expression compendium could address.

34. **Sastry AV, Gao Y, Szubin R, … Palsson BO.** (2019). "The *Escherichia coli* transcriptome mostly consists of independently regulated modules." *Nat Commun* 10:5536. DOI: 10.1038/s41467-019-13483-w — foundational iModulon paper; ICA on the *E. coli* RNA-seq compendium recovers regulator-aligned modules.
35. **Rychel K, Decker K, Sastry AV, Phaneuf PV, Poudel S, Palsson BO.** (2021). "iModulonDB: a knowledgebase of microbial transcriptional regulation derived from machine learning." *Nucleic Acids Res* 49(D1):D112. PMID 33045728. PMC7778901. — multi-organism iModulon knowledgebase; confirms no Caulobacter set exists yet.

### Other context

36. **Skerker JM, Perchuk BS, … Goulian M, Laub MT.** (2008). "Rewiring the specificity of two-component signal transduction systems." *Cell* 133(6):1043. PMID 18555780. PMC2453690. — context for the Caulobacter TCS regulatory landscape.

---

## Hypothesis evaluation against the literature (informs RESEARCH_PLAN.md)

| Original hypothesis | Status after lit review | What the data can still ask |
|---|---|---|
| **H1 — ChvG-ChvI envelope-stress route** | Plausible but NOT pre-established. PaperBLAST finds no snippet linking ChvG-ChvI to the Δ*fur* Δ*lpxC* rescue. Stein 2021 / Quintero-Yanes 2022 give the ChvI regulon as a reference set. | Test ChvI-regulon induction signal in the 4584/4599 strains versus baseline. If ChvI is strongly induced in 4584 (just Δ*fur* Δ*sspB*), then ChvI may participate; if only in 4599 (with Δ*lpxC*), it's a downstream consequence rather than a permissive condition. |
| **H2 — Iron-flux remodeling** | Re-frame from "iron status per se" to "specific Fur regulon targets." Zik 2022 explicitly says Fur-regulated **processes** (not iron status) matter. Leaden 2018 + da Silva Neto 2009 define the Caulobacter Fur regulon (~256 up / 236 down). | Identify which Fur regulon members are induced in 4584 and remain induced in 4599 — these are candidate "rescue genes." Need Leaden 2018 SRP136695 re-analyzed or use the published gene list. |
| **H3 — Alternative lipid substitution** | Re-frame: **NOT hopanoids — anionic sphingolipids (CPG).** CCNA_01212 / CCNA_01217-01223 (Olea-Ozuna 2020/2024) is the substitute-lipid pathway. CtpA/LpxE-like CCNA_03113 may substitute for LpxF. CpgB (Dhakephalkar 2023) and CpgD (Dhakephalkar 2025) are CPG biosynthesis enzymes. Uchendu 2026 (preprint) identifies an inner-membrane CPG transport complex. | Test sphingolipid-locus expression in the data — is it upregulated in 4584 or 4599? If yes, by how much, and in coordination with which other genes? OM proteome: do CPG-transport proteins (Uchendu 2026 candidates) appear at increased abundance in 4659/4672? |

## New question this dataset can actually address

Given the published mechanism, the value-add this dataset can provide is:

1. **Which sub-set of the Fur regulon is sufficient for *lpxC* rescue?** Not all Fur targets are equally important — the dataset can rank them by induction strength.
2. **Is the sphingolipid pathway transcriptionally induced** (vs. just permitted by Fur-mediated derepression of something else)? Olea-Ozuna 2020/2024 mapped the genes but did not characterize *fur*-dependent transcriptional control.
3. **Does ChvG-ChvI participate**, even if not strictly required, and if so does it cooperate or conflict with the Fur-released program?
4. **What does the OM remodel into at the protein level** — which OMPs gain/lose abundance in 4672 vs 4659 vs 4580? This is novel: Zik 2022 did not characterize the OM proteome.
5. **Comparative arm**: Why don't *A. baumannii / N. meningitidis / M. catarrhalis* need the equivalent rescue? Hypothesis: they lack the bacterial-ceramide-synthase locus entirely, so the rescue path is *structurally unavailable*; they have evolved unrelated routes (PG remodeling in *A. baumannii*, capsular substitution in *N. meningitidis*).

## Method failures to note

- PubMed `find_related_articles` returned API_ERROR for all 8 attempted top-10 PMIDs. Snowballing was completed via Google Scholar related-work instead.
- Direct bioRxiv search returned unrelated neuroscience content for every query — Scholar surfaced the Uchendu 2026 preprint.
- arXiv had zero hits for iModulon queries (methods aren't on arXiv).
