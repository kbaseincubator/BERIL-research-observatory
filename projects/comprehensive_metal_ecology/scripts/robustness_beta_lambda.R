#!/usr/bin/env Rscript
# Phylogenetic signal robustness check: beta-regression-compatible Pagel's λ
# via phylolm on arcsine-sqrt-transformed genus presence fractions.
#
# Method:
#   - Load genus presence fractions (0.0001 to 0.9999 clipped)
#   - Arcsine-sqrt transform to stabilize variance
#   - Fit phylolm(y ~ 1, model="BM") for each KO to estimate λ via profile likelihood
#   - Compare to original PGLS-based λ estimates
#   - Report correlation, mean absolute difference, classification changes
#
# Classification threshold: λ < 0.3 indicates weak phylogenetic signal

library(phylolm)
library(ape)

set.seed(42)

# Load input data
cat("Loading data...\n")
input_file <- "results/robustness_beta_lambda_input.csv"
d <- read.csv(input_file, stringsAsFactors=FALSE)

cat("Loaded:", nrow(d), "rows,", length(unique(d$ko_id)), "unique KOs\n")

# Load tree
cat("Loading tree...\n")
tree_file <- "data/gtdb_bac_genus_pruned.tree"
tree <- read.tree(tree_file)
cat("Tree has", length(tree$tip.label), "tips\n")

# Fit phylolm for each KO
cat("\nFitting phylolm for each KO...\n")

ko_list <- unique(d$ko_id)
results_list <- list()

for (i in seq_along(ko_list)) {
  ko <- ko_list[i]

  if (i %% 20 == 0) cat("  KO", i, "/", length(ko_list), "\n")

  ko_data <- d[d$ko_id == ko, ]

  # Check how many unique genera we have
  n_unique_genera <- length(unique(ko_data$genus))
  if (n_unique_genera < 10) {
    cat("    Warning: KO", ko, "has only", n_unique_genera, "genera, skipping\n")
    next
  }

  # Match genera to tree tips
  ko_data$genus_in_tree <- ko_data$genus %in% tree$tip.label
  n_matched <- sum(ko_data$genus_in_tree)

  if (n_matched < 10) {
    cat("    Warning: KO", ko, "matched only", n_matched, "genera to tree, skipping\n")
    next
  }

  # Prune data to matched genera
  ko_data_pruned <- ko_data[ko_data$genus_in_tree, ]

  # Data is already at genus-KO level (one row per genus per KO)
  # Set row names to genus for phylolm
  rownames(ko_data_pruned) <- ko_data_pruned$genus

  # Ensure no NAs
  if (any(is.na(ko_data_pruned$y_transformed))) {
    cat("    Warning: KO", ko, "has NAs in y_transformed, skipping\n")
    next
  }

  ko_genus_level <- ko_data_pruned[, c("y_transformed", "presence_fraction", "n_genomes_with_ko")]
  genus_names <- rownames(ko_genus_level)

  # Match to tree
  tree_pruned <- drop.tip(tree, tree$tip.label[!(tree$tip.label %in% genus_names)])

  # Fit phylolm with lambda model (Pagel's lambda)
  tryCatch({
    fit <- phylolm(y_transformed ~ 1, data=ko_genus_level, phy=tree_pruned, model="lambda")
    lambda_estimate <- fit$optpar[1]  # optpar is a numeric vector with the lambda estimate

    # Get metadata for this KO
    ko_meta <- ko_data[1, c("gene_name", "subcategory", "evidence_tier", "lambda_original")]

    results_list[[ko]] <- data.frame(
      ko_id = ko,
      gene_name = ko_meta$gene_name,
      subcategory = ko_meta$subcategory,
      evidence_tier = ko_meta$evidence_tier,
      lambda_original = ko_meta$lambda_original,
      lambda_beta = lambda_estimate,
      n_genera_analyzed = nrow(ko_genus_level),
      stringsAsFactors = FALSE
    )
  }, error = function(e) {
    cat("    Error fitting KO", ko, ":", e$message, "\n")
  })
}

# Combine results
cat("\nCombining results...\n")
results_df <- do.call(rbind, results_list)
rownames(results_df) <- NULL

# Compute delta and classification change
results_df$delta <- abs(results_df$lambda_beta - results_df$lambda_original)
results_df$class_original <- ifelse(results_df$lambda_original < 0.3, "weak", "strong")
results_df$class_beta <- ifelse(results_df$lambda_beta < 0.3, "weak", "strong")
results_df$class_changed <- ifelse(results_df$class_original != results_df$class_beta, 1, 0)

cat("\nResults summary:\n")
cat("N KOs analyzed:", nrow(results_df), "\n")

# Compute statistics excluding NAs
valid_idx <- !is.na(results_df$lambda_original)
n_valid <- sum(valid_idx)
cat("N KOs with valid original lambda:", n_valid, "\n")

if (n_valid > 0) {
  spearman_cor <- cor(results_df$lambda_original[valid_idx], results_df$lambda_beta[valid_idx], method="spearman")
  mean_delta <- mean(results_df$delta[valid_idx])
  n_class_change <- sum(results_df$class_changed[valid_idx], na.rm=TRUE)
  pct_change <- 100 * n_class_change / n_valid

  cat("Spearman correlation (original vs beta):",
      round(spearman_cor, 4), "\n")
  cat("Mean absolute difference (delta):",
      round(mean_delta, 4), "\n")
  cat("N KOs with classification change:",
      n_class_change, "out of", n_valid, "\n")
  cat("Percent classification change:",
      round(pct_change, 2), "%\n")
} else {
  cat("No valid comparisons available.\n")
}

# Save results
cat("\nSaving results...\n")
output_file <- "results/robustness_beta_lambda.csv"
write.csv(results_df, output_file, row.names=FALSE)
cat("Saved to", output_file, "\n")

# Summary statistics
cat("\n=== ROBUSTNESS CHECK SUMMARY ===\n")
cat("Original lambda (PGLS on genus presence):\n")
print(summary(results_df$lambda_original))
cat("\nBeta-regression lambda (phylolm on arcsine-sqrt):\n")
print(summary(results_df$lambda_beta))

if (n_valid > 0) {
  cat("\nDelta (absolute difference) for valid comparisons:\n")
  print(summary(results_df$delta[valid_idx]))
  cat("\nClassification contingency table (excluding NAs):\n")
  print(table(original=results_df$class_original[valid_idx], beta=results_df$class_beta[valid_idx]))
}
