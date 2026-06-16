# Subsurface Genomics

## Overview

Subsurface genomics is the study of the microorganisms that live below the
soil zone — in deep clay rock, fractured aquifers, contaminated groundwater
plumes, and other settings where light, oxygen, and fresh organic carbon are
scarce. This page exists because a surprisingly large slice of the corpus,
spanning fourteen independent projects, converges on the same handful of
deep-subsurface field sites (the DOE Oak Ridge Reservation in Tennessee and
the Mont Terri Opalinus clay rock laboratory in Switzerland chief among them)
and on the same recurring biological questions: do subsurface specialists
shrink or expand their genomes, which anaerobic respiratory strategies they
favor, how community composition tracks the physical and chemical structure of
an aquifer, and whether genomics measured in a database faithfully represents
the organisms actually in the ground. The work draws on cultured isolate
genomes, metagenome-assembled genomes (MAGs), 16S amplicon surveys, and
fitness data, all routed through the BERDL data lakehouse, and it is unusually
explicit about its own statistical caveats — which is why the uncertainty is
foregrounded throughout rather than buried.

A reader should treat this page as a cross-project synthesis: no single study
"owns" subsurface genomics here. Instead, several teams independently probed
adjacent corners of the same environment and, in aggregate, sketch a coherent
but heavily caveated picture of how microbial genomes and communities are
shaped by life underground.

## What the Corpus Shows

**Subsurface specialization can mean genome expansion, not streamlining.** A
long-standing expectation is that subsurface microbes streamline their genomes
— shedding genes under energy limitation, as the ultra-small Patescibacteria
(also called CPR, candidate phyla radiation) do. The clay-confined work tests
this directly and finds the opposite for cultivable Bacillota_B (a clade of
Firmicutes-type bacteria). Deep-clay genomes are roughly 1 Mbp larger than
their soil-baseline relatives at equivalent CheckM completeness (CheckM
estimates how complete a genome assembly is), rejecting the streamlining
hypothesis in the opposite direction. Per-orthogroup Fisher's exact testing
flagged 547 eggNOG orthologous groups (OGs — clusters of evolutionarily
related genes) significantly enriched in deep-clay versus soil Bacillota_B,
far exceeding the pre-registered prediction of at least ten. Those enriched
OGs fall into the five pre-declared functional categories — anaerobic
respiration, sporulation revival, mineral attachment, regulators, and
osmoadaptation — with anaerobic respiration the largest annotated bucket. A
molybdopterin-cofactor orthogroup (COG1977), a cofactor source for
anaerobic-respiration enzymes, appeared in all ten anchor genomes but only 11
of 62 baseline genomes, a strong niche signal. The conclusion is that, at
least for this cultivable lineage, deep-clay life correlates with gene-content
expansion rather than reductive streamlining, refuting a universal "subsurface
equals streamlining" model.

**Sulfate reduction is the robust anaerobic signature of the deep clay.**
Deep clay-confined isolates jointly carry an anaerobic toolkit — the
Wood-Ljungdahl carbon-fixation pathway, group-1 [NiFe]-hydrogenase, and
dissimilatory sulfate reduction — at far higher rates than soil or shallow-clay
cohorts (mean toolkit score 1.89 of 3 modules versus 0.39 and 0.03). But a
within-phylum control is sobering: Wood-Ljungdahl and the hydrogenase track the
Bacillota_B lineage itself rather than the deep-clay habitat, because soil
Bacillota_B already carry them at high background rates. Only dissimilatory
sulfate reduction (the dsrAB-aprAB-sat marker set) survives that control,
enriched in 5 of 5 deep Bacillota_B isolates versus 4 of 19 soil-baseline
isolates. Deep isolates are dominated by sulfate-reduction-only marker
profiles while shallow-clay isolates are dominated by iron-reduction-only
profiles — a clean mirror-image contrast — and the sulfate-reduction enrichment
is overwhelming against a rock-attached null distribution (binomial
p = 4.0x10^-12). The companion Bacillota_B accessory-genome project confirms
the sulfate-reduction side is robust because its markers were correctly
identified, even as its iron-reduction story collapses (see Caveats).

