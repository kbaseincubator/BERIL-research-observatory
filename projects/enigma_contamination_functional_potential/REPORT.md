# Report: Contamination Gradient vs Functional Potential in ENIGMA Communities

## Key Findings

### No strong contamination-functional association detected
Across 108 ENIGMA samples, contamination index was not significantly associated with inferred site-level stress functional potential.

- `site_stress_score`: Spearman rho = 0.0587, p = 0.546, permutation p = 0.531
- `site_defense_score`: Spearman rho = 0.0587, p = 0.546, permutation p = 0.531
- `site_metabolism_score`: Spearman rho = -0.00645, p = 0.947, permutation p = 0.944

### Sensitivity analysis: strict vs relaxed mapping is directionally consistent
Using two mapping modes gave similar conclusions:

- `relaxed_all_clades` (aggregate all mapped clades per genus): no significant stress/defense association
- `strict_single_clade` (one representative clade per genus): no significant stress/defense association

Effect sizes shifted slightly but remained non-significant in both modes.

### Weak positive slope without statistical support
Linear trend estimates for defense/stress scores were positive but not statistically significant:

- `site_defense_score`: beta = 0.000946, p = 0.0681
- `site_stress_score`: beta = 0.000473, p = 0.0681

### Mobilome signal collapsed in current feature mapping
`site_mobilome_score` was explicitly flagged as `constant_feature` in both mapping modes, indicating the current genus-level mapping/feature extraction did not recover a usable mobilome gradient for modeling.

## Results

### Data products generated
- `data/geochemistry_sample_matrix.tsv`
- `data/community_taxon_counts.tsv`
- `data/sample_location_metadata.tsv`
- `data/taxon_bridge.tsv`
- `data/taxon_functional_features.tsv`
- `data/site_functional_scores.tsv`
- `data/model_results.tsv`

### Modeling outcome
Primary hypothesis (H1) was not supported in this first-pass analysis. The observed effect sizes are small and unstable relative to null/permutation baselines.

## Interpretation

The current evidence suggests that contamination gradients in this ENIGMA subset do not produce a large detectable shift in inferred stress-related functional potential at the genus-aggregated resolution used here. This does not rule out ecological filtering; it indicates that this specific mapping and feature abstraction may be too coarse to capture it robustly.

### Literature Context

This result is directionally consistent with prior BERIL findings in `projects/lab_field_ecology/`: contamination-related ecological structure can appear at taxon-abundance level without yielding a simple global functional score relationship.

### Limitations

- Genus-level aggregation may mask species/strain-level functional shifts.
- ENIGMA→pangenome bridge is name-normalization based and can introduce mapping ambiguity.
- COG-derived proxy features are broad summaries, not direct pathway-level stress markers.
- Compositional effects and sparse features (notably mobilome) constrain power.

## Supporting Evidence

### Notebooks
| Notebook | Purpose |
|---|---|
| `01_enigma_extraction_qc.ipynb` | ENIGMA extraction, overlap QC, export of geochemistry/community/metadata |
| `02_taxonomy_bridge_functional_features.ipynb` | Genus bridge to pangenome and COG-based feature construction |
| `03_contamination_functional_models.ipynb` | Contamination index, site-level feature scoring, association testing |

### Figures
| Figure | Description |
|---|---|
| `figures/contamination_vs_functional_score.png` | Stress score vs contamination, faceted by mapping mode |
| `figures/contamination_index_distribution.png` | Distribution of contamination index across 108 samples |
| `figures/mapping_coverage_by_mode.png` | Mapping and feature coverage summary for strict vs relaxed modes |

### Data Files
| File | Description |
|---|---|
| `data/model_results.tsv` | Spearman, permutation, and linear trend statistics |
| `data/site_functional_scores.tsv` | Sample-level functional summary scores |
| `data/taxon_functional_features.tsv` | Genus-level COG-derived functional proxies |

## Future Directions

1. Move from genus-level mapping to species/strain-resolved mapping where possible.
2. Replace broad COG proxies with targeted stress pathway markers (e.g., curated metal resistance signatures).
3. Add compositional modeling and covariate controls (location/time/depth strata).
4. Re-run with stricter and relaxed bridge confidence tiers as explicit sensitivity analyses.
5. Replace COG-mobilome proxy with alternative mobile element signals to avoid constant-feature collapse.
