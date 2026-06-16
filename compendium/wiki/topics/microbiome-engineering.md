# Microbiome Engineering

Microbiome engineering is the deliberate design of microbial communities — or of interventions against them — to achieve a defined outcome: excluding a pathogen from a niche, promoting plant growth, or selectively killing a disease-associated species. This page exists because that goal recurs across an unusually wide span of the corpus. Projects working on the cystic-fibrosis airway, the inflamed gut, the rhizosphere, contaminated subsurface groundwater, and the bacterial pangenome at large all converge on the same design questions: which organisms can be assembled into a stable community, which metabolic or genomic markers predict a useful function, and which targets can be hit without collateral damage. The page synthesizes what these otherwise-separate projects say about turning microbial ecology into engineerable practice, and where the underlying evidence is still thin.

## Overview

Three broad design strategies appear in the corpus, each grounded in a different mechanism. The first is **competitive exclusion** — assembling commensals that out-compete a pathogen for its nutrient niche so it cannot establish. The cystic-fibrosis (CF) formulation work pursues this against *Pseudomonas aeruginosa*, the dominant CF-lung pathogen. The second is **targeted removal** — using bacteriophages (viruses that infect specific bacteria) to selectively kill disease-associated strains while sparing the rest of the community, the approach the inflammatory bowel disease (IBD) phage work takes against Crohn's pathobionts (commensals that turn harmful in the diseased state). The third is **trait-marker discovery** — mining pangenomes for genomic signatures that predict a desirable phenotype, such as plant growth promotion, so that effective strains can be selected or designed rather than screened blindly.

Cutting across all three is a recurring lesson: useful microbial functions are rarely the property of a single organism. Competitive exclusion of *P. aeruginosa* requires community-level niche coverage rather than one dominant strain; phage cocktails must be matched to an individual patient's community state; and even the genetic determinants of plant benefit are distributed and context-dependent. The corpus repeatedly pushes the unit of engineering from the strain to the community.

## What the Corpus Shows

### Competitive exclusion in the cystic-fibrosis airway

The most fully developed example is the design of a commensal formulation to exclude *P. aeruginosa* strain PA14 from the CF airway. A central, repeatedly confirmed result is that **no single commensal can do the job**: no individual organism outgrows PA14 on any tested carbon substrate, so exclusion must come from community-level coverage of the pathogen's nutrient niche rather than from one superior competitor. PA14 also outgrows the average commensal on every tested amino acid and simple sugar, which closes off the obvious shortcut — there is no single substrate that selectively feeds the commensals while starving the pathogen.

The design therefore proceeds by coverage rather than dominance. Full coverage of PA14's amino-acid niche — at least one community member able to grow on every amino acid PA14 uses — is first reached with a three-organism set (*Micrococcus luteus*, *Neisseria mucosa*, *Streptococcus salivarius*). Extending this to a five-organism, FDA-safe formulation (adding *Rothia dentocariosa* and *Gemella sanguinis*) reaches 100% niche coverage with 78% mean inhibition of PA14 in planktonic assays. The mechanistic rationale is that **metabolic overlap predicts inhibition**: carbon-source overlap with PA14 is a significant predictor of how strongly a commensal suppresses it (r = 0.384), though it explains only about 27% of the variance — so overlap is real but far from the whole story.

Two refinements sharpen the strategy. First, timing may matter more than raw competitiveness: commensals rarely exceed PA14's maximum growth rate, but they begin growing before PA14 on 43% of substrate comparisons, suggesting that pre-establishing commensals before pathogen exposure (priority effects) is the lever to pull. Second, although no single amino acid or sugar is a selective prebiotic, genomic pathway comparison nominates **sugar alcohols** (xylitol, myo-inositol) and pentoses (xylose, arabinose, fucose, rhamnose) as candidate prebiotics the commensals can metabolize but PA14 cannot — a way to feed the protective community without feeding the pathogen.

