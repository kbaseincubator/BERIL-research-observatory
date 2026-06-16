# Enigma Coral

## Overview

ENIGMA CORAL is the shared field-and-laboratory data collection for the
Department of Energy ENIGMA program's long-term study site at Oak Ridge,
Tennessee — a uranium- and nitrate-contaminated subsurface aquifer that
has become a model system for studying how microbial communities respond
to heavy-metal and acid stress. The collection lives as a set of curated
"bricks" (tabular data objects, e.g. `ddt_brick0000454` taxonomy,
geochemistry bricks 10/80) inside BERDL, the BER Data Lakehouse. It bundles
16S amplicon community surveys, per-well geochemistry, ENIGMA strain
isolates and their growth-curve corpus, and the taxonomy and pangenome
bridges needed to connect those field organisms to laboratory genetics.
This page exists because CORAL is the *connective tissue* of this wiki: five
otherwise independent analysis projects all reach into the same collection,
and reading them side by side reveals both what the data can support and
where it runs out. As one project notes, this is the first body of work to
treat CORAL as analysis-ready ecological data and to link it directly to
laboratory fitness measurements.

Several recurring constraints shape everything built on CORAL, so it is
worth stating them up front. First, the community data is **16S amplicon
sequencing**, which resolves taxonomy only to the genus level — so a field
genus cannot be matched to a specific laboratory strain or species, and
genus-level mapping can mask the strain-level adaptation that actually drives
metal resistance at Oak Ridge. Second, the ENIGMA taxonomy table itself stops
at genus, blocking true species-level bridge testing. Third, a large fraction
of the geochemistry that would let community patterns be interpreted causally
has not yet been loaded into BERDL, so environmental inferences currently rest
on community composition alone. These are not flaws in any single analysis;
they are properties of the collection that every downstream project inherits,
and they explain why the studies below so often land on "suggestive but not
significant."

## Projects Using This Collection

**Spatial ecology of the Oak Ridge subsurface
(`enigma_sso_asv_ecology`).** This project treats CORAL's amplicon survey as a
map of subsurface hydrology. Across a 3×3 grid of wells, all findings converge
on a single model: community spatial structure is governed by a contamination
plume entering from the northeast and flowing southwest through the saturated
zone, with the U3–M6–L7 wells forming a diagonal community-similarity corridor
along the expected flow path from the uphill Area 3 source. Strikingly, this
plume is visible purely in Bray-Curtis community similarity, demonstrating that
16S structure can map hydrology at meter scale. Depth dominates the signal —
PERMANOVA attributes 27.5% of sediment variance to hydrogeological depth zone
(p=0.0001) while well identity is not significant — and ten of twelve dominant
phyla split cleanly into shallow-oxic versus deep-anoxic groups that mirror the
subsurface redox gradient. Genus-level functional inference even arranges
biogeochemical processes along the [thermodynamic redox ladder](../topics/metabolic-pathways.md)
expected down a plume, with central well M5 a denitrification hotspot
(7.7% *Rhodanobacter*). Groundwater communities are remarkably stable over nine
days (sampling date explains 0.8% of variance versus 49.9% for well identity)
and are enriched in planktonic plume-adapted denitrifiers, distinct from
sediment-attached anaerobes. The honest limits are sharp: the plume model still
awaits geochemical confirmation because SSO geochemistry is not yet loaded;
genus-level annotation covers only 21% of reads, making process estimates lower
bounds; and only 5 of 9 wells have groundwater data, so the M5 denitrification
hotspot and U3 plume-entry interpretations rest on sediment alone. The clear
next steps are loading the 221 registered geochemistry samples and adding
shotgun metagenomics at the same resolution.

