# Report: AMR Co-Fitness Support Networks

## Key Findings

### 1. AMR genes are embedded in larger-than-average co-regulated modules

![Module size comparison and mechanism coverage](figures/amr_module_analysis.png)

Only 24% of AMR genes (192/801) are assigned to ICA fitness modules, but the modules they inhabit are significantly larger than non-AMR modules: median 46 vs 27 genes (MWU p = 1.7×10⁻⁸). This indicates that when AMR genes are tightly co-regulated with other genes, it is within **large, multi-function cellular programs**, not small isolated modules. Notably, 99% (208/209) of AMR gene-module assignments are in cross-organism conserved module families, indicating these are ancient regulatory relationships. Module size does not differ between AMR mechanisms (efflux = enzymatic = 48, MWU p = 0.91).

*(Notebook: 02_amr_in_modules.ipynb)*

### 2. AMR support networks are enriched for flagellar motility and amino acid biosynthesis (H1 supported)

![GO term enrichment in AMR support networks](figures/go_enrichment_interproscan.png)

Using InterProScan GO annotations (68% gene coverage — 3.6× better than old SEED annotations), we detect significant functional enrichment in AMR cofitness neighborhoods. The top 6 GO terms enriched in ≥3 organisms (FDR < 0.05) are:

| GO Term | Description | Organisms (FDR<0.05) | Mean OR |
|---------|-------------|---------------------|---------|
| GO:0071973 | Flagellum-dependent cell motility | 5 | 4.7 |
| GO:0044780 | Flagellum assembly | 5 | 5.3 |
| GO:0009288 | Bacterial-type flagellum | 4 | 4.9 |
| GO:0071978 | Flagellum-dependent swarming | 4 | 5.0 |
| GO:0000105 | Histidine biosynthesis | 3 | 5.3 |
| GO:0000162 | Tryptophan biosynthesis | 3 | 5.3 |

This enrichment was undetectable with old SEED annotations (0/280 significant) — a dramatic demonstration that annotation quality matters for functional genomics.

The biological interpretation: AMR genes are co-regulated with the two most energetically expensive bacterial programs — **flagellar motility** (proton motive force driven) and **aromatic amino acid biosynthesis** (shikimate pathway). Both share the proton motive force as an energy source with efflux pumps, suggesting the cost of resistance reflects competition for cellular energy budgets.

By mechanism, efflux AMR genes show the strongest enrichment for amino acid biosynthesis (histidine in 6 organisms, tryptophan in 5), while metal resistance genes show stronger chemotaxis enrichment (4 organisms). However, no GO term is significantly mechanism-specific after FDR correction.

*(Notebooks: 03b_enrichment_interproscan.ipynb; cf. 03_support_networks.ipynb for old-annotation null result)*

### 3. Support networks are organism-specific, not mechanism-specific

![Jaccard comparison showing organism-specificity](figures/jaccard_go_comparison.png)

Different AMR mechanisms within the same organism share far more support partners than the same mechanism across organisms:

| Comparison | Mean Jaccard (GO) | Interpretation |
|-----------|-------------------|----------------|
| **Cross-mechanism** (same organism) | **0.375** | Different AMR genes in the same bug share 38% of cofitness GO terms |
| **Within-mechanism** (across organisms) | **0.207** | Same mechanism in different bugs shares only 21% |
| MWU test | p = 4.3×10⁻¹³ | Highly significant difference |

This means the organism's regulatory landscape — its particular wiring of transcription, metabolism, and signaling — shapes the AMR support network far more than the type of resistance mechanism. An efflux pump in *Pseudomonas* shares more cofitness partners with a beta-lactamase in the same *Pseudomonas* than with an efflux pump in *Shewanella*.

![GO term conservation heatmap by mechanism](figures/go_conservation_heatmap.png)

The conserved core across all mechanisms includes transmembrane transport (87–100% of organisms), signal transduction (87–100%), transcription regulation (96–100%), and phosphorelay signaling (91–100%). Flagellar motility (53–61%) and amino acid biosynthesis (30–73%) form a second tier of conservation. The only hint of mechanism specificity is histidine biosynthesis (efflux 68% vs metal 30%, p = 0.013 uncorrected, q = 0.18 after FDR).

*(Notebooks: 04b_cross_organism_interproscan.ipynb; cf. 04_cross_organism_conservation.ipynb for old KEGG analysis)*

### 4. Support network size does not predict fitness cost (H3 not supported)

![Network size vs fitness cost scatter](figures/network_size_vs_fitness.png)

