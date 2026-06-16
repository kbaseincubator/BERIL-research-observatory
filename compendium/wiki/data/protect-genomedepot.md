# Protect GenomeDepot

## Overview

This page documents the **Protect GenomeDepot** collection: the shared store of bacterial and viral genomes, pangenomes, and genome-derived annotations that two otherwise unrelated microbiome-engineering projects both draw on. GenomeDepot is, in essence, the genomic substrate behind both efforts — the reference genomes used to compute pangenome conservation, the per-genome metabolic-pathway calls used to reason about who can eat what, and the biosynthetic-gene-cluster and effector signatures used to classify strains. The page exists in this wiki because that genomic layer is the concrete artifact that links a [cystic fibrosis](../topics/environment-biogeography.md) airway formulation project to a gut [inflammatory bowel disease](../topics/microbial-ecotypes.md) phage-targeting project: different diseases, different body sites, different therapeutic modalities, but the same style of evidence — claims grounded in genome-scale comparisons rather than in a handful of isolates.

A scientist reading this should understand the two recurring genomic methods. The first is **pangenome analysis**: rather than judging a species from one genome, these projects pool hundreds to thousands of genomes and ask which metabolic traits are *conserved* across the whole set versus variable. The second is **GapMind**, a tool that reconstructs which catabolic pathways (for amino acids and carbon sources) a genome encodes, letting the projects predict metabolic capability directly from sequence. Together these support a key methodological stance shared by both projects: treat metabolic and pathogenic capabilities as **species-level traits** and design interventions that are *strain-agnostic* — robust to the genomic diversity GenomeDepot reveals — rather than tuned to a single isolate.

The two projects use the collection in mirror-image ways. The CF project mines pangenomes to argue that a competitive-exclusion formulation will work across lung *Pseudomonas* diversity; the IBD project mines metagenome-derived genomes and viral databases to argue that a phage cocktail must be matched to a patient's microbiome state. Both ultimately use genomic evidence to expose where a tidy intervention breaks down.

## Projects Using This Collection

### CF formulation design — competitive exclusion of *Pseudomonas aeruginosa*

The [cf_formulation_design](../topics/microbiome-engineering.md) project designs a defined consortium of commensal bacteria intended to outcompete *Pseudomonas aeruginosa* in the cystic fibrosis airway by metabolic **competitive exclusion** — collectively consuming the nutrients PA depends on. GenomeDepot supplies the genomic backbone for both the design and its central justification.

The metabolic logic begins with what PA itself does in the lung. Lung-adapted *P. aeruginosa* undergoes **metabolic streamlining**: in the amino-acid-rich sputum environment, sugar-catabolism pathways are lost under relaxed selection, while amino-acid catabolism is preserved as an invariant evolutionary adaptation. That observation reframes the target — the formulation should compete for amino acids, not sugars. Crucially, the amino-acid catabolic pathways the formulation targets are **97.4% conserved across 1,796 lung PA genomes**, so a single formulation is predicted to suppress PA equivalently across lung variants, including CF-derived strains. This pangenome-scale invariance is the strongest argument that one design can generalize.

The consortium itself is built from metabolic-niche reasoning. No individual commensal outgrows PA14 on any tested carbon substrate, so competitive exclusion requires **community-level niche coverage** rather than one dominant strain. Full coverage of PA14's amino-acid niche is first reached by a three-organism set (*M. luteus*, *N. mucosa*, *S. salivarius*), where at least one member can grow on every amino acid PA14 uses. The proposed clinical candidate is a **five-organism FDA-safe formulation** (*Neisseria mucosa*, *Streptococcus salivarius*, *Micrococcus luteus*, *Rothia dentocariosa*, *Gemella sanguinis*) achieving 100% amino-acid niche coverage with 78% mean inhibition. GapMind pangenome analysis across 499 genomes confirms these species' metabolic capabilities are species-level traits conserved above 95%, supporting strain-agnostic design. Two anchor species — *Rothia dentocariosa* and *Neisseria mucosa* — are naturally lung-adapted, with 33–38% of their pangenome genomes from respiratory sources, so they are not gut commensals being forced into the airway; and across 175 patient samples, *N. mucosa* has the highest engraftability score, marking it the most promising colonization anchor.

