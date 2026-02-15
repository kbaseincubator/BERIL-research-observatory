# Research Plan: The Pan-Bacterial Essential Genome

## Research Question

Which essential genes are conserved across bacteria, which are context-dependent, and can we predict function for uncharacterized essential genes using module context from non-essential orthologs?

## Hypothesis

- **H0**: Essential gene families are independent across organisms — essentiality in organism A does not predict essentiality of orthologs in organism B. Hypothetical essential genes cannot be functionally annotated via ortholog-module context.
- **H1**: A subset of essential gene families are universally essential across diverse bacteria, while others show context-dependent essentiality determined by genomic background. Non-essential orthologs in ICA fitness modules can transfer functional context to predict function for hypothetical essential genes.

## Literature Context

The concept of a minimal bacterial gene set has been explored computationally (Koonin 2000, 2003; Gil et al. 2004) and experimentally (Hutchison et al. 2016). Koonin estimated ~60 universally conserved proteins, primarily in translation. Gil et al. proposed ~206 genes as the minimal bacterial gene set. Hutchison et al. synthesized a 473-gene minimal *Mycoplasma* genome but found 149 essential genes (31%) of unknown function.

Context-dependent essentiality was demonstrated within a single species by Rosconi et al. (2022), who showed that the *S. pneumoniae* pan-genome makes gene essentiality "strain-dependent and evolvable." Our analysis extends this concept across 48 phylogenetically diverse species.

The Fitness Browser (Price et al. 2018) provides RB-TnSeq data across 48 organisms, and our prior projects built FB-pangenome links (conservation_vs_fitness) and ICA fitness modules (fitness_modules). This project synthesizes both into a cross-organism essentiality analysis.

Full references in `references.md`.

## Query Strategy

### Tables Required

| Table | Database | Purpose | Estimated Rows | Filter Strategy |
|-------|----------|---------|---------------|-----------------|
| `gene` | `kescience_fitnessbrowser` | All CDS genes (type=1) per organism | 228K | Filter by `orgId`, `type='1'` |
| `genefitness` | `kescience_fitnessbrowser` | Identify essentials (genes with no entries) | 27M | `DISTINCT orgId, locusId` per organism |
| `ortholog` | `kescience_fitnessbrowser` | BBH pairs across all organisms | ~2.8M (48 orgs) | Filter both `orgId1` and `orgId2` to target set |
| `seedannotation` | `kescience_fitnessbrowser` | Functional annotations | 177K | Per organism |
| `fb_pangenome_link.tsv` | Shared (conservation_vs_fitness) | Gene-to-cluster conservation | 177K | Pre-cached |
| `*_gene_membership.csv` | Shared (fitness_modules) | ICA module membership | ~31K genes | Pre-cached, 32 organisms |
| `*_module_annotations.csv` | Shared (fitness_modules) | Module functional enrichments | ~890 modules | Pre-cached |
| `module_families.csv` | Shared (fitness_modules) | Cross-organism module families | 156 families | Pre-cached |

### Key Queries

1. **Essential gene identification** (per organism):
```sql
-- All type=1 CDS genes
SELECT orgId, locusId, begin, end, gene, desc
FROM kescience_fitnessbrowser.gene
WHERE orgId = '{orgId}' AND type = '1'

-- Genes with fitness data (NOT essential)
SELECT DISTINCT orgId, locusId
FROM kescience_fitnessbrowser.genefitness
WHERE orgId = '{orgId}'
```
Essential = type=1 genes NOT in genefitness.

2. **BBH ortholog extraction**:
```sql
SELECT orgId1, locusId1, orgId2, locusId2, CAST(ratio AS FLOAT) as ratio
FROM kescience_fitnessbrowser.ortholog
WHERE orgId1 IN ({all_48_orgs}) AND orgId2 IN ({all_48_orgs})
```

### Performance Plan

- **Tier**: Mixed — Spark Connect for extraction, local for analysis
- **Estimated complexity**: Moderate (largest query is ortholog extraction at ~2.8M rows)
- **Known pitfalls**:
  - All FB columns are strings — use `CAST` for numeric comparisons
  - `fillna(False)` produces object dtype — must `.astype(bool)` after
  - Ortholog scope must match analysis scope (extract all 48 organisms)
  - Row-wise `.apply()` is slow — use merge-based lookups

## Analysis Plan

### Script: Data Extraction (`src/extract_data.py`)
- **Goal**: Extract essential gene status, BBH pairs, and SEED annotations for all 48 organisms. Build ortholog groups via networkx connected components.
- **Expected output**: `all_essential_genes.tsv`, `all_bbh_pairs.csv`, `all_ortholog_groups.csv`, `all_seed_annotations.tsv`

### Notebook 1: Essential Gene Families (`02_essential_families.ipynb`)
- **Goal**: Classify ortholog families as universally essential, variably essential, or never essential. Distinguish single-copy from multi-copy families. Functional characterization.
- **Expected output**: `essential_families.tsv`, overview figure, heatmap figure

### Notebook 2: Function Prediction (`03_function_prediction.ipynb`)
- **Goal**: Predict function for hypothetical essential genes by finding non-essential orthologs in ICA fitness modules and transferring module enrichment labels.
- **Expected output**: `essential_predictions.tsv`

### Notebook 3: Conservation Architecture (`04_conservation_architecture.ipynb`)
- **Goal**: Connect essential families to pangenome core/accessory status. Test whether universally essential families are always core. Analyze predictors of variable essentiality.
- **Expected output**: `family_conservation.tsv`, conservation figure

## Expected Outcomes

- **If H1 supported**: A subset of essential gene families will be universally essential across diverse bacteria, defining the irreducible core of bacterial life. Variably essential families will reveal context-dependent essentiality. Module transfer will predict function for a meaningful fraction of hypothetical essentials.
- **If H0 not rejected**: Essential gene identity would be largely random across organisms, with no conserved essential core and no predictive power from module context.
- **Potential confounders**:
  - Essentiality definition is an upper bound (short genes may lack insertions by chance)
  - Connected components can over-merge paralogous families
  - 48 organisms are taxonomically biased toward culturable Proteobacteria
  - Module transfer predictions are indirect (non-essential ortholog function may diverge)

## Revision History

- **v1** (2026-02-15): Initial plan — designed and executed in a single session. Covered all 48 FB organisms, 3 analysis notebooks, function prediction via module transfer.

## Authors

- **Paramvir S. Dehal** (ORCID: [0000-0001-5810-2497](https://orcid.org/0000-0001-5810-2497)) — Lawrence Berkeley National Laboratory
