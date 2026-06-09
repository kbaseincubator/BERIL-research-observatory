# Report: ENIGMA Carbon Census — A Tiered Knowledge Census of 83 Enrichment Compounds

## Key Findings

### 1. The census is mostly dark: 75 of 83 compounds have no isolate-level utilizer call

The governing result is a gap, not a coverage claim. Of 83 compounds (59 SSO-groundwater + 24 necromass), all 83 resolved to structures (InChIKey via PubChem), 54 linked to KEGG, but only **8 are "callable"** — i.e. have ≥1 ENIGMA-isolate utilizer prediction with a catabolic (compound-degrading) reaction in a genome. The remaining **75/83 (90%) are organism-dark**: the genetic determinants of their utilization are genuinely unknown in this data. This dark list, stratified by reason and chemical class, is the actionable enrichment-design output — it tells the wet lab which enrichments are *discover-new* versus *characterize-known*.

![Discovery funnel](figures/08_funnel.png)

The funnel: 83 compounds → 83 structure-resolved → 54 KEGG-linked → **8 callable**; 75 organism-dark.

Organism-dark breakdown by reason: `kegg_no_rxn_in_genomes` 33, `no_kegg` 29, `only_biosynthetic_signatures` 7, `only_generic_rxns` 6. By class, the dark set is dominated by exactly the predicted classes: Alkaloids 24, Shikimates/Phenylpropanoids 20, Terpenoids 16, Fatty acids 10.

*(Notebooks: 01_identity_resolution, 02_pathway_linkage, 02b_linkage_deepening, 03_organism_mapping, 08_synthesis)*

### 2. H1 (coverage gradient by chemical class) — supported in direction

The 8 callable compounds are overwhelmingly **pollutant-adjacent aromatics**: salicylic acid, 3-hydroxybenzoic acid, 4-hydroxybenzaldehyde, phthalic acid, terephthalic acid (all Shikimates/Phenylpropanoids), plus Phenylethylamine and xanthine (Alkaloids) and Abscisic acid (Terpenoid, a single 2-strain call). Coverage is sharply non-uniform across chemical classes, in the predicted direction: catabolic knowledge concentrates on the aromatic/phthalate subset that curated biodegradation knowledge and KEGG cover, and collapses for most alkaloids and terpenoids. The clean Tier-0 list by class is the enrichment-design deliverable regardless of the formal test.

*(Notebook: 08_synthesis)*

### 3. H2 (cross-module modularity) — not supported beyond a shared aromatic funnel

Among the 8 callable compounds across 800 genomes carrying ≥1 capacity, catabolic versatility is right-skewed (mean 1.19, median 1, max 4 capacities per genome). Co-occurrence is concentrated **within the aromatic block** (mean φ +0.021, 3/10 pairs q<0.05) — expected, because those compounds funnel through one shared protocatechuate/catechol → β-ketoadipate lower pathway, so this is mechanistic coupling, not independent modules. The genuine test is **cross-block** pairs (distinct lower pathways): mean φ +0.007, only 2/15 significant (3-hydroxybenzoic acid + Phenylethylamine φ=+0.057 q=0.031; 4-hydroxybenzaldehyde + Phenylethylamine φ=+0.056 q=0.035), and only 25 genomes carry both an aromatic and a non-aromatic capacity. **Verdict: no broad cross-module modularity.** What *is* supported is phylogenetic concentration — Burkholderiales dominate utilizer counts, and high-versatility genera (Polaromonas, Alcaligenes, Burkholderia, Paraburkholderia, Comamonas, Hydrogenophaga) cluster in that order.

![Catabolic co-occurrence](figures/05_cooccurrence.png)
![Genus versatility](figures/05_genus_versatility.png)

*(Notebook: 05_cooccurrence)*

### 4. H3 (source-tracking: groundwater vs necromass) — untestable / confounded, reported as such

Of the 8 callable compounds, only 2 are necromass-sourced (terephthalic + phthalic acid), and both are phthalate-class aromatics with Actinomycetota-heavy utilizers. Source is therefore inseparable from chemical class at n=2 — there is no honest statistical contrast to run. Rather than fabricate a confounded result, NB07 was reframed as a straight SSO field-occurrence atlas (Zhou Lab 16S, `enigma_coral` bricks): 62 of the implicated utilizer genera are observed in the SSO field at genus resolution, with top field prevalences ~0.7–0.9 for the aromatic utilizers (e.g. 3-hydroxybenzoic-acid utilizers at 0.90 field prevalence).

