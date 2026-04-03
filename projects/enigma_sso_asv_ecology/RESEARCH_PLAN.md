# Research Plan: SSO Subsurface Community Ecology — Spatial Structure, Functional Gradients, and Hydrogeological Drivers

## Research Question

Does 16S community similarity across the 9 SSO wells (3x3 grid, ~4 m span) recapitulate the spatial arrangement in X, Y, and Z? Where spatial distance fails to predict community similarity, can hydrogeological connectivity or environmental gradients provide a consistent explanation? Can we infer from taxonomic composition what functional differences exist across the site and what they imply about subsurface environmental parameters (oxygen, nutrients, pH, metals, redox)?

## Hypothesis

- **H0a**: Community similarity across SSO wells is spatially random — geographic distance does not predict Bray-Curtis dissimilarity.
- **H1a**: Community dissimilarity increases with geographic distance (distance-decay), but specific well pairs deviate from this trend in ways consistent with subsurface hydrology (e.g., shared flow paths) or environmental discontinuities (e.g., lithological boundaries).

- **H0b**: Inferred functional profiles (from taxonomy → pangenome mapping) show no spatial gradient across the SSO grid.
- **H1b**: Functional composition varies systematically across the grid, with gradients in anaerobic metabolism, sulfur cycling, or metal response that imply spatial variation in redox, sulfate, or metal concentrations.

- **H0c**: Depth (vertical zonation through VZ → VSZ → SZ1 → SZ2) has no effect on community composition independent of horizontal position.
- **H1c**: Vertical stratification (hydrogeological zone) structures communities more strongly than horizontal distance at this spatial scale, reflecting the steep redox and moisture gradients with depth.

## Literature Context

The ENIGMA Subsurface Science Observatory (SSO) at Oak Ridge Reservation Area 3 is a 3×3 grid of boreholes (U1-U3 uphill, M4-M6 middle, L7-L9 downhill) spanning ~4 meters horizontally. Each borehole was cored from surface through the vadose zone (VZ), variably saturated zone (VSZ), and saturated zones (SZ1, SZ2), with sediment 16S profiles at multiple depths and periodic groundwater sampling.

Prior BERIL work (`lab_field_ecology`) found that 14 of 26 Fitness Browser genera are detectable at Oak Ridge and that 5 correlate with uranium gradients. The `enigma_contamination_functional_potential` project attempted functional inference from ENIGMA 16S data but was limited by genus-level resolution — only 530 genera mapped to pangenome species, and many mapped ambiguously. This sets a clear expectation: **functional inference from 16S must focus on phylogenetically conserved traits (phylum/class level metabolism) rather than species-level gene content.**

At the scale of the SSO grid (~4 m), distance-decay of community similarity would be remarkable and would imply very fine-scale environmental heterogeneity. The existing (unreproduced) analysis shows a positive but moderate distance-decay (Spearman rho = 0.36, p = 0.031) in sediment communities, with notable deviations: M4 clusters with Upper wells in ordination space, and L8 is more similar to Middle wells than to its Lower neighbors. These deviations may reflect subsurface flow paths, lithological boundaries, or localized geochemistry.

Key knowledge gap: SSO geochemistry measurements (metals, IC/TOC, isotopes, NH3/NO2) are registered as samples in ENIGMA CORAL but the measurement values have not been loaded into BERDL data bricks. This means we must **infer** environmental gradients from community composition rather than directly correlating with measured parameters.

## Data Sources

### Available (extracted)
| Dataset | Source | Samples | Wells | Depths | Dates | Rows |
|---------|--------|---------|-------|--------|-------|------|
| Sediment 16S ASV | Brick 0000457-459 | 37 | All 9 | 1.7-9.3 m | Feb-Mar 2023 | 42,599 |
| Groundwater 16S ASV | Brick 0000477-479 | 40 | 5 (L7,L9,M4,M6,U2) | 5.2, 7.0 m | Sep 2024 | 35,428 |
| Sample metadata | `sdt_sample` | 547 | All 9 | 0.4-10.5 m | Feb 2023 - Oct 2024 | 547 |

### Available but not yet extracted
| Dataset | Source | Description |
|---------|--------|-------------|
| Pump test ASV | Brick 0000460-462 | 14 communities, Mar 2024, wells L8/M5/U2 |
| ASV 16S sequences | Bricks 457/460/477 | Actual DNA sequences for phylogenetic analysis |
| Nearby well geochemistry | Bricks 0000010/0000080 | 100WS/27WS metals data for EU/ED wells ~90-120 m from SSO (48-52 analytes) |
| SSO isolate genomes | `sdt_genome` / `sdt_strain` | 18 genomes, 144 isolates from SSO-M6-C2 — direct functional annotation |

