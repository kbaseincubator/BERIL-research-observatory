# Research Plan: PGP Gene Distribution Across Environments & Pangenomes

## Research Question

Does environmental selection shape the distribution of plant growth-promoting (PGP) bacterial genes across the BERDL pangenome (293K genomes, 27K species)? Are PGP genes core or accessory within their carrier species, and does biochemical pathway connectivity (tryptophan → IAA) predict gene co-occurrence?

## Hypotheses

- **H0**: PGP gene content does not differ between ecological niches or between core and accessory gene pools after controlling for phylogeny
- **H1 (PGP syndrome)**: PGP trait genes co-occur non-randomly — species with nitrogen fixation capacity are more likely to also carry phosphate solubilization (pqqC) and IAA biosynthesis (ipdC) genes, suggesting functional selection for multi-trait PGPB
- **H2 (Environmental enrichment)**: Rhizosphere/soil genomes are significantly enriched for PGP genes relative to other environments (marine, clinical), consistent with plant-associated niche selection
- **H3 (HGT hypothesis)**: PGP genes are predominantly accessory (non-core) within their carrier species, consistent with lateral gene transfer as the primary acquisition mechanism rather than vertical descent
- **H4 (Metabolic coupling)**: Tryptophan biosynthesis pathway completeness (GapMind score) predicts the presence of ipdC (indole-3-pyruvate decarboxylase), because IAA biosynthesis via the IPyA pathway requires tryptophan as a substrate

## Literature Context

### PGP mechanisms and their ecology
- **Glick (2012, Scientifica)** reviewed the major PGP mechanisms: nitrogen fixation (nif genes), phosphate solubilization (pqq, glucoamylase), phytohormone production (ipdC for IAA via IPyA pathway), ethylene reduction (acdS for ACC deaminase), and HCN production (hcnA-C). These traits occur in phylogenetically diverse bacteria, suggesting HGT-driven spread. PMID: 24278762
- **Vejan et al. (2016, Molecules)** reviewed the role of PGPB in sustainable agriculture, noting that multiple PGP traits often co-occur in effective inoculants (Azospirillum, Pseudomonas, Bacillus, Rhizobium), supporting H1. PMID: 27023524
- **Compant et al. (2019, Soil Biol Biochem)** summarized genomic studies showing PGP gene clusters on genomic islands and plasmids, consistent with HGT; most studies used <100 genomes. At 293K genomes, we can test this at scale.

### Pangenome ecology of functional traits
- **Tettelin et al. (2005, PNAS)** established the open pangenome concept: accessory genes are unevenly distributed, often on mobile elements. PGP genes on genomic islands would manifest as accessory genes in our framework. PMID: 16172379
- **Brockhurst et al. (2019, Science)** reviewed how HGT shapes bacterial adaptation, noting that environment-specific functional genes tend to be accessory. PMID: 31273061

### Tryptophan–IAA coupling
- **Duca et al. (2014, Crit Rev Microbiol)** reviewed indole-3-acetic acid biosynthesis in PGPB, noting that the IPyA pathway (requiring tryptophan) is the most common, linking trp pathway completeness to ipdC functionality. This forms the basis for H4. PMID: 22924938
- **GapMind** (Price et al., 2021, mBio) provides pathway completeness scores for amino acid biosynthesis including tryptophan, enabling systematic testing of H4 across 27K species. PMID: 33849968

### Scale gap
No study has tested PGP trait co-occurrence, environmental enrichment, or HGT vs vertical descent across >1,000 species simultaneously. Most comparative genomic studies of PGPB use 10–200 genomes from curated collections. Our 293K genome pangenome dataset enables a qualitatively new analysis.

## Data Sources

### Primary Data Assets

