# Phase 1 Investigation Report
**per_ko_metal_associations — robustness control design**
Generated: 2026-07-10

---

## 1a — Metal co-occurrence structure

Spearman correlation matrix across 8,585 MGnify MAGs:

|        | As     | Cd     | Cr     | Cu     | Hg     | Pb     |
|--------|--------|--------|--------|--------|--------|--------|
| As     | 1.000  | −0.366 | **0.684** | **0.600** | **0.551** | −0.109 |
| Cd     | −0.366 | 1.000  | **−0.478** | **−0.434** | **−0.459** | 0.167  |
| Cr     | **0.684** | **−0.478** | 1.000  | **0.710** | **0.433** | −0.040 |
| Cu     | **0.600** | **−0.434** | **0.710** | 1.000  | **0.443** | 0.107  |
| Hg     | **0.551** | **−0.459** | **0.433** | **0.443** | 1.000  | −0.092 |
| Pb     | −0.109 | 0.167  | −0.040 | 0.107  | −0.092 | 1.000  |

**Strong pairs (|ρ| > 0.3):** As–Cr (0.684), Cr–Cu (0.710), As–Cu (0.600), As–Hg (0.551), Cd–Hg (−0.459), Cd–Cu (−0.434), Cd–Cr (−0.478), Cr–Hg (0.433), Cu–Hg (0.443), As–Cd (−0.366).

**Notable structure:**
- As, Cr, Cu, Hg form a correlated cluster (all positive pairs > 0.4).
- Cd is negatively correlated with all four cluster members (ρ −0.37 to −0.48).
- Pb is weakly correlated with all metals (|ρ| ≤ 0.167); effectively orthogonal.

**Implications for Phase 2:**
- Associations with As need Cr as control (ρ = 0.684, strongest).
- Associations with Cr need Cu as control (ρ = 0.710, strongest).
- Associations with Cu need Cr as control.
- Associations with Hg need As as control (ρ = 0.551).
- Associations with Cd need Cr as control (ρ = −0.478, highest |ρ|).
- Associations with Pb use Cd as control (ρ = 0.167; Pb is near-orthogonal — multi-metal control adds minimal confound adjustment but is included for consistency).

---

## 1b — Taxonomic structure

| Level  | Unique groups | Singletons (n=1) | Mean group size | n ≥ 5 |
|--------|--------------|------------------|-----------------|--------|
| Phylum | 91           | (not computed)   | 94              | —      |
| Class  | 232          | 79 (34%)         | 37.0            | 90     |
| Order  | 610          | 245 (40%)        | ~14             | 185    |
| Genus  | 3,300        | 2,141 (65%)      | 2.5             | 288    |

MAGs with genus assignment: 8,177 / 8,585 (95.2%).

**Top 5 phyla by MAG count (with mean PF1 values):**

| Phylum | n MAGs | Hg mean | As mean | Pb mean |
|--------|--------|---------|---------|---------|
| Pseudomonadota | 2,441 | 0.123 | 0.096 | 0.077 |
| Actinomycetota | 1,760 | 0.143 | 0.101 | 0.076 |
| Acidobacteriota | 1,338 | 0.153 | 0.105 | 0.073 |
| Bacteroidota | 606 | 0.117 | 0.091 | 0.077 |
| Chloroflexota | 290 | 0.133 | 0.099 | 0.071 |

Metal distributions are broadly similar across top phyla (range ~0.05 within any metal), suggesting the phylum-metal confound is moderate but real for Hg and Acidobacteriota.

**Genus-level feasibility:**
65% of genera are singletons; median genus size = 1. Genus as a **fixed effect** is not feasible (singular matrices, massive degree-of-freedom cost). Genus as a **random intercept** (linear mixed model) is possible for the targeted 219-pair analysis but:
- statsmodels MixedLM is linear (not logistic), introducing a linear probability model approximation
- Many genera contribute only one MAG, so random effect variance estimation is unreliable

**Decision for Phase 4:** Use **class-level fixed effects** (232 classes, mean 37 MAGs/class) — the same model as NB05 Model A. Class provides 4× finer resolution than phylum with stable group sizes. Order-level is too sparse (median 2 MAGs/order). Genus random intercept is infeasible.

---

## 1c — MAG quality metrics

**Not available.** The following sources were checked:
- `final_mags_geospatial_traits.csv` — no completeness/contamination columns
- `mgnify_mag_metal_traits.csv` — no quality columns
- `global_soil_genomic_atlas.csv` — grid-level aggregated means, not MAG-level
- Spark table `kescience_mgnify.genome` — inaccessible outside JupyterHub

**Conclusion:** Phase 3 (MAG quality controls) cannot be executed in this compute context. This is documented as a limitation. Quality filtering was applied upstream by the MGnify pipeline (all MAGs passed QC thresholds to be included), but specific CheckM completeness/contamination values are not retrievable here.

---

## 1d — Phylogenetic feasibility

The GTDB r214 bacterial genus pruned tree (`gtdb_bac_genus_pruned.tree`) contains 821 genera.

Of the 8,177 MAGs with a genus assignment:
- **1,324 MAGs (16.2%)** have a genus present in the GTDB pruned tree.
- **6,853 MAGs (83.8%)** have novel GTDB genera (e.g., `PALSA-1003`, `DASUNP01`) absent from the pruned representative tree.

The low coverage reflects that the pruned tree was built from representative type-strain genera, not from the full environmental MAG diversity of GTDB r214.

**Conclusion:** 16.2% << 70% threshold → **Phase 5 (PGLS) is not feasible for the full MAG set** and would introduce severe survivor bias. Phase 5 is skipped. This is documented as a limitation: phylogenetic control was attempted but the available tree covers only named type-genus clades, missing the majority of novel environmental diversity in the MGnify dataset.

---

## Phase feasibility summary

| Phase | Feasibility | Reason |
|-------|-------------|--------|
| Phase 2 (multi-metal) | **FEASIBLE** | All metals available; strong correlations warrant control |
| Phase 3 (MAG quality) | **NOT FEASIBLE** | Quality metrics unavailable outside JupyterHub |
| Phase 4 (finer taxonomy) | **FEASIBLE (class-level)** | 232 classes, mean 37 MAGs/class; genus too sparse |
| Phase 5 (PGLS) | **NOT FEASIBLE** | 16.2% tree coverage; severe survivor bias would result |