*(Notebook: 07_environmental_atlas)*

### 5. Deliverables (a) + (b): tier-stratified isolate predictions, phylogenetically concentrated

**Deliverable (a)** — 569 ENIGMA-isolate utilizer prediction rows across the 8 callable compounds. The aromatics carry the bulk: salicylic acid 129 strains, 3-hydroxybenzoic acid 127, 4-hydroxybenzaldehyde 125; terephthalic acid 34 (all high-certainty); phthalic acid 36; Phenylethylamine 28; xanthine 13; Abscisic acid 2.

**Deliverable (b)** — 494 strain placements on the GTDB taxonomy (359 distinct strains), each carrying a tier × certainty score: 64 high-certainty (gene-complete pathway, Tier 2), 387 medium (Tier 2 pathway), 43 medium (Tier 3 signature enzyme). Utilizers concentrate in **Pseudomonadota / Burkholderiales**, with Pseudomonadales and Sphingomonadales contributing to specific compounds (e.g. Sphingomonadales 47 strains for 4-hydroxybenzaldehyde).

![Utilizer genera](figures/04_utilizer_genera.png)
![Phylogenetic order map](figures/06_phylo_order_map.png)
![Certainty composition](figures/06_certainty_composition.png)

*(Notebooks: 04_enigma_utilizers, 06_phylo_maps)*

### 6. Deliverable (c), global arm: a cross-environment abundance atlas for the 86 implicated genera

Beyond the local SSO field atlas, the implicated utilizer genera were placed across global environments — terrestrial/freshwater (NMDC, `kbase.nmdc_arkin`) and marine (Planet Microbe, as a contrast). **This is a biome-abundance proxy, not catabolic activity**: no environmental dataset measures the census compounds, so genus abundance indicates where the *organisms* live, not where the *compounds are degraded*.

![Environmental atlas heatmap](figures/07b_env_atlas_heatmap.png)

NMDC scale: **3825 taxonomy-bearing metagenomes** (denominator = covstats files with taxonomy), 83/86 genera detected in 1719 metagenomes, **99% sample-labeled** via two independent ontologies (ENVO MIxS triad + GOLD ecosystem path). Macro-environment distribution: soil 2260, freshwater 723, periphyton 472, plant 119, sediment 42.

Soil-vs-freshwater abundance contrast (**exploratory** — see Limitations) recovers textbook biogeography: soil-enriched genera are classic soil taxa (Mycobacterium log2 +5.09, Terriglobus +5.29, Nitrobacter +4.79, Afipia, Streptomyces, Nocardioides, Mesorhizobium), and freshwater-enriched genera are aquatic Betaproteobacteria (Cellvibrio log2 −2.19, Curvibacter, Rhodoferax, Comamonas, Acidovorax). The newly surfaced **periphyton** class (freshwater biofilms: epilithon/epipsammon/epiphyton) is a strong reservoir — Burkholderiales/Comamonadaceae (Rhizobacter, Variovorax, Polaromonas, Methylibium, Sphingomonas, Hydrogenophaga) at ~96–97% prevalence and mean relative abundance ~0.005–0.009.

![Soil/freshwater enrichment](figures/07b_soil_fresh_enrichment.png)

**Label-free outlier discovery** (the most defensible signal, robust to label noise): top genus×sample relative-abundance spikes occur in periphyton (Nocardioides 0.43 in epipsammon, Hydrogenophaga 0.28 in epiphyton) and soil (Mycobacterium 0.22). Outliers peak in periphyton (34 genera) and soil (32).

Marine (Planet Microbe, 302 runs): 68/68 listed genera show positive abundance, but marine is **mostly a negative biome contrast** — terrestrial/freshwater genera sit at ~1e-3 to 1e-4 in open ocean. Genuine marine members are the exception (Alteromonas 0.048 in 240/302 runs, prevalence 0.79; cosmopolitan Pseudomonas 0.011, Sphingomonas 0.0063).

*(Notebook: 07b_environmental_atlas_global)*

## Discoveries

- The ENIGMA Carbon Census is **90% organism-dark** (75/83 compounds with no isolate utilizer call) — the actionable product of a knowledge census can be the map of ignorance, and that map is biased exactly by chemical class (alkaloids/terpenoids dark, aromatics callable).
- Callable catabolic capacity among these compounds is **phylogenetically concentrated in Burkholderiales** rather than modularly distributed: cross-module co-occurrence is near-zero (mean φ +0.007), so versatility is a clade trait, not a portable module set.
- A **periphyton (freshwater-biofilm) ENVO/GOLD class**, separated out from bulk freshwater, surfaces a Comamonadaceae/Burkholderiales reservoir at ~97% prevalence that bulk-water labels hide — relevant for siting SSO-relevant enrichments.
- Both NMDC covstats and Planet Microbe `taxonomy.name` are **species-level**; any genus-level abundance claim requires species→genus aggregation first. Filtering on bare genus names silently matches only near-zero genus-rank reference rows (the bug that first showed 0/68 marine genera).