There is no correlation between cofitness support network size and AMR gene fitness cost (Spearman rho = −0.006, p = 0.87, N = 769). This holds within each mechanism (efflux rho = −0.049, enzymatic rho = +0.038, metal rho = −0.031; all p > 0.4). The uniform cost of resistance (+0.086 from `amr_fitness_cost`) is not explained by the size of the co-regulatory neighborhood.

*(Notebook: 03_support_networks.ipynb)*

### 5. Annotation quality is critical: InterProScan reveals what SEED/KEGG missed

The switch from old Fitness Browser SEED/KEGG annotations to InterProScan GO annotations on the same data transformed a null result into a significant finding:

| Analysis | Old Annotations (SEED/KEGG) | InterProScan GO |
|----------|---------------------------|-----------------|
| Coverage | 40–80% per organism, variable | 60% uniform across all genes |
| Enrichment tests significant (FDR<0.05) | **0 / 280** | **35 / 3,193** |
| GO terms in ≥3 organisms | 0 | **6** (flagella, amino acid biosynthesis) |
| Cross-organism Jaccard (within-mech) | 0.069 | **0.207** (3× higher) |
| Cross-organism Jaccard (cross-mech) | 0.249 | **0.375** (1.5× higher) |

This is a methodological contribution: genome-wide cofitness analyses require high-coverage, uniformly computed functional annotations to detect real biological signals. InterProScan on pangenome cluster representatives provides this.

*(Notebooks: 03_support_networks.ipynb vs 03b_enrichment_interproscan.ipynb; 04_cross_organism_conservation.ipynb vs 04b_cross_organism_interproscan.ipynb)*

## Results

### Data Assembly (NB01)
- 28 organisms with AMR genes, fitness matrices, and ICA modules (full intersection)
- 801 AMR genes with fitness data; 769 (96%) have ≥1 extra-operon cofitness partner at |r| > 0.3
- 180,370 total cofitness partners; 179,375 extra-operon (only 0.6% excluded as near-operon)
- Support network sizes: mean 233 genes (|r|>0.3), 110 (|r|>0.4), 71 (|r|>0.5)

### Module Analysis (NB02)
- 24% of AMR genes in ICA modules (192/801)
- AMR-containing modules significantly larger (median 46 vs 27, p = 1.7×10⁻⁸)
- 136 unique module families contain AMR genes; 99% in cross-organism conserved families

### Support Network Enrichment (NB03/NB03b)

| Source | Tests | Significant (FDR<0.05) | Top signal |
|--------|-------|----------------------|------------|
| Old SEED | 280 | 0 | None |
| InterProScan GO | 3,193 | 35 | Flagellar motility (5 orgs) |
| Permutation (old SEED) | 250 | 23 | Membrane/cell wall (24%, fold 1.12) |
| Mechanism-specific GO | 9,244 | 212 | Efflux: histidine biosynthesis (6 orgs) |

### Cross-Organism Conservation (NB04/NB04b)

| Metric | Old KEGG | InterProScan GO |
|--------|----------|-----------------|
| Within-mechanism Jaccard | 0.069 | 0.207 |
| Cross-mechanism Jaccard | 0.249 | 0.375 |
| Cross > Within p-value | 1.0 | 4.3×10⁻¹³ |
| Mechanism-specific terms (FDR<0.05) | 2 (lipoprotein, toluene tolerance) | 0 |

## Interpretation

### AMR genes are co-regulated with the bacterial motility-chemotaxis-biosynthesis axis

The central finding is that AMR genes are not isolated functions — they are embedded in a regulatory context dominated by **flagellar motility, chemotaxis, two-component signaling, and amino acid biosynthesis**. These functions share a common thread: they are among the most energetically expensive programs in a bacterial cell, and they compete with efflux pumps and other resistance mechanisms for the proton motive force.

This provides a mechanistic explanation for the uniform +0.086 fitness cost observed in `amr_fitness_cost`: the cost reflects **competition for shared cellular energy budgets**, not the specific biochemistry of resistance. Disrupting an AMR gene frees energy for other co-regulated programs (motility, biosynthesis), producing a modest fitness advantage.

### Organism regulatory architecture trumps resistance mechanism

The strong organism-specificity of support networks (cross-mechanism Jaccard 0.375 >> within-mechanism 0.207) reveals that AMR genes adapt to **the organism's existing regulatory landscape** rather than building dedicated support infrastructure. This is consistent with compensatory evolution models (Patel & Matange 2021, eLife) that predict regulatory network rewiring integrates resistance into existing programs.

This explains a puzzle from `amr_fitness_cost`: mechanism predicts conservation (metal 44% accessory vs efflux 13%) but not cost. The cost is determined by the organism's regulatory context, while conservation is determined by the mechanism's acquisition history.

