# PhageFoundry

## Overview

PhageFoundry is a shared BERDL data collection of experimentally measured
phage–host susceptibility: a matrix recording which bacteriophages can
productively infect which bacterial strains. Where most genomic resources only
predict that a phage *might* target a host from sequence similarity,
PhageFoundry encodes the empirical answer — phage X plates on strain Y or it
does not. That distinction is what makes the collection valuable as a wiki
page: it is the empirical backbone that turns "design a phage therapy" from a
sequence-matching exercise into a coverage-optimization problem over real
infectivity data.

The collection's most direct use is in the IBD phage-targeting work, where a
greedy minimum-set-cover design over the experimentally tested phage–strain
susceptibility in PhageFoundry yields a five-phage cocktail covering 94.7% of
188 *E. coli* strains. Set-cover is the natural framing here: each phage covers
some subset of strains, and the goal is the smallest cocktail that covers as
many strains as possible. PhageFoundry supplies the ground-truth coverage that
the optimizer consumes.

But PhageFoundry does not stand alone. It is one node in a constellation of
BERDL data collections — RB-TnSeq fitness datasets, GapMind pangenome
metabolic reconstructions, curated metagenomic cohorts, and multi-omics strain
databases — that four otherwise independent projects all reach into. This page
exists to explain why those projects are adjacent: they share not just a data
lake but overlapping methods (fitness profiling, pangenome conservation
analysis, set-cover and niche-coverage optimization) and overlapping biology
(host range, [gene fitness](../topics/gene-fitness.md), and
[pangenome architecture](../topics/pangenome-architecture.md)). Read together,
they sketch a workflow: characterize a microbe's genes and metabolism, place
those traits in a pangenome to judge how general they are, then design an
intervention — a phage cocktail, a probiotic formulation, or an engineered
defense — whose feasibility is bounded by the empirical coverage data
collections like PhageFoundry provide.

A recurring, honestly-surfaced limitation runs through every project that
touches this data: experimental coverage is sparse and biased. The two
highest-priority Crohn's pathobiont targets, *H. hathewayi* and *M. gnavus*,
have the *weakest* phage availability — exactly the most actionable species sit
in the coverage gap. The proposed remedy is to query external phage databases
(INPHARED and IMG/VR) for gut-anaerobe phages, which could close that gap and
convert a hybrid phage-plus-alternative framework into a pure-phage cocktail
for some patients. This tension — rich empirical data where it exists, blank
spaces where it does not — is the through-line connecting PhageFoundry to the
projects below.

## Projects Using This Collection

### IBD phage targeting

The [microbiome-engineering](../topics/microbiome-engineering.md) project that
leans most heavily on PhageFoundry treats Crohn's disease as an ecosystem to be
re-engineered with phages. Two independent clustering methods on 8,489
metagenomic samples converge on four reproducible IBD microbiome ecotypes
(E0–E3), and a confound-free within-substudy CD-vs-nonIBD meta-analysis across
four cohorts recovers the canonical Crohn's signature — pathobionts up,
protective commensals down. These [microbial ecotypes](../topics/microbial-ecotypes.md)
matter operationally because clinical covariates can separate healthy from IBD
samples but cannot distinguish the transitional E1 from severe E3 ecotype, so
metagenomics remains required for ecotype assignment, and a cohort-level
cocktail will mismatch individual patients unless each patient's ecotype is
determined first. A single patient's ecotype can even drift between E1 and E3
between visits (Jaccard 0.60), motivating state-dependent re-design rather than
a fixed prescription.

On the genomic side, the project ties Crohn's biology to specific
[mobile genetic elements](../topics/mobile-genetic-elements.md) and
biosynthetic capabilities. Tier-A pathobiont genomes are strongly enriched for
iron-siderophore biosynthetic gene clusters, and among the six actionable
Tier-A pathobionts only *E. coli* (the AIEC subset) carries the combined
iron-siderophore and genotoxin signature, localizing iron-driven Crohn's
biology to *E. coli*. On the viral side, the Microviridae member Gokushovirus
WZ-2015a is robustly depleted in Crohn's, strongest in the transitional E1
ecotype — a phage signal rather than a bacterial one.