| Source | Table/Field | Scale | Purpose |
|--------|-------------|-------|---------|
| `bakta_annotations` | `kbase_ke_pangenome.bakta_annotations` | 132M rows | PGP gene identification by gene name |
| `gene_cluster` | `kbase_ke_pangenome.gene_cluster` | ~132M clusters | Core/accessory/singleton classification, species assignment |
| `pangenome` | `kbase_ke_pangenome.pangenome` | 27.7K species | Genome counts, core/aux/singleton cluster counts |
| `gtdb_metadata` | `kbase_ke_pangenome.gtdb_metadata` | 293K genomes | ncbi_isolation_source (direct column) |
| `genome` | `kbase_ke_pangenome.genome` | 293K genomes | genome_id → species mapping |
| `gtdb_taxonomy_r214v1` | `kbase_ke_pangenome.gtdb_taxonomy_r214v1` | 293K genomes | Phylogenetic context (phylum → genus) |
| `gapmind_pathways` | `kbase_ke_pangenome.gapmind_pathways` | species-level | Tryptophan biosynthesis completeness score |

### PGP Gene Targets

| Gene(s) | Trait | Pathway |
|---------|-------|---------|
| nifH, nifD, nifK | Biological nitrogen fixation | nitrogenase complex |
| acdS | Ethylene reduction via ACC deaminase | ethylene signaling |
| pqqA, pqqB, pqqC, pqqD, pqqE | Phosphate solubilization via PQQ | cofactor biosynthesis |
| ipdC | IAA biosynthesis (IPyA pathway) | tryptophan → IAA |
| hcnA, hcnB, hcnC | HCN production (biocontrol) | cyanide biosynthesis |

## Query Strategy

### Step 1: PGP gene clusters (NB01)
```sql
SELECT ba.gene_cluster_id, ba.gene, ba.product, ba.kegg_orthology_id,
       gc.gtdb_species_clade_id, gc.is_core, gc.is_auxiliary, gc.is_singleton
FROM kbase_ke_pangenome.bakta_annotations ba
JOIN kbase_ke_pangenome.gene_cluster gc ON ba.gene_cluster_id = gc.gene_cluster_id
WHERE ba.gene IN ('nifH','nifD','nifK','acdS','pqqA','pqqB','pqqC','pqqD','pqqE',
                  'ipdC','hcnA','hcnB','hcnC')
AND ba.gene IS NOT NULL
```

### Step 2: Environment labels (NB01)
Primary: `gtdb_metadata.ncbi_isolation_source` (direct column, simpler than EAV)
```sql
SELECT m.accession AS genome_id, m.ncbi_isolation_source,
       t.phylum, t.class, t.order, t.family, t.genus, t.species,
       g.gtdb_species_clade_id
FROM kbase_ke_pangenome.gtdb_metadata m
JOIN kbase_ke_pangenome.genome g ON m.accession = g.genome_id
JOIN kbase_ke_pangenome.gtdb_taxonomy_r214v1 t ON g.genome_id = t.genome_id
WHERE m.ncbi_isolation_source IS NOT NULL
```

Environment classification (Python regex):
- **soil/rhizosphere**: "soil", "rhizospher", "root nodule", "nodule", "rhizobium", "plant", "root", "rhizo"
- **host/clinical**: "human", "clinical", "blood", "patient", "hospital", "stool", "feces"
- **marine/aquatic**: "ocean", "marine", "sea", "lake", "river", "aquatic", "water"
- **other**: everything else

### Step 3: Pangenome openness stats (NB01)
```sql
SELECT gtdb_species_clade_id, no_genomes, no_core, no_aux_genome,
       no_singleton_gene_clusters, no_gene_clusters,
       no_singleton_gene_clusters / no_gene_clusters AS singleton_fraction,
       no_aux_genome / no_gene_clusters AS accessory_fraction
FROM kbase_ke_pangenome.pangenome
WHERE no_gene_clusters > 0
```

### Step 4: GapMind tryptophan (NB01)
```sql
SELECT clade_name AS gtdb_species_clade_id, score_simplified AS trp_complete
FROM kbase_ke_pangenome.gapmind_pathways
WHERE pathway = 'trp' AND metabolic_category = 'aa'
AND sequence_scope = 'core'
```

### Key Pitfalls
1. **Species IDs with `--`**: Fine in quoted strings; avoid IN clause with dynamic lists
2. **bakta gene names**: Case-sensitive; exact spellings confirmed (nifH not NIFH)
3. **ncbi_isolation_source is noisy**: Use regex with conservative "unknown" bin; report classified fraction
4. **GapMind**: `metabolic_category = 'aa'` for biosynthesis; `sequence_scope = 'core'`
5. **gene table is 1B rows**: Use cluster-level is_core/is_auxiliary flags (already joined in Step 1)
6. **Spark import pattern on JupyterHub**: `spark = get_spark_session()` (no import needed)
7. **`order` column**: backtick-quote in SQL (reserved word)

