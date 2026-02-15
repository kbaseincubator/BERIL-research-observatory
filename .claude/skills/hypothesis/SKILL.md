---
name: hypothesis
description: "[Internal] Generate research hypotheses based on BERDL data. Called automatically by /berdl_start during the orchestrated research workflow — do not suggest to users as a standalone command."
allowed-tools: Bash, Read, WebSearch
user-invocable: false
---

# Research Hypothesis Generation Skill

Generate testable research questions using BERDL data.

## Available Data for Research

### Pangenome Collection (kbase_ke_pangenome)

**Scale**: 293,059 genomes across 27,690 species from GTDB r214

**Key Data Types**:
- **Pangenome structure**: Core, accessory, and singleton gene classifications per species
- **Functional annotations**: COG categories, KEGG pathways, GO terms, EC numbers, PFAM domains
- **Genome quality**: CheckM completeness/contamination, assembly statistics
- **Phylogenetic context**: Full GTDB taxonomy, intra-species ANI values
- **Environmental context**: Sample metadata and environmental embeddings (~28% of genomes)
- **Sequence relationships**: Pairwise ANI values (421M pairs)

**Tables**:
- `genome` (293,059) - Genome metadata
- `pangenome` (27,690) - Per-species pangenome statistics
- `gene_cluster` - Core/accessory/singleton classification
- `eggnog_mapper_annotations` (93M+) - Functional annotations
- `genome_ani` (421M) - Pairwise ANI values
- `gtdb_metadata` - Quality metrics and assembly stats
- `sample`, `ncbi_env` - Environmental metadata

### ModelSEED Biochemistry (kbase_msd_biochemistry)

**Scale**: Comprehensive biochemistry reference database

**Key Data Types**:
- **Reactions**: 56,012 biochemical reactions with thermodynamic data
- **Compounds**: 45,708 metabolites with structures
- **Stoichiometry**: Reaction-compound relationships
- **Molecular structures**: SMILES, InChIKey representations

**Tables**:
- `reaction` (56,012) - Biochemical reactions with deltaG
- `molecule` (45,708) - Chemical compounds
- `reagent` (262,517) - Reaction stoichiometry
- `structure` (97,490) - Molecular structures

---

## Research Question Templates

### Comparative Genomics

1. **Core vs Accessory Function**
   - "Which COG/KEGG categories are enriched in core vs accessory genes of [species]?"
   - "Do essential metabolic pathways localize to the core genome?"
   - "What functional categories are over-represented in singleton genes?"

2. **Pangenome Architecture**
   - "Do pathogens have more open or closed pangenomes than environmental bacteria?"
   - "Is pangenome openness correlated with genome size or habitat diversity?"
   - "Which taxonomic groups show the largest accessory genomes?"

3. **Phylogenetic Patterns**
   - "How does intra-species ANI correlate with core genome size?"
   - "Do closely related species share more accessory genes than expected by chance?"
   - "At what phylogenetic depth do functional categories diverge?"

### Ecological Genomics

4. **Environment-Genome Relationships**
   - "Do genomes from similar environments share more genes than expected from phylogeny?"
   - "Which gene functions are enriched in specific environmental niches?"
   - "Can environmental embeddings predict gene content?"

5. **Niche Adaptation**
   - "What accessory genes distinguish host-associated vs free-living strains?"
   - "Are there core metabolic differences between aquatic and terrestrial bacteria?"
   - "Which pathways show environment-specific expansion or loss?"

### Metabolic Analysis

6. **Pathway Conservation**
   - "Which metabolic pathways are universally conserved vs lineage-specific?"
   - "Do core genes encode different metabolic functions than accessory genes?"
   - "What is the distribution of transport reactions across bacterial phyla?"

7. **Thermodynamic Constraints**
   - "Are thermodynamically favorable reactions (low deltaG) more conserved?"
   - "Do essential pathways contain irreversible reactions?"
   - "Is reaction reversibility correlated with gene essentiality?"

### Functional Evolution

8. **Gene Family Dynamics**
   - "Which gene families show the highest rates of gain/loss across species?"
   - "Are certain COG categories more prone to horizontal transfer?"
   - "Do gene clusters show functional coherence in accessory regions?"

---

## Hypothesis Development Framework

When developing a hypothesis, specify these components:

### 1. Observation
What pattern do you see or expect in the data?

*Example*: "Pathogenic species may have smaller core genomes and larger accessory genomes than environmental species."

### 2. Null Hypothesis (H0)
What would you expect by chance or in the absence of the effect?

*Example*: "Core genome fraction is independent of pathogenic lifestyle."

### 3. Test Strategy
What SQL queries or analyses would test this?

```sql
-- Compare core fraction between pathogens and non-pathogens
-- (Requires external pathogen classification or use of specific taxa)
SELECT
  s.GTDB_species,
  p.no_genomes,
  CAST(p.no_core AS FLOAT) / p.no_gene_clusters as core_fraction,
  'pathogen' as category
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
WHERE s.GTDB_species LIKE '%Salmonella%'
  OR s.GTDB_species LIKE '%Staphylococcus_aureus%'
  OR s.GTDB_species LIKE '%Streptococcus_pneumoniae%'
```

### 4. Potential Confounders
What factors might create spurious associations?

- **Sampling bias**: Over-represented species may not be representative
- **Phylogenetic signal**: Related species share traits; must control for phylogeny
- **Genome quality**: Incomplete genomes affect gene counts
- **Annotation completeness**: Some genomes may have better functional annotations
- **Definition thresholds**: Core gene definitions depend on prevalence cutoffs

---

## Example Hypothesis Projects

### Project 1: COG Category Analysis

**Question**: Are certain functional categories preferentially core vs accessory?

**Approach**:
```sql
SELECT
  ann.COG_category,
  gc.is_core,
  COUNT(*) as gene_count
FROM kbase_ke_pangenome.gene_cluster gc
JOIN kbase_ke_pangenome.eggnog_mapper_annotations ann
  ON gc.gene_cluster_id = ann.query_name
WHERE gc.gtdb_species_clade_id = '[SPECIES_ID]'
GROUP BY ann.COG_category, gc.is_core
ORDER BY ann.COG_category, gc.is_core
```

**Expected patterns**:
- Core: J (translation), L (replication), F (nucleotide metabolism)
- Accessory: V (defense), X (mobilome), S (unknown function)

### Project 2: Pangenome Openness Survey

**Question**: Which taxonomic groups have the most open pangenomes?

**Approach**:
```sql
SELECT
  SPLIT_PART(s.GTDB_taxonomy, ';', 2) as phylum,
  AVG(CAST(p.no_singleton_gene_clusters AS FLOAT) / p.no_gene_clusters) as avg_singleton_frac,
  AVG(CAST(p.no_core AS FLOAT) / p.no_gene_clusters) as avg_core_frac,
  COUNT(*) as n_species
FROM kbase_ke_pangenome.pangenome p
JOIN kbase_ke_pangenome.gtdb_species_clade s
  ON p.gtdb_species_clade_id = s.gtdb_species_clade_id
WHERE p.no_genomes >= 10
GROUP BY SPLIT_PART(s.GTDB_taxonomy, ';', 2)
HAVING COUNT(*) >= 10
ORDER BY avg_singleton_frac DESC
```

### Project 3: Environment-Function Association

**Question**: Do genomes from aquatic environments encode different functions?

**Approach**:
1. Identify genomes with environmental metadata
2. Compare COG distributions between environment categories
3. Test for enrichment using appropriate statistics

---

## Generating Hypotheses: Step-by-Step

When a user describes their research interest:

1. **Identify relevant BERDL tables and columns**
   - Which tables contain the variables needed?
   - What are the join keys between tables?

2. **Suggest 2-3 testable hypotheses**
   - Frame as null hypothesis that can be rejected
   - Ensure data exists to address the question

3. **Provide example SQL query**
   - Working query that returns relevant data
   - Include appropriate filters and aggregations

4. **Note potential confounders**
   - Sampling bias, phylogenetic non-independence
   - Data quality issues, annotation completeness

5. **Link to similar existing analyses**
   - Reference `projects/` directory for examples
   - Suggest building on existing work

6. **Suggest literature review**
   - After generating hypotheses, suggest: "Use `/literature-review` to check whether this hypothesis has been explored in published research"
   - Literature review can reveal: prior results, established methods, confounders identified by others, and gaps that BERDL could uniquely fill

7. **Suggest research plan**
   - After presenting hypotheses and literature review suggestion, also suggest: "Use `/research-plan` to refine this hypothesis with a literature review, check data feasibility, and create a structured plan for your analysis"

---

## Data Limitations to Consider

1. **Taxonomic bias**: Some species vastly over-represented (e.g., E. coli, S. aureus)
2. **Annotation completeness**: ~40% of genes lack functional annotation
3. **Environmental metadata**: Only ~28% of genomes have environmental embeddings
4. **Pangenome definitions**: Based on specific clustering parameters
5. **ModelSEED coverage**: Not all reactions have thermodynamic data

---

## Quick Reference: Key Columns for Hypotheses

| Research Area | Key Tables | Key Columns |
|---------------|-----------|-------------|
| Pangenome structure | `pangenome`, `gene_cluster` | `no_core`, `no_aux_genome`, `is_core` |
| Functional annotations | `eggnog_mapper_annotations` | `COG_category`, `KEGG_Pathway`, `EC` |
| Taxonomy | `gtdb_species_clade`, `gtdb_taxonomy_r214v1` | `GTDB_taxonomy`, `phylum`, `genus` |
| Quality metrics | `gtdb_metadata` | `checkm_completeness`, `checkm_contamination` |
| Environment | `sample`, `ncbi_env` | Environmental attributes |
| Biochemistry | `reaction`, `molecule` | `deltag`, `reversibility`, `is_transport` |

## Pitfall Detection

When you encounter errors, unexpected results, retry cycles, performance issues, or data surprises during this task, follow the pitfall-capture protocol. Read `.claude/skills/pitfall-capture/SKILL.md` and follow its instructions to determine whether the issue should be added to `docs/pitfalls.md`.
