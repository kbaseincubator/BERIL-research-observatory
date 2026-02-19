# Gene-Environment Association Across Pangenome Species

## Research Question

For species with strains isolated from diverse environments, do specific accessory gene clusters show significant over- or under-representation in particular environments? This provides generic infrastructure for linking pangenome gene content to NCBI biosample metadata via within-tenant (`ncbi_env`) and cross-tenant (`nmdc_ncbi_biosamples`) joins.

## Approach

1. **Environmental metadata pivot** (notebook 02): Transform the `ncbi_env` EAV table into per-genome environment categories (human_clinical, host_associated, soil, aquatic, plant_associated, food, engineered, sediment, air). Cross-tenant join with NMDC harmonized ontology labels.
2. **Gene-environment association** (notebook 03): For species with >=10 genomes in >=2 environment categories, test each accessory gene cluster for differential prevalence (Fisher's exact / chi-squared, BH FDR correction). Functional enrichment via COG categories.
## Key Findings

### Environmental Metadata Coverage

- 292,913 genomes in the pangenome database have environment metadata from `ncbi_env`
- Dominant categories: human_clinical (104,932), other (81,829), host_associated (51,868), aquatic (33,834)
- 212 species meet the statistical testing threshold (>=2 environment categories with >=10 genomes each)
- Top species by qualifying genome count: *S. aureus* (12,906), *K. pneumoniae* (12,888), *S. pneumoniae* (7,933), *S. enterica* (6,838)

### S. aureus Gene-Environment Associations (Proof of Concept)

- **13,351 of 133,007** accessory gene clusters (10.0%) show significant differential prevalence across 5 environment categories (q < 0.05, BH FDR correction)
- **Food enrichment dominates**: 4,681 clusters enriched in food isolates, followed by host_associated (4,068), aquatic (1,678), air (1,549), human_clinical (1,375)
- Food dominance is unexpected for a primarily clinical/commensal pathogen and may reflect accessory genes supporting persistence in food-processing environments (biofilm formation, stress tolerance, antimicrobial resistance)

### COG Enrichment in Environment-Associated Genes (S. aureus)

- 5,134 of 13,351 significant clusters have COG annotations
- Top COGs: S (unknown function, 1,698), L (replication/repair, 813), M (cell wall, 505), K (transcription, 348), E (amino acid, 295)
- **Mobilome (X) enriched** in environment-associated vs background accessory genes, consistent with horizontal gene transfer driving niche adaptation

## Interpretation

### Literature Context

- **S. aureus food enrichment** aligns with Richardson et al. (2018), who found that *S. aureus* food isolates carry distinct accessory gene repertoires compared to clinical isolates, including genes for biofilm formation and osmotic stress resistance. Weinert et al. (2012) showed *S. aureus* has undergone multiple host-switching events throughout history, suggesting host/niche adaptation is a recurring evolutionary pattern.
- **Mobilome enrichment** is consistent with the broader understanding that horizontal gene transfer drives bacterial niche adaptation (Ochman et al., 2000). Mobile genetic elements (phages, plasmids, transposons) are major vehicles for accessory gene acquisition and can enable rapid adaptation to new environments (Koskella & Brockhurst, 2014).
- **Pangenome-environment associations** are an emerging area. Gautreau et al. (2020) developed partitioned pangenome graphs that distinguish persistent, shell, and cloud gene families -- our framework complements this by testing individual accessory clusters for environment-specific prevalence.
- **Environment shapes pangenomes**: Maistrenko et al. (2020) showed environmental preferences explain up to 49% of prokaryotic within-species diversity, stronger than phylogenetic inertia. This validates the approach of linking gene cluster presence/absence to environmental metadata.
- **Pan-GWAS methods** (Brynildsrud et al., 2016; Lees et al., 2018) provide more sophisticated alternatives to our Fisher's exact approach by controlling for population structure -- a natural extension for future work.
- **Novel contribution**: The BERDL pangenome database enables gene-environment association testing at unprecedented scale (133,007 clusters x 12,913 genomes for a single species). The EAV-to-category pivot of `ncbi_env` metadata provides a reusable environmental classification for any BERDL pangenome species.

### Limitations

- Environment categorization from free-text `isolation_source` is heuristic and lossy (e.g., "leaves" maps to "other" not "plant_associated")
- `ncbi_env` coverage is incomplete; many genomes lack environment metadata
- Spark Connect auth timeout (~40 min) limits single-query size; species with >10K genomes need query batching for the full multi-species analysis
- Only one species (S. aureus) completed as proof of concept due to timeout constraints
- COG enrichment uses a sampled background (5,000 clusters) rather than all accessory clusters

### Future Directions

1. Batch large-species queries (chunk genomes into groups of ~2,000) to stay under auth timeout
2. Extend to mid-size species (Campylobacter, Enterococcus, Listeria -- 1,000-2,000 genomes each) that can complete within timeout
3. Improve environment categorization (map "leaves", "tree leaf surface" to plant_associated)
4. Annotate significant S. aureus food-enriched clusters to identify specific functions (biofilm, AMR, stress tolerance)
5. Formal statistical comparison of enrichment patterns across species

## Visualizations

| Figure | Description |
|--------|-------------|
| `volcano_gene_env.png` | Volcano plot of prevalence difference vs q-value for S. aureus accessory gene clusters |
| `cog_enrichment.png` | COG category enrichment in environment-associated vs background accessory genes (S. aureus) |

## Data Files

| File | Description |
|------|-------------|
| `data/genome_env_metadata.csv` | Per-genome environment metadata (292,913 genomes), produced by notebook 02 |
| `data/gene_env_summary.csv` | Cross-species summary of gene-environment association results |
| `data/gene_env_Staphylococcus_aureus.csv` | Per-cluster association results for S. aureus (133,007 rows) |

## Data Sources

| Source | Database | Table(s) |
|--------|----------|----------|
| Genomes | `kbase_ke_pangenome` | `genome` |
| Environment (EAV) | `kbase_ke_pangenome` | `ncbi_env` |
| NCBI biosamples | `nmdc_ncbi_biosamples` | `biosamples_flattened`, `env_triads_flattened` |
| Gene clusters | `kbase_ke_pangenome` | `gene_cluster`, `gene`, `gene_genecluster_junction` |
| Annotations | `kbase_ke_pangenome` | `eggnog_mapper_annotations` |

## Notebooks

| Notebook | Purpose | Runtime |
|----------|---------|---------|
| `02_env_metadata_exploration.ipynb` | EAV pivot, cross-tenant NMDC join, environment categorization | ~10 min |
| `03_gene_environment_association.ipynb` | Species selection, statistical tests, COG enrichment | ~30 min (S. aureus) |

## Known Issues

- **Spark Connect auth timeout**: Sessions expire after ~40 minutes (KBaseAuthServerInterceptor). Notebook 03 includes `refresh_spark()` to restart the session between queries.
- **Environment categorization gap**: "leaves" and "tree leaf surface" in `isolation_source` don't map to `plant_associated`; they fall into `other`.

## Reproduction

1. Upload notebooks to BERDL JupyterHub
2. Run in order: 02 -> 03 (notebook 03 depends on `data/genome_env_metadata.csv` from 02)
3. Both notebooks require Spark Connect

## Related Projects

- `listeria_pangenome_case/` -- *L. monocytogenes* pathway completeness case study using GapMind predictions
- `temporal_core_dynamics/` -- Uses same `ncbi_env` EAV pivot pattern

## References

- Brockhurst MA, et al. (2019). The ecology and evolution of pangenomes. *Curr Biol*, 29(20), R1094-R1103.
- Brynildsrud O, et al. (2016). Rapid scoring of genes in microbial pan-genome-wide association studies with Scoary. *Genome Biol*, 17, 238.
- Gautreau G, et al. (2020). PPanGGOLiN: depicting microbial diversity via a partitioned pangenome graph. *PLoS Comput Biol*, 16(3), e1007732.
- Koskella B, Brockhurst MA. (2014). Bacteria-phage coevolution as a driver of ecological and evolutionary processes in microbial communities. *FEMS Microbiol Rev*, 38(5), 916-931.
- Lees JA, et al. (2018). pyseer: a comprehensive tool for microbial pangenome-wide association studies. *Bioinformatics*, 34(24), 4310-4312.
- Maistrenko OM, et al. (2020). Disentangling the impact of environmental and phylogenetic constraints on prokaryotic within-species diversity. *ISME J*, 14(5), 1247-1259.
- Ochman H, Lawrence JG, Groisman EA. (2000). Lateral gene transfer and the nature of bacterial innovation. *Nature*, 405(6784), 299-304.
- Richardson EJ, et al. (2018). Gene exchange drives the ecological success of a multi-host bacterial pathogen. *Nat Ecol Evol*, 2(9), 1468-1478.
- Tettelin H, et al. (2005). Genome analysis of multiple pathogenic isolates of *Streptococcus agalactiae*: implications for the microbial "pan-genome." *PNAS*, 102(39), 13950-13955.
- Weinert LA, et al. (2012). Molecular dating of human-to-bovid host jumps by *Staphylococcus aureus* reveals an association with the spread of domestication. *Biol Lett*, 8(5), 829-832.

## Authors

- **Mark A. Miller** (Lawrence Berkeley National Lab)
