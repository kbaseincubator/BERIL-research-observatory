# References — ibd_phage_targeting

Papers cited in `REPORT.md` and `RESEARCH_PLAN.md`, with identifiers for easy follow-up.

## Ecotype / enterotype framework

1. **Arumugam M et al. (2011).** "Enterotypes of the human gut microbiome." *Nature* 473(7346):174–180. PMID: 21508958.  
   *Original enterotype paper (Bacteroides / Prevotella / Ruminococcus clustering). Motivates the K=4 framework used here.*

2. **Costea PI et al. (2018).** "Enterotypes in the landscape of gut microbial community composition." *Nat Microbiol* 3(1):8–16. PMID: 29255284.  
   *Argues enterotypes are gradients rather than hard clusters; justifies the ~49 % cross-method agreement we observe.*

3. **Vandeputte D et al. (2017).** "Quantitative microbiome profiling links gut community variation to microbial load." *Nature* 551(7681):507–511. PMID: 29143816.  
   *Defines the Bacteroides2 (Bact2) dysbiosis subtype, which corresponds to our E1 / E3 ecotypes.*

## Methods

4. **Holmes I, Harris K, Quince C. (2012).** "Dirichlet multinomial mixtures: generative models for microbial metagenomics." *PLoS One* 7(2):e30126. PMID: 22319561.  
   *DMM, the canonical ecotype-discovery method. Our LDA-on-pseudo-counts is the sklearn-compatible equivalent.*

5. **Gloor GB, Macklaim JM, Pawlowsky-Glahn V, Egozcue JJ. (2017).** "Microbiome datasets are compositional: and this is not optional." *Front Microbiol* 8:2224. PMID: 29187837.  
   *Motivates CLR transformation and compositional-aware DA — the norm-N1 foundation.*

6. **Lin H, Peddada SD. (2020).** "Analysis of compositions of microbiomes with bias correction." *Nat Commun* 11(1):3514. PMID: 32665548.  
   *ANCOM-BC — one of the three compositional DA methods originally planned for NB04.*

6b. **Tsilimigras MC, Fodor AA. (2016).** "Compositional data analysis of the microbiome: fundamentals, tools, and challenges." *Ann Epidemiol* 26(5):330–335. PMID: 27255738.  
   *Compositional-data fundamentals; spurious-correlation warning. Motivates our layered CLR + permutation-null + independent-contrast design.*

6c. **Zhou H, He K, Chen J, Zhang X. (2022).** "LinDA: linear models for differential abundance analysis of microbiome compositional data." *Genome Biology* 23(1):95. PMID: 35421994.  
   *LinDA — linear CLR regression with median-based bias correction. Used in NB04c §4 as the second-method concordance check for within-ecotype DA. Implemented in pure NumPy for this project (~20 lines) to avoid the rpy2/R dependency that blocked our attempted ANCOM-BC run.*

## IBD multi-omics cohorts

7. **Lloyd-Price J et al. (2019).** "Multi-omics of the gut microbial ecosystem in inflammatory bowel diseases." *Nature* 569(7758):655–662. PMID: 31142855.  
   *HMP2 / IBDMDB primary cohort paper — the external-validation cohort we will add in NB02 when MetaPhlAn3 is ingested.*

8. **Vujkovic-Cvijin I et al. (2020).** "Host variables confound gut microbiota studies of human disease." *Nature* 587(7834):448–454. PMID: 33149306.  
   *Demonstrates that pooled multi-cohort microbiome DA is confounded by host variables (age, diet, geography) — our H1c finding is a concrete instance.*

## Pathobionts / mechanism

9. **Henke MT et al. (2019).** "Ruminococcus gnavus, a member of the human gut microbiome associated with Crohn's disease, produces an inflammatory polysaccharide." *Proc Natl Acad Sci USA* 116(26):12672–12677. PMID: 31182571.  
   *Molecular mechanism (glucorhamnan / TLR4 activation) for R. gnavus pathogenicity. Tier-A candidate anchor. M. gnavus is the top hit in E1 Tier-A (+4.85 CLR-Δ), E3 Tier-A (+4.46), and cross-ecotype engraftment-confirmed set (+5.13).*

9b. **Dalmasso G, Nguyen HTT, Faïs T, et al. (2021).** "Yersiniabactin siderophore of Crohn's disease-associated adherent-invasive Escherichia coli." *Int J Mol Sci* 22(7):3512. PMID: 33805299.  
    *Direct mechanism for the NB05 A6 Yersiniabactin MIBiG match on E. coli — AIEC siderophore function.*

9c. **Prudent V et al. (2021).** "The Crohn's disease-related bacterial strain LF82 assembles biofilm-like communities to protect itself from phagolysosomal attack." *Commun Biol* 4(1). PMID: 34035436.  
    *AIEC LF82 yersiniabactin iron-capture pathway required for intracellular bacterial-community formation and macrophage survival.*