The caveats here are substantial and stated plainly. In pooled
curatedMetagenomicData, healthy and Crohn's samples come from disjoint source
studies, making a pooled case-vs-control model structurally unidentifiable and
forcing the within-substudy design. The E3 Tier-A target list rests on
single-study evidence and is explicitly provisional. And the coverage gap
already noted — the most actionable pathobionts having the least phage data —
means no E1 Crohn's patient can be treated with a pure phage cocktail today;
only a hybrid combining phages with non-phage alternatives is feasible. A
reusable taxonomy synonymy layer (NCBI taxid plus a GTDB-version-aware rename
table) is flagged as a foundation any multi-cohort microbiome project needs.

### CF formulation design

The cystic-fibrosis formulation project shares PhageFoundry's design philosophy
— suppress a pathogen by engineering its competitors — but swaps phages for a
defined commensal community. The target is *Pseudomonas aeruginosa* in the
CF airway, and the strategy is competitive exclusion through
[metabolic pathway](../topics/metabolic-pathways.md) overlap. No individual
commensal outgrows PA14 on any tested carbon substrate, so exclusion requires
community-level niche coverage rather than a single dominant strain. Full
amino-acid niche coverage is first reached at a three-organism formulation
(*M. luteus*, *N. mucosa*, *S. salivarius*), and a five-organism FDA-safe
formulation achieves 100% coverage of PA14's amino-acid niche with 78% mean
inhibition. Metabolic carbon-source overlap with PA14 significantly predicts
planktonic inhibition (r = 0.384) but explains only about 27% of the variance,
so overlap is a real but partial driver.

Pangenome reasoning makes the design strain-agnostic, the same logic
PhageFoundry-adjacent projects use to judge generality. The amino-acid
catabolic pathways the formulation targets are 97.4% conserved across 1,796
lung PA genomes, and GapMind pangenome analysis across 499 genomes confirms the
formulation species' capabilities are species-level traits conserved above 95%.
Lung-adapted PA undergoes metabolic streamlining — losing sugar-catabolism
pathways under relaxed selection in amino-acid-rich sputum while keeping amino
acid catabolism as an invariant adaptation — which is precisely why an
amino-acid-targeted formulation should generalize across the
[environment-biogeography](../topics/environment-biogeography.md) of lung
strains. Two anchor species, *Rothia dentocariosa* and *Neisseria mucosa*, are
themselves naturally lung-adapted (33–38% of their pangenome genomes from
respiratory sources), and *N. mucosa* has the highest engraftability score
among inhibition-tested species. Genomic pathway comparison also nominates
sugar alcohols (xylitol, myoinositol) and pentoses as candidate selective
prebiotics the commensals can metabolize but PA14 cannot.

The caveats again temper the optimism. All inhibition assays measure planktonic
competition, whereas PA14 grows primarily in CF-lung biofilms with very
different spatial and diffusion dynamics; all assays used PA14, an ExoU+
Pel-only strain representing under 5% of CF isolates, while T3SS effector
typing of 6,760 genomes shows CF isolates are overwhelmingly ExoS+ (94%). The
multivariate metabolic-feature model overfits its 142-isolate cohort
(cross-validated R² near 0.145 versus training 0.274). And *M. luteus*, the
keystone for full niche coverage, has zero detected patient engraftability and
no lung genomes — the most metabolically important member is the least likely
to persist. The highest-priority validations are measuring the complete 10-pair
interaction matrix of the five core species and testing them plus PA14 on the
predicted prebiotic sugar alcohols.

### Acinetobacter ADP1 explorer

The ADP1 explorer is the project that most clearly demonstrates *why*
collections like PhageFoundry need to be integrated into BERDL rather than
standing alone. It centers on the [Adp1 model system](../topics/adp1-model-system.md)
— *Acinetobacter baylyi* ADP1 — and integrates a user-provided SQLite database
of 15 tables (461,522 rows; central genome_features table of 5,852 genes with
51 annotation columns spanning six modalities). Because ADP1 is absent from the
Fitness Browser, its condition-specific mutant growth data is a unique
[gene fitness](../topics/gene-fitness.md) resource not available elsewhere in
BERDL, paralleling PhageFoundry's role as a one-of-a-kind empirical collection.