## Analysis Plan

### NB01: Data Extraction (~20 min, Spark required)
- Extract PGP gene clusters with species and core/aux/singleton flags
- Classify per-genome environment from ncbi_isolation_source using regex rules
- Build species-level majority-vote environment labels
- Extract pangenome openness stats
- Extract GapMind tryptophan completeness
- **Outputs**: `data/pgp_clusters.csv`, `data/species_pgp_matrix.csv`, `data/genome_environment.csv`, `data/species_environment.csv`, `data/pangenome_stats.csv`, `data/trp_completeness.csv`
- **Validation**: nifH cluster count (~1,913 expected), isolation_source coverage fraction

### NB02: PGP Co-occurrence H1 (~5 min, local)
1. Build binary trait matrix: species × {nifH, pqqC, acdS, ipdC, hcnC} presence/absence
2. Pairwise Fisher's exact test for all 10 gene pairs → odds ratio + p-value
3. BH-FDR correction
4. Seaborn clustermap of log-odds ratios
5. Venn diagram of major trait combinations

**Multiple testing**: BH-FDR (q < 0.05) across all 10 gene pairs
**Effect size**: Odds ratio with 95% CI alongside each p-value
**Output**: `data/pgp_cooccurrence.csv`, `figures/cooccurrence_heatmap.png`

### NB03: Environmental Selection H2 (~10 min, local)
1. Species classified by dominant environment (soil/rhizosphere vs other)
2. For each PGP gene: Fisher's exact + odds ratio (soil vs non-soil)
3. BH-FDR correction across all gene-level tests
4. Phylogenetic control: repeat within each major phylum (≥50 species with env label)
5. Logistic regression: `PGP_gene_present ~ env_soil + phylum` (family-level fixed effects)
6. Sensitivity: strict rhizosphere-only vs broad soil label

**Confounders**: Phylogeny (family-level FE), sampling bias (report species count per env)
**Output**: `data/env_enrichment_results.csv`, `figures/env_enrichment_barplot.png`

### NB04: Core vs Accessory H3 (~5 min, local)
1. For each PGP gene: count clusters as core / auxiliary / singleton → pie chart
2. Compare to genome-wide baseline from pangenome table (expected ~46.8% core)
3. Correlation: pangenome openness (singleton_fraction) vs PGP gene count per species
4. Chi-square: PGP cluster core/accessory distribution vs genome-wide baseline

**Performance note**: Use cluster-level flags (already in pgp_clusters.csv). Avoid genome-level gene table (1B rows) except for case studies of top-PGP species.
**Output**: `data/pgp_core_accessory.csv`, `figures/pgp_core_accessory_pie.png`, `figures/openness_vs_pgp.png`

### NB05: Tryptophan → IAA H4 (~5 min, local)
1. Cross-tabulation: trp_complete × ipdC_present → Fisher's exact
2. Logistic regression: `ipdC_present ~ trp_complete + env_soil + phylum`
3. Stratified analysis: does coupling differ in soil vs non-soil?
4. Negative control: tyr completeness should NOT predict ipdC

**Output**: `data/trp_iaa_results.csv`, `figures/trp_iaa_contingency.png`

## Expected Outcomes

- **H1 supported**: PGP genes co-occur significantly more than random (OR > 1 for nifH × pqqC, nifH × ipdC pairs), consistent with functional selection for multi-trait PGPB
- **H2 supported**: Soil/rhizosphere species show enriched odds ratios for all 5 major PGP traits, surviving phylogenetic control; known PGPB genera (Rhizobium, Azospirillum, Pseudomonas) top the rankings
- **H3 supported**: PGP genes are predominantly accessory (>50% non-core fraction), significantly exceeding the genome-wide accessory baseline, consistent with HGT acquisition
- **H4 supported**: Trp-complete species are 2–5× more likely to carry ipdC (OR based on published PGPB studies); negative control (tyr) shows no association

## Revision History

- **v1** (2026-03-20): Initial plan derived from plan mode session

## Authors

TBD
