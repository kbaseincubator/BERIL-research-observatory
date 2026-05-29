#!/usr/bin/env Rscript
# pagel_lambda.R  —  GTDB tree pruning + Pagel's λ analysis
#
# Usage:
#   Rscript scripts/pagel_lambda.R /path/to/data/dir
#
# Input files (in data_dir):
#   genus_trait_table.csv          — per-genus trait values (from NB04 Python cells)
#   genus_bac_reps.csv             — columns: genus_lower, accession  (bacterial reps)
#   genus_arc_reps.csv             — columns: genus_lower, accession  (archaeal reps)
#   gtdb_bac120_r214.tree          — raw GTDB bacterial species tree (newick)
#   gtdb_ar53_r214.tree            — raw GTDB archaeal species tree (newick)
#
# Output files (in data_dir):
#   gtdb_bac_genus_pruned.tree     — bacterial genus-level tree (tips = lowercase genus)
#   gtdb_arc_genus_pruned.tree     — archaeal genus-level tree
#   pagel_lambda_results.csv       — λ, logL, LRT statistic, p-value per analysis
#
# Required R packages: ape, phytools, geiger
#   install.packages(c('ape', 'phytools', 'geiger'))

suppressPackageStartupMessages({
    library(ape)
    library(phytools)
    library(geiger)
})

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], '.')
cat('\n=== Pagel lambda analysis ===\n')
cat(sprintf('Data dir: %s\n', data_dir))


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Prune GTDB trees to one tip per genus, relabel to genus names
# ─────────────────────────────────────────────────────────────────────────────
prune_to_genera <- function(tree_file, reps_file, output_file, domain_label) {
    cat(sprintf('\n--- Pruning %s tree ---\n', domain_label))
    if (!file.exists(tree_file)) {
        cat(sprintf('  SKIP: %s not found\n', tree_file)); return(FALSE)
    }
    if (!file.exists(reps_file)) {
        cat(sprintf('  SKIP: %s not found\n', reps_file)); return(FALSE)
    }

    cat(sprintf('  Loading %s ...\n', basename(tree_file)))
    tree <- read.tree(tree_file)
    cat(sprintf('  Tips in raw tree: %d\n', length(tree$tip.label)))

    reps <- read.csv(reps_file, stringsAsFactors = FALSE)
    cat(sprintf('  Requested genus reps: %d\n', nrow(reps)))

    # Filter to accessions that are actually in the tree
    reps <- reps[reps$accession %in% tree$tip.label, ]
    cat(sprintf('  Accessions found in tree: %d\n', nrow(reps)))

    if (nrow(reps) < 2) {
        cat('  ERROR: fewer than 2 matching accessions — skipping\n'); return(FALSE)
    }

    # Handle duplicate accessions (shouldn't happen, but be safe)
    reps <- reps[!duplicated(reps$accession), ]

    # Prune to representative accessions
    cat(sprintf('  Pruning to %d representatives ...\n', nrow(reps)))
    tree <- keep.tip(tree, reps$accession)

    # Relabel tips: accession → lowercase genus name
    label_map <- setNames(reps$genus_lower, reps$accession)
    tree$tip.label <- unname(label_map[tree$tip.label])

    # Check for any duplicated genus names after relabeling (shouldn't happen)
    dups <- duplicated(tree$tip.label)
    if (any(dups)) {
        cat(sprintf('  WARNING: %d duplicate genus labels — keeping first\n', sum(dups)))
        tree <- keep.tip(tree, tree$tip.label[!dups])
    }

    write.tree(tree, file = output_file)
    cat(sprintf('  Pruned tree saved: %s (%d tips)\n', basename(output_file), length(tree$tip.label)))
    return(TRUE)
}

prune_to_genera(
    tree_file   = file.path(data_dir, 'gtdb_bac120_r214.tree'),
    reps_file   = file.path(data_dir, 'genus_bac_reps.csv'),
    output_file = file.path(data_dir, 'gtdb_bac_genus_pruned.tree'),
    domain_label = 'Bacterial'
)

