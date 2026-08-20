#!/usr/bin/env Rscript
# discriminant_genomesize_pgls.R
#
# Tests whether the discriminant (19-KO sensing/cofactor) PGLS signal survives
# genome-size control — the key test of whether the result is a genome-complexity proxy.
#
# Runs 4 models on the SAME matched subset (~400-500 genera):
#   1. B_std ~ disc_types_z             (discriminant, no genome-size control)
#   2. B_std ~ disc_types_z + genome_z  (discriminant + genome size)
#   3. B_std ~ metal_types_z            (94-KO, same subset)
#   4. B_std ~ metal_types_z + genome_z (94-KO + genome size)
#
# Input:
#   data/genus_discriminant_metal.csv  — 7,976 genera; mean_n_disc_metal_types
#   data/genus_genome_size.csv         — 527 genera; mean_genome_size_bp
#   data/genus_trait_table.csv         — 3,160 genera; mean_levins_B_std, n_otus, mean_n_metal_types
#   data/gtdb_bac_genus_pruned.tree
#
# Output:
#   data/pgls_results_discriminant_genomesize.csv

suppressPackageStartupMessages({
    library(ape)
    library(nlme)
})

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], 'data')
cat('\n=== Genome-size Controlled Discriminant PGLS ===\n')
cat(sprintf('Data dir: %s\n\n', data_dir))

# ─── 1. Load data ─────────────────────────────────────────────────────────────
tree   <- read.tree(file.path(data_dir, 'gtdb_bac_genus_pruned.tree'))
traits <- read.csv(file.path(data_dir, 'genus_trait_table.csv'),         stringsAsFactors = FALSE)
disc   <- read.csv(file.path(data_dir, 'genus_discriminant_metal.csv'),  stringsAsFactors = FALSE)
gsz    <- read.csv(file.path(data_dir, 'genus_genome_size.csv'),         stringsAsFactors = FALSE)

cat(sprintf('Tree:             %d tips\n', length(tree$tip.label)))
cat(sprintf('Trait table:      %d genera\n', nrow(traits)))
cat(sprintf('Discriminant:     %d genera\n', nrow(disc)))
cat(sprintf('Genome size:      %d genera\n', nrow(gsz)))

# ─── 2. Merge ─────────────────────────────────────────────────────────────────
# Join traits (niche breadth + 94-KO) with discriminant and genome size
m <- merge(
    traits[, c('genus_lower', 'mean_levins_B_std', 'mean_n_metal_types', 'n_otus')],
    disc[,   c('genus_lower', 'mean_n_disc_metal_types')],
    by = 'genus_lower', all.x = FALSE
)
m <- merge(m, gsz[, c('genus_lower', 'mean_genome_size_bp')], by = 'genus_lower', all.x = FALSE)

# Fill discriminant NAs with 0 (genera not in discriminant set had zero genes)
m$mean_n_disc_metal_types[is.na(m$mean_n_disc_metal_types)] <- 0

# ─── 3. Filter to PGLS-eligible genera ────────────────────────────────────────
sub <- m[
    m$n_otus >= 3 &
    m$genus_lower %in% tree$tip.label &
    !is.na(m$mean_levins_B_std) &
    !is.na(m$mean_n_metal_types) &
    !is.na(m$mean_genome_size_bp),
]
cat(sprintf('\nMatched subset: %d genera (n_otus≥3, in tree, all variables present)\n', nrow(sub)))

# Z-score predictors
sub$disc_types_z   <- as.numeric(scale(sub$mean_n_disc_metal_types))
sub$metal_types_z  <- as.numeric(scale(sub$mean_n_metal_types))
sub$genome_z       <- as.numeric(scale(log(sub$mean_genome_size_bp)))

# Align rows to tree order
tree_sub <- keep.tip(tree, sub$genus_lower)
rownames(sub) <- sub$genus_lower
sub <- sub[tree_sub$tip.label, ]
cat(sprintf('Pruned tree:    %d tips\n\n', length(tree_sub$tip.label)))

