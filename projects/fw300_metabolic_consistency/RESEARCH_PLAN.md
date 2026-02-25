# Research Plan: Metabolic Consistency of Pseudomonas FW300-N2E3 Across Exometabolomics, Fitness, and Phenotypic Databases

## Research Question

For *Pseudomonas fluorescens* FW300-N2E3, how consistent are experimentally measured exometabolomic outputs (Web of Microbes) with genome-wide gene fitness data (Fitness Browser), species-level metabolite utilization phenotypes (BacDive), and computationally predicted metabolic capabilities (GapMind pathways)?

## Hypothesis

- **H0**: The metabolic profile of FW300-N2E3 is internally consistent across databases — compounds it produces correspond to active biosynthetic pathways (GapMind), genes required for their metabolism show fitness effects (FB), and production/utilization calls agree with species-level phenotypes (BacDive).
- **H1**: Significant discordances exist across databases, reflecting (a) the difference between strain-level and species-level measurements, (b) the distinction between production vs. utilization capabilities, (c) gaps in computational pathway predictions, or (d) condition-dependent metabolic states not captured by single-condition assays.

## Literature Context

No published study has directly integrated exometabolomics with RB-TnSeq fitness data, despite both datasets existing for FW300-N2E3 through the ENIGMA program. Key references:

- **Kosina et al. (2018)** — Web of Microbes database (BMC Microbiology 18:139)
- **Price et al. (2018)** — RB-TnSeq fitness for 48 bacteria (Nature 557:503-509)
- **de Raad et al. (2022)** — NLDM exometabolomics for 110 soil bacteria (Front Microbiol 13:855331)
- **Price et al. (2022)** — GapMind pathway predictions (PLoS Genetics 18:e1010156)
- **Ramoneda et al. (2023)** — Amino acid auxotrophy mapping (Nature Communications 14:7608)

The `webofmicrobes_explorer` project in this repository identified 19 WoM metabolites with direct FB condition matches but did not perform the integration analysis.

## Approach

### Three-Way Metabolite Triangulation

For each metabolite in the WoM profile of FW300-N2E3, compare:
1. **WoM action** (E=emerged/produced de novo, I=increased/amplified, N=no change)
2. **FB fitness** (gene fitness when grown on that compound as C/N source, if tested)
3. **BacDive consensus** (utilization +/- across P. fluorescens strains)
4. **GapMind prediction** (pathway completeness for biosynthesis/catabolism)

### Key Comparisons

| Comparison | Question | Expected Pattern |
|---|---|---|
| WoM ↔ FB | Do genes for metabolizing compound X show fitness effects when X is the carbon source? | If WoM says organism produces X, FB should reveal biosynthetic gene dependencies |
| WoM ↔ BacDive | Does strain-level exometabolomics agree with species-level utilization? | Production ≠ utilization, so partial agreement expected |
| FB ↔ BacDive | Do gene fitness experiments agree with species-level +/- calls? | FB carbon source growth should correlate with BacDive + |
| WoM ↔ GapMind | Are produced metabolites predicted by complete biosynthetic pathways? | Emerged metabolites should have complete pathways |
| FB ↔ GapMind | Do fitness-important genes map to predicted pathway steps? | Fitness hits should enrich predicted pathway genes |

## Data Sources

### Strain: Pseudomonas fluorescens FW300-N2E3

| Database | Identifier | Key Details |
|---|---|---|
| Web of Microbes | `Pseudomonas sp. (FW300-N2E3)` in `kescience_webofmicrobes` | 105 observations (27 E + 31 I + 47 N), grown on R2A |
| Fitness Browser | `pseudo3_N2E3` in `kescience_fitnessbrowser` | 211 experiments: 82 carbon source, 38 nitrogen source, 68 stress, others |
| BacDive | `Pseudomonas fluorescens` in `kescience_bacdive` | 105 strains, 83 compounds tested |
| Pangenome | `RS_GCF_001307155.1` in `kbase_ke_pangenome` | Clade `s__Pseudomonas_E_fluorescens_E` (40 genomes), representative genome |
| ModelSEED | `kbase_msd_biochemistry` | Cross-reference for reaction/compound mapping |

