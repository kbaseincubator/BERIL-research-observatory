# Research Plan: Annotation-Gap Discovery via Phenotype-Fitness-Pangenome-Gapfilling Integration

## Research Question

Can we systematically identify and resolve metabolic annotation gaps in bacterial genomes by integrating experimental growth phenotypes, gene fitness data, metabolic model gapfilling, pangenome context, and sequence homology to gapfilled-reaction exemplars?

## Hypothesis

- **H0**: Gapfilled reactions required to reconcile observed growth phenotypes with metabolic model predictions cannot be assigned to specific genes using fitness data, pangenome co-occurrence, and exemplar sequence homology — the annotation gaps are genuine knowledge gaps with no tractable candidates.
- **H1**: A significant fraction of gapfilled reactions can be confidently assigned to specific genes by triangulating (A) BLAST/DIAMOND homology to known exemplar sequences, (B) gene fitness evidence under the relevant carbon source, and (C) pangenome co-occurrence with known pathway genes — resolving annotation gaps and improving model-phenotype agreement.

## Literature Context

Genome-scale metabolic models (GEMs) built from automated annotation pipelines (RAST, Prokka, Bakta) routinely require gapfilling to match observed growth phenotypes. These gapfilled reactions represent "annotation gaps" — metabolic functions the organism demonstrably performs but whose responsible genes remain unidentified. Prior work has addressed this through:

- **Gapfilling algorithms** (Henry et al. 2010, *Nat Biotechnol*): ModelSEED gapfilling adds minimal reactions to enable growth
- **Fitness-based gene assignment** (Deutschbauer et al. 2011; Price et al. 2018): RB-TnSeq fitness data identifies condition-specific gene importance
- **GapMind** (Price et al. 2020): Pathway completeness predictions identify missing steps
- **Pangenome co-occurrence**: Genes that co-occur across species with known pathway genes are likely functionally related

No prior study has systematically integrated all four evidence types (gapfilling + fitness + pangenome + homology) to resolve annotation gaps at scale across multiple organisms and carbon sources.

## Approach

### Overview

1. **Select ~20 genomes** from Fitness Browser organisms with rich carbon-source experiment coverage, cross-referenced with BacDive growth phenotypes
2. **Build draft metabolic models** using ModelSEEDpy from RAST/Bakta annotations
3. **Simulate growth** on each carbon source via FBA (COBRApy) and compare to observed phenotypes
4. **Conditional gapfilling** for false-negative cases (observed growth, predicted no-growth)
5. **GapMind pathway analysis** to identify missing pathway steps independently
6. **Fitness-guided candidate identification** using RB-TnSeq data under carbon-source conditions
7. **Exemplar BLAST** of gapfilled-reaction protein sequences against target proteomes
8. **Triangulated gene-reaction assignment** with confidence scoring
9. **Validation** by re-running FBA with new GPRs and measuring improvement

### Data Sources

