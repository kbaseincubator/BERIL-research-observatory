# M. extorquens Pangenome Case Study: B Vitamin Auxotrophy and Lanthanide-Dependent MDH

## Research Question

*Methylobacterium extorquens* AM1 carries two methanol dehydrogenases: the lanthanide-dependent XoxF and the calcium-dependent MxaF. We ask:

1. **B vitamin biosynthesis**: Is *M. extorquens* auxotrophic for any B vitamins? Which pathways are complete vs incomplete?
2. **xoxF/mxaF classification**: eggNOG `Preferred_name` misannotates xoxF as mxaF. Can EC/KEGG reliably distinguish them?
3. **Cross-species MDH profiles**: Across *Methylobacterium*, how does the xoxF/mxaF distribution change when using EC/KEGG instead of gene names?

## Key Findings

### eggNOG Misannotation of Lanthanide-Dependent MDH

eggNOG systematically labels xoxF (EC 1.1.2.8 / K00114) as `Preferred_name = 'mxaF'` in *Methylobacterium*. In *M. extorquens*, 4 of 5 gene clusters annotated as "mxaF" actually carry EC 1.1.2.8 / K00114 (xoxF markers), not EC 1.1.2.7 / K14028 (true mxaF). Reclassification using EC numbers and KEGG orthologs completely inverted the MDH profile across 49 species:

- **Gene-name-based (wrong)**: 44 mxaF-only / 5 BOTH / 0 xoxF-only
- **EC/KEGG-based (corrected)**: 0 mxaF-only / 39 BOTH / 10 xoxF-only

Lanthanide-dependent methanol oxidation (xoxF) is ubiquitous in *Methylobacterium*, not rare. Every species with MDH annotations carries xoxF; no species has mxaF without xoxF.

### B Vitamin Auxotrophy Predictions

- **Riboflavin (B2)**: 67% complete (missing ribA, ribC across all strains) -- strongest auxotrophy signal
- **Thiamine (B1)**: 75% complete (missing thiM, thiO)
- **Cobalamin (B12)**: 83% complete after removing bch* contamination -- above 80% threshold, but high core/accessory variability of cob genes (cobA through cobT appear as core, auxiliary, AND singleton) suggests strain-specific B12 requirements
- **Biotin (B7), Folate (B9)**: 100% complete
- **Pyridoxine (B6)**: 80% complete (missing pdxK, a salvage kinase rather than de novo synthesis gene)

### B12 Core/Accessory Variability

B12 biosynthesis shows the most striking core/accessory variation of any pathway. Many cob genes appear simultaneously as core, auxiliary, and singleton across *M. extorquens* strains -- different strains carry different subsets. This is the strongest signal for strain-specific B12 requirements and suggests *M. extorquens* strains differ in cobalamin self-sufficiency.

### Pathway Definition Audit

Tightened the B vitamin classifier to match by gene name and KEGG KO only (not KEGG pathway number), removing contamination from bacteriochlorophyll (bch\*) in B12 and molybdopterin/queuosine (moa\*/que\*) in B9. Added pabA/pabB (para-aminobenzoate synthase) to B9 as direct folate precursors.

### MDH and B Vitamin Independence

B vitamin gene counts are nearly identical between BOTH (54.5 +/- 6.9 genes) and xoxF_only (54.3 +/- 6.5 genes) species -- MDH profile does not predict B vitamin biosynthetic capacity.

## Interpretation

### Literature Context

- **xoxF ubiquity** aligns with Pol et al. (2014), who first demonstrated rare earth-dependent methanol oxidation, and Keltjens et al. (2014), who showed XoxF is more widely distributed than MxaF across methylotrophs. Our pangenome-scale analysis confirms this at the genus level: all 49 *Methylobacterium* species carry xoxF.
- **Lanthanide switch**: Masuda et al. (2016) showed that *M. extorquens* AM1 reciprocally regulates mxaF and xoxF expression depending on lanthanide availability. The 39 species carrying BOTH enzymes likely maintain this regulatory switch, while the 10 xoxF-only species may be obligately lanthanide-dependent.
- **Annotation misannotation** is a known problem in public databases. Schnoes et al. (2009) found misannotation rates of 5-63% across enzyme superfamilies in GenBank, TrEMBL, and KEGG. Our finding that eggNOG systematically misannotates xoxF as mxaF is a specific, high-impact instance of this broader problem -- particularly since xoxF and mxaF share ~50% sequence identity (Schmidt et al., 2010) but differ in cofactor requirements.
- **B vitamin auxotrophy predictions** are consistent with the broader pattern of B vitamin auxotrophies in phyllosphere bacteria. Ryback et al. (2022) found up to half of leaf-associated bacteria are auxotrophic for one or more B vitamins. The Black Queen Hypothesis (Morris et al., 2012) provides the evolutionary framework: biosynthetic genes can be adaptively lost when vitamins are available from community members. Standard *M. extorquens* AM1 minimal media formulations vary in vitamin supplementation; our predictions that riboflavin and thiamine should enhance growth are testable.
- **Taxonomy**: Green & Ardley (2018) proposed splitting *Methylobacterium* into *Methylobacterium* and *Methylorubrum*, but recent phylogenomics (Hesse et al., 2022) supports monophyly. GTDB retains *Methylobacterium*; our analysis includes both names to ensure completeness.

