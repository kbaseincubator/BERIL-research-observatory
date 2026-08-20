#!/usr/bin/env Rscript
# taxonomic_tier_pgls.R
#
# Two questions:
#   1. Tier breakdown: do Tier 1 (defense/resistance) and Tier 2 (homeostasis)
#      differ in their PGLS association with niche breadth — raw and per-Mb?
#   2. Taxonomic drivers: which phyla, classes, orders drive the signal?
#      (a) Leave-one-phylum-out sensitivity
#      (b) Within-phylum PGLS for the five largest phyla
#      (c) Top-25 genera by metal diversity — ranked table
#
# Output:
#   data/pgls_results_tier_normalized.csv   — tier × predictor type
#   data/pgls_results_leave1phylum.csv      — LOPO sensitivity
#   data/pgls_results_within_phylum.csv     — per-phylum PGLS (≥40 genera)
#   data/top_genera_metal_diversity.csv     — ranked genus table

suppressPackageStartupMessages({ library(ape); library(nlme) })

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], 'data')

cat('\n=== Taxonomic-tier PGLS driver analysis ===\n\n')

# ─── 1. Load ──────────────────────────────────────────────────────────────────
tree   <- read.tree(file.path(data_dir, 'gtdb_bac_genus_pruned.tree'))
traits <- read.csv(file.path(data_dir, 'genus_trait_table.csv'), stringsAsFactors = FALSE)
gsz    <- read.csv(file.path(data_dir, 'genus_genome_size_gtdb.csv'), stringsAsFactors = FALSE)

cat(sprintf('Tree tips:      %d\n', length(tree$tip.label)))
cat(sprintf('Trait genera:   %d\n', nrow(traits)))
cat(sprintf('Genome genera:  %d\n', nrow(gsz)))

# ─── 2. Build base dataset ────────────────────────────────────────────────────
base <- merge(
    traits[, c('genus_lower', 'phylum', 'mean_levins_B_std',
               'mean_n_metal_types', 'n_otus',
               'mean_n_defense_clusters', 'mean_n_homeostasis_clusters')],
    gsz[, c('genus_lower', 'mean_genome_size_bp', 'mean_protein_count')],
    by = 'genus_lower', all.x = FALSE
)
base <- base[
    !is.na(base$mean_levins_B_std) &
    !is.na(base$mean_n_metal_types) &
    !is.na(base$mean_genome_size_bp) &
    base$n_otus >= 3 &
    base$genus_lower %in% tree$tip.label,
]

# Normalized predictors
base$defense_per_Mb    <- base$mean_n_defense_clusters     / (base$mean_genome_size_bp / 1e6)
base$homeostasis_per_Mb <- base$mean_n_homeostasis_clusters / (base$mean_genome_size_bp / 1e6)
base$metal_per_Mb      <- base$mean_n_metal_types           / (base$mean_genome_size_bp / 1e6)

base$defense_z         <- as.numeric(scale(base$mean_n_defense_clusters))
base$homeostasis_z     <- as.numeric(scale(base$mean_n_homeostasis_clusters))
base$metal_types_z     <- as.numeric(scale(base$mean_n_metal_types))
base$defense_per_Mb_z  <- as.numeric(scale(base$defense_per_Mb))
base$homeostasis_per_Mb_z <- as.numeric(scale(base$homeostasis_per_Mb))
base$metal_per_Mb_z    <- as.numeric(scale(base$metal_per_Mb))
base$metal_per_1k_z    <- as.numeric(scale(base$mean_n_metal_types * 1000 / base$mean_protein_count))

tree_s <- keep.tip(tree, base$genus_lower)
rownames(base) <- base$genus_lower
base <- base[tree_s$tip.label, ]

cat(sprintf('Analysis n:     %d genera\n', nrow(base)))

