#!/usr/bin/env Rscript
# pgls_regression.R  —  PGLS regression: metal AMR vs niche breadth
#
# Usage:
#   Rscript scripts/pgls_regression.R /path/to/data/dir
#
# Method:
#   Phylogenetic Generalized Least Squares via ape::gls + nlme::corPagel.
#   Pagel's λ is estimated jointly with regression coefficients (ML).
#   Predictors are z-scored before fitting so β values are comparable.
#
# Input files (in data_dir):
#   gtdb_bac_genus_pruned.tree    — 2,286-tip bacterial genus tree (from NB04)
#   genus_trait_table.csv         — 3,160 genera × 26 cols (niche breadth + metal AMR)
#
# Output files (in data_dir):
#   pgls_results.csv              — β, SE, t, p, λ, AIC per model
#   pgls_multi_results.csv        — coefficients for multi-predictor model

suppressPackageStartupMessages({
    library(ape)
    library(nlme)
})

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], '.')
cat('\n=== PGLS regression (ape + nlme) ===\n')
cat(sprintf('Data dir: %s\n', data_dir))


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Load data
# ─────────────────────────────────────────────────────────────────────────────
tree_file  <- file.path(data_dir, 'gtdb_bac_genus_pruned.tree')
trait_file <- file.path(data_dir, 'genus_trait_table.csv')

if (!file.exists(tree_file))  stop(sprintf('Missing: %s', tree_file))
if (!file.exists(trait_file)) stop(sprintf('Missing: %s', trait_file))

tree   <- read.tree(tree_file)
traits <- read.csv(trait_file, stringsAsFactors = FALSE)
cat(sprintf('\nTree:        %d tips\n', length(tree$tip.label)))
cat(sprintf('Trait table: %d genera, %d cols\n', nrow(traits), ncol(traits)))

# Check metal AMR columns present
amr_raw <- c('mean_n_metal_amr_clusters', 'mean_metal_core_fraction', 'mean_n_metal_types')
missing_cols <- amr_raw[!amr_raw %in% colnames(traits)]
if (length(missing_cols) > 0) stop(sprintf('Missing AMR columns: %s', paste(missing_cols, collapse=', ')))


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Filter and prepare data
# ─────────────────────────────────────────────────────────────────────────────
sub <- traits[
    traits$n_otus >= 3 &
    traits$genus_lower %in% tree$tip.label &
    !is.na(traits$mean_n_metal_amr_clusters) &
    !is.na(traits$mean_levins_B_std) &
    !is.na(traits$mean_n_envs),
]
cat(sprintf('\nPGLS subset:  %d genera (n_otus>=3, in tree, has AMR + niche breadth)\n', nrow(sub)))

# Z-score predictors for comparable β estimates
amr_z <- paste0(amr_raw, '_z')
for (i in seq_along(amr_raw)) {
    sub[[amr_z[i]]] <- as.numeric(scale(sub[[amr_raw[i]]]))
}
cat('  Predictor means and SDs (raw):\n')
for (col in amr_raw) {
    cat(sprintf('    %-35s  mean=%.3f  sd=%.3f\n', col,
                mean(sub[[col]], na.rm=TRUE), sd(sub[[col]], na.rm=TRUE)))
}

