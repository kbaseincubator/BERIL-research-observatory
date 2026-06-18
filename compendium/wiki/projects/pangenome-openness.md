# Pangenome Openness

This project tested whether the openness of a bacterial pangenome—the degree to which gene content varies across species—predicts whether environmental selection or evolutionary history drives that variation. Analyzing pangenome statistics and ecological effect sizes across dozens of species, the study found no correlation between pangenome openness and the strength of environmental or phylogenetic effects on gene content. This null result suggests that pangenome structure and the eco-phylogenetic forces shaping it are largely independent, implying that simply counting variable genes may not reveal which ecological pressures a species faces.

## Key findings

- Core/accessory classification may not capture functional adaptation, since the genes that vary may not be the ones responding to environment. *(confidence: medium)*
- Environment and phylogeny effects come from partial correlations that may not fully disentangle confounded variables. *(confidence: medium)*
- Openness is a single summary metric that may not capture the full complexity of pangenome structure, potentially masking real relationships. *(confidence: medium)*
- The analysis is limited to species having both pangenome statistics and ecotype analysis results, constraining sample size and statistical power. *(confidence: high)*
- Because openness is uncorrelated with environment effects, horizontal gene transfer may be opportunistic rather than tracking environmental similarity. *(confidence: medium)*
- The Tettelin open/closed pangenome distinction describes gene-content variability but does not predict its ecological versus phylogenetic drivers. *(confidence: medium)*
- The null result implies pangenome structure is largely independent of the eco-phylo dynamics governing gene-content variation. *(confidence: medium)*
- The project hypothesized that open pangenomes should show stronger environment effects due to high gene turnover and HGT. *(confidence: low)*
- Whether a species has an open or closed pangenome does not predict whether environment or phylogeny dominates its gene-content variation. *(confidence: high)*
- Pangenome openness shows no significant correlation with either environmental or phylogenetic effect sizes on gene content across species. *(confidence: high)*
- Pangenome openness was operationalized as one minus the core gene fraction, with higher values denoting more open pangenomes. *(confidence: high)*
- Spearman correlations between openness and effects were near zero and non-significant (environment rho = -0.05, p = 0.54; phylogeny rho = 0.03, p = 0.73). *(confidence: high)*
- The BERDL pangenome table already contains pre-computed pangenome statistics, removing the need to compute them from the gene_cluster table. *(confidence: high)*
- The uncorrelated openness finding is consistent with McInerney et al. (2017) view of HGT as opportunistic rather than ecologically directed. *(confidence: medium)*
- Alternative openness metrics such as auxiliary fraction, Heap's law alpha, or pangenome fluidity could be tested to probe the null result. *(confidence: low)*
- Stratifying by gene function could reveal whether open pangenomes show environment effects specifically in mobile (L) or defense (V) COG categories. *(confidence: low)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Functional Dark Matter](../topics/functional-dark-matter.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)
- [Topic: Mobile Genetic Elements](../topics/mobile-genetic-elements.md)
- [Topic: Pangenome Architecture](../topics/pangenome-architecture.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/pangenome_openness/REPORT.md)
