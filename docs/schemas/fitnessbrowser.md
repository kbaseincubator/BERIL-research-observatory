# Fitness Browser Database Schema Documentation

**Database**: `kescience_fitnessbrowser`
**Location**: On-prem Delta Lakehouse (BERDL)
**Tenant**: KE Science
**Last Updated**: 2026-02-11
**Verified**: REST API schema introspection and sample queries

---

## Overview

The Fitness Browser contains **genome-wide mutant fitness data** from transposon mutant (RB-TnSeq) experiments across **48 bacterial organisms**. For each organism, the database includes fitness scores measuring how important each gene is for growth under hundreds of experimental conditions (stress, carbon sources, antibiotics, etc.).

Key data:
- 48 organisms with transposon mutant libraries
- 228,709 genes with systematic annotations
- 7,552 experiments across diverse growth conditions
- 27,410,721 gene-fitness measurements
- Cross-organism orthologs and co-fitness relationships

**Source**: [Fitness Browser](https://fit.genomics.lbl.gov/) (Price et al., 2018)

---

## Table Summary

### Core Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `organism` | 48 | Organisms with mutant libraries |
| `gene` | 228,709 | Gene records with genomic coordinates |
| `experiment` | 7,552 | Experimental conditions and metadata |
| `genefitness` | 27,410,721 | Gene fitness scores per experiment |
| `cofit` | 13,656,145 | Gene co-fitness relationships |
| `specificphenotype` | 38,525 | Genes with specific phenotypes |
| `ortholog` | ~millions | Cross-organism orthologs (BBH) |

### Annotation Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `genedomain` | ~millions | Protein domain annotations (TIGRFam, PFam, etc.) |
| `besthitkegg` | 200,074 | Best BLAST hits to KEGG |
| `keggmember` | 82,687 | KEGG ortholog group memberships |
| `kgroupdesc` | 4,938 | KEGG group descriptions |
| `kgroupec` | 2,513 | KEGG group EC number mappings |
| `seedannotation` | 177,519 | SEED/RAST functional annotations |
| `seedclass` | 61,874 | SEED classification categories |
| `ecinfo` | 4,900 | EC number descriptions |
| `reannotation` | varies | Curated re-annotations |

### MetaCyc Pathway Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `metacycpathway` | 3,512 | MetaCyc pathway definitions |
| `metacycpathwayreaction` | varies | Pathway-reaction relationships |
| `metacycreaction` | 20,793 | MetaCyc reactions |
| `metacyccompound` | varies | MetaCyc compounds |

### Media/Condition Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `mediacomponents` | 10,439 | Growth media composition |
| `compounds` | varies | Compound definitions |

### Per-Organism Fitness Tables

Each organism has a dedicated `fitbyexp_{orgId}` table with pre-pivoted fitness data (genes as rows, experiments as columns). These are convenience tables for fast per-organism lookups.

Examples: `fitbyexp_keio`, `fitbyexp_dvh`, `fitbyexp_mr1`, `fitbyexp_pseudo1_n1b4`, etc.

---

## Table Schemas

### `organism`

| Column | Type | Description |
|--------|------|-------------|
| `orgId` | string | **Primary Key**. Short organism identifier (e.g., "Keio", "dvh") |
| `division` | string | Taxonomic division |
| `genus` | string | Genus name |
| `species` | string | Species name |
| `strain` | string | Strain designation |
| `taxonomyId` | string | NCBI taxonomy ID |

---

### `gene`

| Column | Type | Description |
|--------|------|-------------|
| `orgId` | string | FK -> `organism.orgId` |
| `locusId` | string | **Primary Key** (with orgId). Locus identifier |
| `sysName` | string | Systematic gene name (e.g., locus tag) |
| `scaffoldId` | string | Scaffold/chromosome identifier |
| `begin` | string | Start position |
| `end` | string | End position |
| `type` | string | Feature type |
| `strand` | string | Strand (+/-) |
| `gene` | string | Gene symbol (if known) |
| `desc` | string | Gene description |
| `GC` | string | GC content |

---

### `experiment`

| Column | Type | Description |
|--------|------|-------------|
| `orgId` | string | FK -> `organism.orgId` |
| `expName` | string | **Primary Key** (with orgId). Experiment identifier |
| `expDesc` | string | Short condition description |
| `expDescLong` | string | Detailed condition description |
| `expGroup` | string | Experiment group (e.g., "stress", "carbon source", "lb") |
| `media` | string | Growth medium used |
| `mediaStrength` | string | Medium concentration |
| `temperature` | string | Growth temperature |
| `pH` | string | pH value |
| `vessel` | string | Growth vessel type |
| `aerobic` | string | Aerobic/Anaerobic |
| `liquid` | string | Liquid/Solid |
| `shaking` | string | Shaking method |
| `condition_1` | string | Primary condition/compound |
| `units_1` | string | Units for condition_1 |
| `concentration_1` | string | Concentration of condition_1 |
| `condition_2..4` | string | Additional conditions (up to 4) |
| `mutantLibrary` | string | Mutant library used |
| `person` | string | Experimenter |
| `dateStarted` | string | Experiment date |
| `pubId` | string | Publication reference |
| `nMapped` | string | Number of mapped reads |
| `nUsed` | string | Number of usable insertions |
| `gMed` | string | Median reads per gene |
| `cor12` | string | Correlation between replicates |
| `mad12` | string | Median absolute deviation |
| `maxFit` | string | Maximum fitness score |

---

### `genefitness`

Gene fitness scores per experiment.

| Column | Type | Description |
|--------|------|-------------|
| `orgId` | string | FK -> `organism.orgId` |
| `locusId` | string | FK -> `gene.locusId` |
| `expName` | string | FK -> `experiment.expName` |
| `fit` | string | Fitness score (log2 ratio) |
| `t` | string | T-statistic for fitness score |

**Fitness score interpretation**:
- `fit` ~ 0: Gene is not important for this condition
- `fit` < -1: Gene is important (mutant grows poorly)
- `fit` < -2: Gene is very important
- `fit` > 0: Mutant grows better than wild-type (rare)

---

### `cofit`

Co-fitness relationships between gene pairs within an organism.

| Column | Type | Description |
|--------|------|-------------|
| `orgId` | string | FK -> `organism.orgId` |
| `locusId` | string | FK -> `gene.locusId` (query gene) |
| `hitId` | string | FK -> `gene.locusId` (co-fit partner) |
| `rank` | string | Co-fitness rank |
| `cofit` | string | Co-fitness score (Pearson correlation) |

---

### `ortholog`

Bidirectional best BLAST hits between organisms.

| Column | Type | Description |
|--------|------|-------------|
| `orgId1` | string | FK -> `organism.orgId` |
| `locusId1` | string | FK -> `gene.locusId` |
| `orgId2` | string | FK -> `organism.orgId` |
| `locusId2` | string | FK -> `gene.locusId` |
| `ratio` | string | Sequence identity ratio |

---

### `genedomain`

Protein domain annotations from multiple databases.

| Column | Type | Description |
|--------|------|-------------|
| `domainDb` | string | Domain database (TIGRFam, PFam, CDD, etc.) |
| `orgId` | string | FK -> `organism.orgId` |
| `locusId` | string | FK -> `gene.locusId` |
| `domainId` | string | Domain identifier |
| `domainName` | string | Domain name |
| `begin` | string | Domain start position |
| `end` | string | Domain end position |
| `score` | string | Hit score |
| `evalue` | string | E-value |
| `type` | string | Annotation type |
| `geneSymbol` | string | Associated gene symbol |
| `ec` | string | EC number |
| `definition` | string | Functional definition |

---

### `specificphenotype`

Genes with strong, specific fitness effects.

| Column | Type | Description |
|--------|------|-------------|
| `orgId` | string | FK -> `organism.orgId` |
| `expName` | string | FK -> `experiment.expName` |
| `locusId` | string | FK -> `gene.locusId` |

---

### `specog`

Specific phenotypes aggregated by ortholog group.

| Column | Type | Description |
|--------|------|-------------|
| `ogId` | string | Ortholog group ID |
| `expGroup` | string | Experiment group |
| `condition` | string | Condition description |
| `orgId` | string | FK -> `organism.orgId` |
| `locusId` | string | FK -> `gene.locusId` |
| `minFit` | string | Minimum fitness in this condition |
| `maxFit` | string | Maximum fitness in this condition |
| `minT` | string | Minimum t-statistic |
| `maxT` | string | Maximum t-statistic |
| `nInOG` | string | Number of genes in ortholog group |

---

## Key Relationships

```
organism (48)
    │
    ├── 1:N → gene (228,709)
    │            │
    │            ├── N:M → genefitness (27M) ← experiment
    │            ├── 1:N → genedomain
    │            ├── N:M → cofit (13.6M)
    │            ├── N:M → ortholog (cross-organism)
    │            └── 1:N → specificphenotype ← experiment
    │
    ├── 1:N → experiment (7,552)
    │            └── uses → mediacomponents → compounds
    │
    └── 1:1 → fitbyexp_{orgId} (per-organism convenience tables)
```

---

## Common Query Patterns

### List All Organisms
```sql
SELECT orgId, genus, species, strain, taxonomyId
FROM kescience_fitnessbrowser.organism
ORDER BY genus, species
```

### Get Genes for an Organism
```sql
SELECT locusId, sysName, gene, desc
FROM kescience_fitnessbrowser.gene
WHERE orgId = 'Keio'
LIMIT 20
```

### Get Fitness Scores for a Gene
```sql
SELECT gf.expName, e.expDesc, gf.fit, gf.t
FROM kescience_fitnessbrowser.genefitness gf
JOIN kescience_fitnessbrowser.experiment e
  ON gf.orgId = e.orgId AND gf.expName = e.expName
WHERE gf.orgId = 'Keio' AND gf.locusId = '14407'
ORDER BY CAST(gf.fit AS FLOAT) ASC
LIMIT 20
```

### Find Important Genes for a Condition
```sql
SELECT gf.locusId, g.gene, g.desc, gf.fit, gf.t
FROM kescience_fitnessbrowser.genefitness gf
JOIN kescience_fitnessbrowser.gene g
  ON gf.orgId = g.orgId AND gf.locusId = g.locusId
WHERE gf.orgId = 'dvh' AND gf.expName = 'set1IT049'
  AND CAST(gf.fit AS FLOAT) < -2
ORDER BY CAST(gf.fit AS FLOAT) ASC
```

### Find Co-fitness Partners
```sql
SELECT c.hitId, g.gene, g.desc, c.cofit, c.rank
FROM kescience_fitnessbrowser.cofit c
JOIN kescience_fitnessbrowser.gene g
  ON c.orgId = g.orgId AND c.hitId = g.locusId
WHERE c.orgId = 'dvh' AND c.locusId = 'DVU0001'
ORDER BY CAST(c.rank AS INT) ASC
LIMIT 20
```

### Find Orthologs Across Organisms
```sql
SELECT o.orgId2, o.locusId2, g.gene, g.desc, o.ratio
FROM kescience_fitnessbrowser.ortholog o
JOIN kescience_fitnessbrowser.gene g
  ON o.orgId2 = g.orgId AND o.locusId2 = g.locusId
WHERE o.orgId1 = 'dvh' AND o.locusId1 = 'DVU0001'
```

---

## Pitfalls

- **All values are strings**: Numeric columns like `fit`, `t`, `begin`, `end` are stored as strings. Cast to float/int for comparisons: `CAST(fit AS FLOAT) < -2`
- **genefitness is large**: 27M rows. Always filter by `orgId` at minimum
- **cofit is large**: 13.6M rows. Always filter by `orgId` and `locusId`
- **orgId is case-sensitive**: Use exact matches (e.g., "Keio" not "keio")
- **Per-organism tables**: The `fitbyexp_*` tables provide faster access for single-organism queries but have non-standard schemas

---

## Changelog

- **2026-02-11**: Initial schema documentation via REST API introspection.
