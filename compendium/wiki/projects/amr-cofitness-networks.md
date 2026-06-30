# Amr Cofitness Networks

This project mapped antibiotic resistance gene fitness relationships across 28 bacterial species to understand how resistance mechanisms integrate into cellular regulation. The key finding is that AMR support networks are surprisingly organism-specific rather than mechanism-specific—different resistance strategies within a single bacterium share far more cofitness partners than the same mechanism across different organisms, revealing that each organism's regulatory landscape shapes the co-regulatory context of resistance more than the type of resistance mechanism itself. The work also demonstrates that high-quality functional annotation (InterProScan GO terms) is essential for detecting real biological signals in cofitness networks, transforming a null enrichment result into one showing significant associations with flagellar motility and amino acid biosynthesis.

## Key findings

- High cofitness implies shared fitness phenotypes rather than direct transcriptional co-regulation, so functional enrichment in cofitness neighborhoods can reflect shared experimental context rather than biology. *(confidence: high)*
- The 28 Fitness Browser organisms are lab-adapted, phylogenetically biased toward Pseudomonas, and limited in ecological diversity, constraining generalizability. *(confidence: medium)*
- The flagellar and biosynthesis enrichment in AMR support networks may reflect shared dispensability under lab conditions rather than genuine mechanistic co-regulation. *(confidence: high)*
- Genome-wide cofitness analyses require high-coverage, uniformly computed functional annotations such as InterProScan on pangenome cluster representatives to detect real biological signals. *(confidence: medium)*
- Nearly all AMR gene-module assignments belong to cross-organism conserved module families, indicating these co-regulatory relationships are ancient. *(confidence: medium)*
- The organism-specificity of support networks is robust to the dispensability confound and reveals that each organism has its own characteristic set of co-varying genes, a genuine structural feature of genome organization. *(confidence: high)*
- This work is the first pan-bacterial mapping of AMR co-fitness neighborhoods across 28 organisms. *(confidence: high)*
- AMR cofitness support networks are significantly enriched for flagellar motility and amino acid biosynthesis GO terms across multiple organisms (FDR < 0.05). *(confidence: medium)*
- AMR support networks are organism-specific rather than mechanism-specific: different AMR mechanisms within one organism share more cofitness partners (Jaccard 0.375) than the same mechanism across organisms (Jaccard 0.207). *(confidence: high)*
- Cofitness support network size shows no correlation with AMR gene fitness cost (Spearman rho = -0.006, p = 0.87, N = 769), so the uniform cost of resistance is not explained by co-regulatory neighborhood size. *(confidence: high)*
- Only 24% of AMR genes fall into ICA fitness modules, but those modules are significantly larger than non-AMR modules (median 46 vs 27 genes), placing AMR genes within large multi-function cellular programs. *(confidence: high)*
- Switching from legacy SEED/KEGG annotations to InterProScan GO annotations on the same data turned a null enrichment result into a significant one. *(confidence: high)*
- A fitness-matched permutation test drawing random non-AMR genes matched on mean fitness level would distinguish whether the support-network enrichment is true co-regulation or a shared-dispensability artifact. *(confidence: high)*
- Computing cofitness separately for antibiotic versus standard growth conditions could distinguish true co-regulation from shared dispensability in AMR support networks. *(confidence: medium)*

## Topics

- [Topic: Amr Resistome](../topics/amr-resistome.md)
- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Gene Fitness](../topics/gene-fitness.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)
- [Kescience Fitnessbrowser](../data/kescience-fitnessbrowser.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/amr_cofitness_networks/REPORT.md)
