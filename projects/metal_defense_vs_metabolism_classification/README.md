# Metal Defense vs. Metal Metabolism: A Classification Framework for Bacterial Metal Proteins

## Research Question

Can bacterial metal-related proteins be reliably classified into "metal defense" (toxic
metal resistance) vs. "metal metabolism" (adaptive metal utilization and critical mineral
acquisition) categories, and what are the phylogenetic distributions and ecological
signatures of each class across the BERDL pangenome?

## Status

Completed — metal defense genes are near-universal (98.6%) while metal metabolism genes are phylogenetically selective (54.0%) and specifically enriched in contaminated habitats (phylum-adj OR=1.28, q=0.002); co-occurrence is the modal state (53.8%); top ENIGMA candidates identified. (Submission pending; see SUBMISSION_FAILED.md.)

## Background

Metal-related genes in bacteria serve fundamentally different adaptive roles. Some
confer tolerance to toxic metal concentrations (defense systems: efflux pumps,
sequestration proteins, detoxification enzymes), while others enable the organism to
exploit rare or exotic metals as cofactors or substrates (metabolic systems: lanthanide
binding, unusual metal-dependent enzymes, critical mineral acquisition).

These two classes are often conflated in AMR and metal resistance databases, which
focus on resistance rather than metabolic function. Distinguishing them is essential
for understanding:
- Which organisms thrive at contaminated vs. metal-rich pristine sites
- Which metal functions are adaptive vs. constitutive
- Which genes are candidates for experimental validation of ecological adaptation

This project builds a classification scheme grounded in known functional categories
(COG, KO, InterPro) and applies it across the BERDL pangenome (~27,000 species) and
ENIGMA isolates.

## Approach

1. **Define the classification scheme**: compile a curated seed list of metal defense
   and metal metabolism genes from literature and existing databases (COG category P,
   relevant KO pathways, AMRFinderPlus metal categories).
2. **Annotate across the pangenome**: map seed list to `kbase.ke_pangenome` annotations;
   classify each metal-related gene cluster as defense, metabolism, or ambiguous.
3. **Characterize phylogenetic distributions**: compute phylum- and order-level prevalence
   for each class; test for Pagel's λ to quantify phylogenetic signal.
4. **Ecological signature**: link distributions to habitat metadata (NMDC, MIxS) to
   identify whether defense vs. metabolism classes associate with different environment
   types (contaminated, pristine, redox-stratified, etc.).
5. **ENIGMA application**: apply classifier to ENIGMA isolate genomes to identify
   which isolates carry defense-only vs. metabolism-enriched gene complements.
6. **Candidate identification**: flag genes with strong phylogenetic restriction and
   habitat correlation as high-priority experimental targets.

## Data Sources

| Source | Table/Resource | Purpose |
|---|---|---|
| KBase pangenome | `kbase.ke_pangenome` | Gene annotations, COG, KO, InterPro, taxonomy |
| NMDC biosamples | `nmdc.ncbi_biosamples` | Habitat and geochemical metadata |
| Enigma Genome Depot | `enigma.genome_depot_enigma` | Isolate application of classifier |
| AMRFinderPlus metal categories | External database | Defense seed list |

## Notebooks

| NB | File | Description |
|---|---|---|
| 01 | `01_seed_list_and_annotation.ipynb` | Compile seed list; map to pangenome annotations |
| 02 | `02_pangenome_classification.ipynb` | Classify all metal-related clusters; compute prevalences |
| 03 | `03_phylogenetic_distribution.ipynb` | Pagel's λ, phylum/order enrichment, co-occurrence |
| 04 | `04_ecological_signature.ipynb` | Habitat correlation for each class |
| 05 | `05_enigma_application.ipynb` | Apply to ENIGMA isolates; rank experimental candidates |

## Expected Outcomes

- A reusable classification table mapping annotated metal genes to defense vs. metabolism
- Phylum-level prevalence profiles showing which lineages specialize in each strategy
- Ranked list of ENIGMA isolates with strong defense or metabolism signatures for
  experimental prioritization
- Identification of phylogenetically restricted metal metabolism genes as high-value
  targets for adaptive function studies

## Quick Links

- [Research Plan](RESEARCH_PLAN.md)
- [Latest Review](REVIEW_4.md)

## Reproduction

All five notebooks can be re-executed from JupyterHub (Kernel → Restart & Run All) or via nbconvert writing to a separate output file (see `docs/pitfalls.md` — `--inplace` silently drops outputs on this JupyterHub):

| Notebook | Live Spark required? | Notes |
|----------|----------------------|-------|
| `01_seed_list_and_annotation.ipynb` | Yes (first run) | Cached: `data/seed_list.tsv`, `data/annotation_vocab_map.parquet` |
| `02_pangenome_classification.ipynb` | Yes (first run) | Cached: `data/genome_metal_counts.parquet`, `data/species_trait_matrix.csv` |
| `03_phylogenetic_distribution.ipynb` | No (reads parquets) | Requires R + phytools for Pagel's λ; uses `RSCRIPT=/home/hmacgregor/r_env/bin/Rscript` |
| `04_ecological_signature.ipynb` | Yes (first run) | Cached: `data/genome_env.parquet`, `data/ecology_results_phylum_adj.csv` |
| `05_enigma_application.ipynb` | Yes (first run) | Cached: `data/enigma_isolate_classification.parquet` |

After caches exist, NB03 is the only notebook requiring non-standard dependencies (R, phytools). Seaborg cluster is required for first-run Spark queries.

## Authors

Heather MacGregor, Lawrence Berkeley National Laboratory

## Related Projects

- [`mycothiol_detox_module`](../mycothiol_detox_module/) — template for pangenomic enrichment methodology
- [`metal_resistance_genomic_signatures`](../metal_resistance_genomic_signatures/) — related genomic signatures work
- [`microbeatlas_metal_ecology`](../microbeatlas_metal_ecology/) — ecological context for metal resistance
- [`enigma_isolate_mycothiol_isomerase`](../enigma_isolate_mycothiol_isomerase/) — targeted follow-up for one candidate gene
