# Research Plan: Pan-Bacterial Metal Fitness Atlas

## Research Question

Across diverse bacteria subjected to genome-wide fitness profiling under metal stress, what is the genetic architecture of metal tolerance — is it encoded in the core or accessory genome, is it conserved or lineage-specific across species, and can fitness-validated metal tolerance genes predict capabilities in the broader pangenome?

## Hypothesis

- **H0**: Metal tolerance genes identified by RB-TnSeq are randomly distributed across core and accessory genomes, and cross-species conservation of metal fitness determinants is no greater than expected by chance.
- **H1**: Metal tolerance has a two-tier genetic architecture — general metal stress response is encoded in the core genome while specific metal resistance mechanisms (efflux, sequestration) are accessory — and conserved cross-species metal fitness gene families exist that can predict metal tolerance from genome content alone.

### Sub-hypotheses

- **H1a**: Genes important for tolerance to toxic metals (Co, Ni, Cu, Zn, Al) are enriched in the accessory genome relative to baseline, consistent with HGT-mediated acquisition. (Prior: DvH heavy-metal genes are 71.2% core vs 76.3% baseline.)
- **H1b**: Genes important for metal homeostasis under essential metal limitation (Fe, Mo, W) are enriched in the core genome, reflecting fundamental metabolic dependence.
- **H1c**: Cross-species conserved metal fitness gene families (ortholog groups with consistent metal phenotypes in ≥3 organisms) exist and are enriched for known metal resistance functions (efflux, metal-binding, redox).
- **H1d**: Hypothetical proteins with conserved metal fitness phenotypes across species represent novel metal biology genes that can be functionally annotated by this approach.

## Literature Context

No published study has performed a systematic cross-species, genome-wide fitness comparison for metal tolerance. The Fitness Browser (Price et al. 2018, *Nature*) contains RB-TnSeq data for 48 bacteria under ~570 metal-related experiments covering 16 metal categories (14 retained for analysis after excluding Platinum/Cisplatin and unresolved Metal_limitation), but cross-species metal analysis has not been attempted. Key context:

- **Price et al. (2018)** assigned phenotypes to thousands of genes of unknown function using RB-TnSeq across 32 bacteria, including metal stress conditions, but did not systematically compare metal determinants across species.
- **Carlson et al. (2019)** used Fitness Browser data to predict which organisms survive at the ENIGMA Oak Ridge metal-contaminated site, demonstrating lab-to-field prediction.
- **Trotter et al. (2023)** comprehensively characterized DvH via RB-TnSeq, the most metal-profiled organism in the database (12 metals).
- **Peng et al. (2022)** showed heavy metal resistance in Oak Ridge *Rhodanobacter* is acquired via HGT (accessory genome), consistent with H1a.
- **Our prior work** (field_vs_lab_fitness project) found DvH heavy-metal resistance genes are the least conserved condition class (71.2% core), while uranium/mercury stress genes are the most conserved (83.6% core), suggesting a two-tier architecture.
- **Rosconi et al. (2022)** showed gene essentiality is strain-dependent within pangenomes (*S. pneumoniae*), but not for metals.
- The bioleaching/biomining field (Vera et al. 2013; Quatrini & Johnson 2019) relies on genomics/transcriptomics without genome-wide fitness data. No Tn-seq for *Acidithiobacillus* or *Leptospirillum*.
- **BacMet database** (Pal et al. 2014) catalogs known metal resistance genes but lacks fitness-based validation.

**Gap**: No cross-species genome-wide fitness atlas for metal tolerance exists. This project fills that gap using the unique combination of Fitness Browser data, pangenome conservation from BERDL, and cross-organism ortholog groups.

## Data Sources

### Fitness Browser (`kescience_fitnessbrowser`)

~570 metal experiments across 48 organisms covering 13 metals:

