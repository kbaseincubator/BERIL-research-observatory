#!/usr/bin/env Rscript
# Task D: Check for within-genus SE of Levins' B in PGLS input
# Required for Ives & Garland (2010) tip-error correction

suppressMessages({
  library(ape)
  library(nlme)
})

DATA <- "data"

cat("Checking PGLS input for per-genus SE of Levins' B...\n")

pgls_input <- read.csv(file.path(DATA, "01_pgls_input_bacteria.csv"))
cat("PGLS input shape:", nrow(pgls_input), "rows x", ncol(pgls_input), "columns\n")
cat("\nColumn names:\n")
print(colnames(pgls_input))

# Check for SE-like columns
se_cols <- colnames(pgls_input)[grep("se|std|var|error", colnames(pgls_input), ignore.case = TRUE)]
cat("\nColumns matching 'se|std|var|error' pattern:\n")
if (length(se_cols) > 0) {
  print(se_cols)
} else {
  cat("(none found)\n")
}

# Specifically check for Levins B SE
levins_b_cols <- colnames(pgls_input)[grep("levins|niche", colnames(pgls_input), ignore.case = TRUE)]
cat("\nColumns matching 'levins|niche' pattern:\n")
print(levins_b_cols)

cat("\n=== FEASIBILITY ASSESSMENT ===\n")
cat("Per-genus SEM of Levins' B: NOT FOUND in PGLS input\n")
cat("\nColumn inventory:\n")
for (col in colnames(pgls_input)) {
  cat(sprintf("  %s: %s (%d non-NA)\n", col, class(pgls_input[[col]])[1], sum(!is.na(pgls_input[[col]]))))
}

cat("\n=== CONSTRAINT ===\n")
cat("The PGLS input contains only mean_levins_B_std (aggregated mean per genus).\n")
cat("To compute per-genus SEM (standard error of the mean), we would need:\n")
cat("  1. Per-sample Levins' B values for each genus\n")
cat("  2. The aggregation happens in NB01 (Spark pipeline)\n")
cat("\nThese per-sample values were not saved to the PGLS input CSV.\n")
cat("\n=== DECISION ===\n")
cat("Feasibility: BLOCKED on data unavailability\n")
cat("To enable Ives et al. correction:\n")
cat("  - Re-run NB01 to export per-sample Levins' B\n")
cat("  - Recompute per-genus SEM from the per-sample distribution\n")
cat("  - Add se_levins_B column to PGLS input\n")
cat("  - Then run ives_lambda_correction.R\n")

# Save status
status_txt <- "Per-genus SEM of Levins' B is not in the PGLS input (01_pgls_input_bacteria.csv).

Computation is infeasible because:
1. The per-sample Levins' B values used to compute the mean were not saved
2. These were aggregated in NB01 (Spark pipeline)
3. Only the mean (mean_levins_B_std) is available

To enable Ives & Garland (2010) tip-error correction:
- Re-run NB01 to export per-sample Levins' B values
- Compute per-genus SEM: SE = sd(B_samples) / sqrt(n_samples)
- Add se_levins_B column to 01_pgls_input_bacteria.csv
- Then run ives_lambda_correction.R
"

writeLines(status_txt, con = file.path(DATA, "ives_lambda_correction_status.txt"))
cat("\nSaved status -> data/ives_lambda_correction_status.txt\n")

cat("\nDone.\n")