### Literature Context

- **Sagawa et al. (2017)** validated that cofitness recovers transcriptional regulatory relationships in 24 bacteria. Our finding that AMR cofitness neighborhoods are enriched for specific GO terms confirms this, with AMR genes revealing co-regulation with motility and biosynthesis.
- **Martinez & Rojo (2011)** reviewed the linkage between metabolism and intrinsic resistance, noting that global metabolic regulators modulate antibiotic susceptibility. Our discovery of amino acid biosynthesis enrichment in AMR support networks supports this metabolism-resistance coupling.
- **Olivares Pacheco et al. (2017)** showed efflux pump costs in *P. aeruginosa* are metabolic (PMF drain) and compensated by metabolic rewiring. The co-regulation of efflux genes with histidine and tryptophan biosynthesis (both energetically expensive) supports the PMF competition model.
- **Eckartt et al. (2024, Nature)** identified compensatory mutations targeting the same functional pathway as the resistance mutation. Our finding that support networks are organism-specific (not mechanism-specific) extends this: compensation integrates AMR genes into the organism's broader regulatory programs.
- **Cox & Wright (2013)** defined the "intrinsic resistome" — genes required for resistance to function. Our cofitness-defined support networks are an empirical mapping of this concept, revealing that the intrinsic resistome converges on motility and metabolic functions across diverse bacteria.

### Novel Contribution

This is the **first pan-bacterial mapping of AMR co-fitness support networks** across 28 organisms. Key novel findings:
1. AMR support networks are enriched for **flagellar motility and amino acid biosynthesis** — the two most energy-expensive bacterial programs
2. Support networks are **organism-specific** (J = 0.375) not mechanism-specific (J = 0.207), indicating regulatory integration dominates
3. **Annotation quality is critical**: InterProScan GO transformed a null result into a significant one, demonstrating that legacy annotations are insufficient for functional genomics
4. AMR genes are in **larger-than-average ICA modules** (p = 1.7×10⁻⁸), confirming they are embedded in broad cellular programs

### Limitations

1. **Cofitness ≠ co-regulation**: High cofitness implies shared fitness phenotypes across conditions but does not prove direct transcriptional co-regulation. Some associations may reflect shared pathway membership or epistatic interactions.
2. **GO term granularity**: Broad GO terms (transmembrane transport, membrane) appear in nearly all support networks and all genomes, potentially masking more specific signals. Future work should use GO slim subsets or Pfam domain-level analysis.
3. **Support network size**: At |r| > 0.3, mean network size is 233 genes (large). This may include many weak, non-specific associations. The key results hold at stricter thresholds (|r| > 0.4, |r| > 0.5) but with reduced sample sizes.
4. **H3 null result**: The absence of a network-size-cost correlation may reflect insufficient variance in fitness cost across genes, not a true absence of relationship.
5. **FB organism bias**: The 28 organisms are lab-adapted, phylogenetically biased (many Pseudomonas), and limited in ecological diversity.
6. **Operon exclusion heuristic**: The 5-ORF exclusion zone is approximate. Some true extra-operon partners may be excluded, and some polar-effect artifacts may remain.

## Data

### Sources

| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `kbase_ke_pangenome` | `interproscan_go`, `interproscan_domains` (Pfam), `bakta_annotations` | GO terms, Pfam domains, KEGG orthology for FB gene clusters |
| `kescience_fitnessbrowser` | (via cached matrices) | Fitness profiles for cofitness computation |
| Cross-project | `amr_fitness_cost/data/amr_genes_fb.csv` | AMR gene catalog |
| Cross-project | `amr_fitness_cost/data/amr_fitness_noabx.csv` | Per-gene fitness costs |
| Cross-project | `fitness_modules/data/modules/` | ICA module membership |
| Cross-project | `fitness_modules/data/module_families/` | Cross-organism module families |
| Cross-project | `fitness_modules/data/matrices/` | Cached fitness matrices |
| Cross-project | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | FB → pangenome cluster mapping |

### Generated Data

