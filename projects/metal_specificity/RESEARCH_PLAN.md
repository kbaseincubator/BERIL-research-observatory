# Research Plan: Metal-Specific vs General Stress Genes

## Research Question

Among the 12,838 genes identified as metal-important in the Metal Fitness Atlas, which are specifically required for metal tolerance vs general stress survival? Can we isolate a refined set of metal-specific genes that are the true metal resistance determinants — and do these show the expected accessory-genome enrichment that the broader set does not?

## Hypothesis

- **H0**: Metal-important genes are no more condition-specific than expected by chance; the 87.4% core enrichment reflects the true genetic architecture of metal tolerance.
- **H1**: The 87.4% core enrichment is driven by general stress genes (cell envelope, DNA repair, central metabolism) that are needed for many stresses. After removing genes also important under non-metal conditions, the remaining **metal-specific** genes are enriched in the accessory genome and represent the true metal resistance repertoire (efflux, sequestration, detoxification).

### Sub-hypotheses

- **H1a**: Genes important for metals AND non-metal stresses (antibiotics, osmotic, oxidative) are >90% core — these are general stress response genes.
- **H1b**: Genes important for metals but NOT for any non-metal stress are <80% core — recovering the accessory enrichment expected for specialized resistance mechanisms.
- **H1c**: Metal-specific genes are enriched for known metal resistance functions (efflux pumps, metal-binding proteins, CDF transporters) relative to general stress genes.
- **H1d**: The 149 novel metal candidates from the atlas are disproportionately metal-specific (not general stress genes), confirming they represent genuine metal biology discoveries.
- **H1e** (exploratory): Different metals differ in their ratio of metal-specific to general stress genes. Note: essential metals (Fe, Mo, W) have limited organism coverage (1-3 organisms each), so this comparison is underpowered and treated as exploratory.

## Literature Context

- The Metal Fitness Atlas (this observatory) found 87.4% core enrichment for metal-important genes (OR=2.08, p=4.3e-162), surprising because metal resistance was expected to be accessory-enriched.
- The atlas report itself noted: "the majority of metal fitness genes are core cellular processes vulnerable to metal disruption" and recommended isolating metal-specific genes as a future direction.
- Prior DvH work (field_vs_lab_fitness project) found condition-specific heavy-metal genes were the LEAST conserved class (71.2% core), consistent with accessory enrichment — but that analysis used a different methodology (ICA module-based condition specificity).
- Price et al. 2018 showed that many genes have fitness defects across many conditions ("general sick" genes).
- The counter_ion_effects project showed 39.8% overlap between metal-important and NaCl-stress genes, confirming substantial shared-stress biology.
- The Fitness Browser `specificphenotype` table (38,525 rows) already identifies genes with strong condition-specific fitness effects and can serve as an independent validation set.

## Data Sources

All data is available locally from prior projects — no Spark queries needed.

### Primary Data

| Source | File | Content |
|--------|------|---------|
| Metal Atlas | `metal_fitness_atlas/data/metal_important_genes.csv` | 12,838 metal-important gene records |
| Metal Atlas | `metal_fitness_atlas/data/metal_experiments.csv` | 559 metal experiments classified by metal |
| Fitness Modules | `fitness_modules/data/matrices/{org}_fitness_matrix.csv` | Full fitness matrices for 32 organisms (6,504 total experiments) |
| Fitness Modules | `fitness_modules/data/matrices/{org}_t_matrix.csv` | T-score matrices for significance |
| Fitness Modules | `fitness_modules/data/annotations/{org}_experiments.csv` | Experiment metadata with condition groups |

### Supporting Data

| Source | File | Content |
|--------|------|---------|
| Conservation | `conservation_vs_fitness/data/fb_pangenome_link.tsv` | 177,863 gene-to-pangenome links with core/accessory status |
| Ortholog Groups | `essential_genome/data/all_ortholog_groups.csv` | 179,237 gene-OG assignments |
| Novel Candidates | `metal_fitness_atlas/data/novel_metal_candidates.csv` | 149 novel metal gene families |
| Conserved Families | `metal_fitness_atlas/data/conserved_metal_families.csv` | 1,182 conserved metal families |
| SEED Annotations | `essential_genome/data/all_seed_annotations.tsv` | Functional annotations |
| ICA Modules | `fitness_modules/data/modules/{org}_module_*.csv` | ICA module definitions and condition activities |
| Counter Ion Effects | `counter_ion_effects/data/` | NaCl overlap analysis (checkpoint for validation) |

### Fitness Browser Tables (if needed for validation)

| Table | Content | Access |
|-------|---------|--------|
| `specificphenotype` | 38,525 genes with strong condition-specific phenotypes | REST API or Spark |

## Query Strategy

No BERDL queries required for primary analysis — all uses cached local data.
The `specificphenotype` table may be queried via REST API for validation in NB02.

### Performance Plan
- **Tier**: Local analysis (no Spark)
- **Estimated complexity**: Moderate — per-organism fitness matrix processing, cross-condition comparison
- **Known pitfalls**:
  - Fitness matrix columns are experiment IDs that must be matched to annotation files
  - T-score thresholds matter (|t|>4 for significance)
  - Different organisms have very different numbers of non-metal experiments (2 to 608), which biases absolute specificity thresholds — use rate-based metrics alongside absolute counts
  - Essential genes (~14% of protein-coding genes, ~82% core) are invisible in fitness data and cannot be classified — this biases conservation analysis toward core enrichment (same caveat as the Metal Atlas)
  - Core denominator must match the Metal Atlas's methodology (mapped genes only) for valid comparison

## Analysis Plan

