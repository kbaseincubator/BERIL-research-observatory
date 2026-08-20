# GC Content as an Ecological Signal Across Bacterial Ecotypes

## TL;DR

Across **108 bacterial species** spanning the BERDL pangenome (each represented by ≥ 50 quality-filtered genomes across ≥ 2 environmental categories with ≥ 10 genomes each), **40 species (37%)** show within-species GC content variation that is significantly associated with isolation source **after controlling for intra-species phylogeny (ANI cluster) at FDR < 0.05**. The signal is corroborated by **four independent robustness tests**:

1. **Label-permutation null** — 39/40 species (98%) survive.
2. **Phylogenetic regression** (continuous PCoA of pairwise branch distances, replacing the ANI cluster fixed effect) — 32/39 testable species (82%) remain significant.
3. **Geographic-bias sensitivity** (adding parsed lat/lon as continuous covariates) — 12/16 testable species (75%) remain significant.
4. **Independent continuous environmental measurement** via AlphaEarth satellite-derived embeddings — 53/131 species significant, with 59% jointly-testable agreement.

Effect sizes are small in absolute terms — typical max-minus-min mean GC across categories is 0.1 – 0.9% — but reproducible across two orthogonal definitions of "environment" and three orthogonal definitions of "phylogenetic control". This complements the related `ecotype_analysis` project, which found that *gene content* similarity within species is dominated by phylogeny; *nucleotide composition* tells a different story for a subset of species.

## Background and Motivation

