# Antibiotic Resistance Hotspots: Analysis Checklist

Use this checklist to track progress through the project phases.

## Phase 1: Data Exploration (Notebook 01)

- [ ] Verify BERDL access and Spark session
- [ ] List available collections
- [ ] Explore pangenome tables (`pangenome`, `genome`, `gene`, `orthogroup`)
- [ ] Check GTDB taxonomy table
- [ ] Count total genomes, genes, and orthogroups
- [ ] Identify metadata fields (genome sources, environmental origin)
- [ ] Document table schemas and row counts
- [ ] Review gene annotation availability

**Deliverables:**
- [ ] Table schema documentation
- [ ] Row count summary
- [ ] Data quality assessment

---

## Phase 2: ARG Identification (Notebook 02)

- [ ] Download CARD database (https://card.mcmaster.ca/)
- [ ] Parse ResFinder annotations
- [ ] Create ARG reference dataset with gene names and drug classes
- [ ] Query BERDL for gene descriptions/functions
- [ ] Implement keyword matching for ARG detection
- [ ] Perform homology search (BLASTP) if needed for annotation matching
- [ ] Create comprehensive ARG annotation table
- [ ] Export to `data/arg_annotations.csv`

**Deliverables:**
- [ ] `data/arg_annotations.csv` with columns:
  - `gene_id`, `orthogroup_id`, `arg_name`, `drug_class`, `resistance_mechanism`, `source_db`, `confidence`

---

## Phase 3: Distribution Analysis (Notebook 03)

- [ ] Calculate ARG prevalence by species
  - [ ] Total genomes per species
  - [ ] Genomes with ARGs per species
  - [ ] Prevalence percentages
- [ ] Identify hotspot species (top 20-50 by prevalence/diversity)
- [ ] Analyze distribution by drug class
- [ ] Test for phylogenetic patterns
- [ ] Correlate with environment (if available)
- [ ] Create prevalence rankings
- [ ] Export to `data/hotspot_species.csv`

**Deliverables:**
- [ ] `data/hotspot_species.csv` ranking species by ARG metrics
- [ ] Prevalence distribution statistics
- [ ] Top hotspot species list with profiles

---

## Phase 4: Pangenome Analysis (Notebook 04)

- [ ] Classify genes as core/accessory/unique for each species
  - [ ] Core: ≥95% genome presence
  - [ ] Accessory: <95% but >0%
  - [ ] Unique: single genome only
- [ ] Calculate pangenome metrics:
  - [ ] Core genome size
  - [ ] Accessory genome size
  - [ ] Openness scores
- [ ] Test if ARGs are preferentially core/accessory/unique
- [ ] Correlate pangenome openness with ARG diversity
- [ ] Statistical tests (Pearson/Spearman correlations)

**Deliverables:**
- [ ] Pangenome classification data
- [ ] Correlation analysis results
- [ ] Openness vs. ARG diversity figures

---

## Phase 5: Fitness Analysis (Notebook 05)

- [ ] Explore fitness browser tables
- [ ] Map ARG genes to fitness data (handling ID format conversions)
- [ ] Extract fitness scores for ARG genes
- [ ] Calculate fitness effects across conditions
- [ ] Compare ARG fitness to background distribution
- [ ] Identify conditions with strong effects
- [ ] Analyze trade-offs (prevalence vs. fitness cost)
- [ ] Export to `data/fitness_results.csv`

**Deliverables:**
- [ ] `data/fitness_results.csv` with fitness data
- [ ] Trade-off analysis results
- [ ] Condition-specific fitness landscapes

---

## Phase 6: Visualization & Dashboards (Notebook 06)

### Figures for Publication

- [ ] **Figure 1**: Top hotspot species (bar chart)
  - X: species name
  - Y: ARG prevalence
  - Color: by drug class

- [ ] **Figure 2**: Phylogenetic distribution
  - Tree diagram with ARG heatmap overlay
  - Shows prevalence at major taxonomic levels

- [ ] **Figure 3**: Fitness trade-offs
  - X: ARG prevalence
  - Y: fitness cost
  - Size: ARG diversity

- [ ] **Figure 4**: Pangenome openness vs. ARG diversity
  - X: openness score
  - Y: ARG diversity
  - Regression line with R²

### Interactive Dashboards

- [ ] Build Plotly dashboard with:
  - [ ] Drug class filter
  - [ ] Phylogenetic level selector
  - [ ] Prevalence range slider
  - [ ] Environment filter (if applicable)
  - [ ] Interactive species search
  - [ ] Mouse-over gene details

### Summary Statistics

- [ ] Generate statistics file: `results/summary_statistics.txt`
  - Total ARGs identified
  - Number of hotspot species
  - Average prevalence
  - Fitness trade-off correlations
  - Key findings

**Deliverables:**
- [ ] `figures/arg_prevalence.png`
- [ ] `figures/phylogenetic_distribution.png`
- [ ] `figures/fitness_tradeoffs.png`
- [ ] `figures/pangenome_analysis.png`
- [ ] Interactive dashboard (HTML/Plotly)
- [ ] `results/summary_statistics.txt`

---

## Documentation & Publication

- [ ] Document discoveries in `../../docs/discoveries.md`
- [ ] Add SQL patterns to `../../docs/pitfalls.md`
- [ ] Record lessons learned and challenges
- [ ] Identify future research directions
- [ ] Prepare manuscript outline
- [ ] Create reproducible analysis report

**Deliverables:**
- [ ] Entries in shared documentation
- [ ] Analysis report
- [ ] Reproducible code comments

---

## Data Quality & Validation

- [ ] Verify ARG annotation accuracy (manual spot checks)
- [ ] Check for duplicates and missing data
- [ ] Validate BERDL query results
- [ ] Cross-check with published databases
- [ ] Document any data limitations

---

## Final Validation

- [ ] All notebooks run without errors
- [ ] All data files generated successfully
- [ ] All figures meet publication standards
- [ ] Results are reproducible
- [ ] Documentation is complete
- [ ] Ready for submission/sharing

---

## Notes & Issues Encountered

Use this section to document challenges, workarounds, and lessons learned:

```
[Add notes as you progress through the project]
```

---

## Status Summary

**Last Updated:** [Date]
**Current Phase:** [1-6]
**% Complete:** [0-100%]

Overall progress:
- [ ] 0-20% (Exploring)
- [ ] 20-40% (ARG Identification)
- [ ] 40-60% (Analysis)
- [ ] 60-80% (Visualization)
- [ ] 80-100% (Finalization)
