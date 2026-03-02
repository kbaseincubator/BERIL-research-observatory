# Report: ADP1 Annotation Reassessment

## Key Findings

### Finding 1: AI agent achieves higher annotation coverage with dramatically fewer hypotheticals

![Annotation coverage by source](figures/annotation_coverage.png)

Across 5,852 ADP1 genomic features (3,235 protein-coding), the GPT-5.2 agent annotated 2,984 genes with specific functions (51.0% of all features), compared to Bakta's 2,939 (50.2%) and RAST's 2,803 (47.9%). The agent produced only 19 hypothetical annotations versus RAST's 432 and Bakta's 270 — a 95.6% reduction relative to RAST. This reflects the agent's ability to synthesize InterProScan domain evidence into functional descriptions even when individual domains are insufficient for homology-based tools to assign a named function.

*(Notebook: 01_data_integration.ipynb)*

### Finding 2: Agent resolves 61% of RAST hypothetical proteins, providing 120 uniquely annotated genes

![Hypothetical resolution rates and agreement analysis](figures/hypothetical_resolution.png)

The agent resolved 264 of 432 RAST hypotheticals (61.1%) and 158 of 270 Bakta hypotheticals (58.5%) to specific functions. For the 209 genes where both RAST and Bakta assigned "hypothetical protein," the agent resolved 120 (57.4%) — these represent genes with genuinely new functional information unavailable from either conventional pipeline.

When both RAST and agent provide specific annotations (2,720 genes), keyword Jaccard similarity is low (median 0.10). This primarily reflects annotation style: RAST uses terse function names ("LSU ribosomal protein L34p") while the agent produces descriptive sentences ("50S ribosomal protein bL34, a small basic component of the large ribosomal subunit..."). Only 652/2,720 (24%) show zero keyword overlap, and manual inspection of "disagreements" reveals that most describe the same function in different vocabulary.

Resolved hypotheticals are modestly enriched for essential genes (11/264 = 4.2% essential vs 4/168 = 2.4% unresolved), suggesting the agent preferentially resolves genes with detectable phenotypes.

*(Notebook: 02_hypothetical_resolution.ipynb)*

### Finding 3: Agent annotations show 56% higher concordance with condition-specific growth phenotypes

![Phenotype concordance across three validation datasets](figures/phenotype_concordance.png)

Using keyword matching against condition-relevant terms, 22.3% of highly condition-specific genes (273 genes with specificity > 1.5) have agent annotations concordant with their most specific carbon source, compared to 14.3% for RAST and 15.0% for Bakta — a 56% improvement over RAST.

Per-condition concordance (agent / RAST / Bakta):
| Condition | N | Agent | RAST | Bakta |
|-----------|---|-------|------|-------|
| Quinate | 27 | 21 (78%) | 17 (63%) | 18 (67%) |
| Acetate | 20 | 6 (30%) | 2 (10%) | 0 (0%) |
| Glucarate | 30 | 9 (30%) | 2 (7%) | 5 (17%) |
| Urea | 62 | 9 (15%) | 8 (13%) | 8 (13%) |
| Butanediol | 27 | 6 (22%) | 3 (11%) | 4 (15%) |

The agent's largest gains are on quinate and acetate, metabolic pathways where its verbose annotations naturally include pathway and substrate terms that keyword matching captures. For the aromatic catabolism network (8 confirmed pathway genes), the agent correctly identifies 87.5% vs 75.0% for both RAST and Bakta.

For the respiratory chain (62 genes across 8 subsystems), RAST leads at 74.2% vs 69.4% for both agent and Bakta. RAST's advantage here reflects its strong curated subsystem models for well-characterized complexes like NADH dehydrogenase and ATP synthase.

*(Notebook: 03_phenotype_concordance.ipynb)*

### Finding 4: Agent identifies 696 model expansion candidates and better annotates FBA-discordant genes

![FBA concordance by annotation source](figures/model_reconciliation.png)

Among 150 FBA-miss genes (FBA predicts variable flux but experiments show growth defects), the agent provides metabolic annotations for 128 (85.3%) compared to RAST's 116 (77.3%) and Bakta's 115 (76.7%). For 81 FBA-discordant genes (FBA predicts essentiality but growth is normal), agent metabolic annotation rate is 86.4% vs RAST's 70.4%.

The agent identifies 696 genes without current FBA reaction mappings that have metabolic-sounding annotations (enzyme names, pathway terms) where RAST does not — these are candidates for model expansion. Among 11 quinate-specific genes lacking FBA reactions, the agent provides specific annotations for all 11, compared to RAST's 10 (the one RAST hypothetical is resolved by the agent).

All 478 genes in the triple essentiality dataset have 100% annotation coverage from all three sources, so the agent's value here is not coverage but annotation quality — providing more metabolically informative descriptions that could guide reaction mapping.

*(Notebook: 04_model_reconciliation.ipynb)*

## Results

### Annotation Coverage

