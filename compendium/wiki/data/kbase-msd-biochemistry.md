# KBase MSD Biochemistry

## Overview

The **KBase MSD Biochemistry** collection is the ModelSEED Database (MSD) biochemistry reference inside the BER Data Lakehouse (BERDL): a curated, shared vocabulary of biochemical compounds and reactions, each carrying a stable identifier (the familiar `cpd#####` compound and `rxn#####` reaction IDs) together with names, molecular formulas, and the enzymatic logic that links substrates to products. It is not the output of any single experiment. Instead it is the common metabolic coordinate system onto which many otherwise incompatible datasets — exometabolomic profiles, gene-fitness landscapes, draft metabolic models, and pangenome pathway predictions — are projected so they can be compared with one another. This page exists because seven independent BERDL projects, spanning soil and groundwater isolates, a soil model organism, cystic-fibrosis airway communities, and inflammatory-bowel-disease microbiomes, all lean on this same biochemistry reference to translate their organism- and assay-specific measurements into a single namespace of compounds and reactions. The collection is therefore best understood as connective tissue: the layer that lets a metabolite secreted by a groundwater *Pseudomonas* be matched to a reaction in a draft genome-scale model, and that reaction in turn to a gene flagged by a transposon-mutant fitness screen.

That connective role is also the source of the collection's main limitations, which several projects surface honestly. Mapping real measurements onto ModelSEED identifiers is frequently ambiguous. When a metabolite can only be matched to ModelSEED by its molecular formula rather than its exact name, the match is one-to-many and provides a candidate set for manual curation rather than a definitive compound identification — in one survey of Web of Microbes metabolites, only about 27% (69 compounds) resolved to a clean 1:1 ModelSEED link by name, while another ~42% matched by formula alone at an average of roughly eight ModelSEED molecules per formula, and a majority of the source metabolites were never identified at all. The biochemistry reference is precise where identifiers are exact and provisional where they are inferred, and downstream conclusions inherit that gradient of confidence.

## Projects Using This Collection

The seven projects use the MSD biochemistry layer in distinct but complementary ways, and reading them together shows what a shared compound/reaction namespace makes possible.

The **Acinetobacter ADP1 explorer** demonstrates the integration mechanics most directly. *Acinetobacter baylyi* ADP1 is a soil bacterium and a long-standing genetic model organism that is absent from the Fitness Browser, so its condition-specific mutant-growth data is a unique fitness resource within BERDL. The project ingests a multi-omics SQLite database (15 tables, ~462k rows) whose central genome-features table holds 5,852 genes annotated across six data modalities. Critically, four of five connection types between this database and BERDL collections matched at over 90% — including 100% of compound IDs and 91% of reactions — which is exactly the kind of deep coupling the MSD biochemistry reference enables: shared compound and reaction identifiers let the ADP1 data plug into the lakehouse even though a gene-junction table was needed to bridge cluster IDs that had 0% direct string overlap. On the biology side, the project finds core metabolism highly conserved (1,248 of 1,330 reactions shared across all 14 *Acinetobacter* genomes) and gene essentiality strongly media-dependent (499 essential genes on minimal media versus 346 on LB), with flux-balance-analysis (FBA, a constraint-based method that predicts metabolic flux through a genome-scale model) predictions agreeing with transposon-sequencing (TnSeq) essentiality calls for 73.8% of co-measured genes.

The **annotation-gap discovery** project uses MSD reactions as the unit of the problem it is trying to solve: the gapfilled reactions a draft model needs to grow, but for which no gene has been assigned. It integrates five evidence streams — gapfilling, gene fitness, pangenome conservation, GapMind pathway predictions, and BLAST homology — to assign candidate genes to these orphan reactions, resolving 47.8% (96 of 201) of gapfilled reaction-organism pairs and beating its pre-specified 30% threshold. No single stream sufficed (BLAST alone reached ~35%), and "dark reactions" lacking an EC number proved hardest, resolved only 16% of the time. Two branched-chain amino-acid biosynthesis reactions (rxn02185 and rxn03436) were independently resolved in 9 of 14 organisms, a co-resolution that validates the triangulation logic and supplies concrete CRISPRi knockout targets.