| Metal | Experiments | Organisms | USGS Critical? |
|-------|------------|-----------|----------------|
| Cobalt | 89 | 27 | Yes |
| Nickel | 79 | 26 | Yes (class 1 ally) |
| Copper | 60 | 23 | No (but energy-critical) |
| Aluminum | 54 | 22 | Yes |
| Zinc | 52 | 17 | No (but energy-critical) |
| Iron | 45 | 3 | No |
| Tungsten | 42 | 1 (DvH) | Yes |
| Molybdenum | 39 | 1 (DvH) | No |
| Chromium | 11 | 2 | Yes |
| Uranium | 9 | 2 | Yes |
| Selenium | 9 | 1 (DvH) | No |
| Manganese | 6 | 1 (DvH) | Yes |
| Mercury | 5 | 1 (DvH) | No |

Key organisms: DvH (12 metals), psRCH2 (7 metals + Fe-Cu limitation), Cup4G11 (*Cupriavidus*, 3 metals), MR1 (*Shewanella*, 4 metals), 5 *Pseudomonas fluorescens* FW300 strains from Oak Ridge.

### Pangenome Database (`kbase_ke_pangenome`)

- 293K genomes, 27,690 species, 132M gene clusters
- Core/auxiliary/singleton classification per gene cluster
- eggNOG functional annotations (COG, KEGG, PFAM)
- Existing FB-pangenome link: 177,863 gene-to-cluster mappings for 44 organisms

### Reusable Data from Prior Projects

| Source | Asset | Use |
|--------|-------|-----|
| `conservation_vs_fitness` | `organism_mapping.tsv` (44 orgs → 154 clades) | FB-to-pangenome bridge |
| `conservation_vs_fitness` | `fb_pangenome_link.tsv` (177K links) | Gene-to-cluster conservation |
| `field_vs_lab_fitness` | `experiment_classification.csv` (757 DvH exps) | Template for metal classification |
| `field_vs_lab_fitness` | `gene_fitness_conservation.csv` (2,725 genes) | DvH baseline metal-conservation data |
| `fitness_modules` | `matrices/{org}_fitness_matrix.csv` (32 orgs) | Raw fitness data for metal extraction |
| `fitness_modules` | `annotations/{org}_experiments.csv` (32 orgs) | Experiment metadata for metal identification |
| `fitness_modules` | `modules/{org}_module_*.csv` (27+ orgs) | ICA modules for metal-responsive module analysis |
| `essential_genome` | `ortholog_groups.csv` (179K assignments) | Cross-organism gene family mapping |
| `essential_genome` | `essential_families.tsv` (17K families) | Essentiality context per family |
| `essential_genome` | `family_conservation.tsv` (16.7K families) | Pangenome conservation per family |

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_fitnessbrowser.genefitness` | Metal-condition fitness scores | 27M total; ~1M metal-relevant | Filter by orgId + expName for metal experiments |
| `kescience_fitnessbrowser.expcondition` | Map experiments to metal conditions | ~7.5K | Filter by condition_1 for metal compounds |
| `kescience_fitnessbrowser.experiment` | Experiment metadata | ~7.5K | Full scan (small) |
| `kescience_fitnessbrowser.ortholog` | Cross-organism BBH orthologs | ~1.15M | Filter by orgId1/orgId2 IN clause |
| `kbase_ke_pangenome.gene_cluster` | Core/aux/singleton status | 132M | Filter by species clade |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | Functional annotations | 93M | Filter by query_name (cluster IDs) |

### Key Queries

1. **Identify metal experiments across all organisms**:
```sql
SELECT orgId, expName, expDesc, expGroup, condition_1, concentration_1
FROM kescience_fitnessbrowser.expcondition
WHERE condition_1 LIKE '%chloride%'
   OR condition_1 LIKE '%sulfate%'
   OR condition_1 LIKE '%acetate%'
   OR condition_1 LIKE '%molybdat%'
   OR condition_1 LIKE '%tungstat%'
   OR condition_1 LIKE '%chromat%'
   OR condition_1 LIKE '%selenat%'
   OR expGroup = 'metal limitation'
