#!/usr/bin/env Rscript
# taxonomic_rank_pgls.R
#
# Within-group PGLS at class, order, and family level.
# For each group with ≥20 genera, runs:
#   (a) Total raw predictor (metal_types_z)
#   (b) Total per-Mb predictor (metal_per_Mb_z)
#   (c) Tier 2 per-Mb predictor (homeostasis_per_Mb_z)
#
# Also prints top-genus breakdown within the most interesting groups.

suppressPackageStartupMessages({ library(ape); library(nlme) })

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], 'data')

cat('\n=== Taxonomic rank PGLS (class / order / family) ===\n\n')

# ─── 1. Load ──────────────────────────────────────────────────────────────────
tree   <- read.tree(file.path(data_dir, 'gtdb_bac_genus_pruned.tree'))
traits <- read.csv(file.path(data_dir, 'genus_trait_table.csv'), stringsAsFactors = FALSE)
gsz    <- read.csv(file.path(data_dir, 'genus_genome_size_gtdb.csv'), stringsAsFactors = FALSE)
taxon  <- read.csv(file.path(data_dir, 'gtdb_bac120_taxonomy_parsed.csv'), stringsAsFactors = FALSE)

cat(sprintf('Taxonomy file:  %d genome records, %d unique genera\n',
            nrow(taxon), length(unique(taxon$gtdb_genus))))

# ─── 2. Build genus-level taxonomy lookup ─────────────────────────────────────
# Most genera have one class/order/family; use the most common assignment.
genus_taxon <- do.call(rbind, lapply(split(taxon, taxon$gtdb_genus), function(g) {
    mode_val <- function(x) names(sort(table(x), decreasing = TRUE))[1]
    data.frame(
        genus_lower  = tolower(g$gtdb_genus[1]),
        gtdb_class   = mode_val(g$gtdb_class),
        gtdb_order   = mode_val(g$gtdb_order),
        gtdb_family  = mode_val(g$gtdb_family),
        stringsAsFactors = FALSE
    )
}))
cat(sprintf('Genus-level taxonomy: %d genera\n', nrow(genus_taxon)))

# ─── 3. Build analysis dataset ────────────────────────────────────────────────
base <- merge(
    traits[, c('genus_lower', 'phylum', 'mean_levins_B_std',
               'mean_n_metal_types', 'n_otus',
               'mean_n_defense_clusters', 'mean_n_homeostasis_clusters')],
    gsz[, c('genus_lower', 'mean_genome_size_bp', 'mean_protein_count')],
    by = 'genus_lower', all.x = FALSE
)
base <- merge(base, genus_taxon, by = 'genus_lower', all.x = TRUE)
base <- base[
    !is.na(base$mean_levins_B_std) &
    !is.na(base$mean_n_metal_types) &
    !is.na(base$mean_genome_size_bp) &
    base$n_otus >= 3 &
    base$genus_lower %in% tree$tip.label,
]

base$metal_per_Mb          <- base$mean_n_metal_types         / (base$mean_genome_size_bp / 1e6)
base$homeostasis_per_Mb    <- base$mean_n_homeostasis_clusters / (base$mean_genome_size_bp / 1e6)
base$defense_per_Mb        <- base$mean_n_defense_clusters     / (base$mean_genome_size_bp / 1e6)
base$metal_types_z         <- as.numeric(scale(base$mean_n_metal_types))
base$metal_per_Mb_z        <- as.numeric(scale(base$metal_per_Mb))
base$homeostasis_per_Mb_z  <- as.numeric(scale(base$homeostasis_per_Mb))
base$defense_per_Mb_z      <- as.numeric(scale(base$defense_per_Mb))

tree_s <- keep.tip(tree, base$genus_lower)
rownames(base) <- base$genus_lower
base <- base[tree_s$tip.label, ]
cat(sprintf('Analysis n:     %d genera\n\n', nrow(base)))

# ─── 4. PGLS helper ───────────────────────────────────────────────────────────
run_pgls <- function(d, t, formula_str, label, group_name) {
    d   <- d[d$genus_lower %in% t$tip.label, ]
    t   <- keep.tip(t, d$genus_lower)
    rownames(d) <- d$genus_lower
    d   <- d[t$tip.label, ]
    if (nrow(d) < 10) return(NULL)

    cor_s <- tryCatch(corPagel(0.5, phy = t, fixed = FALSE), error = function(e) NULL)
    if (is.null(cor_s)) return(NULL)
    fit <- tryCatch(
        gls(as.formula(formula_str), data = d, correlation = cor_s, method = 'ML'),
        error = function(e) NULL
    )
    if (is.null(fit)) return(NULL)

    ct   <- coef(summary(fit))
    lam  <- tryCatch(as.numeric(coef(fit$modelStruct$corStruct)), error = function(e) NA)
    pred <- ct[rownames(ct) != '(Intercept)', , drop = FALSE]
    if (nrow(pred) == 0) return(NULL)

    data.frame(
        group     = group_name,
        model     = label,
        n         = nrow(d),
        lambda    = round(lam, 3),
        beta      = pred[1, 'Value'],
        SE        = pred[1, 'Std.Error'],
        p_value   = pred[1, 'p-value'],
        stringsAsFactors = FALSE
    )
}