### Not available in BERDL
- SSO-specific geochemistry (221 METALS/ICTOC/ISOTOPES/NH3NO2 sample tubes registered in CORAL but analytical results never ingested)
- Well elevation / true Z coordinates — only lat/lon + sample depth
- Continuous sensor data (if any)

### Regional Geochemistry Context
The 100 Well Survey and 27 Well Survey metals bricks cover 20 wells within 500 m of SSO, with the closest (EU02-EU07, ED04-ED08) only ~90-120 m northeast. These provide 48-52 analyte panels (uranium, chromium, iron, sulfate, etc.) that establish the regional geochemical gradient context even though they are not SSO well-specific.

### Taxonomy Resolution Constraints
| Level | Groundwater | Sediment |
|-------|-------------|----------|
| Phylum | 70% | 97% |
| Class | 69% | 92% |
| Order | 67% | 80% |
| Family | 66% | 57% |
| Genus | 63% | 35% |
| Species | 0% | 2% |

## Query Strategy

### Tables Required
| Table | Database | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|---|
| `ddt_ndarray` | `enigma_coral` | Extract pump test ASVs (Bricks 460-462) | ~132K | Filter by brick_id |
| `ddt_brick0000010` | `enigma_coral` | 100WS metals — nearby well geochemistry | 52,884 | Filter by well for EU/ED wells |
| `ddt_brick0000080` | `enigma_coral` | 27WS metals — nearby well geochemistry | 98,176 | Filter by well for EU/ED wells |
| `sdt_sample` | `enigma_coral` | Sample metadata enrichment | 547 SSO | Filter by location LIKE 'SSO%' |
| `sdt_community` | `enigma_coral` | Community-level metadata | 69 SSO | Filter by location LIKE 'SSO%' |
| `sdt_strain` | `enigma_coral` | SSO isolates from M6-C2 | 144 SSO | Filter by location |
| `sdt_genome` | `enigma_coral` | SSO isolate genomes — functional annotation | 18 SSO | Filter by location |
| `gene_cluster` | `kbase_ke_pangenome` | Functional profiles for mapped genera | Variable | Filter by species matching SSO genera |
| `eggnog_mapper_annotations` | `kbase_ke_pangenome` | COG categories for functional inference | Variable | Filter by gene_cluster_id |

### Performance Plan
- **Tier**: Direct Spark (JupyterHub) for data extraction; local for analysis
- **Estimated complexity**: Moderate — most analysis is on pre-extracted small datasets; pangenome lookups need care
- **Known pitfalls**: 
  - Genus-level pangenome mapping is ambiguous (prior lesson from `enigma_contamination_functional_potential`)
  - String-typed numeric columns in ENIGMA tables
  - DECIMAL→float conversion for Spark aggregates

## Analysis Plan

### Notebook 01: Data Integration & Well Geometry (`01_data_integration.ipynb`)
- **Goal**: Build complete dataset with well coordinates, distance matrices, and regional geochemistry context
- **Steps**:
  1. Load all three ASV datasets (sediment, groundwater, pump test if extractable)
  2. Compute inter-well geographic distances from lat/lon (Haversine)
  3. Assign grid positions (row: U/M/L; col: 1-3) and compute row/column distances
  4. Extract lithological zone annotations (VZ, VSZ, SZ1, SZ2) from sample descriptions
  5. Build depth-resolved and well-aggregated community matrices
  6. Extract nearby well geochemistry (EU/ED wells from 100WS/27WS metals bricks)
  7. Characterize regional geochemical gradients as context for SSO interpretation
  8. Extract SSO isolate metadata (144 strains from M6-C2, 18 genomes)
- **Expected output**: `data/well_distances.csv`, `data/community_matrices.pkl`, `data/nearby_geochem.csv`, `data/sso_isolates.csv`, summary statistics

### Notebook 02: Spatial Analysis of Sediment Communities (`02_sediment_spatial.ipynb`)
- **Goal**: Test whether community similarity tracks spatial arrangement; identify deviations
- **Steps**:
  1. Compute Bray-Curtis dissimilarity matrix (well-aggregated sediment profiles)
  2. Mantel test: dissimilarity vs geographic distance
  3. MDS ordination of community dissimilarity
  4. Procrustes analysis: rotate MDS to match physical grid coordinates
  5. Identify outlier well pairs (residuals from distance-decay regression)
  6. Interpret outliers in terms of grid position (uphill/downhill, row proximity)
- **Expected output**: Figures (heatmap, Mantel plot, MDS vs grid, Procrustes), `data/spatial_stats.csv`