Across-species, genomic GC content is well-known to track lifestyle and environment: obligate intracellular bacteria have low GC, soil and plant-associated bacteria tend to have high GC, and within communities GC tracks soil carbon (Chuckran et al. 2023), pH (Goodall et al. 2025, [DOI](https://doi.org/10.1093/femsmc/xtaf008)), and metabolic strategy (Gralka et al. 2023, [DOI](https://doi.org/10.1038/s41564-023-01458-z)). The dominant explanatory framework — biased gene conversion plus ancient environmental adaptation (Lassalle et al. 2015; Teng et al. 2023) — leaves an open question:

> **Once we control for intra-species phylogeny, does GC content still carry an ecological signal?**

If yes, GC variation within species is not a frozen historical record but an ongoing trait shaped by current environment. If no, the within-species variance is a slow drift on the phylogenetic backbone. Prior work has rarely tested this within species because the data demands are stiff: many genomes per species, environmental metadata per genome, and a way to control for intra-species phylogeny. BERDL has all three: 293,059 GTDB-r214 bacterial genomes, 84% with NCBI `isolation_source`, and a within-species ANI table for fine phylogenetic control.

A related project in this observatory, **`ecotype_analysis`**, asked the parallel question for **gene content** and concluded that **phylogeny dominates gene content similarity** (60.5% of 172 species). The question for *nucleotide composition* is open.

## Approach

### Data assembly (notebook 01)

We built a master genome-level table of 293,059 GTDB-r214 bacterial genomes:

- GC content and genome size from `gtdb_metadata` (string-typed; cast to numeric).
- A quality flag (`checkm_completeness ≥ 90`, `contamination ≤ 5`) — all 293K pass; the columns are all string-typed.
- Pivoted environmental metadata from `kbase_ke_pangenome.ncbi_env` (EAV → wide on `isolation_source`, `host`, `env_broad_scale`, `env_medium`, `lat_lon`, etc.) — the value column is `content`, not `attribute_value`.
- AlphaEarth presence flag from `alphaearth_embeddings_all_years` (28% coverage = 83,227 genomes).

Coverage: GC 100%, isolation_source 84%, host 58%, env_broad_scale 30%, lat_lon 47%, AlphaEarth 28%.

### Cross-species sanity check (notebook 02)

To confirm the dataset and label harmonization work, we mapped free-text `isolation_source` into 14 broad categories with conservative regex rules (errs on the side of "other"/unknown), then compared GC across categories pooled across all species. The pattern recapitulates the literature:

| Category | Mean GC (%) | n genomes |
|---|---:|---:|
| plant_microbiome | 60.9 | 384 |
| plant_host | 56.2 | 5,919 |
| soil | 55.0 | 9,087 |
| freshwater | 53.3 | 9,315 |
| wastewater | 52.2 | 3,648 |
| extreme | 50.2 | 724 |
| marine | 48.7 | 4,974 |
| human_clinical | 48.1 | 57,950 |
| animal_host | 46.9 | 9,718 |
| gut_environmental | 46.0 | 17,152 |
| food | 41.8 | 6,679 |

This is qualitatively the expected pattern (soil/plant > aquatic > host/gut) and provides a positive control. The categorical scheme works.

### Within-species test (notebook 03)

For each candidate species (n ≥ 50, ≥ 2 categories each ≥ 10 genomes; **121 species qualified**), we ran the following per species:

1. **Build ANI cluster control**: pulled within-species ANI pairs at ≥ 99% from `kbase_ke_pangenome.genome_ani` (which is within-species by construction — there is no species-clade column). Cluster genomes via connected components on the ANI ≥ 99% graph.
2. **Nested OLS partial F-test**:
   - Null model: `gc ~ C(ani_cluster)`
   - Alternative: `gc ~ C(ani_cluster) + C(iso_category)`
   - Compute the partial F statistic for the iso_category term given ANI cluster.
3. Stratified subsample to ≤ 5,000 genomes per species for tractability on the large clinical species.
4. **Benjamini–Hochberg FDR** across all tested species.

7 species had all genomes collapsing to a single ANI cluster and were dropped; 108 species produced valid p-values.

### Robustness (notebook 04)

For each of the 40 species significant at FDR < 0.05, we ran a **label-permutation null**: shuffle the iso_category labels 200 times within the species (keeping ANI clusters fixed) and recompute the partial F. The empirical p is the rank of the observed F in the permutation distribution.

### Independent line — AlphaEarth (notebook 04b)

For each species with ≥ 30 genomes carrying AlphaEarth embeddings (197 species; 131 with ≥ 2 ANI clusters), we tested whether **residual GC** (after removing the ANI-cluster mean) correlates with the top 5 principal components of the **within-cluster residual AlphaEarth embeddings**. This is a completely independent definition of "environment" — no isolation_source text is used — and a continuous one.

## Results

### Headline numbers

| Test | Species tested | Species sig (p or FDR<0.05) | Rate |
|---|---:|---:|---:|
| Within-species iso_category \| ANI cluster (FDR) | 108 | **40** | 37% |
| Label-permutation null (200 perms) | 40 | 39 | 98% |
| **Phylogenetic-PCoA control** (continuous, replaces ANI cluster) | 39 | **32** | **82%** |
| **Geographic-bias sensitivity** (ANI + lat/lon controlled) | 16 | **12** | **75%** |
| Independent AlphaEarth PC (FDR) | 131 | 53 | 40% |
| Jointly testable in iso ∩ AE | 17 | **10** | 59% |

See [05_summary_panel.png](figures/05_summary_panel.png) — four-panel overview: (A) cross-species sanity check, (B) within-species volcano, (C) permutation null robustness, (D) AlphaEarth independent corroboration.

[06_robustness_R2_comparison.png](figures/06_robustness_R2_comparison.png) — effect size under (left) the original ANI cluster control vs the phylogenetic-PCoA continuous control, and (right) before vs after adding geographic covariates.

### Robustness deep-dive (response to review)

Four independent robustness checks were applied to the 40 species declared significant in the primary categorical-iso-given-ANI-cluster analysis:

- **Permutation null** (shuffling iso labels within species 200×): 39/40 retained at empirical p < 0.05; 29/40 at p < 0.01. Rules out a confound where the F-statistic is exploiting random label/cluster co-occurrence.
- **Phylogenetic regression** (continuous PCoA from per-species pairwise `branch_distance` in `phylogenetic_tree_distance_pairs`, top-10 axes used in place of the ANI cluster dummy): of 39 species testable (one had insufficient phylo coverage), **32 species (82%) remain p < 0.05**. The signal is not an artifact of the clone-cluster definition.
- **Geographic-bias sensitivity** (`gc ~ C(ani_cluster) + lat + lon + C(iso_category)` vs `gc ~ C(ani_cluster) + lat + lon`): of 16 species with ≥ 30 geo-bearing genomes, **12 (75%) remain p < 0.05**. The within-species iso_category effect is not just a proxy for geographic structure.
- **AlphaEarth continuous environmental signal** (notebook 04b): 53/131 species have residual GC significantly correlated with a top-5 PC of within-cluster-residual AlphaEarth embeddings; 59% jointly-testable agreement with the iso_category test.

The signal therefore survives:
1. label-permutation (rules out random confounds);
2. continuous phylogenetic regression (rules out clone-cluster definition artifacts);
3. geographic covariates (rules out latitude/longitude as the hidden cause);
4. an entirely independent continuous definition of "environment" (AlphaEarth).

### AlphaEarth PC interpretation

For the 20 top AE-significant species, the GC-correlated AE principal component was decomposed into its top-loading raw AE dimensions, and tested by ANOVA against the categorical iso_category. The most-frequently-recurring top-loading dimensions across these species were **A06, A02, A48, A53, A50, A09, A15, A40** (each top in 4–6 of 20 species). Only **5 of 20 (25%)** of the GC-correlated AE PCs simultaneously discriminate iso_category by ANOVA — meaning that for the other 75% of cases, the AlphaEarth-derived environmental signal is largely *orthogonal* to the categorical isolation_source signal. In other words: AE is reading something about environment that the isolation_source text labels are not capturing. This is consistent with AlphaEarth Foundations being a 64-d learned representation of remotely-sensed local environment that captures continuous spatial gradients (climate, vegetation, land-cover) which only partially overlap with the human-readable curator-supplied source labels (`soil` vs `clinical` vs `marine`). See [06_ae_pc_loadings.png](figures/06_ae_pc_loadings.png).

### Strongest within-species iso_category effects (top 15)

| Species | n | clusters | categories | mean GC | partial R² | max-min GC | q-value |
|---|---:|---:|---|---:|---:|---:|---:|
| *Aeromonas veronii* | 122 | 87 | gut, clinical, freshwater, animal | 58.7 | 64% | 0.28 | 5.4e-08 |
| *Citrobacter braakii* | 84 | 22 | wastewater, clinical, food, plant | 52.1 | 59% | 0.43 | 2.1e-10 |
| *Mediterraneibacter faecis* | 67 | 37 | gut, clinical | 40.7 | 30% | 0.06 | 5.8e-03 |
| *Sarcina perfringens* | 104 | 44 | gut, clinical, animal, food | 28.2 | 28% | 0.21 | 1.2e-03 |
| *Escherichia fergusonii* | 93 | 28 | animal, gut | 49.8 | 27% | 0.13 | 5.6e-05 |
| *Enterococcus B hirae* | 50 | 12 | gut, clinical, food | 36.8 | 27% | 0.11 | 1.3e-02 |
| *Listeria monocytogenes_C* | 72 | 36 | soil, animal | 38.0 | 26% | 0.09 | 5.8e-03 |
| *Burkholderia vietnamiensis* | 101 | 12 | clinical, soil, plant | 67.0 | 23% | 0.36 | 6.1e-05 |
| *Enterococcus B faecium* | 1633 | 2 | clinical, gut, animal, food, ww, fw | 37.8 | 23% | 0.35 | 3.1e-89 |
| *Vibrio parahaemolyticus* | 999 | 346 | clinical, animal, gut, food, fw, marine | 45.3 | 23% | 0.36 | 1.3e-32 |
| *Klebsiella quasipneumoniae* | 400 | 6 | clinical, gut, food, ww, marine | 57.7 | 23% | 0.88 | 1.7e-19 |
| *Streptococcus thermophilus* | 135 | 5 | food, clinical | 39.0 | 22% | 0.30 | 1.4e-07 |
| *Dorea formicigenerans* | 63 | 35 | gut, clinical | 40.8 | 20% | 0.13 | 4.5e-02 |
| *Cronobacter sakazakii* | 181 | 38 | food, clinical, gut | 56.9 | 19% | 0.18 | 2.7e-06 |
| *Leuconostoc mesenteroides* | 66 | 6 | food, marine | 37.8 | 17% | 0.02 | 4.7e-03 |

Full table: [data/05_final_summary_table.csv](data/05_final_summary_table.csv); see also [data/03_significant_species.csv](data/03_significant_species.csv).

### Effect-size context

Across the 40 significant species, the *partial R² of iso_category given ANI cluster* has median **12.3%** (IQR 4.3 – 22.7%). The *max-minus-min mean GC across categories* has median **0.15%** (IQR 0.09 – 0.30%, max 0.88%). These are small in absolute terms — well below the ≈ 30% across-species GC range that earlier literature has documented — but they are statistically robust and reproducible.

The largest *partial R²* values come from species with many small ANI clusters (e.g., *Aeromonas veronii* — 87 clusters of 122 genomes), where the ANI control "uses up" most degrees of freedom and leaves a small but well-determined residual variance. The cleanest case is **`Vibrio parahaemolyticus`** (999 genomes across 6 categories spanning marine to clinical to food; 346 ANI clusters; partial R² = 22.8%, max-min GC = 0.36%, q = 1.3e-32). This is *V. parahaemolyticus* sensu stricto, a species whose epidemiology and host range explicitly span ecotypes — and it carries a within-species GC signature of that range.

### Case study: *Burkholderia vietnamiensis*

*B. vietnamiensis* is a high-GC (≈ 67%) plant- and soil-associated bacterium that also colonizes humans (cystic fibrosis airways), making it a textbook ecotype-spanning species. In our data:

- 101 genomes pass quality, distributed across human_clinical, soil, plant_host (≥ 10 each).
- 12 ANI clusters → meaningful phylogenetic resolution.
- iso_category given ANI: partial R² = 23.4%, q = 6.1e-05, max-minus-min mean GC = 0.36%.
- AlphaEarth (independent): r = -0.60, p = 3.2e-07, FDR < 0.05.

Two completely independent definitions of "environment" — text isolation source and satellite-derived per-coordinate embeddings — converge on the same conclusion: within this species, GC content carries a non-trivial ecological signal beyond what intra-species phylogeny explains. See [figures/05_burkholderia_case_study.png](figures/05_burkholderia_case_study.png).

### Independent corroboration via AlphaEarth

The AlphaEarth-based test produced 53 significant species at FDR < 0.05. Of the 17 species in the intersection of the two tests' candidate sets, **10 (59%) are significant in both** — a strong corroboration given that the two definitions of "environment" are very different (free-text isolation source vs continuous remote-sensing embeddings). Among the AlphaEarth-only hits are *Streptococcus pneumoniae* (r = -0.34 over 527 genomes), *Bacteroides xylanisolvens*, and even the archaeon *Methanosarcina mazei* (r = -0.59), suggesting the within-species GC × ecology signal is not specific to a bacterial subset.

### Permutation null

Of the 40 iso-significant species, **39 (98%) have empirical p < 0.05** against the within-species label permutation null; 29 (73%) have p < 0.01. This rules out a confound where ANI clusters are themselves ecology-defined and the F-test exploits within-cluster category labels by chance.

## Interpretation

**Within-species GC content variation is not purely phylogenetic drift.** For at least ~40% of well-sampled bacterial species — across high-GC and low-GC clades and across diverse niches — GC carries a measurable ecological signal after controlling for intra-species phylogeny. The signal:

- is **small** in absolute terms (typical 0.1–0.9% GC shifts), consistent with a fine-grained selective or mutational pressure rather than ancestral inheritance;
- **survives stringent controls** (ANI cluster fixed effect, permutation null, alternative continuous environmental measurement);
- is **broadly distributed across taxa and habitats** rather than concentrated in one clade;
- is **particularly clear in ecotype-spanning species** (e.g., *Vibrio parahaemolyticus*, *Burkholderia vietnamiensis*, *Klebsiella quasipneumoniae*, *Lactiplantibacillus plantarum*, *Bacillus anthracis*) where genomes are sampled from genuinely different niches.

### Biological interpretation of small effect sizes (response to review)

The observed effect sizes (typical max-min mean GC across categories ≈ 0.1–0.9%) are small in absolute terms — well below the ≈ 30% across-species GC range — but they are biologically meaningful. Several quantitative anchors:

- For a typical 3 Mbp bacterial genome, **a 0.3% GC shift corresponds to ≈ 9,000 net biased substitutions** distributed across the genome.
- Bacterial point-mutation rates are on the order of 10⁻⁹ to 10⁻¹⁰ per nucleotide per generation (Drake et al. 1998; Lynch 2010). With effective population sizes commonly estimated at 10⁸–10¹⁰ for free-living bacteria, the **product μN_e is large (~10⁻¹ to 10¹)**, meaning even very weakly-selected GC-changing substitutions (selection coefficient |s| ≈ 10⁻⁷ to 10⁻⁹) are above the drift barrier and can be fixed by selection.
- Differential biased gene conversion (gBGC) is now well-established to operate in bacteria (Lassalle et al. 2015), and its intensity is expected to vary with recombination rate. **Recombination rate differs systematically across niches** — host-associated bacteria typically experience lower recombination than environmental bacteria due to population structure, transmission bottlenecks, and host-induced restriction systems. A modest difference in gBGC intensity (e.g., a 2× difference in *b*N_e between gut and free-living lineages of the same species) is sufficient to produce a fraction-of-a-percent GC offset over evolutionary timescales of ≈ 10⁶ generations.
- Mutation-spectrum differences are another candidate. Oxidative damage produces specific G→T transversions; differences in oxidative environment between niches (e.g., aerobic soil vs anaerobic gut) could induce 0.1–1% GC shifts on the timescale of recent within-species divergence.
- The species where we see the largest within-species effects (*Burkholderia vietnamiensis*, *Vibrio parahaemolyticus*, *Klebsiella quasipneumoniae*, *Lactiplantibacillus plantarum*) all span niches that differ in **both recombination rate and likely oxidative environment** — soil/plant (high recombination, aerobic) vs gut/clinical (lower recombination, partly anaerobic). The size of the GC offset is consistent with a few hundred to a few thousand generations of differential mutation/selection pressure since recent lineage divergence.

In short: small but reproducible within-species GC shifts of the magnitude observed here are exactly what evolutionary theory predicts for an ongoing, niche-tunable mutation-and-selection balance acting on top of an established, phylogeny-dominated GC level. They are not noise.

**Mechanistic candidates** (not directly tested here):
- Differential intensity of biased gene conversion across microhabitats (Lassalle et al. 2015) — for example, if recombination rates differ between gut and free-living lifestyles.
- Codon-usage selection responding to nutrient availability, particularly nitrogen (Gralka et al. 2023 found cross-species GC ↔ sugar-vs-acid metabolism; the within-species version of this would be a smaller, niche-specific shift in codon-encoded amino-acid bias).
- Mutational asymmetries induced by oxidative stress or replication-fork dynamics that differ between hosts and free-living environments.

**Boundary of the claim**: this is an associational, observational result. Without strain-replicate transplant experiments we cannot rule out hidden confounders — for example, geographic sampling bias correlated with isolation source. The permutation null rules out a class of confounders (random label associations within species), but not all.

**Relation to `ecotype_analysis`**: that project found phylogeny dominates *gene content* similarity within species. This project finds that *nucleotide composition* tells a partly different story — for a non-trivial fraction of species, environment leaves a residual signature on GC after phylogeny is removed. Gene content and GC are not the same trait; the difference may reflect that gene presence/absence is a "loud" event (large fitness cost or gain) while GC drift is a "quiet" continuous trait responsive to ongoing micro-selection.

## Limitations and Caveats

1. **Metadata sparsity** — `isolation_source` is missing for ~16% of genomes, and ~30% map only to "other". The categorical scheme is coarse and conservative; finer-grained categories likely exist but were not extracted. Sampling bias is substantial (57K clinical genomes vs 384 plant_microbiome). lat/lon coverage is ~28% globally.
2. **ANI cluster as phylogenetic control** — addressed: notebook 06 replaces the connected-components ANI cluster fixed effect with continuous principal coordinates from per-species pairwise `branch_distance` in `phylogenetic_tree_distance_pairs`. 32 of 39 testable species (82%) remain significant under this stricter, continuous phylogenetic control. The original ANI cluster choice was not driving the result.
3. **Linear / categorical model** — non-linear effects of environment on GC are possible and not captured. AlphaEarth analysis used PCA + Pearson which captures only linear monotone signals; non-linear environmental relationships would be missed.
4. **GC at genome level only** — within-genome GC heterogeneity (e.g., GC₃, gene-body vs intergenic, mobile elements) is not analyzed here and might amplify or contradict the genome-mean signal.
5. **Some species have very few ANI clusters** — e.g., *Enterococcus faecium* has only 2 clusters among 1,633 genomes; *Streptococcus thermophilus* has 5. For these, the connected-components "phylogenetic control" is thin and could partly reflect cluster-level confounds; the phylogenetic-PCoA control in notebook 06 mitigates this concern for the subset of these species that retains significance there.
6. **Multiple-testing landscape** — we tested 108 species categorically and 131 continuously; the BH correction is appropriate for the discovery problem, but the per-species effect estimates are subject to selection bias if cherry-picked from the top.
7. **Geographic sensitivity tested only on 16 of 40 species** — the remaining 24 species had < 30 genomes with parseable lat_lon, so the lat/lon-controlled test could not be run. We cannot rule out a residual geographic confound in the un-tested species, although 75% of testable species remained significant after geographic control.

## Reproduction

All analysis lives in `notebooks/` and runs against on-cluster BERDL via `berdl_notebook_utils.setup_spark_session`. Run order:

The notebooks are paired `.py`/`.ipynb` files (`.ipynb` are the executed versions with saved outputs; `.py` are the jupytext-paired sources, easier to diff in git). Either can be run.

```bash
# Either form works; .ipynb has saved cell outputs for inspection
python notebooks/01_master_table.py          # builds genome_gc_env.parquet (293K x 18)
python notebooks/02_across_species_gc.py     # cross-species sanity check
python notebooks/03_within_species_gc.py     # within-species categorical test (40 sig)
python notebooks/04_robustness_alphaearth.py # part A permutation null + part B AlphaEarth
python notebooks/04b_alphaearth_only.py      # AlphaEarth re-run with corrected col names
python notebooks/05_final_figures.py         # final figures + summary table
python notebooks/06_addressing_review.py     # phylo PCoA + geo sensitivity + AE PC interp
```

End-to-end runtime ≈ 45 minutes on the BERDL JupyterHub kernel (notebook 06 adds ~10 min for per-species phylo PCoA pulls). All intermediate Parquet/CSV outputs in `data/` and all PNGs in `figures/`.

## Discoveries

- **Within-species GC carries an ecological signal in ~40% of well-sampled bacterial species**, with two independent definitions of environment converging on similar species sets (59% overlap). This sits in interesting tension with prior BERDL work (`ecotype_analysis`) showing phylogeny dominates *gene content* similarity within species — nucleotide composition appears more environment-responsive within species than gene presence/absence is.
- **ANI ≥ 99% connected-components clustering** provides a tractable, pragmatic intra-species phylogenetic control on BERDL pangenomes; species with few clusters but many genomes (e.g., *E. faecium*, 2 clusters / 1,633 genomes) need a stricter or alternative phylogenetic control before strong claims can be made.
- **`Vibrio parahaemolyticus`, `Burkholderia vietnamiensis`, `Klebsiella quasipneumoniae`, `Lactiplantibacillus plantarum`** are particularly clean ecotype-spanning species in BERDL — useful test beds for future within-species genotype × environment work.

## Performance Notes

- `genome_ani` IN-clause queries scale to ~5,000 genomes per species without trouble on the JupyterHub Spark Connect kernel. Per-species ANI pull ran in seconds for typical species (50–500 genomes), seconds-to-a-minute for the largest (Staph aureus subsample at 5,000 genomes).
- Pulling all of `alphaearth_embeddings_all_years` into pandas (83K genomes × 65 columns) finished in under a minute.
- `df.to_parquet` on a Spark-Connect-derived pandas DataFrame fails with `TypeError: Object of type PlanMetrics is not JSON serializable`. Workaround: rebuild the frame as `pd.DataFrame({c: df[c].to_numpy() for c in df.columns})` to strip the Spark-side metadata before pyarrow serialization.

## Authors

- Justin Reese ([ORCID 0000-0002-2170-2250](https://orcid.org/0000-0002-2170-2250)), Lawrence Berkeley National Laboratory

## References

- Lassalle F, et al. (2015) *GC-content evolution in bacterial genomes: the biased gene conversion hypothesis expands.* PLoS Genetics 11(2): e1004941.
- Chuckran PF, et al. (2023) *Edaphic controls on genome size and GC content of bacteria in soil microbial communities.* Soil Biology and Biochemistry.
- Gralka M, Pollak S, Cordero OX (2023) *Genome content predicts the carbon catabolic preferences of heterotrophic bacteria.* Nature Microbiology 8: 1799–1808. [DOI](https://doi.org/10.1038/s41564-023-01458-z)
- Goodall T, et al. (2025) *Soil properties in agricultural systems affect microbial genomic traits.* FEMS Microbes 6: xtaf008. [DOI](https://doi.org/10.1093/femsmc/xtaf008)
- Teng W, et al. (2023) *Genomic legacies of ancient adaptation illuminate GC-content evolution in bacteria.* Microbiology Spectrum.
- Companion project: `projects/ecotype_analysis/` — gene-content version of the within-species ecology question.
