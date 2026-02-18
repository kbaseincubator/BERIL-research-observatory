# Key Findings from GapMind Pathway Analysis

**Date**: 2026-02-17
**Analysis**: Notebook 02 - GapMind pathway completeness across 8 FB organisms

---

## Critical Discovery: GapMind Coverage Gap

**E. coli genomes are completely absent from GapMind.**

- **Keio (E. coli K-12 MG1655, GCF_000005845.2)**: 0 predictions
- Searched for all E. coli genomes in GapMind: 0 found
- This is the most well-studied model organism, yet has no GapMind data

**Impact on Analysis**:
- Only **7 of 8** mapped organisms have GapMind data
- Effective sample size: 7 organisms (not 8)
- Cannot assess E. coli metabolic pathway completeness using GapMind

---

## GapMind Coverage Summary

| Organism | Species | Genome ID | GapMind Predictions | Status |
|----------|---------|-----------|---------------------|--------|
| Keio | *Escherichia coli* K-12 | GCF_000005845.2 | 0 | ❌ Missing |
| DvH | *Desulfovibrio vulgaris* | GCF_000195755.1 | 694 | ✅ Present |
| MR1 | *Shewanella oneidensis* | GCF_000146165.2 | 694 | ✅ Present |
| Putida | *Pseudomonas putida* KT2440 | GCF_000007565.2 | 1,041 | ✅ Present |
| PS | *Pseudomonas aeruginosa* PAO1 | GCF_000006765.1 | 745 | ✅ Present |
| Caulo | *Caulobacter vibrioides* CB15 | GCF_000022005.1 | 694 | ✅ Present |
| Smeli | *Sinorhizobium meliloti* 1021 | GCF_000006965.1 | 1,735 | ✅ Present |
| azobra | *Azospirillum brasilense* Sp245 | GCF_000011365.1 | 1,786 | ✅ Present |

**Total**: 7,389 predictions across 7 organisms (average: 1,056 per organism)

---

## Amino Acid Biosynthesis Pathway Completeness

### Overall Pattern
- **6 of 7 organisms** (85.7%) have complete biosynthesis pathways for **all 18 amino acids**
- **1 organism** (*Desulfovibrio vulgaris*) lacks **serine biosynthesis**

### Pathway Completeness Table

| Pathway | Present in | % Complete | Missing Organism(s) |
|---------|-----------|-----------|---------------------|
| arg, asn, chorismate, cys, gln, gly, his, ile, leu, lys, met, phe, pro, thr, trp, tyr, val | 7/7 | 100% | None |
| **ser** | **6/7** | **85.7%** | ***Desulfovibrio vulgaris*** |

### Organism Completeness

| Organism | Species | AA Pathways | % Complete |
|----------|---------|-------------|-----------|
| Caulo | *Caulobacter vibrioides* | 18/18 | 100% |
| MR1 | *Shewanella oneidensis* | 18/18 | 100% |
| PS | *Pseudomonas aeruginosa* | 18/18 | 100% |
| Putida | *Pseudomonas putida* | 18/18 | 100% |
| Smeli | *Sinorhizobium meliloti* | 18/18 | 100% |
| azobra | *Azospirillum brasilense* | 18/18 | 100% |
| **DvH** | ***Desulfovibrio vulgaris*** | **17/18** | **94.4%** |

---

## Biological Interpretation

### *Desulfovibrio vulgaris* Serine Auxotrophy

**Finding**: DvH lacks serine biosynthesis pathway according to GapMind.

**Biological Context**:
- *Desulfovibrio vulgaris* is a sulfate-reducing bacterium
- Lives in anaerobic environments (sediments, intestinal tracts)
- Known for complex metabolic capabilities (hydrogen metabolism, metal reduction)

**Possible Explanations**:
1. **True auxotrophy**: DvH may acquire serine from its environment
   - Consistent with niche in organic-rich anaerobic sediments
   - Serine is abundant in protein degradation products

2. **Alternative pathway**: DvH may use a non-canonical serine biosynthesis route not detected by GapMind
   - GapMind searches for known pathway genes
   - Novel/divergent enzymes may be missed

3. **GapMind limitation**: Pathway may be present but below GapMind's confidence threshold
   - "steps_missing" category not included in "complete" analysis
   - Could check lower confidence predictions

**Literature Check Needed**: Is DvH serine auxotrophy documented?

---

## Implications for Essential Metabolome Study

### Strengths
1. **High pathway completeness** across diverse bacteria (6/7 with all 18 pathways)
2. **Clear identification** of metabolic gaps (DvH serine)
3. **GapMind data quality** appears good for covered organisms

### Limitations Discovered
1. **E. coli absence** is a major gap
   - E. coli is one of the 45 FB organisms with essential gene data
   - Cannot link essential genes → metabolic pathways for this key organism

2. **Coverage uncertainty** for remaining 37 unmapped organisms
   - Unknown how many will lack GapMind data
   - May affect feasibility of full 45-organism analysis

### Revised Research Strategy

**Option A: Proceed with GapMind for organisms with coverage**
- Map remaining 37 FB organisms → genome IDs
- Filter to organisms with GapMind predictions
- Analyze pathway completeness across available subset (~20-30 organisms expected)

**Option B: Pivot to alternative metabolic data**
- Use eggNOG EC annotations → KEGG pathways
- Build pathway completeness from gene annotations
- Would include E. coli and all 45 FB organisms

**Option C: Hybrid approach**
- Use GapMind for organisms with coverage (pathway-level)
- Use eggNOG for organisms without GapMind (gene-level)
- Compare methodologies

---

## Next Steps

1. **Document GapMind coverage limitation** in RESEARCH_PLAN.md
2. **Investigate DvH serine auxotrophy** in literature
3. **Decide on research strategy** (Option A, B, or C above)
4. **Update mapping** to include more organisms if proceeding with GapMind
5. **Consider eggNOG pathway analysis** as alternative/complement

---

## Data Provenance

- **GapMind predictions**: `kbase_ke_pangenome.gapmind_pathways` (305M predictions, 293K genomes)
- **Analysis dataset**: 7,389 predictions across 7 organisms
- **Notebook**: `notebooks/02_gapmind_pathway_analysis.ipynb`
- **Data files**: `data/pathway_completeness.tsv`, `data/aa_pathway_completeness.tsv`

---

## References for Follow-up

- **GapMind publication**: Price et al., 2020, mSystems (pathway prediction methodology)
- **Desulfovibrio vulgaris**: Heidelberg et al., 2004, Nat Biotechnol (genome)
- **Serine biosynthesis**: Classical pathway: 3-phosphoglycerate → serine
- **E. coli essential genes**: Baba et al., 2006, Mol Syst Biol (Keio collection)
