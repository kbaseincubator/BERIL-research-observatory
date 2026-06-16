# Heather MacGregor

Heather MacGregor is a contributor to this compendium whose work sits at the
intersection of environmental microbial genomics, metal-resistance ecology, and
horizontal gene transfer (HGT) at planetary scale. Across five projects she has
repeatedly asked variations of one question: how the genes that let microbes
tolerate toxic metals are distributed across the globe, which environments
concentrate them, what they reveal about how broadly a microbe can live, and how
they spread between unrelated lineages. This page exists to summarise that
project and topic footprint in one place — to show how the individual studies
connect, and to be honest about where the conclusions are still provisional. The
recurring methodological signature is large public-data reanalysis (tens of
thousands of metagenome-assembled genomes, hundreds of thousands of 16S samples)
combined with phylogenetically aware statistics and an unusually candid running
ledger of caveats.

## Overview

MacGregor's five projects form two tightly linked threads. The first is
**biogeography and ecology of metal resistance**: where metal-resistance genes
occur on the map (`metal_resistance_global_biogeography`, a question of
[Environment Biogeography](../topics/environment-biogeography.md)), what
soil-metal chemistry does to community gene content
(`soil_metal_functional_genomics`), and whether the breadth of a microbe's metal
repertoire predicts how many habitats it can occupy
(`microbeatlas_metal_ecology`). The second thread is **how genomic content moves
and where it is missing**: a global audit of which soils remain genomic "dark
matter" (`soil_frontier_genomics`) and a study of HGT machinery carrying
carbohydrate-active enzyme cassettes between phyla (`t4ss_cazy_environmental_hgt`).
[Metal Resistance](../topics/metal-resistance.md) is the connective tissue
across all five; the metal-resistance niche turns out to be linked to mobile
genetic elements, to ecological generalism, and to the soils we have sampled
least.

The topic footprint follows directly. Heavy weight falls on
[Metal Resistance](../topics/metal-resistance.md) and
[Environment Biogeography](../topics/environment-biogeography.md), with strong
secondary presence in [Microbial Ecotypes](../topics/microbial-ecotypes.md)
(niche-breadth ecology), [Functional Dark Matter](../topics/functional-dark-matter.md)
(under-sampled soils and unmapped genomes),
[Mobile Genetic Elements](../topics/mobile-genetic-elements.md) and
[Pangenome Architecture](../topics/pangenome-architecture.md) (HGT and accessory
genomes), plus [Metabolic Pathways](../topics/metabolic-pathways.md),
[Amr Resistome](../topics/amr-resistome.md),
[Subsurface Genomics](../topics/subsurface-genomics.md), and
[Microbiome Engineering](../topics/microbiome-engineering.md). The work draws on
two shared data collections in this compendium: the
[Kbase Ke Pangenome](../data/kbase-ke-pangenome.md) (the genome and pangenome
reference used to annotate metal-resistance repertoires) and the
[Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md). A unifying
empirical headline is that metal resistance is globally **rare** — only about
2.8% of coordinate-bearing environmental MAGs carry any metal-resistance type —
yet sharply **patterned**, being enriched in soil and depleted in marine
habitats, and concentrated in a handful of geographic hotspots.

## Projects

