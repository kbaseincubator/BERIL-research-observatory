# Research Plan: The Pan-Bacterial Essential Metabolome

## Research Question

Which biochemical reactions are universally essential across bacteria, and what does the essential metabolome reveal about the minimal core metabolism required for microbial life?

## Hypothesis

- **H0**: There is no conserved set of universally essential biochemical reactions; essential metabolism is highly species-specific.
- **H1**: A core set of biochemical reactions is universally essential across bacteria, concentrated in central carbon metabolism, amino acid biosynthesis, nucleotide metabolism, and core biosynthetic pathways.

## Secondary Hypotheses

1. **Pathway enrichment**: Universally essential reactions will be enriched in glycolysis, TCA cycle, amino acid biosynthesis, and nucleotide biosynthesis pathways.
2. **Cofactor dependency**: Essential reactions will show higher dependency on core cofactors (ATP, NAD+, CoA) compared to peripheral metabolism.
3. **Reaction reversibility**: Essential reactions will be biased toward irreversible steps (thermodynamic control points in pathways).
4. **Network centrality**: Essential reactions will have higher betweenness centrality in the metabolic network (critical connectors between pathways).

## Literature Context

### Essential Genes and Minimal Genomes
- Experimental studies using transposon mutagenesis (e.g., RB-TnSeq, Tn-Seq) have identified essential gene sets across diverse bacteria
- Synthetic biology efforts (JCVI-syn3.0, minimal *Mycoplasma*) have defined minimal genomes with ~400-500 genes
- Essential genes are typically enriched in core metabolism, translation, and DNA replication

### Metabolic Core vs Periphery
- Central metabolism (glycolysis, TCA, pentose phosphate pathway) is highly conserved across bacteria
- Amino acid biosynthesis pathways vary by nutritional environment (auxotrophs vs prototrophs)
- Cofactor biosynthesis pathways are often essential despite low flux rates

### Linking Genotype to Biochemistry
- Gene-protein-reaction (GPR) associations enable mapping from essentiality data to metabolic reactions
- ModelSEED provides comprehensive biochemical reaction database with EC number mappings
- eggNOG annotations provide high-quality EC assignments for bacterial genes

### Gaps in Current Knowledge
- Most studies focus on individual species or small sets of model organisms
- No systematic pan-bacterial analysis linking experimental essentiality to biochemical reactions
- Unclear which reactions are universally essential vs environmentally/phylogenetically conditional

## Approach

### Data Sources

| Source | Purpose | Scale | Filter Strategy |
|--------|---------|-------|----------------|
| `projects/essential_genome/data/essential_families.tsv` | Universally essential gene families (859 families) | 859 families, 48 organisms | Precomputed, reuse via MinIO |
| `kbase_ke_pangenome.eggnog_mapper_annotations` | EC numbers for gene clusters | 93M annotations | Join on gene_cluster_id from essential families |
| `kbase_msd_biochemistry.reaction` | Biochemical reactions | 56K reactions | Filter by EC numbers from essential genes |
| `kbase_msd_biochemistry.reaction_ec` | EC → reaction mappings | Small | Join table for EC lookups |

### Workflow

This project tests the new local BERDL workflow with both MinIO data access and Spark Connect queries.

**MinIO Operations** (test data download/upload):
1. Download existing essential gene data: `mc cp --recursive berdl-minio/.../microbialdiscoveryforge/projects/essential_genome/data/ ./data/`
2. Upload results: `python tools/lakehouse_upload.py essential_metabolome`

**Spark Connect Queries** (test local query execution):
1. Extract EC annotations for essential gene clusters
2. Join EC numbers to ModelSEED reactions
3. Query reaction properties (reversibility, pathways, cofactors)

### Analysis Plan

#### Notebook 1: Data Extraction & Linking (`01_data_extraction.ipynb`)

**Goal**: Map essential gene families → EC numbers → biochemical reactions

