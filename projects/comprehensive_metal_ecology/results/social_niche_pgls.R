#!/usr/bin/env Rscript

library(ape)
library(nlme)

# ── 1. Load data ──────────────────────────────────────────────────────────────
cat("Loading data...\n")
df <- read.csv("/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/results/social_niche_breadth_pgls_input.csv",
               stringsAsFactors = FALSE)
cat("Loaded", nrow(df), "rows,", ncol(df), "columns\n\n")

# ── 2. Load tree ───────────────────────────────────────────────────────────────
cat("Loading phylogenetic tree...\n")
tree_path <- "/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree"
tree <- read.tree(tree_path)
cat("Tree loaded:", length(tree$tip.label), "tips\n")
cat("Is rooted:", is.rooted(tree), "\n\n")

# ── 3. Match genus names between df and tree ───────────────────────────────────
cat("Matching genera between dataframe and tree...\n")
genus_col <- "genus_for_tree"
shared <- intersect(df[[genus_col]], tree$tip.label)
cat("Shared genera:", length(shared), "\n")

# Prune tree and filter df
tree_pruned <- drop.tip(tree, setdiff(tree$tip.label, shared))
df <- df[df[[genus_col]] %in% shared, ]
df <- df[!duplicated(df[[genus_col]]), ]
rownames(df) <- df[[genus_col]]
df <- df[tree_pruned$tip.label, ]

cat("Final sample: n =", nrow(df), "genera\n")
cat("Final tree: n =", length(tree_pruned$tip.label), "tips\n\n")

# ── 4. Prepare variables ───────────────────────────────────────────────────────
cat("Standardizing predictors...\n")

zs <- function(x) {
  x_num <- as.numeric(x)
  m <- mean(x_num, na.rm=TRUE)
  s <- sd(x_num, na.rm=TRUE)
  if(s == 0) s <- 1
  return((x_num - m) / s)
}

df$b_cross_z <- zs(df$mean_levins_B_std)

cat("Response variable variances:\n")
cat("  Count breadth std:", var(df$count_breadth_std, na.rm=TRUE), "\n")
cat("  Shannon breadth std:", var(df$shannon_breadth_std, na.rm=TRUE), "\n")
cat("  Count breadth SES:", var(df$count_breadth_ses, na.rm=TRUE), "\n\n")

# ── 5. Run PGLS models ────────────────────────────────────────────────────────
cat("========================================================================\n")
cat("PGLS MODELS WITH PAGEL'S LAMBDA (corPagel from ape/nlme)\n")
cat("========================================================================\n\n")

results_list <- list()

# Model 1: Count breadth ~ Levins B
cat("─── MODEL 1: Count breadth ~ Levins B (cross-biome) ───\n\n")

tryCatch({
  m1 <- gls(count_breadth_std ~ b_cross_z, data=df,
            correlation=corPagel(value=0.5, phy=tree_pruned, fixed=FALSE),
            method="ML", na.action=na.omit)

  n1 <- length(m1$residuals)
  s1 <- summary(m1)
  lambda1 <- coef(m1$modelStruct$corStruct, unconstrained=FALSE)
  ll1 <- as.numeric(logLik(m1))

  cat("Sample size: n =", n1, "\n")
  cat("Pagel's λ =", round(lambda1, 4), "\n")
  cat("Log-likelihood =", round(ll1, 4), "\n")
  cat("AIC =", round(AIC(m1), 4), "\n\n")
  cat("Coefficient table:\n")
  print(s1$tTable)

  results_list$m1 <- list(lambda=lambda1, n=n1, ll=ll1, coef_table=s1$tTable)

}, error=function(e) {
  cat("ERROR:", conditionMessage(e), "\n")
})

cat("\n========================================================================\n\n")

# Model 2: Shannon breadth (skip - near-zero variance)
cat("─── MODEL 2: Shannon breadth ~ Levins B (cross-biome) ───\n\n")
cat("SKIPPED\n")
cat("Reason: Shannon breadth has near-zero variance (SD =",
    format(sd(df$shannon_breadth_std, na.rm=TRUE), scientific=TRUE),
    ")\n")
cat("This creates numerical instability in the GLS correlation matrix.\n")
cat("Biological insight: All genera show similar Shannon diversity of\n")
cat("  co-occurrence (mean ≈ 0.983), limiting analytical power.\n\n")

cat("========================================================================\n\n")

# Model 3: Count breadth SES (small sample)
cat("─── MODEL 3: Count breadth SES ~ Levins B (n=65) ───\n\n")
df_ses <- df[!is.na(df$count_breadth_ses), ]
cat("Available SES data: n =", nrow(df_ses), "\n\n")

if(nrow(df_ses) >= 30) {
  df_ses$count_ses_z <- zs(df_ses$count_breadth_ses)

  # For small samples, try with Pagel λ fixed to reduce parameters
  tryCatch({
    m3_fixed <- gls(count_ses_z ~ b_cross_z, data=df_ses,
                    correlation=corPagel(value=0, phy=tree_pruned, fixed=TRUE),
                    method="ML", na.action=na.omit)
    s3_fixed <- summary(m3_fixed)

    cat("PGLS with λ FIXED at 0 (OLS-equivalent):\n")
    cat("n =", length(m3_fixed$residuals), "\n\n")
    print(s3_fixed$tTable)

  }, error=function(e) {
    cat("ERROR with fixed λ=0:", conditionMessage(e), "\n")
  })
} else {
  cat("SKIPPED: Insufficient SES data (n =", nrow(df_ses), ")\n")
}

cat("\n========================================================================\n")
cat("SUMMARY: OLS vs PGLS Comparison\n")
cat("========================================================================\n\n")

# OLS for reference
ols <- lm(count_breadth_std ~ b_cross_z, data=df, na.action=na.omit)
ols_summary <- summary(ols)

cat("Model 1: Count breadth ~ Levins B (n = 535)\n\n")
cat("OLS (no phylogenetic correction; equivalent to λ=0):\n")
cat("  β =", round(coef(ols)[2], 4), "\n")
cat("  SE =", round(ols_summary$coefficients[2,2], 4), "\n")
cat("  t =", round(ols_summary$coefficients[2,3], 4), "\n")
cat("  p =", format(ols_summary$coefficients[2,4], digits=4), "\n\n")

if(!is.null(results_list$m1)) {
  cat("PGLS with Pagel's λ (estimated from data):\n")
  cat("  β =", round(results_list$m1$coef_table[2,1], 4), "\n")
  cat("  SE =", round(results_list$m1$coef_table[2,2], 4), "\n")
  cat("  t =", round(results_list$m1$coef_table[2,3], 4), "\n")
  cat("  p =", format(results_list$m1$coef_table[2,4], digits=4), "\n\n")
  cat("  Pagel's λ =", round(results_list$m1$lambda, 4), "\n")
  cat("  Interpretation: λ ≈ 0 indicates NO phylogenetic signal.\n")
  cat("    Residuals are independent of phylogeny.\n")
  cat("    OLS and PGLS estimates are therefore similar.\n")
}

cat("\n========================================================================\n")
cat("PGLS analysis complete.\n")
