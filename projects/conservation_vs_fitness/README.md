# Conservation vs Fitness — Linking FB Genes to Pangenome Clusters

## Research Question

How do gene conservation patterns (core/auxiliary/singleton in pangenome clusters) relate to fitness phenotypes across diverse bacteria? Specifically: are essential genes preferentially conserved in the core genome, and what functional categories distinguish essential-core from essential-auxiliary and strain-specific essential genes?

## Motivation

The Fitness Browser provides mutant fitness data for ~221K genes across 48 bacteria, while the KBase pangenome classifies 132.5M gene clusters by conservation level (how many genomes in a species carry a given cluster). By linking these datasets, we can ask: do core genes (present in ≥95% of species genomes) show different fitness patterns than auxiliary or singleton genes? This project builds the bridge between the two datasets and performs the first cross-species analysis of essentiality vs conservation.

## Approach

1. **Link table** (Phase 1) — Map FB genes to pangenome clusters via DIAMOND blastp (≥90% identity, best hit per gene), resolving GTDB taxonomic renames via three matching strategies (NCBI taxid, organism name, scaffold accession)
2. **Essential gene identification** (Phase 2) — Identify putative essential genes as protein-coding genes (type=1) absent from `genefitness` (no viable transposon mutants recovered)
3. **Conservation analysis** — Compare conservation status (core/auxiliary/singleton) between essential and non-essential genes across 34 organisms
4. **Functional characterization** — Use FB annotations (SEED, KEGG) to profile essential genes by conservation category

## Key Methods

