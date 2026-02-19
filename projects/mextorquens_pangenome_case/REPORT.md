# Report: M. extorquens B Vitamin Auxotrophy and Lanthanide-Dependent MDH

## Key Findings

### 1. eggNOG Systematically Misannotates xoxF as mxaF

eggNOG labels xoxF (EC 1.1.2.8 / K00114, lanthanide-dependent MDH) as `Preferred_name = 'mxaF'` in *Methylobacterium*. In *M. extorquens*, 4 of 5 "mxaF" gene clusters carry EC 1.1.2.8 / K00114 (xoxF markers), not EC 1.1.2.7 / K14028 (true mxaF).

Reclassification using EC/KEGG completely inverted the MDH profile across 49 *Methylobacterium* species:

| Classification | mxaF-only | BOTH | xoxF-only |
|---|---|---|---|
| Gene-name-based (wrong) | 44 | 5 | 0 |
| EC/KEGG-based (corrected) | 0 | 39 | 10 |

**Lanthanide-dependent methanol oxidation (xoxF) is ubiquitous** — every species carries xoxF; no species has mxaF without xoxF. Zero clusters were ambiguous (lacking both EC and KEGG_ko).

### 2. B Vitamin Auxotrophy Predictions

| Pathway | Completeness | Missing genes | Status |
|---|---|---|---|
| Biotin (B7) | 100% | -- | Complete |
| Folate (B9) | 100% | -- | Complete |
| Cobalamin (B12) | 83% | btuR, cobE, cobR, cobU | Above threshold, but high core/accessory variability |
| Pyridoxine (B6) | 80% | pdxK (salvage kinase) | Borderline |
| Thiamine (B1) | 75% | thiM, thiO | **Predicted auxotrophy** |
| Riboflavin (B2) | 67% | ribA, ribC | **Predicted auxotrophy** (strongest signal) |

Riboflavin is the strongest auxotrophy signal: ribA and ribC are missing from all strains and all found rib genes are core. Thiamine is the second strongest: thiM and thiO are absent.

### 3. B12 Cobalamin Shows Strain-Specific Variability

B12 biosynthesis has the most striking core/accessory variation. Genes cobA through cobT appear simultaneously as core, auxiliary, AND singleton — meaning some strains carry them universally while others have them as accessory or unique. This predicts strain-specific B12 requirements.

### 4. Pathway Classifier Audit

The B vitamin classifier was tightened to match only by gene name and KEGG KO, removing a KEGG pathway number fallback that pulled in unrelated genes:
- **B12**: bch\* (bacteriochlorophyll) and bfr (bacterioferritin) shared KEGG map 00860 but are not cobalamin biosynthesis. Removing them raised B12 completeness from 78% to 83%.
- **B9**: moa\*/que\* (molybdopterin/queuosine) shared KEGG map 00790. Added pabA/pabB as direct folate precursors.

### 5. MDH Profile Does Not Predict B Vitamin Capacity

B vitamin gene counts are nearly identical between BOTH (54.5 +/- 6.9) and xoxF_only (54.3 +/- 6.5) species. MDH type does not predict vitamin biosynthetic capacity in *Methylobacterium*.

## Interpretation

### Literature Context

- **xoxF ubiquity** confirms Pol et al. (2014) and Keltjens et al. (2014) at pangenome scale: all 49 species carry xoxF.
- **Lanthanide switch**: Masuda et al. (2016) demonstrated reciprocal mxaF/xoxF regulation in AM1. The 39 BOTH species likely maintain this switch; the 10 xoxF-only species may be obligately lanthanide-dependent.
- **Annotation errors**: Schnoes et al. (2009) found 5-63% misannotation in enzyme superfamilies. Our xoxF/mxaF finding is a specific, high-impact instance — particularly consequential since the misannotation inverts the biological conclusion (from "xoxF is rare" to "xoxF is universal").
- **B vitamin auxotrophy**: Consistent with Ryback et al. (2022) finding ~50% of phyllosphere bacteria are auxotrophic for B vitamins. The Black Queen Hypothesis (Morris et al., 2012) provides the evolutionary framework for adaptive gene loss in community contexts.
- **Taxonomy**: Green & Ardley (2018) proposed *Methylorubrum* but Hesse et al. (2022) supports monophyly. GTDB retains *Methylobacterium*; our analysis includes both names.

### Novel Contributions

1. First pangenome-scale demonstration that eggNOG's xoxF/mxaF misannotation completely inverts the MDH profile across an entire genus
2. Genome-derived B vitamin auxotrophy predictions with testable growth medium implications
3. Discovery that B12 cobalamin shows the most core/accessory variability of any B vitamin pathway, predicting strain-specific requirements

### Limitations

- Missing annotations may reflect eggNOG sensitivity gaps rather than true gene absence
- Pathway gene lists are curated but not exhaustive; alternative biosynthesis routes may exist
- The 80% auxotrophy threshold is heuristic, not empirically validated
- Cross-species MDH classification depends on EC/KEGG annotation quality (though zero ambiguous clusters in this dataset)

## Testable Predictions

1. *M. extorquens* AM1 growth should be enhanced by supplementing riboflavin and/or thiamine
2. Different strains should have different B12 requirements given cob gene core/accessory variability
3. xoxF-only species should require lanthanide supplementation for methanol-dependent growth

## Methods

### Data
- *M. extorquens* pangenome: 22 genomes (main) + 4 genomes (*M. extorquens_A*) from `kbase_ke_pangenome`
- 49 *Methylobacterium/Methylorubrum* species for cross-species MDH classification
- eggNOG-mapper annotations queried via Spark SQL on BERDL JupyterHub

### B Vitamin Pathway Assessment
- Defined 6 pathways (B1, B2, B6, B7, B9, B12) with expected gene lists and KEGG KOs
- Classified annotations by gene name and KEGG KO only (not KEGG pathway number)
- Completeness = (found genes / expected genes) x 100%
- Auxotrophy predicted when completeness < 80%

### MDH Classification
- Priority system: EC 1.1.2.7 / K14028 = true mxaF; EC 1.1.2.8 / K00114 = xoxF
- Preferred_name used as fallback only when EC and KEGG_ko are both absent
- Taxonomy filter includes both *Methylobacterium* and *Methylorubrum*
