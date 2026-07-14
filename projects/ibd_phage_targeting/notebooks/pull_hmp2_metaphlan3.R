# Pull HMP_2019_ibdmdb MetaPhlAn3 relative abundance from curatedMetagenomicData.
# Writes:
#   /home/aparkin/data/CrohnsPhage_ext/hmp2_ibdmdb_relative_abundance.tsv
#   /home/aparkin/data/CrohnsPhage_ext/hmp2_ibdmdb_sample_metadata.tsv
suppressMessages({
  library(curatedMetagenomicData)
  library(SummarizedExperiment)
  library(mia)
})

outdir <- "/home/aparkin/data/CrohnsPhage_ext"
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

cat("Resolving HMP_2019_ibdmdb.relative_abundance ...\n")
res <- curatedMetagenomicData("HMP_2019_ibdmdb.relative_abundance",
                              dryrun = FALSE, counts = FALSE, rownames = "short")
stopifnot(length(res) >= 1)
se <- res[[1]]
cat("Experiment dim: ", dim(se)[1], " taxa x ", dim(se)[2], " samples\n", sep = "")

ab <- assay(se)            # taxa x samples
md <- as.data.frame(colData(se))
md$sample_id <- rownames(md)

# Keep species-level rows (MetaPhlAn3 rowData lineage):
rdf <- as.data.frame(rowData(se))
cat("rowData columns: ", paste(colnames(rdf), collapse = ", "), "\n", sep = "")

# cMD v3.18 relative_abundance experiment rowData has: superkingdom, phylum, class,
# order, family, genus, species. All 585 rows are species-level (no strain column).
# Keep all rows with a non-blank species name.
is_species <- !is.na(rdf$species) & nchar(rdf$species) > 0
cat("Species-level rows (species column non-blank): ", sum(is_species), " of ", nrow(rdf), "\n", sep = "")
ab_sp <- ab[is_species, , drop = FALSE]
cat("Resulting abundance matrix: ", nrow(ab_sp), " taxa x ", ncol(ab_sp), " samples\n", sep = "")

# Write TSVs
write.table(as.data.frame(ab_sp), file.path(outdir, "hmp2_ibdmdb_relative_abundance.tsv"),
            sep = "\t", row.names = TRUE, col.names = NA, quote = FALSE)
write.table(md, file.path(outdir, "hmp2_ibdmdb_sample_metadata.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE)

# Save the rowData (lineage + NCBI taxid) for synonymy reconciliation
write.table(rdf, file.path(outdir, "hmp2_ibdmdb_taxon_metadata.tsv"),
            sep = "\t", row.names = TRUE, col.names = NA, quote = FALSE)
cat("Wrote HMP2 MetaPhlAn3 to ", outdir, "/\n", sep = "")