## Performance Notes

- The NMDC abundance denominator is the set of covstats files that actually carry taxonomy (**3825**), not the larger `sample_file_lookup` row count (~6700) — using the lookup count deflates relative abundances by ~1.75×.
- Sample-level environment labels come from `nmdc_metadata.biosample_set` (joined to covstats `sample_id` via `kbase.nmdc_arkin.sample_file_lookup`), which gives 99% coverage across two ontologies — far better than `study_table` GOLD alone (~13%).

## Results

### The callable-compound table (the table a wet-lab planner reads)

| Compound | Source | NPC pathway | Best tier | n strains (a) | n high-cert | n genera (b) | n field genera (c) | top field prev |
|---|---|---|---|---|---|---|---|---|
| salicylic acid | groundwater | Shikimates/Phenylpropanoids | T2_3_reaction | 129 | 2 | 24 | 20 | 0.86 |
| 3-hydroxybenzoic acid | groundwater | Shikimates/Phenylpropanoids | T2_3_reaction | 127 | 18 | 42 | 33 | 0.90 |
| 4-hydroxybenzaldehyde | groundwater | Shikimates/Phenylpropanoids | T2_3_reaction | 125 | 10 | 34 | 25 | 0.86 |
| phthalic acid | necromass | Shikimates/Phenylpropanoids | T2_3_reaction | 36 | 0 | 15 | 12 | 0.75 |
| terephthalic acid | necromass | Shikimates/Phenylpropanoids | T2_3_reaction | 34 | 34 | 17 | 10 | 0.67 |
| Phenylethylamine | groundwater | Alkaloids | T2_3_reaction | 28 | 0 | 11 | 7 | 0.61 |
| xanthine | groundwater | Alkaloids | T3_kegg | 13 | 0 | 6 | 4 | 0.75 |
| Abscisic acid | groundwater | Terpenoids | T2_3_reaction | 2 | 0 | 1 | 1 | 0.02 |

### Headline numbers

| Metric | Value |
|---|---|
| Compounds in census | 83 |
| Structure-resolved (InChIKey) | 83 |
| KEGG-linked | 54 |
| Callable (≥1 isolate utilizer) | 8 |
| Organism-dark (discovery targets) | 75 (90%) |
| Utilizer strains placed (b) | 359 (64 high-certainty) |
| Utilizer genera in SSO field (c) | 62 |
| NMDC taxonomy-bearing metagenomes (global c) | 3825 |
| Implicated genera detected in NMDC | 83/86 (1719 metagenomes) |
| Planet Microbe runs / genera positive | 302 / 68 of 68 |

## Interpretation

The census behaves exactly as a knowledge product over natural-product secondary metabolites should: catabolic knowledge is real and deep for the **aromatic/phthalate** subset and effectively absent for most alkaloids and terpenoids. The eight callable compounds all route through well-characterized aromatic catabolism (salicylate, hydroxybenzoates, and phthalates converging on protocatechuate/catechol and the β-ketoadipate pathway), which is why their utilizers are numerous and phylogenetically concentrated. The 75 dark compounds are not a failure of method — they are the deliverable: they name where genetic determinants of carbon use are unknown and where enrichment is genuinely discovery-mode.

The environmental atlas adds *where to look*, with an honest ceiling. Because no environmental dataset measures the compounds, the global atlas reports **biome occupancy of the implicated genera**, not catabolic flux. The signal is biologically coherent (soil generalists in soil, aquatic Betaproteobacteria in freshwater, a Comamonadaceae periphyton reservoir, terrestrial taxa rare in open ocean), which validates the linkage chain — but it cannot, and does not, claim that any genus degrades a census compound in any sampled environment.

### Literature Context

