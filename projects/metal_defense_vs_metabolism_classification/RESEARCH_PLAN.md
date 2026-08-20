# Research Plan: Metal Defense vs. Metal Metabolism Classification Framework

## Research Question

Can bacterial metal-related proteins be reliably classified into defense (toxicity
resistance) vs. metabolism (adaptive utilization) categories, and what are the
phylogenetic distributions and ecological signatures of each class?

## Hypotheses

- **H1**: Metal defense genes are broadly distributed across phyla and associated with
  contaminated or high-metal-concentration environments.
- **H2**: Metal metabolism genes (exotic metal utilization, critical mineral acquisition)
  are phylogenetically restricted and show habitat-specific enrichment in pristine
  or redox-active environments where those metals are available.
- **H3**: A small number of lineages (e.g., specific Actinobacteria, Chloroflexota)
  carry high densities of *both* classes, suggesting dual specialization in metal-rich
  niches.

## Scientific Context

Bacterial metal biology spans two distinct adaptive strategies:

**Metal defense**: proteins that protect the cell from toxic metal concentrations —
efflux pumps (CopA, CzcA, ArsB), metallothioneins, metal-specific transcription
regulators (MerR family), detoxification enzymes (arsenate reductase, chromate
reductase), and periplasmic sequestration proteins.

**Metal metabolism**: proteins that exploit metals as functional cofactors or
substrates beyond standard biology — lanthanide-dependent methanol dehydrogenase
(XoxF), molybdenum-dependent nitrogenase variants, mycothiol-dependent
malonylpyruvate isomerase in metal detox pathways (bridging both classes), exotic
metal-dependent oxidoreductases, and critical mineral acquisition systems.

Current databases (AMRFinderPlus, CARD) focus on resistance, not metabolism. KEGG
metal categories mix both. This project builds the first explicit, pangenome-scale
classification of these two classes and tests whether they show distinct phylogenetic
and ecological signals.

## Approach

### NB01: Seed List and Annotation Mapping (`01_seed_list_and_annotation.ipynb`)

**Goal**: Build a curated seed list of metal defense and metabolism genes; map to
pangenome annotation vocabulary.

1. Compile seed lists from:
   - AMRFinderPlus metal resistance nodes (defense seeds)
   - KEGG module M00917 (lanthanide processing, metabolism seeds)
   - COG category P (inorganic ion transport and metabolism — mixed; curate manually)
   - Literature: XoxF MDH, NiSOD (K00518), mycothiol pathway KOs (metabolism)
   - Metal efflux KOs: K02585 (CopA), K07636 (CzcA), K03455 (ArsB), K01551 (CopB)
2. Assign each seed a primary class label (defense / metabolism / ambiguous) with
   literature justification.
3. Map seeds to annotation vocabulary in `kbase.ke_pangenome.eggnog_mapper_annotations`
   (KO, COG, product name) and `kbase.ke_pangenome.genome_gene` (InterPro domains).
4. Export: `data/seed_list.tsv`, `data/annotation_vocab_map.tsv`

### NB02: Pangenome Classification (`02_pangenome_classification.ipynb`)

**Goal**: Classify all metal-annotated gene clusters in the pangenome.

1. Pull all gene clusters with COG category P or metal-related KO annotations.
2. Assign class (defense / metabolism / ambiguous) from seed list mapping; propagate
   to unannotated clusters by nearest-annotated-neighbor in cluster similarity space
   if available, otherwise mark as unclassified.
3. Compute genome-level counts of defense and metabolism genes.
4. Export: `data/gene_cluster_classification.tsv`, `data/genome_metal_gene_counts.tsv`

### NB03: Phylogenetic Distribution (`03_phylogenetic_distribution.ipynb`)

**Goal**: Characterize the phylogenetic structure of each class.

