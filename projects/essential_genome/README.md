# The Pan-Bacterial Essential Genome

## Research Question

Which essential genes are conserved across bacteria, which are context-dependent, and can we predict function for uncharacterized essential genes using module context from non-essential orthologs?

## Motivation

The `conservation_vs_fitness` project identified 27,693 putative essential genes across 33 bacteria and showed they are modestly enriched in core pangenome clusters (OR=1.56). The `fitness_modules` project built 1,116 ICA fitness modules across 32 organisms and aligned them into 156 cross-organism families. But no one has asked: **when an essential gene in organism A has an ortholog in organism B, is that ortholog also essential?**

This project clusters essential genes into cross-organism ortholog families and classifies them along a spectrum:

- **Universally essential** — essential in every organism where the family has members. These are the most fundamental bacterial functions.
- **Variably essential** — essential in some organisms, non-essential in others. Essentiality depends on genomic context, metabolic wiring, or strain background.
- **Never essential** — ortholog family has no essential members in any organism.

For uncharacterized essential genes (~44% hypothetical), we predict function by finding non-essential orthologs in other organisms that participate in ICA fitness modules, transferring the module's functional context.

## Approach

1. **Extract data** — Essential gene status + BBH ortholog pairs for all 48 FB organisms via Spark
2. **Build ortholog groups** — Connected components of BBH graph (networkx)
3. **Classify families** — Universal vs variable vs never essential
4. **Predict function** — Module-based function transfer for hypothetical essentials
5. **Conservation architecture** — Connect essential families to pangenome core/accessory status

## Data Sources

| Database | Table | Use |
|----------|-------|-----|
| `kescience_fitnessbrowser` | `organism` | All 48 organisms |
| `kescience_fitnessbrowser` | `gene` | Gene metadata, type=1 for CDS |
| `kescience_fitnessbrowser` | `genefitness` | Absence = putative essential |
| `kescience_fitnessbrowser` | `ortholog` | BBH pairs across organisms |
| `kescience_fitnessbrowser` | `seedannotation` | SEED functional annotations |
| Shared | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | Conservation status |
| Shared | `fitness_modules/data/modules/*` | ICA module membership + annotations |
| Shared | `fitness_modules/data/module_families/*` | Cross-organism module families |

## Project Structure

```
projects/essential_genome/
├── README.md
├── requirements.txt
├── references.md
├── src/
│   └── extract_data.py                    # Spark: extract essentials + orthologs + build OGs
├── notebooks/
│   ├── 02_essential_families.ipynb           # Build and classify essential gene families
│   ├── 03_function_prediction.ipynb          # Predict function for hypothetical essentials
│   └── 04_conservation_architecture.ipynb    # Connect to pangenome conservation
├── data/
│   ├── all_essential_genes.tsv            # Essential status for all 48 organisms
│   ├── all_bbh_pairs.csv                  # BBH pairs for all 48 organisms
│   ├── all_ortholog_groups.csv            # OG assignments for all 48 organisms
│   ├── essential_families.tsv             # Per-family essentiality classification
│   ├── essential_predictions.tsv          # Function predictions for hypothetical essentials
│   └── family_conservation.tsv            # Per-family pangenome conservation
└── figures/
```

### Cross-Project Dependencies

This project requires cached data from two upstream projects:

| File | Source Project | Description |
|------|--------------|-------------|
| `conservation_vs_fitness/data/fb_pangenome_link.tsv` | conservation_vs_fitness | Gene-to-cluster links with conservation status |
| `conservation_vs_fitness/data/organism_mapping.tsv` | conservation_vs_fitness | FB orgId → pangenome species clade mapping |
| `conservation_vs_fitness/data/pangenome_metadata.tsv` | conservation_vs_fitness | Clade size, core counts |
| `conservation_vs_fitness/data/seed_annotations.tsv` | conservation_vs_fitness | SEED functional annotations (34 organisms) |
| `conservation_vs_fitness/data/seed_hierarchy.tsv` | conservation_vs_fitness | SEED functional category hierarchy |
| `fitness_modules/data/modules/*_gene_membership.csv` | fitness_modules | ICA module membership (32 organisms) |
| `fitness_modules/data/modules/*_module_annotations.csv` | fitness_modules | Module functional enrichments |
| `fitness_modules/data/module_families/module_families.csv` | fitness_modules | Module → family mapping |
| `fitness_modules/data/module_families/family_annotations.csv` | fitness_modules | Family consensus annotations |

## Key Definitions

