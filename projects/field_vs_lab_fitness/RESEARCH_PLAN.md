# Research Plan: Field vs Lab Gene Importance in *Desulfovibrio vulgaris* Hildenborough

## Research Question

Which genes matter for survival under environmentally-realistic conditions but appear dispensable in the lab, and vice versa? Do field-relevant fitness effects predict pangenome conservation better than lab-only effects?

## Hypotheses

- **H1**: Genes with strong fitness effects under field-relevant conditions (uranium, mercury, sulfate reduction, nitrate) are more likely to be in the core genome than genes important only under lab conditions (antibiotics, rich media).
- **H2**: ICA fitness modules responding to field-relevant conditions are more conserved (higher core %) than modules responding to lab-only conditions.
- **H3**: "Ecologically essential" genes (field-important + core) define a functional core relevant to environmental survival distinct from "lab essentials."

- **H0**: Conservation patterns are independent of condition type -- genes important for field and lab conditions show equivalent core genome fractions. Condition relevance does not improve prediction of pangenome conservation beyond overall fitness magnitude.

## Literature Context

DvH is the primary model organism of the ENIGMA (Ecosystems and Networks Integrated with Genes and Molecular Assemblies) project studying microbial communities at the Oak Ridge Field Research Center (FRC). The FRC site is contaminated with uranium, mercury, nitrate, and other heavy metals from Cold War-era activities.

Kuehl et al. (2014) characterized a comprehensive transposon mutant library for DvH with fitness data across hundreds of conditions. Price et al. (2018) expanded this into the Fitness Browser with 757 DvH experiments. Borchert et al. (2019) used ICA to decompose fitness data into functional modules.

Our prior work (conservation_vs_fitness) showed essential genes are enriched in core clusters (OR=1.56), and fitness_effects_conservation demonstrated a 16-percentage-point conservation gradient from essential to neutral genes. This project tests whether the ecological relevance of conditions modulates this gradient.

## Query Strategy

### Tables Required

All data is pre-cached from upstream projects. No new Spark queries needed for NB02-04.

| Asset | Source | Rows | Notes |
|-------|--------|------|-------|
| DvH fitness matrix | `fitness_modules/data/matrices/DvH_fitness_matrix.csv` | 2,741 x 757 | Gene x experiment fitness scores |
| DvH experiments | `fitness_modules/data/annotations/DvH_experiments.csv` | 757 | Condition metadata |
| FB-pangenome link | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | 177,863 (3,206 DvH) | Gene-to-cluster links |
| Essential genes | `conservation_vs_fitness/data/essential_genes.tsv` | 153,143 (3,403 DvH) | Essentiality status |
| ICA module membership | `fitness_modules/data/modules/DvH_gene_membership.csv` | 2,741 x 52 | Binary membership matrix |
| Module conditions | `fitness_modules/data/modules/DvH_module_conditions.csv` | ~39,000 | Module-condition activity scores |
| Module annotations | `fitness_modules/data/modules/DvH_module_annotations.csv` | ~200 | Functional enrichments |
| SEED annotations | `conservation_vs_fitness/data/seed_annotations.tsv` | ~125,000 | Functional annotations |

### NB01 Queries (ENIGMA CORAL -- Spark)

```sql
SELECT * FROM enigma_coral.sdt_tnseq_library LIMIT 50
SELECT * FROM enigma_coral.sdt_dubseq_library LIMIT 50
SELECT * FROM enigma_coral.sdt_strain LIMIT 100
SELECT * FROM enigma_coral.sdt_condition LIMIT 100
SELECT * FROM enigma_coral.sdt_sample LIMIT 50
SELECT * FROM enigma_coral.sdt_community LIMIT 50
SELECT * FROM enigma_coral.sdt_location LIMIT 50
SELECT COUNT(*) FROM enigma_coral.sdt_taxon WHERE sdt_taxon_name LIKE '%Desulfovibrio%'
```

### Performance Plan

- **NB01**: Spark Connect on JupyterHub -- small discovery queries
- **NB02-04**: Local only -- all data pre-cached, fits in memory

## Analysis Plan

### NB01: ENIGMA CORAL Discovery (Spark)

**Goal**: Discover what's in the undocumented ENIGMA tables.

Survey `sdt_tnseq_library`, `sdt_dubseq_library`, `sdt_strain`, `sdt_condition`, `sdt_sample`, `sdt_community`, `sdt_location`, `sdt_taxon` tables. Sample `ddt_brick*` tables to understand numerical data format.

**Expected output**: Summary of ENIGMA data availability, assessment of whether ENIGMA adds data beyond the Fitness Browser.

### NB02: Condition Classification (local)

**Goal**: Classify DvH's 757 experiments into ecological relevance categories.

**Classification scheme** (based on Oak Ridge FRC contaminants and DvH ecology):

| Category | Conditions | Rationale |
|----------|-----------|-----------|
| Field-core | Sulfate, lactate, H2, formate, pyruvate | DvH's primary metabolism in situ |
| Field-stress | Uranium, mercury, chromium, nitrate, nitrite, oxygen, NO | FRC contaminants and stresses |
| Heavy metals | Cobalt, nickel, zinc, copper, manganese, selenium | Metal stress (environmental) |
| Lab-nutrient | Amino acids, organic acids, carbon sources | Nutrient screening (lab-typical) |
| Lab-antibiotic | Tetracycline, chloramphenicol, spectinomycin, cefoxitin | Purely lab conditions |
| Lab-other | DMSO, PEG, formamide, casamino acids | Lab reagents |

**Expected output**: `data/experiment_classification.csv`

### NB03: Field vs Lab Fitness x Conservation (local)

**Goal**: Test whether field-relevant fitness effects predict pangenome conservation better than lab effects.

**Analyses**:
1. Condition-class fitness profiles per gene
2. Conservation by condition importance (Fisher exact tests)
3. Specificity analysis: field-specific vs lab-specific vs universally important genes
4. Logistic regression: `is_core ~ mean_field_fitness + mean_lab_fitness + gene_length`
5. ROC analysis: compare AUC for predicting core status

**Expected output**: 4 figures, statistical test results

### NB04: Module-Level Analysis (local)

**Goal**: Test whether ICA modules responding to field conditions are more conserved.

**Analyses**:
1. Module conservation score (fraction of member genes that are core)
2. Module ecological relevance (mean activity across field vs lab conditions)
3. Correlation: `module_core_fraction ~ module_field_activity`
4. Module characterization: ecological vs lab modules
5. Gene-level candidates from ecological modules

**Expected output**: 2 figures, module characterization table

## Known Pitfalls

- All Fitness Browser columns are strings -- use `CAST` for numeric comparisons
- `fillna(False)` produces object dtype -- must `.astype(bool)` after
- Condition classification requires manual review of `condition_1` values
- Multiple experiments per condition (replicates) -- use mean across replicates
- Some genes may have extreme fitness in one condition class due to few experiments