### Notebook 1: Classify Experiments by Stress Category
- **Goal**: For each organism, classify ALL 6,504 experiments (559 metal + 5,945 non-metal) into stress categories: metal, antibiotic, osmotic, oxidative, carbon source, nitrogen source, pH, temperature, other
- **Method**: Parse experiment annotations; match condition_1 to stress categories using keyword matching; cross-validate metal classifications against `metal_fitness_atlas/data/metal_experiments.csv`
- **Expected output**: `data/experiment_classification.csv` — all 6,504 experiments classified by stress type and organism

### Notebook 2: Identify Metal-Specific vs General Stress Genes
- **Goal**: For each metal-important gene, determine whether it is also important under non-metal conditions
- **Method**:
  1. For each organism, load fitness and t-score matrices
  2. For each metal-important gene, compute fitness under all non-metal experiments
  3. Classify genes using **two complementary approaches**:
     - **Absolute threshold**: sick under non-metal condition = fit < -1 AND |t| > 4 for any single non-metal experiment
     - **Rate-based threshold**: fraction of non-metal experiments where gene is sick; classify as metal-specific if sick_rate < 5% across non-metal experiments
  4. Gene categories (using rate-based as primary):
     - **Metal-specific**: sick_rate < 5% across all non-metal experiments
     - **Metal+stress**: sick_rate ≥ 5% in non-metal stress experiments (antibiotic, osmotic, oxidative) but < 5% in non-stress (carbon/nitrogen source)
     - **General sick**: sick_rate ≥ 5% across ≥3 different non-metal condition categories
  5. Sensitivity analysis: vary the sick_rate threshold (1%, 2%, 5%, 10%) and report classification stability
  6. Cross-validate against `counter_ion_effects` NaCl overlap results as a checkpoint
  7. Where available, compare against the Fitness Browser `specificphenotype` table as an independent validation
- **Expected output**: `data/gene_specificity_classification.csv`, `figures/specificity_breakdown.png`, `figures/threshold_sensitivity.png`

### Notebook 3: Conservation Analysis — Metal-Specific vs General
- **Goal**: Test H1a/H1b — do metal-specific genes show different core/accessory distribution than general stress genes?
- **Method**:
  1. Join specificity classification with fb_pangenome_link (core/accessory status)
  2. **Match the Metal Atlas's denominator**: use mapped genes only, same is_core definition
  3. Compare % core for metal-specific vs metal+stress vs general sick genes
  4. Fisher exact test for each organism; meta-analysis across organisms (Cochran-Mantel-Haenszel)
  5. Stratify by metal type (essential vs toxic) — treat as exploratory given limited essential metal coverage
  6. **Note essential gene bias**: ~14% of genes are putatively essential, ~82% core, and invisible in fitness data. Report this caveat alongside all conservation comparisons.
- **Expected output**: `data/specificity_conservation.csv`, `figures/conservation_by_specificity.png`, `figures/conservation_by_metal_type.png`

### Notebook 4: Functional Enrichment & Module Analysis
- **Goal**: Test H1c/H1d — are metal-specific genes enriched for known metal resistance functions? Are the novel candidates metal-specific?
- **Method**:
  1. Map metal-specific genes to SEED annotations and ortholog groups
  2. Keyword enrichment: efflux, transporter, metal, pump, CDF, P-type ATPase, siderophore
  3. Compare functional composition of metal-specific vs general stress gene sets
  4. Test H1d: are the 149 novel candidates disproportionately metal-specific?
  5. **ICA module specificity analysis**: For organisms with ICA modules, score module activity under metal vs non-metal conditions. Identify "metal-specific modules" (high metal activity, low non-metal activity). Compare with per-gene specificity classification. This provides a complementary, threshold-independent view of metal specificity.
- **Expected output**: `data/specificity_functional_enrichment.csv`, `data/module_metal_specificity.csv`, `figures/functional_comparison.png`, `figures/module_specificity.png`

## Expected Outcomes

- **If H1 supported**: The 87.4% core enrichment is a composite signal. Metal-specific genes (~20-40% of the total) are accessory-enriched (<80% core), while general stress genes (~60-80%) are core-enriched (>90%). This resolves the apparent contradiction between the atlas finding and prior literature. The refined metal-specific gene set represents the true metal resistance repertoire — candidates for functional characterization and engineering.

- **If H0 not rejected**: Metal tolerance genuinely requires core cellular machinery — there is no "hidden" accessory signal. This would mean that metal resistance cannot be conferred by transferring a few genes; it requires the entire core stress response apparatus. This is itself an important finding: engineering metal-tolerant organisms requires more than adding resistance genes to a chassis.

- **Potential confounders**:
  - Definition of "metal-specific" depends on threshold choice — mitigated by sensitivity analysis across multiple thresholds
  - Some non-metal experiments may have metal contamination in the media
  - Organisms with few non-metal experiments (e.g., Miya with only 2 metal experiments out of 178 total) will have less power to classify specificity — mitigated by rate-based thresholds
  - General sick genes may include experimental artifacts (growth-rate-dependent fitness effects)
  - Essential genes (~14%, ~82% core) are absent from fitness data — biases conservation toward core enrichment in all categories

## Revision History
- **v1** (2026-02-27): Initial plan
- **v2** (2026-02-27): Incorporated plan review feedback: added rate-based thresholds alongside absolute counts to address experiment-count bias; clarified total experiment count (6,504 total = 559 metal + 5,945 non-metal); added `specificphenotype` table as validation; added ICA module specificity analysis; downgraded H1e to exploratory; added essential gene bias caveat; added counter_ion_effects cross-validation checkpoint

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy
