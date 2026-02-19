# Research Plan: M. extorquens B Vitamin Auxotrophy and Lanthanide-Dependent MDH

## Research Question

*Methylobacterium extorquens* AM1 carries two methanol dehydrogenases: the lanthanide-dependent XoxF and the calcium-dependent MxaF. We ask:

1. **B vitamin biosynthesis**: Is *M. extorquens* auxotrophic for any B vitamins? Which pathways are complete vs incomplete?
2. **xoxF/mxaF classification**: eggNOG `Preferred_name` misannotates xoxF as mxaF. Can EC/KEGG reliably distinguish them?
3. **Cross-species MDH profiles**: Across *Methylobacterium*, how does the xoxF/mxaF distribution change when using EC/KEGG instead of gene names?

## Hypothesis

- **H1 (B vitamins)**: *M. extorquens* is auxotrophic for one or more B vitamins, consistent with the Black Queen Hypothesis prediction that phyllosphere bacteria adaptively lose biosynthetic genes when vitamins are available from community members (Morris et al., 2012; Ryback et al., 2022).
- **H2 (MDH annotation)**: EC/KEGG-based classification will reveal that xoxF is far more widespread than eggNOG gene names suggest, because eggNOG systematically misannotates xoxF as mxaF in PQQ-dependent alcohol dehydrogenases.
- **H3 (MDH-vitamin independence)**: MDH profile (xoxF-only vs BOTH) does not predict B vitamin biosynthetic capacity, since lanthanide utilization and vitamin biosynthesis are independent metabolic axes.

## Approach

### 1. B Vitamin Pathway Assessment
- Define 6 pathways (B1, B2, B6, B7, B9, B12) with expected gene lists and KEGG KOs
- Query eggNOG annotations for *M. extorquens* pangenome (22 + 4 genomes)
- Classify annotations by gene name and KEGG KO only (not KEGG pathway number, to avoid contamination from related pathways)
- Completeness = (found genes / expected genes) x 100%
- Auxotrophy predicted when completeness < 80%

### 2. xoxF/mxaF Audit
- For *M. extorquens* gene clusters annotated as "mxaF", check EC numbers and KEGG orthologs
- EC 1.1.2.7 / K14028 = true mxaF (calcium-dependent)
- EC 1.1.2.8 / K00114 = xoxF (lanthanide-dependent)
- Quantify how many "mxaF" clusters are actually xoxF by EC/KEGG

### 3. Cross-Species MDH Classification
- Query all *Methylobacterium* and *Methylorubrum* species (Green & Ardley 2018 reclassification)
- Classify each MDH cluster using EC/KEGG priority over Preferred_name
- Aggregate per species: xoxF_only / BOTH / mxaF_only
- Compare B vitamin gene counts between MDH profiles

## Data Sources

- **Database**: `kbase_ke_pangenome` on BERDL Delta Lakehouse
- **Tables**:
  - `gtdb_species_clade` - Species metadata and GTDB taxonomy
  - `pangenome` - Pangenome statistics
  - `gene_cluster` - Gene cluster classifications (core/auxiliary/singleton)
  - `eggnog_mapper_annotations` - Functional annotations (EC, KEGG_ko, Preferred_name)

## Expected Outputs

### Figures
- `bvitamin_completeness.png` - B vitamin pathway completeness across 6 pathways with core/accessory breakdown

### Notebooks
- `01_mextorquens_bvitamin_case.ipynb` - B vitamin survey, xoxF/mxaF audit, cross-species MDH classification (~15 min runtime)

## Related Projects

- **gene_environment_association** - Extends the MDH and B vitamin analysis to 209 *Methylobacterium* genomes with environment metadata (notebook 03, section 10)

## Revision History
- **v1** (2026-02): Created from README.md content
