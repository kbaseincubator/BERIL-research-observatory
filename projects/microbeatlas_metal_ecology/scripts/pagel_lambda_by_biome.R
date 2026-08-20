#!/usr/bin/env Rscript
# pagel_lambda_by_biome.R  —  Pagel's lambda for a biome-specific genus subset
#
# Usage:
#   Rscript scripts/pagel_lambda_by_biome.R \
#       --data_dir  /path/to/data \
#       --genus_file /tmp/groundwater_genera.csv \
#       --biome     groundwater \
#       --out       /tmp/groundwater_lambda.csv
#
# Required columns in genus_file: genus_lower
# Required files in data_dir:
#   genus_trait_table.csv        — global per-genus traits
#   gtdb_bac_genus_pruned.tree   — pre-pruned bacterial genus tree (from pagel_lambda.R)
#   gtdb_arc_genus_pruned.tree   — pre-pruned archaeal genus tree
#
# Output CSV columns: biome, domain, trait, n_genera, lambda, logL, logL0, lrt_stat, p_value

suppressPackageStartupMessages({
    library(ape)
    library(phytools)
})

# ── Parse arguments ────────────────────────────────────────────────────────────
args <- commandArgs(trailingOnly = TRUE)
parse_arg <- function(flag, default = NULL) {
    idx <- which(args == flag)
    if (length(idx) == 0) return(default)
    if (idx + 1 > length(args)) stop(paste("Missing value after", flag))
    args[idx + 1]
}

data_dir   <- parse_arg('--data_dir',   '.')
genus_file <- parse_arg('--genus_file', NULL)
biome_name <- parse_arg('--biome',      'unknown')
out_file   <- parse_arg('--out',        NULL)

if (is.null(genus_file) || is.null(out_file)) {
    stop("Required: --genus_file and --out")
}

cat(sprintf('\n=== Pagel lambda (biome: %s) ===\n', biome_name))

# ── Load inputs ────────────────────────────────────────────────────────────────
traits     <- read.csv(file.path(data_dir, 'genus_trait_table.csv'), stringsAsFactors = FALSE)
biome_gen  <- read.csv(genus_file, stringsAsFactors = FALSE)

# Normalise genus names to lowercase
biome_gen$genus_lower <- tolower(trimws(biome_gen$genus_lower))
traits$genus_lower    <- tolower(trimws(traits$genus_lower))

cat(sprintf('  Biome genera supplied: %d\n', nrow(biome_gen)))
cat(sprintf('  Global trait table genera: %d\n', nrow(traits)))

# Filter trait table to biome genera
sub <- traits[traits$genus_lower %in% biome_gen$genus_lower, ]
cat(sprintf('  Biome genera in trait table: %d\n', nrow(sub)))

# ── Run lambda for each pruned tree ───────────────────────────────────────────
results <- list()

run_lambda <- function(tree_path, domain_label, trait_col = 'mean_n_metal_types') {
    if (!file.exists(tree_path)) {
        cat(sprintf('  SKIP %s: tree not found\n', domain_label)); return(NULL)
    }
    tree <- tryCatch(
        read.tree(tree_path),
        error = function(e) { cat('  ERROR reading tree:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(tree)) return(NULL)
    cat(sprintf('\n  [%s] Tree tips: %d\n', domain_label, length(tree$tip.label)))

    # Filter to genera in both the biome subset and the tree
    matched <- sub[sub$genus_lower %in% tree$tip.label, ]
    cat(sprintf('  [%s] Biome genera matched to tree: %d\n', domain_label, nrow(matched)))

    if (nrow(matched) < 20) {
        cat(sprintf('  [%s] SKIP: fewer than 20 genera\n', domain_label)); return(NULL)
    }

    tree_sub <- keep.tip(tree, matched$genus_lower)
    x        <- setNames(matched[[trait_col]], matched$genus_lower)
    x        <- x[!is.na(x)]
    tree_sub <- keep.tip(tree_sub, names(x))

    cat(sprintf('  [%s] Running phylosig on %d genera...\n', domain_label, length(x)))
    res <- tryCatch(
        phylosig(tree_sub, x, method = 'lambda', test = TRUE),
        error = function(e) { cat('  ERROR in phylosig:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(res)) return(NULL)

    cat(sprintf('  [%s] lambda=%.4f  logL=%.2f  logL0=%.2f  p=%.4g\n',
                domain_label, res$lambda, res$logL, res$logL0, res$P))

    data.frame(
        biome    = biome_name,
        domain   = domain_label,
        trait    = trait_col,
        n_genera = length(x),
        lambda   = res$lambda,
        logL     = res$logL,
        logL0    = res$logL0,
        lrt_stat = 2 * (res$logL - res$logL0),
        p_value  = res$P,
        stringsAsFactors = FALSE
    )
}

bac_tree <- file.path(data_dir, 'gtdb_bac_genus_pruned.tree')
arc_tree <- file.path(data_dir, 'gtdb_arc_genus_pruned.tree')

results[['bac']] <- run_lambda(bac_tree, 'Bacteria')
results[['arc']] <- run_lambda(arc_tree, 'Archaea')

out_df <- do.call(rbind, Filter(Negate(is.null), results))

if (is.null(out_df) || nrow(out_df) == 0) {
    cat('\n  No results produced (all domains skipped).\n')
    out_df <- data.frame(biome=biome_name, domain=NA, trait=NA, n_genera=0,
                         lambda=NA, logL=NA, logL0=NA, lrt_stat=NA, p_value=NA)
}

write.csv(out_df, out_file, row.names = FALSE)
cat(sprintf('\nSaved: %s\n', out_file))