Engraftment — whether a chosen organism actually persists in the patient — is treated as a first-class design constraint. Across 175 patient samples, *Neisseria mucosa* scores highest on engraftability (prevalence × log activity ratio), marking it the most promising colonization anchor, and two anchor species (*R. dentocariosa* and *N. mucosa*) are genuinely lung-adapted, with a third of their pangenome genomes drawn from respiratory sources rather than being gut commensals repurposed for the airway. Independently, *P. aeruginosa* itself retains near-universal amino-acid and organic-acid catabolism (>99% across subgenera), consistent with its using host amino acids to grow in CF sputum — which is precisely why amino-acid niche competition is a sensible point of attack.

### Phage cocktails for individualized gut targeting

The IBD work shifts from feeding a community to surgically removing members of it. A confound-controlled meta-analysis across four Crohn's-disease cohorts recovers the canonical signature — pathobionts up, protective commensals down — with strong sign concordance, confirming a stable set of targets. Among six actionable "Tier-A" pathobionts, iron acquisition emerges as a defining genomic capability: their genomes are strongly enriched for iron-siderophore biosynthetic gene clusters (siderophores are secreted iron-scavenging molecules), making iron acquisition a pathobiont-defining trait rather than merely a cohort-level pathway signal. That signal localizes sharply: only the adherent-invasive *E. coli* (AIEC) subset carries both the iron-siderophore and the colibactin genotoxin gene-cluster signature, pinning iron-driven Crohn's biology onto *E. coli*.

For *E. coli*, the engineering is tractable. A greedy minimum-set-cover design over experimentally measured phage–strain susceptibility yields a five-phage cocktail covering 94.7% of 188 *E. coli* strains in [PhageFoundry](../data/phagefoundry.md). The harder lesson is that cocktails cannot be designed once at the cohort level. Patients distribute non-randomly across distinct microbiome **ecotypes** (community-composition states), and clinical covariates can separate healthy from IBD samples but cannot tell the transitional (E1) from the severe (E3) ecotype apart — so metagenomic sequencing remains mandatory for assigning a patient before dosing. Worse, an individual's ecotype can drift between visits (Jaccard 0.60 between states), which argues for **state-dependent re-dosing** rather than a fixed prescription, and means cohort-level cocktails will mismatch individuals unless each patient's ecotype is typed first. For the transitional E1 state no pure phage cocktail is feasible at all; a hybrid combining phages with non-phage alternatives is required, because the two highest-priority targets — *H. hathewayi* and *M. gnavus* — have the weakest phage availability, leaving a coverage gap exactly where action is most needed.

### Genomic markers for plant-growth-promoting design

A third strand asks whether useful traits can be read directly from genomes, using plant-growth-promoting bacteria (PGPB) as the test case. Across 11,272 species carrying at least one PGP gene, the traits co-occur non-randomly, and *pqqC* (involved in mineral-phosphate solubilization) and *acdS* (ACC deaminase, which lowers plant stress ethylene) form the strongest positive pairing (odds ratio 7.24) — an apparently coherent "rhizosphere-effectiveness" module. This module is environment-selected: soil and rhizosphere habitats enrich *acdS* roughly sevenfold (OR 7.02) and *pqqC* (OR 2.90), with the *acdS* enrichment surviving phylum-level controls and a strict rhizosphere-only sensitivity analysis. The interpretation offered is that the canonical PGPB phenotype is a **stable, vertically inherited niche adaptation** rather than a recently acquired bolt-on trait package. Nitrogen fixation (*nifH*) sits outside this module — it is negatively associated with it — meaning diazotrophs form a separate ecological guild and the classical PGPB suite is primarily a non-diazotrophic phenotype. A finer metabolic predictor also appears: tryptophan-biosynthesis completeness predicts presence of *ipdC* (a gene in the auxin/IAA biosynthesis route), 2.5% vs 0.9% in trp-incomplete species (OR 2.81).