**Linking laboratory fitness to field abundance (`lab_field_ecology`).** This
project asks whether organisms that tolerate metals in the laboratory are the
ones that thrive in contaminated field sites — joining CORAL's field
communities to laboratory [gene-fitness](../topics/gene-fitness.md) data from
the Fitness Browser. It is the first study to directly link Fitness Browser lab
fitness with CORAL field community composition across a geochemical gradient. Of
26 genera in the Fitness Browser, 14 appear in Oak Ridge groundwater; of 11 with
sufficient prevalence, 5 correlate significantly with uranium after FDR
correction, yielding actionable [ecotype](../topics/microbial-ecotypes.md)
indicators — *Caulobacter* and *Sphingomonas* decline at high uranium (sensitive
indicators) while *Herbaspirillum* and *Bacteroides* increase (tolerant
colonizers). Yet the headline result is a careful negative: lab metal tolerance
does *not* simply predict field abundance. The aggregate-tolerance-versus-field
correlation is only suggestive (Spearman rho=0.503, p=0.095, n=12), the metric
itself is crude, and the comparison is confounded by uncontrolled geochemistry
(pH, oxygen, carbon). The ENIGMA model organisms underscore the gap:
*Desulfovibrio* is detected at only 34% of sites at very low abundance, and
neither *Desulfovibrio* nor *Pseudomonas* correlates with uranium at all.
Consistent with the broader [metal-resistance](../topics/metal-resistance.md)
literature, *Rhodanobacter*'s heavy-metal resistance appears enriched in the
accessory genome rather than the core. The flagged opportunities — adding
*Rhodanobacter* (which dominates contaminated wells but is absent from the
Fitness Browser) and moving to species-level metagenomics — target exactly the
genus-resolution wall.

**Pangenome conservation of fitness-important genes
(`field_vs_lab_fitness`).** Because CORAL contains *no* *Desulfovibrio vulgaris*
Hildenborough fitness data, this project pairs the collection's ecological
framing with RB-TnSeq fitness data (random-barcode transposon sequencing, which
measures each gene's fitness contribution by quantifying insertion-mutant
abundance) from the Fitness Browser, and asks how fitness importance relates to
[pangenome architecture](../topics/pangenome-architecture.md) — whether a gene
sits in the conserved core or the variable accessory genome. DvH's 757 RB-TnSeq
experiments were sorted into field (44.5%) versus lab (55.5%) conditions. The
dominant signal is that *any* fitness importance predicts conservation
regardless of condition type (universally important genes OR=1.35, p=0.033);
field-stress genes are the most conserved (83.6% core, OR=1.58, q=0.026) and the
pattern is robust across fitness thresholds. Counter to the hypothesis,
lab-specific genes are 96.0% core — even *higher* than field-specific genes —
so the core genome seems to reflect general functional importance rather than
niche-specific selection, the first analysis to stratify RB-TnSeq effects by
ecological relevance this way. Antibiotic- and heavy-metal-resistance genes are
the least conserved (below baseline), consistent with these being accessory
traits carried on [mobile genetic elements](../topics/mobile-genetic-elements.md).
The caveats are substantial and well surfaced: results cover a single organism
whose sparse pangenome forces a coarse 76.3%-core baseline that compresses
effect sizes; gene length confounds both fitness quality and core status; and the
field/lab-specific gene sets are tiny (n=50–52). Tellingly, gene length alone is
a far stronger predictor of core status (CV-AUC 0.645) than fitness. Twenty-one
conserved "ecological" ICA modules contain 52 unannotated genes — candidate
[functional dark matter](../topics/functional-dark-matter.md) for environmental
adaptation — and a quantitative conservation metric is the recommended way to
recover statistical power.

