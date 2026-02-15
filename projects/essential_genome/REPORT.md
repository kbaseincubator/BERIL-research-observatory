# Report: The Pan-Bacterial Essential Genome

## Key Findings

### 15 Gene Families Are Essential in All 48 Bacteria
The absolute core of bacterial life: ribosomal proteins (rpsC, rplW, rplK, rplB, rplA, rplF, rps11, rpsJ, rpsI, rpsM), chaperonin (groEL), CTP synthase (pyrG), translation elongation factor G (fusA), valyl-tRNA synthetase (valS), and geranyltranstransferase (SelGGPS). These 15 families span all 48 organisms with no exceptions.

### Only 5% of Ortholog Families Are Universally Essential
Of 17,222 ortholog families across 48 bacteria, 859 (5.0%) are universally essential. Of these, 839 are strict single-copy families (copy ratio ≤1.5, no non-essential paralogs); 20 contain paralogs. 4,799 families (27.9%) are variably essential — essential in some organisms, non-essential in others. 11,564 (67.1%) are never essential.

### Orphan Essential Genes Are 58.7% Hypothetical
7,084 essential genes have no orthologs in any other FB organism. These are 58.7% hypothetical — the least characterized yet most functionally important genes in each organism. By contrast, universally essential genes are only 8.2% hypothetical.

### 1,382 Function Predictions for Hypothetical Essentials
Module transfer via non-essential orthologs in ICA fitness modules generated 1,382 function predictions for hypothetical essential genes (35.3% of predictable targets). All predictions are family-backed. Top predicted functions: TIGR00254 (signal transduction), PF00460 (flagellar basal body rod), PF00356 (lactoylglutathione lyase).

### Universally Essential Families Are Overwhelmingly Core
Universally essential genes are 91.7% core vs 80.7% for non-essential. 71% of universally essential families are 100% core across all genomes in their species. Orphan essentials are only 49.5% core — strain-specific essential functions.

## Results

### Essential Gene Landscape
- **221,005 genes** across 48 organisms, **41,059 essential** (18.6%)
- Essentiality rate ranges from 12.2% (*Pedo557*) to 29.7% (*Magneto*)
- **2,838,750 BBH pairs** yield **17,222 ortholog groups** spanning all 48 organisms
- Essential genes are shorter than non-essential (median 675 bp vs 885 bp); 17.8% of essentials are <300 bp

### Family Classification

| Class | Families | % | Description |
|-------|---------|---|-------------|
| Universally essential | 859 | 5.0% | Essential in every organism where family has members |
| Variably essential | 4,799 | 27.9% | Essential in some organisms, not others |
| Never essential | 11,564 | 67.1% | No essential members in any organism |

Variably essential families have median essentiality penetrance of 33%. 813 families are >50% essential, 704 are <10% essential.

### Conservation Hierarchy

| Essentiality class | % Core | n genes |
|-------------------|--------|---------|
| Universally essential | 91.7% | 6,963 |
| Variably essential | 88.9% | 90,844 |
| Never essential | 81.7% | 47,140 |
| Orphan essential | 49.5% | 4,683 |

Weak positive correlation between essentiality penetrance and core fraction (rho=0.123, p=1.6e-17): families essential in more organisms tend to be slightly more core (97.1% for >80% penetrance vs 92.8% for <20%). Clade size does NOT predict essentiality rate (rho=-0.13, p=0.36).

### Function Predictions
- 8,297 hypothetical essential genes across 48 organisms (20.2% of all essentials)
- 3,912 have orthologs (predictable); 4,385 are orphans (not predictable by this method)
- 1,382 predictions generated (35.3% of predictable targets), all family-backed
- Predictions span 48 organisms, from 90 predictions (pseudo1_N1B4) to 1 (Caulo)

## Interpretation

### The Essential Genome Is Small and Deeply Conserved