**Steps**:
1. Load essential families from MinIO or local cache (`essential_genome/data/essential_families.tsv`)
2. Extract gene cluster IDs for universal essential families (859 families present in all 48 organisms)
3. Query `eggnog_mapper_annotations` to get EC numbers for essential clusters (Spark Connect)
4. Query `kbase_msd_biochemistry` to map EC → reactions (Spark Connect)
5. Filter to reactions with complete GPR associations (all constituent genes are essential)

**Expected output**:
- `data/essential_gene_clusters.tsv` — gene clusters in universal essential families
- `data/essential_ec_numbers.tsv` — EC numbers from essential genes
- `data/essential_reactions.tsv` — reactions catalyzed by essential genes
- `data/universal_essential_reactions.tsv` — reactions present in all 48 organisms

**Spark Connect test**: Medium-scale join (859 families → ~5K gene clusters → ~2K EC numbers → ~1K reactions)

#### Notebook 2: Metabolic Network Analysis (`02_metabolic_analysis.ipynb`)

**Goal**: Characterize the essential metabolome and test hypotheses

**Analyses**:

1. **Reaction coverage**:
   - How many reactions are universally essential? (all 48 organisms)
   - How many are essential in ≥90% of organisms? ≥50%?
   - Species-specific essential reactions

2. **Pathway enrichment**:
   - Which ModelSEED pathways are enriched in essential reactions?
   - Compare to background (all annotated reactions)
   - Fisher's exact test with FDR correction

3. **Cofactor dependency**:
   - Frequency of ATP, NAD+, NADP+, CoA, FAD in essential vs non-essential reactions
   - Chi-squared test for enrichment

4. **Reaction properties**:
   - Reversibility (reversible vs irreversible)
   - Stoichiometry complexity (number of reactants/products)
   - Reaction class distribution (oxidoreductase, transferase, hydrolase, etc.)

5. **Network analysis**:
   - Build metabolic network from ModelSEED (nodes = compounds, edges = reactions)
   - Calculate betweenness centrality for essential vs non-essential reactions
   - Identify critical connectors in the metabolic network

**Expected outputs**:
- `figures/reaction_coverage.png` — histogram of reaction prevalence
- `figures/pathway_enrichment.png` — bar chart of enriched pathways
- `figures/cofactor_dependency.png` — cofactor frequency in essential reactions
- `figures/network_centrality.png` — centrality distributions
- `data/pathway_enrichment.tsv` — statistical test results
- `data/reaction_properties.tsv` — properties of essential vs non-essential reactions

**Local analysis test**: Network analysis (igraph/networkx), statistical tests (scipy), plotting (matplotlib/seaborn)

### Performance Considerations

**Spark queries**:
- Essential gene cluster query: ~859 families → ~5K clusters (small, fast)
- eggNOG annotation join: ~5K clusters → ~93M table (indexed on query_name, should be fast)
- Biochemistry queries: Small tables (<100K rows), can scan or use exact lookups

**Local analysis**:
- Network analysis on ~1K essential reactions + ~10K background reactions (manageable)
- All datasets small enough for pandas/local processing after Spark extraction

**Estimated runtime**:
- NB01 (Spark extraction): 5-10 minutes
- NB02 (local analysis): 5-10 minutes

## Expected Outcomes

### If H1 is supported (universal essential core exists):
- Identify 100-500 universally essential reactions (present in all 48 organisms)
- Essential reactions will cluster in central metabolism (glycolysis, TCA, nucleotide biosynthesis)
- High betweenness centrality in metabolic network (critical connectors)
- Provides first experimental catalog of pan-bacterial essential metabolome

### If H0 is not rejected (no universal core):
- Essential reactions are highly species-specific
- Nutritional environment determines essential metabolism (auxotrophs vs prototrophs)
- Phylogenetic constraint dominates (different essential pathways in different phyla)

