#!/usr/bin/env Rscript
# Metal niche breadth PGLS: Cu_sd, Zn_sd, composite ~ KO density + genome size
# Uses AusMicrobiome bedrock metal SD per genus (actual niche breadth)

library(ape)
library(nlme)

DATA_DIR <- "projects/comprehensive_metal_ecology/results"
TREE_FILE <- "projects/microbeatlas_metal_ecology/data/gtdb_bac_genus_pruned.tree"

cat("Loading data...\n")
df <- read.csv(file.path(DATA_DIR, "env_niche_metal_sd_input.csv"), stringsAsFactors=FALSE)
df_tier <- read.csv(file.path(DATA_DIR, "env_niche_metal_sd_tier_input.csv"), stringsAsFactors=FALSE)
cat(sprintf("Input: %d genera\n", nrow(df)))

cat("Loading tree...\n")
tree <- read.tree(TREE_FILE)
cat(sprintf("Tree tips: %d\n", length(tree$tip.label)))

# Match genus names: replace spaces with underscores for tree matching
df$genus_tree <- gsub(" ", "_", df$genus_lower)
df_tier$genus_tree <- gsub(" ", "_", df_tier$genus_lower)

# Prune tree to genus set
shared <- intersect(df$genus_tree, tree$tip.label)
cat(sprintf("Tree overlap: %d of %d genera\n", length(shared), nrow(df)))

tree_pruned <- drop.tip(tree, setdiff(tree$tip.label, shared))
df_clean <- df[df$genus_tree %in% shared, ]
df_clean <- df_clean[match(tree_pruned$tip.label, df_clean$genus_tree), ]
rownames(df_clean) <- df_clean$genus_tree

df_tier_clean <- df_tier[df_tier$genus_tree %in% shared, ]
df_tier_clean <- df_tier_clean[match(tree_pruned$tip.label, df_tier_clean$genus_tree), ]
rownames(df_tier_clean) <- df_tier_clean$genus_tree

cat(sprintf("Final n: %d\n\n", nrow(df_clean)))

# Helper function
run_model <- function(data, tree, formula_str, label) {
  cat(sprintf("--- %s ---\n", label))
  fml <- as.formula(formula_str)
  tryCatch({
    mod <- gls(fml, data=data,
               correlation=corPagel(value=1, phy=tree, fixed=FALSE, form=~genus_tree),
               method="ML", na.action=na.omit)
    co <- summary(mod)$tTable
    lam <- as.numeric(mod$modelStruct$corStruct)
    cat(sprintf("  n=%d, lambda=%.4f\n", nrow(data), lam))
    for (i in 1:nrow(co)) {
      cat(sprintf("  %-25s beta=%.4f SE=%.4f t=%.3f p=%.4f\n",
                  rownames(co)[i], co[i,1], co[i,2], co[i,3], co[i,4]))
    }
    return(list(label=label, n=nrow(data), lambda=lam,
                coef=as.data.frame(co), formula=formula_str))
  }, error=function(e) {
    cat(sprintf("  ERROR: %s\n", conditionMessage(e)))
    # Fallback: OLS
    tryCatch({
      mod0 <- gls(fml, data=data,
                  correlation=corPagel(value=0, phy=tree, fixed=TRUE, form=~genus_tree),
                  method="ML", na.action=na.omit)
      co <- summary(mod0)$tTable
      cat(sprintf("  Fallback OLS: n=%d, lambda=0 (fixed)\n", nrow(data)))
      for (i in 1:nrow(co)) {
        cat(sprintf("  %-25s beta=%.4f SE=%.4f t=%.3f p=%.4f\n",
                    rownames(co)[i], co[i,1], co[i,2], co[i,3], co[i,4]))
      }
      return(list(label=label, n=nrow(data), lambda=0,
                  coef=as.data.frame(co), formula=formula_str))
    }, error=function(e2) {
      cat(sprintf("  Fallback also failed: %s\n", conditionMessage(e2)))
      return(NULL)
    })
  })
}

cat("========================================\n")
cat("METAL NICHE BREADTH PGLS (AusMicrobiome)\n")
cat("Response = SD of bedrock metal across occupied samples\n")
cat("========================================\n\n")

results <- list()

# Primary predictor models
results[["Cu_primary"]] <- run_model(df_clean, tree_pruned,
  "Cu_sd ~ ko_z + genome_z", "Cu_sd ~ KO_primary + genome")
cat("\n")
results[["Zn_primary"]] <- run_model(df_clean, tree_pruned,
  "Zn_sd ~ ko_z + genome_z", "Zn_sd ~ KO_primary + genome")
cat("\n")
results[["Pb_primary"]] <- run_model(df_clean, tree_pruned,
  "Pb_sd ~ ko_z + genome_z", "Pb_sd ~ KO_primary + genome")
cat("\n")
results[["Ni_primary"]] <- run_model(df_clean, tree_pruned,
  "Ni_sd ~ ko_z + genome_z", "Ni_sd ~ KO_primary + genome")
cat("\n")
results[["Co_primary"]] <- run_model(df_clean, tree_pruned,
  "Co_sd ~ ko_z + genome_z", "Co_sd ~ KO_primary + genome")
cat("\n")
results[["composite_primary"]] <- run_model(df_clean, tree_pruned,
  "composite_metal_sd ~ ko_z + genome_z", "composite_metal_sd ~ KO_primary + genome")
cat("\n")

# Subcategory models (tier1=resistance, tier2=cofactor)
has_tier <- !is.na(df_tier_clean$ko_per_mb_tier1_z)
df_tier_sub <- df_tier_clean[has_tier, ]
tree_tier <- drop.tip(tree_pruned, setdiff(tree_pruned$tip.label, df_tier_sub$genus_tree))
df_tier_sub <- df_tier_sub[match(tree_tier$tip.label, df_tier_sub$genus_tree), ]
cat(sprintf("Subcategory dataset: n=%d\n\n", nrow(df_tier_sub)))

results[["Cu_tiers"]] <- run_model(df_tier_sub, tree_tier,
  "Cu_sd ~ ko_per_mb_tier1_z + ko_per_mb_tier2_z + genome_z",
  "Cu_sd ~ tier1(resist) + tier2(cofactor) + genome")
cat("\n")
results[["composite_tiers"]] <- run_model(df_tier_sub, tree_tier,
  "composite_metal_sd ~ ko_per_mb_tier1_z + ko_per_mb_tier2_z + genome_z",
  "composite_metal_sd ~ tier1(resist) + tier2(cofactor) + genome")
cat("\n")

# Collect results into a flat CSV
rows <- list()
for (nm in names(results)) {
  r <- results[[nm]]
  if (is.null(r)) next
  co <- r$coef
  for (pred in rownames(co)) {
    if (pred == "(Intercept)") next
    rows[[length(rows)+1]] <- data.frame(
      model=r$label, predictor=pred, n=r$n, lambda=r$lambda,
      beta=co[pred,"Value"], SE=co[pred,"Std.Error"],
      t=co[pred,"t-value"], p=co[pred,"p-value"],
      stringsAsFactors=FALSE
    )
  }
}
out <- do.call(rbind, rows)
write.csv(out, file.path(DATA_DIR, "env_niche_metal_sd_pgls_results.csv"), row.names=FALSE)
cat("Results saved to env_niche_metal_sd_pgls_results.csv\n")