Only 859 of 17,222 ortholog families (5%) are universally essential, and just 15 are essential in all 48 organisms. These 15 families — ribosomal proteins, groEL, CTP synthase, translation elongation factor G, and valyl-tRNA synthetase — represent the irreducible functional core of bacterial life. This aligns with Koonin (2003), who estimated ~60 proteins are common to all cellular life, and Gil et al. (2004), who proposed a minimal gene set of ~206 genes. Our experimentally-defined universally essential set is smaller because it is restricted to genes where transposon disruption is lethal across all 48 tested organisms, which is more stringent than computational conservation.

### Variable Essentiality Is the Norm, Not the Exception

The largest category is variably essential families (4,799, 28%) — genes essential in some organisms but dispensable in others. With a median essentiality penetrance of 33%, most essential gene families are essential in only a minority of organisms. This directly extends Rosconi et al. (2022), who demonstrated within *S. pneumoniae* that the pan-genome makes gene essentiality "strain-dependent and evolvable." Our analysis shows this principle holds across 48 phylogenetically diverse species spanning Proteobacteria, Bacteroidetes, Firmicutes, and Archaea.

Variable essentiality implies that whether a gene is essential depends on genomic context — the presence of paralogs, alternative pathways, or compensatory functions in the accessory genome. This has implications for antibiotic target selection: only the 859 universally essential families are reliable broad-spectrum targets.

### Orphan Essentials: The Frontier of Unknown Biology

7,084 essential genes have no detectable orthologs in any other Fitness Browser organism. These orphan essentials are 58.7% hypothetical — the highest uncharacterized fraction of any category. They represent strain-specific essential functions that may include recently acquired genes, rapidly evolving proteins, or lineage-specific innovations. Their low core genome rate (49.5%) suggests many are not conserved even within their own species. Hutchison et al. (2016) similarly found that 149 of 473 genes (31%) in their minimal *Mycoplasma* genome had unknown function — our analysis shows this "dark matter" of essential genes is even larger when considering diverse bacteria.

### Module Transfer Illuminates Essential Gene Function

The ortholog-module transfer approach generated 1,382 function predictions for hypothetical essential genes. The method works because essential genes are invisible to ICA (no fitness data), but their non-essential orthologs in other organisms DO have fitness data and can participate in modules. By transferring the module's functional context across organisms, we bridge the gap between essentiality (which prevents fitness measurement) and function prediction (which requires fitness data).

### Literature Context

- **Koonin (2003)** estimated ~60 universally conserved proteins across all life, primarily translation-related. Our 15 pan-bacterial essential families are consistent — dominated by ribosomal proteins and translation machinery, but also include cell wall biosynthesis and nucleotide metabolism genes that may be bacteria-specific essentials.
- **Gil et al. (2004)** proposed a ~206-gene minimal bacterial gene set based on computational comparison of reduced genomes. Our 859 universally essential families is larger because it includes genes essential in free-living bacteria with larger genomes, not just obligate symbionts with minimal genomes.
- **Rosconi et al. (2022)** demonstrated context-dependent essentiality across 36 *S. pneumoniae* strains. Our work extends this concept from within-species to cross-species variation: the same gene can be essential in *Methanococcus* but dispensable in *Pseudomonas*, depending on metabolic context.
- **Duffield et al. (2010)** identified 52 conserved essential proteins across 14 bacterial genomes as drug targets. Our approach is complementary but uses experimental (RB-TnSeq) essentiality data across 48 organisms rather than computational prediction, providing empirical validation of conservation patterns.
- **Price et al. (2018)** generated the Fitness Browser data used here. Our work adds a cross-organism essentiality dimension to their fitness data, enabling function prediction for essential genes that are outside the reach of fitness profiling.
- **Hutchison et al. (2016)** found 149 essential genes of unknown function in their synthetic minimal genome. Our 7,084 orphan essentials (58.7% hypothetical) show this problem is universal across bacteria, not specific to *Mycoplasma*.

### Limitations