**Biosynthetic self-sufficiency does not generalize to cultured cohorts.**
The literature highlights extremely self-sufficient subsurface lineages such as
Candidatus Desulforudis audaxviator that synthesize most of their own building
blocks. That signal does not appear here: deep-clay GapMind amino-acid pathway
completeness (GapMind reconstructs biosynthetic pathways from genomes) is
comparable to or slightly below the soil baseline (15.5 of 18 versus 17.1 of
18, p=0.009). The interpretation is that BERDL's cultured cohort simply
excludes the characteristically uncultivated, MAG-recovered self-sufficient
lineages the literature points to — an absence-of-evidence rather than a
contradiction.

**Cultivation bias is measurable, and BERDL captures the porewater fraction.**
A central methodological result is that the marker profile itself diagnoses
what BERDL has sampled. The cultured clay genomes carry the Bagnoud Mont Terri
porewater signature (sulfate-reduction-rich), not the Mitzscherling
rock-attached signature (iron-reduction-rich); all eight Opalinus genomes trace
to two boreholes, giving a quantitative diagnostic that the lakehouse holds the
free-living porewater fraction rather than rock-attached cells. Anchor genera
include exactly the recurrent Mont Terri lineages Bagnoud found across seven
boreholes (Desulfosporosinus, Peptococcaceae BRH-c8a), cross-validating
indigeneity.

**Community structure maps subsurface hydrology at meter scale.** In the Oak
Ridge SSO (Shallow Subsurface Observatory) ASV study, 16S community
composition alone reproduces the physical aquifer. Hydrogeological depth zone
explains 27.5% of sediment community variance by PERMANOVA while well identity
is not significant — vertical zonation dominates horizontal position.
Communities show significant distance-decay at meter scale along the east-west
axis, ten of twelve dominant phyla split into shallow-oxic-enriched versus
deep-anoxic-enriched groups mirroring the redox gradient, and genus-level
functional inference lays biogeochemical processes onto a 3x3 well grid in a
sequence that recapitulates the thermodynamic redox ladder. Wells U3-M6-L7
form a diagonal similarity corridor from the northeast Area 3 source toward the
southwest, and central well M5 carries the highest denitrification potential
(7.7% Rhodanobacter), consistent with a plume mixing zone where nitrate-rich
contaminated groundwater meets native carbon. Groundwater communities sampled
nine days apart are strikingly stable (sampling date explains 0.8% of variance
versus 49.9% for well identity). Everything converges on a single model: a
contamination plume entering from the northeast and flowing southwest — visible
purely in Bray-Curtis similarity.

**Contamination shifts composition more than inferred function.** Across an
ENIGMA contamination subset, predeclared confirmatory Spearman tests of a site
defense score against a composite contamination index stayed non-significant in
both genus mapping modes, and re-testing under four index variants (including
uranium-only) left everything non-significant after FDR correction.
Exploratory coverage-adjusted models showed the strongest positive defense
associations, but those attenuated under multiple-testing control. The reading
is functional redundancy or taxonomic turnover too fine to resolve at genus
level — consistent with prior Oak Ridge work reporting strong compositional
shifts but only modest functional-diversity decline. By contrast, a
MicrobeAtlas analysis found that plume wells FW215/FW216 host higher
community-weighted-mean metal-type diversity that rises with time after carbon
amendment, independently validated in 1,624 BERDL groundwater samples where
genera with broader metal-resistance repertoires are more prevalent.

## Projects and Evidence

The deep-clay story rests on two linked projects. **clay_confined_subsurface**
contributes the core findings — genome expansion, the anaerobic toolkit, the
porewater diagnostic, and the negative self-sufficiency result — while
**bacillota_b_subsurface_accessory** re-examines the same cohort at orthogroup
resolution, contributing the 547-OG enrichment and a careful correction of the
iron-reduction signal.

