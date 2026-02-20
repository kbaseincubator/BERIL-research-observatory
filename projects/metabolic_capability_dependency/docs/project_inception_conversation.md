# Metabolic Capability vs Dependency — Project Inception Conversation

**Date**: 2026-02-18
**Participants**: Sierra Moxon + Claude Code (AI co-scientist)

---

## Overview

This document captures the research project ideation and setup conversation that produced the Metabolic Capability vs Dependency project. It covers literature review, project selection, notebook design decisions, and initial scaffolding.

---

## Phase 1: Orientation & Ideation

### System Context

The BERIL Research Observatory (Microbial Discovery Forge) uses the BERDL Data Lakehouse — 35 databases across 9 tenants — to pursue scientific questions across microbial genomics, ecology, metabolic modeling, and multi-omics analysis.

Key resources:
- `kbase_ke_pangenome`: 293K genomes, 1B genes, 27K species pangenomes
- `kescience_fitnessbrowser`: 48 organisms, 27M fitness scores from RB-TnSeq
- `kbase_ke_pangenome.gapmind_pathways`: 305M rows, 80 metabolic pathway predictions
- `kbase_msd_biochemistry`: 56K reactions, 46K molecules (ModelSEED)
- `planetmicrobe_planetmicrobe`: 2K marine samples
- PhageFoundry: Species-specific genome browsers

### Existing Projects Reviewed

23 existing projects were reviewed, including:
- **Completed**: ecotype_analysis, pangenome_openness, cog_analysis, conservation_vs_fitness, fitness_effects_conservation, essential_genome, fitness_modules, core_gene_tradeoffs, costly_dispensable_genes, module_conservation, conservation_fitness_synthesis, env_embedding_explorer, ecotype_env_reanalysis, lab_field_ecology, field_vs_lab_fitness, cofitness_coinheritance
- **In progress**: pangenome_pathway_geography, fitness_modules
- **Already scaffolded**: metabolic_capability_dependency (current branch)

### Literature Review

A literature search across 5 research directions assessed novelty potential against BERDL's unique assets:

| Topic | Literature Maturity | BERDL Novelty |
|-------|-------------------|---------------|
| Pangenome metabolic capability vs dependency | Medium | **Very High** — 27K pangenomes + GapMind + fitness for 33+ organisms |
| Gene fitness essentiality cross-species | Medium | **High** — 48 organisms with quantitative fitness + pangenome conservation |
| Hypothetical protein function prediction | High activity | **High** — Fitness phenotypes for thousands of unannotated genes |
| Marine multi-omics ecology | High activity | **Medium** — PlanetMicrobe + NMDC + pangenome |
| Phage-host defense systems | Very active | **Medium-High** — PhageFoundry + pangenome accessory gene analysis |

Key literature cited:
1. Price MN et al. (2020). "GapMind: Automated Annotation of Amino Acid Biosynthesis." *mSystems* 5(3).
2. Price MN et al. (2018). "Filling gaps in bacterial amino acid biosynthesis pathways with high-throughput genetics." *PLOS Genetics* 14(1).
3. Morris JJ et al. (2012). "The Black Queen Hypothesis: Evolution of Dependencies through Adaptive Gene Loss." *mBio* 3(2).
4. Seif Y et al. (2025). "Rare metabolic gene essentiality is a determinant of microniche adaptation in E. coli." *PLOS Pathogens*.
5. Pangenome-derived GEMs for Lactobacillaceae (mSystems 2024), Klebsiella (Microbiology Society 2024), Bacillus subtilis (mSystems 2024).
6. PanKB knowledgebase (NAR 2024).
7. Gene essentiality is strain-dependent within a pan-genome (Nature Microbiology 2022).

**Key finding**: No study has attempted cross-species, pangenome-scale comparison of *predicted* metabolic capability versus *experimentally measured* metabolic dependency. BERDL is uniquely positioned for this.

---

## Phase 2: Project Selection

Four project ideas were presented:

1. **Metabolic Capability vs Dependency** (Recommended) — Already scaffolded on current branch. Highest novelty.
2. **Defense System Repertoires Across Pangenomes** — Map CRISPR/R-M/CBASS as core vs accessory.
3. **Fitness-Informed Dark Matter Annotation** — Predict function for unannotated genes using fitness modules.
4. **Marine Metabolic Potential** — First use of PlanetMicrobe + ModelSEED data.

**Selected**: Option 1 — Metabolic Capability vs Dependency.

---

## Phase 3: Data Availability Assessment

### Existing Assets
The project depends on upstream data from `conservation_vs_fitness`:
- `fb_pangenome_link.tsv` — 177,863 gene-cluster links (44 organisms, DIAMOND-based)
- `organism_mapping.tsv` — 44 FB → GTDB mappings
- `essential_genes.tsv` — Gene essentiality classification

**Finding**: These data files are NOT in git (generated on JupyterHub, too large to commit). Only notebooks, figures, and reports are committed.

**Decision**: Notebooks must be self-contained — NB01 re-extracts organism mappings from BERDL directly (simplified taxid-based approach), and checks for the upstream DIAMOND link table if available.

### Upstream Notebook Analysis

The `conservation_vs_fitness` NB01 (organism_mapping) and NB03 (build_link_table) were reviewed in detail:
- NB01 uses 3 strategies: NCBI taxid, NCBI organism name, scaffold accession
- NB03 resolves multi-clade ambiguities via DIAMOND hit counts
- Final link table: 177,863 rows, 44 organisms, 94.2% median coverage

### GapMind Schema

The `gapmind_pathways` table was analyzed:
- 305,471,280 rows
- Columns: genome_id, pathway, clade_name, metabolic_category, sequence_scope, nHi, nMed, nLo, score, score_category, score_simplified
- Score categories: complete, likely_complete, steps_missing_low, steps_missing_medium, not_present
- **Multiple rows per genome-pathway pair** — must aggregate with MAX
- genome_id format may differ from pangenome genome table (bare vs GTDB-prefixed)

---

## Phase 4: Notebook Design

### Architecture Decisions

1. **Self-contained extraction**: NB01 extracts everything from BERDL rather than depending on upstream data files. This makes the project independently reproducible.

2. **KEGG-to-GapMind mapping approach**: Since GapMind step-level data is not available in BERDL (only pathway-level scores), we use KEGG pathway annotations from eggNOG to map gene clusters to GapMind pathways. This is imperfect but practical.

3. **Two JupyterHub notebooks, three local**: NB01-02 require Spark; NB03-05 run locally from extracted CSVs.

4. **Classification scheme**:
   - **Active dependency**: pathway complete/likely_complete AND ≥1 gene is fitness-important or essential
   - **Latent capability**: pathway complete/likely_complete AND no fitness-important genes
   - **Absent**: pathway not_present or steps_missing_medium
   - **Partial**: pathway steps_missing_low
   - **Unmapped**: pathway complete but no genes assigned via KEGG

### Notebook Pipeline

| Notebook | Purpose | Environment | Key Outputs |
|----------|---------|-------------|-------------|
| 01_data_extraction | Extract organism mapping, GapMind scores, eggNOG annotations, fitness stats, species-level aggregates | JupyterHub | 7 CSV files |
| 02_pathway_gene_linking | Map pathways to genes via KEGG/EC, merge with fitness | JupyterHub | pathway_gene_fitness.csv |
| 03_pathway_classification | Classify pathways, statistical tests | Local | pathway_classifications.csv, 3 figures |
| 04_cross_species_patterns | Test H2 (Black Queen), H3 (metabolic ecotypes) | Local | cross_species_analysis.csv, 2 figures |
| 05_summary_figures | 5 publication-quality figures | Local | 5 PNG figures |

### Key Design Choices in Notebooks

**NB01 — Organism Mapping**: Uses simplified taxid-based matching (vs. full DIAMOND approach in upstream project). Checks GapMind genome_id format and reconciles with pangenome genome table. Extracts species-level GapMind aggregates for all 27K species in a single Spark job (~10-15 min).

**NB02 — Pathway-Gene Linking**: Defines KEGG pathway ID → GapMind pathway name mapping for 20 amino acid biosynthesis and 31 carbon source utilization pathways. Uses eggNOG KEGG_Pathway column to assign gene clusters to pathways. Falls back to upstream DIAMOND link table if available.

**NB03 — Classification**: Fitness importance threshold: |fitness| > 1 in any condition with |t| > 4. Essential genes (absent from genefitness) are included as the most extreme fitness category. Three statistical tests: chi-square (classification × metabolic category), Mann-Whitney (active vs latent fitness), Mann-Whitney (conservation comparison).

**NB04 — Cross-Species**: Tests H2 at two scales: FB organisms (~33) and all 27K species. Uses pathway completeness CV as heterogeneity metric. Controls for genome count as confounder (more genomes → more observed variation by sampling).

---

## Phase 5: Commit

All 5 notebooks were committed to the `projects/metabolic_capability_dependency` branch:

```
2f7797a Add analysis notebooks for metabolic capability vs dependency project
```

RESEARCH_PLAN.md updated to v2 noting notebook creation.

---

## Next Steps

1. Upload NB01 and NB02 to BERDL JupyterHub and run them
2. Download output CSVs to local `data/` directory
3. Run NB03-05 locally
4. Run `/synthesize` to create REPORT.md
5. Run `/submit` for automated review

---

## Key Pitfalls to Watch For

From `docs/pitfalls.md` and this conversation:
- GapMind has **multiple rows per genome-pathway pair** — always MAX aggregate
- GapMind genome_id may lack GTDB prefix (RS_/GB_) — check and reconcile
- FB fitness values are **strings** — CAST to FLOAT before comparison
- Gene cluster IDs are **species-specific** — use EC/KEGG for cross-species
- KEGG-to-GapMind mapping is **approximate** — one KEGG pathway may contain genes for multiple GapMind pathways (e.g., map00250 covers alanine, aspartate, glutamate, asparagine)
- Score categories are: complete, likely_complete, steps_missing_low, steps_missing_medium, not_present — **NOT a binary 'present' flag**
- `.toPandas()` on large results will OOM — aggregate in Spark first
