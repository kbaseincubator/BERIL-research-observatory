#!/usr/bin/env Rscript
# discriminant_pgls.R — PGLS for metal-dependent / metal-sensing discriminant gene set
#
# Purpose:
#   Test whether the 19-KO discriminant control gene set (11 seed-homeostasis genes
#   excluded from the 94-KO list + 8 metal-dependent metabolic enzymes: SOD, catalase,
#   ferredoxin, cytochrome c oxidase) shows a similar niche-breadth association to
#   the 94-KO list. Two outcomes are equally informative:
#
#     NULL  (β≈0, p>0.05)  → 94-KO signal is specific to metal-handling genes ✓
#     POSITIVE (β>0, p<0.05) → signal reflects genome size / broad metal-gene count ✗
#
# Requires:
#   data/genus_discriminant_metal.csv  — from extract_discriminant_spark.py (JupyterHub)
#   data/genus_trait_table.csv         — niche breadth + 94-KO data (already exists)
#   data/gtdb_bac_genus_pruned.tree    — GTDB r214 bacterial genus tree
#
# Output:
#   data/pgls_results_discriminant.csv — β, SE, t, p, λ per model
#
# Usage:
#   Rscript scripts/discriminant_pgls.R data/

suppressPackageStartupMessages({
    library(ape)
    library(nlme)
})

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], '.')
cat('\n=== Discriminant PGLS — metal-sensing / metal-dependent gene set ===\n')
cat(sprintf('Data dir: %s\n', data_dir))

# ─── 1. Load data ──────────────────────────────────────────────────────────
tree_file  <- file.path(data_dir, 'gtdb_bac_genus_pruned.tree')
trait_file <- file.path(data_dir, 'genus_trait_table.csv')
disc_file  <- file.path(data_dir, 'genus_discriminant_metal.csv')

for (f in c(tree_file, trait_file, disc_file)) {
    if (!file.exists(f)) stop(sprintf('Missing: %s', f))
}

tree   <- read.tree(tree_file)
traits <- read.csv(trait_file,  stringsAsFactors = FALSE)
disc   <- read.csv(disc_file,   stringsAsFactors = FALSE)

cat(sprintf('\nTree:                %d tips\n', length(tree$tip.label)))
cat(sprintf('94-KO trait table:   %d genera\n', nrow(traits)))
cat(sprintf('Discriminant table:  %d genera\n', nrow(disc)))

# ─── 2. Merge and filter ───────────────────────────────────────────────────
# Join on genus_lower; keep genera present in all three (tree + niche + discriminant)
merged <- merge(
    traits[, c('genus_lower', 'mean_levins_B_std', 'mean_n_metal_types', 'n_otus',
                'mean_n_metal_clusters', 'mean_metal_core_fraction')],
    disc[, c('genus_lower', 'mean_n_disc_metal_types', 'mean_n_disc_clusters',
              'mean_has_sod', 'mean_has_catalase', 'mean_has_cox',
              'mean_has_fur', 'mean_has_znuABC', 'mean_has_ferredoxin')],
    by = 'genus_lower', all.x = TRUE
)

# Genera with zero discriminant genes get 0
merged$mean_n_disc_metal_types[is.na(merged$mean_n_disc_metal_types)] <- 0
merged$mean_n_disc_clusters[is.na(merged$mean_n_disc_clusters)] <- 0

sub <- merged[
    merged$n_otus >= 3 &
    merged$genus_lower %in% tree$tip.label &
    !is.na(merged$mean_levins_B_std),
]

cat(sprintf('\nPGLS subset: %d genera (n_otus>=3, in tree, has niche breadth)\n', nrow(sub)))
cat(sprintf('  With any discriminant gene: %d (%.1f%%)\n',
            sum(sub$mean_n_disc_metal_types > 0),
            100 * mean(sub$mean_n_disc_metal_types > 0)))

# Z-score predictors
sub$disc_types_z    <- as.numeric(scale(sub$mean_n_disc_metal_types))
sub$disc_clusters_z <- as.numeric(scale(sub$mean_n_disc_clusters))
sub$metal_types_z  <- as.numeric(scale(sub$mean_n_metal_types))

# Match tree to data
tree_sub <- keep.tip(tree, sub$genus_lower)
rownames(sub) <- sub$genus_lower
sub <- sub[tree_sub$tip.label, ]
cat(sprintf('Pruned tree: %d tips\n', length(tree_sub$tip.label)))