- The aromatic convergence onto the **β-ketoadipate / protocatechuate–catechol** funnel is the canonical bacterial route for hydroxybenzoates, salicylate, and phthalates (Harwood & Parales, *Annu. Rev. Microbiol.* 1996), consistent with this census finding that the eight callable aromatics share one lower pathway and therefore co-occur within the aromatic block.
- The dominance of **Burkholderiales / Comamonadaceae** as aromatic degraders and their prevalence in freshwater biofilm/periphyton are well established in environmental microbiology, matching both the versatility ranking (NB05) and the periphyton reservoir (NB07b).
- **Terephthalate/phthalate** catabolism is the best-characterized necromass aromatic here, concentrated in Actinomycetota and Pseudomonadota — consistent with the high-certainty terephthalic-acid call set.

### Novel Contribution

What this census adds beyond what any single database states: (1) a unified, **tier-stratified** linkage from 83 named compounds → structures → pathways → ENIGMA isolate strains → GTDB phylogeny → SSO field occurrence → global biome abundance, with the gap (Tier 0) treated as a first-class result; (2) a **quantified dark-fraction** (90%) with per-class, per-reason structure to drive enrichment prioritization; (3) a **periphyton-resolved** abundance reservoir for the implicated genera that bulk-environment labels obscure.

### Limitations

- **The soil-vs-freshwater enrichment p/q-values are exploratory and not calibrated.** Each metagenome is treated as an independent observation in a rank test over compositional, zero-inflated relative abundances; with thousands of non-independent samples this inflates significance massively (all 83 genera reach q<0.05, many at q~1e-70). The *direction and rank* of the contrast are trustworthy and biologically sensible; the *p-values are not* and should not be quoted as calibrated significance. The label-free outlier mode (Arm B) is the more defensible discovery signal.
- **Abundance ≠ activity.** No environmental dataset measures the census compounds; the entire global atlas is a biome-occupancy proxy. A genus being enriched in soil does not mean it degrades the compound there.
- **H3 is genuinely untestable** with these compounds (n=2 necromass callables, fully confounded with phthalate chemistry) — reported as such rather than forced.
- **Catabolic-direction filter dependence.** The callable count (8) rests on a genome-prevalence-<10% signature-reaction filter that keeps a reaction only if it is catabolic *for the compound* (KEGG degradation map membership or a 3-reaction curated allowlist). A different filter would move the callable/dark boundary; the dark fraction is conditional on this choice.
- **Marine arm is small and gene-blind** (302 PM runs; presence/abundance only), suitable only as a negative biome contrast.
- The pangenome↔ENIGMA taxonomic bridge is genus-level at best; isolate-specific transfer of pangenome Tier-2 reconstructions is avoided in favor of direct genome_depot annotation.

## Data

### Sources
| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| PubChem (external) | PUG-REST | Name → CID → InChIKey/SMILES + KEGG/ChEBI/ModelSEED cross-refs (identity resolution) |
| ModelSEED biochemistry | compound/reaction/enzyme | Compound → reaction → enzyme linkage (Tier 2/3) |
| `kbase_ke_pangenome` | functional annotations (KEGG/EC/eggNOG) | Enzyme presence across GTDB species pangenomes; null denominator (3109 genomes) |
| `kescience_fitnessbrowser` | RB-TnSeq carbon-source experiments | Measured utilization (Tier 1 channel) |
| `enigma_genome_depot_enigma` | `browser_protein`↔`_kegg_reactions`/`_kegg_orthologs`/`_ec_numbers`, `browser_gene`→`browser_genome`→`browser_strain`→`browser_taxon` | Catabolic annotations directly on ENIGMA isolate proteins; isolate→strain→NCBI-taxid crosswalk (deliverables a, b) |
| `enigma` (SSO field) | Zhou Lab 16S, `enigma_coral` bricks | SSO field genus occurrence (deliverable c, local) |
| `kbase.nmdc_arkin` + `nmdc_metadata` | `covstats_taxonomy_rollup`, `sample_file_lookup`, `biosample_set` | Terrestrial/freshwater genus abundance + ENVO/GOLD env labels (deliverable c, global) |
| `planetmicrobe.planetmicrobe` | `run_to_taxonomy`, `taxonomy`, `run`/`experiment`/`sample`/`project`/`campaign` | Marine genus abundance contrast (deliverable c, global) |

### Generated Data
| File | Rows | Description |
|------|------|-------------|
| `data/resolved_compounds.tsv` | 83 | Compound → InChIKey/SMILES + DB cross-refs |
| `data/compound_linkage.tsv` / `_deepened.tsv` | 83 | Per-compound pathway/enzyme linkage + tier |
| `data/compound_organism_predictions.tsv` | 948 | Pathway/enzyme → organism predictions |
| `data/compound_organism_dark.tsv` | 75 | Organism-dark compounds + reason |
| `data/enigma_utilizer_predictions.tsv` | 569 | Deliverable (a): per-compound ENIGMA isolate utilizers |
| `data/phylo_utilizer_map.tsv` | 494 | Deliverable (b): strain placements + certainty |
| `data/cooccurrence_matrix.tsv` | 28 | H2 pairwise co-occurrence (φ, p, q) |
| `data/environmental_atlas.tsv` | 156 | Deliverable (c) local: SSO field genus occurrence |
| `data/env_atlas_global.tsv` | 400 | Deliverable (c) global: genus × biome abundance (NMDC + PM) |
| `data/env_enrichment_soil_fresh.tsv` | 83 | Soil-vs-freshwater abundance contrast (exploratory) |
| `data/env_outlier_samples.tsv` | 249 | Label-free top genus×sample abundance spikes |
| `data/census_master_summary.tsv` | 83 | One row per compound: the master census table |

## Supporting Evidence

### Notebooks
| Notebook | Purpose |
|----------|---------|
| `00_compound_profile.ipynb` | Load xlsx; profile 83 compounds (class, source, MW/LogP) |
| `01_identity_resolution.ipynb` | Name → PubChem CID → InChIKey/SMILES + cross-refs |
| `02_pathway_linkage.ipynb` / `02b_linkage_deepening.ipynb` | Compound → pathway/enzyme, multi-channel + Phase-1 gate |
| `03_organism_mapping.ipynb` | Pathway/enzyme → organisms; catabolic-direction filter |
| `04_enigma_utilizers.ipynb` | Deliverable (a): ENIGMA isolate utilizer table |
| `05_cooccurrence.ipynb` | H2: within/cross-block co-occurrence + versatility |
| `06_phylo_maps.ipynb` | Deliverable (b): GTDB strain placements + certainty |
| `07_environmental_atlas.ipynb` | Deliverable (c) local: SSO field occurrence atlas |
| `07b_environmental_atlas_global.ipynb` | Deliverable (c) global: NMDC + Planet Microbe abundance atlas |
| `08_synthesis.ipynb` | Assemble three deliverables + gap map; master table |

### Figures
| Figure | Description |
|--------|-------------|
| `00_class_composition.png`, `00_mw_logp.png` | Compound class composition and MW/LogP space |
| `02_linkage_coverage.png`, `02b_linkage_deepened.png` | Pathway-linkage coverage by class |
| `03_organism_calls.png` | Organism-mapping call counts |
| `04_utilizer_genera.png` | Deliverable (a) utilizer genera |
| `05_cooccurrence.png`, `05_genus_versatility.png`, `05_versatility.png` | H2 co-occurrence and versatility |
| `06_phylo_order_map.png`, `06_certainty_composition.png` | Deliverable (b) phylogeny and certainty |
| `07_field_occurrence.png` | SSO field occurrence (local atlas) |
| `07b_env_atlas_heatmap.png`, `07b_soil_fresh_enrichment.png` | Global biome abundance atlas + soil/fresh contrast |
| `08_funnel.png` | Discovery funnel (83 → callable) |

## Future Directions

1. **Wet-lab the dark set first.** The 75 organism-dark compounds — especially alkaloids and terpenoids — are discovery-mode enrichment targets; pair anonymous community enrichment with metagenomics to recover the missing catabolic genes.
2. **Promote Tier 5→3 via literature mining.** Targeted PaperBLAST/PubMed mining for alkaloid/terpenoid catabolic enzymes, searched back into the genomes, would convert some dark compounds to callable without new experiments.
3. **Calibrate the environmental contrast properly.** Replace the per-sample rank test with a study-aware mixed model (or sample-level permutation respecting study structure) to get defensible enrichment statistics rather than the current exploratory ranking.
4. **Periphyton-sited enrichment.** The Comamonadaceae periphyton reservoir suggests freshwater-biofilm inocula for the aromatic-utilizer enrichments.

## References
See `references.md` for the full list. Core data sources: PubChem (Kim et al., *Nucleic Acids Res.* 2023); KBase (Arkin et al., *Nat. Biotechnol.* 2018); Fitness Browser / RB-TnSeq (Price et al., *Nature* 2018); GTDB (Parks et al., *Nucleic Acids Res.* 2022); ModelSEED (Henry et al., *Nat. Biotechnol.* 2010); NMDC (Eloe-Fadrosh et al., *Nat. Microbiol.* 2022); Planet Microbe (Ponsero et al., *GigaScience* 2021); aromatic catabolism (Harwood & Parales, *Annu. Rev. Microbiol.* 1996).
