#!/usr/bin/env Rscript
# mcmcglmm_metal.R — Bayesian phylogenetic Poisson model for metal type count
#
# Tests whether niche breadth (B_std) predicts metal type count (discrete)
# with Poisson family — addresses the Gaussian PGLS assumption limitation.
#
# Input:  data/pgls_subset.csv, data/gtdb_bac_genus_pruned.tree
# Output: data/mcmcglmm_result.csv  (posterior mean + 95% CI for B_std effect)

suppressPackageStartupMessages({ library(ape); library(MCMCglmm) })

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], '.')

cat('=== MCMCglmm: metal type count ~ niche breadth (Poisson) ===\n')

tree  <- read.tree(file.path(data_dir, 'gtdb_bac_genus_pruned.tree'))
dat   <- read.csv(file.path(data_dir, 'pgls_subset.csv'), stringsAsFactors = FALSE)

# Filter
dat <- dat[dat$genus_lower %in% tree$tip.label, ]
dat <- dat[!is.na(dat$mean_n_metal_types) & !is.na(dat$mean_levins_B_std), ]
dat <- dat[dat$mean_n_metal_types >= 0, ]
cat(sprintf('Filtered to %d genera\n', nrow(dat)))

tree_sub <- keep.tip(tree, dat$genus_lower)
rownames(dat) <- dat$genus_lower
dat <- dat[tree_sub$tip.label, ]

# Round to integer (metal type count is already integer but stored as float)
dat$n_metal_types_int <- round(dat$mean_n_metal_types)
dat$B_std_z           <- as.numeric(scale(dat$mean_levins_B_std))
dat$animal            <- dat$genus_lower   # MCMCglmm phylo term column

# Clear duplicate internal node labels (inverseA requires unique labels)
tree_sub$node.label <- NULL
# Build inverse.phylo for the variance structure
inv_tree <- inverseA(tree_sub, nodes = 'TIPS', scale = FALSE)$Ainv

# Priors: weakly informative G (phylo) + R (residual)
prior <- list(
    G = list(G1 = list(V = 1, nu = 0.02)),
    R = list(V = 1, nu = 0.02)
)

nitt_arg <- as.integer(ifelse(length(args) >= 2, args[2], 50000))
burnin   <- as.integer(nitt_arg * 0.1)
thin     <- as.integer(max(1, nitt_arg / 1000))
cat(sprintf('Running MCMCglmm (nitt=%d, burnin=%d, thin=%d)...\n', nitt_arg, burnin, thin))
set.seed(42)
model <- MCMCglmm(
    n_metal_types_int ~ B_std_z,
    random   = ~ animal,
    family   = 'poisson',
    ginverse = list(animal = inv_tree),
    prior    = prior,
    data     = dat,
    nitt     = nitt_arg,
    burnin   = burnin,
    thin     = thin,
    verbose  = FALSE
)

# Extract posterior summary for B_std_z
sol <- summary(model)$solutions
cat('\nFixed effects:\n')
print(round(sol, 4))

# Save
out <- as.data.frame(sol)
out$term      <- rownames(out)
out$n_taxa    <- nrow(dat)
out$model     <- 'MCMCglmm_Poisson'
write.csv(out, file.path(data_dir, 'mcmcglmm_result.csv'), row.names = FALSE)
cat('\nSaved: data/mcmcglmm_result.csv\n')