### Limitations

- Missing annotations may reflect gaps in eggNOG sensitivity rather than true gene absence; auxotrophy predictions require experimental validation
- Pathway completeness is based on a curated but not exhaustive gene list; alternative biosynthesis routes may exist
- The 80% completeness threshold for auxotrophy prediction is heuristic, not empirically validated
- Cross-species MDH classification depends on EC/KEGG annotation quality; clusters lacking both EC and KEGG_ko fall back to Preferred_name (zero ambiguous clusters in this dataset)

### Testable Predictions

1. *M. extorquens* AM1 growth should be enhanced by supplementing riboflavin and/or thiamine
2. Different strains may have different B12 requirements given the high core/accessory variability of cob genes
3. xoxF-only *Methylobacterium* species should grow poorly without lanthanide supplementation, while BOTH species should switch between XoxF and MxaF depending on lanthanide availability

## Future Directions

1. Validate auxotrophy predictions with growth experiments (vitamin dropout media)
2. Sequence-level phylogenetic analysis of PQQ MDH genes to further validate xoxF vs mxaF identity beyond EC/KEGG
3. Extend MDH classification to other methylotrophic genera (Methylocystis, Methylomonas, Methylophaga)
4. Cross-reference with environmental metadata analysis in the `gene_environment_association` project

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

## References

- Cotruvo JA Jr. (2019). The chemistry of lanthanides in biology: recent discoveries, emerging principles, and technological applications. *ACS Central Science*, 5(9), 1496-1506.
- Green PN, Ardley JK. (2018). Review of the genus *Methylobacterium* and closely related organisms: a proposal that some *Methylobacterium* species be reclassified into a new genus, *Methylorubrum* gen. nov. *Int J Syst Evol Microbiol*, 68(9), 2727-2748.
- Hesse C, et al. (2022). Comprehensive phylogenomics of *Methylobacterium* reveals four evolutionary distinct groups and underappreciated phyllosphere diversity. *Genome Biol Evol*, 14(8), evac123.
- Keltjens JT, et al. (2014). PQQ-dependent methanol dehydrogenases: rare-earth elements make a difference. *Appl Microbiol Biotechnol*, 98(14), 6163-6183.
- Marx CJ, et al. (2012). Complete genome sequences of six strains of the genus *Methylobacterium*. *J Bacteriol*, 194(17), 4746-4748.
- Masuda S, et al. (2016). Lanthanide-dependent regulation of methanol oxidation systems in *Methylobacterium extorquens* AM1 and their contribution to methanol growth. *J Bacteriol*, 198(8), 1250-1260.
- Morris JJ, Lenski RE, Zinser ER. (2012). The Black Queen Hypothesis: evolution of dependencies through adaptive gene loss. *mBio*, 3(2), e00036-12.
- Pol A, et al. (2014). Rare earth metals are essential for methanotrophic life in volcanic mudpots. *Environ Microbiol*, 16(1), 255-264.
- Ryback B, Bortfeld-Miller M, Vorholt JA. (2022). Metabolic adaptation to vitamin auxotrophy by leaf-associated bacteria. *ISME J*, 16(12), 2712-2724.
- Schnoes AM, et al. (2009). Annotation error in public databases: misannotation of molecular function in enzyme superfamilies. *PLoS Comput Biol*, 5(12), e1000605.
- Vuilleumier S, et al. (2009). *Methylobacterium* genome sequences: a reference blueprint to investigate microbial metabolism of C1 compounds from natural and industrial sources. *PLoS One*, 4(5), e5584.

## Authors

- **Mark A. Miller** (Lawrence Berkeley National Lab)
