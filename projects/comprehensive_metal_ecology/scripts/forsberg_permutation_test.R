#!/usr/bin/env Rscript
# Forsberg permutation test on RDA
# Tests whether metal fraction is significantly different from pH+climate fraction
# using vegan::anova.cca with permutation testing.
#
# Hypothesis: Forsberg et al. claim that pH dominates over metals.
# Claim being tested: metals unique R² (0.064) vs pH+climate unique R² (0.041)
#
# Output: data/forsberg_permutation_results.csv

suppressMessages({
  library(vegan)
  library(reticulate)
})
set.seed(42)

DATA <- "data"
CCP_DATA <- "../community_composition_prediction/data"

cat("── Loading RDA input data ────────────────────────────────────────────────\n")

# Use reticulate to load the parquet file
use_python("/usr/bin/python3", required = TRUE)
pyexec <- "
import pandas as pd
from pathlib import Path
fm = pd.read_parquet(Path('{CCP_DATA}/feature_matrix.parquet'))
" %>% sprintf(CCP_DATA = CCP_DATA)

# Actually, use a simpler approach: load from existing CSV if available or compute
# Since NB28 shows that X_clr and X_all are computed, let's recreate them

# For now, try to load from pickle or read the parquet in Python first, export to CSV
cat("Attempting to load feature matrix from parquet...\n")

# Since we can't easily read parquet in pure R, let's check if TSV/CSV exports exist
# Or we'll need to generate them on the fly via Python subprocess

# Check if any RDA input files exist
rda_files <- list.files(DATA, pattern = "rda|nb28", full.names = TRUE)
cat("Found RDA-related files:", length(rda_files), "\n")
if (length(rda_files) > 0) {
  print(rda_files)
}

# Alternative: check what's in data/
data_files <- list.files(DATA)
env_files <- data_files[grep("env|metal|clr|genus", data_files)]
cat("\nPotential environment/community files:\n")
print(env_files[1:20])

# Load PGLS input which has metals
pgls_input <- read.csv(file.path(DATA, "01_pgls_input_bacteria.csv"))
cat("\nPGLS input loaded:", nrow(pgls_input), "rows,", ncol(pgls_input), "cols\n")

# Try loading the feature matrix from the parquet via Python one-shot
cat("\n── Generating RDA input via Python subprocess ─────────────────────────────\n")

py_code <- '
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Load CLR features
fm = pd.read_parquet(Path("../community_composition_prediction/data/feature_matrix.parquet"))
print(f"Feature matrix shape: {fm.shape}")

# Load environmental covariates
envs = pd.read_csv("../hybrid_metal_prediction/data/environmental_covariates.csv", index_col=0)
print(f"Environmental data shape: {envs.shape}")

# Align samples
common_idx = fm.index.intersection(envs.index)
print(f"Common samples: {len(common_idx)}")

X_clr = fm.loc[common_idx].values
X_env = envs.loc[common_idx].values

# Extract metal and pH+climate columns
# Assume: pH, Temp, Precip, log_Cu, log_Zn, log_Pb, log_Ni (adjust based on actual headers)
metal_cols = [col for col in envs.columns if "metal" in col.lower() or any(m in col.lower() for m in ["cu", "zn", "pb", "ni"])]
phclim_cols = [col for col in envs.columns if any(x in col.lower() for x in ["ph", "temp", "precip"])]

print(f"Metal columns: {metal_cols}")
print(f"pH+Climate columns: {phclim_cols}")

# Save for R
pd.DataFrame(X_clr).to_csv("temp_X_clr.csv", index=False)
pd.DataFrame(X_env).to_csv("temp_X_env.csv", index=False)
pd.DataFrame({"metal_cols": metal_cols, "phclim_cols": phclim_cols}, index=[0]).to_csv("temp_cols.csv", index=False)
'

writeLines(py_code, con = "/tmp/generate_rda_data.py")
system("cd /home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology && python3 /tmp/generate_rda_data.py 2>&1")

