# Ecotype Env Reanalysis

This reanalysis tested whether the weak environment-gene-content correlations observed in microbial ecotypes could be explained by clinical sampling bias in AlphaEarth, by comparing environmental and human-associated species directly. The key finding was that environmental species did not show stronger correlations than human-associated species (p=0.83), and surprisingly, human-associated species showed slightly higher correlations, suggesting environmental factors play a weaker role in shaping bacterial gene content than phylogeny across both species groups.

## Key findings

- Environmental species lose more species to NaN partial correlations (21%) than human-associated species (7%), which could bias the comparison but would only strengthen the null result given the observed direction. *(confidence: high)*
- Klebsiella pneumoniae, a major clinical species, was excluded because it exceeded Spark's maxResultSize during gene-cluster extraction and has no correlation data. *(confidence: high)*
- Median partial correlations in this reanalysis are 27x higher than the original ecotype analysis (0.081 vs 0.003) because of the absence of downsampling, so absolute magnitudes are not comparable even though the group comparison remains valid. *(confidence: high)*
- AlphaEarth embedding similarity may not equate to ecological relevance, since the environmental variation it captures (climate, vegetation, land use) may not strongly predict which genes a bacterium carries. *(confidence: medium)*
- Contrary to the hypothesis, human-associated species showed slightly higher environment-gene-content partial correlations than environmental species, the opposite of the predicted direction. *(confidence: high)*
- Human-associated pathogens may exhibit real geographic structure from global epidemiological patterns, producing environment-gene-content associations that are epidemiological rather than ecological. *(confidence: medium)*
- The clinical sampling bias in the AlphaEarth subset, while real and significant for embedding-based analyses, does not account for or confound the weak environment-gene-content relationship in the ecotype analysis. *(confidence: high)*
- A continuous Spearman analysis confirmed the null result: the fraction of environmental genomes per species does not predict partial-correlation strength (rho=-0.085, p=0.25). *(confidence: high)*
- Genome-level isolation-source classification of the ecotype species set found 47% majority human-associated and only 21% majority environmental, confirming a strong clinical sampling bias in the AlphaEarth subset. *(confidence: high)*
- Restricting the ecotype analysis to environmental species did not yield stronger environment-gene-content correlations than human-associated species, with the Mann-Whitney U test far from significant (p=0.83). *(confidence: high)*
- Using a systematic genome-level harmonized isolation-source classification rather than coarse species-level manual assignment reproduced the prior null result (p=0.83 vs the original p=0.66) for the environment-versus-host comparison. *(confidence: high)*
- Environment may act on specific functional gene categories (transport, secondary metabolism) rather than whole-genome Jaccard distance, motivating targeted gene-subset tests. *(confidence: medium)*
- Repeating the classification with structured ENVO ontology terms from the env_broad_scale field may classify environments more accurately than keyword-based isolation-source harmonization. *(confidence: medium)*

## Topics

- [Topic: Environment Biogeography](../topics/environment-biogeography.md)
- [Topic: Metabolic Pathways](../topics/metabolic-pathways.md)
- [Topic: Microbial Ecotypes](../topics/microbial-ecotypes.md)

## Data

- [Kbase Ke Pangenome](../data/kbase-ke-pangenome.md)

## Authors

- [Paramvir S. Dehal](../authors/0000-0001-5810-2497.md)

[Open the full report →](../../../projects/ecotype_env_reanalysis/REPORT.md)