Integration was nontrivial and is the project's headline achievement: a gene
junction table bridged the database's mmseqs2-style cluster IDs to BERDL
centroid gene IDs — mapping all 4,891 BERDL clusters to 4,081 unique ADP1
clusters *despite 0% direct string match* — and four of five connection types
matched at over 90% (100% of genome IDs and compounds, 91% of reactions),
demonstrating deep lakehouse integration. The biology recovered through that
bridge is coherent with [pangenome architecture](../topics/pangenome-architecture.md):
core metabolism is highly conserved (1,248 of 1,330 reactions shared by all 14
*Acinetobacter* genomes), essential genes are more likely to reside in the core
pangenome, and essential genes are far more annotation-rich than dispensable
ones (33% vs 5% with COG; 92% vs 53% with KEGG KO). Essentiality is
media-dependent (499 essential genes on minimal media vs 346 on LB), and FBA
flux predictions agreed with TnSeq essentiality calls for 73.8% of the 866
genes carrying both, with the discordant quarter flagged for model refinement.

The honest limits: 87% of the 121,519 growth-phenotype predictions rely on at
least one gapfilled reaction, tightly coupling accuracy to gapfilling quality;
no gene carries data across all six modalities, and sparse FBA flux coverage
(15%) limits concordance analysis to just 866 genes. The roughly 8% of
essential genes lacking KEGG KO assignments are flagged as promising candidates
for discovering novel essential functions — a [functional-dark-matter](../topics/functional-dark-matter.md)
opportunity that recurs in the SNIPE project below.

### SNIPE defense system

The SNIPE project shows how the same fitness data that supports phage-cocktail
and formulation design also explains *anti-phage* biology — the bacterial
counter-move to phage therapy, which is exactly the failure mode PhageFoundry's
coverage data must contend with. SNIPE is an antiphage defense system marked by
the domain formerly called DUF4041; InterPro has since renamed IPR025280 from a
domain of unknown function to the "SNIPE associated domain," converting a piece
of [functional dark matter](../topics/functional-dark-matter.md) into a defined
antiphage marker. The diagnostic domain (PF13250) was detected in 4,572 gene
clusters across 1,696 species spanning 33 phyla, far exceeding the ~500
homologues in the original paper, and the system's nuclease is PF13455
(Mug113), a distinct Pfam family in the GIY-YIG clan rather than the canonical
PF01541 — so the absence of DUF4041+PF01541 co-occurrences is a genuine result,
not an artifact.

The mechanistic payoff connects directly to fitness data and to phage host
range. RB-TnSeq fitness from 168 *E. coli* K-12 experiments shows ManXYZ
knockouts incur severe defects on mannose and glucosamine (worst fitness −3.93
to −4.14), and Fitness Browser data directly contradict UniProt's
fructose-transporter annotation — ManXYZ mutants grow normally on fructose —
confirming ManYZ as a mannose/glucosamine-specific transporter. ManYZ is also
the phage lambda receptor, so losing it would confer resistance at a real
metabolic cost. SNIPE resolves this phage-resistance-versus-cost trade-off by
cleaving phage DNA at the ManYZ pore while retaining full transporter function
— the resistance benefit of *man* knockouts without their metabolic penalty.
*Methanococcus maripaludis* JJ carries a full two-domain SNIPE protein with 129
fitness experiments, the first SNIPE homologue with genome-wide knockout
phenotypes.

Distribution and ecology mark SNIPE as a mobile defense element. SNIPE genes
are predominantly accessory (only 13.3% core; 86.7% accessory-plus-singleton),
its patchy spread across phyla is consistent with horizontal gene transfer of
defense islands — connecting it to [mobile genetic elements](../topics/mobile-genetic-elements.md)
— and SNIPE-bearing species occupy statistically distinct
[environmental niches](../topics/environment-biogeography.md) (22 of 64
AlphaEarth dimensions significantly different). Clinically, SNIPE (DUF4041) was
detected in the phage-therapy target *Klebsiella*, co-occurring with its
mannose PTS transporter, where it could blunt phage therapy efficacy. The
caveats are annotation-driven: about 20% of DUF4041 clusters have non-defense
primary annotations and need a stricter description filter, and eggNOG Pfam
annotations may miss divergent homologues (only 54 of 4,572 clusters show
Mug113 co-annotation). Generating *Klebsiella*-specific SNIPE or ManYZ fitness
data is the stated next step.

## Connections