**Genotype-to-phenotype prediction from ENIGMA strains
(`genotype_to_phenotype_enigma`).** This project mines CORAL's strain corpus —
27,632 growth curves across 123 strains — to learn which gene-content features
predict phenotype, anchoring 486 strain-by-condition pairs across 7 strains and
72 conditions to Fitness Browser fitness. Its central methodological lesson is
scale: mechanistic, condition-specific prediction needs on the order of 10⁴
training pairs. With n=7 strains a model learns genome-scale artifacts, whereas
at 46K pairs the same architecture surfaces the mechanistically correct
transporters and enzymes — *rbsC* (ribose transporter), *proP* (proline/betaine
transporter), *pcaB* — for each substrate. Binary growth is predictable from KO
gene presence/absence on amino acids (AUC 0.775) and nucleosides (0.780) but not
on metals, antibiotics, or nitrogen; and continuous parameters (growth rate, lag,
yield) are not predictable at all, a fundamental limit because gene presence
encodes capability, not kinetic rate. A global pH-driven niche partition across
464K worldwide 16S samples explains local Oak Ridge co-occurrence — the
acid-tolerant *Rhodanobacter*–*Ralstonia*–*Dyella* cluster averages pH 5.4 —
tying the strains back to the
[biogeography](../topics/environment-biogeography.md) of the site. Two caveats
deserve emphasis: cross-dataset condition alignment is string-based (only 42
molecular matches; ChEBI-ID canonicalization could reach 60–80), and naïve
strain-name linking is hazardous — a label like "MT20" matched *Streptococcus
pneumoniae* and injected 1,751 spurious clinical genomes before GTDB-Tk taxonomy
corrected it. The proposed field-relevance-weighted active-learning round of 50
experiments shows how CORAL geochemistry can steer future lab work.

**Contamination and functional potential (`enigma_contamination_functional_potential`).**
This project tests the intuitive hypothesis that contaminated CORAL sites carry
more stress- and defense-related functional potential, building a composite
contamination index from eight metal columns (broad but right-skewed across 108
samples) and a reproducible ENIGMA-to-BERDL pangenome bridge. The predeclared
confirmatory test is a clean null: site defense score does not correlate with
the contamination index in either genus-mapping mode (relaxed rho=0.059,
q=0.862; strict rho=0.068, q=0.849), and it stays null under four index variants
including uranium-only and within every community fraction. Exploratory
coverage-adjusted models showed the strongest positive defense associations, but
these attenuated under multiple-testing control — and the team explicitly warns
readers not to over-weight those exploratory estimates against the null
confirmatory endpoint. The interpretation is that contamination gradients here
did not produce a robust genus-resolution shift in inferred stress functional
potential, compatible with functional redundancy or taxonomic turnover too fine
for genus-level detection, and consistent with prior Oak Ridge work reporting
strong compositional shifts but only modest functional-diversity decline. The
binding limitations are again resolution: 862 of 1,392 genera went unmapped to
the pangenome bridge, the COG-fraction proxies are coarse rather than curated
[metal-resistance](../topics/amr-resistome.md) pathways, and a stricter
species-proxy mode collapsed mapped abundance (0.031 vs 0.343). The clear
remedies — a species/strain-level bridge and curated metal-stress gene sets in
place of COG fractions — mirror the resolution wall every CORAL project hits.

## Connections

These five projects rhyme because they share the same collection and the same
two limits. The pairing of CORAL's field communities with laboratory
[gene fitness](../topics/gene-fitness.md) data is the spine of the wiki's
[subsurface genomics](../topics/subsurface-genomics.md) story: `lab_field_ecology`
and `field_vs_lab_fitness` both bridge field ecology to Fitness Browser
genetics, and both run into the fact that CORAL holds no DvH fitness data and
only genus-level taxonomy. Their results feed the
[metal-resistance](../topics/metal-resistance.md) and
[mobile genetic elements](../topics/mobile-genetic-elements.md) pages, since
metal- and antibiotic-resistance functions repeatedly turn out to be accessory,
HGT-borne traits rather than core ones — a recurring theme of the
[pangenome architecture](../topics/pangenome-architecture.md) page. The spatial
plume model from `enigma_sso_asv_ecology` and the global pH partition from
`genotype_to_phenotype_enigma` together anchor the
[environment biogeography](../topics/environment-biogeography.md) and
[microbial ecotypes](../topics/microbial-ecotypes.md) pages: the same
acid-tolerant *Rhodanobacter*-led guild that dominates the local denitrification
hotspot is a globally partitioned ecotype. The unannotated "ecological" ICA
module genes connect to [functional dark matter](../topics/functional-dark-matter.md),
and the genotype-to-phenotype catabolic-gene findings connect to
[metabolic pathways](../topics/metabolic-pathways.md). Read as a set, the most
durable cross-project conclusion is methodological: genus-level 16S and
unloaded geochemistry are the shared ceiling, and the convergent recommendation
across CORAL projects is to raise resolution with metagenomics, species/strain
bridges, and loaded geochemistry before sharper functional claims can be made.