- **Organism matching**: Three complementary strategies (NCBI taxid, NCBI organism name in gtdb_metadata, scaffold accession prefix) to handle GTDB taxonomic renames
- **DIAMOND blastp**: Same-species protein similarity search at ≥90% identity threshold with best-hit-only output
- **Multi-clade resolution**: When GTDB splits an NCBI species into multiple clades, the clade with the most DIAMOND hits is chosen
- **Conservation classification**: Core (≥95% of species genomes), auxiliary (<95%, >1 genome), singleton (1 genome)
- **Essential gene definition**: Protein-coding genes (type=1 in FB gene table) with zero entries in `genefitness`. This is the standard RB-TnSeq definition — no viable transposon mutants were recovered. This is an upper bound on true essentiality; some genes may lack insertions due to being short or in regions with poor transposon coverage.
- **Statistical testing**: Fisher's exact test per organism (2x2: essential/non-essential x core/non-core), odds ratios, Spearman correlations for pangenome context

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kescience_fitnessbrowser` | `organism` | FB organism metadata, taxonomy IDs |
| `kescience_fitnessbrowser` | `gene` | Gene coordinates, type (1=CDS), descriptions |
| `kescience_fitnessbrowser` | `genefitness` | Fitness scores — absence = putative essential |
| `kescience_fitnessbrowser` | `seedannotation` | SEED functional annotations |
| `kescience_fitnessbrowser` | `besthitkegg` + `keggmember` + `kgroupdesc` | KEGG functional annotations |
| `kescience_fitnessbrowser` | `seedannotationtoroles` + `seedroles` | SEED functional hierarchy |
| `kbase_ke_pangenome` | `gtdb_metadata` | NCBI taxid/name for organism matching |
| `kbase_ke_pangenome` | `gene_cluster` | Cluster rep sequences, is_core/is_auxiliary/is_singleton |
| `kbase_ke_pangenome` | `pangenome` | Clade size, core/auxiliary/singleton counts |
| External | `fit.genomics.lbl.gov/cgi_data/aaseqs` | FB protein sequences |

## Results

### Link Table (Phase 1)

- **44 of 48** FB organisms mapped to pangenome species clades
- **177,863 gene-to-cluster links** at 100.0% median protein identity, 94.2% median gene coverage
- 34 organisms have ≥90% coverage; 33 used for downstream analysis (Dyella79 excluded due to locus tag mismatch)
- 4 organisms unmatched: Cola, Kang, Magneto, SB2B (species had too few genomes in GTDB for pangenome construction)
- Conservation breakdown: 145,821 core (82.0%), 32,042 auxiliary (18.0%) — of which 7,574 are singletons (singletons are a subset of auxiliary)

### Essential Genes Are Enriched in Core Clusters (Phase 2)

- **27,693 putative essential genes** identified (18.6% of 148,826 protein-coding genes across 33 organisms; range 12.9–28.9% per organism)
- Essential genes are **86.1% core** vs 81.2% for non-essential genes
- **Median odds ratio 1.56** — essential genes are 1.56x more likely to be in the core genome
- **18 of 33 organisms** show statistically significant enrichment (Fisher's exact test, BH-FDR q < 0.05)
- Strongest signal: *Methanococcus maripaludis* S2 (OR=5.21), *Ralstonia syzygii* PSI07 (OR=3.41), *Marinobacter adhaerens* (OR=3.08)

### Functional Profiles Differ by Conservation Category

| Category | n genes | % Enzyme | % Hypothetical |
|----------|--------:|:--------:|:--------------:|
| Essential-core | 22,751 | **41.9%** | **13.0%** |
| Essential-auxiliary | 3,683 | 13.4% | 38.2% |
| Essential-unmapped | 1,259 | 18.2% | 44.7% |
| Non-essential | 124,744 | 21.5% | 24.5% |

**Essential-core genes** are the most enzyme-rich (41.9%) and best-annotated (87% with known function). They are enriched in Protein Metabolism (+13.7 percentage points vs non-essential), Cofactors/Vitamins (+6.2%), Cell Wall (+3.9%), and Fatty Acid biosynthesis (+3.1%). They are depleted in Carbohydrates (-7.9%), Amino Acids (-5.6%), and Membrane Transport (-4.0%) — functions that tend to be conditionally important rather than universally essential.

**Essential-auxiliary genes** (3,683 genes essential for viability but not in all strains) are poorly characterized (38.2% hypothetical) and less likely to be enzymes (13.4%). Top subsystems: ribosomes, DNA replication, type 4 secretion, plasmid replication — suggesting strain-specific variants of core machinery plus mobile genetic elements.

**Essential-unmapped genes** (1,259 strain-specific essentials with no pangenome cluster match) are the least characterized (44.7% hypothetical). Known functions include divergent ribosomal proteins (L34, L36, S11, S12), translation factors, transposases, and DNA-binding proteins — likely recently acquired or highly divergent variants of core functions.

## Interpretation

### Literature Context

- Our finding that essential genes are enriched in core clusters aligns with the general expectation that genes required for viability are conserved across a species. However, the enrichment is modest (OR=1.56), reflecting that most genes in well-characterized bacteria are core regardless of essentiality.
- **Rosconi et al. (2022)** studied essentiality across 36 *S. pneumoniae* strains and found that the pan-genome makes gene essentiality strain-dependent. They identified "universal essential," "core strain-specific essential," and "accessory essential" genes — directly paralleling our essential-core, essential-auxiliary, and essential-unmapped categories. Our work extends this concept across 33 diverse bacterial species.
- **Hutchison et al. (2016)** designed a minimal *Mycoplasma* genome (473 genes) and found that 149 essential genes (31%) had unknown function. This parallels our finding that essential-unmapped genes are 44.7% hypothetical — essential genes remain among the least characterized.
- **Goodall et al. (2018)** used TraDIS to define the *E. coli* K-12 essential genome and noted that gene length biases can affect essentiality calls from transposon data. Our gene length validation (NB04) addresses this concern.
- **Price et al. (2018)** generated the Fitness Browser data used here, demonstrating genome-wide mutant fitness across 32 bacteria. Our work adds a pangenome conservation dimension to their fitness data.

### Limitations

- **Essential gene definition is an upper bound**: Genes without fitness data may lack transposon insertions due to being short, in low-complexity regions, or at scaffold edges — not necessarily because they are essential. Gene length validation shows essential genes are slightly shorter on average, suggesting some insertion bias.
- **Pangenome coverage varies**: Clades with only 2 genomes have trivially high core fractions (a gene in both genomes = 100% = core), reducing the discriminative power of core/auxiliary classification.
- **E. coli excluded**: The main *E. coli* clade was absent from the pangenome (too many genomes). *Keio* (E. coli BW25113) mapped to the small `s__Escherichia_coli_E` clade at only 26.1% coverage.
- **Single growth condition for essentiality**: RB-TnSeq essentiality is defined under the specific library construction conditions. Genes essential only under stress conditions would not be captured.
- **Dyella79 excluded** from Phase 2 due to locus tag format mismatch between FB gene table (`N515DRAFT_*`) and protein sequences (`ABZR86_RS*`), causing 0% join rate.
- **10 organisms excluded from Phase 2** due to <90% DIAMOND coverage, reducing taxonomic breadth.

## Future Directions

1. **Condition-specific fitness vs conservation**: Extend beyond essentiality to ask whether genes important for specific stress conditions (fitness < -2) show different conservation patterns
2. **Cross-organism essential gene families**: Use FB ortholog data to identify essential gene families conserved across multiple species
3. **Quantitative fitness vs conservation**: Correlate mean fitness effect (not just essential/non-essential binary) with core genome fraction
4. **Accessory genome essential functions**: Deeper characterization of the 3,683 essential-auxiliary genes — are they compensating for missing core functions?

## Project Structure

```
projects/conservation_vs_fitness/
├── README.md
├── notebooks/
│   ├── 01_organism_mapping.ipynb        # Map FB orgs → pangenome clades (Spark)
│   ├── 02_extract_cluster_reps.ipynb    # Download FB proteins + extract per-species FASTAs (Spark)
│   ├── 03_build_link_table.ipynb        # DIAMOND results → link table + QC (local)
│   └── 04_essential_conservation.ipynb  # Essential genes vs conservation analysis (local)
├── src/
│   ├── run_pipeline.py                  # NB01+NB02 data extraction via Spark Connect
│   ├── run_diamond.sh                   # DIAMOND search script (local)
│   └── extract_essential_genes.py       # NB04 data extraction via Spark Connect
├── data/
│   ├── organism_mapping.tsv             # FB org → clade mapping (44 organisms)
│   ├── fb_pangenome_link.tsv            # Final link table (177,863 rows)
│   ├── essential_genes.tsv              # Gene essentiality classification (153,143 genes)
│   ├── cluster_metadata.tsv             # Cluster conservation data (2.2M clusters)
│   ├── seed_annotations.tsv             # SEED annotations (125K)
│   ├── kegg_annotations.tsv             # KEGG annotations (73K)
│   ├── seed_hierarchy.tsv               # SEED functional hierarchy
│   └── pangenome_metadata.tsv           # Clade size and openness metrics
└── figures/
    ├── identity_distributions.png       # DIAMOND identity per organism
    ├── conservation_breakdown.png       # Core/aux/singleton per organism
    ├── essential_vs_core_forest_plot.png # Odds ratios across organisms
    ├── essential_length_validation.png   # Gene length validation
    ├── essential_enrichment_by_context.png # Clade size and openness effects
    ├── essential_enrichment_by_lifestyle.png # Lifestyle stratification
    ├── essential_enzyme_breakdown.png    # Enzyme classification by category
    └── essential_seed_toplevel_heatmap.png # SEED functional categories
