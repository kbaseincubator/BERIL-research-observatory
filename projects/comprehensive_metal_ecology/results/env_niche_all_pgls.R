#!/usr/bin/env Rscript
# Comprehensive environmental niche breadth PGLS
# Responses: pH_sd, temp_sd, 9 GeoROC metals, 6 CSU metals, 8 NGSA ICP-MS, 8 NGSA MMI-ME
# Predictors: ko_per_mb_primary (z), genome_mb (z)

library(ape)
library(nlme)

DATA_DIR  <- "projects/comprehensive_metal_ecology/results"
TREE_FILE <- "projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree"

cat("Loading data...\n")
df <- read.csv(file.path(DATA_DIR, "env_niche_all_pgls_input.csv"), stringsAsFactors=FALSE)
cat(sprintf("Input: %d genera\n", nrow(df)))

cat("Loading tree...\n")
tree <- read.tree(TREE_FILE)
cat(sprintf("Tree tips: %d\n", length(tree$tip.label)))

df$genus_tree <- gsub(" ", "_", df$genus_lower)
shared <- intersect(df$genus_tree, tree$tip.label)
cat(sprintf("Tree overlap: %d of %d genera\n", length(shared), nrow(df)))

tree_pruned <- drop.tip(tree, setdiff(tree$tip.label, shared))
df_clean    <- df[df$genus_tree %in% shared, ]
df_clean    <- df_clean[match(tree_pruned$tip.label, df_clean$genus_tree), ]
rownames(df_clean) <- df_clean$genus_tree
cat(sprintf("Final n: %d\n\n", nrow(df_clean)))

# ─────────────────────────────────────────────────────────────────
run_model <- function(data, tree, response_col, label_prefix) {
  fml_str  <- sprintf("%s ~ predictor_z + genome_mb_z", response_col)
  label    <- sprintf("%s ~ KO_primary + genome", label_prefix)
  cat(sprintf("--- %s ---\n", label))
  tryCatch({
    mod <- gls(as.formula(fml_str), data=data,
               correlation=corPagel(value=1, phy=tree, fixed=FALSE, form=~genus_tree),
               method="ML", na.action=na.omit)
    co  <- summary(mod)$tTable
    lam <- as.numeric(mod$modelStruct$corStruct)
    n_fit <- length(mod$residuals)
    cat(sprintf("  n=%d, lambda=%.4f\n", n_fit, lam))
    for (i in 1:nrow(co)) {
      cat(sprintf("  %-25s beta=%.4f SE=%.4f t=%.3f p=%.4f\n",
                  rownames(co)[i], co[i,1], co[i,2], co[i,3], co[i,4]))
    }
    return(list(label=label, response=response_col, n=n_fit, lambda=lam, coef=as.data.frame(co)))
  }, error=function(e) {
    cat(sprintf("  PGLS error: %s — trying OLS fallback\n", conditionMessage(e)))
    tryCatch({
      mod0 <- gls(as.formula(fml_str), data=data,
                  correlation=corPagel(value=0, phy=tree, fixed=TRUE, form=~genus_tree),
                  method="ML", na.action=na.omit)
      co <- summary(mod0)$tTable
      n_fit <- length(mod0$residuals)
      cat(sprintf("  Fallback OLS: n=%d, lambda=0 (fixed)\n", n_fit))
      for (i in 1:nrow(co)) {
        cat(sprintf("  %-25s beta=%.4f SE=%.4f t=%.3f p=%.4f\n",
                    rownames(co)[i], co[i,1], co[i,2], co[i,3], co[i,4]))
      }
      return(list(label=label, response=response_col, n=n_fit, lambda=0, coef=as.data.frame(co)))
    }, error=function(e2) {
      cat(sprintf("  Fallback also failed: %s\n", conditionMessage(e2)))
      return(NULL)
    })
  })
}