A parallel project warns that these benefits do not come cleanly separated from harm. Even after KEGG-module gating cut type-III-secretion-system false positives by 86% and narrowed the panel to 17 plant-specific markers, the **dual-nature rate** — species carrying both beneficial and pathogenic functions — rose to 78.7%, indicating genuine co-occurrence rather than annotation noise. The categorical "beneficial / pathogenic / dual" label is in fact uninformative: all 14 experimentally confirmed ground-truth species fall into the dual-nature class, so only a continuous pathogenicity ratio discriminates them (median 0.50 vs 0.60, p = 0.027). Architecturally, the explanation is that beneficial PGP gene clusters are predominantly core-genome-encoded (64.6% core) while pathogenic clusters are accessory (45.2% core) — a difference far exceeding the genome-wide baseline — so benefit is a conserved species property while pathogenicity rides on the mobile accessory genome.

### Targets, gene loss, and defense systems

Several projects feed the target-selection side of engineering. The essential-genome analysis tempers ambitions for broad-spectrum antibiotics: because most essential gene families are essential in only a minority of organisms, only the 859 *universally* essential families are reliable broad-spectrum targets — condition- and lineage-dependent essentiality undercuts the rest. The costly-dispensable-genes work flags genes that were acquired by horizontal gene transfer but impose enough fitness cost to be candidates for ongoing loss, marking unstable accessory functions that an engineered strain might shed. On the phage-defense side, the SNIPE (DUF4041) defense system was detected in a *Klebsiella* phage-therapy target, co-occurring with its mannose-PTS (ManYZ) transporter in the same genome — clinically relevant because such a defense could blunt phage-therapy efficacy in that pathogen. More broadly, anti-defense modules are enriched in human-associated bacteria beyond phylogenetic expectation (alongside tail and head-morphogenesis modules), and their depletion in freshwater and animal-associated niches points to host–phage coevolutionary arms races being most intense where bacterial immune systems are under strongest selection — directly relevant to whether phage interventions will hold up in the human niche.

Finally, the subsurface metabolic work supplies a cross-feeding building block. Production and utilization of a metabolite measure genuinely different capabilities — an organism can secrete a compound for ecological reasons without being able to catabolize it — and the strongest example is the groundwater isolate FW300-N2E3, which produces tryptophan and grows on it as a sole carbon source while no BacDive *P. fluorescens* strain can catabolize it. That overflow-metabolism discordance is a hallmark of cross-feeding potential: a prototroph that exports an essential amino acid is a natural feeder for auxotrophic community members, a primitive that any rational community design wants to exploit.

## Projects and Evidence

The evidence base spans twelve projects with very different methods and confidence levels. The **CF formulation design** project supplies the deepest single line of work — niche-coverage analysis, planktonic inhibition assays, growth kinetics, engraftability scoring, and genomic prebiotic prediction — and most of its core findings are high-confidence, though all rest on planktonic assays of a single strain. The **IBD phage targeting** project contributes the meta-analysis, ecotype classification, set-cover cocktail design, and the genomic iron signature, mixing high-confidence findings with medium-confidence individualized-dosing claims. The **PGP pangenome ecology** and **plant microbiome ecotypes** projects supply the trait-marker and dual-nature evidence from large pangenome surveys. Supporting projects — **essential genome** (broad-spectrum targets), **costly dispensable genes** (gene-loss candidates), **snipe defense system** (phage-defense in *Klebsiella*), **prophage ecology** (anti-defense biogeography), **fw300 metabolic consistency** and **pseudomonas carbon ecology** (cross-feeding and catabolic retention), **respiratory chain wiring** (the ADP1 NDH-2 case), and **microbeatlas metal ecology** (broad-niche resistant taxa) — each contribute one or a few statements that bear on a specific design decision. The breadth is the point: microbiome engineering here is an emergent theme assembled from projects that were not primarily about engineering.

## Connections

This page sits at the intersection of several more mechanistic topics, each of which supplies a piece of the engineering logic.

