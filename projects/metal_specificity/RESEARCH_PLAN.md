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
- **H1e**: Different metals differ in their ratio of metal-specific to general stress genes, with essential metals (Fe, Mo, W) showing more specific genes than toxic metals (Co, Ni, Cu) which primarily disrupt general cellular processes.

## Literature Context

- The Metal Fitness Atlas (this observatory) found 87.4% core enrichment for metal-important genes (OR=2.08, p=4.3e-162), surprising because metal resistance was expected to be accessory-enriched.
- The atlas report itself noted: "the majority of metal fitness genes are core cellular processes vulnerable to metal disruption" and recommended isolating metal-specific genes as a future direction.
- Prior DvH work (field_vs_lab_fitness project) found condition-specific heavy-metal genes were the LEAST conserved class (71.2% core), consistent with accessory enrichment — but that analysis used a different methodology (ICA module-based condition specificity).
- Price et al. 2018 showed that many genes have fitness defects across many conditions ("general sick" genes).
- The counter_ion_effects project showed 39.8% overlap between metal-important and NaCl-stress genes, confirming substantial shared-stress biology.

## Data Sources

All data is available locally from prior projects — no Spark queries needed.

### Primary Data

| Source | File | Content |
|--------|------|---------|
| Metal Atlas | `metal_fitness_atlas/data/metal_important_genes.csv` | 12,838 metal-important gene records |
| Metal Atlas | `metal_fitness_atlas/data/metal_experiments.csv` | 559 metal experiments classified by metal |
| Fitness Modules | `fitness_modules/data/matrices/{org}_fitness_matrix.csv` | Full fitness matrices for 32 organisms |
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

## Query Strategy

No BERDL queries required — all analysis uses cached local data.

### Performance Plan
- **Tier**: Local analysis (no Spark)
- **Estimated complexity**: Moderate — per-organism fitness matrix processing, cross-condition comparison
- **Known pitfalls**: Fitness matrix columns are experiment IDs that must be matched to annotation files; t-score thresholds matter (|t|>4 for significance); different organisms have very different numbers of non-metal experiments

## Analysis Plan

### Notebook 1: Classify Experiments by Stress Category
- **Goal**: For each organism, classify ALL experiments into stress categories (metal, antibiotic, osmotic, oxidative, carbon source, nitrogen source, pH, temperature, other)
- **Method**: Parse experiment annotations; match condition_1 to stress categories using keyword matching
- **Expected output**: `data/experiment_classification.csv` — all 6,504 experiments classified by stress type

### Notebook 2: Identify Metal-Specific vs General Stress Genes
- **Goal**: For each metal-important gene, determine whether it is also important under non-metal conditions
- **Method**:
  1. For each organism, load fitness and t-score matrices
  2. For each metal-important gene, compute fitness under all non-metal experiments
  3. Classify genes as:
     - **Metal-specific**: important for metals but NOT for any non-metal condition (mean fit > -1 AND n_sick = 0 across all non-metal experiments)
     - **Metal+stress**: important for metals AND ≥1 non-metal stress (antibiotic, osmotic, oxidative)
     - **General sick**: important for metals AND ≥3 different non-metal condition categories
  4. Count fraction in each category per organism and per metal
- **Expected output**: `data/gene_specificity_classification.csv`, `figures/specificity_breakdown.png`

### Notebook 3: Conservation Analysis — Metal-Specific vs General
- **Goal**: Test H1a/H1b — do metal-specific genes show different core/accessory distribution than general stress genes?
- **Method**:
  1. Join specificity classification with fb_pangenome_link (core/accessory status)
  2. Compare % core for metal-specific vs metal+stress vs general sick genes
  3. Fisher exact test for each organism; meta-analysis across organisms
  4. Stratify by metal type (essential vs toxic)
- **Expected output**: `data/specificity_conservation.csv`, `figures/conservation_by_specificity.png`

### Notebook 4: Functional Enrichment — What Are the Metal-Specific Genes?
- **Goal**: Test H1c — are metal-specific genes enriched for known metal resistance functions?
- **Method**:
  1. Map metal-specific genes to SEED annotations and ortholog groups
  2. Keyword enrichment: efflux, transporter, metal, pump, CDF, P-type ATPase, siderophore
  3. Compare functional composition of metal-specific vs general stress gene sets
  4. Test H1d: are the 149 novel candidates disproportionately metal-specific?
- **Expected output**: `data/specificity_functional_enrichment.csv`, `figures/functional_comparison.png`

### Notebook 5: Refined Metal Tolerance Gene Set for IP
- **Goal**: Produce the refined list of metal-specific gene families for patent claims
- **Method**:
  1. Filter conserved metal families (1,182) to those that are metal-specific
  2. Re-rank by: n_organisms × n_metals × specificity_score
  3. Re-assess the top IP candidates (YebC, YfdZ, Mla/Yrb, DUF1043, RapZ, DUF39) — are they metal-specific or general stress?
  4. Identify any NEW high-value targets that emerge from specificity filtering
- **Expected output**: `data/refined_metal_targets.csv`, updated IP assessment

## Expected Outcomes

- **If H1 supported**: The 87.4% core enrichment is a composite signal. Metal-specific genes (~20-40% of the total) are accessory-enriched (<80% core), while general stress genes (~60-80%) are core-enriched (>90%). This resolves the apparent contradiction between the atlas finding and prior literature. The refined metal-specific gene set is the true patent target.

- **If H0 not rejected**: Metal tolerance genuinely requires core cellular machinery — there is no "hidden" accessory signal. This would mean that metal resistance cannot be conferred by transferring a few genes; it requires the entire core stress response apparatus. This is itself an important finding for the bioleaching field: you can't just add metal resistance genes to a chassis organism.

- **Potential confounders**:
  - Definition of "metal-specific" depends on threshold choice (fit < -1 across non-metal experiments)
  - Some non-metal experiments may have metal contamination in the media
  - Organisms with few non-metal experiments will have less power to classify specificity
  - General sick genes may include experimental artifacts (growth-rate-dependent fitness effects)

## Revision History
- **v1** (2026-02-27): Initial plan

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy
