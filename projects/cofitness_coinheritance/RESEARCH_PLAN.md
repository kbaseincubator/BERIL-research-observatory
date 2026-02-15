# Research Plan: Co-fitness Predicts Co-inheritance

## Overview

Test whether genes with correlated fitness profiles (co-fit) tend to co-occur in the same genomes across a species' pangenome, using continuous prevalence rather than binary core/auxiliary classification.

## Key Design Decisions

### Prevalence gradient (not binary core/aux)

Use continuous prevalence (fraction of species genomes carrying each gene cluster) rather than restricting to auxiliary-auxiliary pairs. The phi coefficient is computed from binary presence/absence, but results are analyzed as a function of prevalence. This uses ALL gene pairs and maximizes statistical power.

**Key visualization**: phi vs mean prevalence for cofit pairs vs random pairs. The gap between curves = co-inheritance signal. Expected to be largest at intermediate prevalences (50-90%) and collapse at >99%.

### Cofit primary, modules secondary

1. **Raw cofit pairs** (primary): Top-20 co-fitness partners per gene from FB `cofit` table. Available for all organisms.
2. **ICA module membership** (secondary): Genes in the same ICA module. Available for ~6 overlapping organisms.

### Phylogenetic control

Use phylogenetic tree distance pairs to stratify genomes by distance from the FB organism's genome (near <0.01, medium 0.01-0.05, far >0.05). Compute phi separately per stratum. Elevated phi among distant genomes = functional coupling, not shared ancestry.

### Organism selection

11 organisms with >=40 genomes and >=100 auxiliary FB genes. Ralstonia spp. (lowest ANI) are most promising for diverse gene content.

## Analysis Steps

### Step 1: Data Extraction (Spark)

For each target species:
- Genome x gene_cluster presence matrix (filtered to FB-linked clusters)
- Cofit pairs from `kescience_fitnessbrowser.cofit`
- Gene coordinates for adjacency control
- Phylogenetic distances between genomes

### Step 2: Co-occurrence Analysis (local)

For each organism:
1. Compute phi for each cofit cluster pair
2. Record prevalence of each cluster and mean prevalence
3. Generate 10 matched random pairs per cofit pair (same prevalence +/-5%)
4. Label pairs as adjacent (<= 5 loci apart) vs distant

### Step 3: Module-Level Analysis (local, secondary)

For organisms with ICA modules:
1. Compute mean pairwise phi within each module
2. Compare to prevalence-matched random gene sets
3. Stratify by core vs accessory modules

### Step 4: Cross-Organism Synthesis (local)

Six planned figures:
1. Main result: phi vs prevalence for cofit vs random pairs
2. Operon control: same as Fig 1 excluding adjacent pairs
3. Phylogenetic control: phi by genome distance stratum
4. Cofit strength vs co-occurrence strength
5. Module co-inheritance scores vs null
6. Functional interpretation of high-phi + high-cofit pairs

## Verification Checks

1. At prevalence >99%, phi should be ~0 for both groups
2. Known operons should show high phi and high cofit
3. Random pair phi should center near 0 at each prevalence
4. Results should be consistent with module_conservation findings

## Risks

- Signal may be dominated by operons (mitigated by adjacency control)
- Near-clonal species may lack gene content variation
- Small pangenomes give noisy phi estimates
- Not all species may have phylogenetic trees