# ─── 4. PGLS helper ───────────────────────────────────────────────────────────
pgls_one <- function(formula_str, label) {
    cor_s <- tryCatch(
        corPagel(0.5, phy = tree_sub, fixed = FALSE),
        error = function(e) { cat('  ERROR corPagel:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(cor_s)) return(NULL)
    fit <- tryCatch(
        gls(as.formula(formula_str), data = sub, correlation = cor_s, method = 'ML'),
        error = function(e) { cat('  ERROR gls:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(fit)) return(NULL)

    s      <- summary(fit)
    ct     <- coef(s)
    lam    <- as.numeric(coef(fit$modelStruct$corStruct))

    cat(sprintf('[%s]\n', label))
    cat(sprintf('  lambda=%.4f  n=%d\n', lam, nrow(sub)))
    for (i in seq_len(nrow(ct))) {
        cat(sprintf('  %-22s  beta=%.5f  SE=%.5f  p=%.4g\n',
                    rownames(ct)[i], ct[i, 'Value'], ct[i, 'Std.Error'], ct[i, 'p-value']))
    }

    # Collect one row per predictor (skip intercept)
    rows <- lapply(seq_len(nrow(ct)), function(i) {
        data.frame(
            label     = label,
            predictor = rownames(ct)[i],
            n         = nrow(sub),
            lambda    = lam,
            beta      = ct[i, 'Value'],
            SE        = ct[i, 'Std.Error'],
            t_stat    = ct[i, 't-value'],
            p_value   = ct[i, 'p-value'],
            stringsAsFactors = FALSE
        )
    })
    do.call(rbind, rows)
}

# ─── 5. Run four models ────────────────────────────────────────────────────────
cat('=== Running 4 models on matched n ===\n\n')
r1 <- pgls_one('mean_levins_B_std ~ disc_types_z',                  'Discriminant (no genome ctrl)')
cat('\n')
r2 <- pgls_one('mean_levins_B_std ~ disc_types_z + genome_z',       'Discriminant + log(genome size)')
cat('\n')
r3 <- pgls_one('mean_levins_B_std ~ metal_types_z',                 '94-KO (no genome ctrl)')
cat('\n')
r4 <- pgls_one('mean_levins_B_std ~ metal_types_z + genome_z',      '94-KO + log(genome size)')
cat('\n')

results <- do.call(rbind, Filter(Negate(is.null), list(r1, r2, r3, r4)))

# ─── 6. Print summary ─────────────────────────────────────────────────────────
cat('\n=== SUMMARY (predictor rows only) ===\n')
pred_rows <- results[results$predictor != '(Intercept)', ]
cat(sprintf('%-38s  %-20s  %8s  %8s  %8s\n', 'Model', 'Predictor', 'beta', 'SE', 'p-value'))
cat(strrep('-', 90), '\n')
for (i in seq_len(nrow(pred_rows))) {
    r <- pred_rows[i, ]
    sig <- if (!is.na(r$p_value) && r$p_value < 0.05) '*' else ' '
    cat(sprintf('%-38s  %-20s  %8.5f  %8.5f  %8.4g%s\n',
                r$label, r$predictor, r$beta, r$SE, r$p_value, sig))
}

# ─── 7. Interpretation ────────────────────────────────────────────────────────
disc_ctrl  <- pred_rows[pred_rows$label == 'Discriminant (no genome ctrl)' &
                         pred_rows$predictor == 'disc_types_z', ]
disc_gs    <- pred_rows[pred_rows$label == 'Discriminant + log(genome size)' &
                         pred_rows$predictor == 'disc_types_z', ]
ko94_ctrl  <- pred_rows[pred_rows$label == '94-KO (no genome ctrl)' &
                         pred_rows$predictor == 'metal_types_z', ]
ko94_gs    <- pred_rows[pred_rows$label == '94-KO + log(genome size)' &
                         pred_rows$predictor == 'metal_types_z', ]

cat('\n=== INTERPRETATION ===\n')
if (nrow(disc_gs) > 0 && nrow(ko94_gs) > 0) {
    disc_survives <- disc_gs$p_value < 0.05
    ko94_survives <- ko94_gs$p_value < 0.05
    cat(sprintf('Discriminant + genome size: beta=%.5f  p=%.4g  %s\n',
                disc_gs$beta, disc_gs$p_value, if (disc_survives) 'SURVIVES' else 'ATTENUATED'))
    cat(sprintf('94-KO + genome size:        beta=%.5f  p=%.4g  %s\n',
                ko94_gs$beta, ko94_gs$p_value, if (ko94_survives) 'SURVIVES' else 'ATTENUATED'))

    if (disc_survives && ko94_survives) {
        cat('\nCONCLUSION: Both signals survive genome-size control.\n')
        cat('The niche breadth association is NOT a genome-complexity proxy.\n')
        cat('Metal-interacting gene diversity predicts niche breadth independently of genome size.\n')
    } else if (!disc_survives && ko94_survives) {
        cat('\nCONCLUSION: Discriminant attenuated; 94-KO survives.\n')
        cat('The sensing/cofactor signal may be driven by genome size;\n')
        cat('the 94-KO (resistance) signal is more specific.\n')
    } else if (!disc_survives && !ko94_survives) {
        cat('\nCONCLUSION: Both attenuated — genome size is a major confound.\n')
        cat('Metal-interacting gene counts are a proxy for genome complexity.\n')
        cat('Major reframe required before submission.\n')
    } else {
        cat('\nCONCLUSION: Discriminant survives; 94-KO attenuated.\n')
        cat('Sensing/cofactor gene diversity is not genome-size driven;\n')
        cat('the 94-KO result may partially reflect genome size.\n')
    }
}

# ─── 8. Save ──────────────────────────────────────────────────────────────────
out_file <- file.path(data_dir, 'pgls_results_discriminant_genomesize.csv')
write.csv(results, out_file, row.names = FALSE)
cat(sprintf('\nSaved: %s\n', out_file))