# ─────────────────────────────────────────────────────────────────
# Response variable groups
# ─────────────────────────────────────────────────────────────────
climatic_vars <- list(
  list(col="pH_sd",   label="pH_sd"),
  list(col="temp_sd", label="temp_sd")
)
georoc_vars <- list(
  list(col="georoc_Cu_sd", label="GeoROC_Cu_sd"),
  list(col="georoc_Ni_sd", label="GeoROC_Ni_sd"),
  list(col="georoc_Zn_sd", label="GeoROC_Zn_sd"),
  list(col="georoc_Co_sd", label="GeoROC_Co_sd"),
  list(col="georoc_Cr_sd", label="GeoROC_Cr_sd"),
  list(col="georoc_Pb_sd", label="GeoROC_Pb_sd"),
  list(col="georoc_As_sd", label="GeoROC_As_sd"),
  list(col="georoc_Cd_sd", label="GeoROC_Cd_sd"),
  list(col="georoc_Hg_sd", label="GeoROC_Hg_sd")
)
csu_vars <- list(
  list(col="PF1_As_sd", label="CSU_As_sd"),
  list(col="PF1_Cd_sd", label="CSU_Cd_sd"),
  list(col="PF1_Cr_sd", label="CSU_Cr_sd"),
  list(col="PF1_Cu_sd", label="CSU_Cu_sd"),
  list(col="PF1_Hg_sd", label="CSU_Hg_sd"),
  list(col="PF1_Pb_sd", label="CSU_Pb_sd")
)
ngsa_icp_vars <- list(
  list(col="Cu_ICP_MS_mg_kg_0_2_sd",  label="NGSA_ICP_Cu_sd"),
  list(col="Ni_ICP_MS_mg_kg_0_5_sd",  label="NGSA_ICP_Ni_sd"),
  list(col="Zn_ICP_MS_mg_kg_0_9_sd",  label="NGSA_ICP_Zn_sd"),
  list(col="Pb_ICP_MS_mg_kg_0_1_sd",  label="NGSA_ICP_Pb_sd"),
  list(col="As_ICP_MS_mg_kg_0_4_sd",  label="NGSA_ICP_As_sd"),
  list(col="Co_ICP_MS_mg_kg_0_1_sd",  label="NGSA_ICP_Co_sd"),
  list(col="Cr_ICP_MS_mg_kg_0_5_sd",  label="NGSA_ICP_Cr_sd"),
  list(col="Hg_AR_mg_kg_0_01_sd",     label="NGSA_ICP_Hg_sd")
)
ngsa_mmi_vars <- list(
  list(col="Cu_MMI_ME_mg_kg_0_01_sd",   label="NGSA_MMI_Cu_sd"),
  list(col="Ni_MMI_ME_mg_kg_0_005_sd",  label="NGSA_MMI_Ni_sd"),
  list(col="Zn_MMI_ME_mg_kg_0_02_sd",   label="NGSA_MMI_Zn_sd"),
  list(col="Pb_MMI_ME_mg_kg_0_01_sd",   label="NGSA_MMI_Pb_sd"),
  list(col="As_MMI_ME_mg_kg_0_01_sd",   label="NGSA_MMI_As_sd"),
  list(col="Co_MMI_ME_mg_kg_0_005_sd",  label="NGSA_MMI_Co_sd"),
  list(col="Cr_MMI_ME_mg_kg_0_001_sd",  label="NGSA_MMI_Cr_sd"),
  list(col="Hg_MMI_ME_mg_kg_0_001_sd",  label="NGSA_MMI_Hg_sd")
)

all_vars <- c(climatic_vars, georoc_vars, csu_vars, ngsa_icp_vars, ngsa_mmi_vars)

# ─────────────────────────────────────────────────────────────────
results <- list()

cat("========================================\n")
cat("CLIMATIC NICHE BREADTH PGLS\n")
cat("========================================\n\n")
for (v in climatic_vars) {
  results[[v$label]] <- run_model(df_clean, tree_pruned, v$col, v$label)
  cat("\n")
}

cat("========================================\n")
cat("GEOROC BEDROCK METAL NICHE BREADTH PGLS\n")
cat("========================================\n\n")
for (v in georoc_vars) {
  results[[v$label]] <- run_model(df_clean, tree_pruned, v$col, v$label)
  cat("\n")
}

cat("========================================\n")
cat("CSU MOBILE METAL NICHE BREADTH PGLS (global)\n")
cat("========================================\n\n")
for (v in csu_vars) {
  results[[v$label]] <- run_model(df_clean, tree_pruned, v$col, v$label)
  cat("\n")
}

cat("========================================\n")
cat("NGSA ICP-MS NICHE BREADTH PGLS (Australia)\n")
cat("========================================\n\n")
for (v in ngsa_icp_vars) {
  results[[v$label]] <- run_model(df_clean, tree_pruned, v$col, v$label)
  cat("\n")
}

cat("========================================\n")
cat("NGSA MMI_ME NICHE BREADTH PGLS (Australia)\n")
cat("========================================\n\n")
for (v in ngsa_mmi_vars) {
  results[[v$label]] <- run_model(df_clean, tree_pruned, v$col, v$label)
  cat("\n")
}

# ─────────────────────────────────────────────────────────────────
# Flatten to CSV
# ─────────────────────────────────────────────────────────────────
rows <- list()
for (nm in names(results)) {
  r <- results[[nm]]
  if (is.null(r)) next
  co <- r$coef
  for (pred in rownames(co)) {
    if (pred == "(Intercept)") next
    rows[[length(rows)+1]] <- data.frame(
      response=r$response, model=r$label, predictor=pred,
      n=r$n, lambda=r$lambda,
      beta=co[pred,"Value"], SE=co[pred,"Std.Error"],
      t=co[pred,"t-value"], p=co[pred,"p-value"],
      stringsAsFactors=FALSE
    )
  }
}
out <- do.call(rbind, rows)
write.csv(out, file.path(DATA_DIR, "env_niche_all_pgls_results.csv"), row.names=FALSE)
cat("Saved env_niche_all_pgls_results.csv\n")
cat(sprintf("Total models: %d, total coefficient rows: %d\n",
            length(results), nrow(out)))