# ─── 3. PGLS helper ────────────────────────────────────────────────────────
run_pgls <- function(response_col, predictor_col, label, data, tree) {
    cat(sprintf('\n[PGLS] %s ~ %s  (n=%d)  [%s]\n', response_col, predictor_col, nrow(data), label))

    formula_obj <- as.formula(paste(response_col, '~', predictor_col))
    cor_struct  <- tryCatch(
        corPagel(0.5, phy = tree, fixed = FALSE),
        error = function(e) { cat('  ERROR corPagel:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(cor_struct)) return(NULL)

    fit <- tryCatch(
        gls(formula_obj, data = data, correlation = cor_struct, method = 'ML'),
        error = function(e) { cat('  ERROR gls:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(fit)) return(NULL)

    fit0 <- tryCatch(
        gls(as.formula(paste(response_col, '~ 1')),
            data = data, correlation = cor_struct, method = 'ML'),
        error = function(e) NULL
    )

    s          <- summary(fit)
    ct         <- coef(s)
    lambda_val <- as.numeric(coef(fit$modelStruct$corStruct))

    if (!(predictor_col %in% rownames(ct))) {
        cat('  WARNING: predictor not in coefficient table\n'); return(NULL)
    }
    pr        <- ct[predictor_col, ]
    delta_AIC <- if (!is.null(fit0)) AIC(fit) - AIC(fit0) else NA

    cat(sprintf('  lambda=%.4f  beta=%.4f  SE=%.4f  t=%.3f  p=%.4g  deltaAIC=%.2f\n',
                lambda_val, pr['Value'], pr['Std.Error'],
                pr['t-value'], pr['p-value'], delta_AIC))

    data.frame(
        label     = label,
        response  = response_col,
        predictor = predictor_col,
        n_taxa    = nrow(data),
        lambda    = lambda_val,
        beta      = pr['Value'],
        SE        = pr['Std.Error'],
        t_stat    = pr['t-value'],
        p_value   = pr['p-value'],
        AIC       = AIC(fit),
        delta_AIC = delta_AIC,
        stringsAsFactors = FALSE
    )
}


# ─── 4. Run PGLS models ────────────────────────────────────────────────────
cat('\n=== Discriminant PGLS models ===\n')

models <- list(
    # Primary discriminant predictors
    list('mean_levins_B_std', 'disc_types_z',    'Discriminant: metal types (19-KO set)'),
    list('mean_levins_B_std', 'disc_clusters_z', 'Discriminant: gene clusters (19-KO set)'),
    # Comparison: 94-KO on same n
    list('mean_levins_B_std', 'metal_types_z',   '94-KO metal types (same subset, for comparison)')
)

results_list <- lapply(models, function(m) {
    run_pgls(m[[1]], m[[2]], m[[3]], sub, tree_sub)
})
results <- do.call(rbind, Filter(Negate(is.null), results_list))


# ─── 5. Print comparison summary ──────────────────────────────────────────
cat('\n\n=== COMPARISON SUMMARY ===\n')
cat(sprintf('%-52s  %7s  %7s  %7s  %8s\n', 'Model', 'beta', 'SE', 'p-value', 'lambda'))
cat(strrep('-', 85), '\n')
for (i in seq_len(nrow(results))) {
    r <- results[i, ]
    sig <- if (!is.na(r$p_value) && r$p_value < 0.05) '*' else ' '
    cat(sprintf('%-52s  %7.4f  %7.4f  %7.4f%s  %8.4f\n',
                r$label, r$beta, r$SE, r$p_value, sig, r$lambda))
}

disc_94ko <- results[results$label == '94-KO metal types (same subset, for comparison)', ]
disc_ctrl  <- results[results$label == 'Discriminant: metal types (19-KO set)', ]
cat('\n=== INTERPRETATION ===\n')
if (nrow(disc_ctrl) > 0 && nrow(disc_94ko) > 0) {
    if (disc_ctrl$p_value > 0.05) {
        cat('RESULT: DISCRIMINANT NULL — discriminant gene set shows no niche breadth association.\n')
        cat(sprintf('  94-KO p=%.4f vs. discriminant p=%.4f.\n', disc_94ko$p_value, disc_ctrl$p_value))
        cat('  Conclusion: 94-KO signal is SPECIFIC to metal-resistance / homeostasis genes.\n')
    } else {
        cat('RESULT: DISCRIMINANT POSITIVE — discriminant gene set also predicts niche breadth.\n')
        cat(sprintf('  94-KO p=%.4f vs. discriminant p=%.4f.\n', disc_94ko$p_value, disc_ctrl$p_value))
        cat('  Implication: the signal may reflect genome complexity or broad metal-gene count,\n')
        cat('  not metal-handling specificity. Review gene list curation before final submission.\n')
    }
}

# ─── 6. Save results ──────────────────────────────────────────────────────
out_file <- file.path(data_dir, 'pgls_results_discriminant.csv')
write.csv(results, out_file, row.names = FALSE)
cat(sprintf('\nSaved: %s\n', out_file))
