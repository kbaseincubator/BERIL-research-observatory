#!/usr/bin/env Rscript
# pgls_multivariate.R — Multivariate PGLS with Pagel's lambda (free, ML)
#
# Fits:
#   Full:      response ~ pred1_z + pred2_z + ... + predK_z
#   Bivariate: response ~ focal_pred_z
# Extracts per-predictor coefficients (beta, SE, t, p) from the full model.
#
# Usage:
#   Rscript scripts/pgls_multivariate.R \
#     --input  data/nb30_env_cache/aus_multi_Cu_input.csv \
#     --tree   data/gtdb_bac_genus_pruned.tree \
#     --response  mean_levins_B_std \
#     --predictors Cu_mean,pH_mean,SOC_mean,MAT_mean,MAP_mean,elev_mean \
#     --focal  Cu_mean \
#     --output data/nb30_env_cache/aus_multi_Cu_result.csv \
#     --label  "AusMicrobiome+NGSA Cu multivariate (NB30)"

suppressPackageStartupMessages({ library(ape); library(nlme) })

# ── Args ───────────────────────────────────────────────────────────────────────
args <- commandArgs(trailingOnly=TRUE)
get_arg <- function(flag, default=NULL) {
    i <- which(args == flag)
    if (length(i) == 0) return(default)
    if (i >= length(args)) stop(paste("Flag", flag, "missing value"))
    args[i + 1]
}
input_file  <- get_arg("--input")
tree_file   <- get_arg("--tree",     "data/gtdb_bac_genus_pruned.tree")
response    <- get_arg("--response", "mean_levins_B_std")
preds_str   <- get_arg("--predictors")
focal_pred  <- get_arg("--focal")
output_file <- get_arg("--output")
label       <- get_arg("--label",   "multivariate")

if (is.null(input_file))  stop("--input required")
if (is.null(output_file)) stop("--output required")
if (is.null(preds_str))   stop("--predictors required (comma-separated)")

predictors <- trimws(strsplit(preds_str, ",")[[1]])
if (is.null(focal_pred) || !focal_pred %in% predictors)
    focal_pred <- predictors[1]
z_cols  <- paste0(predictors, "_z")
focal_z <- paste0(focal_pred, "_z")

cat(sprintf("\n=== Multivariate PGLS: %s ===\n", label))
cat(sprintf("Predictors: %s\n", paste(predictors, collapse=", ")))
cat(sprintf("Focal:      %s\n", focal_pred))

# ── Load data ─────────────────────────────────────────────────────────────────
tree <- read.tree(tree_file)
df   <- read.csv(input_file, stringsAsFactors=FALSE)
cat(sprintf("Input: %d rows | Tree: %d tips\n", nrow(df), length(tree$tip.label)))

if (!response %in% names(df)) stop(paste("Response not found:", response))
if (!"genus_lower" %in% names(df)) stop("genus_lower column required")
for (p in predictors)
    if (!p %in% names(df)) stop(paste("Predictor not found:", p))

# ── Z-score all predictors ────────────────────────────────────────────────────
for (i in seq_along(predictors))
    df[[z_cols[i]]] <- as.numeric(scale(df[[predictors[i]]]))

# ── Complete-case filter + tree overlap ───────────────────────────────────────
keep <- df$genus_lower %in% tree$tip.label & !is.na(df[[response]])
for (col in z_cols) keep <- keep & !is.na(df[[col]])
sub  <- df[keep, ]
cat(sprintf("After complete-case filter: %d genera\n", nrow(sub)))
if (nrow(sub) < 30) stop("Fewer than 30 genera — check data")

tree_pruned <- drop.tip(tree, setdiff(tree$tip.label, sub$genus_lower))
sub <- sub[match(tree_pruned$tip.label, sub$genus_lower), ]
rownames(sub) <- sub$genus_lower
cat(sprintf("After tree pruning: %d genera\n", nrow(sub)))

# ── Helper ────────────────────────────────────────────────────────────────────
pgls_coefs <- function(fit, model_type, pred_names, pred_z_names, lam, n) {
    tt <- summary(fit)$tTable
    rows <- lapply(seq_along(pred_names), function(i) {
        pz <- pred_z_names[i]
        if (!pz %in% rownames(tt)) return(NULL)
        data.frame(
            model_type = model_type,
            predictor  = pred_names[i],
            beta       = tt[pz, "Value"],
            SE         = tt[pz, "Std.Error"],
            t_stat     = tt[pz, "t-value"],
            p_value    = tt[pz, "p-value"],
            lambda     = lam,
            n          = n,
            stringsAsFactors = FALSE
        )
    })
    do.call(rbind, Filter(Negate(is.null), rows))
}

# ── Full multivariate model ───────────────────────────────────────────────────
cat("Fitting full multivariate model...\n")
form_full  <- as.formula(paste(response, "~", paste(z_cols, collapse=" + ")))
fit_full   <- tryCatch(
    gls(form_full, data=sub,
        correlation=corPagel(1, phy=tree_pruned, fixed=FALSE), method="ML"),
    error=function(e) { cat("Full model error:", e$message, "\n"); NULL }
)
if (is.null(fit_full)) stop("Full model failed to converge")
lam_full <- coef(fit_full$modelStruct$corStruct, unconstrained=FALSE)
cat(sprintf("Full model: λ=%.3f, n=%d\n", lam_full, nrow(sub)))

rows_full <- pgls_coefs(fit_full, "full_multivariate",
                        predictors, z_cols, lam_full, nrow(sub))

# ── Bivariate (focal predictor only, same filtered data) ─────────────────────
cat("Fitting bivariate model (focal predictor only)...\n")
form_biv <- as.formula(paste(response, "~", focal_z))
fit_biv  <- tryCatch(
    gls(form_biv, data=sub,
        correlation=corPagel(1, phy=tree_pruned, fixed=FALSE), method="ML"),
    error=function(e) { cat("Bivariate error:", e$message, "\n"); NULL }
)
rows_biv <- NULL
if (!is.null(fit_biv)) {
    lam_biv  <- coef(fit_biv$modelStruct$corStruct, unconstrained=FALSE)
    rows_biv <- pgls_coefs(fit_biv, "bivariate_only",
                           focal_pred, focal_z, lam_biv, nrow(sub))
    cat(sprintf("Bivariate: λ=%.3f, β=%+.4f, p=%.4g\n",
        lam_biv, rows_biv$beta[1], rows_biv$p_value[1]))
}

# ── Save ──────────────────────────────────────────────────────────────────────
out <- rbind(rows_full, rows_biv)
out$label <- label
write.csv(out, output_file, row.names=FALSE)
cat(sprintf("Saved: %s\n", output_file))

cat("\n=== FULL MODEL RESULTS ===\n")
print(rows_full[, c("predictor","beta","SE","t_stat","p_value","lambda","n")])
if (!is.null(rows_biv)) {
    cat("\n=== BIVARIATE (focal only, same data) ===\n")
    print(rows_biv[, c("predictor","beta","SE","t_stat","p_value","lambda","n")])
}
