# Report: Contamination Gradient vs Functional Potential in ENIGMA Communities

## Key Findings

### H1 not supported in current genus-level model
Across 108 overlapping ENIGMA samples, contamination index was not significantly associated with inferred stress-related functional potential in either mapping mode.

![Stress score vs contamination index by mapping mode](figures/contamination_vs_functional_score.png)

- `relaxed_all_clades`, `site_stress_score`: rho = 0.0587, p = 0.546, permutation p = 0.531, beta = 0.000473, OLS p = 0.0681
- `strict_single_clade`, `site_stress_score`: rho = 0.0682, p = 0.483, permutation p = 0.463, beta = 0.000444, OLS p = 0.127
- `relaxed_all_clades`, `site_defense_score`: rho = 0.0587, p = 0.546, permutation p = 0.531, beta = 0.000946, OLS p = 0.0681
- `strict_single_clade`, `site_defense_score`: rho = 0.0682, p = 0.483, permutation p = 0.463, beta = 0.000888, OLS p = 0.127

*(Notebook: `03_contamination_functional_models.ipynb`)*

### Mapping sensitivity changed magnitude, not conclusion
The strict vs relaxed bridge sensitivity analysis showed small numeric differences but no significance shift:
- `site_metabolism_score` remained null in both modes (`relaxed`: rho = -0.00645, p = 0.947; `strict`: rho = -0.0147, p = 0.880).
- `site_mobilome_score` was `constant_feature` in both modes (no variance; no inferential test).

![Mapping and feature coverage by mode](figures/mapping_coverage_by_mode.png)

Coverage diagnostics from upstream outputs:
- 1,392 ENIGMA genera observed
- 530 mapped genera, 862 unmapped genera
- Bridge table rows: 8,242 (many-to-many genus-to-clade expansion)
- Functional feature rows: 3,180 (530 genera x 3 features x 2 modes)

*(Notebook: `02_taxonomy_bridge_functional_features.ipynb`; data: `taxon_bridge.tsv`, `taxon_functional_features.tsv`)*

### Contamination index was broad but right-skewed
NB03 built contamination index from 8 metal columns (`arsenic`, `cadmium`, `chromium`, `copper`, `lead`, `nickel`, `uranium`, `zinc`) using per-metal `log1p` z-scoring and row-wise mean.

- n = 108 samples
- min = -0.448, max = 3.836
- median = -0.271, IQR = [-0.363, 0.053]

![Distribution of contamination index](figures/contamination_index_distribution.png)

*(Notebook: `03_contamination_functional_models.ipynb`)*

## Results

NB01 extracted and QC-filtered overlap data to 108 samples with both geochemistry and community composition:
- Geochemistry matrix shape: `(108, 49)`
- Community taxon rows: `41,711`
- Distinct communities: `212`
- Distinct genera: `1,392`

NB02 built a genus-normalized bridge to pangenome clades:
- GTDB species rows parsed for genus mapping: `27,690`
- Mapped genera: `530`
- Unmapped genera: `862`
- Strict clades: `530`, relaxed clades: `7,380`

NB03 produced:
- Site functional score rows: `216` (108 samples x 2 mapping modes)
- Model result rows: `8` (4 outcomes x 2 mapping modes)

Overall, the modeled contamination-functional signal is weak and statistically unsupported under this feature abstraction, so H1 is not supported and H0 is not rejected.

## Interpretation

Within this ENIGMA subset, contamination gradients did not translate into a robust community-level shift in inferred stress-related functional potential when features are aggregated at genus resolution from broad COG categories. This is compatible with contamination-driven taxonomic turnover that is functionally redundant or too fine-scale (species/strain/pathway level) for the present mapping.

### Literature Context
- Directionally aligned with prior BERIL ENIGMA work in `projects/lab_field_ecology/REPORT.md`, where contamination effects are evident ecologically but are not guaranteed to collapse into one global functional index.
- The bridge and annotation strategy relies on GTDB taxonomy and eggNOG functional annotation conventions; broad annotation classes can dilute specific metal-stress pathway signal.

