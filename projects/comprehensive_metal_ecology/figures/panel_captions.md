# Figure S1 — Panel Captions

## Panel A — `figS1_panelA_overview`

Overview of datasets used in this study. *(Left)* Size of each dataset on a log scale; units vary by dataset type (genera, samples, MAGs, or sites). The annotation indicates the 539 EMP-linked genera used for niche PGLS. *(Right)* Biome composition of the MicrobeAtlas 16S sample collection (n=462,716 samples; biome labels from `Env_Level_1`).

## Panel B — `figS1_panelB_map`

Geographic coverage of datasets used in this study. Scatter dots show MicrobeAtlas 16S samples with valid coordinates (n=386,064) coloured by biome (`Env_Level_1`; see upper-left legend). Coloured density blobs show kernel density estimates (Gaussian, σ=7°, constrained to land) for CSU PF1 samples (blue; n=264,653 samples matched to PF1 fitness data, a georeferenced subset of MicrobeAtlas 16S) and NGSA soil geochemistry survey sites (crimson; n=1,315; Australia only). Gold shading shows regions where both datasets co-occur (pixel-wise minimum of both normalised KDE grids). The star marks ENIGMA ORFRC (Oak Ridge, TN, USA). Robinson projection.

## Panel C — `figS1_panelC_quality`

MGnify MAG composition and quality. *(Left)* All MGnify environmental metagenome-assembled genomes (n=260,652 total) distributed by biome; host-associated biomes (grey) were excluded from downstream analysis. *(Centre)* Environmental MAGs retained for analysis, by biome. *(Right)* Distribution of mean completeness and mean contamination per genus in the KBase pangenome collection (n=1,574 genera); medians are annotated.

## Panel D — `figS1_panelD_taxonomy`

Taxonomic composition and dataset overlap. *(Left)* Number of genera per bacterial phylum in the KBase PGLS dataset (n=1,574 genera; top 15 phyla shown); stacked bars indicate genera also present in the EMP 16S niche dataset (orange) or the MGnify PGLS dataset (red). *(Right)* Dataset membership counts: genera exclusive to KBase, shared with EMP 16S, shared with MGnify, or present in all three datasets.

## Panel E — `figS1_panelE_environment`

Distributions of environmental predictor variables used in PGLS models. Soil pH (SoilGrids, n=9,961 genera) and ERA5 mean air temperature (n=9,961 genera) are per-genus medians computed over MicrobeAtlas 16S samples; dashed lines indicate medians. The remaining six panels show soil metal concentrations from the National Geochemical Survey of Australia (NGSA; n=1,315 sites) on a log₁₀ scale; element labels indicate the analyte.

## Panel F — `figS1_panelF_density`

Distributions of metal-gene KO density across bacterial phyla. Each panel shows the density distribution of metal-gene KO count per Mb of genome for genera within the indicated phylum (top 12 phyla by median KO density; n=1,574 genera total in the KBase PGLS dataset). Dashed lines indicate medians. Red ticks show Levins' standardised niche breadth (B_std) for genera in each phylum, scaled to the x-axis range of each panel.

## Panel G — `figS1_panelG_tsne`

t-SNE embedding of MicrobeAtlas 16S samples coloured by biome. A stratified subsample of 24,997 samples was embedded using truncated SVD (50 components, explaining 43.8% of variance) followed by t-SNE (perplexity=50, n_iter=1000, PCA initialisation). Genus-level features (3,389 genera present in ≥10 samples) were used as input. Points are coloured by `Env_Level_1` biome label. Axis ticks are omitted as t-SNE coordinates have no absolute interpretation.