The four projects are adjacent because they share both data and method.
[Gene fitness](../topics/gene-fitness.md) data (RB-TnSeq, the Fitness Browser,
and the ADP1 condition-specific resource) is the common substrate that powers
ADP1 essentiality calls, the SNIPE ManYZ mechanism, and the empirical host
ranges underlying phage-cocktail and formulation design.
[Pangenome architecture](../topics/pangenome-architecture.md) is the shared
lens for judging generality — core-vs-accessory placement explains why ADP1
essential genes cluster in the core, why SNIPE is mobile and accessory, and why
the CF formulation's targets are conserved enough to be strain-agnostic.
[Metabolic pathways](../topics/metabolic-pathways.md) link the FBA/GapMind
reconstructions in the ADP1 and CF projects.
[Microbiome engineering](../topics/microbiome-engineering.md) and
[microbial ecotypes](../topics/microbial-ecotypes.md) unite the two
intervention-design projects (phage cocktails and commensal formulations),
[mobile genetic elements](../topics/mobile-genetic-elements.md) and
[functional dark matter](../topics/functional-dark-matter.md) connect SNIPE's
HGT-borne, formerly-uncharacterized defense domain to the IBD project's phage
and pathobiont gene clusters, and
[environment-biogeography](../topics/environment-biogeography.md) ties together
the lung-adaptation, engraftability, and AlphaEarth-niche threads across the CF
and SNIPE work.

## Sources

- [stmt:five-phage-cocktail-coverage; ibd_phage_targeting]
- [stmt:phage-coverage-gap; ibd_phage_targeting]
- [stmt:external-phage-db-opportunity; ibd_phage_targeting]
- [stmt:four-ibd-ecotypes; ibd_phage_targeting]
- [stmt:canonical-cd-signature; ibd_phage_targeting]
- [stmt:cohort-cocktail-mismatch; ibd_phage_targeting]
- [stmt:state-dependent-dosing; ibd_phage_targeting]
- [stmt:clinical-covariates-insufficient; ibd_phage_targeting]
- [stmt:iron-acquisition-genomic; ibd_phage_targeting]
- [stmt:ecoli-carries-iron-genotoxin; ibd_phage_targeting]
- [stmt:gokushovirus-cd-down; ibd_phage_targeting]
- [stmt:substudy-nesting-unidentifiable; ibd_phage_targeting]
- [stmt:hybrid-cocktail-needed; ibd_phage_targeting]
- [stmt:synonymy-layer-reusable; ibd_phage_targeting]
- [stmt:no-single-organism-outgrows-pa14; cf_formulation_design]
- [stmt:five-organism-formulation; cf_formulation_design]
- [stmt:formulation-target-invariant; cf_formulation_design]
- [stmt:metabolic-traits-species-level; cf_formulation_design]
- [stmt:pa-lung-metabolic-streamlining; cf_formulation_design]
- [stmt:pa14-strain-bias-caveat; cf_formulation_design]
- [stmt:planktonic-only-caveat; cf_formulation_design]
- [stmt:m-luteus-engraftment-tension; cf_formulation_design]
- [stmt:metabolic-model-overfits; cf_formulation_design]
- [stmt:pairwise-interaction-gap; cf_formulation_design]
- [stmt:adp1-fitness-unique-resource; acinetobacter_adp1_explorer]
- [stmt:adp1-multiomics-database; acinetobacter_adp1_explorer]
- [stmt:cluster-id-bridge; acinetobacter_adp1_explorer]
- [stmt:berdl-connectivity; acinetobacter_adp1_explorer]
- [stmt:essential-genes-annotation-rich; acinetobacter_adp1_explorer]
- [stmt:fba-tnseq-concordance; acinetobacter_adp1_explorer]
- [stmt:gapfilling-dependence; acinetobacter_adp1_explorer]
- [stmt:unannotated-essential-genes; acinetobacter_adp1_explorer]
- [stmt:duf4041-renamed-snipe-domain; snipe_defense_system]
- [stmt:snipe-widespread-1696-species; snipe_defense_system]
- [stmt:snipe-resolves-resistance-cost-tradeoff; snipe_defense_system]
- [stmt:manxyz-fitness-cost-mannose-glucosamine; snipe_defense_system]
- [stmt:snipe-predominantly-accessory; snipe_defense_system]
- [stmt:snipe-in-klebsiella-phage-therapy; snipe_defense_system]
- [stmt:caveat-duf4041-false-positives; snipe_defense_system]