- **Essential gene definition is an upper bound**: Genes without transposon insertions may lack insertions due to small size, AT-rich sequence, or scaffold edge effects, not true essentiality.
- **BBH orthology is conservative**: Bidirectional best BLAST hits miss paralogs, gene fusions, and distant homologs. Some "orphan essentials" may have undetected orthologs with diverged sequences.
- **Connected components can over-merge**: Transitive connections in the BBH graph can merge unrelated genes into the same ortholog group, particularly for multi-domain proteins.
- **Essentiality is condition-dependent**: RB-TnSeq essentiality is defined under specific library construction conditions (typically rich media). Genes essential only under stress would be missed.
- **48 organisms is taxonomically limited**: The Fitness Browser organisms are biased toward culturable Proteobacteria. Essentiality patterns in uncultured lineages, Actinobacteria, or Firmicutes are underrepresented.
- **Module transfer predictions are indirect**: Function predictions for essential genes come from non-essential orthologs in other organisms. The essential gene's function may have diverged.

## Supporting Evidence

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `notebooks/02_essential_families.ipynb` | Build ortholog families, classify essentiality, functional characterization |
| `notebooks/03_function_prediction.ipynb` | Predict function for hypothetical essentials via module transfer |
| `notebooks/04_conservation_architecture.ipynb` | Connect essential families to pangenome conservation |

### Figures

| Figure | Description |
|--------|-------------|
| `figures/essential_families_overview.png` | 4-panel: family classification counts, size distribution by class, essentiality penetrance, annotation status |
| `figures/essential_families_heatmap.png` | Essentiality status across 48 organisms for top 40 universally essential families |
| `figures/conservation_architecture.png` | 4-panel: core fraction by class, family-level core distribution, penetrance vs conservation, clade size vs essentiality |

### Data Files

| File | Description |
|------|-------------|
| `data/all_essential_genes.tsv` | Essential status for 221,005 genes across 48 organisms (regenerate with `src/extract_data.py`) |
| `data/all_bbh_pairs.csv` | 2.84M BBH pairs across 48 organisms (regenerate with `src/extract_data.py`) |
| `data/all_ortholog_groups.csv` | 179,237 gene-OG assignments across 17,222 ortholog groups |
| `data/essential_families.tsv` | Per-family essentiality classification (17,222 families) |
| `data/essential_predictions.tsv` | 1,382 function predictions for hypothetical essential genes |
| `data/family_conservation.tsv` | Per-family pangenome conservation metrics (16,758 families with links) |

## Future Directions

1. **Characterize the 7,084 orphan essentials** — Are they on mobile elements? Recently acquired? Rapidly evolving? What functional categories do they represent?
2. **Validate predictions experimentally** — The 1,382 module-transfer predictions could be tested via CRISPRi knockdown under specific conditions predicted by the module context.
3. **Connect to metabolic networks** — For variably essential families, determine whether essentiality correlates with metabolic pathway completeness (e.g., is a gene essential only when an alternative pathway is absent?).
4. **Expand taxonomic coverage** — As the Fitness Browser adds more organisms, re-run the analysis to test whether the 15 pan-essential families remain universal.
5. **Compare to DEG database** — Cross-reference with the Database of Essential Genes to identify families that are essential in non-FB organisms.

## References

1. Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509. DOI: 10.1038/s41586-018-0124-0. PMID: 29769716
2. Rosconi F et al. (2022). "A bacterial pan-genome makes gene essentiality strain-dependent and evolvable." *Nat Microbiol* 7:1580-1592. DOI: 10.1038/s41564-022-01208-7. PMID: 36097170
3. Hutchison CA 3rd et al. (2016). "Design and synthesis of a minimal bacterial genome." *Science* 351:aad6253. DOI: 10.1126/science.aad6253. PMID: 27013737
4. Koonin EV. (2003). "Comparative genomics, minimal gene-sets and the last universal common ancestor." *Nat Rev Microbiol* 1:127-136. PMID: 15035042
5. Gil R et al. (2004). "Determination of the core of a minimal bacterial gene set." *Microbiol Mol Biol Rev* 68:518-537. PMID: 15353568
6. Duffield M et al. (2010). "Predicting conserved essential genes in bacteria." *Mol BioSyst* 6:2482-2489. PMID: 20949199