### WoM ↔ FB Metabolite Overlap (Preliminary)

At least 19 metabolites appear in both WoM (produced/increased) and FB (tested as C/N source):
- **Carbon sources also produced in WoM**: carnitine, lactate, valine, alanine, arginine, proline, phenylalanine, tryptophan, trehalose, malate, glutamic acid, and more
- **Nitrogen sources also produced in WoM**: adenine, adenosine, inosine, arginine, carnitine

### WoM ↔ BacDive Matches (7 exact name matches)

| Compound | WoM Action | BacDive | Notes |
|---|---|---|---|
| lysine | E (produced) | - (0/3) | Produces it but species can't catabolize it |
| valine | E (produced) | + (1/1) | Consistent — both biosynthesis and catabolism |
| malate | I (increased) | + (49/49) | Consistent — universal utilization |
| arginine | I (increased) | mixed (42+/10-) | Strain variation |
| trehalose | I (increased) | mixed (2+/5-) | Strain variation |
| tryptophan | I (increased) | - (0/52) | Produces but never catabolized by any strain |
| glycine | I (increased) | - (0/1) | Limited data |

## Query Strategy

### Tables Required

| Table | Purpose | Estimated Rows | Filter Strategy |
|---|---|---|---|
| `kescience_webofmicrobes.observation` | WoM metabolite profile | ~105 | Filter by organism_id for FW300-N2E3 |
| `kescience_webofmicrobes.compound` | Metabolite identities | ~589 | Join to observations |
| `kescience_fitnessbrowser.genefitness` | Per-gene fitness scores | ~300K for this organism | Filter by orgId = 'pseudo3_N2E3' |
| `kescience_fitnessbrowser.experiment` | Experiment conditions | ~211 | Filter by orgId |
| `kescience_fitnessbrowser.gene` | Gene annotations | ~5,854 | Filter by orgId |
| `kescience_fitnessbrowser.seedannotation` | SEED functional annotations | ~5K | Filter by orgId |
| `kescience_bacdive.metabolite_utilization` | Species utilization data | ~1,200 for P. fluorescens | Join taxonomy on genus='Pseudomonas', species='Pseudomonas fluorescens' |
| `kbase_ke_pangenome.gapmind_pathways` | Pathway completeness | ~5K for clade | Filter by clade_name |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | COG/KEGG annotations | ~200K for clade | Filter by clade |

### Key Queries

1. **WoM full profile with compound details**:
```sql
SELECT c.compound_name, obs.action, c.formula, c.pubchem_id, c.inchi_key,
       e.env_name
FROM kescience_webofmicrobes.observation obs
JOIN kescience_webofmicrobes.organism o ON o.id = obs.organism_id
JOIN kescience_webofmicrobes.compound c ON c.id = obs.compound_id
JOIN kescience_webofmicrobes.environment e ON e.id = obs.environment_id
WHERE o.common_name = 'Pseudomonas sp. (FW300-N2E3)'
```

2. **FB fitness for carbon/nitrogen source experiments**:
```sql
SELECT e.condition_1, e.expGroup, gf.locusId, gf.fit, gf.t
FROM kescience_fitnessbrowser.genefitness gf
JOIN kescience_fitnessbrowser.experiment e ON gf.orgId = e.orgId AND gf.expName = e.expName
WHERE gf.orgId = 'pseudo3_N2E3'
AND e.expGroup IN ('carbon source', 'nitrogen source')
AND ABS(gf.fit) > 1 AND ABS(gf.t) > 4
```

3. **GapMind pathways for FW300-N2E3 clade** (take best score per genome-pathway pair):
```sql
SELECT pathway, genome_id, MAX(CASE score_category
    WHEN 'complete' THEN 5 WHEN 'likely_complete' THEN 4
    WHEN 'steps_missing_low' THEN 3 WHEN 'steps_missing_medium' THEN 2
    WHEN 'not_present' THEN 1 ELSE 0 END) as best_score
FROM kbase_ke_pangenome.gapmind_pathways
WHERE clade_name = 's__Pseudomonas_E_fluorescens_E--RS_GCF_001307155.1'
AND genome_id = 'RS_GCF_001307155.1'
GROUP BY pathway, genome_id
```

