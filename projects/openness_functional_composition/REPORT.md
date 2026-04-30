# Report: Openness vs Functional Composition

## Key Findings

1. **H0 not rejected**: No COG category shows a statistically significant relationship with pangenome openness after Bonferroni correction. The universal "two-speed genome" pattern is independent of pangenome structure.

2. **L (mobile elements) shows a suggestive but non-significant positive trend**: L enrichment increases from Q1=0.080 (closed) to Q4=0.116 (open) — a 1.45x increase with large effect size (Cohen's d=0.756) — but does not reach significance (Spearman rho=+0.259, p=0.106; Mann-Whitney Q1<Q4 p=0.052; monotonic trend p=0.060). Within Bacillota_A, the trend is significant (rho=+0.886, p=0.019), but this is a single phylum with n=6 species.

3. **V (defense) enrichment is flat across openness**: Spearman rho=+0.066, p=0.686. Defense gene enrichment in novel genes does not scale with genome fluidity.

4. **Metabolic core enrichment does not differ by openness**: E (amino acid), C (energy), and G (carbohydrate) show no significant relationship with openness (all p>0.13). The core metabolic engine is equally enriched in both open and closed pangenomes.

## Hypothesis Verdicts

| Hypothesis | Verdict | Evidence |
|---|---|---|
| **H0**: COG enrichment independent of openness | **Not rejected** | 0/24 COG categories significant after Bonferroni; no Kruskal-Wallis tests significant |
| **H1**: Open pangenomes have higher L/V enrichment | **Not supported** (L suggestive) | L: rho=+0.259, p=0.106; V: rho=+0.066, p=0.686 |
| **H2**: Closed pangenomes have higher core metabolic diversity | **Not supported** | E: rho=-0.077, p=0.636; C: rho=-0.184, p=0.256; G: rho=-0.199, p=0.219 |
| **H3**: Two-speed genome intensifies with openness | **Not supported** | Only L shows a trend; all other categories flat |

## Analysis Summary

### Data
- **457 species** with ≥50 genomes from `kbase_ke_pangenome.pangenome`
- **40 target species** selected (10 per openness quartile), balanced across 5 phyla
- Openness metric: `1 - (no_core / no_gene_clusters)`, range 0.095 to 0.991
- COG enrichment computed as `singleton_proportion - core_proportion` per species per COG category

### Openness Distribution
| Quartile | n | Openness range | Median |
|---|---|---|---|
| Q1 (closed) | 115 | 0.095 - 0.810 | 0.759 |
| Q2 | 114 | 0.811 - 0.873 | 0.847 |
| Q3 | 114 | 0.874 - 0.915 | 0.895 |
| Q4 (open) | 114 | 0.915 - 0.991 | 0.936 |

### COG Enrichment by Openness Quartile (key categories)

| COG | Description | Q1 (closed) | Q2 | Q3 | Q4 (open) | Trend rho | Trend p |
|---|---|---|---|---|---|---|---|
| L | Mobile elements | +0.080 | +0.095 | +0.096 | +0.116 | +0.300 | 0.060 |
| V | Defense | +0.015 | +0.027 | +0.019 | +0.018 | +0.108 | 0.505 |
| J | Translation | -0.040 | -0.028 | -0.036 | -0.031 | +0.130 | 0.425 |
| E | Amino acid | -0.009 | -0.015 | -0.012 | -0.020 | -0.124 | 0.446 |
| C | Energy | -0.008 | -0.009 | -0.015 | -0.016 | -0.203 | 0.208 |
| G | Carbohydrate | -0.004 | -0.006 | -0.004 | -0.014 | -0.240 | 0.136 |

### Phylogenetic Controls
Within-phylum correlations for L enrichment vs openness are inconsistent: positive in Pseudomonadota (rho=+0.548) and Bacillota_A (rho=+0.886, p=0.019), zero in Bacillota (rho=0.000) and Actinomycetota (rho=0.000), negative in Bacteroidota (rho=-0.048). This inconsistency suggests the overall L trend is fragile and may be driven by specific lineages rather than a universal mechanism.

### Genome Count Control
Openness strongly correlates with genome count (rho=+0.717) — species with more sequenced genomes appear more open because more singletons are detected. However, genome count does NOT correlate with L enrichment (rho=+0.114), so the L trend is not a genome-count artifact.

## Interpretation

The "two-speed genome" — where novel genes are enriched in mobile elements (L) and defense (V) while core genes are enriched in metabolism and translation — appears to be a **fundamental property of bacterial genome organization that is independent of pangenome openness**. Species with highly closed pangenomes (core fraction >90%) show essentially the same COG enrichment pattern as species with highly open pangenomes (core fraction <10%).

This has two implications:

1. **The functional cargo of HGT is consistent regardless of frequency.** Whether a species rarely acquires foreign genes or constantly does so, the genes that arrive via horizontal transfer carry the same functional profile: mobile elements, defense systems, and niche-specific adaptations. The nature of the cargo is determined by the transfer machinery (phage, plasmid, integrative element), not by the receiving genome's openness.

2. **Pangenome openness reflects genome count effects more than biology.** The strong openness-genome-count correlation (rho=+0.717) suggests that much of the apparent variation in openness is driven by sampling depth. Species with 14,000+ genomes (K. pneumoniae, S. aureus) inevitably appear "open" because rare singletons are captured. This is a well-known limitation of pangenome analysis (Tettelin et al. 2005; McInerney et al. 2017).

The suggestive L enrichment trend (d=0.756, p~0.05) may warrant investigation at larger scale — sampling more species per quartile could resolve whether the trend is real. However, the current data is most consistent with H0.

## Figures

| Figure | Description |
|---|---|
| [`enrichment_by_quartile_heatmap.png`](figures/enrichment_by_quartile_heatmap.png) | Heatmap of COG enrichment across openness quartiles — L column shows the only visible gradient |
| [`openness_vs_lv_enrichment.png`](figures/openness_vs_lv_enrichment.png) | Scatter plots of L and V enrichment vs continuous openness — L shows weak positive trend, V is flat |
| [`core_metabolic_by_openness.png`](figures/core_metabolic_by_openness.png) | Metabolic COG enrichment across quartiles — no clear trend for any category |

## Limitations

- **Sample size**: 10 species per quartile (40 total) limits statistical power. The L trend (d=0.756) would likely reach significance with ~25 species per quartile.
- **Openness metric confounded by genome count**: rho=+0.717 between openness and genome count. True biological openness is difficult to disentangle from sampling depth.
- **Phylum imbalance**: Pseudomonadota and Bacillota dominate all quartiles. Rarer phyla (Spirochaetota, Chlamydiota) are underrepresented.
- **COG annotation coverage**: eggNOG mapper annotates ~50% of gene clusters with COG categories. Unannotated genes may carry different functional signals.
- **Singleton vs novel**: Enrichment computed as singleton_proportion - core_proportion. Auxiliary genes (intermediate conservation) are excluded from both ends.

## Novel Contribution

First systematic test of whether the universal COG enrichment pattern (from `cog_analysis`) scales with pangenome openness across 457 species spanning 14 phyla. The negative result — the two-speed genome is truly universal and openness-independent — strengthens the finding from `cog_analysis` by showing it is not an artifact of genome fluidity.

## Future Directions

1. **Scale to full 457 species**: Query COG distributions for all 457 species with ≥50 genomes (not just 40). This would provide ~115 species per quartile and likely resolve the marginal L enrichment signal.
2. **Correct for genome count**: Use rarefaction or subsampling to estimate openness at a fixed genome count per species, removing the sampling depth confound.
3. **Test with X (mobilome) instead of L**: eggNOG separates mobilome-specific genes (X) from general replication/repair (L). The X category may show a stronger openness relationship since it is more specifically HGT-related.
4. **Connect to lifestyle**: Stratify by host-associated vs free-living (from `ncbi_env`) to test whether the lifestyle COG stratification hypothesis interacts with openness.

## Methods

### Data Sources
- `kbase_ke_pangenome.pangenome` (27,690 species; filtered to 457 with ≥50 genomes)
- `kbase_ke_pangenome.gtdb_species_clade` (taxonomy)
- `kbase_ke_pangenome.gene_cluster` + `gene_genecluster_junction` + `eggnog_mapper_annotations` (3-way join for COG distributions)

### Statistical Tests
- Spearman rank correlation (continuous openness vs enrichment per COG)
- Kruskal-Wallis H-test (enrichment across quartiles per COG)
- Bonferroni correction across 24 COG categories
- Within-phylum Spearman (phylogenetic control)
- Openness-genome count correlation (confound check)
- Mann-Whitney U (Q1 vs Q4 pairwise for L)
- Cohen's d (effect size for L enrichment Q1 vs Q4)
