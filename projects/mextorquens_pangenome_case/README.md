# M. extorquens Pangenome Case Study: B Vitamin Auxotrophy and Lanthanide-Dependent MDH

## Research Question

*Methylobacterium extorquens* AM1 carries two methanol dehydrogenases: the lanthanide-dependent XoxF and the calcium-dependent MxaF. We ask:

1. **B vitamin biosynthesis**: Is *M. extorquens* auxotrophic for any B vitamins? Which pathways are complete vs incomplete?
2. **xoxF/mxaF classification**: eggNOG `Preferred_name` misannotates xoxF as mxaF. Can EC/KEGG reliably distinguish them?
3. **Cross-species MDH profiles**: Across *Methylobacterium*, how does the xoxF/mxaF distribution change when using EC/KEGG instead of gene names?

## Key Findings

### eggNOG Misannotation of Lanthanide-Dependent MDH
eggNOG systematically labels xoxF (EC 1.1.2.8 / K00114) as `Preferred_name = 'mxaF'` in *Methylobacterium*. Reclassification using EC numbers and KEGG orthologs completely inverted the MDH profile:
- **Gene-name-based (wrong)**: 44 mxaF-only / 5 BOTH / 0 xoxF-only
- **EC/KEGG-based (corrected)**: 0 mxaF-only / 39 BOTH / 10 xoxF-only

Lanthanide-dependent methanol oxidation (xoxF) is ubiquitous in *Methylobacterium*, not rare.

### B Vitamin Auxotrophy Predictions
- **Riboflavin (B2)**: 67% complete (missing ribA, ribC across all strains) -- strongest auxotrophy signal
- **Thiamine (B1)**: 75% complete (missing thiM, thiO)
- **Cobalamin (B12)**: 83% complete after removing bch* contamination -- above 80% threshold, but high core/accessory variability of cob genes suggests strain-specific B12 requirements
- **Biotin (B7), Folate (B9)**: 100% complete

### Pathway Definition Audit
Tightened the B vitamin classifier to match by gene name and KEGG KO only (not KEGG pathway number), removing contamination from bacteriochlorophyll (bch*) in B12 and molybdopterin/queuosine (moa*/que*) in B9.

## Data Sources

| Source | Database | Table(s) |
|--------|----------|----------|
| Species stats | `kbase_ke_pangenome` | `gtdb_species_clade`, `pangenome` |
| Gene clusters | `kbase_ke_pangenome` | `gene_cluster` |
| Annotations | `kbase_ke_pangenome` | `eggnog_mapper_annotations` |

## Notebooks

| Notebook | Purpose | Runtime |
|----------|---------|---------|
| `01_mextorquens_bvitamin_case.ipynb` | B vitamin survey, xoxF/mxaF audit, cross-species MDH classification | ~15 min |

## Reproduction

1. Upload notebook to BERDL JupyterHub
2. Run all cells (requires Spark Connect to `kbase_ke_pangenome`)

## Authors

- **Mark A. Miller** (Lawrence Berkeley National Lab)