### Performance Plan
- **Tier**: JupyterHub Spark SQL (all queries are filtered, moderate complexity)
- **Estimated complexity**: moderate (multiple joins, but all filtered to single organism/clade)
- **Known pitfalls**: GapMind has multiple rows per genome-pathway pair (take MAX score); BacDive uses `compound_name` not `metabolite_name`; WoM compound table uses `compound_name` not `common_name`

## Analysis Plan

### Notebook 1: Data Extraction and Harmonization
- **Goal**: Extract WoM, FB, BacDive, and GapMind data for FW300-N2E3; harmonize metabolite/compound names across databases
- **Key challenge**: Name matching — WoM compound names, BacDive compound names, FB condition names, GapMind pathway names, and ModelSEED molecule names all use different nomenclature
- **Approach**: Build a manual metabolite mapping table + automated fuzzy matching + formula matching as fallback
- **Expected output**: `data/metabolite_crosswalk.tsv` (unified metabolite table with IDs from each database)

### Notebook 2: WoM ↔ Fitness Browser Integration
- **Goal**: For each WoM-produced metabolite that has a corresponding FB carbon/nitrogen source experiment, identify genes with significant fitness effects
- **Analysis**:
  - For each overlapping metabolite, extract genes with |fitness| > 1 and |t| > 4
  - Annotate these genes with SEED functions and KEGG pathways
  - Classify as biosynthetic vs catabolic vs regulatory
  - Ask: are the fitness-important genes for growing ON metabolite X the same genes involved in PRODUCING metabolite X?
- **Expected output**: `data/wom_fb_gene_table.tsv`, figures showing fitness landscapes per metabolite

### Notebook 3: Three-Way Consistency Matrix
- **Goal**: Build the full consistency matrix across WoM × FB × BacDive × GapMind
- **Analysis**:
  - Score each metabolite on a concordance scale across all databases
  - Identify concordant metabolites (all databases agree) vs discordant ones
  - Classify discordance types: strain-vs-species, production-vs-utilization, prediction-vs-observation
  - Statistical test: is concordance better than random?
- **Expected output**: `data/consistency_matrix.tsv`, heatmap figure, summary statistics

### Notebook 4: Pathway-Level Analysis
- **Goal**: Map metabolite-level findings to pathway-level predictions
- **Analysis**:
  - For amino acids produced in WoM, check GapMind biosynthesis pathway completeness
  - For carbon sources tested in FB, check GapMind catabolism pathway completeness
  - Compare: does GapMind "complete" predict FB growth? Does it predict WoM production?
- **Expected output**: pathway concordance table, Sankey or alluvial diagram

## Expected Outcomes

- **If H1 supported (discordances exist)**: Characterize the nature and frequency of each discordance type. The most interesting cases are metabolites where production (WoM) and utilization (BacDive) disagree — these reveal overflow metabolism, cross-feeding potential, or strain-specific adaptations. Discordances between fitness data and pathway predictions reveal gaps in computational annotation.

- **If H0 not rejected (high consistency)**: This validates the use of these databases for integrated metabolic analysis and demonstrates that exometabolomics, mutant fitness, phenotypic databases, and computational predictions converge on a coherent metabolic picture — a useful benchmark for the field.

- **Potential confounders**:
  - WoM measured in R2A (rich medium) vs FB in minimal medium with single C/N sources
  - BacDive aggregates across many strains, some may not be true P. fluorescens by GTDB
  - GapMind predictions are for pathways, not individual metabolites
  - Name matching between databases may miss true correspondences or create false ones

## Revision History
- **v1** (2026-02-25): Initial plan based on data exploration across WoM, FB, BacDive, and pangenome

## Authors
- Paramvir Dehal (ORCID: 0000-0001-5810-2497)
- Claude (AI assistant, Anthropic)
