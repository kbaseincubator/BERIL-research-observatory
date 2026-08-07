#!/usr/bin/env Rscript
# Environmental niche breadth PGLS analysis
# Phylogenetic generalized least squares models for environmental niche predictors

library(ape)
library(nlme)
library(dplyr)

# Set working directory
setwd('/home/hmacgregor/BERIL-research-observatory')

# Load tree
cat("Loading phylogenetic tree...\n")
tree <- read.tree('projects/comprehensive_metal_ecology/data/gtdb_bac_genus_pruned.tree')
cat(sprintf("Tree: %d tips, %d internal nodes\n", Ntip(tree), tree$Nnode))

# Function to run PGLS model with Pagel's lambda estimation
run_pgls_model <- function(data, formula, tree, model_name) {
  cat("\n", strrep("=", 70), "\n", sep="")
  cat(sprintf("Model: %s\n", model_name))
  cat(strrep("=", 70), "\n", sep="")

  # Remove NAs
  data_clean <- na.omit(data)
  n_obs <- nrow(data_clean)
  cat(sprintf("n = %d (after removing NAs)\n", n_obs))

  if (n_obs < 3) {
    cat("Too few observations for model fitting.\n")
    return(NULL)
  }

  # Prepare tree - prune to match data
  tree_pruned <- keep.tip(tree, intersect(tree$tip.label, data_clean$genus_lower))
  n_matched <- length(tree_pruned$tip.label)
  cat(sprintf("Tree tips matched: %d of %d in data\n", n_matched, n_obs))

  if (n_matched < 3) {
    cat("Too few taxa matched to tree.\n")
    return(NULL)
  }

  # Match data to tree (reorder by tree tip labels)
  data_clean <- data_clean[match(tree_pruned$tip.label, data_clean$genus_lower), ]

  # Fit model with Pagel's lambda
  lambda_val <- NA
  model <- NULL
  error_msg <- NULL

  tryCatch({
    # First try with lambda estimation
    model <- gls(formula, data = data_clean,
                 correlation = corPagel(1, phy = tree_pruned, fixed = FALSE),
                 method = 'ML')

    lambda_val <- model$modelStruct$corStruct[1]
    cat(sprintf("Lambda (Pagel's λ): %.4f\n", lambda_val))

  }, error = function(e) {
    cat(sprintf("Lambda estimation failed: %s\n", e$message))
    cat("Fitting with lambda = 0 (no phylogenetic signal)...\n")
    model <<- gls(formula, data = data_clean,
                  correlation = corPagel(0, phy = tree_pruned, fixed = TRUE),
                  method = 'ML')
    lambda_val <<- 0
    cat("Lambda (fixed): 0.0000\n")
  })

  if (is.null(model)) {
    cat("Model fitting failed.\n")
    return(NULL)
  }

  # Extract results
  summary_table <- data.frame(
    model = model_name,
    n = nrow(data_clean),
    lambda = lambda_val,
    AIC = AIC(model),
    stringsAsFactors = FALSE
  )

  # Get coefficients
  coef_tbl <- summary(model)$tTable
  coef_table <- data.frame(
    model = model_name,
    predictor = rownames(coef_tbl),
    beta = coef_tbl[, 'Value'],
    SE = coef_tbl[, 'Std.Error'],
    t_stat = coef_tbl[, 't-value'],
    p_value = coef_tbl[, 'p-value'],
    stringsAsFactors = FALSE
  )

  # Print results
  cat("\nCoefficients:\n")
  print(coef_table)

  cat("\nModel summary:\n")
  print(summary(model))

  list(model = model, coef_table = coef_table, summary_table = summary_table)
}

# Load datasets
cat("\nLoading PGLS input datasets...\n")
dataset_a <- read.csv('projects/comprehensive_metal_ecology/results/env_niche_A_pgls_input.csv')
dataset_b <- read.csv('projects/comprehensive_metal_ecology/results/env_niche_B_pgls_input.csv')
dataset_c <- read.csv('projects/comprehensive_metal_ecology/results/env_niche_C_pgls_input.csv')
dataset_d <- read.csv('projects/comprehensive_metal_ecology/results/env_niche_D_pgls_input.csv')

