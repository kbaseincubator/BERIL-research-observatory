# Macro-Micro Nutrient Gene Co-occurrence Across 27,682 Bacterial Pangenomes

## Key Findings

1. **P-acquisition and metal-handling genes co-occur significantly** across 27,682 GTDB species pangenomes (phi=0.110, OR=2.3, Fisher p=1.3×10⁻⁶⁵; permutation Z=17.7, p<0.001). 80.2% of species encode at least one P-acquisition gene; 91.7% encode at least one metal-handling gene; 74.7% encode both.

2. **N-fixation and metal-handling show stronger individual-gene associations.** The nifH(Pfam)–feoB pair has the highest enrichment of any nutrient–metal combination (1.90×, phi=0.269, p≈0), consistent with the Fe-Mo cofactor requirement of nitrogenase. The nifH(Pfam)–HMA pair is similarly enriched (1.96×, phi=0.229).

3. **All 63 phenazine operon carriers encode both P-acquisition and metal-handling genes** (100% overlap, OR=∞, Fisher p=9.4×10⁻³ for Phz-operon × Metal). These 63 species are concentrated in plant-associated and soil-dwelling families: Streptomycetaceae (24), Pseudomonadaceae (17), Streptosporangiaceae (10), and Enterobacteriaceae (6).

4. **P-acquisition genes are predominantly core** (70.7% of gene clusters in core genomes), while metal-handling genes span the core–accessory boundary (copA 56.8% core, corA 73.5%, feoB 30.0%, HMA 23.6%). The core–accessory structure differs significantly between nutrient and metal gene sets (Stouffer meta-Z=68.3, p≈0).

5. **Negative associations reveal biological structure.** Pst transporter genes (pstC, pstS, pstA) are depleted relative to feoB (0.64–0.86× expected; phi as low as −0.256), suggesting that high-affinity phosphate transport and ferrous iron uptake occupy distinct ecological niches.

## Background

Plant productivity and soil organic matter turnover depend on the simultaneous availability of macronutrients (C, N, P) and trace metals (Fe, Cu, Zn, Mn, Co, Ni, Mo). These pools are coupled through enzyme cofactor biochemistry — nitrogenase requires Fe and Mo, alkaline phosphatases require Zn or Ca, and urease requires Ni — and through mineral-surface biogeochemistry, where phosphate and trace-metal cations co-adsorb onto Fe(III)-oxyhydroxide surfaces in acidic, iron-rich soils (Edayilam et al. 2018).

McRose & Newman (2021, *Science* 371:1033–1037) demonstrated that phenazine biosynthesis is upregulated 1–3 orders of magnitude under phosphate starvation via the conserved PhoB regulon. Phenazines reductively dissolve Fe(III)-oxyhydroxides, simultaneously releasing adsorbed phosphate and co-adsorbed trace metals (Co, Cu, Ni). Wu et al. (2022) confirmed the presence of phenazine biosynthesis genes (phzS) in metagenome-assembled genomes from P-limited reforestation soils, establishing that this pathway operates in natural terrestrial microbiomes.

Despite these mechanistic links, macro-nutrient cycling and trace-metal dynamics are typically studied separately. This analysis provides the first genome-scale test of whether genes mediating phosphate and nitrogen acquisition share genomic context with metal-handling genes across bacterial diversity.

## Hypothesis

Bacterial pangenomes encoding genes for macro-nutrient acquisition (phosphatases, phosphate/phosphonate transporters, nitrogenases) and for microbial Fe-oxyhydroxide dissolution (phenazine biosynthesis) are disproportionately enriched for trace-metal handling pathways (Cu, Fe, Zn, Co, Ni transport and homeostasis), beyond what is expected by chance.

## Data and Methods

### Dataset

`kbase_ke_pangenome` on the KBase BER Data Lakehouse (BERDL): 132.5 million gene clusters across 27,702 GTDB species pangenomes with Bakta functional annotations (KEGG KO, gene names) and PFAM domain assignments (18.8M domain hits). Taxonomy from GTDB R214.

### Gene family definitions

| Group | Genes | Annotation source |
|-------|-------|------------------|
| **P-acquisition** (9 families) | phoA, phoD, pstA/B/C/S, phnC/D/E | KEGG KO K01077, PFAM PF09423, gene names |
| **N-fixation** (3 families) | nifH, nifD, nifH(Pfam) | KO K02588/K02586, PFAM PF00142 |
| **Metal-handling** (4 families) | copA, corA, feoB, HMA | KO K17686, gene name, PFAM PF02421/PF00403 |
| **Phenazine biosynthesis** (7 families) | phzA/B/D/F/G/S/M | KO K06998/K20940, gene names |