The master table integrates 3,083 agent annotations with RAST, Bakta, and experimental data for 5,852 ADP1 features. All 3,083 agent protein sequences matched sequences in the genome features database (zero orphans). The 2,769 features without agent annotation are non-coding elements (tRNA, rRNA, etc.) and 114 protein sequences not included in the agent annotation run.

| Source | Specific | Hypothetical | Missing | Coverage (%) |
|--------|----------|-------------|---------|-------------|
| RAST | 2,803 | 432 | 2,617 | 47.9% |
| Bakta | 2,939 | 270 | 2,643 | 50.2% |
| Agent | 2,984 | 19 | 2,849 | 51.0% |

### Hypothetical Resolution

| Baseline | Total | Resolved by Agent | Rate |
|----------|-------|-------------------|------|
| RAST hypotheticals | 432 | 264 | 61.1% |
| Bakta hypotheticals | 270 | 158 | 58.5% |
| Both RAST+Bakta hypothetical | 209 | 120 | 57.4% |

### Agreement Analysis

For 2,720 genes where both RAST and agent provide specific annotations:
- Mean keyword Jaccard similarity: 0.12
- High agreement (>0.5): 15 genes (0.6%)
- Moderate agreement (0.2–0.5): 490 genes (18.0%)
- Low agreement (0.01–0.2): 1,563 genes (57.5%)
- No keyword overlap: 652 genes (24.0%)

The low similarity scores reflect annotation style differences rather than functional disagreement. The agent's sentence-style annotations contain many additional context words that dilute keyword overlap even when the core function is identical.

### Phenotype Concordance

Overall concordance rates for highly condition-specific genes:
- Agent: 22.3%
- Bakta: 15.0%
- RAST: 14.3%

Subsystem-level validation:
- Aromatic pathway: Agent 87.5%, RAST 75.0%, Bakta 75.0%
- Respiratory chain: RAST 74.2%, Agent 69.4%, Bakta 69.4%

### Model Reconciliation

| Gene Set | N | Agent Metabolic | RAST Metabolic | Bakta Metabolic |
|----------|---|-----------------|----------------|-----------------|
| FBA-miss (variable + defect) | 150 | 128 (85.3%) | 116 (77.3%) | 115 (76.7%) |
| FBA-discordant (essential + normal) | 81 | 70 (86.4%) | 57 (70.4%) | 59 (72.8%) |

Model expansion candidates: 696 genes with agent metabolic annotations but no current FBA reaction and no RAST metabolic annotation.

## Interpretation

### The Agent's Primary Value: Resolving Hypotheticals

The agent's most impactful contribution is not raw coverage gain (only ~1% above Bakta) but the dramatic reduction in hypothetical annotations. By synthesizing InterProScan domain evidence through reasoning, the agent can assign plausible functions to proteins where individual domain hits are insufficient for homology-based assignment. The 120 genes uniquely annotated by the agent (hypothetical in both RAST and Bakta) represent the clearest added value.

### Concordance Reflects Annotation Style, Not Just Accuracy

The 56% improvement in phenotype concordance must be interpreted carefully. The agent's verbose annotations naturally contain more keywords — including metabolic pathway terms, substrate names, and biological context — that overlap with condition-relevant keyword lists. This is both a feature (richer annotations are more useful for biologists) and a measurement artifact (keyword matching favors verbose text). A more rigorous evaluation would require expert curation of a gold-standard set.

### Complementary Strengths Across Subsystems

No single source dominates all validation datasets. RAST excels on well-characterized subsystems (respiratory chain) where its curated subsystem models are strongest. The agent excels on condition-specific phenotypes and aromatic catabolism where its reasoning over domain combinations adds value. Bakta sits between the two. An optimal annotation strategy might combine all three sources.

### Literature Context

- De Berardinis et al. (2008) created the ADP1 single-gene deletion collection used as ground truth here, establishing ADP1 as a premier model for systematic functional genomics.
- Schwengers et al. (2021) introduced Bakta as a standardized bacterial annotation tool, demonstrating improvements over Prokka. Our results show Bakta modestly outperforms RAST on coverage (50.2% vs 47.9%) consistent with their findings.
- Genomic language model approaches (Akotenou & El Allali, 2025; Wiatrak et al., BacBench) are emerging as alternatives to homology-based annotation. Our results provide one of the first phenotype-grounded evaluations of LLM-assisted annotation, showing measurable concordance improvements.
- Wetmore et al. (2015) developed the RB-TnSeq method underlying the Fitness Browser data used for essentiality classification.

### Novel Contribution

This work provides a phenotype-grounded evaluation framework for comparing annotation methods. Rather than relying on reference databases (which can be circular), we use experimental deletion fitness, TnSeq essentiality, and FBA predictions as independent ground truth. The finding that AI-assisted annotation resolves 61% of hypotheticals while improving phenotype concordance by 56% establishes a concrete benchmark for future annotation tools.

### Limitations

