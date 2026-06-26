library(phytools)
library(ape)
tree <- read.tree("/home/hmacgregor/BERIL-research-observatory/projects/microbeatlas_metal_ecology/data/genus_tree.nwk")
traits <- read.csv("/home/hmacgregor/BERIL-research-observatory/projects/metal_defense_vs_metabolism_classification/data/species_trait_matrix.csv")
rownames(traits) <- traits$species
for (trait_col in c("has_defense", "has_metabolism", "has_homeostasis")) {
  trait_vec <- setNames(traits[[trait_col]], rownames(traits))
  tryCatch({
    sig <- phylosig(tree, trait_vec, method="lambda", test=TRUE)
    cat(paste0(trait_col, ": lambda=", round(sig$lambda, 4), ", p=", format(sig$P, scientific=TRUE), "\n"))
  }, error = function(e) {
    cat(paste0(trait_col, ": ERROR - ", e$message, "\n"))
  })
}