Species-level presence was scored as ≥1 gene cluster matching the annotation criterion. Phenazine "operon carriers" required ≥3 distinct phz gene families in a single species, filtering broad-family hits (phzF superfamily alone spans 10,856 species) from true operon-bearing lineages (63 species).

### Statistical tests

- **Pairwise co-occurrence:** Jaccard index, phi coefficient, Fisher's exact test (2×2 contingency) for all group pairs and all 76 individual nutrient×metal gene pairs.
- **Permutation null:** 1,000 random permutations of group membership vectors, preserving marginal counts. Observed phi compared to null distribution; Z-score and permutation p-value reported.
- **Core vs. accessory enrichment:** Fisher's exact test per species comparing core/non-core fractions between nutrient and metal gene sets. Stouffer meta-analysis across species (Z-scores combined as Z_meta = Σz / √n).
- **Phylogenetic stratification:** Phi coefficient computed within each GTDB phylum and class (minimum 50 or 20 species, respectively). Plant-associated families tested against global baseline.

## Results

### 1. Group-level co-occurrence

| Pair | n_both | Jaccard | Phi | OR | Fisher p | Permutation Z |
|------|-------:|--------:|----:|---:|:--------:|--------------:|
| P × Metal | 20,683 | 0.769 | 0.110 | 2.30 | 1.3×10⁻⁶⁵ | 17.7 |
| N × Metal | 5,718 | 0.224 | 0.107 | 4.04 | 1.5×10⁻⁸⁷ | 18.4 |
| Phz-operon × Metal | 63 | 0.002 | 0.014 | ∞ | 9.4×10⁻³ | 2.3 |
| P × N | 4,873 | 0.210 | 0.037 | 1.27 | 5.8×10⁻¹⁰ | 6.1 |
| Phz-operon × P | 63 | 0.003 | 0.024 | ∞ | 1.5×10⁻⁶ | 4.0 |
| N × Phz-operon | 3 | 0.001 | −0.019 | 0.19 | 5.3×10⁻⁴ | — |

All group pairs except N × Phz-operon show significant positive co-occurrence. The negative N × Phz-operon association (OR=0.19) reflects the concentration of phenazine operons in non-diazotrophic Actinomycetota (Streptomycetaceae) and non-diazotrophic Pseudomonas lineages.

### 2. Individual gene pair highlights

**Strongest positive associations (nutrient × metal):**

| Nutrient gene | Metal gene | Enrichment | Phi | n_both |
|--------------|-----------|----------:|----:|-------:|
| nifH(Pfam) | HMA | 1.96× | 0.229 | 1,988 |
| nifH(Pfam) | feoB | 1.90× | 0.269 | 2,641 |
| phzG | corA | 1.79× | 0.057 | 116 |
| phoD | HMA | 1.72× | 0.084 | 468 |
| phzB | corA | 1.65× | 0.030 | 43 |

**Strongest negative associations:**

| Nutrient gene | Metal gene | Enrichment | Phi | n_both |
|--------------|-----------|----------:|----:|-------:|
| pstC | feoB | 0.67× | −0.256 | 3,386 |
| pstS | feoB | 0.64× | −0.184 | 2,038 |
| pstC | HMA | 0.72× | −0.173 | 2,655 |

The nifH–feoB and nifH–HMA associations are mechanistically expected: nitrogenase requires an Fe₄S₄ cluster and Fe-Mo cofactor, making iron uptake (feoB) and heavy-metal ATPase transport (HMA) essential in diazotrophs. The pstC/S–feoB anti-correlation may reflect niche separation between organisms specializing in high-affinity phosphate scavenging (oligotrophic, often aerobic) versus those with active ferrous iron uptake (anaerobic or microaerobic environments where Fe²⁺ is soluble).

### 3. Core vs. accessory structure

P-acquisition genes are strongly core-biased (70.7% of clusters in core genomes), with Pst transporter genes reaching 73–77% core. In contrast, metal-handling genes show a bimodal distribution: corA (73.5%) is as core as phosphate transporters, while feoB (30.0%) and HMA (23.6%) are predominantly accessory.

Among co-occurring species, the Stouffer meta-Z for P-genes vs. metal-genes core-fraction enrichment is 68.3 (p≈0), confirming that nutrient and metal gene sets occupy systematically different positions in the core–accessory spectrum. Phenazine genes mirror the P-acquisition pattern: phzF (65.3%), phzS (65.9%), and phzM (78.9%) are predominantly core, consistent with stable genomic coupling.