- [Metabolic Pathways](metabolic-pathways.md) is the most load-bearing neighbor: niche coverage, prebiotic selection, cross-feeding, and overflow metabolism are all metabolic-pathway analyses, and competitive exclusion is fundamentally a question of who can eat what.
- [Microbial Ecotypes](microbial-ecotypes.md) underpins the individualized-medicine thread — the IBD ecotype states that make cohort-level cocktails fail, and the patient-typing requirement, live there.
- [Pangenome Architecture](pangenome-architecture.md) explains why beneficial traits (core) and pathogenic traits (accessory) behave differently, and frames the *pqqC*/*acdS* module and costly-dispensable-gene results.
- [Mobile Genetic Elements](mobile-genetic-elements.md) connects the phage-cocktail, anti-defense, SNIPE, and iron-siderophore-gene-cluster strands — engineering with and against phages is engineering with mobile DNA.
- [Gene Fitness](gene-fitness.md) and the [Essential Genome](gene-fitness.md) reasoning constrain which targets are safely hittable; the [Adp1 Model System](adp1-model-system.md) supplies the respiratory-wiring test case for condition-dependent essentiality.
- [Environment Biogeography](environment-biogeography.md) grounds engraftment and habitat-selection arguments (lung-adapted anchors, soil enrichment of PGP genes), while [Metal Resistance](metal-resistance.md) and [Subsurface Genomics](subsurface-genomics.md) extend the engineering frame to environmental microcosms and groundwater cross-feeding.

## Caveats and Open Directions

The corpus is unusually candid about the limits of this work, and the caveats fall into a few clear groups.

**The assays are narrower than the claims.** Every CF inhibition measurement is planktonic, whereas PA14 grows primarily in lung biofilms where diffusion gradients and spatial structure change the competitive dynamics — so the inhibition numbers may not transfer. They were also all run on PA14, an ExoU+ Pel-only strain representing under 5% of CF isolates, leaving the dominant ExoS+/PAO1-type clinical strains untested. And the formulation is additive by assumption: the complete ten-pair interaction matrix of the five core species has not been measured, and a single antagonistic pair could invalidate the design, making that matrix the highest-priority validation. The sugar-alcohol prebiotic strategy is likewise genomic prediction that still needs the five core species plus PA14 tested on xylitol, myo-inositol, and the candidate pentoses.

**The most important member may not persist.** *M. luteus* is the keystone for full niche coverage yet has zero detected patient engraftability and no lung genomes — a real tension where the metabolically pivotal member is the least likely to colonize.

**Some predictions are simply untestable with current data.** The respiratory-chain prediction that NDH-2 loss makes Complex I essential cannot be tested directly because NDH-2 is absent from the ADP1 deletion collection and has no growth data, making it the weakest finding in that study; the proposed fix is to build an NDH-2 deletion mutant. Similarly, *Klebsiella*-specific SNIPE/ManYZ fitness data would require new mutant libraries that do not yet exist.

**Markers are presence-based, not expression-validated.** The dual-nature and PGP-module results rest on gene presence; RNA-seq under beneficial-versus-pathogenic conditions is needed to test whether the marker sets are actually co-expressed or differentially regulated. Whether co-occurring *pqqC* and *acdS* are physically linked on one operon or island — operon linkage versus independent co-selection — is also unresolved.

The forward-looking opportunities are correspondingly concrete: querying external phage databases (INPHARED, IMG/VR) to close the gut-anaerobe coverage gap and convert hybrid cocktails into pure-phage ones; building a reusable taxonomy-synonymy layer (NCBI taxid plus GTDB-version-aware rename table) that any multi-cohort microbiome project needs; parameterizing a community metabolic model from the FW300-N2E3 tryptophan-overflow finding to predict cross-feeding in the Oak Ridge groundwater community; testing the Black Queen Hypothesis (that organisms shed functions provided by neighbors) against ENIGMA CORAL co-occurrence data; cross-referencing the *pqqC*+*acdS*+*hcnC* signature against commercial inoculant strains to test whether it predicts field efficacy; running controlled microcosm metal-stress experiments on a shortlist of broad-niche resistant OTUs; and mining the genus dossiers and host-specificity matrix for crop-specific synthetic-community biocontrol designs. Several of these are low- or medium-confidence proposals rather than results, and should be read as a research agenda, not a set of established methods.

## Sources

- [stmt:no-single-organism-outgrows-pa14; cf_formulation_design]
- [stmt:no-selective-amino-acid-prebiotic; cf_formulation_design]
- [stmt:k3-full-niche-coverage; cf_formulation_design]
- [stmt:five-organism-formulation; cf_formulation_design]
- [stmt:metabolic-overlap-predicts-inhibition; cf_formulation_design]
- [stmt:lag-advantage-precolonization; cf_formulation_design]
- [stmt:sugar-alcohol-prebiotics; cf_formulation_design]
- [stmt:neisseria-mucosa-engraftability; cf_formulation_design]
- [stmt:anchor-species-lung-adapted; cf_formulation_design]
- [stmt:amino-acid-pathways-retained; pseudomonas_carbon_ecology]
- [stmt:canonical-cd-signature; ibd_phage_targeting]
- [stmt:iron-acquisition-genomic; ibd_phage_targeting]
- [stmt:ecoli-carries-iron-genotoxin; ibd_phage_targeting]
- [stmt:five-phage-cocktail-coverage; ibd_phage_targeting]
- [stmt:clinical-covariates-insufficient; ibd_phage_targeting]
- [stmt:ucdavis-spans-ecotypes; ibd_phage_targeting]
- [stmt:state-dependent-dosing; ibd_phage_targeting]
- [stmt:cohort-cocktail-mismatch; ibd_phage_targeting]
- [stmt:hybrid-cocktail-needed; ibd_phage_targeting]
- [stmt:pgp-syndrome-pqqc-acds-module; pgp_pangenome_ecology]
- [stmt:pqqc-acds-niche-marker-claim; pgp_pangenome_ecology]
- [stmt:soil-enriches-acds-pqqc; pgp_pangenome_ecology]
- [stmt:nifh-separate-guild; pgp_pangenome_ecology]
- [stmt:trp-completeness-predicts-ipdc; pgp_pangenome_ecology]
- [stmt:refined-panel-dual-nature-persists; plant_microbiome_ecotypes]
- [stmt:dual-nature-label-uninformative; plant_microbiome_ecotypes]
- [stmt:beneficial-core-pathogenic-accessory; plant_microbiome_ecotypes]
- [stmt:universal-essentials-only-broad-spectrum-targets; essential_genome]
- [stmt:ongoing-gene-loss-candidates; costly_dispensable_genes]
- [stmt:snipe-in-klebsiella-phage-therapy; snipe_defense_system]
- [stmt:structural-antidefense-human-enriched; prophage_ecology]
- [stmt:antidefense-arms-race-human-niche; prophage_ecology]
- [stmt:production-not-utilization; fw300_metabolic_consistency]
- [stmt:tryptophan-overflow-discordance; fw300_metabolic_consistency]
- [stmt:tryptophan-cross-feeding-candidate; fw300_metabolic_consistency]
- [stmt:planktonic-only-caveat; cf_formulation_design]
- [stmt:pa14-strain-bias-caveat; cf_formulation_design]
- [stmt:m-luteus-engraftment-tension; cf_formulation_design]
- [stmt:pairwise-interaction-gap; cf_formulation_design]
- [stmt:sugar-alcohol-validation-opportunity; cf_formulation_design]
- [stmt:phage-coverage-gap; ibd_phage_targeting]
- [stmt:external-phage-db-opportunity; ibd_phage_targeting]
- [stmt:synonymy-layer-reusable; ibd_phage_targeting]
- [stmt:caveat-ndh2-no-growth-data; respiratory_chain_wiring]
- [stmt:opportunity-ndh2-deletion-mutant; respiratory_chain_wiring]
- [stmt:opportunity-klebsiella-fitness-curation; snipe_defense_system]
- [stmt:transcriptomic-dual-nature-validation; plant_microbiome_ecotypes]
- [stmt:syncom-biocontrol-design; plant_microbiome_ecotypes]
- [stmt:pqqc-acds-operon-context-opportunity; pgp_pangenome_ecology]
- [stmt:inoculant-efficacy-opportunity; pgp_pangenome_ecology]
- [stmt:community-metabolic-modeling-opportunity; fw300_metabolic_consistency]
- [stmt:black-queen-community-opportunity; costly_dispensable_genes]
- [stmt:opportunity-microcosm-validation; microbeatlas_metal_ecology]
- [stmt:metabolic-versatility-hypothesis; microbeatlas_metal_ecology]