The **essential metabolome** project asks which biosynthetic pathways form a minimal metabolic repertoire for free-living bacteria, using GapMind (a tool that scores amino-acid and carbon-source pathway completeness from genomes) over a 7-organism pilot. It finds 17 of 18 amino-acid biosynthesis pathways present in all 7 organisms, suggesting amino-acid prototrophy is an ancestral state, with *Desulfovibrio vulgaris* the lone apparent serine auxotroph.

The **FW300 metabolic consistency** and **Web of Microbes (WoM) explorer** projects both center on exometabolomics — the metabolites bacteria secrete into and draw from their surroundings — and on reconciling that production data with gene fitness, utilization, and pathway databases through MSD compound identifiers. The WoM explorer characterizes a 2018 snapshot (589 metabolites across 37 ENIGMA-funded organisms) and quantifies exactly how well its metabolites map to ModelSEED. The FW300 project then pushes one organism, groundwater *Pseudomonas* FW300-N2E3, to four-way database concordance (0.94 mean), with malate, arginine, and valine reaching a "gold standard" of being produced, grown on, species-utilized, and computationally complete simultaneously. Its standout result is a production-versus-utilization discordance: FW300-N2E3 both secretes tryptophan and grows on it, while no BacDive *P. fluorescens* strain catabolizes it — a signature of overflow metabolism and a candidate for amino-acid cross-feeding in a community.

The **CF formulation design** project applies the same metabolic-overlap logic to engineer a therapeutic community. It designs a five-organism, FDA-safe commensal formulation that covers 100% of the amino-acid niche of *Pseudomonas aeruginosa* PA14 (the cystic-fibrosis airway pathogen) with 78% mean inhibition, the target pathways being 97.4% conserved across 1,796 lung PA genomes. No single commensal outgrows PA14 on any substrate, so competitive exclusion is necessarily a community-level property rather than a single dominant strain. The **IBD phage targeting** project works one layer up, stratifying 8,489 metagenomic samples into four reproducible microbiome ecotypes (E0–E3) and designing phage cocktails against Crohn's-disease pathobionts — a five-phage set covering 94.7% of 188 *E. coli* strains — while localizing iron-siderophore and genotoxin (colibactin) biology to the AIEC *E. coli* subset.

Across all seven, the recurring methodological caveats are worth taking seriously. Gapfilled-model predictions are fragile: 87% of ADP1's 121,519 growth-phenotype predictions depend on at least one gapfilled reaction, and FBA knockout validation in the annotation-gap project was structurally circular because models cannot grow on carbon-source minimal media without those same gapfilled reactions. Essentiality calls inherit assay conditions — biosynthetic genes can look non-essential when RB-TnSeq (random-barcode transposon sequencing, which measures mutant fitness across conditions) is run in nutrient-rich media. GapMind can miss divergent enzymes below its homology threshold, so the inferred *D. vulgaris* serine auxotrophy may be a detection artifact rather than real biology. Sampling biases run through the engineering projects too: PA14 is an ExoU+ strain representing under 5% of CF isolates, all its inhibition assays measure planktonic rather than biofilm competition, and the formulation's keystone species *Micrococcus luteus* has zero detected patient engraftability. The metabolic-feature model of inhibition overfits, dropping from a training R² of 0.27 to a cross-validated ~0.15. And the WoM data has a hard structural gap: its 2018 snapshot records production but no consumption, so it cannot test whether consumed metabolites predict gene essentiality. These uncertainties do not undercut the collection; they define the boundary between what its shared identifiers can and cannot yet support.

## Connections

The MSD biochemistry reference sits at the intersection of several cross-cutting topics in this wiki. Most directly, it underpins [Metabolic Pathways](../topics/metabolic-pathways.md), since every reaction and compound the projects analyze — from branched-chain amino-acid biosynthesis to TCA-cycle catabolism — is expressed in MSD terms; the annotation-gap and essential-metabolome work is fundamentally about completing and validating these pathways. It is paired tightly with [Gene Fitness](../topics/gene-fitness.md): the entire value proposition of the FW300, WoM, and ADP1 projects is mapping MSD compounds and reactions onto RB-TnSeq fitness data so that a secreted metabolite or a model reaction can be tied to the genes that matter for it.