**Global biogeography of metal resistance**
(`metal_resistance_global_biogeography`). This project built a genome-resolved
world map of microbial metal resistance from 260,652 environmental MAGs in
MGnify, of which 22,356 carried usable latitude/longitude coordinates (73.3%
coverage). Annotating those genomes with AMRFinderPlus showed that only 2.8% of
coordinate-bearing MAGs carry at least one metal-resistance type — metal
resistance is rare in the global pool. A 5° grid Fisher's-exact scan over 289
cells found 11 significant hotspots and 3 coldspots, with the Atacama/Andean
region of Chile the strongest (21.8% prevalence, odds ratio 9.83, q = 7.6e-12).
Biome stratification showed soil significantly enriched (5.8%, OR 5.05) and
marine MAGs significantly depleted (1.2%, OR 0.20). MacGregor argues this
genome-resolved, coordinate-precise approach complements rather than duplicates
OTU-level 16S surveys, because it gives strain-level resolution and direct gene
presence/absence. Two caveats are foregrounded: the hotspots are explicitly
**provisional** because many apparent peaks track sequencing effort in Europe,
the USA, and East Asia rather than real biology, and expedition-level clustering
validation is still pending, so a hotspot like Atacama cannot yet be
distinguished from a single-study artifact. A second data-quality theme runs
through the project: roughly a third of archived metagenome samples lack usable
coordinates (the ENA batch retrieval returned valid lat/lon for only 69.2% of
24,511 records), a per-sample rather than geographic gap that nonetheless leaves
global maps with blind spots. The low 2.8% prevalence is itself caveated — it
may partly reflect a narrow GapMind pathway definition that misses efflux pumps,
metallothioneins, and metal-sequestering operons rather than true rarity.

**Metal repertoire breadth and ecological niche**
(`microbeatlas_metal_ecology`). This is, by MacGregor's framing, the first
analysis to link genus-level metal-type diversity (from pangenome AMR
annotations across 6,789 species) to global ecological niche breadth (from a
464,000-sample 16S atlas), with phylogenetic control via PGLS — phylogenetic
generalised least squares, a regression that corrects for the fact that closely
related taxa are not statistically independent. The central finding is that
across 606 bacterial genera, the **number of distinct metal types** a genus can
resist is the only metal-AMR predictor of niche breadth that survives both
phylogenetic and Bonferroni correction (β = +0.021, p = 1.5e-4). Crucially it is
breadth, not depth: total AMR gene-cluster count and core-resistance fraction do
not predict niche breadth, and the effect persists after controlling for species
richness and genome size. Nitrification served as a positive control with
near-maximal phylogenetic signal, contrasting with the intermediate signal of
metal AMR and lending confidence to the pipeline. Independent validation in
1,624 BERDL groundwater samples confirmed that broad-repertoire genera are more
prevalent in groundwater. The interpretive caveats here are the project's
strongest feature. The cross-sectional design means **direction cannot be
established** — metal diversity might facilitate generalism, or generalism might
enable metal-gene acquisition. "Niche breadth" is a sequencing-effort proxy from
OTU detection, not confirmed ecological range, and genus-level aggregation can
make a genus look broad-niched simply because different species occupy different
habitats. The archaeal arm is severely underpowered (n = 48 genera, 11% power),
so its non-significant result must not be read as evidence against the
association in archaea.

**Soil genomic frontiers and the clay-shield test**
(`soil_frontier_genomics`). This project mapped where soil microbial diversity
outruns our genome reference databases, defining a Genomic Discovery Index
(GDI = OTU richness / (mean genome completeness + 1)) at 1° spatial bins. Forest
(GDI 902.36) and Cropland (890.82) soils emerged as the highest-GDI genomic
frontiers — rich in observed diversity but sparsely referenced — while Grassland
and Wetland are comparatively well-mapped. The work also surfaced a systematic
sampling bias: databases lean about +0.8 pH units toward acidic soils, leaving
alkaline-specialist microbes disproportionately as functional dark matter. A
separate hypothesis test asked whether clay content "shields" communities from
industrial or geochemical stress; across 5,441 samples it found **no detectable
buffering**, and all three predictive model families returned negative
out-of-sample R² — they predict functional potential worse than the training
mean. MacGregor is careful that this is a contingent null: the GDI formula is
novel and may be dominated by its richness term, the Forest-vs-Cropland
difference (1.3%) is not meaningfully distinguishable without bootstrap intervals
and should be framed as jointly highest, and the negative-R² diagnosis is
incomplete because distributional shift, outlier leverage, and genuine
unpredictability have not been separated. Spatial-validation and pH-debiasing
analyses are flagged as the next steps before the null is taken as final.