The Oak Ridge community work spans several teams. **enigma_sso_asv_ecology**
supplies the plume model and hydrology mapping; **enigma_contamination_functional_potential**
supplies the contamination-versus-function null result and a reproducible
ENIGMA-to-BERDL functional inference workflow with strict-versus-relaxed
feature construction and a species-proxy sensitivity mode;
**microbeatlas_metal_ecology** supplies the metal-diversity gradient. Several
single-statement projects anchor specific mechanisms:
**genotype_to_phenotype_enigma** documents a global pH-driven niche partition
across 464K worldwide 16S samples (the acid-tolerant Rhodanobacter-Ralstonia-Dyella
Cluster B occupies environments about 1.35 pH units more acidic) and aligns
27,632 ENIGMA growth curves with Fitness Browser RB-TnSeq data (RB-TnSeq is
random-barcode transposon sequencing, which measures each gene's fitness
contribution across conditions) through 486 strain-by-condition anchor pairs.
**fw300_metabolic_consistency** identifies tryptophan secretion by strain
FW300-N2E3 as a cross-feeding candidate. **lab_field_ecology** and
**field_vs_lab_fitness** flag that Desulfovibrio — the canonical ENIGMA model
organism — is detected at only 34% of sites and at low abundance, and that the
ENIGMA CORAL database holds no Desulfovibrio vulgaris Hildenborough fitness
data, forcing reliance on the Fitness Browser. **lanthanide_methylotrophy_atlas**
reports that 37 rare-earth-element acid-mine-drainage MAGs are dominated by
acidophiles rather than methylotrophs, with only 4 of 37 carrying any xoxF
(a lanthanide-dependent methanol dehydrogenase gene). Supporting projects
(**bacdive_metal_validation**, **env_embedding_explorer**, **module_conservation**,
**plant_microbiome_ecotypes**) contribute validation opportunities and coverage
caveats rather than primary subsurface findings.

## Connections

Subsurface genomics sits at the intersection of several other topic pages in
this wiki. The genome-expansion-versus-streamlining debate is fundamentally
about [Pangenome Architecture](pangenome-architecture.md) — the accessory
genome content that distinguishes deep-clay specialists from soil relatives.
The community-composition results, distance-decay, depth zonation, and the
global pH niche partition belong to [Environment Biogeography](environment-biogeography.md),
while the question of whether locally co-occurring strains are distinct adapted
ecotypes connects to [Microbial Ecotypes](microbial-ecotypes.md). The anaerobic
respiratory toolkit (sulfate reduction, iron reduction, denitrification,
Wood-Ljungdahl) is the subject matter of [Metabolic Pathways](metabolic-pathways.md),
and the contamination-driven metal-resistance gradients link to
[Metal Resistance](metal-resistance.md). Gene-level fitness evidence from
RB-TnSeq and the growth-curve anchor set ties to [Gene Fitness](gene-fitness.md).
The large unannotated orthogroup buckets — where ~80-100 anaerobic OGs hide
behind keyword scanners — overlap [Functional Dark Matter](functional-dark-matter.md),
and the cross-feeding and active-learning experiment proposals point toward
[Microbiome Engineering](microbiome-engineering.md).

The primary data collections underpinning this work are also linked targets:
the ENIGMA [Enigma Coral](../data/enigma-coral.md) database, the
[Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md) RB-TnSeq
resource, the [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) and
[Kbase Msd Biochemistry](../data/kbase-msd-biochemistry.md) collections, and
the [Nmdc Arkin](../data/nmdc-arkin.md) metagenome holdings.

## Caveats and Open Directions

The honest weak spots are numerous and the projects state them plainly. **Small
cohorts:** the deep-clay enrichment rests on only 10 anchor versus 62 baseline
genomes, so marginal effects built on anchor counts of 3-5 should be read
descriptively, not inferentially, and genus-level phylogenetic confounding is
only partly mitigated. **Iron-reduction correction:** the companion
Bacillota_B project found the clay project's original iron-reduction markers
(K07811, K17324, K17323) were mismatched genes (TMAO reductase, glycerol
transport) rather than iron-reduction functions; with corrected triple-signal
multi-heme cytochrome detection the original "shallow much greater than deep"
iron-reduction pattern disappears and no cohort comparison stays significant.
Multi-heme cytochrome PFAMs are sparse in Bacillota_B, so CXXCH heme-binding
motif counting on protein sequences — not PFAM detection — carried the corrected
signal, and keyword scanning undercounted the anaerobic bucket by roughly
80-100 OGs. The sulfate-reduction side, however, remains robust. **Cohort
scope:** all clay conclusions apply only to cultivable porewater isolates;
CPR/DPANN episymbionts and rock-attached Geobacter/Geothrix lineages are
essentially absent, which is precisely why self-sufficiency did not appear.