The one notable exception is phoD (PFAM PF09423), which is only 17.2% core — the lowest core fraction of any P-acquisition gene. PhoD is a calcium-dependent phosphodiesterase often carried on mobile elements, and its accessory status is consistent with horizontal transfer as a mechanism for spreading P-acquisition capacity.

### 4. Phylogenetic distribution

**Phylum-level:** Positive P × Metal co-occurrence (phi > 0) is found in all 12 largest phyla except Spirochaetota (phi=−0.085, n=296) and Chloroflexota (phi=−0.074, n=457). The highest phi values occur in Cyanobacteriota (0.355, n=469), Fusobacteriota (0.453, n=59), and Bacillota (0.246, n=2,146). Pseudomonadota — the largest phylum (n=7,456) and the one hosting 27 of 63 phenazine operon carriers — has phi=0.167.

**Plant-associated families:** Pseudomonadaceae (n=498), Rhizobiaceae (n=413), Burkholderiaceae (n=333), Streptomycetaceae (n=382), and Xanthomonadaceae (n=207) all show near-universal P-acquisition (100%) and metal-handling (93–100%) gene prevalence. Their enrichment ratios (1.00×) reflect ceiling effects — essentially all species in these families encode both functional groups.

**Phenazine operon carriers (63 species):** Concentrated in 9 families:
- Streptomycetaceae (24): *Streptomyces* and *Kitasatospora* — soil actinomycetes
- Pseudomonadaceae (17): *Pseudomonas* and *Pseudomonas_E* — rhizosphere colonizers
- Streptosporangiaceae (10): *Microbispora*, *Nocardiopsis*, *Nonomuraea* — soil actinomycetes
- Enterobacteriaceae (6): *Xenorhabdus* — insect-associated (entomopathogenic nematode symbionts)
- Xanthomonadaceae (2): *Lysobacter* — soil/rhizosphere
- Burkholderiaceae (1): *Burkholderia*

The dominance of soil Actinomycetota (35/63, 56%) and rhizosphere Pseudomonadota (27/63, 43%) among phenazine operon carriers is consistent with the McRose-Newman model: phenazine-mediated Fe(III) reduction is an adaptive strategy in soils where Fe-oxyhydroxides lock up phosphate and trace metals.

## Interpretation

### The macro-micro nutrient coupling is genomically encoded

The central result — significant positive co-occurrence of P-acquisition, N-fixation, and metal-handling genes across 27,682 bacterial pangenomes — supports the hypothesis that macro-nutrient and trace-metal cycling are genomically coupled in bacteria. The effect sizes are modest at the group level (phi 0.01–0.11) but highly significant given the dataset size, and individual gene pairs reach enrichments of 1.7–2.0× with phi > 0.2.

The coupling is not uniform: it is strongest for the specific mechanistic links predicted by biochemistry:
- **nifH × feoB/HMA** (nitrogenase requires Fe-Mo cofactor) — strongest positive signal
- **phoD × HMA** (PhoD requires metal cofactors) — strong positive signal
- **pstC × feoB** (high-affinity phosphate transport vs. ferrous iron) — strong negative signal, suggesting niche separation

### Phenazine operon carriers as the extreme case

The 63 species with true phenazine operons (≥3 phz genes) represent the most extreme co-occurrence: 100% encode both P-acquisition and metal-handling genes. Their taxonomic distribution — dominated by soil Actinomycetota and rhizosphere Pseudomonadota — is precisely the ecological context where the McRose-Newman reductive dissolution mechanism would operate. These organisms live in soils where Fe(III)-oxyhydroxides are abundant, phosphate is limiting, and trace metals are co-adsorbed. The phenazine pathway provides a unified mechanism for accessing both macro and micro nutrients from the same mineral pool.

### Core vs. accessory reveals evolutionary stability

The differential core-genome placement of nutrient vs. metal genes suggests two modes of macro-micro coupling:
1. **Stable coupling** (corA + pst/phn genes, all >60% core): essential nutrient and metal handling co-inherited as part of the species' core metabolic identity
2. **Flexible coupling** (feoB/HMA + phoD, all <30% core): accessory metal handling and phosphodiesterase capacity acquired or lost via horizontal gene transfer, potentially responsive to local geochemical conditions

### Negative associations are informative