# ─── 3. PGLS helper ───────────────────────────────────────────────────────────
run_pgls <- function(d, t, formula_str, label, subset_name) {
    d <- d[d$genus_lower %in% t$tip.label, ]
    t <- keep.tip(t, d$genus_lower)
    rownames(d) <- d$genus_lower
    d <- d[t$tip.label, ]
    if (nrow(d) < 15) { cat(sprintf('  [skip] %s n=%d < 15\n', subset_name, nrow(d))); return(NULL) }

    cor_s <- tryCatch(corPagel(0.5, phy = t, fixed = FALSE), error = function(e) NULL)
    if (is.null(cor_s)) return(NULL)

    fit <- tryCatch(
        gls(as.formula(formula_str), data = d, correlation = cor_s, method = 'ML'),
        error = function(e) { cat(sprintf('  ERROR in %s: %s\n', label, conditionMessage(e))); NULL }
    )
    if (is.null(fit)) return(NULL)

    ct  <- coef(summary(fit))
    lam <- tryCatch(as.numeric(coef(fit$modelStruct$corStruct)), error = function(e) NA)
    pred_row <- ct[rownames(ct) != '(Intercept)', , drop = FALSE]
    if (nrow(pred_row) == 0) return(NULL)

    data.frame(
        subset    = subset_name,
        label     = label,
        n         = nrow(d),
        lambda    = lam,
        beta      = pred_row[1, 'Value'],
        SE        = pred_row[1, 'Std.Error'],
        t_stat    = pred_row[1, 't-value'],
        p_value   = pred_row[1, 'p-value'],
        stringsAsFactors = FALSE
    )
}

# ─── 4. Part 1 — Tier × predictor type ───────────────────────────────────────
cat('\n--- Part 1: Tier-stratified normalized PGLS ---\n')

tier_models <- list(
    list('mean_levins_B_std ~ defense_z',           'Tier1 raw'),
    list('mean_levins_B_std ~ homeostasis_z',        'Tier2 raw'),
    list('mean_levins_B_std ~ metal_types_z',        'Total raw'),
    list('mean_levins_B_std ~ defense_per_Mb_z',     'Tier1 per Mb'),
    list('mean_levins_B_std ~ homeostasis_per_Mb_z', 'Tier2 per Mb'),
    list('mean_levins_B_std ~ metal_per_Mb_z',       'Total per Mb'),
    list('mean_levins_B_std ~ metal_per_1k_z',       'Total per 1k genes')
)

tier_res <- do.call(rbind, Filter(Negate(is.null), lapply(tier_models, function(m) {
    run_pgls(base, tree_s, m[[1]], m[[2]], 'all_genera')
})))

cat(sprintf('\n%-30s  %5s  %8s  %8s  %9s\n', 'Model', 'n', 'beta', 'SE', 'p-value'))
cat(strrep('-', 65), '\n')
for (i in seq_len(nrow(tier_res))) {
    r <- tier_res[i, ]
    sig <- if (!is.na(r$p_value) && r$p_value < 0.05) '*' else ' '
    cat(sprintf('%-30s  %5d  %8.5f  %8.5f  %9.4g%s\n',
                r$label, r$n, r$beta, r$SE, r$p_value, sig))
}

# ─── 5. Part 2a — Leave-one-phylum-out ───────────────────────────────────────
cat('\n--- Part 2a: Leave-one-phylum-out (metal_types_z ~ niche breadth) ---\n')

phyla <- sort(unique(base$phylum[!is.na(base$phylum) & base$phylum != '']))
lopo_res <- do.call(rbind, Filter(Negate(is.null), lapply(phyla, function(p) {
    d_sub <- base[base$phylum != p, ]
    r <- run_pgls(d_sub, tree_s, 'mean_levins_B_std ~ metal_types_z',
                  'metal_types_z', paste0('drop_', gsub(' ', '_', p)))
    if (!is.null(r)) { r$phylum_dropped <- p; r$n_dropped <- sum(base$phylum == p, na.rm=TRUE) }
    r
})))

cat(sprintf('\n%-35s  %5s  %5s  %8s  %9s\n', 'Phylum dropped', 'n', 'n_drop', 'beta', 'p-value'))
cat(strrep('-', 70), '\n')
lopo_sorted <- lopo_res[order(lopo_res$p_value), ]
for (i in seq_len(nrow(lopo_sorted))) {
    r <- lopo_sorted[i, ]
    sig <- if (!is.na(r$p_value) && r$p_value < 0.05) '*' else ' '
    cat(sprintf('%-35s  %5d  %5d  %8.5f  %9.4g%s\n',
                r$phylum_dropped, r$n, r$n_dropped, r$beta, r$p_value, sig))
}

# ─── 6. Part 2b — Within-phylum PGLS ─────────────────────────────────────────
cat('\n--- Part 2b: Within-phylum PGLS (phyla with ≥40 genera) ---\n')

phylum_counts <- table(base$phylum)
large_phyla <- names(phylum_counts[phylum_counts >= 40])
cat(sprintf('Phyla with ≥40 genera: %s\n', paste(large_phyla, collapse=', ')))