## Sources

- [stmt:first-link-fb-fitness-enigma-coral; lab_field_ecology]
- [stmt:genus-resolution-limitation; lab_field_ecology]
- [stmt:contamination-plume-model; enigma_sso_asv_ecology]
- [stmt:16s-maps-subsurface-hydrology; enigma_sso_asv_ecology]
- [stmt:depth-dominates-zonation; enigma_sso_asv_ecology]
- [stmt:column3-corridor; enigma_sso_asv_ecology]
- [stmt:m5-denitrification-hotspot; enigma_sso_asv_ecology]
- [stmt:groundwater-temporal-stability; enigma_sso_asv_ecology]
- [stmt:no-direct-geochemistry-caveat; enigma_sso_asv_ecology]
- [stmt:genus-coverage-caveat; enigma_sso_asv_ecology]
- [stmt:groundwater-key-well-gap-caveat; enigma_sso_asv_ecology]
- [stmt:load-geochemistry-opportunity; enigma_sso_asv_ecology]
- [stmt:lab-fitness-does-not-simply-predict-field; lab_field_ecology]
- [stmt:caulobacter-sphingomonas-uranium-indicators; lab_field_ecology]
- [stmt:genus-abundance-correlates-uranium-bidirectional; lab_field_ecology]
- [stmt:lab-tolerance-not-significant-field-ratio; lab_field_ecology]
- [stmt:model-organisms-no-uranium-correlation; lab_field_ecology]
- [stmt:metal-resistance-enriched-accessory-genome; lab_field_ecology]
- [stmt:opportunity-add-rhodanobacter-fitness-browser; lab_field_ecology]
- [stmt:enigma-coral-no-dvh-fitness; field_vs_lab_fitness]
- [stmt:any-fitness-importance-predicts-conservation; field_vs_lab_fitness]
- [stmt:field-stress-genes-more-conserved; field_vs_lab_fitness]
- [stmt:lab-specific-genes-surprisingly-core; field_vs_lab_fitness]
- [stmt:condition-type-vs-fitness-magnitude; field_vs_lab_fitness]
- [stmt:resistance-genes-accessory-mge; field_vs_lab_fitness]
- [stmt:single-organism-coarse-pangenome-caveat; field_vs_lab_fitness]
- [stmt:gene-length-stronger-than-fitness; field_vs_lab_fitness]
- [stmt:ecological-modules-dark-candidates; field_vs_lab_fitness]
- [stmt:46k-pairs-for-mechanistic-prediction; genotype_to_phenotype_enigma]
- [stmt:condition-specific-catabolic-genes; genotype_to_phenotype_enigma]
- [stmt:binary-growth-predictable-aa-nucleosides; genotype_to_phenotype_enigma]
- [stmt:continuous-params-not-predictable; genotype_to_phenotype_enigma]
- [stmt:global-ph-niche-partition; genotype_to_phenotype_enigma]
- [stmt:multidataset-anchor-set; genotype_to_phenotype_enigma]
- [stmt:caveat-strain-name-collision; genotype_to_phenotype_enigma]
- [stmt:caveat-string-based-condition-alignment; genotype_to_phenotype_enigma]
- [stmt:confirmatory-defense-null; enigma_contamination_functional_potential]
- [stmt:exploratory-defense-coverage-aware; enigma_contamination_functional_potential]
- [stmt:functional-redundancy-interpretation; enigma_contamination_functional_potential]
- [stmt:exploratory-overweight-risk; enigma_contamination_functional_potential]
- [stmt:unmapped-genera-coarse-cog; enigma_contamination_functional_potential]
- [stmt:species-proxy-coverage-limited; enigma_contamination_functional_potential]
- [stmt:reproducible-bridge-workflow; enigma_contamination_functional_potential]
- [stmt:opp-species-strain-bridge; enigma_contamination_functional_potential]
