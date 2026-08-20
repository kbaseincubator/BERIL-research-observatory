#!/usr/bin/env Rscript
# pgls_kbase_isolates.R  —  PGLS: KBase isolate ko_per_mb vs niche breadth
#
# Usage:
#   Rscript scripts/pgls_kbase_isolates.R /path/to/data/dir
#
# Method:
#   Phylogenetic GLS via ape::gls + nlme::corPagel (λ free, ML).
#   Predictor z-scored. Uses existing bacterial genus tree.
#
# Input:
#   kbase_pgls_input.csv     — genus_lower, kbase_ko_per_mb, mean_levins_B_std, n_species
#   gtdb_bac_genus_pruned.tree
#
# Output:
#   kbase_pgls_results.csv

suppressPackageStartupMessages({ library(ape); library(nlme) })

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], '.')
cat('\n=== PGLS: KBase isolate ko_per_mb vs niche breadth ===\n')
cat(sprintf('Data dir: %s\n', data_dir))

tree_file  <- file.path(data_dir, 'gtdb_bac_genus_pruned.tree')
input_file <- file.path(data_dir, 'kbase_pgls_input.csv')

if (!file.exists(tree_file))  stop(sprintf('Missing: %s', tree_file))
if (!file.exists(input_file)) stop(sprintf('Missing: %s', input_file))

tree <- read.tree(tree_file)
dat  <- read.csv(input_file, stringsAsFactors = FALSE)

cat(sprintf('\nTree: %d tips\nInput: %d genera\n', length(tree$tip.label), nrow(dat)))

# Filter: in tree, niche breadth non-NA, n_species >= 1
sub <- dat[
    dat$genus_lower %in% tree$tip.label &
    !is.na(dat$mean_levins_B_std) &
    !is.na(dat$kbase_ko_per_mb),
]
cat(sprintf('After filters: %d genera\n', nrow(sub)))

# Z-score predictor
sub$kbase_ko_per_mb_z <- as.numeric(scale(sub$kbase_ko_per_mb))

# Prune tree and align rows
tree_sub <- keep.tip(tree, sub$genus_lower)
rownames(sub) <- sub$genus_lower
sub <- sub[tree_sub$tip.label, ]
cat(sprintf('Pruned tree: %d tips\n', length(tree_sub$tip.label)))

# PGLS: mean_levins_B_std ~ kbase_ko_per_mb_z
cat('\n[PGLS] mean_levins_B_std ~ kbase_ko_per_mb_z\n')
cor_struct <- corPagel(0.5, phy = tree_sub, fixed = FALSE)

fit <- tryCatch(
    gls(mean_levins_B_std ~ kbase_ko_per_mb_z,
        data = sub, correlation = cor_struct, method = 'ML'),
    error = function(e) { cat('ERROR gls:', conditionMessage(e), '\n'); NULL }
)

if (is.null(fit)) quit(status = 1)

fit0 <- tryCatch(
    gls(mean_levins_B_std ~ 1,
        data = sub, correlation = cor_struct, method = 'ML'),
    error = function(e) NULL
)

s          <- summary(fit)
ct         <- coef(s)
lambda_val <- as.numeric(coef(fit$modelStruct$corStruct))
pr         <- ct['kbase_ko_per_mb_z', ]
delta_AIC  <- if (!is.null(fit0)) AIC(fit) - AIC(fit0) else NA

cat(sprintf('  n=%d  lambda=%.4f  beta=%.4f  SE=%.4f  t=%.3f  p=%.4g  deltaAIC=%.2f\n',
            nrow(sub), lambda_val, pr['Value'], pr['Std.Error'],
            pr['t-value'], pr['p-value'], delta_AIC))

result <- data.frame(
    response  = 'mean_levins_B_std',
    predictor = 'kbase_ko_per_mb',
    dataset   = 'KBase isolate pangenome',
    metric    = 'clusters_per_genome / mean_genome_size_mb',
    n_taxa    = nrow(sub),
    lambda    = lambda_val,
    beta      = pr['Value'],
    SE        = pr['Std.Error'],
    t_stat    = pr['t-value'],
    p_value   = pr['p-value'],
    delta_AIC = delta_AIC,
    stringsAsFactors = FALSE
)

out_file <- file.path(data_dir, 'kbase_pgls_results.csv')
write.csv(result, out_file, row.names = FALSE)
cat(sprintf('\nResults saved: %s\n', out_file))