| Source | Database | What it provides |
|--------|----------|-----------------|
| Growth phenotypes | `kescience_fitnessbrowser.experiment` | Carbon source conditions with fitness data |
| Growth phenotypes | `kescience_bacdive.metabolite_utilization` | Binary +/- utilization for 988K strain-compound pairs |
| Gene fitness | `kescience_fitnessbrowser.genefitness` | Per-gene fitness scores under carbon source conditions |
| Metabolic models | ModelSEEDpy (installed locally) | Draft GEM construction from genome annotations |
| FBA/Gapfilling | COBRApy (installed locally) | Flux balance analysis and conditional gapfilling |
| Reference biochemistry | `kbase_msd_biochemistry` | 56K reactions, 46K molecules, stoichiometry |
| Pathway predictions | `kbase_ke_pangenome.gapmind_pathways` | Carbon + amino acid pathway completeness per genome |
| Pangenome clusters | `kbase_ke_pangenome.gene_cluster` | Gene families, presence/absence, representative sequences |
| Functional annotations | `kbase_ke_pangenome.eggnog_mapper_annotations` | EC, KEGG, COG for gene clusters |
| Protein annotations | `kbase_ke_pangenome.bakta_annotations` | EC, UniRef, product descriptions |
| Cross-references | `kbase_ke_pangenome.bakta_db_xrefs` | UniRef, KEGG, Pfam cross-references (572M rows) |
| Exemplar sequences | UniProt/Swiss-Prot via UniRef mappings | Reviewed protein sequences for gapfilled reactions |

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|-------|---------|----------------|-----------------|
| `kescience_fitnessbrowser.experiment` | Identify carbon source experiments | ~7,500 | `expGroup = 'carbon source'` |
| `kescience_fitnessbrowser.organism` | Organism metadata + genome IDs | 48 | Full scan |
| `kescience_fitnessbrowser.genefitness` | Gene fitness per condition | 27M | Filter by `orgId` |
| `kescience_fitnessbrowser.gene` | Gene annotations per organism | ~200K | Filter by `orgId` |
| `kescience_bacdive.metabolite_utilization` | Growth +/- per strain per compound | 988K | Filter by organism |
| `kbase_ke_pangenome.genome` | Genome metadata | 293K | Filter by clade |
| `kbase_ke_pangenome.gene_cluster` | Cluster reps + sequences | 132M | Filter by `gtdb_species_clade_id` |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | EC/KEGG per cluster | 93M | Filter by `query_name` |
| `kbase_ke_pangenome.gapmind_pathways` | Pathway completeness | 305M | Filter by `genome_id` |
| `kbase_msd_biochemistry.reaction` | Reaction definitions | 56K | Full scan |
| `kbase_msd_biochemistry.reagent` | Stoichiometry | 262K | Full scan |

### Key Queries

1. **Carbon source experiment inventory**:
```sql
SELECT orgId, condition_1, COUNT(*) as n_exps
FROM kescience_fitnessbrowser.experiment
WHERE expGroup = 'carbon source'
GROUP BY orgId, condition_1
ORDER BY orgId, n_exps DESC
```

2. **Genome-to-pangenome linking** (for FB organisms):
```sql
SELECT o.orgId, o.taxonomyId, g.genome_id, g.gtdb_species_clade_id
FROM kescience_fitnessbrowser.organism o
JOIN kbase_ke_pangenome.genome g ON ...
-- Join via taxonomy or DIAMOND link table from conservation_vs_fitness
```

3. **GapMind pathway completeness for target genomes**:
```sql
SELECT genome_id, pathway, metabolic_category, score_category
FROM kbase_ke_pangenome.gapmind_pathways
WHERE genome_id IN (...)
```

### Performance Plan

- **Tier**: Direct Spark SQL on JupyterHub
- **Estimated complexity**: Moderate-Complex (multi-table joins, 20-genome scope)
- **Known pitfalls**:
  - FB columns are all strings — CAST before numeric comparisons
  - GapMind `metabolic_category` values are `'aa'` and `'carbon'`, not full names
  - GapMind has multiple rows per genome-pathway pair — take MAX score
  - Gene clusters are species-specific — use COG/KEGG for cross-species comparisons
  - `gapmind_pathways.clade_name` uses `gtdb_species_clade_id` format
  - GapMind genome IDs lack RS_/GB_ prefix

## Analysis Plan

### Notebook 1: Genome and Carbon Source Selection (`01_genome_carbon_selection.ipynb`)
- **Goal**: Select ~20 FB organisms with best carbon-source coverage; cross-reference BacDive
- **Queries**: FB `experiment` (expGroup='carbon source'), FB `organism`, BacDive `metabolite_utilization`
- **Expected output**: `data/genome_manifest.tsv`, `data/carbon_source_panel.tsv`
- **Deliverables**: Summary stats, taxonomic distribution, carbon source overlap matrix

### Notebook 2: Model Building and Baseline FBA (`02_model_building_fba.ipynb`)
- **Goal**: Build draft ModelSEED models for each genome; run FBA across carbon sources
- **Tools**: ModelSEEDpy, COBRApy
- **Expected output**: `data/models/` (SBML files), `data/baseline_fba_results.tsv`
- **Deliverables**: Confusion matrices, baseline accuracy heatmap (Fig 2)

### Notebook 3: Conditional Gapfilling (`03_gapfilling.ipynb`)
- **Goal**: Gapfill false-negative cases (observed growth, predicted no-growth)
- **Tools**: COBRApy gapfilling
- **Expected output**: `data/gapfill_events.tsv`, `data/gapfilled_reactions.tsv`
- **Deliverables**: Per carbon source gapfill burden (Fig 3), subsystem distribution

