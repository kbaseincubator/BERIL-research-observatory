#!/usr/bin/env Rscript
# normalized_pgls.R — PGLS with genome-size normalized metal gene metrics
#
# Tests whether normalizing metal type diversity by genome size (per Mb)
# or gene count (per 1k genes) reveals a signal independent of genome complexity.
#
# Predictors tested:
#   raw:           mean_n_metal_types (z-scored)
#   per_Mb:        metal types per megabase of genome
#   per_1k_genes:  metal types per 1,000 predicted proteins
#   disc_raw:      mean_n_disc_metal_types (discriminant, z-scored)
#   disc_per_Mb:   discriminant types per Mb
#
# Two subsets:
#   n_orig  — original n=523 (genus_genome_size.csv); for direct comparison with Block B
#   n_gtdb  — extended n from gtdb_metadata (genus_genome_size_gtdb.csv); ~700+ genera
#
# Output: data/pgls_results_normalized.csv

suppressPackageStartupMessages({ library(ape); library(nlme) })

args     <- commandArgs(trailingOnly = TRUE)
data_dir <- ifelse(length(args) >= 1, args[1], 'data')
cat('\n=== Normalized Predictor PGLS ===\n\n')

# ─── 1. Load ──────────────────────────────────────────────────────────────────
tree   <- read.tree(file.path(data_dir, 'gtdb_bac_genus_pruned.tree'))
traits <- read.csv(file.path(data_dir, 'genus_trait_table.csv'),         stringsAsFactors = FALSE)
disc   <- read.csv(file.path(data_dir, 'genus_discriminant_metal.csv'),  stringsAsFactors = FALSE)
gsz_orig <- read.csv(file.path(data_dir, 'genus_genome_size.csv'),       stringsAsFactors = FALSE)
gsz_gtdb <- read.csv(file.path(data_dir, 'genus_genome_size_gtdb.csv'),  stringsAsFactors = FALSE)

cat(sprintf('Tree:              %d tips\n', length(tree$tip.label)))
cat(sprintf('Trait table:       %d genera\n', nrow(traits)))
cat(sprintf('Discriminant:      %d genera\n', nrow(disc)))
cat(sprintf('Genome size orig:  %d genera\n', nrow(gsz_orig)))
cat(sprintf('Genome size GTDB:  %d genera\n', nrow(gsz_gtdb)))

# ─── 2. Build base dataset ────────────────────────────────────────────────────
base <- merge(
    traits[, c('genus_lower', 'mean_levins_B_std', 'mean_n_metal_types', 'n_otus')],
    disc[,   c('genus_lower', 'mean_n_disc_metal_types')],
    by = 'genus_lower', all.x = FALSE
)
base$mean_n_disc_metal_types[is.na(base$mean_n_disc_metal_types)] <- 0

# ─── 3. Helper: build PGLS subset ─────────────────────────────────────────────
make_subset <- function(gsz, label_prefix) {
    # Merge genome size source
    has_prot  <- 'mean_protein_count' %in% names(gsz)
    gsz_cols  <- c('genus_lower', 'mean_genome_size_bp',
                   if (has_prot) 'mean_protein_count')
    m <- merge(base, gsz[, gsz_cols], by = 'genus_lower', all.x = FALSE)
    m <- m[
        m$n_otus >= 3 &
        m$genus_lower %in% tree$tip.label &
        !is.na(m$mean_levins_B_std) &
        !is.na(m$mean_n_metal_types) &
        !is.na(m$mean_genome_size_bp),
    ]

    # Normalized predictors
    m$metal_per_Mb         <- m$mean_n_metal_types     / (m$mean_genome_size_bp / 1e6)
    m$disc_per_Mb          <- m$mean_n_disc_metal_types / (m$mean_genome_size_bp / 1e6)
    m$log_genome_z         <- as.numeric(scale(log(m$mean_genome_size_bp)))
    m$metal_types_z        <- as.numeric(scale(m$mean_n_metal_types))
    m$disc_types_z         <- as.numeric(scale(m$mean_n_disc_metal_types))
    m$metal_per_Mb_z       <- as.numeric(scale(m$metal_per_Mb))
    m$disc_per_Mb_z        <- as.numeric(scale(m$disc_per_Mb))

    if (has_prot) {
        m$metal_per_1k_z   <- as.numeric(scale(m$mean_n_metal_types * 1000 / m$mean_protein_count))
        m$disc_per_1k_z    <- as.numeric(scale(m$mean_n_disc_metal_types * 1000 / m$mean_protein_count))
    }

    tree_s <- keep.tip(tree, m$genus_lower)
    rownames(m) <- m$genus_lower
    m <- m[tree_s$tip.label, ]
    cat(sprintf('\n[%s] n=%d genera\n', label_prefix, nrow(m)))
    list(data = m, tree = tree_s, label = label_prefix, has_prot = has_prot)
}