The reference is also the proving ground for [Functional Dark Matter](../topics/functional-dark-matter.md): the "dark reactions" that lack EC numbers and the essential genes lacking KEGG KO assignments are exactly the unannotated functions these projects try to illuminate through evidence triangulation. Because pathway completeness is assessed across many genomes, the collection connects to [Pangenome Architecture](../topics/pangenome-architecture.md) — formulation traits are confirmed as species-level, conserved features across hundreds of genomes, and one open question is whether metabolic novelty rate tracks pangenome openness.

On the applied side, the CF formulation and IBD phage projects make this collection a foundation for [Microbiome Engineering](../topics/microbiome-engineering.md), using metabolic overlap to design competitive-exclusion communities and phage cocktails, while the IBD ecotype stratification ties into [Microbial Ecotypes](../topics/microbial-ecotypes.md). The ADP1 work anchors the [Adp1 Model System](../topics/adp1-model-system.md) page, and the groundwater and soil isolates that supply much of the exometabolomic and fitness data connect to [Subsurface Genomics](../topics/subsurface-genomics.md) and [Environment Biogeography](../topics/environment-biogeography.md). Finally, the AIEC siderophore-and-genotoxin gene-cluster signature links the IBD work to [Mobile Genetic Elements](../topics/mobile-genetic-elements.md), since those biosynthetic clusters are the genomic markers that define the actionable pathobionts.

## Sources

- [stmt:modelseed-definitive-links; webofmicrobes_explorer]
- [stmt:formula-matches-ambiguous; webofmicrobes_explorer]
- [stmt:database-scale-unidentified; webofmicrobes_explorer]
- [stmt:h1-partially-supported; webofmicrobes_explorer]
- [stmt:wom-no-consumption-data; webofmicrobes_explorer]
- [stmt:adp1-fitness-unique-resource; acinetobacter_adp1_explorer]
- [stmt:berdl-connectivity; acinetobacter_adp1_explorer]
- [stmt:adp1-multiomics-database; acinetobacter_adp1_explorer]
- [stmt:cluster-id-bridge; acinetobacter_adp1_explorer]
- [stmt:conserved-core-metabolism; acinetobacter_adp1_explorer]
- [stmt:essentiality-media-dependence; acinetobacter_adp1_explorer]
- [stmt:fba-tnseq-concordance; acinetobacter_adp1_explorer]
- [stmt:gapfilling-dependence; acinetobacter_adp1_explorer]
- [stmt:triangulation-resolves-48pct; annotation_gap_discovery]
- [stmt:no-single-stream-sufficient; annotation_gap_discovery]
- [stmt:dark-reactions-resist-resolution; annotation_gap_discovery]
- [stmt:bcaa-reactions-dominate; annotation_gap_discovery]
- [stmt:knockout-validation-inconclusive; annotation_gap_discovery]
- [stmt:aa-biosynthesis-high-conservation; essential_metabolome]
- [stmt:aa-prototrophy-ancestral; essential_metabolome]
- [stmt:dvh-serine-auxotrophy; essential_metabolome]
- [stmt:serine-gapmind-detection-caveat; essential_metabolome]
- [stmt:rich-media-essentiality-confound; essential_metabolome]
- [stmt:high-cross-database-concordance; fw300_metabolic_consistency]
- [stmt:four-way-concordant-metabolites; fw300_metabolic_consistency]
- [stmt:tryptophan-overflow-discordance; fw300_metabolic_consistency]
- [stmt:production-not-utilization; fw300_metabolic_consistency]
- [stmt:five-organism-formulation; cf_formulation_design]
- [stmt:formulation-target-invariant; cf_formulation_design]
- [stmt:no-single-organism-outgrows-pa14; cf_formulation_design]
- [stmt:metabolic-model-overfits; cf_formulation_design]
- [stmt:pa14-strain-bias-caveat; cf_formulation_design]
- [stmt:planktonic-only-caveat; cf_formulation_design]
- [stmt:m-luteus-engraftment-tension; cf_formulation_design]
- [stmt:four-ibd-ecotypes; ibd_phage_targeting]
- [stmt:five-phage-cocktail-coverage; ibd_phage_targeting]
- [stmt:ecoli-carries-iron-genotoxin; ibd_phage_targeting]
- [stmt:iron-acquisition-genomic; ibd_phage_targeting]