### Notebook 4: GapMind Pathway Analysis (`04_gapmind_analysis.ipynb`)
- **Goal**: Identify missing pathway steps via GapMind; compare to gapfilled reactions
- **Queries**: `gapmind_pathways` for target genomes
- **Expected output**: `data/gapmind_gaps.tsv`, `data/gapmind_vs_gapfill_concordance.tsv`
- **Deliverables**: Concordance matrix, Venn diagram of gap sources

### Notebook 5: Pangenome Context and Fitness Evidence (`05_pangenome_fitness.ipynb`)
- **Goal**: Build presence/absence matrix for target species; extract fitness profiles for carbon sources
- **Queries**: `gene_cluster`, `gene_genecluster_junction`, `genefitness`
- **Expected output**: `data/presence_absence_matrix.tsv`, `data/fitness_support.tsv`
- **Deliverables**: Nearest-neighbor mapping, candidate gene lists per gapfilled reaction

### Notebook 6: Exemplar BLAST and Gene Assignment (`06_exemplar_blast.ipynb`)
- **Goal**: Retrieve exemplar sequences for gapfilled reactions; DIAMOND against proteomes; triangulate evidence
- **Tools**: DIAMOND blastp, ModelSEED reaction-to-EC mapping, UniProt exemplars
- **Expected output**: `data/blast_hits.tsv`, `data/reaction_gene_candidates.tsv`
- **Deliverables**: Confidence-scored gene-reaction assignments (High/Medium/Low)

### Notebook 7: Validation and Final Analysis (`07_validation_analysis.ipynb`)
- **Goal**: Insert new GPRs into models; re-run FBA; quantify improvement
- **Expected output**: `data/final_fba_results.tsv`, `data/delta_metrics.tsv`
- **Deliverables**: Before/after comparison plots (Fig 4), case studies (Fig 6)

### Notebook 8: Figures and Reporting (`08_figures_report.ipynb`)
- **Goal**: Generate all publication-quality figures; compute statistics
- **Expected output**: `figures/*.png`, enrichment analysis, robustness analysis
- **Deliverables**: All 6+ figures, statistical tables, manuscript outline

## Expected Outcomes

- **If H1 supported**: A significant fraction (>30%) of gapfilled reactions gain confident gene assignments through the triangulation approach. This demonstrates that annotation gaps are largely resolvable with existing data when properly integrated, and the pipeline is generalizable to other organisms.
- **If H0 not rejected**: Few gapfilled reactions can be confidently assigned, indicating that most annotation gaps represent genuine biological unknowns — novel enzyme families, moonlighting proteins, or non-homologous isofunctional enzymes (NISEs). These become high-priority targets for experimental characterization.
- **Potential confounders**:
  - Model quality: draft models from automated pipelines may have systematic errors
  - Media definition: carbon source identity mapping between FB experiments and model exchange reactions
  - Fitness threshold sensitivity: results may depend on chosen |fitness| and q-value cutoffs
  - GapMind scope: only covers ~80 pathways (amino acid + carbon), not full metabolism
  - Gapfilling non-uniqueness: multiple possible gapfill solutions may exist

## Confidence Scoring Framework

Gene-reaction assignments will be scored:

| Level | Criteria | Expected Fraction |
|-------|----------|-------------------|
| **High** | BLAST hit (e-value ≤ 1e-10, coverage ≥ 70%, %id ≥ 30%) AND fitness support (\|fit\| ≥ 1, q ≤ 0.05) | ~15-25% |
| **Medium** | Strong BLAST hit + pangenome co-occurrence support (no direct fitness) | ~10-20% |
| **Low** | BLAST hit only (no fitness or pangenome support) | ~20-30% |
| **Unresolved** | No convincing BLAST hit | ~30-50% |

## Revision History

- **v1** (2026-05-07): Initial plan

## Authors

- Janaka N. Edirisinghe (ORCID: 0000-0003-2493-234X), Data Science and Learning Division, Argonne National Laboratory, Lemont, IL, 60439, USA