# Prune tree to subset
tree_sub <- keep.tip(tree, sub$genus_lower)
# CRITICAL: sort data rows to match tree tip order.
# corPagel without a 'form' argument matches by row position, not by name.
# Misalignment causes NA/NaN in the VCV Cholesky and wrong lambda estimates.
rownames(sub) <- sub$genus_lower
sub <- sub[tree_sub$tip.label, ]   # reorder rows to match tree tip order
cat(sprintf('\nPruned tree:  %d tips\n', length(tree_sub$tip.label)))


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: PGLS helper function
# ─────────────────────────────────────────────────────────────────────────────
run_pgls <- function(response_col, predictor_col, data, tree) {
    cat(sprintf('\n[PGLS] %s ~ %s  (n=%d)\n', response_col, predictor_col, nrow(data)))

    formula_obj <- as.formula(paste(response_col, '~', predictor_col))

    # Build Pagel correlation structure (λ free, initialised at 0.5)
    cor_struct <- tryCatch(
        corPagel(0.5, phy = tree, fixed = FALSE),
        error = function(e) { cat('  ERROR corPagel:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(cor_struct)) return(NULL)

    # Full model
    fit <- tryCatch(
        gls(formula_obj, data = data, correlation = cor_struct, method = 'ML'),
        error = function(e) { cat('  ERROR gls:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(fit)) return(NULL)

    # Null model (intercept only) with same λ structure for ΔAIC
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
    pr <- ct[predictor_col, ]

    delta_AIC  <- if (!is.null(fit0)) AIC(fit) - AIC(fit0) else NA
    # Pseudo-R² (Orme & Freckleton 2012): partial correlation in GLS space
    # = 1 - RSS_full / RSS_null (in the iC-weighted sense)
    r2_pgls <- NA
    if (!is.null(fit0)) {
        resid_full <- residuals(fit)
        resid_null <- residuals(fit0)
        r2_pgls <- 1 - sum(resid_full^2) / sum(resid_null^2)
    }

    cat(sprintf('  lambda=%.4f  beta=%.4f  SE=%.4f  t=%.3f  p=%.4g  deltaAIC=%.2f\n',
                lambda_val, pr['Value'], pr['Std.Error'],
                pr['t-value'], pr['p-value'], delta_AIC))

    data.frame(
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
        r2_pgls   = r2_pgls,
        logL      = as.numeric(logLik(fit)),
        stringsAsFactors = FALSE
    )
}


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Run simple (one-predictor) PGLS models
# ─────────────────────────────────────────────────────────────────────────────
responses  <- c('mean_levins_B_std', 'mean_n_envs')
predictors <- amr_z   # z-scored predictors

cat('\n=== Simple PGLS models ===\n')
results_list <- list()
k <- 1L
for (resp in responses) {
    for (pred in predictors) {
        r <- run_pgls(resp, pred, sub, tree_sub)
        if (!is.null(r)) { results_list[[k]] <- r; k <- k + 1L }
    }
}
results <- do.call(rbind, Filter(Negate(is.null), results_list))


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Multiple-predictor model
# ─────────────────────────────────────────────────────────────────────────────
cat('\n=== Multiple predictor: mean_levins_B_std ~ all 3 AMR predictors ===\n')
cor_multi <- tryCatch(
    corPagel(0.5, phy = tree_sub, fixed = FALSE),
    error = function(e) NULL
)
fit_multi <- NULL
if (!is.null(cor_multi)) {
    fit_multi <- tryCatch(
        gls(mean_levins_B_std ~ mean_n_metal_amr_clusters_z +
                mean_metal_core_fraction_z + mean_n_metal_types_z,
            data = sub, correlation = cor_multi, method = 'ML'),
        error = function(e) { cat('ERROR (multi):', conditionMessage(e), '\n'); NULL }
    )
}

multi_results <- NULL
if (!is.null(fit_multi)) {
    s_multi    <- summary(fit_multi)
    ct_multi   <- coef(s_multi)
    lam_multi  <- as.numeric(coef(fit_multi$modelStruct$corStruct))
    cat(sprintf('  Multi lambda = %.4f   AIC = %.2f   logL = %.2f\n',
                lam_multi, AIC(fit_multi), logLik(fit_multi)))
    cat('  Coefficients:\n')
    print(round(ct_multi, 4))

    # Collect rows for each predictor in the multi model
    multi_rows <- list()
    for (pred in amr_z) {
        if (pred %in% rownames(ct_multi)) {
            pr <- ct_multi[pred, ]
            multi_rows[[pred]] <- data.frame(
                response  = 'mean_levins_B_std',
                predictor = pred,
                model     = 'multi',
                n_taxa    = nrow(sub),
                lambda    = lam_multi,
                beta      = pr['Value'],
                SE        = pr['Std.Error'],
                t_stat    = pr['t-value'],
                p_value   = pr['p-value'],
                AIC       = AIC(fit_multi),
                logL      = as.numeric(logLik(fit_multi)),
                stringsAsFactors = FALSE
            )
        }
    }
    multi_results <- do.call(rbind, multi_rows)
    multi_file <- file.path(data_dir, 'pgls_multi_results.csv')
    write.csv(multi_results, multi_file, row.names = FALSE)
    cat(sprintf('\nMulti-predictor results saved: %s\n', multi_file))
}


# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Save simple results
# ─────────────────────────────────────────────────────────────────────────────
if (is.null(results) || nrow(results) == 0) {
    cat('\nWARNING: no results produced\n')
    quit(status = 1)
}

out_file <- file.path(data_dir, 'pgls_results.csv')
write.csv(results, out_file, row.names = FALSE)
cat(sprintf('\nSimple PGLS results saved: %s  (%d models)\n', out_file, nrow(results)))
cat('\nSummary:\n')
print(results[, c('response', 'predictor', 'n_taxa', 'lambda', 'beta', 'p_value', 'delta_AIC')])
