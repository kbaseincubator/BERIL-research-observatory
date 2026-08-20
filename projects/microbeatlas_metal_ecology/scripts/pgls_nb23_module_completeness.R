#!/usr/bin/env Rscript
# pgls_nb23_module_completeness.R
# PGLS: mean metal KEGG module completeness vs niche breadth (genus level)
#
# Usage: Rscript scripts/pgls_nb23_module_completeness.R /path/to/data/dir
#
# Input:
#   nb23_pgls_input.csv     — genus_lower, mean_metal_completeness, mean_levins_B_std, n_genomes
#   gtdb_bac_genus_pruned.tree
# Output:
#   nb23_pgls_results.csv

suppressPackageStartupMessages({ library(ape); library(nlme) })

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], '.')
cat('\n=== PGLS NB23: metal module completeness vs niche breadth ===\n')

tree   <- read.tree(file.path(data_dir, 'gtdb_bac_genus_pruned.tree'))
dat    <- read.csv(file.path(data_dir, 'nb23_pgls_input.csv'), stringsAsFactors = FALSE)
cat(sprintf('Tree: %d tips   Input: %d genera\n', length(tree$tip.label), nrow(dat)))

sub <- dat[
    dat$genus_lower %in% tree$tip.label &
    !is.na(dat$mean_metal_completeness) &
    !is.na(dat$mean_levins_B_std),
]
cat(sprintf('After filter: %d genera\n', nrow(sub)))

sub$predictor_z <- as.numeric(scale(sub$mean_metal_completeness))
tree_sub <- keep.tip(tree, sub$genus_lower)
rownames(sub) <- sub$genus_lower
sub <- sub[tree_sub$tip.label, ]

cat(sprintf('Pruned tree: %d tips\n', length(tree_sub$tip.label)))

cor_struct <- corPagel(0.5, phy = tree_sub, fixed = FALSE,
                       form = ~genus_lower)
fit  <- gls(mean_levins_B_std ~ predictor_z, data = sub,
            correlation = cor_struct, method = 'ML')
fit0 <- gls(mean_levins_B_std ~ 1, data = sub,
            correlation = cor_struct, method = 'ML')

s         <- summary(fit)
ct        <- coef(s)
lam       <- as.numeric(coef(fit$modelStruct$corStruct))
pr        <- ct['predictor_z', ]
delta_AIC <- AIC(fit) - AIC(fit0)

cat(sprintf('  lambda=%.4f  beta=%.4f  SE=%.4f  t=%.3f  p=%.4g  deltaAIC=%.2f\n',
            lam, pr['Value'], pr['Std.Error'], pr['t-value'], pr['p-value'], delta_AIC))

write.csv(data.frame(
    response = 'mean_levins_B_std', predictor = 'mean_metal_completeness',
    n_taxa = nrow(sub), lambda = lam,
    beta = pr['Value'], SE = pr['Std.Error'],
    t_stat = pr['t-value'], p_value = pr['p-value'],
    delta_AIC = delta_AIC, stringsAsFactors = FALSE
), file.path(data_dir, 'nb23_pgls_results.csv'), row.names = FALSE)

cat(sprintf('\nSaved: %s\n', file.path(data_dir, 'nb23_pgls_results.csv')))