### Novel Contribution
This project contributes a reproducible ENIGMA-to-BERDL functional inference workflow with explicit strict-vs-relaxed mapping sensitivity, quantifying where signal is lost (notably mobilome collapse) rather than only reporting a null hypothesis test.

### Limitations
- Genus-level mapping may mask strain-level adaptation.
- 862/1,392 observed genera were unmapped to current pangenome bridge.
- COG-fraction proxies are coarse summaries, not curated resistance pathways.
- Current models are primarily unadjusted for depth/site/time structure beyond sample overlap filtering.

## Data

### Sources
| Collection | Tables Used | Purpose |
|---|---|---|
| `enigma_coral` | `ddt_brick0000010`, `ddt_brick0000459`, `ddt_brick0000454`, `sdt_sample`, `sdt_community`, `sdt_location` | Geochemistry, community composition, taxonomy linkage, and sample metadata |
| `kbase_ke_pangenome` | `gtdb_species_clade`, `pangenome`, `gene_cluster`, `eggnog_mapper_annotations` | Taxonomy bridge and COG-derived functional feature construction |

### Generated Data
| File | Rows | Description |
|---|---:|---|
| `data/geochemistry_sample_matrix.tsv` | 108 | Per-sample geochemistry matrix used for contamination index |
| `data/community_taxon_counts.tsv` | 41,711 | Sample-community-genus abundance table |
| `data/sample_location_metadata.tsv` | 108 | Location/depth metadata for overlapping samples |
| `data/taxon_bridge.tsv` | 8,242 | Genus-to-GTDB species-clade bridge with mapping tier |
| `data/taxon_functional_features.tsv` | 3,180 | Per-genus functional proxy features across two mapping modes |
| `data/site_functional_scores.tsv` | 216 | Site-level functional scores by mapping mode |
| `data/model_results.tsv` | 8 | Spearman, permutation, and OLS trend outputs |

## Supporting Evidence

### Notebooks
| Notebook | Purpose |
|---|---|
| `notebooks/01_enigma_extraction_qc.ipynb` | ENIGMA overlap extraction and QC export |
| `notebooks/02_taxonomy_bridge_functional_features.ipynb` | Taxonomy bridge and functional feature engineering |
| `notebooks/03_contamination_functional_models.ipynb` | Contamination index construction, modeling, and diagnostics |

### Figures
| Figure | Description |
|---|---|
| `figures/contamination_vs_functional_score.png` | Stress score vs contamination index, faceted by mapping mode |
| `figures/contamination_index_distribution.png` | Histogram of contamination index values across 108 samples |
| `figures/mapping_coverage_by_mode.png` | Number of feature-covered genera per mapping mode |

## Future Directions

1. Replace COG-fraction proxies with curated metal-stress gene sets and pathway-level summaries.
2. Increase taxonomic resolution where possible (species/strain-level bridge) and quantify incremental gains over genus-level mapping.
3. Fit adjusted models with explicit covariates (depth, location cluster, sampling date) and compositional modeling controls.
4. Investigate unmapped genera contribution to contamination gradients and bridge expansion opportunities.
5. Rework mobilome feature definition to avoid constant-feature collapse and recover variance.

## References

- Carlson HK et al. (2019). The selective pressures on the microbial community in a metal-contaminated aquifer. *ISME J* 13:937-949. PMID: 30523276.
- Parks DH et al. (2022). GTDB: an ongoing census of bacterial and archaeal diversity through a phylogenetically consistent, rank normalized and complete genome-based taxonomy. *Nucleic Acids Res* 50:D785-D794.
- Cantalapiedra CP et al. (2021). eggNOG-mapper v2: Functional annotation, orthology assignments, and domain prediction at the metagenomic scale. *Mol Biol Evol* 38:5825-5829.