- **Essential gene**: Protein-coding gene (type=1 in FB gene table) with zero entries in `genefitness` — no viable transposon mutants were recovered during RB-TnSeq library construction. This is an upper bound on true essentiality; some genes may lack insertions due to being short or in regions with poor transposon coverage.
- **Ortholog group (OG)**: Connected component in the BBH (bidirectional best BLAST hit) graph across organisms. Each OG represents a family of orthologous genes.
- **Universally essential family**: OG where every member gene is essential in its respective organism.
- **Variably essential family**: OG with at least one essential and one non-essential member.

## Key Findings

### Essential Gene Landscape (NB01)
- **221,005 genes** across 48 organisms, **41,059 essential** (18.6%)
- Essentiality rate ranges from 12.2% (*Pedo557*) to 29.7% (*Magneto*)
- **2,838,750 BBH pairs** yield **17,222 ortholog groups** spanning all 48 organisms

### Essential Gene Families (NB02)
- **859 universally essential families** (5.0%) — essential in every organism where they have members. Of these, **839 are strict single-copy families** (copy ratio ≤1.5, no non-essential paralogs); 20 contain paralogs where at least one copy per organism is essential. Dominated by ribosomal proteins, tRNA synthetases, cell wall biosynthesis, and DNA replication.
- **15 families essential in ALL 48 organisms** — the absolute core of bacterial life (rpsC, rplW, groEL, pyrG, fusA, rplK, valS, rplB, rplA, rpsJ, rplF, rpsI, rpsM, rps11, SelGGPS)
- **4,799 variably essential families** (27.9%) — essential in some organisms, non-essential in others. Median essentiality penetrance is 33%.
- **7,084 orphan essential genes** with no orthologs — 58.7% hypothetical, the highest-priority targets for functional discovery
- Universally essential genes are only 8.2% hypothetical vs 58.7% for orphan essentials
- Essential genes are shorter than non-essential (median 675 bp vs 885 bp); 17.8% of essentials are <300 bp, suggesting some false positives from transposon insertion bias

### Function Prediction for Hypothetical Essentials (NB03)
- **8,297 hypothetical essential genes** across 48 organisms (20.2% of all essentials)
- **1,382 function predictions** for hypothetical essentials via ortholog-module transfer (35.3% of predictable targets)
- All 1,382 predictions are family-backed (supported by cross-organism module conservation)
- Top predicted functions: TIGR00254 (signal transduction), PF00460 (flagellar basal body rod), PF00356 (lactoylglutathione lyase)

### Conservation Architecture (NB04)
- Universally essential genes are **91.7% core** vs 80.7% for non-essential genes — the strongest conservation enrichment
- **71% of universally essential families are 100% core**; 82% are ≥90% core
- Variably essential families are 88.9% core — between universal and never-essential
- Orphan essentials (no orthologs) are only **49.5% core** — they are strain-specific essential functions
- There is a weak positive correlation between essentiality penetrance and core fraction (rho=0.123, p=1.6e-17) among variably essential families: families essential in more organisms tend to be slightly more core (97.1% for >80% penetrance vs 92.8% for <20%)
- Clade size does NOT predict essentiality rate (rho=-0.13, p=0.36)

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

### Conservation Architecture: Essential = Core = Selected

The conservation hierarchy — universally essential (91.7% core) > variably essential (88.9%) > never essential (81.7%) > orphan essential (49.5%) — reveals that essentiality breadth predicts pangenome conservation. This extends the conservation_vs_fitness finding (essential genes are 86.1% core, OR=1.56) by showing the enrichment is strongest for genes essential across many organisms. The 71% of universally essential families that are 100% core represent the deepest level of purifying selection detectable in this dataset.

### Literature Context

- **Koonin (2003)** estimated ~60 universally conserved proteins across all life, primarily translation-related. Our 15 pan-bacterial essential families are consistent — they are dominated by ribosomal proteins and translation machinery, but also include cell wall biosynthesis and nucleotide metabolism genes that may be bacteria-specific essentials.
- **Gil et al. (2004)** proposed a ~206-gene minimal bacterial gene set based on computational comparison of reduced genomes. Our 859 universally essential families is larger because it includes genes essential in free-living bacteria with larger genomes, not just obligate symbionts with minimal genomes.
- **Rosconi et al. (2022)** demonstrated context-dependent essentiality across 36 *S. pneumoniae* strains. Our work extends this concept from within-species to cross-species variation: the same gene can be essential in *Methanococcus* but dispensable in *Pseudomonas*, depending on metabolic context.
- **Duffield et al. (2010)** identified 52 conserved essential proteins across 14 bacterial genomes as drug targets. Our approach is complementary but uses experimental (RB-TnSeq) essentiality data across 48 organisms rather than computational prediction, providing empirical validation of conservation patterns.
- **Price et al. (2018)** generated the Fitness Browser data used here. Our work adds a cross-organism essentiality dimension to their fitness data, enabling function prediction for essential genes that are outside the reach of fitness profiling.
- **Hutchison et al. (2016)** found 149 essential genes of unknown function in their synthetic minimal genome. Our 7,084 orphan essentials (58.7% hypothetical) show this problem is universal across bacteria, not specific to *Mycoplasma*.