### Potential Confounders
- **Growth medium dependency**: RB-TnSeq experiments use rich media; genes for biosynthesis pathways may appear non-essential due to nutrient supplementation
- **Genetic redundancy**: Isozymes and alternative pathways can mask essentiality
- **Incomplete annotations**: Not all essential genes have EC assignments (hypothetical proteins)
- **ModelSEED coverage**: Some bacterial-specific reactions may be missing from ModelSEED
- **Species bias**: 48 FB organisms are phylogenetically biased (many Proteobacteria); may not represent all bacterial diversity

## Validation Strategy

1. **Compare to minimal genome studies**: Do our essential reactions overlap with JCVI-syn3.0 metabolic requirements?
2. **Cross-reference with iModulon analysis**: Do essential reactions belong to core metabolic modules?
3. **Check pathway completeness**: For pathways enriched in essential reactions, are all steps essential or only key regulatory/irreversible steps?

## Revision History

- **v1** (2026-02-17): Initial plan. Approach: link essential gene families from `essential_genome` project to ModelSEED reactions via eggNOG EC annotations. Test local BERDL workflow (MinIO + Spark Connect). Two notebooks: extraction + analysis.

## Authors

Paramvir Dehal (ORCID: 0000-0001-5810-2497, Lawrence Berkeley National Lab)

---

## REVISION: Pivot to Pathway-Level Analysis

**Date**: 2026-02-17  
**Reason**: Biochemistry database lacks EC → reaction mappings (see `docs/schemas/biochemistry.md`)

### Revised Research Question

**Which metabolic pathways are universally complete across bacteria with essential genes, and what does the essential metabolic repertoire reveal about minimal cellular requirements?**

### Revised Hypotheses

- **H0**: No conserved set of universally complete metabolic pathways; metabolic capabilities are highly species-specific
- **H1**: A core set of metabolic pathways (amino acid biosynthesis, central carbon metabolism) is universally complete across bacteria, representing the minimal metabolic repertoire

### Revised Approach: GapMind Pathway Analysis

**Data Sources**:

| Source | Purpose | Scale | Strategy |
|--------|---------|-------|----------|
| `projects/essential_genome/data/` | 48 organisms with essential gene data | 859 universal families | Reference from lakehouse |
| `kbase_ke_pangenome.gapmind_pathways` | Pathway completeness predictions | 305M predictions | Filter to 48 FB organisms |
| `kbase_ke_pangenome.genome` | Genome metadata | 293K genomes | Map FB organisms to genome IDs |

**GapMind Pathway Data**:
- **80 pathways**: 18 amino acids + 62 carbon sources
- **Score categories**: complete, likely_complete, steps_missing_low/medium, not_present
- **Sequence scope**: aux (can import), all (make OR import), core (in all strains)
- **Metabolic categories**: amino acids (aa), carbon sources (carbon)

**Analysis Plan**:

1. **Map FB organisms to genome IDs** (48 organisms from essential_genome)
2. **Extract GapMind predictions** for those 48 genomes
3. **Identify universally complete pathways**:
   - Pathways that are "complete" or "likely_complete" in all 48 organisms
   - Focus on amino acid biosynthesis (essential metabolism)
4. **Characterize essential metabolic repertoire**:
   - Which amino acids can all bacteria synthesize?
   - Which carbon sources can all utilize?
   - Core vs peripheral metabolism
5. **Compare to minimal genomes** (JCVI-syn3.0, literature)

**Expected Outcomes**:
- Catalog of universally complete metabolic pathways
- Minimal metabolic repertoire required for bacterial life
- Amino acid biosynthesis capabilities (auxotrophs vs prototrophs)
- Comparison to synthetic minimal genomes

**Advantages over EC→reaction approach**:
- Pathway-level analysis is more biologically meaningful
- GapMind data already in BERDL (no external mappings needed)
- Directly answers "what can bacteria do?" vs "what reactions exist?"
- Aligns with minimal genome research (pathway completeness)

---

## Revision History

- **v2** (2026-02-17): Pivoted from EC→reaction to GapMind pathway analysis due to missing EC mappings in biochemistry database. Focus on pathway completeness in 48 FB organisms. More biologically meaningful approach.
- **v1** (2026-02-17): Initial plan - EC number to biochemical reaction mapping