On the community side, **no geochemistry has been loaded into BERDL for the SSO
site**, so the plume model rests on composition alone and awaits geochemical
confirmation; only 5 of 9 wells have groundwater ASV data, leaving the M5
denitrification hotspot and U3 plume entry interpreted from sediment alone.
**Taxonomic resolution** is a recurring ceiling: the ENIGMA taxonomy table
stops at genus, so true species-level bridge testing is impossible and may mask
strain-level adaptation, and the main interpretive risk is that readers
over-weight significant exploratory adjusted-model estimates shown beside the
null confirmatory endpoint. Restricting to a single-clade species-proxy mode
sharply dropped mapped abundance (0.031 versus 0.343). **Strain-name
collisions** are dangerous: short identifiers like "MT20" matched unrelated
NCBI organisms (Streptococcus pneumoniae) and injected 1,751 spurious clinical
genomes before GTDB-Tk taxonomy corrected them. Other caveats span a crude
coordinate-QC heuristic that mislabels legitimate field sites (DOE Rifle,
Saanich Inlet), incomplete pangenome and phylogenetic-tree coverage (only 18 of
65 plant-associated species, 29 of 32 module organisms), and the REE-impacted
xoxF signal that is only descriptive at n=37 (p_BH=0.082).

Open directions follow directly from these gaps. Loading the 221 registered SSO
geochemistry samples and per-well uranium/nitrate/metal concentrations into
CORAL would let the plume and Cluster-B contamination hypotheses be tested
against measured chemistry rather than community proxies. Ingesting
deep-subsurface MAGs (Mont Terri, Olkiluoto, MX-80 bentonite, Oak Ridge) and
re-running the H1/H2/H3 framework would reveal whether the self-sufficiency
signal emerges once rock-attached and uncultivated lineages are present, while
the porewater/rock SR-versus-IR diagnostic could be applied across other
subsurface cohorts to quantify cultivation bias. A species- or strain-level
taxonomy bridge, per-genus decomposition via BacDive linkage, a larger
REE-impacted metagenome collection, a community metabolic model parameterized
by the tryptophan overflow, and a field-relevance-weighted active-learning round
of 50 experiments (favoring organic acids, nitrate, and low-pH substrates) are
each proposed as concrete next steps. Cross-referencing BacDive predictions
with ENIGMA field data at Oak Ridge offers a complementary validation route.

## Sources

