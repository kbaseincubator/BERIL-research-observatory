# Gene Fitness

**Gene fitness** is the measurable contribution of an individual gene to an organism's growth under a defined condition. In bacteria, the dominant way to measure it at genome scale is RB-TnSeq (Random-Barcode Transposon Sequencing): a transposon is inserted at thousands of positions across the chromosome, each insertion is tagged with a DNA barcode, and the change in barcode abundance after growth tells you how much each gene mattered. A gene whose disruption hurts growth has a negative fitness score (it is "important"); a gene whose disruption is harmless scores near zero ("neutral"); and a gene whose disruption *helps* growth scores positive (a "burden" under that condition). Genes that cannot be disrupted at all without killing the cell are called essential. This page exists because gene fitness is the connective tissue running through a large fraction of the compendium: many projects use the same public fitness resource — the [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md), which holds RB-TnSeq data for roughly 48 diverse bacteria and archaea — and join it against pangenome conservation, annotation, AMR, metabolism, and field ecology. Reading those projects side by side surfaces a coherent, sometimes counterintuitive picture of which genes matter, why they are conserved, and how badly lab phenotypes proxy for natural selection.

## Overview

The organizing insight across the corpus is that **fitness importance and evolutionary conservation are linked, but the relationship is a continuous gradient rather than a clean essential/dispensable dichotomy**. Joining the Fitness Browser to the [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) — gene-cluster conservation across tens of thousands of microbial species — repeatedly shows that the conserved "core" genome is not the inert housekeeping backbone of textbooks but the most functionally active part of the genome, carrying the largest fitness effects in both the important and the burdensome direction. More important genes are more conserved, but the effect is modest, and conservation is better predicted by mundane covariates (like gene length) than by lab fitness alone.

The second organizing theme is **honest skepticism about the lab**. RB-TnSeq is a powerful but biased instrument: it measures one library-construction condition, in lab-adapted strains, biased toward culturable Proteobacteria, and it conflates fitness cost with lethality. Several projects find that laboratory conditions are an impoverished proxy for natural selection — a gene that looks costly in rich media may be essential in soil, biofilm, or host tissue — and this single idea resolves a recurring paradox in the data: why genes that selection clearly preserves can look like dead weight on a plate.

## What the Corpus Shows

**A fitness-conservation gradient, and the burden paradox.** Across 194,216 protein-coding genes in 43 bacteria, conservation declines smoothly from essential genes (about 82% core) to always-neutral genes (about 66% core), so importance predicts conservation but weakly. The striking twist is the *burden paradox*: core genes are MORE likely than accessory genes to show positive fitness when deleted (24.4% versus 19.9% ever beneficial), the opposite of the genome-streamlining model that casts accessory genes as the metabolic burden. The excess is function-specific — driven by motility/chemotaxis, RNA metabolism, and protein metabolism, and reversed for cell-wall genes — and it resolves once lab conditions are read as a poor proxy for nature: flagellar machinery is costly to build on a plate but essential for chemotaxis in the wild. Crossing lab fitness cost against pangenome conservation yields a selection-signature matrix in which 28,017 costly-but-conserved genes are the strongest evidence for purifying selection in natural environments, while 5,526 costly-and-dispensable genes look like candidates for ongoing gene loss. Consistent with the gradient view, genes important across more conditions, and genes with strong *condition-specific* phenotypes, are both more likely to be core — counter to the naive expectation that condition-specific genes would be accessory.

**Essentiality is context-dependent, not absolute.** Defining essentiality as the absence of viable transposon mutants, putative essential genes are modestly enriched in core clusters (median odds ratio ~1.56). But essentiality itself is mostly conditional: across 48 organisms only 859 of 17,222 ortholog families (5.0%) are universally essential, just fifteen families (ribosomal proteins plus groEL, pyrG, fusA, valS) are essential in every organism, and the largest single class is *variably* essential — essential in some organisms, dispensable in others. Conservation breadth tracks essentiality (universal essentials are 91.7% core; orphan essentials only 49.5%), and the most uncharacterized essential genes are the ones lacking orthologs anywhere, a frontier of unknown essential biology.

**Co-fitness organizes the genome into modules.** Robust Independent Component Analysis (rICA) decomposes fitness matrices into latent functional modules — sets of genes whose fitness rises and falls together across conditions. Across 32 organisms this yields 1,116 stable modules with strongly elevated within-module cofitness (mean |r| 0.34 vs 0.12 background) and 22.7x genomic-adjacency enrichment, confirming many modules are operons. Modules are core-enriched (86% core vs 81.5% baseline), extending the pangenomic notion of "core" from single genes to coherent regulatory units, and they support function prediction: adding PFam domains lifted the module annotation rate from 8% to 80% and generated thousands of hypothesis for hypothetical proteins. Cofitness also weakly predicts co-inheritance (co-fit gene pairs tend to co-occur across genomes), though the pairwise effect is small — lab-measured coupling explains only a tiny fraction of what is inherited together.

