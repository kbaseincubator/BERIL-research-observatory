#!/usr/bin/env Rscript
# Phylogenetic effective sample size (pESS) for the primary PGLS
# Formula: pESS = n^2 / sum(C_lambda)
#   C_lambda = lambda * C_phylo + (1 - lambda) * I
#   C_phylo  = phylogenetic correlation matrix from GTDB tree
# Reference: Bartoszek 2016 J Theor Biol 407:371; Cheverud et al. 1985
# Lambda values: 0 (OLS), 0.757618 (Pagel ML from NB01), 1 (Brownian)

suppressMessages(library(ape))

DATA <- "projects/comprehensive_metal_ecology/data"

cat("Loading tree...\n")
tree <- read.tree(file.path(DATA, "gtdb_bac_genus_pruned.tree"))
n <- length(tree$tip.label)
cat(sprintf("  Tips: %d\n", n))

cat("Building VCV matrix (ape::vcv)...\n")
vcv_mat <- vcv(tree)
cat("  VCV built. Computing correlation matrix...\n")

# Normalise to correlation matrix: C[i,j] = VCV[i,j] / sqrt(VCV[i,i] * VCV[j,j])
d <- sqrt(diag(vcv_mat))
corr_mat <- vcv_mat / outer(d, d)

# Sanity check: diagonal should be 1 throughout
stopifnot(all(abs(diag(corr_mat) - 1) < 1e-10))
cat(sprintf("  Mean off-diagonal phylogenetic correlation: %.4f\n",
            (sum(corr_mat) - n) / (n * (n - 1))))

cat("\nComputing pESS for each lambda:\n")
lambdas <- c(0, 0.757618448344632, 1.0)
labels  <- c("OLS (lambda=0)", "Pagel ML (lambda=0.758)", "Brownian (lambda=1)")

results <- data.frame(
  lambda  = numeric(),
  label   = character(),
  n       = integer(),
  pESS    = numeric(),
  pESS_n  = numeric(),
  stringsAsFactors = FALSE
)

for (i in seq_along(lambdas)) {
  lam <- lambdas[i]
  C_lambda <- lam * corr_mat + (1 - lam) * diag(n)
  pess <- n^2 / sum(C_lambda)
  cat(sprintf("  %-30s  pESS = %6.1f  (pESS/n = %.4f)\n",
              labels[i], pess, pess / n))
  results <- rbind(results, data.frame(
    lambda = lam, label = labels[i], n = n,
    pESS = round(pess, 1), pESS_n = round(pess / n, 4)
  ))
}

out <- file.path(DATA, "pgls_pess.csv")
write.csv(results, out, row.names = FALSE)
cat(sprintf("\nSaved -> %s\n", out))