**Soil metal chemistry and community gene content**
(`soil_metal_functional_genomics`). Pairing soil metal measurements with
co-located community gene profiles across 51,748 samples, this project found
2,355 significant COG–metal associations (FDR < 0.05) across nine metals, with
chromium and lead driving the strongest signals and transporters (ABC, RND)
plus biosynthesis genes dominating. A distance-based RDA attributed about 80% of
variance in community COG profiles to metal concentrations (R² = 0.799,
p = 0.005). The copper-specific picture — enrichment of cell division and
nucleotide transport alongside suppressed energy production — is consistent with
the known energetic trade-offs of copper toxicity. The dominant caveat is
**co-contamination**: in industrial soils Cr, Cu, Pb, and Zn co-vary, so it is
hard to know whether associations are metal-specific or reflect a generic
multi-metal stress response. Effect sizes (Spearman ρ) have not been
systematically reported across all 2,355 hits, so many significant associations
may be biologically small; the 0.799 R² is conditional on project accession and
needs an unconditional counterpart; and with a 60% discovery rate across
non-independent tests, the Benjamini-Hochberg FDR is likely anti-conservative.
Spatial autocorrelation testing (Moran's I) and proximity-threshold sensitivity
checks are the proposed remedies.

**T4SS-mediated horizontal transfer of CAZy cassettes**
(`t4ss_cazy_environmental_hgt`). This project examined how type IV secretion
systems (T4SS, conjugative HGT machinery) co-occur with carbohydrate-active
enzymes (CAZymes). About 21.8% of 30,497 high-quality environmental MAGs carry
T4SS machinery; 92 CAZy families are enriched within 10 kb of T4SS loci, with
GT2 glycosyltransferases the top hit across 767 genomes. Phylogenetic analysis
of the GT2 gene tree detected 77 HGT events including 32 high-confidence
cross-phylum events, the headline being Node_4915 — a 35-gene, 82.9% syntenic
cluster spanning eight bacterial phyla. Because CAZy genes sit off plasmids while
T4SS-positive genomes show 10x higher mobile-element density, MacGregor infers
chromosomal or integrative transfer rather than plasmid mobilisation, a mechanism
she argues is distinct from the TonB-dependent PUL paradigm of Bacteroidetes.
The project also ties back to the metal thread: GT2-neighbourhood MAGs carry
roughly 11x more metal-resistance genes than non-GT2 MAGs, linking these
synteny hubs to the metal-resistance niche, and the synteny is most enriched in
barley rhizosphere (OR 10.4). The author is explicit that every association is
observational and the central claim is associative — mechanistic confirmation of
T4SS-mediated CAZy transfer needs experimental validation. The 10 kb synteny
threshold and the cross-phylum incongruence rate are still unvalidated pending a
permutation test and a housekeeping-gene null baseline, and the Node_4915 result
needs BLAST verification against NCBI to rule out chimeric or misclassified
sequences.

## Topics

The work clusters around [Metal Resistance](../topics/metal-resistance.md), which
appears in every project: as a mapped trait
([Environment Biogeography](../topics/environment-biogeography.md)), as an
ecological predictor, as a chemistry-driven community signal, and as cargo for
HGT. [Environment Biogeography](../topics/environment-biogeography.md) is the
second pillar — the global maps, the Atacama hotspot, the soil-versus-marine
enrichment, and the spatial data gaps all live here, and they connect to
[Functional Dark Matter](../topics/functional-dark-matter.md) because the same
coordinate gaps and database biases that limit the maps are exactly what defines
which soils remain genomically unmapped. The pH discovery bias and the
Forest/Cropland genomic frontiers are the clearest functional-dark-matter
findings.

[Microbial Ecotypes](../topics/microbial-ecotypes.md) anchors the niche-breadth
story: the claim that repertoire breadth, not depth, tracks ecological
generalism is fundamentally a statement about how metal tolerance maps onto
ecotype range. That story leans on
[Pangenome Architecture](../topics/pangenome-architecture.md) — the metal
repertoires come from pangenome AMR annotations, and the open question of whether
pangenome openness (accessory-genome proportion) is the hidden driver of both
metal diversity and niche breadth is explicitly raised as future work — and on
[Mobile Genetic Elements](../topics/mobile-genetic-elements.md), since the HGT
project shows metal and CAZy genes riding the same conjugative machinery. The
contrast that metal resistance (2.8% prevalence) and T4SS HGT machinery (21.8%)
are distinct, non-co-distributed features keeps the two threads honestly
separated rather than conflated. [Metabolic Pathways](../topics/metabolic-pathways.md)
covers the COG/KEGG functional interpretation (copper energetic trade-offs,
nitrification control), [Amr Resistome](../topics/amr-resistome.md) the AMR
annotation backbone, [Subsurface Genomics](../topics/subsurface-genomics.md) the
groundwater and contamination-plume validation, and
[Microbiome Engineering](../topics/microbiome-engineering.md) the forward-looking
microcosm experiments proposed to turn correlations into tests.

## Sources

- [stmt:eleven-hotspots-atacama; metal_resistance_global_biogeography]
- [stmt:soil-enriched-marine-depleted; metal_resistance_global_biogeography]
- [stmt:low-global-prevalence; metal_resistance_global_biogeography]
- [stmt:coordinate-gap-data-quality; metal_resistance_global_biogeography]
- [stmt:ena-spatial-data-gap; metal_resistance_global_biogeography]
- [stmt:hotspots-provisional; metal_resistance_global_biogeography]
- [stmt:gapmind-narrow-scope; metal_resistance_global_biogeography]
- [stmt:genome-resolved-vs-otu; metal_resistance_global_biogeography]
- [stmt:metal-vs-t4ss-distinct; metal_resistance_global_biogeography]
- [stmt:metal-type-diversity-predicts-niche-breadth; microbeatlas_metal_ecology]
- [stmt:breadth-not-depth-distinguishes-generalists; microbeatlas_metal_ecology]
- [stmt:effect-independent-of-richness-and-genome-size; microbeatlas_metal_ecology]
- [stmt:first-global-metal-niche-link; microbeatlas_metal_ecology]
- [stmt:caveat-direction-not-established; microbeatlas_metal_ecology]
- [stmt:caveat-niche-breadth-sequencing-proxy; microbeatlas_metal_ecology]
- [stmt:caveat-archaeal-underpowered; microbeatlas_metal_ecology]
- [stmt:enigma-groundwater-validation; microbeatlas_metal_ecology]
- [stmt:gdi-definition; soil_frontier_genomics]
- [stmt:forest-cropland-frontiers; soil_frontier_genomics]
- [stmt:clay-shield-null-result; soil_frontier_genomics]
- [stmt:negative-out-of-sample-r2; soil_frontier_genomics]
- [stmt:ph-discovery-bias; soil_frontier_genomics]
- [stmt:gdi-formula-validity-caveat; soil_frontier_genomics]
- [stmt:cog-metal-associations; soil_metal_functional_genomics]
- [stmt:dbrda-variance; soil_metal_functional_genomics]
- [stmt:copper-trade-offs; soil_metal_functional_genomics]
- [stmt:cocontamination-confound; soil_metal_functional_genomics]
- [stmt:chromium-lead-strongest; soil_metal_functional_genomics]
- [stmt:t4ss-prevalence-environmental-mags; t4ss_cazy_environmental_hgt]
- [stmt:t4ss-cazy-synteny; t4ss_cazy_environmental_hgt]
- [stmt:gt2-metal-resistance-link; t4ss_cazy_environmental_hgt]
- [stmt:cross-phylum-hgt-events; t4ss_cazy_environmental_hgt]
- [stmt:hgt-conjugative-transfer-claim; t4ss_cazy_environmental_hgt]
- [stmt:caveat-associative-not-causal; t4ss_cazy_environmental_hgt]
- [stmt:node4915-eight-phyla; t4ss_cazy_environmental_hgt]
- [stmt:biome-enrichment-marine-rhizosphere; t4ss_cazy_environmental_hgt]