### Notebook 03: Depth Stratification & Vertical Zonation (`03_depth_zonation.ipynb`)
- **Goal**: Test whether vertical structure (hydrogeological zones) is stronger than horizontal distance
- **Steps**:
  1. Classify each sediment sample by hydrogeological zone (VZ, VSZ, SZ1, SZ2) using depth + descriptions
  2. PERMANOVA: community ~ zone + well (partition variance)
  3. Compare within-zone vs within-well dissimilarity
  4. Ordination colored by zone to visualize vertical structure
  5. Identify taxa with strong depth preferences (indicator species analysis)
- **Expected output**: Figures (ordination by zone, depth profiles), variance decomposition statistics

### Notebook 04: Functional Inference from Taxonomy (`04_functional_inference.ipynb`)
- **Goal**: Infer functional gradients across the SSO grid from taxonomic composition
- **Approach**: Two complementary strategies acknowledging genus-level limitations
  1. **Phylum/class-level trait mapping** (conservative, well-supported):
     - Map dominant phyla/classes to known metabolic modes (aerobic/anaerobic, sulfur cycling, iron reduction, methanogenesis, etc.)
     - Compute trait-weighted community profiles per well
     - Test for spatial gradients in trait profiles
  2. **Pangenome-informed genus mapping** (exploratory, known limitations):
     - Map SSO genera to BERDL pangenome species where unambiguous (1:1 genus→species)
     - Aggregate COG functional categories weighted by abundance
     - Test for enrichment of specific COG categories along spatial axes
  3. **Indicator taxon functional annotation**:
     - For taxa identified as spatial indicators (NB03), look up known functional roles in literature
     - WPS-2 (Eremiobacterota) gradient: literature review of this phylum's ecology
- **Expected output**: Trait profile heatmaps, COG enrichment results, functional gradient interpretation

### Notebook 05: Groundwater vs Sediment Comparison (`05_gw_vs_sediment.ipynb`)
- **Goal**: Compare planktonic (groundwater) vs attached (sediment) communities
- **Steps**:
  1. For overlapping wells (5 wells with both materials), compare community composition
  2. Test whether groundwater is a taxonomic subset of sediment or distinct assemblage
  3. Check if spatial patterns are conserved between materials
  4. Temporal offset analysis (sediment: Feb 2023, groundwater: Sep 2024)
- **Expected output**: Comparison figures, shared vs unique taxa analysis

### Notebook 06: Synthesis — Environmental Gradient Inference (`06_gradient_synthesis.ipynb`)
- **Goal**: Integrate all evidence to infer environmental gradients and hydrological patterns
- **Steps**:
  1. Compile spatial deviations from NB02 (which wells don't fit distance-decay?)
  2. Overlay vertical zonation effects from NB03
  3. Map functional gradients from NB04 onto the physical grid
  4. Propose environmental gradient hypotheses consistent with all observations
  5. Compare with known ORR hydrogeology (dip direction, fracture networks, redox zonation)
  6. Identify predictions that could be tested with the unmeasured geochemistry data
- **Expected output**: Synthesis figure (physical grid annotated with community/functional patterns), testable predictions

## Expected Outcomes

- **If H1a supported**: Distance-decay at ~4 m scale implies extreme fine-scale heterogeneity. Deviations from distance-decay will point to subsurface connectivity or environmental discontinuities.
- **If H0a not rejected**: Communities are homogeneous at this scale, implying effective mixing or uniform environment across the grid.
- **If H1b supported**: Functional gradients imply systematic environmental variation (e.g., increasing anaerobic metabolism downgradient → oxygen depletion along flow path).
- **If H0b not rejected**: Functional composition is uniform despite taxonomic turnover, suggesting ecological equivalence / functional redundancy.
- **If H1c supported**: Vertical zonation dominates, consistent with the steep physicochemical gradients across VZ→SZ transitions.

### Potential Confounders
- **Temporal mismatch**: Sediment (2023) vs groundwater (2024) — communities may have shifted
- **Incomplete groundwater coverage**: Only 5/9 wells sampled for GW
- **Taxonomy resolution**: Genus-level limits functional inference precision
- **No geochemistry**: Environmental gradient inference is indirect, from taxonomy alone
- **Sequencing depth**: ASV abundance reflects PCR amplification, not absolute cell counts
- **Core disturbance**: Coring process may have introduced surface contamination at shallow depths

## Revision History
- **v1** (2026-04-03): Initial plan — restart from corrupted start; builds on existing extracted data + prior project lessons
- **v1.1** (2026-04-03): Added nearby well geochemistry (EU/ED from 100WS/27WS) as regional context; added SSO isolate genomes (18 from M6-C2); confirmed SSO geochemistry values not in BERDL despite 221 registered sample tubes

## Authors
- Adam Arkin (ORCID: 0000-0002-4999-2931), U.C. Berkeley / Lawrence Berkeley National Laboratory