**Methods measure different things.** A deep dive on *Acinetobacter baylyi* ADP1 — uniquely paired here with a genome-wide deletion collection — shows that knockout lethality, FBA, RB-TnSeq, proteomics, and mutant growth each capture a distinct facet of importance. Continuous RB-TnSeq fitness is the best single predictor of true essentiality (AUC 0.70–0.73), FBA is a useful first-pass screen (Cohen's kappa ~0.49), but RB-TnSeq *systematically disagrees* with knockout essentiality (it captures fitness cost, not lethality). ADP1's own phenotype landscape is a continuum, not discrete modules, with carbon sources spanning a demanding-to-robust tier structure (urea most demanding, quinate most robust).

## Projects and Evidence

The Fitness Browser is the shared substrate, and projects fan out from it into distinct biological questions.

**Conservation and selection.** A cluster of projects — `conservation_fitness_synthesis`, `core_gene_tradeoffs`, `conservation_vs_fitness`, `fitness_effects_conservation`, and `costly_dispensable_genes` — establish the gradient, the burden paradox, and the selection-signature matrix described above, repeatedly mapping Fitness Browser genes to pangenome clusters (e.g. 177,863 DIAMOND links for 44 organisms, ~82% landing in core clusters). They converge on the same interpretation: the conserved genome is functionally active, and lab burden is offset by environmental essentiality. See [Pangenome Architecture](pangenome-architecture.md) for the core/accessory framework these joins depend on.

**Module structure.** `fitness_modules` and `module_conservation` build and validate the rICA modules, while `cofitness_coinheritance` and `amr_cofitness_networks` test what cofitness predicts — co-occurrence across genomes, and the neighborhood structure of antibiotic-resistance genes, respectively.

**The ADP1 model system.** `adp1_deletion_phenotypes`, `adp1_triple_essentiality`, `acinetobacter_adp1_explorer`, `respiratory_chain_wiring`, and `aromatic_catabolism_network` exploit a deletion collection absent from the Fitness Browser. They cross-validate essentiality methods and dissect ADP1's branched respiratory chain: three parallel NADH dehydrogenases (Complex I, NDH-2, ACIAD3522) are constitutively co-expressed yet used condition-dependently as a passive flux-based system, and a counterintuitive result — quinate yields fewer NADH per carbon yet makes Complex I *more* essential — is resolved by a concentrated TCA-cycle NADH burst from aromatic ring cleavage exceeding NDH-2's reoxidation capacity. See [Adp1 Model System](adp1-model-system.md).

**Antibiotic resistance.** `amr_fitness_cost` and `amr_cofitness_networks` ask what resistance costs. The answer is a small but universal cost: AMR knockouts have systematically higher fitness than non-AMR knockouts under non-antibiotic conditions (pooled +0.086, positive in all 25 organisms), the cost does not vary by mechanism, and ~57% of AMR genes show a fitness "flip" toward importance under antibiotic. This reconciles the long persistence of resistance after antibiotic withdrawal with its measurable cost. See [Amr Resistome](amr-resistome.md).

**Metals and stress.** `counter_ion_effects`, `lab_field_ecology`, and `bacdive_phenotype_metal_tolerance` use fitness data to dissect metal stress. A central control finding is that metal–NaCl fitness overlap (39.8% of metal-important records) reflects shared stress biology rather than the chloride counter-ion — zinc sulfate (zero chloride) overlaps with NaCl more than most chloride salts — so counter-ions are not the driver. See [Metal Resistance](metal-resistance.md).

**Function discovery and metabolism.** `functional_dark_matter`, `truly_dark_genes`, `essential_genome`, `pathway_capability_dependency`, `fw300_metabolic_consistency`, and `genotype_to_phenotype_enigma` use fitness as a lever on the unknown. A census of 48 organisms finds 57,011 genes (24.9%) lacking annotation, of which 17,344 have measurable phenotypes — the actionable dark matter — and cross-species synteny plus cofitness yields 998 double-validated dark-gene/operon pairs, the highest-confidence predictions. Pathway analysis reframes genomic "latency": all 66 Latent Capability pathway-organism pairs become fitness-important under at least one condition, so genome completeness does not equal active dependency. See [Functional Dark Matter](functional-dark-matter.md) and [Metabolic Pathways](metabolic-pathways.md).

## Connections

Gene fitness is a hub topic, so most of its neighbors are pages whose phenomena it directly measures or constrains.

- [Pangenome Architecture](pangenome-architecture.md) — nearly every conservation result here is a join of fitness scores against core/accessory gene-cluster classifications; the two topics are mutually defining.
- [Adp1 Model System](adp1-model-system.md) — the single organism where deletion, FBA, proteomics, and RB-TnSeq can be compared head to head, making it the testbed for what "fitness" actually measures.
- [Amr Resistome](amr-resistome.md) — fitness data supply the cost-of-resistance estimate and the antibiotic-induced fitness flip.
- [Functional Dark Matter](functional-dark-matter.md) — measurable fitness effects on unannotated genes are what make dark matter *actionable* and prioritizable.
- [Metabolic Pathways](metabolic-pathways.md) — condition-specific fitness recovers metabolic architecture from phenotype alone and tests which complete pathways are truly used.
- [Metal Resistance](metal-resistance.md) — metal fitness profiles separate genuine metal-specific responses from shared ionic/osmotic stress.
- [Environment Biogeography](environment-biogeography.md) and [Microbial Ecotypes](microbial-ecotypes.md) — the lab-to-field bridge, where fitness phenotypes are tested against real community distributions, lives at the boundary of these pages.
- [Mobile Genetic Elements](mobile-genetic-elements.md) — costly-and-dispensable genes carry hallmarks of recently acquired, on-their-way-out mobile DNA.

The primary evidence source is [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md), joined repeatedly against [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md), [Kbase Genomes](../data/kbase-genomes.md), and [Enigma Coral](../data/enigma-coral.md) field data.

## Caveats and Open Directions

The corpus is unusually disciplined about the limits of fitness data, and these caveats should temper every conclusion above.

**RB-TnSeq is not gene deletion, and not lethality.** Transposon insertion can leave partial protein function, so some knockout-essential genes look TnSeq-dispensable, and RB-TnSeq systematically captures fitness cost rather than lethality — making it a poor lethality proxy in absolute terms even where it is the best continuous predictor. Relatedly, a binary "essentiality fraction" aggregated across many conditions performs *worse than random* against knockout truth (AUC 0.34–0.40) and should not be used as a classifier.

**One condition, biased organisms.** Essentiality here reflects a single library-construction condition, so stress-only essentials are invisible; the ~48 organisms skew toward culturable, lab-adapted Proteobacteria, so patterns in underrepresented lineages remain uncertain. Lab condition types are chosen for experimental convenience, not ecological relevance, which is exactly why the burden paradox needs the "lab as impoverished proxy" reading rather than a literal one.

**Statistical ceilings and confounds.** Because most well-characterized bacteria are mostly core, core-enrichment effects run into ceiling effects, and co-inheritance signals are throttled by a prevalence ceiling (most fitness-mapped genes are >95% prevalent, leaving little presence/absence variance). Gene length confounds both fitness measurement quality and core status, and in at least one analysis gene length predicts core status better than fitness does. ICA modules exclude essential genes entirely (they lack insertions), so module-level conclusions cover only the non-essential genome. Cofitness implies shared phenotype, not transcriptional co-regulation, so enrichment in cofitness neighborhoods can reflect shared experimental context. The synthesis layer is honest about its own seams: a reported 16-percentage-point gradient has a Figure-1-versus-text discrepancy, and essential-gene core rates are quoted as both 82% and 86% without full reconciliation.

**Specific weak spots.** The cross-species NDH-2 compensation prediction cannot be tested directly because NDH-2 is absent from the deletion collection and has no growth data — the study's own weakest finding. The only within-metal counter-ion comparison (CuCl2 vs CuSO4 in psRCH2) is confounded by aerobic/anaerobic growth. AMR cost estimates may be lower bounds because lab adaptation can have erased compensable cost in maintained strains.

**Open directions.** The most repeated next step is to validate lab-derived sets against natural conditions — testing the costly-but-conserved genes in soil or biofilm, and connecting fitness to environmental data such as AlphaEarth to ask whether organisms from more variable niches carry more trade-off genes in their core. Module-transfer and dark-gene function predictions are framed as directly testable by CRISPRi knockdown under the implied conditions, with a dual-route campaign (evidence-weighted vs conservation-weighted) proposed to characterize dark matter efficiently. And a definitive NDH-2 deletion mutant in ADP1 would settle the respiratory-wiring question that the data could only infer.

## Sources

- [stmt:dual-dataset-synthesis; conservation_fitness_synthesis]
- [stmt:fitness-conservation-gradient; conservation_fitness_synthesis]
- [stmt:selection-signature-purifying; conservation_fitness_synthesis]
- [stmt:burden-paradox-core-more-costly; conservation_fitness_synthesis]
- [stmt:fitness-modules-core-enriched; conservation_fitness_synthesis]
- [stmt:burden-paradox-function-specific; conservation_fitness_synthesis]
- [stmt:lab-impoverished-proxy; conservation_fitness_synthesis]
- [stmt:core-burden-paradox-claim; core_gene_tradeoffs]
- [stmt:motility-case-study-finding; core_gene_tradeoffs]
- [stmt:tradeoff-genes-core-enriched-finding; core_gene_tradeoffs]
- [stmt:continuous-not-binary-claim; fitness_effects_conservation]
- [stmt:breadth-predicts-conservation; fitness_effects_conservation]
- [stmt:specific-phenotype-genes-core; fitness_effects_conservation]
- [stmt:essential-genes-enriched-in-core; conservation_vs_fitness]
- [stmt:essentiality-tracks-core-conservation; essential_genome]
- [stmt:five-percent-universally-essential; essential_genome]
- [stmt:variable-essentiality-is-norm; essential_genome]
- [stmt:fifteen-pan-essential-families; essential_genome]
- [stmt:1116-stable-modules; fitness_modules]
- [stmt:cofitness-enrichment-validation; fitness_modules]
- [stmt:pfam-boosts-annotation-rate; fitness_modules]
- [stmt:module-genes-enriched-core; module_conservation]
- [stmt:cofit-predicts-cooccurrence; cofitness_coinheritance]
- [stmt:small-effect-size; cofitness_coinheritance]
- [stmt:fitness-best-essentiality-predictor; adp1_triple_essentiality]
- [stmt:rbtnseq-systematic-discordance; adp1_triple_essentiality]
- [stmt:fba-moderate-ko-concordance; adp1_triple_essentiality]
- [stmt:adp1-three-tier-landscape; adp1_deletion_phenotypes]
- [stmt:condition-specific-respiratory-wiring; respiratory_chain_wiring]
- [stmt:quinate-complex-i-paradox-flux-rate; respiratory_chain_wiring]
- [stmt:metal-nacl-overlap; counter_ion_effects]
- [stmt:counter-ions-not-driver; counter_ion_effects]
- [stmt:amr-universal-cost; amr_fitness_cost]
- [stmt:amr-mechanism-no-cost-difference; amr_fitness_cost]
- [stmt:dark-gene-census-actionable; functional_dark_matter]
- [stmt:synteny-cofit-validation; functional_dark_matter]
- [stmt:field-stress-genes-more-conserved; field_vs_lab_fitness]
- [stmt:gene-length-stronger-than-fitness; field_vs_lab_fitness]
- [stmt:46k-pairs-for-mechanistic-prediction; genotype_to_phenotype_enigma]
- [stmt:lab-tolerance-not-significant-field-ratio; lab_field_ecology]
- [stmt:latent-conditionally-active; pathway_capability_dependency]
- [stmt:manyz-not-fructose-transporter; snipe_defense_system]
- [stmt:transposon-not-deletion-caveat; adp1_triple_essentiality]
- [stmt:single-condition-caveat; conservation_vs_fitness]
- [stmt:lab-condition-bias-caveat; core_gene_tradeoffs]
- [stmt:taxonomic-bias-caveat; essential_genome]
- [stmt:figure1-text-discrepancy; conservation_fitness_synthesis]
- [stmt:essentiality-fraction-worse-than-random; adp1_triple_essentiality]
- [stmt:cofitness-not-coregulation; amr_cofitness_networks]
- [stmt:amr-lab-adaptation-bias; amr_fitness_cost]
- [stmt:prevalence-ceiling-caveat; cofitness_coinheritance]
- [stmt:caveat-ndh2-no-growth-data; respiratory_chain_wiring]
- [stmt:psrch2-confounded; counter_ion_effects]
- [stmt:essential-genes-absent; module_conservation]
- [stmt:natural-condition-validation-opportunity; core_gene_tradeoffs]
- [stmt:opportunity-alphaearth-environment; conservation_fitness_synthesis]
- [stmt:crispri-validation-opportunity; essential_genome]
- [stmt:dual-route-experimental-campaign; functional_dark_matter]
- [stmt:opportunity-ndh2-deletion-mutant; respiratory_chain_wiring]