within_models <- list(
    list('mean_levins_B_std ~ metal_types_z',   'Total raw'),
    list('mean_levins_B_std ~ metal_per_Mb_z',  'Total per Mb')
)

within_res <- do.call(rbind, Filter(Negate(is.null), lapply(large_phyla, function(p) {
    d_sub <- base[!is.na(base$phylum) & base$phylum == p, ]
    do.call(rbind, Filter(Negate(is.null), lapply(within_models, function(m) {
        r <- run_pgls(d_sub, tree_s, m[[1]], m[[2]], p)
        if (!is.null(r)) { r$phylum <- p }
        r
    })))
})))

if (!is.null(within_res) && nrow(within_res) > 0) {
    cat(sprintf('\n%-25s  %-20s  %5s  %8s  %9s\n', 'Phylum', 'Model', 'n', 'beta', 'p-value'))
    cat(strrep('-', 75), '\n')
    for (i in seq_len(nrow(within_res))) {
        r <- within_res[i, ]
        sig <- if (!is.na(r$p_value) && r$p_value < 0.05) '*' else ' '
        cat(sprintf('%-25s  %-20s  %5d  %8.5f  %9.4g%s\n',
                    r$phylum, r$label, r$n, r$beta, r$p_value, sig))
    }
}

# ─── 7. Part 3 — Top genera ranking ──────────────────────────────────────────
cat('\n--- Part 3: Top 25 genera by metal type diversity ---\n')

top_g <- base[order(-base$mean_n_metal_types), ][1:min(25, nrow(base)), ]
top_g$metal_per_Mb_display <- round(top_g$metal_per_Mb, 3)
top_out <- top_g[, c('genus_lower', 'phylum', 'mean_n_metal_types',
                     'metal_per_Mb_display', 'mean_levins_B_std',
                     'mean_n_defense_clusters', 'mean_n_homeostasis_clusters')]
colnames(top_out) <- c('genus', 'phylum', 'metal_types', 'metal_per_Mb',
                       'levins_B_std', 'defense_clusters', 'homeostasis_clusters')

cat(sprintf('\n%-25s  %-20s  %11s  %11s  %12s  %8s  %11s\n',
            'Genus', 'Phylum', 'metal_types', 'metal_per_Mb', 'levins_B_std',
            'defense', 'homeostasis'))
cat(strrep('-', 105), '\n')
for (i in seq_len(nrow(top_out))) {
    r <- top_out[i, ]
    cat(sprintf('%-25s  %-20s  %11.1f  %11.3f  %12.4f  %8.1f  %11.1f\n',
                r$genus, r$phylum, r$metal_types, r$metal_per_Mb,
                r$levins_B_std, r$defense_clusters, r$homeostasis_clusters))
}

cat('\n--- Bottom 10 genera by metal diversity (ecological context) ---\n')
bot_g <- base[order(base$mean_n_metal_types), ][1:10, ]
cat(sprintf('%-25s  %-20s  %11s  %12s\n', 'Genus', 'Phylum', 'metal_types', 'levins_B_std'))
cat(strrep('-', 75), '\n')
for (i in seq_len(nrow(bot_g))) {
    r <- bot_g[i, ]
    cat(sprintf('%-25s  %-20s  %11.1f  %12.4f\n',
                r$genus_lower, r$phylum, r$mean_n_metal_types, r$mean_levins_B_std))
}

# ─── 8. Save ─────────────────────────────────────────────────────────────────
write.csv(tier_res,    file.path(data_dir, 'pgls_results_tier_normalized.csv'),  row.names = FALSE)
cat(sprintf('\nSaved: %s\n', file.path(data_dir, 'pgls_results_tier_normalized.csv')))

if (!is.null(lopo_res) && nrow(lopo_res) > 0) {
    write.csv(lopo_res, file.path(data_dir, 'pgls_results_leave1phylum.csv'), row.names = FALSE)
    cat(sprintf('Saved: %s\n', file.path(data_dir, 'pgls_results_leave1phylum.csv')))
}

if (!is.null(within_res) && nrow(within_res) > 0) {
    write.csv(within_res, file.path(data_dir, 'pgls_results_within_phylum.csv'), row.names = FALSE)
    cat(sprintf('Saved: %s\n', file.path(data_dir, 'pgls_results_within_phylum.csv')))
}

write.csv(top_out, file.path(data_dir, 'top_genera_metal_diversity.csv'), row.names = FALSE)
cat(sprintf('Saved: %s\n', file.path(data_dir, 'top_genera_metal_diversity.csv')))

cat('\nDone.\n')