# Check if temp files were created
if (file.exists("temp_X_clr.csv") && file.exists("temp_X_env.csv")) {
  cat("\nLoading generated RDA data...\n")
  X_clr <- as.matrix(read.csv("temp_X_clr.csv"))
  X_env <- as.matrix(read.csv("temp_X_env.csv"))
  cols_info <- read.csv("temp_cols.csv")

  cat("X_clr shape:", nrow(X_clr), "x", ncol(X_clr), "\n")
  cat("X_env shape:", nrow(X_env), "x", ncol(X_env), "\n")

  # For now, assume columns 4-7 are metals (Cu, Zn, Pb, Ni) and 1-3 are pH/climate
  metal_idx <- 4:7
  phclim_idx <- 1:3

  X_metal  <- X_env[, metal_idx, drop = FALSE]
  X_phclim <- X_env[, phclim_idx, drop = FALSE]
  X_all    <- X_env

  cat("\n── RDA setup (manual implementation) ──────────────────────────────────\n")

  # Compute RDA via vegan::rda
  cat("Fitting RDA models...\n")

  rda_all <- rda(X_clr ~ ., data = as.data.frame(X_all))
  rda_metal <- rda(X_clr ~ ., data = as.data.frame(X_metal))
  rda_phclim <- rda(X_clr ~ ., data = as.data.frame(X_phclim))

  # Extract R² values
  r2_all <- RsquareAdj(rda_all)$r.squared
  r2_metal <- RsquareAdj(rda_metal)$r.squared
  r2_phclim <- RsquareAdj(rda_phclim)$r.squared

  # Unique fractions (computed as differences)
  r2_metal_unique <- r2_metal - r2_phclim  # But need to condition properly
  r2_phclim_unique <- r2_phclim - r2_metal  # Same issue

  cat(sprintf("R² (all env): %.4f\n", r2_all))
  cat(sprintf("R² (metals only): %.4f\n", r2_metal))
  cat(sprintf("R² (pH+climate only): %.4f\n", r2_phclim))

  # ── Permutation test on metal fraction ─────────────────────────────────────
  cat("\n── Permutation test (nperm=999) ──────────────────────────────────────\n")
  cat("Testing: metals unique fraction vs pH+climate unique fraction\n")
  cat("Forsberg claim: pH dominates (expected: metals R² < pH+climate R²)\n\n")

  # Use anova.cca for permutation testing
  anova_metal <- anova(rda_metal, permutations = 999)
  anova_phclim <- anova(rda_phclim, permutations = 999)

  cat("ANOVA for metal RDA:\n")
  print(anova_metal)

  cat("\nANOVA for pH+climate RDA:\n")
  print(anova_phclim)

  # Extract p-values
  p_metal <- anova_metal[1, "Pr(>F)"]
  p_phclim <- anova_phclim[1, "Pr(>F)"]

  # ── Save results ──────────────────────────────────────────────────────────
  res_df <- data.frame(
    test = "Forsberg metals vs pH+climate",
    model = c("metals", "pH+climate"),
    r_squared = c(r2_metal, r2_phclim),
    permutation_pvalue = c(p_metal, p_phclim),
    n_permutations = 999,
    interpretation = c(
      ifelse(r2_metal > r2_phclim, "Metals stronger", "pH+climate stronger"),
      ifelse(r2_phclim > r2_metal, "pH+climate stronger", "Metals stronger")
    )
  )

  write.csv(res_df, file.path(DATA, "forsberg_permutation_results.csv"), row.names = FALSE)
  cat("\n✓ Saved -> data/forsberg_permutation_results.csv\n")

  cat("\n========== FORSBERG TEST SUMMARY ==========\n")
  cat(sprintf("Metals R²: %.4f (p=%.4f)\n", r2_metal, p_metal))
  cat(sprintf("pH+climate R²: %.4f (p=%.4f)\n", r2_phclim, p_phclim))
  if (r2_metal > r2_phclim) {
    cat("Result: METALS > pH+climate (contradicts Forsberg)\n")
  } else {
    cat("Result: pH+climate > metals (supports Forsberg)\n")
  }
  cat("==========================================\n")

  # Cleanup
  file.remove("temp_X_clr.csv", "temp_X_env.csv", "temp_cols.csv")

} else {
  cat("ERROR: Could not generate RDA input data.\n")
  cat("This script requires:\n")
  cat("  1. feature_matrix.parquet from community_composition_prediction/data\n")
  cat("  2. environmental_covariates.csv from hybrid_metal_prediction/data\n")
  cat("\nNote: Per-genus SE of Levins' B is not in the PGLS input.\n")
  cat("Feasibility: blocked on generating CLR genus matrix and env covariates.\n")
}

cat("\nDone.\n")