### Limitations

- **Essential gene definition is an upper bound**: Genes without transposon insertions may lack insertions due to small size, AT-rich sequence, or scaffold edge effects, not true essentiality. A gene length filter could reduce false positives.
- **BBH orthology is conservative**: Bidirectional best BLAST hits miss paralogs, gene fusions, and distant homologs. Some "orphan essentials" may have undetected orthologs with diverged sequences.
- **Connected components can over-merge**: Transitive connections in the BBH graph can merge unrelated genes into the same ortholog group, particularly for multi-domain proteins. This could misclassify some families.
- **Essentiality is condition-dependent**: RB-TnSeq essentiality is defined under specific library construction conditions (typically rich media). Genes essential only under stress would be missed. Conversely, genes essential in rich media may be dispensable in natural environments.
- **48 organisms is taxonomically limited**: The Fitness Browser organisms are biased toward culturable Proteobacteria. Essentiality patterns in uncultured lineages, Actinobacteria, or Firmicutes are underrepresented.
- **Module transfer predictions are indirect**: Function predictions for essential genes come from non-essential orthologs in other organisms. The essential gene's function may have diverged from its non-essential ortholog.

## Future Directions

1. **Characterize the 7,084 orphan essentials** — Are they on mobile elements? Recently acquired? Rapidly evolving? What functional categories do they represent?
2. **Validate predictions experimentally** — The 1,382 module-transfer predictions could be tested via CRISPRi knockdown under specific conditions predicted by the module context.
3. **Connect to metabolic networks** — For variably essential families, determine whether essentiality correlates with metabolic pathway completeness (e.g., is a gene essential only when an alternative pathway is absent?).
4. **Expand taxonomic coverage** — As the Fitness Browser adds more organisms, re-run the analysis to test whether the 15 pan-essential families remain universal.
5. **Compare to DEG database** — Cross-reference with the Database of Essential Genes (Luo et al., 2014) to identify families that are essential in non-FB organisms.

## Visualizations

| Figure | Description |
|--------|-------------|
| `essential_families_overview.png` | 4-panel: family classification counts, size distribution by class, essentiality penetrance, annotation status |
| `essential_families_heatmap.png` | Essentiality status across 48 organisms for top 40 universally essential families |
| `conservation_architecture.png` | 4-panel: core fraction by class, family-level core distribution, penetrance vs conservation, clade size vs essentiality |

## Data Files

| File | Description |
|------|-------------|
| `all_essential_genes.tsv` | Essential status for 221,005 genes across 48 organisms (regenerate with `src/extract_data.py`) |
| `all_bbh_pairs.csv` | 2.84M BBH pairs across 48 organisms (regenerate with `src/extract_data.py`) |
| `all_ortholog_groups.csv` | 179,237 gene-OG assignments across 17,222 ortholog groups |
| `essential_families.tsv` | Per-family essentiality classification (17,222 families) |
| `essential_predictions.tsv` | 1,382 function predictions for hypothetical essential genes |
| `family_conservation.tsv` | Per-family pangenome conservation metrics (16,758 families with links) |

## Reproduction

**Prerequisites**: Python 3.10+, pandas, numpy, matplotlib, scipy, networkx, scikit-learn. BERDL Spark Connect for data extraction.

```bash
cd projects/essential_genome
pip install -r requirements.txt

# Step 1: Extract data from Spark (requires BERDL access)
python3 src/extract_data.py

# Step 2-4: Run analysis notebooks (local, no Spark needed)
jupyter nbconvert --to notebook --execute --inplace notebooks/02_essential_families.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_function_prediction.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/04_conservation_architecture.ipynb
```

Requires cached data from `conservation_vs_fitness` and `fitness_modules` projects (see Cross-Project Dependencies above).

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