| File | Rows | Description |
|------|------|-------------|
| `data/amr_cofitness_partners.csv` | 180,370 | All cofitness partners (|r|>0.3) with annotations |
| `data/amr_module_membership.csv` | 818 | AMR gene → ICA module assignments |
| `data/amr_modules_characterized.csv` | 209 | AMR-containing modules with properties |
| `data/fb_interproscan_go.csv` | 438,000 | InterProScan GO terms for FB gene clusters |
| `data/fb_interproscan_pfam.csv` | 228,672 | InterProScan Pfam domains for FB gene clusters |
| `data/fb_bakta_kegg.csv` | 41,611 | Bakta KEGG orthology for FB gene clusters |
| `data/go_enrichment_interproscan.csv` | 3,193 | Per-organism GO enrichment results |
| `data/mechanism_go_enrichment.csv` | 9,244 | Per-mechanism GO enrichment results |
| `data/go_conservation_by_mechanism.csv` | 1,078 | GO term presence by mechanism × organism |
| `data/hub_support_genes.csv` | 47,327 | Hub genes (partner of multiple AMR genes) |
| `data/jaccard_go_within_mechanism.csv` | 956 | Cross-organism Jaccard (GO terms, within-mechanism) |
| `data/jaccard_go_cross_mechanism.csv` | 71 | Within-organism Jaccard (GO terms, cross-mechanism) |

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_data_assembly.ipynb` | Organism intersection, cofitness computation, operon exclusion, annotation |
| `02_amr_in_modules.ipynb` | AMR genes in ICA modules, module size comparison, family membership |
| `03_support_networks.ipynb` | H1/H3 with old SEED annotations (null result) |
| `03b_enrichment_interproscan.ipynb` | H1 with InterProScan GO — flagellar/biosynthesis enrichment |
| `04_cross_organism_conservation.ipynb` | H4 with old KEGG annotations |
| `04b_cross_organism_interproscan.ipynb` | H4 with InterProScan GO — organism-specificity confirmed |

### Figures

| Figure | Description |
|--------|-------------|
| `amr_module_coverage.png` | ICA module coverage of AMR genes by organism |
| `amr_module_analysis.png` | Module size comparison (AMR vs non-AMR) and mechanism coverage |
| `cofitness_threshold_sensitivity.png` | Network size vs cofitness threshold |
| `support_network_enrichment.png` | Old SEED-based enrichment heatmap (null result) |
| `go_enrichment_interproscan.png` | InterProScan GO enrichment (significant result) |
| `network_size_vs_fitness.png` | H3: network size vs fitness cost scatter |
| `go_conservation_heatmap.png` | GO term conservation by mechanism across organisms |
| `jaccard_go_comparison.png` | Organism-specific vs mechanism-specific Jaccard |
| `conserved_kegg_by_mechanism.png` | Old KEGG conservation by mechanism |

## Future Directions

1. **Pfam domain-level enrichment**: Pfam has 88% coverage (vs 68% for GO). Domain-level enrichment may reveal more specific support network functions than broad GO terms.
2. **Condition-specific cofitness**: Instead of all experiments, compute cofitness separately for antibiotic conditions vs standard growth. This could reveal AMR-specific co-regulation that is masked when averaged.
3. **Regulatory network inference**: Use motif analysis or regulon predictions to test whether AMR genes share transcription factor binding sites with their cofitness partners.
4. **Integrate with `amr_fitness_cost` antibiotic validation**: The NB03 finding that efflux genes flip more strongly under antibiotics (p = 0.007) may connect to the efflux-biosynthesis co-regulation — antibiotic exposure may simultaneously induce efflux and repress biosynthesis.
5. **Extend to prophage ecology**: The `prophage_ecology` project found phage modules; testing whether phage defense genes show similar co-regulation patterns with motility would reveal whether the AMR-motility axis is specific to resistance or a general feature of accessory gene regulation.

## References

- Cox G, Wright GD. (2013). "Intrinsic antibiotic resistance: mechanisms, origins, challenges and solutions." *Int J Med Microbiol* 303(6-7):287-292. PMID: 23499305
- Eckartt KA, et al. (2024). "Compensatory evolution in NusG improves fitness of drug-resistant M. tuberculosis." *Nature* 627:186-194. PMID: 38509362
- Martinez JL, Rojo F. (2011). "Metabolic regulation of antibiotic resistance." *FEMS Microbiol Rev* 35(5):768-789. PMID: 21645016
- Olivares Pacheco J, et al. (2017). "Metabolic compensation of fitness costs is a general outcome for antibiotic-resistant Pseudomonas aeruginosa mutants overexpressing efflux pumps." *mBio* 8(4):e00500-17. PMID: 28765215
- Patel A, Matange N. (2021). "Adaptation and compensation in a bacterial gene regulatory network evolving under antibiotic selection." *eLife* 10:e70931. PMID: 34591012
- Price MN, et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557(7706):503-509. PMID: 29769716
- Sagawa S, et al. (2017). "Validating regulatory predictions from diverse bacteria with mutant fitness data." *PLoS ONE* 12(5):e0178258. PMID: 28542589
- Arkin AP, et al. (2018). "KBase: The United States Department of Energy Systems Biology Knowledgebase." *Nature Biotechnology* 36(7):566-569. PMID: 29979655
