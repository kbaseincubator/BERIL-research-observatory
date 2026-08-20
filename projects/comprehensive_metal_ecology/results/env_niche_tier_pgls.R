#!/usr/bin/env Rscript
# Resistance vs cofactor split for all 33 environmental niche breadth responses
# response ~ tier1_z (resistance) + tier2_z (cofactor) + genome_mb_z
# n=386 genera (AusMicrobiome overlap with tier z-scores)

library(ape)
library(nlme)

DATA_DIR  <- "projects/comprehensive_metal_ecology/results"
TREE_FILE <- "projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree"

cat("Loading data...\n")
df <- read.csv(file.path(DATA_DIR, "env_niche_tier_pgls_input.csv"), stringsAsFactors=FALSE)
cat(sprintf("Input: %d genera\n", nrow(df)))

cat("Loading tree...\n")
tree <- read.tree(TREE_FILE)

df$genus_tree <- gsub(" ", "_", df$genus_lower)
shared <- intersect(df$genus_tree, tree$tip.label)
tree_pruned <- drop.tip(tree, setdiff(tree$tip.label, shared))
df_clean <- df[df$genus_tree %in% shared, ]
df_clean <- df_clean[match(tree_pruned$tip.label, df_clean$genus_tree), ]
rownames(df_clean) <- df_clean$genus_tree
cat(sprintf("Tree overlap: %d genera\n\n", nrow(df_clean)))

# ─────────────────────────────────────────────────────────────────
run_tier_model <- function(data, tree, response_col, label_prefix) {
  fml_str  <- sprintf("%s ~ ko_per_mb_tier1_z + ko_per_mb_tier2_z + genome_mb_z", response_col)
  label    <- sprintf("%s ~ resist + cofactor + genome", label_prefix)
  tryCatch({
    mod <- gls(as.formula(fml_str), data=data,
               correlation=corPagel(value=1, phy=tree, fixed=FALSE, form=~genus_tree),
               method="ML", na.action=na.omit)
    co  <- summary(mod)$tTable
    lam <- as.numeric(mod$modelStruct$corStruct)
    n_fit <- length(mod$residuals)
    cat(sprintf("--- %s: n=%d lambda=%.4f ---\n", label, n_fit, lam))
    for (i in 1:nrow(co)) {
      cat(sprintf("  %-25s beta=%.4f SE=%.4f t=%.3f p=%.4f\n",
                  rownames(co)[i], co[i,1], co[i,2], co[i,3], co[i,4]))
    }
    return(list(label=label, response=response_col, n=n_fit, lambda=lam, coef=as.data.frame(co)))
  }, error=function(e) {
    cat(sprintf("  PGLS error: %s — OLS fallback\n", conditionMessage(e)))
    tryCatch({
      mod0 <- gls(as.formula(fml_str), data=data,
                  correlation=corPagel(value=0, phy=tree, fixed=TRUE, form=~genus_tree),
                  method="ML", na.action=na.omit)
      co <- summary(mod0)$tTable
      n_fit <- length(mod0$residuals)
      cat(sprintf("  Fallback OLS: n=%d, lambda=0\n", n_fit))
      return(list(label=label, response=response_col, n=n_fit, lambda=0, coef=as.data.frame(co)))
    }, error=function(e2) {
      cat(sprintf("  Both failed: %s\n", conditionMessage(e2))); return(NULL)
    })
  })
}