- [stmt:expansion-not-streamlining; clay_confined_subsurface]
- [stmt:h2-genomes-larger; bacillota_b_subsurface_accessory]
- [stmt:h1-547-enriched-ogs; bacillota_b_subsurface_accessory]
- [stmt:h1-functional-categories; bacillota_b_subsurface_accessory]
- [stmt:molybdopterin-cofactor-signal; bacillota_b_subsurface_accessory]
- [stmt:anaerobic-toolkit-enriched; clay_confined_subsurface]
- [stmt:toolkit-phylum-confound; clay_confined_subsurface]
- [stmt:sr-survives-phylo-control; clay_confined_subsurface]
- [stmt:deep-shallow-mirror-image; clay_confined_subsurface]
- [stmt:sr-enrichment-binomial; clay_confined_subsurface]
- [stmt:h3-sr-side-robust; bacillota_b_subsurface_accessory]
- [stmt:self-sufficiency-not-supported; clay_confined_subsurface]
- [stmt:self-sufficient-lineages-uncultivated; clay_confined_subsurface]
- [stmt:porewater-signature-h3; clay_confined_subsurface]
- [stmt:cultivation-bias-diagnostic; clay_confined_subsurface]
- [stmt:bagnoud-lineage-overlap; clay_confined_subsurface]
- [stmt:depth-dominates-zonation; enigma_sso_asv_ecology]
- [stmt:distance-decay-meter-scale; enigma_sso_asv_ecology]
- [stmt:phylum-depth-redox-split; enigma_sso_asv_ecology]
- [stmt:redox-ladder-spatial-map; enigma_sso_asv_ecology]
- [stmt:column3-corridor; enigma_sso_asv_ecology]
- [stmt:m5-denitrification-hotspot; enigma_sso_asv_ecology]
- [stmt:groundwater-temporal-stability; enigma_sso_asv_ecology]
- [stmt:contamination-plume-model; enigma_sso_asv_ecology]
- [stmt:16s-maps-subsurface-hydrology; enigma_sso_asv_ecology]
- [stmt:confirmatory-defense-null; enigma_contamination_functional_potential]
- [stmt:index-sensitivity-null; enigma_contamination_functional_potential]
- [stmt:exploratory-defense-coverage-aware; enigma_contamination_functional_potential]
- [stmt:functional-redundancy-interpretation; enigma_contamination_functional_potential]
- [stmt:reproducible-bridge-workflow; enigma_contamination_functional_potential]
- [stmt:enigma-plume-wells-higher-cwm; microbeatlas_metal_ecology]
- [stmt:enigma-groundwater-validation; microbeatlas_metal_ecology]
- [stmt:global-ph-niche-partition; genotype_to_phenotype_enigma]
- [stmt:multidataset-anchor-set; genotype_to_phenotype_enigma]
- [stmt:tryptophan-cross-feeding-candidate; fw300_metabolic_consistency]
- [stmt:desulfovibrio-rare-low-abundance; lab_field_ecology]
- [stmt:enigma-coral-no-dvh-fitness; field_vs_lab_fitness]
- [stmt:ree-amd-acidophiles-not-methylotrophs; lanthanide_methylotrophy_atlas]
- [stmt:small-cohort-limitation; bacillota_b_subsurface_accessory]
- [stmt:h3-mismatched-kos; bacillota_b_subsurface_accessory]
- [stmt:h3-ir-pattern-disappears; bacillota_b_subsurface_accessory]
- [stmt:multiheme-pfams-sparse; bacillota_b_subsurface_accessory]
- [stmt:keyword-scanner-undercounts; bacillota_b_subsurface_accessory]
- [stmt:cohort-cultured-only-caveat; clay_confined_subsurface]
- [stmt:no-direct-geochemistry-caveat; enigma_sso_asv_ecology]
- [stmt:groundwater-key-well-gap-caveat; enigma_sso_asv_ecology]
- [stmt:genus-only-taxonomy-limit; enigma_contamination_functional_potential]
- [stmt:exploratory-overweight-risk; enigma_contamination_functional_potential]
- [stmt:species-proxy-coverage-limited; enigma_contamination_functional_potential]
- [stmt:caveat-strain-name-collision; genotype_to_phenotype_enigma]
- [stmt:coord-qc-crude-caveat; env_embedding_explorer]
- [stmt:phylo-tree-coverage-gap; plant_microbiome_ecotypes]
- [stmt:organism-subset-caveat; module_conservation]
- [stmt:ree-impacted-small-n-caveat; lanthanide_methylotrophy_atlas]
- [stmt:load-geochemistry-opportunity; enigma_sso_asv_ecology]
- [stmt:mag-augmented-expansion; clay_confined_subsurface]
- [stmt:porewater-diagnostic-generalizes; clay_confined_subsurface]
- [stmt:opp-species-strain-bridge; enigma_contamination_functional_potential]
- [stmt:community-metabolic-modeling-opportunity; fw300_metabolic_consistency]
- [stmt:opportunity-active-learning-experiments; genotype_to_phenotype_enigma]
- [stmt:larger-ree-metagenome-opportunity; lanthanide_methylotrophy_atlas]
- [stmt:enigma-field-validation-opportunity; bacdive_metal_validation]