orig <- make_subset(gsz_orig, 'orig')   # n~523 for direct comparison with Block B
gtdb <- make_subset(gsz_gtdb, 'gtdb')   # n~700+ extended from GTDB metadata

# ─── 4. PGLS helper ───────────────────────────────────────────────────────────
pgls_one <- function(formula_str, label, sub_list) {
    d <- sub_list$data
    t <- sub_list$tree
    cor_s <- tryCatch(
        corPagel(0.5, phy = t, fixed = FALSE),
        error = function(e) NULL
    )
    if (is.null(cor_s)) return(NULL)
    fit <- tryCatch(
        gls(as.formula(formula_str), data = d, correlation = cor_s, method = 'ML'),
        error = function(e) { cat('  ERROR:', conditionMessage(e), '\n'); NULL }
    )
    if (is.null(fit)) return(NULL)

    s   <- summary(fit)
    ct  <- coef(s)
    lam <- as.numeric(coef(fit$modelStruct$corStruct))
    n   <- nrow(d)

    rows <- lapply(seq_len(nrow(ct)), function(i) {
        data.frame(
            subset    = sub_list$label,
            label     = label,
            predictor = rownames(ct)[i],
            n         = n,
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

# ─── 5. Run models ────────────────────────────────────────────────────────────
cat('\n=== Running normalized PGLS models ===\n')

run_all <- function(sub) {
    hp <- sub$has_prot
    models <- list(
        list('mean_levins_B_std ~ metal_types_z',   '94-KO raw (z-scored)'),
        list('mean_levins_B_std ~ metal_per_Mb_z',  '94-KO per Mb (z-scored)'),
        list('mean_levins_B_std ~ disc_types_z',    'Disc raw (z-scored)'),
        list('mean_levins_B_std ~ disc_per_Mb_z',   'Disc per Mb (z-scored)')
    )
    if (hp) {
        models <- c(models, list(
            list('mean_levins_B_std ~ metal_per_1k_z', '94-KO per 1k genes'),
            list('mean_levins_B_std ~ disc_per_1k_z',  'Disc per 1k genes')
        ))
    }
    results <- lapply(models, function(m) pgls_one(m[[1]], m[[2]], sub))
    do.call(rbind, Filter(Negate(is.null), results))
}

res_orig <- run_all(orig)
res_gtdb <- run_all(gtdb)
all_res  <- rbind(res_orig, res_gtdb)

# ─── 6. Summary ──────────────────────────────────────────────────────────────
cat('\n\n=== SUMMARY (predictor rows only) ===\n')
pred_rows <- all_res[all_res$predictor != '(Intercept)', ]
cat(sprintf('%-6s  %-30s  %5s  %8s  %8s  %8s\n',
            'Subset', 'Model', 'n', 'beta', 'SE', 'p-value'))
cat(strrep('-', 75), '\n')
for (i in seq_len(nrow(pred_rows))) {
    r <- pred_rows[i, ]
    sig <- if (!is.na(r$p_value) && r$p_value < 0.05) '*' else ' '
    cat(sprintf('%-6s  %-30s  %5d  %8.5f  %8.5f  %8.4g%s\n',
                r$subset, r$label, r$n, r$beta, r$SE, r$p_value, sig))
}

# ─── 7. Save ─────────────────────────────────────────────────────────────────
out <- file.path(data_dir, 'pgls_results_normalized.csv')
write.csv(all_res, out, row.names = FALSE)
cat(sprintf('\nSaved: %s\n', out))