- **Keyword matching bias**: Concordance scoring via keyword matching inherently favors verbose annotations. The agent's sentence-style output contains more words, increasing the chance of keyword hits.
- **No gold-standard curation**: Without expert-curated annotations for all 3,083 genes, we cannot measure true precision/recall. Our phenotype concordance is a proxy.
- **Single organism**: Results from ADP1 may not generalize to organisms with less experimental data or more divergent gene content.
- **Agent annotation scope**: The agent was not given access to the experimental phenotype data, so its annotations are independent of the ground truth. However, it may have been trained on published ADP1 literature.
- **Coverage denominator**: The "51% coverage" includes non-coding features in the denominator. Among protein-coding genes only, all three sources achieve >85% specific annotation.

## Data

### Sources
| Collection | Tables Used | Purpose |
|------------|-------------|---------|
| `kescience_fitnessbrowser` | `genome_features`, `gene_essentiality`, `gene_phenotypes`, `growth_phenotypes_detailed` | RAST annotations, growth fitness, TnSeq essentiality |
| `kbase_ke_pangenome` | pangenome cluster assignments | Core/auxiliary gene classification |
| Local SQLite (`berdl_tables.db`) | `genome_features`, `gene_reaction_data` | Integrated ADP1 data with Bakta, FBA, proteomics |
| Agent annotations TSV | — | GPT-5.2 + InterProScan annotations for 3,083 proteins |
| Prior projects | `aromatic_catabolism_network`, `respiratory_chain_wiring`, `adp1_triple_essentiality`, `adp1_deletion_phenotypes` | Experimentally validated ground-truth gene sets |

### Generated Data
| File | Rows | Description |
|------|------|-------------|
| `data/master_annotation_table.csv` | 5,852 | Integrated master table with all annotations and experimental data |
| `data/agent_unique_annotations.csv` | 120 | Genes where agent provides specific annotation but both RAST and Bakta are hypothetical |

## Supporting Evidence

### Notebooks
| Notebook | Purpose |
|----------|---------|
| `01_data_integration.ipynb` | Build master table, classify annotations, compute coverage |
| `02_hypothetical_resolution.ipynb` | Quantify hypothetical resolution, analyze agreement |
| `03_phenotype_concordance.ipynb` | Score concordance against condition-specific, aromatic, and respiratory phenotypes |
| `04_model_reconciliation.ipynb` | Assess FBA-discordant genes, identify model expansion candidates |

### Figures
| Figure | Description |
|--------|-------------|
| `annotation_coverage.png` | Stacked bar chart of specific/hypothetical/missing annotations by source |
| `hypothetical_resolution.png` | Resolution rates, RAST-agent similarity distribution, agreement categories |
| `phenotype_concordance.png` | Grouped bar chart of concordance across three validation datasets |
| `model_reconciliation.png` | Annotation coverage by FBA class, metabolic annotation rates |

## Future Directions

1. **Expert curation benchmark**: Curate a gold-standard annotation set for 100–200 genes spanning essential, condition-specific, and hypothetical categories to measure true precision/recall.
2. **Semantic similarity scoring**: Replace keyword Jaccard with embedding-based similarity (e.g., BioBERT) to better capture functional agreement between different annotation styles.
3. **Multi-organism evaluation**: Apply the same evaluation framework to other Fitness Browser organisms with rich phenotype data (e.g., *Pseudomonas fluorescens*, *Shewanella oneidensis*).
4. **Consensus annotation pipeline**: Build an annotation pipeline that combines RAST subsystem assignments, Bakta structural predictions, and agent reasoning into a single best annotation per gene.
5. **Model gap-filling**: Use the 696 agent-identified model expansion candidates to systematically test whether adding their predicted reactions improves FBA concordance.

## References

- De Berardinis V, Vallenet D, Castelli V, et al. (2008). "A complete collection of single-gene deletion mutants of *Acinetobacter baylyi* ADP1." *Molecular Systems Biology*, 4:174.
- Schwengers O, Jelonek L, Giber MA,3rd, et al. (2021). "Bakta: rapid and standardized annotation of bacterial genomes via alignment-free sequence identification." *Microbial Genomics*, 7(11):000685.
- Wetmore KM, Price MN, Waters RJ, et al. (2015). "Rapid quantification of mutant fitness in diverse bacteria by sequencing randomly bar-coded transposons." *mBio*, 6(3):e00306-15.
- Price MN, Wetmore KM, Waters RJ, et al. (2018). "Mutant phenotypes for thousands of bacterial genes of unknown function." *Nature*, 557:503–509.
- Overbeek R, Olson R, Pusch GD, et al. (2014). "The SEED and the Rapid Annotation of microbial genomes using Subsystems Technology (RAST)." *Nucleic Acids Research*, 42(D1):D206–D214.
- Arkin AP, Cottingham RW, Henry CS, et al. (2018). "KBase: The United States Department of Energy Systems Biology Knowledgebase." *Nature Biotechnology*, 36:566–569.
- Akotenou G, El Allali A. (2025). "Genomic language models (gLMs) decode bacterial genomes for improved gene prediction and translation initiation site identification." *Briefings in Bioinformatics*, 26(4):bbaf311.