The depletion of pstC/S with feoB suggests that high-affinity phosphate scavenging and ferrous iron uptake occupy distinct ecological niches. Organisms investing in Pst-type phosphate transport (typically aerobic, low-P environments) may not coexist with conditions favoring FeoB-dependent Fe²⁺ uptake (anaerobic/microaerobic, high-Fe²⁺). This niche separation is consistent with the redox geochemistry of P and Fe: under aerobic conditions, Fe(III) precipitates and adsorbs phosphate (favoring Pst for P scavenging), while under anaerobic conditions, Fe(II) is soluble and P is released (favoring FeoB for Fe uptake but reducing P limitation).

## Limitations

1. **Presence/absence only.** This analysis scores whether a species pangenome contains at least one gene cluster matching an annotation criterion. It does not test whether the genes are co-expressed, co-regulated, or physically clustered in genomes. Expression-level coupling (e.g., PhoB-dependent phenazine upregulation) cannot be inferred from co-occurrence alone.

2. **Annotation-dependent coverage.** Gene families identified via KEGG KO and PFAM domain hits may miss divergent homologs. The pstA/B/C/S genes lack KEGG KO assignments in Bakta and were identified by gene name only; some genuine pst genes may be annotated with different names. Similarly, phenazine gene identification relies on gene name matching, which may miss renamed or poorly annotated homologs.

3. **Phylogenetic non-independence.** Closely related species share gene content by descent, inflating co-occurrence statistics. The permutation test controls for marginal gene frequencies but not for phylogenetic autocorrelation. A full phylogenetic logistic regression or phylogenetic independent contrasts analysis would provide a stronger control.

4. **Ecological inference from genomic potential.** Encoding a gene does not guarantee its expression in a given environment. The co-occurrence pattern is consistent with — but does not prove — coordinated nutrient-metal cycling in natural environments.

5. **Phenazine operon definition.** The ≥3 distinct phz gene threshold is a heuristic. Some species may carry partial operons or unlinked phz genes from different biosynthetic pathways. Manual curation of operon structure (e.g., checking genomic synteny) would strengthen the phenazine results.

## Future Directions

- **Substrate C (mechanistic, deferred):** Gene-level fitness analysis under controlled P-starvation and metal-stress conditions. The RB-TnSeq dataset in `kescience_fitnessbrowser` lacks P-starvation experiments (see exhaustive search in `memory/20260507e_*`). New RB-TnSeq campaigns under defined low-P media, or GapMind-extended P-pathway scoring, would provide the mechanistic substrate.

- **Substrate B (ecological):** Where do communities enriched for the macro-micro co-occurrence gene profile appear along nutrient gradients in natural soils? Data: NMDC multi-omics + abiotic features + ENIGMA CORAL.

- **Phylogenetic independent contrasts:** Apply phylogenetic logistic regression using GTDB phylogenetic distance pairs to control for shared ancestry and test whether co-occurrence remains significant after accounting for phylogenetic signal.

- **Field validation (Point Reyes):** The mafic-vs-felsic fault gradient at Point Reyes (Rowley et al. 2023, 2024) provides a natural experiment to test whether co-released P and trace metals (Co, Cu, Ni) from Fe-oxyhydroxide dissolution shape rhizosphere community composition in the pattern predicted by this genomic analysis.

## References

- Edayilam, N. et al. (2018). Phosphorus stress-induced changes in plant root exudate composition and their effects on morphology and key functional groups of soil bacterial and archaeal communities. *Environmental Microbiology*, 20(7), 2504–2521.
- McRose, D.L. & Newman, D.K. (2021). Redox-active antibiotics enhance phosphorus bioavailability. *Science*, 371, 1033–1037.
- Wu, Z. et al. (2022). Phenazine biosynthesis genes in metagenome-assembled genomes from phosphorus-limited reforestation soils. *ISME Journal*.
- Dakora, F.D. & Phillips, D.A. (2002). Root exudates as mediators of mineral acquisition in low-nutrient environments. *Plant and Soil*, 245, 35–47.

## Data and Reproducibility

All analyses were performed on the KBase BER Data Lakehouse using Spark SQL queries against `kbase_ke_pangenome` (132.5M gene clusters, 27,702 species pangenomes, GTDB R214). Source code is in `src/01_extract_gene_families.py` through `src/05_figure.py`. Intermediate data files are in `data/`. The multi-panel figure is at `figures/figure1_cooccurrence.png`.

**Figure 1.** (A) Phi coefficient heatmap for 76 nutrient × metal gene pairs. (B) Core genome fraction per gene family. (C) Phylum-level P × Metal co-occurrence. (D) Taxonomic distribution of phenazine operon carriers.
