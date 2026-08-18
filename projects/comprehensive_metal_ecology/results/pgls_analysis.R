
library(ape)
library(nlme)
library(caper)
suppressMessages(library(dplyr))

# Load data
df <- read.csv("/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/results/social_niche_breadth_pgls_input.csv")
tree <- read.tree("/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/data/gtdb_bac_genus_pruned.tree")

# Prune tree to genera in data
tree <- drop.tip(tree, setdiff(tree$tip.label, df$genus_for_tree))
df <- df[df$genus_for_tree %in% tree$tip.label, ]
rownames(df) <- df$genus_for_tree

cat("Phylogenetic PGLS Analysis\n")
cat("==============================\n")
cat(paste("Genera analyzed:", nrow(df), "\n"))
cat(paste("Tree tips:", length(tree$tip.label), "\n\n"))

# Standardize predictors
df$ko_z <- scale(df$ko_per_mb)[,1]
df$genome_z <- scale(df$genome_size_mb)[,1]
df$log_n <- log10(df$n_samples)
df$log_n_z <- scale(df$log_n)[,1]

# Standardize response
df$count_std <- scale(df$count_breadth_std)[,1]
df$shannon_std <- scale(df$shannon_breadth_std)[,1]

# Model 1: Count breadth ~ ko + genome
cat("\nMODEL 1: Social niche breadth (count) ~ KO density + genome size\n")
m1 <- gls(count_std ~ ko_z + genome_z,
          data=df, correlation=corPagel(1, phy=tree, fixed=FALSE),
          method="ML", na.action=na.omit)
cat("\nCoefficients:\n")
print(summary(m1)\$tTable)
cat(paste("\nLambda:", round(coef(m1\$modelStruct\$corStruct, unconstrained=FALSE), 4), "\n"))
cat(paste("AIC:", round(AIC(m1), 2), "\n\n"))

# Model 2: Shannon breadth ~ ko + genome
cat("MODEL 2: Social niche breadth (Shannon) ~ KO density + genome size\n")
m2 <- gls(shannon_std ~ ko_z + genome_z,
          data=df, correlation=corPagel(1, phy=tree, fixed=FALSE),
          method="ML", na.action=na.omit)
cat("\nCoefficients:\n")
print(summary(m2)\$tTable)
cat(paste("\nLambda:", round(coef(m2\$modelStruct\$corStruct, unconstrained=FALSE), 4), "\n"))
cat(paste("AIC:", round(AIC(m2), 2), "\n\n"))

# Model 3: Count breadth ~ ko + genome + sample size control
cat("MODEL 3: Count breadth ~ KO + genome + log(n_samples)\n")
m3 <- gls(count_std ~ ko_z + genome_z + log_n_z,
          data=df, correlation=corPagel(1, phy=tree, fixed=FALSE),
          method="ML", na.action=na.omit)
cat("\nCoefficients:\n")
print(summary(m3)\$tTable)
cat(paste("\nLambda:", round(coef(m3\$modelStruct\$corStruct, unconstrained=FALSE), 4), "\n"))
cat(paste("AIC:", round(AIC(m3), 2), "\n\n"))

# Model 4: Joint with cross-biome B_std
cat("MODEL 4: Count breadth ~ KO + cross-biome niche breadth + genome\n")
m4 <- gls(count_std ~ ko_z + mean_levins_B_std + genome_z,
          data=df, correlation=corPagel(1, phy=tree, fixed=FALSE),
          method="ML", na.action=na.omit)
cat("\nCoefficients:\n")
print(summary(m4)\$tTable)
cat(paste("\nLambda:", round(coef(m4\$modelStruct\$corStruct, unconstrained=FALSE), 4), "\n"))
cat(paste("AIC:", round(AIC(m4), 2), "\n\n"))

# Save results to file
results <- data.frame(
  Model = c("Count breadth ~ KO + genome", 
            "Shannon breadth ~ KO + genome",
            "Count breadth ~ KO + genome + log(n)",
            "Count breadth ~ KO + biome_breadth + genome"),
  n = c(nrow(m1\$data), nrow(m2\$data), nrow(m3\$data), nrow(m4\$data)),
  Lambda = c(coef(m1\$modelStruct\$corStruct, unconstrained=FALSE),
             coef(m2\$modelStruct\$corStruct, unconstrained=FALSE),
             coef(m3\$modelStruct\$corStruct, unconstrained=FALSE),
             coef(m4\$modelStruct\$corStruct, unconstrained=FALSE)),
  AIC = c(AIC(m1), AIC(m2), AIC(m3), AIC(m4))
)
write.csv(results, "/home/hmacgregor/BERIL-research-observatory/projects/comprehensive_metal_ecology/results/social_niche_breadth_pgls_summary.csv", row.names=FALSE)
cat("\n\nResults written to social_niche_breadth_pgls_summary.csv\n")