cat(sprintf("Dataset A: %d x %d\n", nrow(dataset_a), ncol(dataset_a)))
cat(sprintf("Dataset B: %d x %d\n", nrow(dataset_b), ncol(dataset_b)))
cat(sprintf("Dataset C: %d x %d\n", nrow(dataset_c), ncol(dataset_c)))
cat(sprintf("Dataset D: %d x %d\n", nrow(dataset_d), ncol(dataset_d)))

# Store all results
all_results <- list()
all_coefs <- data.frame()

# ============================================================================
# DATASET A: Temperature niche with primary predictors
# ============================================================================
cat("\n\n", strrep("#", 70), "\n", sep="")
cat("# DATASET A: Temperature niche breadth (primary predictors)\n")
cat(strrep("#", 70), "\n", sep="")

# Model A1: median_temp_range_C ~ ko_per_mb_z + genome_mb_z
result_a1 <- run_pgls_model(
  dataset_a[, c('genus_lower', 'median_temp_range_C', 'ko_per_mb_z', 'genome_mb_z')],
  median_temp_range_C ~ ko_per_mb_z + genome_mb_z,
  tree, 'A1: Temp ~ KO_density + genome_size'
)
if (!is.null(result_a1)) {
  all_results$A1 <- result_a1
  all_coefs <- rbind(all_coefs, result_a1$coef_table)
}

# Model A2: median_soil_ph ~ ko_per_mb_z + genome_mb_z
result_a2 <- run_pgls_model(
  dataset_a[, c('genus_lower', 'median_soil_ph', 'ko_per_mb_z', 'genome_mb_z')],
  median_soil_ph ~ ko_per_mb_z + genome_mb_z,
  tree, 'A2: Soil_pH ~ KO_density + genome_size'
)
if (!is.null(result_a2)) {
  all_results$A2 <- result_a2
  all_coefs <- rbind(all_coefs, result_a2$coef_table)
}

# Model A3: median_soil_moisture ~ ko_per_mb_z + genome_mb_z
result_a3 <- run_pgls_model(
  dataset_a[, c('genus_lower', 'median_soil_moisture', 'ko_per_mb_z', 'genome_mb_z')],
  median_soil_moisture ~ ko_per_mb_z + genome_mb_z,
  tree, 'A3: Soil_moisture ~ KO_density + genome_size'
)
if (!is.null(result_a3)) {
  all_results$A3 <- result_a3
  all_coefs <- rbind(all_coefs, result_a3$coef_table)
}

# ============================================================================
# DATASET B: Temperature niche with tier1/tier2 predictors
# ============================================================================
cat("\n\n", strrep("#", 70), "\n", sep="")
cat("# DATASET B: Temperature niche (tier1/tier2 subcategories)\n")
cat(strrep("#", 70), "\n", sep="")

# Model B1: median_temp_range_C ~ ko_per_mb_tier1_z + ko_per_mb_tier2_z + genome_mb_z
result_b1 <- run_pgls_model(
  dataset_b[, c('genus_lower', 'median_temp_range_C', 'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z', 'genome_mb_z')],
  median_temp_range_C ~ ko_per_mb_tier1_z + ko_per_mb_tier2_z + genome_mb_z,
  tree, 'B1: Temp ~ Tier1(resist) + Tier2(cofactor) + genome_size'
)
if (!is.null(result_b1)) {
  all_results$B1 <- result_b1
  all_coefs <- rbind(all_coefs, result_b1$coef_table)
}

# Model B2: median_soil_ph ~ ko_per_mb_tier1_z + ko_per_mb_tier2_z + genome_mb_z
result_b2 <- run_pgls_model(
  dataset_b[, c('genus_lower', 'median_soil_ph', 'ko_per_mb_tier1_z', 'ko_per_mb_tier2_z', 'genome_mb_z')],
  median_soil_ph ~ ko_per_mb_tier1_z + ko_per_mb_tier2_z + genome_mb_z,
  tree, 'B2: Soil_pH ~ Tier1(resist) + Tier2(cofactor) + genome_size'
)
if (!is.null(result_b2)) {
  all_results$B2 <- result_b2
  all_coefs <- rbind(all_coefs, result_b2$coef_table)
}