# ─────────────────────────────────────────────────────────────────
# SD response variables (same 33 as primary env niche PGLS)
sd_responses <- list(
  list(col="pH_sd",   lab="pH_sd"),
  list(col="temp_sd", lab="temp_sd"),
  # GeoROC
  list(col="georoc_Cu_sd", lab="GeoROC_Cu"), list(col="georoc_Ni_sd", lab="GeoROC_Ni"),
  list(col="georoc_Zn_sd", lab="GeoROC_Zn"), list(col="georoc_Co_sd", lab="GeoROC_Co"),
  list(col="georoc_Cr_sd", lab="GeoROC_Cr"), list(col="georoc_Pb_sd", lab="GeoROC_Pb"),
  list(col="georoc_As_sd", lab="GeoROC_As"), list(col="georoc_Cd_sd", lab="GeoROC_Cd"),
  list(col="georoc_Hg_sd", lab="GeoROC_Hg"),
  # CSU
  list(col="PF1_As_sd", lab="CSU_As"), list(col="PF1_Cd_sd", lab="CSU_Cd"),
  list(col="PF1_Cr_sd", lab="CSU_Cr"), list(col="PF1_Cu_sd", lab="CSU_Cu"),
  list(col="PF1_Hg_sd", lab="CSU_Hg"), list(col="PF1_Pb_sd", lab="CSU_Pb"),
  # NGSA ICP-MS
  list(col="Cu_ICP_MS_mg_kg_0_2_sd", lab="NGSA_ICP_Cu"),
  list(col="Ni_ICP_MS_mg_kg_0_5_sd", lab="NGSA_ICP_Ni"),
  list(col="Zn_ICP_MS_mg_kg_0_9_sd", lab="NGSA_ICP_Zn"),
  list(col="Pb_ICP_MS_mg_kg_0_1_sd", lab="NGSA_ICP_Pb"),
  list(col="As_ICP_MS_mg_kg_0_4_sd", lab="NGSA_ICP_As"),
  list(col="Co_ICP_MS_mg_kg_0_1_sd", lab="NGSA_ICP_Co"),
  list(col="Cr_ICP_MS_mg_kg_0_5_sd", lab="NGSA_ICP_Cr"),
  list(col="Hg_AR_mg_kg_0_01_sd",    lab="NGSA_ICP_Hg"),
  # NGSA MMI_ME
  list(col="Cu_MMI_ME_mg_kg_0_01_sd",  lab="NGSA_MMI_Cu"),
  list(col="Ni_MMI_ME_mg_kg_0_005_sd", lab="NGSA_MMI_Ni"),
  list(col="Zn_MMI_ME_mg_kg_0_02_sd",  lab="NGSA_MMI_Zn"),
  list(col="Pb_MMI_ME_mg_kg_0_01_sd",  lab="NGSA_MMI_Pb"),
  list(col="As_MMI_ME_mg_kg_0_01_sd",  lab="NGSA_MMI_As"),
  list(col="Co_MMI_ME_mg_kg_0_005_sd", lab="NGSA_MMI_Co"),
  list(col="Cr_MMI_ME_mg_kg_0_001_sd", lab="NGSA_MMI_Cr"),
  list(col="Hg_MMI_ME_mg_kg_0_001_sd", lab="NGSA_MMI_Hg")
)

cat("Running tier split PGLS for all 33 env niche breadth responses...\n\n")
results <- lapply(sd_responses, function(v) {
  run_tier_model(df_clean, tree_pruned, v$col, v$lab)
})

# Flatten to CSV
rows <- list()
for (r in results) {
  if (is.null(r)) next
  co <- r$coef
  for (pred_nm in rownames(co)) {
    if (pred_nm == "(Intercept)") next
    rows[[length(rows)+1]] <- data.frame(
      response=r$response, model=r$label, predictor=pred_nm,
      n=r$n, lambda=r$lambda,
      beta=co[pred_nm,"Value"], SE=co[pred_nm,"Std.Error"],
      t=co[pred_nm,"t-value"], p=co[pred_nm,"p-value"],
      stringsAsFactors=FALSE)
  }
}
out <- do.call(rbind, rows)
write.csv(out, file.path(DATA_DIR, "env_niche_tier_pgls_results.csv"), row.names=FALSE)
cat(sprintf("\nSaved env_niche_tier_pgls_results.csv (%d rows)\n", nrow(out)))