```

2. **Extract fitness scores for metal experiments**:
```sql
SELECT orgId, locusId, expName, CAST(fit AS FLOAT) as fit, CAST(t AS FLOAT) as t
FROM kescience_fitnessbrowser.genefitness
WHERE orgId = '{org}' AND expName IN ('{metal_exp_list}')
```

### Performance Plan
- **Tier**: REST API for experiment metadata; Spark SQL for genefitness extraction
- **Estimated complexity**: Moderate (per-organism queries, small-to-medium result sets)
- **Known pitfalls**: All FB columns are strings (CAST required); `genefitness` is 27M rows (always filter by orgId)

## Analysis Plan

### Notebook 1: Metal Experiment Classification
- **Goal**: Identify and classify all metal-related experiments across all 48 FB organisms
- **Method**: Query `expcondition` table; match compound names to metals; classify by metal, concentration, organism
- **Expected output**: `data/metal_experiments.csv` — master table of all metal experiments with standardized metal names, organisms, concentrations
- **Validation**: Cross-check against cached experiment files in `fitness_modules/data/annotations/`

### Notebook 2: Metal Fitness Extraction
- **Goal**: Extract gene-level fitness scores for all metal experiments
- **Method**: For each organism × metal, query `genefitness` for identified metal experiments. Compute per-gene metal fitness summary: mean fitness, min fitness, number of sick experiments (fit < -1, |t| > 4), number of beneficial experiments
- **Expected output**: `data/metal_fitness_scores.csv` — gene × metal fitness summary for all organisms
- **Requires**: NB01 output (metal_experiments.csv)

### Notebook 3: Metal Fitness × Pangenome Conservation
- **Goal**: Test H1a/H1b — do metal-important genes show non-random core/accessory distribution?
- **Method**:
  1. Join metal fitness scores to `fb_pangenome_link.tsv` for conservation status
  2. For each organism × metal, classify genes as metal-important (mean fit < -1 or n_sick ≥ 2)
  3. Compare % core for metal-important vs all genes (Fisher exact test per organism)
  4. Stratify by metal type: toxic metals (Co, Ni, Cu, Zn, Al, Cr, Hg, Cd, U) vs essential metals (Fe, Mo, W, Mn, Se)
  5. Meta-analysis across organisms: is the two-tier pattern (accessory for toxic, core for essential) universal?
- **Expected output**: `data/metal_conservation_stats.csv`, `figures/metal_conservation_by_organism.png`, `figures/core_fraction_by_metal.png`
- **Statistical tests**: Fisher exact test per organism × metal; Cochran-Mantel-Haenszel for cross-organism trend; logistic regression with organism as random effect

### Notebook 4: Cross-Species Metal Fitness Families
- **Goal**: Test H1c/H1d — identify conserved metal fitness gene families
- **Method**:
  1. Map metal-important genes to ortholog groups (`essential_genome/data/ortholog_groups.csv`)
  2. For each ortholog family, count how many organisms show metal fitness phenotype
  3. Identify "conserved metal families" (metal-important in ≥3 organisms for same metal)
  4. Annotate with KEGG, COG, SEED, PFAM
  5. Identify "novel metal families" (conserved metal phenotype + hypothetical/unknown function)
  6. Compare to BacMet database of known metal resistance genes
- **Expected output**: `data/conserved_metal_families.csv`, `data/novel_metal_candidates.csv`, `figures/metal_family_conservation_heatmap.png`

### Notebook 5: Metal-Responsive ICA Modules
- **Goal**: Identify co-regulated gene modules activated by metal stress
- **Method**:
  1. For each organism with ICA modules (27+), score module activity under metal conditions using `module_conditions.csv`
  2. Identify modules with |activity| > 2 for any metal condition
  3. Map module genes to ortholog groups → identify "module families" with conserved metal response
  4. Compare module conservation (% core genes) for metal modules vs non-metal modules
- **Expected output**: `data/metal_modules.csv`, `figures/metal_module_activity_heatmap.png`

### Notebook 6: Pangenome-Scale Metal Tolerance Prediction
- **Goal**: Use conserved metal fitness families to predict metal tolerance across 27,690 species
- **Method**:
  1. For each conserved metal family, check presence/absence across all pangenome species via eggNOG annotations (COG, KEGG, PFAM)
  2. Build a "metal tolerance score" per species: fraction of conserved metal families present
  3. Validate: do known metal-tolerant species (bioleaching organisms, ENIGMA isolates) score higher?
  4. Identify species with high predicted metal tolerance that are not currently used for bioleaching — bioprospecting candidates
- **Expected output**: `data/species_metal_predictions.csv`, `figures/metal_tolerance_score_distribution.png`, `figures/bioprospecting_candidates.png`
- **Requires**: Spark on JupyterHub for pangenome-scale queries

### Notebook 7: Synthesis and Summary Figures
- **Goal**: Generate publication-quality figures summarizing the metal fitness atlas
- **Method**: Combine outputs from NB03-06 into summary visualizations
- **Expected output**: Key publication figures in `figures/`

## Expected Outcomes

- **If H1 supported**: Metal tolerance has a universal two-tier architecture across diverse bacteria — core genome provides baseline stress response while accessory genome provides specific resistance. Conserved metal fitness gene families serve as functional markers for predicting metal capabilities from genome content. Novel hypothetical proteins with conserved metal phenotypes represent new targets for metal biology research and bioleaching strain engineering.

- **If H0 not rejected**: Metal tolerance genetics are idiosyncratic to each species, with no conserved cross-species program. This would suggest metal adaptation proceeds primarily through species-specific regulatory rewiring rather than shared gene repertoires, which is itself an interesting finding for the bioleaching field.

- **Potential confounders**:
  - Variable metal concentrations across organisms may confound cross-species comparison (dose-response vs tolerance)
  - Phylogenetic non-independence: closely related organisms (e.g., multiple Pseudomonas strains) may inflate apparent conservation
  - Core/accessory classification depends on pangenome sampling depth, which varies by species
  - Metal fitness phenotypes may be condition-dependent (media, growth phase) rather than reflecting intrinsic tolerance

## Key References

1. Price MN et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature* 557:503-509.
2. Carlson HK et al. (2019). "The selective pressures on the microbial community in a metal-contaminated aquifer." *ISME J* 13:937-949.
3. Trotter VV et al. (2023). "Large-scale genetic characterization of DvH." *Front Microbiol* 14:1095132.
4. Peng M et al. (2022). "Genomic features and pervasive negative selection in Rhodanobacter." *Microbiol Spectr* 10:e0226321.
5. Rosconi F et al. (2022). "A bacterial pan-genome makes gene essentiality strain-dependent." *Nat Microbiol* 7:1580-1592.
6. Pal C et al. (2014). "BacMet: antibacterial biocide and metal resistance genes database." *Nucleic Acids Res* 42:D617-D624.
7. Mergeay M et al. (2003). "Ralstonia metallidurans, towards a catalogue of metal-responsive genes." *FEMS Microbiol Rev* 27:385-410.
8. Nies DH (2003). "Efflux-mediated heavy metal resistance in prokaryotes." *FEMS Microbiol Rev* 27:313-339.
9. Vera M et al. (2013). "Progress in bioleaching: mechanisms of bacterial metal sulfide oxidation." *Appl Microbiol Biotechnol* 97:7529-7541.
10. Wetmore KM et al. (2015). "Rapid quantification of mutant fitness in diverse bacteria by sequencing randomly bar-coded transposons." *mBio* 6:e00306-15.

## Revision History
- **v1** (2026-02-17): Initial plan

## Authors
- Paramvir Dehal, Lawrence Berkeley National Laboratory, US Department of Energy