1. Compute phylum- and order-level prevalence for defense vs. metabolism genes.
2. Fisher's exact test with BH-FDR correction for enrichment at each taxonomic rank.
3. Compute Pagel's λ for defense-gene count and metabolism-gene count on GTDB tree.
4. Test H3: identify lineages with high counts of both classes (dual specialists).
5. Export: `data/phylum_prevalence.tsv`, `data/pagel_lambda_results.tsv`
6. Figures: volcano plot, dual-specialist scatter, phylogenetic heatmap

### NB04: Ecological Signature (`04_ecological_signature.ipynb`)

**Goal**: Test whether defense vs. metabolism gene loads associate with distinct
habitat types.

1. Join genome-level counts to habitat metadata from `nmdc.ncbi_biosamples`
   (biome, metal concentration, contamination status via MIxS fields).
2. Model: defense ~ contamination_index + phylum + genome_size (linear regression).
3. Model: metabolism ~ biome_type + phylum + genome_size.
4. Test H1 (defense enriched in contaminated) and H2 (metabolism enriched in pristine/
   metal-rich pristine habitats).
5. Export: `data/ecological_model_results.tsv`
6. Figures: boxplots by biome, contamination gradient scatter

### NB05: ENIGMA Application (`05_enigma_application.ipynb`)

**Goal**: Apply the classifier to ENIGMA lab isolates to identify experimental candidates.

1. Query `enigma.genome_depot_enigma` gene annotations; classify all metal genes
   using the vocabulary map from NB01.
2. Compute per-isolate defense and metabolism gene counts.
3. Rank isolates by: high metabolism score (novel targets) or high defense score
   (adaptation to site conditions).
4. Cross-reference with Jen's canonical isolate list.
5. Export: `data/enigma_isolate_metal_classification.tsv`
6. Output: ranked shortlist of high-priority experimental isolates

## Data Sources

| Source | Table/Resource | Purpose |
|---|---|---|
| KBase pangenome | `kbase.ke_pangenome.eggnog_mapper_annotations` | Gene annotation (KO, COG, product) |
| KBase pangenome | `kbase.ke_pangenome.genome`, `gtdb_taxonomy_r214v1` | Taxonomy, genome quality |
| KBase pangenome | `kbase.ke_pangenome.genome_gene` | InterPro domains |
| NMDC biosamples | `nmdc.ncbi_biosamples` | Habitat and geochemical metadata |
| Enigma Genome Depot | `enigma.genome_depot_enigma` | Isolate genome annotations |
| AMRFinderPlus | External (download) | Defense seed list |

## Expected Outputs

- `data/seed_list.tsv` — curated gene seed list with class labels
- `data/annotation_vocab_map.tsv` — seed-to-pangenome annotation mapping
- `data/gene_cluster_classification.tsv` — all classified metal gene clusters
- `data/genome_metal_gene_counts.tsv` — per-genome defense and metabolism counts
- `data/phylum_prevalence.tsv` — phylum-level prevalence by class
- `data/pagel_lambda_results.tsv` — phylogenetic signal estimates
- `data/ecological_model_results.tsv` — habitat association models
- `data/enigma_isolate_metal_classification.tsv` — ENIGMA isolate rankings
- Key figures: volcano plots, dual-specialist scatter, ecological boxplots

## Known Risks and Mitigations

| Risk | Mitigation |
|---|---|
| COG category P is heterogeneous; many housekeeping metal-binding proteins will be included | Manual curation of seed list; exclude generic metal-binding (e.g., ferritin) unless annotated as specific defense/metabolism |
| Many metal genes will be "ambiguous" (serve both roles depending on metal concentration) | Report ambiguous class explicitly; run sensitivity analysis including and excluding ambiguous genes |
| NMDC habitat metadata is patchy | Restrict ecological models to genomes with ≥3 MIxS fields populated; report coverage |
| Phylogenetic models require genome-matched tree | Use GTDB R214 pruned to genomes with metal gene counts; fall back to phylum-level ANOVA if tree too sparse |

## Revision History

- **v1 (2026-06-25)**: Initial plan. Research direction established from committee proposal
  planning meeting (June 2026).

## Authors

- Heather MacGregor, Lawrence Berkeley National Laboratory