The genomic layer also informs adjuncts and strategy. Metabolic carbon-source overlap with PA14 significantly predicts planktonic inhibition (r = 0.384), giving a mechanistic handle on why some commensals inhibit better — though it explains only ~27% of the variance. Comparing pathways genome-by-genome identifies candidate **prebiotics** — sugar alcohols (xylitol, myoinositol) and pentoses (xylose, arabinose, fucose, rhamnose) — that formulation commensals can metabolize but PA14 cannot, a route to selectively feed the consortium. Growth kinetics add nuance: commensals rarely beat PA14's maximum growth rate, but they start growing first on 43% of substrates, suggesting **pre-colonization** before pathogen exposure may matter more than raw growth rate.

These conclusions come with honest, well-flagged limits. Every inhibition assay measures only **planktonic competition**, whereas PA14 actually grows in CF-lung biofilms where diffusion gradients and spatial structure differ substantially. The reference strain itself is unrepresentative: **PA14 is an ExoU+ strain**, and T3SS effector typing across 6,760 PA genomes shows CF isolates are overwhelmingly ExoS+ (94%), so PA14 reflects only ~5% of CF *P. aeruginosa* — the measured inhibition has not been validated against the dominant clinical strains. The keystone species *Micrococcus luteus* is essential for full niche coverage yet has zero detected patient engraftability and no lung genomes, an unresolved tension between metabolic importance and persistence. The multivariate inhibition model **overfits** the 142-isolate cohort (cross-validated R² ≈ 0.145 versus training 0.274), so its real out-of-sample power is near 15%. No single tested substrate works as a selective prebiotic either: PA14 outgrows the average commensal on every amino acid and simple sugar tested. The two priority validations follow directly: experimentally testing the five species plus PA14 on the candidate sugar-alcohol prebiotics, and measuring the full **10-pair interaction matrix** among the five species, since a single antagonistic pair could invalidate the additive design.

### IBD phage targeting — patient-matched phage cocktails

The [ibd_phage_targeting](../topics/microbiome-engineering.md) project designs bacteriophage cocktails to remove pathobionts from the gut in inflammatory bowel disease, using genome-derived metagenomic profiles and viral databases. Here the collection underpins both the disease-signature analysis and the cocktail-design logic, and again the genomic evidence mostly argues *against* a one-size-fits-all therapy.

The disease signal is recovered carefully. In pooled metagenomic data, healthy and Crohn's samples come from disjoint source studies, which makes a naive case-vs-control model structurally **unidentifiable** and forces a within-substudy CD-vs-nonIBD design. Done that way, a confound-free meta-analysis across four cohorts recovers the canonical Crohn's signature — **pathobionts up, protective commensals down** — with strong sign concordance. Two independent clustering methods over 8,489 samples converge on four reproducible **microbiome ecotypes** (E0–E3), and these [ecotypes](../topics/microbial-ecotypes.md) turn out to be clinically load-bearing: clinical covariates can separate healthy from IBD but cannot distinguish the transitional E1 from the severe E3 ecotype, so metagenomics remains required for ecotype assignment. In the 23-patient UC Davis Crohn's cohort, patients distribute non-randomly across three ecotypes (none in the Prevotella E2), with active disease concentrated in E1 and E3.

Genomic annotation localizes the mechanism. Tier-A pathobiont genomes are strongly enriched for **iron-siderophore biosynthetic gene clusters**, making iron acquisition a pathobiont-defining genomic capability rather than just a cohort-level pathway signal. Within that group, only *E. coli* (the AIEC subset) carries both the iron-siderophore and the genotoxin (**colibactin**) gene-cluster signature, pinning the iron-and-genotoxin Crohn's biology specifically to *E. coli*. On the viral side, the Microviridae member **Gokushovirus WZ-2015a** is robustly depleted in Crohn's across ecotypes, strongest in the transitional E1.

The cocktail design uses [mobile genetic elements](../topics/mobile-genetic-elements.md) — phages — as the therapeutic agent. A greedy minimum **set-cover** over experimentally tested phage-strain susceptibility yields a 5-phage cocktail covering 94.7% of 188 *E. coli* strains. But the genomic reality complicates clean prescription. The two highest-priority Crohn's targets, *H. hathewayi* and *M. gnavus*, have the **weakest phage availability**, creating a coverage gap precisely for the most actionable species; consequently no E1 Crohn's patient can be treated with a pure phage cocktail, and only a **hybrid** combining phages with non-phage alternatives is feasible. Cohort-level cocktails will mismatch individual patients unless each patient's ecotype is determined first, and because a single patient's ecotype can drift between E1 and E3 across visits (Jaccard 0.60), the project argues for **state-dependent** cocktail re-design rather than a fixed prescription. The E3 Tier-A target list, resting on single-study evidence, is flagged as provisional until a cohort with enough E3 patients and both diagnosis groups exists. Two forward-looking opportunities round this out: querying external phage databases (**INPHARED**, **IMG/VR**) for gut-anaerobe phages to close the *H. hathewayi* / *F. plautii* / *M. gnavus* gap, and building a reusable **taxonomy synonymy layer** (NCBI taxid plus a GTDB-version-aware rename table) that any multi-cohort microbiome project needs.