```

## Reproduction

**Prerequisites:**
- Python 3.10+ with pandas, numpy, matplotlib, scipy
- DIAMOND (v2.0+) for protein similarity search
- BERDL JupyterHub access (for data extraction scripts)

**Running the pipeline:**

1. **Data extraction** (Spark Connect): `python3 src/run_pipeline.py` (NB01+NB02 data)
2. **DIAMOND search** (local): `src/run_diamond.sh data/organism_mapping.tsv data/fb_fastas data/species_fastas data/diamond_hits`
3. **Link table + QC** (local): Execute `notebooks/03_build_link_table.ipynb`
4. **Essential gene extraction** (Spark Connect): `python3 src/extract_essential_genes.py` — also generates `seed_hierarchy.tsv`
5. **Conservation analysis** (local): Execute `notebooks/04_essential_conservation.ipynb`

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory

## References

- Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509. DOI: 10.1038/s41586-018-0124-0. PMID: 29769716
- Rosconi F et al. (2022). "A bacterial pan-genome makes gene essentiality strain-dependent and evolvable." *Nat Microbiol* 7:1580-1592. DOI: 10.1038/s41564-022-01208-7. PMID: 36097170
- Hutchison CA 3rd et al. (2016). "Design and synthesis of a minimal bacterial genome." *Science* 351:aad6253. DOI: 10.1126/science.aad6253. PMID: 27013737
- Goodall ECA et al. (2018). "The Essential Genome of Escherichia coli K-12." *mBio* 9:e02096-17. DOI: 10.1128/mBio.02096-17. PMID: 29463657
- Deutschbauer A et al. (2014). "Towards an informative mutant phenotype for every bacterial gene." *J Bacteriol* 196:3643-55. DOI: 10.1128/JB.01836-14. PMID: 25112473