# ─── 5. Within-group analysis at each rank ────────────────────────────────────
run_rank <- function(rank_col, rank_name, min_n = 20) {
    cat(sprintf('\n======= %s level (≥%d genera) =======\n', rank_name, min_n))
    groups <- names(which(table(base[[rank_col]]) >= min_n))
    groups <- groups[groups != '' & !is.na(groups)]
    cat(sprintf('%d groups qualify\n\n', length(groups)))

    models <- list(
        list('mean_levins_B_std ~ metal_types_z',        'raw'),
        list('mean_levins_B_std ~ metal_per_Mb_z',       'per_Mb'),
        list('mean_levins_B_std ~ homeostasis_per_Mb_z', 'homeo_per_Mb')
    )

    res <- do.call(rbind, Filter(Negate(is.null), lapply(groups, function(g) {
        d_sub <- base[!is.na(base[[rank_col]]) & base[[rank_col]] == g, ]
        do.call(rbind, Filter(Negate(is.null), lapply(models, function(m) {
            r <- run_pgls(d_sub, tree_s, m[[1]], m[[2]], g)
            r
        })))
    })))
    if (is.null(res) || nrow(res) == 0) { cat('No results.\n'); return(invisible(NULL)) }

    # Print pivot: one row per group, three beta/p columns
    res_raw   <- res[res$model == 'raw',           ]
    res_mb    <- res[res$model == 'per_Mb',        ]
    res_hmb   <- res[res$model == 'homeo_per_Mb',  ]

    # Pivot: merge model results; use all.x=TRUE so missing models produce NAs
    m <- merge(
        res_raw[,  c('group','n','beta','p_value')],
        res_mb[,   c('group','beta','p_value')],
        by = 'group', suffixes = c('_raw','_mb'), all.x = TRUE
    )
    m <- merge(
        m,
        res_hmb[, c('group','beta','p_value')],
        by = 'group', all.x = TRUE
    )
    names(m)[names(m) == 'beta']    <- 'beta_hmb'
    names(m)[names(m) == 'p_value'] <- 'p_hmb'
    m <- m[order(ifelse(is.na(m$p_value_mb), 1, m$p_value_mb)), ]

    cat(sprintf('%-35s  %4s  %7s %6s  %7s %6s  %7s %6s\n',
                rank_name, 'n', 'raw_β', 'p', 'Mb_β', 'p', 'hmb_β', 'p'))
    cat(strrep('-', 95), '\n')
    for (i in seq_len(nrow(m))) {
        r <- m[i, ]
        sig_r <- if (!is.na(r$p_value_raw) && r$p_value_raw < 0.05) '*' else ' '
        sig_m <- if (!is.na(r$p_value_mb)  && r$p_value_mb  < 0.05) '*' else ' '
        sig_h <- if (!is.na(r$p_hmb)       && r$p_hmb       < 0.05) '*' else ' '
        cat(sprintf('%-35s  %4d  %7.4f%s %6.4f  %7.4f%s %6.4f  %7.4f%s %6.4f\n',
                    r$group, r$n,
                    r$beta_raw, sig_r, r$p_value_raw,
                    r$beta_mb,  sig_m, r$p_value_mb,
                    r$beta_hmb, sig_h, r$p_hmb))
    }
    invisible(res)
}

res_class  <- run_rank('gtdb_class',  'Class',  min_n = 20)
res_order  <- run_rank('gtdb_order',  'Order',  min_n = 20)
res_family <- run_rank('gtdb_family', 'Family', min_n = 10)

# ─── 6. Spotlight: top-genera within most informative groups ──────────────────
cat('\n======= Spotlight: top-5 genera by metal_per_Mb within key groups =======\n')

spotlight <- c('Gammaproteobacteria', 'Alphaproteobacteria', 'Bacilli',
               'Actinomycetia', 'Betaproteobacteria')
for (g in spotlight) {
    sub <- base[!is.na(base$gtdb_class) & base$gtdb_class == g, ]
    if (nrow(sub) == 0) next
    sub <- sub[order(-sub$metal_per_Mb), ]
    cat(sprintf('\n%s (n=%d) — top 5 by metal density:\n', g, nrow(sub)))
    cat(sprintf('  %-25s  %10s  %10s  %10s  %10s\n',
                'genus', 'metal_types', 'metal/Mb', 'B_std', 'homeo/Mb'))
    top <- head(sub, 5)
    for (i in seq_len(nrow(top))) {
        r <- top[i, ]
        cat(sprintf('  %-25s  %10.1f  %10.3f  %10.4f  %10.3f\n',
                    r$genus_lower, r$mean_n_metal_types,
                    r$metal_per_Mb, r$mean_levins_B_std, r$homeostasis_per_Mb))
    }
    cat(sprintf('  [correlation metal/Mb ~ B_std: r=%.3f]\n',
                cor(sub$metal_per_Mb, sub$mean_levins_B_std, use='complete.obs')))
}

# ─── 7. Save ─────────────────────────────────────────────────────────────────
all_res <- rbind(
    if (!is.null(res_class))  cbind(rank='class',  res_class)  else NULL,
    if (!is.null(res_order))  cbind(rank='order',  res_order)  else NULL,
    if (!is.null(res_family)) cbind(rank='family', res_family) else NULL
)
if (!is.null(all_res)) {
    write.csv(all_res, file.path(data_dir, 'pgls_results_by_rank.csv'), row.names = FALSE)
    cat(sprintf('\nSaved: %s\n', file.path(data_dir, 'pgls_results_by_rank.csv')))
}
cat('Done.\n')
