#!/usr/bin/env Rscript
# pgls_mgnify_validation.R  —  PGLS validation runner
#
# Usage:
#   Rscript scripts/pgls_mgnify_validation.R <input.csv> <tree> <output.csv>
#
# Input CSV columns required:
#   genus_lower   — GTDB genus name (lowercase)
#   biome_H_std   — response variable (niche breadth metric, any name works here)
#   <any other columns>  — each treated as an independent PGLS predictor
#
# One model is run per predictor column (all columns except genus_lower and biome_H_std).
# Columns with zero variance are skipped.

suppressPackageStartupMessages({ library(ape); library(nlme) })

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("Usage: pgls_mgnify_validation.R <input.csv> <tree> <output.csv>")
input_file  <- args[1]
tree_file   <- args[2]
output_file <- args[3]

cat('\n=== MGnify MAG validation PGLS ===\n')
cat(sprintf('Input:  %s\nTree:   %s\nOutput: %s\n', input_file, tree_file, output_file))

# ─── Load data ─────────────────────────────────────────────────────────────────
data <- read.csv(input_file, stringsAsFactors = FALSE)
tree <- read.tree(tree_file)
cat(sprintf('\nLoaded %d genera from input CSV\n', nrow(data)))
cat(sprintf('Tree has %d tips\n', length(tree$tip.label)))

# ─── Prune tree to genera present in both input and tree ──────────────────────
# Deduplicate genus_lower first (multiple MGnify genus strings can normalize
# to the same GTDB name; duplicates break rowname-based tip matching)
data <- data[!duplicated(data$genus_lower) & !is.na(data$genus_lower) & data$genus_lower != '', ]

in_both  <- data$genus_lower[data$genus_lower %in% tree$tip.label]
tree_sub <- keep.tip(tree, unique(in_both))

# Resolve polytomies introduced by pruning (needed for Cholesky in corPagel)
if (!is.binary(tree_sub)) tree_sub <- multi2di(tree_sub)

# Set a minimum branch length floor to prevent VCV singularity.
# Near-zero branches arise when pruning a 2283-tip tree to ~500 tips;
# the resulting VCV becomes ill-conditioned without this guard.
mean_bl  <- mean(tree_sub$edge.length[tree_sub$edge.length > 0])
min_bl   <- max(1e-6, mean_bl * 1e-3)
tree_sub$edge.length[tree_sub$edge.length < min_bl] <- min_bl

data <- data[data$genus_lower %in% tree_sub$tip.label, ]
# CRITICAL: row order must match tree tip order (corPagel matches by position)
rownames(data) <- data$genus_lower
data <- data[tree_sub$tip.label, ]
cat(sprintf('After tree pruning: %d genera\n', nrow(data)))

# ─── PGLS helper (same logic as pgls_regression.R::run_pgls) ──────────────────
run_pgls <- function(response_col, predictor_col, data, tree) {
    cat(sprintf('\n[PGLS] %s ~ %s  (n=%d)\n', response_col, predictor_col, nrow(data)))

    # Skip degenerate predictors (zero variance → singular design matrix)
    pred_vals <- data[[predictor_col]]
    if (is.null(pred_vals) || all(is.na(pred_vals)) || sd(pred_vals, na.rm = TRUE) < 1e-10) {
        cat('  SKIP: predictor has zero or near-zero variance\n')
        return(NULL)
    }

    formula_obj <- as.formula(paste(response_col, '~', predictor_col))
    ctrl <- glsControl(msMaxIter = 300, tolerance = 1e-5)

    # Try multiple lambda starting values; corPagel can fail to converge near boundary
    fit <- NULL
    lambda_used <- NA
    for (lam_init in c(0.5, 0.9, 0.1, 0.0)) {
        fixed_lam <- (lam_init == 0.0)
        cor_struct <- tryCatch(
            corPagel(lam_init, phy = tree, fixed = fixed_lam),
            error = function(e) NULL
        )
        if (is.null(cor_struct)) next
        fit <- suppressWarnings(tryCatch(
            gls(formula_obj, data = data, correlation = cor_struct,
                method = 'ML', control = ctrl),
            error = function(e) NULL
        ))
        if (!is.null(fit)) { lambda_used <- lam_init; break }
    }
    if (is.null(fit)) {
        cat('  ERROR gls: all lambda starting values failed\n'); return(NULL)
    }
    fit0 <- suppressWarnings(tryCatch(
        gls(as.formula(paste(response_col, '~ 1')),
            data = data, correlation = cor_struct, method = 'ML'),
        error = function(e) NULL
    ))
    s          <- summary(fit)
    ct         <- coef(s)
    lambda_val <- as.numeric(coef(fit$modelStruct$corStruct))
    if (!(predictor_col %in% rownames(ct))) {
        cat('  WARNING: predictor not in coefficient table\n'); return(NULL)
    }
    pr        <- ct[predictor_col, ]
    delta_AIC <- if (!is.null(fit0)) AIC(fit) - AIC(fit0) else NA
    r2_pgls   <- if (!is.null(fit0))
        1 - sum(residuals(fit)^2) / sum(residuals(fit0)^2) else NA
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

# ─── Run one model per predictor column ────────────────────────────────────────
predictor_cols <- setdiff(names(data), c('genus_lower', 'biome_H_std'))
cat(sprintf('\nPredictors to test (%d): %s\n', length(predictor_cols),
            paste(predictor_cols, collapse = ', ')))
results_list <- Filter(Negate(is.null),
    lapply(predictor_cols, function(pred) run_pgls('biome_H_std', pred, data, tree_sub))
)
if (length(results_list) == 0) {
    cat('\nWARNING: No models converged. Try inspecting the tree branch length distribution.\n')
    cat('Tip: tree_sub$edge.length summary:\n')
    print(summary(tree_sub$edge.length))
    stop('No models converged.')
}
results <- do.call(rbind, results_list)

write.csv(results, output_file, row.names = FALSE)
cat(sprintf('\nSaved: %s  (%d models)\n', output_file, nrow(results)))
cat('\nSummary:\n')
print(results[, c('predictor', 'n_taxa', 'lambda', 'beta', 'p_value', 'delta_AIC')])
