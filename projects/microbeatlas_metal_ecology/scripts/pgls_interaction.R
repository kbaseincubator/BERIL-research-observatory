#!/usr/bin/env Rscript
# pgls_interaction.R — Metal × carbon interaction PGLS
#
# Model: B_std ~ metal_types * gapmind_carbon + pct_aquatic
# Purpose: test whether broad-carbon + broad-metal genera show disproportionately
#   wide niches (positive interaction = synergistic).
#
# Input:  data/pgls_subset_interaction.csv  (957 genera; metal + gapmind + habitat)
#         data/gtdb_bac_genus_pruned.tree
# Output: data/pgls_interaction_result.csv

suppressPackageStartupMessages({ library(ape); library(nlme) })

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], '.')

tree  <- read.tree(file.path(data_dir, 'gtdb_bac_genus_pruned.tree'))
dat   <- read.csv(file.path(data_dir, 'pgls_subset_interaction.csv'), stringsAsFactors = FALSE)
cat(sprintf('Loaded: %d genera, tree %d tips\n', nrow(dat), length(tree$tip.label)))

# Filter to genera in tree
dat <- dat[dat$genus_lower %in% tree$tip.label, ]
dat <- dat[!is.na(dat$mean_levins_B_std) & !is.na(dat$mean_n_metal_types) &
           !is.na(dat$mean_gapmind_carbon_score) & !is.na(dat$pct_aquatic_gee), ]
cat(sprintf('After filter: %d genera\n', nrow(dat)))

tree_sub <- keep.tip(tree, dat$genus_lower)
rownames(dat) <- dat$genus_lower
dat <- dat[tree_sub$tip.label, ]

# Z-score predictors
dat$metal_types_z   <- as.numeric(scale(dat$mean_n_metal_types))
dat$gapmind_z       <- as.numeric(scale(dat$mean_gapmind_carbon_score))
dat$pct_aquatic_z   <- as.numeric(scale(dat$pct_aquatic_gee))

# Estimate lambda from a main-effects model first for initialisation
lambda_init <- 0.87  # from prior PGLS results

cor_struct <- corPagel(lambda_init, phy = tree_sub, fixed = FALSE)

# Main-effects model (for comparison)
fit_main <- gls(mean_levins_B_std ~ metal_types_z + gapmind_z + pct_aquatic_z,
                correlation = cor_struct, data = dat, method = 'ML')
s_main   <- summary(fit_main)
lam_main <- as.numeric(coef(fit_main$modelStruct$corStruct))
cat(sprintf('\nMain-effects: lambda=%.4f  AIC=%.2f\n', lam_main, AIC(fit_main)))
print(round(coef(s_main), 4))

# Interaction model
fit_int <- gls(mean_levins_B_std ~ metal_types_z * gapmind_z + pct_aquatic_z,
               correlation = corPagel(lambda_init, phy = tree_sub, fixed = FALSE),
               data = dat, method = 'ML')
s_int   <- summary(fit_int)
lam_int <- as.numeric(coef(fit_int$modelStruct$corStruct))
cat(sprintf('\nInteraction: lambda=%.4f  AIC=%.2f\n', lam_int, AIC(fit_int)))
print(round(coef(s_int), 4))

delta_AIC_int <- AIC(fit_int) - AIC(fit_main)
cat(sprintf('\ndeltaAIC (interaction vs main): %.3f\n', delta_AIC_int))

# Save results
ct_int <- coef(s_int)
rows <- list()
for (nm in rownames(ct_int)) {
    rows[[nm]] <- data.frame(
        term    = nm,
        beta    = ct_int[nm, 'Value'],
        SE      = ct_int[nm, 'Std.Error'],
        t_stat  = ct_int[nm, 't-value'],
        p_value = ct_int[nm, 'p-value'],
        n_taxa  = nrow(dat),
        lambda  = lam_int,
        AIC     = AIC(fit_int),
        delta_AIC_vs_main = delta_AIC_int,
        stringsAsFactors = FALSE
    )
}
out <- do.call(rbind, rows)
write.csv(out, file.path(data_dir, 'pgls_interaction_result.csv'), row.names = FALSE)
cat('\nSaved: data/pgls_interaction_result.csv\n')