## Connections

The collection sits at the intersection of several wiki topics, which is why those pages backlink here. Both projects rest on [Pangenome Architecture](../topics/pangenome-architecture.md): the CF project's claim of one-formulation-fits-all hinges on amino-acid pathways being conserved across 1,796 lung PA genomes, and on GapMind confirming formulation-species traits across 499 genomes. [Metabolic Pathways](../topics/metabolic-pathways.md) is the shared analytic currency — carbon- and amino-acid-catabolism calls drive niche-coverage and prebiotic reasoning in CF and iron-acquisition reasoning in IBD. [Microbial Ecotypes](../topics/microbial-ecotypes.md) connects the IBD ecotype clustering to the strain-type stratification of PA (ExoS+ vs ExoU+). [Mobile Genetic Elements](../topics/mobile-genetic-elements.md) covers both the phages used as therapeutics and the biosynthetic gene clusters (siderophores, colibactin) and T3SS effectors used as genomic markers. [Microbiome Engineering](../topics/microbiome-engineering.md) is the unifying goal — rationally reshaping a microbial community — and [Environment Biogeography](../topics/environment-biogeography.md) captures the body-site adaptation evidence (respiratory-source pangenome fractions, engraftability across patient samples). The collection and its analyses are attributed to [0000 0002 4999 2931](../authors/0000-0002-4999-2931.md).

## Sources

- [stmt:pa-lung-metabolic-streamlining; cf_formulation_design]
- [stmt:formulation-target-invariant; cf_formulation_design]
- [stmt:no-single-organism-outgrows-pa14; cf_formulation_design]
- [stmt:k3-full-niche-coverage; cf_formulation_design]
- [stmt:five-organism-formulation; cf_formulation_design]
- [stmt:metabolic-traits-species-level; cf_formulation_design]
- [stmt:anchor-species-lung-adapted; cf_formulation_design]
- [stmt:neisseria-mucosa-engraftability; cf_formulation_design]
- [stmt:metabolic-overlap-predicts-inhibition; cf_formulation_design]
- [stmt:sugar-alcohol-prebiotics; cf_formulation_design]
- [stmt:lag-advantage-precolonization; cf_formulation_design]
- [stmt:planktonic-only-caveat; cf_formulation_design]
- [stmt:pa14-strain-bias-caveat; cf_formulation_design]
- [stmt:pa14-not-representative-cf; cf_formulation_design]
- [stmt:m-luteus-engraftment-tension; cf_formulation_design]
- [stmt:metabolic-model-overfits; cf_formulation_design]
- [stmt:no-selective-amino-acid-prebiotic; cf_formulation_design]
- [stmt:sugar-alcohol-validation-opportunity; cf_formulation_design]
- [stmt:pairwise-interaction-gap; cf_formulation_design]
- [stmt:substudy-nesting-unidentifiable; ibd_phage_targeting]
- [stmt:canonical-cd-signature; ibd_phage_targeting]
- [stmt:four-ibd-ecotypes; ibd_phage_targeting]
- [stmt:clinical-covariates-insufficient; ibd_phage_targeting]
- [stmt:ucdavis-spans-ecotypes; ibd_phage_targeting]
- [stmt:iron-acquisition-genomic; ibd_phage_targeting]
- [stmt:ecoli-carries-iron-genotoxin; ibd_phage_targeting]
- [stmt:gokushovirus-cd-down; ibd_phage_targeting]
- [stmt:five-phage-cocktail-coverage; ibd_phage_targeting]
- [stmt:phage-coverage-gap; ibd_phage_targeting]
- [stmt:hybrid-cocktail-needed; ibd_phage_targeting]
- [stmt:cohort-cocktail-mismatch; ibd_phage_targeting]
- [stmt:state-dependent-dosing; ibd_phage_targeting]
- [stmt:e3-tier-a-provisional; ibd_phage_targeting]
- [stmt:external-phage-db-opportunity; ibd_phage_targeting]
- [stmt:synonymy-layer-reusable; ibd_phage_targeting]