9d. **Dogan B et al. (2014).** "Inflammation-associated adherent-invasive Escherichia coli are enriched in pathways for use of propanediol and iron and M-cell translocation." *Inflamm Bowel Dis* 21(1):92-111. PMID: 25230163.  
    *AIEC iron (yersiniabactin) pathway enrichment across CD, dog granulomatous colitis, and mouse ileitis.*

9e. **Dubinsky V et al. (2022).** "Escherichia coli strains from patients with inflammatory bowel diseases have disease-specific genomic adaptations." *J Crohns Colitis* 16(9):1484-1497. PMID: 35560165.  
    *IBD-specific E. coli lineages — confirms species-level E. coli CD-association has genomic sub-structure.*

9f. **Veziant J et al. (2016).** "Association of colorectal cancer with pathogenic Escherichia coli: focus on mechanisms using optical imaging." *World J Clin Oncol* 7(3):293-302. PMID: 27298769.  
    *pks+ E. coli colibactin mechanism in colorectal pathology — relevant to NB05 A6 Colibactin MIBiG match.*

9g. **Galtier M et al. (2017).** "Bacteriophages targeting adherent-invasive Escherichia coli strains as a promising new treatment for Crohn's disease." *J Crohns Colitis* 11(7):840-847. PMID: 28130329.  
    *Direct phage therapy precedent for CD targeting AIEC via CEACAM6 receptor. Validates Pillar 4 strategy with E. coli as primary example.*

10. **Darfeuille-Michaud A et al. (2004).** "High prevalence of adherent-invasive Escherichia coli associated with ileal mucosa in Crohn's disease." *Gastroenterology* 127(2):412–421. PMID: 15300573.  
    *AIEC canonical clinical-association paper for ileal CD. Informs E. coli strain-level Tier-A scoring (NB05).*

10b. **Le PH, Yeh YM, Chen YC, Chen CL, et al. (2025).** "Fecal microbiota transplantation for vancomycin-resistant Clostridium innocuum infection in inflammatory bowel disease: A pilot study evaluating safety and clinical and microbiota outcome." *J Microbiol Immunol Infect*. PMID: 40074633.  
    *Establishes C. innocuum (= Erysipelatoclostridium innocuum) as a vancomycin-resistant IBD pathobiome with distinct CD and UC phenotypes (creeping-fat, strictures in CD; reduced UC remission). E. innocuum is rank 4 in our E1 Tier-A with independent clinical-association evidence — the candidate with the strongest standalone case for NB05 prioritization.*

## Oral-gut axis in IBD (context for the E1 Tier-A streptococci)

10c. **Xiang B, Hu J, Zhang M, Zhi M. (2024).** "The involvement of oral bacteria in inflammatory bowel disease." *Gastroenterol Rep (Oxf)* 12:goae076. PMID: 39188957.  
    *Review of oral-derived gut colonization in IBD, including oral-gut axis, metabolic alterations, and ectopic colonization by oral species.*

10d. **Guo Y, Kitamoto S, Caballero-Flores G, et al. (2024).** "Oral pathobiont-derived metabolites promote IBD." *Gut Microbes* 16(1):2333463. PMID: 38545880.  
    *Mechanism paper for ectopic gut colonization by oral pathobionts in IBD pathogenesis.*

10e. **Tanwar H, Gnanasekaran JM, Allison D, et al. (2023).** "Unraveling the link between periodontitis and inflammatory bowel disease: challenges and outlook." *Cells* 12. PMID: 37645044.  
    *Oral-gut axis review — periodontitis ↔ IBD bidirectional relationship.*

10f. **Goel RM, Prosdocimi EM, Amar A, et al. (2019).** "Streptococcus salivarius: A potential salivary biomarker for orofacial granulomatosis and Crohn's disease?" *Inflamm Bowel Dis*. PMID: 30796823.  
    *Specific S. salivarius evidence in OFG + CD — the rank-2 candidate in our E1 Tier-A.*

## Polyphenol / urolithin metabolism (context for ambiguous E1 candidate G. pamelaeae)

10g. **Selma MV, Tomás-Barberán FA, Beltrán D, et al. (2014).** "Gordonibacter urolithinfaciens sp. nov., a urolithin-producing bacterium isolated from the human gut." *Int J Syst Evol Microbiol* 64:2346–2352. PMID: 24744017.  
    *Establishes G. pamelaeae's urolithin-production role from ellagitannins.*

