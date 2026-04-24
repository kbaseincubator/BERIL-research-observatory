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
   *ANCOM-BC — one of the three compositional DA methods we will apply in NB04.*

## IBD multi-omics cohorts

7. **Lloyd-Price J et al. (2019).** "Multi-omics of the gut microbial ecosystem in inflammatory bowel diseases." *Nature* 569(7758):655–662. PMID: 31142855.  
   *HMP2 / IBDMDB primary cohort paper — the external-validation cohort we will add in NB02 when MetaPhlAn3 is ingested.*

8. **Vujkovic-Cvijin I et al. (2020).** "Host variables confound gut microbiota studies of human disease." *Nature* 587(7834):448–454. PMID: 33149306.  
   *Demonstrates that pooled multi-cohort microbiome DA is confounded by host variables (age, diet, geography) — our H1c finding is a concrete instance.*

## Pathobionts / mechanism

9. **Henke MT et al. (2019).** "Ruminococcus gnavus, a member of the human gut microbiome associated with Crohn's disease, produces an inflammatory polysaccharide." *Proc Natl Acad Sci USA* 116(26):12672–12677. PMID: 31182571.  
   *Molecular mechanism (glucorhamnan / TLR4 activation) for R. gnavus pathogenicity. Tier-A candidate anchor.*

10. **Darfeuille-Michaud A et al. (2004).** "High prevalence of adherent-invasive Escherichia coli associated with ileal mucosa in Crohn's disease." *Gastroenterology* 127(2):412–421. PMID: 15300573.  
    *AIEC canonical clinical-association paper for ileal CD. Informs E. coli strain-level Tier-A scoring (NB05).*

## Project-specific data sources (referenced in dim_studies)

11. **Elmassry MM et al. (2025).** [Biosynthetic Gene Cluster catalog of the human gut microbiome; Cell Host & Microbe — full citation in `dim_studies`]. Source of `ref_bgc_catalog` (10,060 BGCs) and `ref_cborf_enrichment` (5,157 CB-ORFs) used in Pillar 3.

12. **Kumbhari A et al. (2024).** [Strain-frequency and gene-level adaptation of IBD-associated species; full citation in `dim_studies`]. Source of `ref_kumbhari_s7_*` strain-level supplementary tables (432 strains × 6,138 samples). Provides strain-resolution inputs for Pillar 2 and 3.

## Still-to-be-read (will expand at project completion)

The synthesis here covers Pillar 1. A full literature review over Pillars 2–5 — in particular published IBD pathobiont target lists, FMT response studies, phage therapy clinical trials (EcoActive / BiomX), and bile-acid / TMA/TMAO / sulfidogenesis mechanism papers — will be added in the next synthesis pass, after NB04–NB14.