prune_to_genera(
    tree_file   = file.path(data_dir, 'gtdb_ar53_r214.tree'),
    reps_file   = file.path(data_dir, 'genus_arc_reps.csv'),
    output_file = file.path(data_dir, 'gtdb_arc_genus_pruned.tree'),
    domain_label = 'Archaeal'
)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Pagel's λ helpers
# ─────────────────────────────────────────────────────────────────────────────
run_lambda_continuous <- function(tree_file, traits, trait_col, label,
                                  min_otus = 3) {
    cat(sprintf('\n[%s] %s (continuous)\n', label, trait_col))
    if (!file.exists(tree_file)) {
        cat('  SKIP: tree file not found\n'); return(NULL)
    }
    tree <- tryCatch(
        read.tree(tree_file),
        error = function(e) { cat('  ERROR reading tree:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(tree)) return(NULL)
    cat(sprintf('  Tree tips: %d\n', length(tree$tip.label)))

    sub <- traits[traits$n_otus >= min_otus &
                  traits$genus_lower %in% tree$tip.label, ]
    cat(sprintf('  Genera matched (n_otus >= %d): %d\n', min_otus, nrow(sub)))
    if (nrow(sub) < 20) {
        cat('  SKIP: fewer than 20 matched genera\n'); return(NULL)
    }

    tree <- keep.tip(tree, sub$genus_lower)
    x    <- setNames(sub[[trait_col]], sub$genus_lower)
    x    <- x[!is.na(x)]
    tree <- keep.tip(tree, names(x))

    cat(sprintf('  Running phylosig on %d genera ...\n', length(x)))
    res <- tryCatch(
        phylosig(tree, x, method = 'lambda', test = TRUE),
        error = function(e) { cat('  ERROR in phylosig:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(res)) return(NULL)

    cat(sprintf('  lambda = %.4f   logL = %.2f   logL0 = %.2f   p = %.4g\n',
                res$lambda, res$logL, res$logL0, res$P))
    data.frame(
        label      = label,
        trait      = trait_col,
        trait_type = 'continuous',
        n_taxa     = length(x),
        lambda     = res$lambda,
        logL       = res$logL,
        logL0      = res$logL0,
        lrt_stat   = 2 * (res$logL - res$logL0),
        p_value    = res$P
    )
}


run_lambda_binary <- function(tree_file, traits, trait_col, label) {
    # Uses phylosig (phytools) treating 0/1 as numeric.
    # geiger::fitDiscrete with model='lambda' is not supported in geiger >= 2.0.
    cat(sprintf('\n[%s] %s (binary via phylosig)\n', label, trait_col))
    if (!file.exists(tree_file)) {
        cat('  SKIP: tree file not found\n'); return(NULL)
    }
    tree <- tryCatch(
        read.tree(tree_file),
        error = function(e) { cat('  ERROR reading tree:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(tree)) return(NULL)
    cat(sprintf('  Tree tips: %d\n', length(tree$tip.label)))

    sub <- traits[traits$genus_lower %in% tree$tip.label, ]
    n_pos <- sum(sub[[trait_col]] == 1, na.rm = TRUE)
    cat(sprintf('  Genera matched: %d  (positives: %d)\n', nrow(sub), n_pos))
    if (nrow(sub) < 20 || n_pos < 2) {
        cat('  SKIP: too few taxa or fewer than 2 positives\n'); return(NULL)
    }

    tree <- keep.tip(tree, sub$genus_lower)
    x    <- setNames(as.numeric(sub[[trait_col]]), sub$genus_lower)
    x    <- x[!is.na(x)]
    tree <- keep.tip(tree, names(x))

    cat(sprintf('  Running phylosig on %d genera ...\n', length(x)))
    res <- tryCatch(
        phylosig(tree, x, method = 'lambda', test = TRUE),
        error = function(e) { cat('  ERROR in phylosig:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(res)) return(NULL)

    lrt_stat <- 2 * (res$logL - res$logL0)
    cat(sprintf('  lambda = %.4f   logL = %.2f   logL0 = %.2f   p = %.4g\n',
                res$lambda, res$logL, res$logL0, res$P))
    data.frame(
        label      = label,
        trait      = trait_col,
        trait_type = 'binary_as_continuous',
        n_taxa     = length(x),
        lambda     = res$lambda,
        logL       = res$logL,
        logL0      = res$logL0,
        lrt_stat   = lrt_stat,
        p_value    = res$P
    )
}


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Load traits and run Pagel's λ
# ─────────────────────────────────────────────────────────────────────────────
trait_file <- file.path(data_dir, 'genus_trait_table.csv')
if (!file.exists(trait_file)) stop(sprintf('trait file not found: %s', trait_file))

traits <- read.csv(trait_file, stringsAsFactors = FALSE)
cat(sprintf('\nGenus trait table: %d genera\n', nrow(traits)))
cat(sprintf('  Nitrifier genera: %d\n', sum(traits$is_nitrifier == 1, na.rm = TRUE)))
has_amr <- 'mean_n_metal_amr_clusters' %in% colnames(traits)
cat(sprintf('  Metal AMR columns present: %s\n', if (has_amr) 'YES' else 'NO (run cell 5b in NB04)'))

bac_tree_file <- file.path(data_dir, 'gtdb_bac_genus_pruned.tree')
arc_tree_file <- file.path(data_dir, 'gtdb_arc_genus_pruned.tree')

cat('\n=== Running Pagel lambda analyses ===\n')
results <- list()

# 1. Levins' B_std (continuous) — bacterial genera with ≥3 OTUs
results[[1]] <- run_lambda_continuous(
    bac_tree_file, traits, 'mean_levins_B_std', 'Bacteria', min_otus = 3)

# 2. Levins' B_std (continuous) — archaeal genera (all: often few OTUs)
results[[2]] <- run_lambda_continuous(
    arc_tree_file, traits, 'mean_levins_B_std', 'Archaea', min_otus = 1)

# 3. n_envs_detected (continuous) — bacteria; complementary to B_std
results[[3]] <- run_lambda_continuous(
    bac_tree_file, traits, 'mean_n_envs', 'Bacteria', min_otus = 3)

# 4. n_envs_detected (continuous) — archaea
results[[4]] <- run_lambda_continuous(
    arc_tree_file, traits, 'mean_n_envs', 'Archaea', min_otus = 1)

# 5. is_nitrifier (binary) — bacterial tree (AOB + NOB)
results[[5]] <- run_lambda_binary(
    bac_tree_file, traits, 'is_nitrifier', 'Bacteria')

# 6. is_nitrifier (binary) — archaeal tree (AOA)
results[[6]] <- run_lambda_binary(
    arc_tree_file, traits, 'is_nitrifier', 'Archaea')

# 7–9. Metal AMR traits (continuous) — bacteria only; skip if columns missing
if (has_amr) {
    results[[7]] <- run_lambda_continuous(
        bac_tree_file, traits, 'mean_n_metal_amr_clusters', 'Bacteria', min_otus = 3)
    results[[8]] <- run_lambda_continuous(
        bac_tree_file, traits, 'mean_metal_core_fraction', 'Bacteria', min_otus = 3)
    results[[9]] <- run_lambda_continuous(
        bac_tree_file, traits, 'mean_n_metal_types', 'Bacteria', min_otus = 3)
    # Archaea: typically fewer AMR hits but worth checking
    results[[10]] <- run_lambda_continuous(
        arc_tree_file, traits, 'mean_n_metal_amr_clusters', 'Archaea', min_otus = 1)
} else {
    cat('\nSKIPPING metal AMR analyses — columns not found in trait table\n')
}


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Save results
# ─────────────────────────────────────────────────────────────────────────────
results <- do.call(rbind, Filter(Negate(is.null), results))

if (is.null(results) || nrow(results) == 0) {
    cat('\nWARNING: no results produced — check tree files and trait table\n')
    quit(status = 1)
}

out_file <- file.path(data_dir, 'pagel_lambda_results.csv')
write.csv(results, out_file, row.names = FALSE)
cat(sprintf('\nResults saved: %s\n', out_file))
cat('\nSummary:\n')
print(results[, c('label', 'trait', 'trait_type', 'n_taxa', 'lambda', 'p_value')])