10h. **Tierney BT, Van den Abbeele P, Al-Ghalith GA, et al. (2023).** "Capacity of a Microbial Synbiotic to Rescue the in vitro Metabolic Activity of the Gut Microbiome Following Perturbation with Alcohol or Antibiotics." *Appl Environ Microbiol* 89(3):e01880-22. PMID: 36840551.  
    *G. pamelaeae increases during microbiome recovery from dysbiosis-inducing insults. Rationale for the "ambiguous CD-associated" flag on G. pamelaeae in our E1 Tier-A — CD↑ signal may reflect opportunity rather than pathobiont activity; requires NB05 A4 protective-analog exclusion.*

## Module-anchor commensals (NB06 pathobiont-module butyrate-producers)

10i. **Geirnaert A, Wang J, Tinck M, et al. (2015a).** "Interindividual differences in response to treatment with butyrate-producing Butyricicoccus pullicaecorum 25-3T studied in an in vitro gut model." *FEMS Microbiol Ecol* 91(6):fiv054. PMID: 25999470.  
     *B. pullicaecorum as candidate butyrate-producing probiotic for IBD — provides the anti-inflammatory-commensal framing for the NB06 E3 pathobiont-module anchor finding.*

10j. **Steppe M et al. (2014).** "Safety assessment of the butyrate-producing Butyricicoccus pullicaecorum strain 25-3T, a potential probiotic for patients with inflammatory bowel disease, based on oral toxicity tests and whole genome sequencing." *Food Chem Toxicol* 72:129-37. PMID: 25007784.  
     *B. pullicaecorum IBD-probiotic safety profile + genome sequence — establishes the reference strain.*

10k. **Jeraldo P et al. (2016).** "Capturing one of the human gut microbiome's most wanted: reconstructing the genome of a novel butyrate-producing, clostridial scavenger from metagenomic sequence data." *Front Microbiol* 7:783. PMID: 27303377.  
     *Novel B. pullicaecorum-related species (71-76 % ANI) assembled from HMP metagenomes; occupies host-dependent nutrient-scavenging niche. Relevant to the "metabolic partner" interpretation of the NB06 pathobiont-module anchor role.*

## Phage therapy / FMT precedent

10l. **Sheikh IA, Bianchi-Smak J, Laubitz D, et al. (2024).** "Transplant of microbiota from Crohn's disease patients to germ-free mice results in colitis." *Gut Microbes* 16(1):2333483. PMID: 38532703.  
     *CD-patient microbiome -> germ-free mouse causally sufficient for colitis (discontinued pattern, proximal colonic localization). Supports Pillar-4/5 premise that compositional modification can have therapeutic effect.*

10m. **Barbour A et al. (2023).** "Discovery of phosphorylated lantibiotics with proimmune activity that regulate the oral microbiome." *Proc Natl Acad Sci USA* 120(23):e2219392120. PMID: 37216534.  
     *Lantibiotic bacteriocin class regulates oral microbiome with proimmune activity. Relevant to NB05 Salivaricin MIBiG matches on S. salivarius — suggests the A6 signal has both antimicrobial (bacteriocin) and proimmune-modulation components.*

## Project-specific data sources (referenced in dim_studies)

11. **Elmassry MM et al. (2025).** [Biosynthetic Gene Cluster catalog of the human gut microbiome; Cell Host & Microbe — full citation in `dim_studies`]. Source of `ref_bgc_catalog` (10,060 BGCs) and `ref_cborf_enrichment` (5,157 CB-ORFs) used in Pillar 3.

12. **Kumbhari A et al. (2024).** [Strain-frequency and gene-level adaptation of IBD-associated species; full citation in `dim_studies`]. Source of `ref_kumbhari_s7_*` strain-level supplementary tables (432 strains × 6,138 samples). Provides strain-resolution inputs for Pillar 2 and 3.

## Still-to-be-read (will expand at project completion)

The synthesis here covers Pillar 1 + rigor-controlled Pillar 2. A full literature review over Pillars 3–5 — in particular published IBD pathobiont target lists, FMT response studies, phage therapy clinical trials (EcoActive / BiomX), and bile-acid / TMA/TMAO / sulfidogenesis mechanism papers — will be added in the next synthesis pass, after NB05–NB14.

Pillar 2 literature grounding added in plan v1.4 post-NB04-rigor-repair synthesis: oral-gut axis (Xiang 2024, Guo 2024, Tanwar 2023), *E. innocuum* clinical association (Le 2025), *S. salivarius* salivary biomarker (Goel 2019), urolithin metabolism and ambiguous-CD-association flag (Selma 2014, Tierney 2023), compositional-data and LinDA methodology (Tsilimigras & Fodor 2016, Zhou 2022). Additional NB05-relevant papers on the Clostridiales-expansion candidates (*Intestinibacter bartlettii*, *Hungatella symbiosa*, *Enterocloster asparagiformis*) will land in a follow-up pass once NB05 A3 literature-grounding is run.