# ============================================================================
# DATASET C: Multi-environment gradient breadth
# ============================================================================
cat("\n\n", strrep("#", 70), "\n", sep="")
cat("# DATASET C: Environmental gradient breadth (composite)\n")
cat(strrep("#", 70), "\n", sep="")

# Model C1: env_gradient_breadth ~ ko_per_mb_z + genome_mb_z
result_c1 <- run_pgls_model(
  dataset_c[, c('genus_lower', 'env_gradient_breadth', 'ko_per_mb_z', 'genome_mb_z')],
  env_gradient_breadth ~ ko_per_mb_z + genome_mb_z,
  tree, 'C1: Env_gradient ~ KO_density + genome_size'
)
if (!is.null(result_c1)) {
  all_results$C1 <- result_c1
  all_coefs <- rbind(all_coefs, result_c1$coef_table)
}

# ============================================================================
# DATASET D: MGnify metal niche breadth (limited sample)
# ============================================================================
cat("\n\n", strrep("#", 70), "\n", sep="")
cat("# DATASET D: MGnify metal niche breadth (limited: n=25)\n")
cat(strrep("#", 70), "\n", sep="")

if (nrow(dataset_d) >= 3) {
  # Model D1: Cu_sd ~ ko_per_mb_total_z
  dat_d1 <- dataset_d[!is.na(dataset_d$Cu_sd), c('genus_lower', 'Cu_sd', 'ko_per_mb_total_z')]
  if (nrow(dat_d1) >= 3) {
    result_d1 <- run_pgls_model(
      dat_d1,
      Cu_sd ~ ko_per_mb_total_z,
      tree, 'D1: Cu_niche ~ KO_density (MGnify, n=25)'
    )
    if (!is.null(result_d1)) {
      all_results$D1 <- result_d1
      all_coefs <- rbind(all_coefs, result_d1$coef_table)
    }
  }

  # Model D2: Zn_sd ~ ko_per_mb_total_z
  dat_d2 <- dataset_d[!is.na(dataset_d$Zn_sd), c('genus_lower', 'Zn_sd', 'ko_per_mb_total_z')]
  if (nrow(dat_d2) >= 3) {
    result_d2 <- run_pgls_model(
      dat_d2,
      Zn_sd ~ ko_per_mb_total_z,
      tree, 'D2: Zn_niche ~ KO_density (MGnify, n=25)'
    )
    if (!is.null(result_d2)) {
      all_results$D2 <- result_d2
      all_coefs <- rbind(all_coefs, result_d2$coef_table)
    }
  }

  # Model D3: metal_niche_composite ~ ko_per_mb_total_z
  dat_d3 <- dataset_d[!is.na(dataset_d$metal_niche_composite), c('genus_lower', 'metal_niche_composite', 'ko_per_mb_total_z')]
  if (nrow(dat_d3) >= 3) {
    result_d3 <- run_pgls_model(
      dat_d3,
      metal_niche_composite ~ ko_per_mb_total_z,
      tree, 'D3: Metal_niche_composite ~ KO_density (MGnify, n=25)'
    )
    if (!is.null(result_d3)) {
      all_results$D3 <- result_d3
      all_coefs <- rbind(all_coefs, result_d3$coef_table)
    }
  }
}

# ============================================================================
# Summary and save
# ============================================================================
cat("\n\n", strrep("=", 70), "\n", sep="")
cat("PGLS RESULTS SUMMARY\n")
cat(strrep("=", 70), "\n", sep="")

print(all_coefs)

# Save results
write.csv(all_coefs, 'projects/comprehensive_metal_ecology/results/env_niche_pgls_coefficients.csv', row.names = FALSE)
cat("\nDetailed coefficients saved to: env_niche_pgls_coefficients.csv\n")

cat("\n", strrep("=", 70), "\n", sep="")
cat("PGLS analysis complete!\n")
cat(strrep("=", 70), "\n", sep="")
