"""Hydrate NB14_endogenous_phageome.ipynb."""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB14_endogenous_phageome.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb14_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB14_endogenous_phageome.png'
fig_b64 = base64.b64encode(open(FIG_PATH, 'rb').read()).decode()

nb = nbf.v4.new_notebook()
cells = []


def code_cell(src, stdout_text=None, execution_count=None, outputs_extra=None):
    c = nbf.v4.new_code_cell(src)
    outs = []
    if stdout_text:
        outs.append(nbf.v4.new_output('stream', name='stdout', text=stdout_text))
    if outputs_extra:
        outs.extend(outputs_extra)
    c.outputs = outs
    if execution_count is not None:
        c.execution_count = execution_count
    return c


cells.append(nbf.v4.new_markdown_cell("""# NB14 — HMP2 Endogenous Phageome × Ecotype × Diagnosis

**Project**: `ibd_phage_targeting` — Pillar 4 third notebook
**Depends on**: HMP2 `fact_viromics` (3,039 sample-rows × 273 viruses); NB04h ecotype projections; `ref_viromics_cd_vs_nonibd` + `ref_viromics_summary_by_disease` precomputed

## Purpose

Test whether the in-vivo endogenous phageome stratifies across the 4-ecotype framework + within-ecotype CD-vs-nonIBD signal. Per plan v1.7 NB14 (endogenous phageome stratification per ecotype) + v1.9 no-raw-reads.

NB12 established the curated-literature phage-availability scoring; NB13 added the experimental PhageFoundry quantitative cocktail design for *E. coli* AIEC. NB14 now adds the **in-vivo phage-community lens**: do CD vs nonIBD HMP2 patients carry distinct endogenous phage signatures per ecotype, and do any phage families correlate with Tier-A pathobiont abundance at the sample level?

## Tests

1. Sample overlap (HMP2 viromics ∩ NB04h ecotype projection)
2. Per-ecotype phage-family abundance distribution
3. Per-ecotype × per-virus CD-vs-nonIBD Mann-Whitney + cliff_delta + BH-FDR
4. Cross-reference precomputed `ref_viromics_cd_vs_nonibd` (22 viruses)
5. Tier-A pathobiont species × phage-family Spearman ρ across paired viromics+metaphlan3 samples
"""))

cells.append(code_cell("""# See run_nb14.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §0. Load HMP2 viromics + NB04h ecotype projections + ref tables"""))
cells.append(code_cell("""# 630 of 648 viromics samples have ecotype calls (97% overlap)""",
                       stdout_text=SECTION_LOGS['0'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §1. Per-ecotype phage-family distribution"""))
cells.append(code_cell("""# 21 unique phage families; Unknown family dominates (VirMAP classification gap)""",
                       stdout_text=SECTION_LOGS['1'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §2. Per-virus CD-vs-nonIBD Mann-Whitney within-ecotype meta"""))
cells.append(code_cell("""# 85 DA tests across 4 ecotypes; 3 pass FDR<0.10 (all CD-DOWN — Gokushovirus dominant)""",
                       stdout_text=SECTION_LOGS['2'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §3. Cross-reference ref_viromics_cd_vs_nonibd (22 precomputed viruses)"""))
cells.append(code_cell("""# Top hit Gokushovirus WZ-2015a CD-DOWN log2fc=-2.7, FDR=1e-11; 11 CD-up + 11 CD-down""",
                       stdout_text=SECTION_LOGS['3'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §4. Phage family × Tier-A pathobiont abundance correlation"""))
cells.append(code_cell("""# 6 species × 21 families = 126 correlations; max |ρ|=0.18 (modest)""",
                       stdout_text=SECTION_LOGS['4'], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §5. Verdict + figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 2000x600 with 3 Axes>']
}, metadata={})
cells.append(code_cell("""# 3-panel: ecotype × phage-family abundance heatmap + top 12 DA viruses + species × family ρ heatmap""",
                       stdout_text=SECTION_LOGS['5'], outputs_extra=[fig_output], execution_count=7))

cells.append(nbf.v4.new_markdown_cell("""## §6. Interpretation

### Headline: Gokushovirus WZ-2015a is robustly CD-DOWN across multiple ecotypes (E1 FDR=5e-7); endogenous phage-family signatures show modest ecotype-specific variation but weak Tier-A species correlation

#### Ecotype × diagnosis sample distribution

630 of 648 HMP2 viromics samples have ecotype calls (97 % overlap with NB04h projections):

| Ecotype | CD | UC | healthy |
|---|---:|---:|---:|
| E0 | 12 | 15 | 14 |
| E1 (dominant) | **231** | 128 | 125 |
| E2 | 21 | 14 | 20 |
| E3 | 30 | 12 | 8 |

The 4-ecotype framework (NB01b consensus) projects cleanly onto HMP2 viromics samples. E1 has the largest sample size for within-ecotype CD-vs-nonIBD DA (231 CD vs 125 healthy).

#### Per-ecotype × per-virus CD-vs-nonIBD DA — robust Gokushovirus signal

Top hits at FDR<0.10 (within-ecotype):

| Ecotype | Virus | Cliff δ | FDR |
|---|---|---:|---:|
| **E1** | **Gokushovirus WZ-2015a** | **−0.358** | **5e-7** |
| E2 | Gokushovirus WZ-2015a | −0.471 | 0.056 |
| E2 | Human feces pecovirus | −0.300 | 0.056 |

**Gokushovirus WZ-2015a is consistently CD-DOWN across multiple ecotypes**, with the strongest signal in E1 (cliff=-0.36 at FDR=5e-7 in n_CD=231 vs n_HC=125). This **independently rediscovers** the precomputed `ref_viromics_cd_vs_nonibd` top hit (Gokushovirus WZ-2015a log2fc=-2.7, FDR=1e-11) — the project's per-ecotype analysis confirms the cohort-aggregate result.

**Gokushovirus** is a member of *Microviridae* (single-stranded DNA phages, ~5 kb genome). The Gokushovirinae subfamily includes the canonical "crassphage-like" lineage that infects *Bacteroides* / *Prevotella* gut commensals. **CD-DOWN in HMP2 across multiple ecotypes** is consistent with the canonical Norman 2015 / Clooney 2019 finding that Microviridae are depleted in IBD.

E0 borderline hits (FDR<0.30) include *C2likevirus* (lactococcal temperate phages) and *Tomato mosaic virus* CD-DOWN; E2 also surfaces a CD-up T7-like virus (Podoviridae, *Autographivirinae*). None pass strict FDR<0.10 outside E1+E2 for Gokushovirus.

#### Tier-A pathobiont species × phage-family correlations are modest

| Species | Phage family | Spearman ρ | p |
|---|---|---:|---:|
| ***E. coli*** | **Podoviridae** | **+0.183** | **4e-6** |
| H. hathewayi | Unknown | -0.150 | 2e-4 |
| M. gnavus | Unknown | -0.134 | 7e-4 |
| ***E. coli*** | **Myoviridae** | **+0.125** | 0.002 |
| E. bolteae | Myoviridae | +0.119 | 0.003 |
| E. lenta | Tymoviridae | +0.108 | 0.006 |
| M. gnavus | Myoviridae | +0.106 | 0.008 |

***E. coli*** **correlates positively with Podoviridae (+0.18) and Myoviridae (+0.13)** — both Caudovirales families that include T7-like and T4-like *E. coli* phages. This is a plausible **endogenous phage-host correlation**: when *E. coli* abundance is high in a sample, *E. coli* phages tend to also be abundant (commensal phage carriage / lysogenic-state co-occurrence). However, |ρ|≈0.18 is modest — the in-vivo phage signal is weak relative to species-abundance signal.

***H. hathewayi* and *M. gnavus* correlate NEGATIVELY with "Unknown" phage family** (the dominant family in viromics, capturing 80 % of phage observations that VirMAP couldn't classify to family level). Negative correlations suggest H. hathewayi / M. gnavus blooms displace some unclassified phages — possibly because these pathobionts crowd out their commensal phage hosts in CD samples.

**No |ρ|>0.30 strong correlations** — the in-vivo endogenous phage signal does NOT identify strong endogenous-phage candidates targeting Tier-A pathobionts via simple species × family correlation. This is consistent with the NB12 §1 finding that gut-anaerobe pathobionts (H. hathewayi, M. gnavus, F. plautii) have minimal characterized phage representation.

#### Phage-family × ecotype abundance heterogeneity

Per-ecotype mean phage-family abundance (Panel A heatmap) shows **modest ecotype-specific variation**:

- **Anelloviridae** is essentially absent in E0 + E2 (mean ~0) but present in E1 (63) and E3 (2.2) — small but ecotype-specific. Anelloviruses are blood-borne/systemic; their gut presence is curious.
- **Parvoviridae** is highest in E2 (100) and absent in E3
- **Tombusviridae** absent in E3
- **"Unknown family"** abundance varies: highest in E2 (20,546), lowest in E1 (9,579) — reflects the dominance of unclassified phage signal that the family-level analysis cannot resolve.

#### Methodological observations

- **VirMAP classification gap**: the "Unknown" family captures 2,425 of 3,039 (80 %) of all viromics observations — at the family level, most observed phages cannot be classified. This is a fundamental limitation of family-level virus taxonomy from short-read metagenomics. Recent improvements (DRAM-v, MMseqs2-based classifiers, IMG/VR cross-reference) would partially close this gap but are out of project scope.
- **Per-ecotype DA power**: only E1 has sufficient sample size (231 CD vs 125 HC) for robust within-ecotype DA at FDR<0.10. Smaller ecotypes (E0, E3) have wide CIs and don't pass strict thresholds despite biologically interesting cliff values (Gokushovirus E0 cliff=-0.55).

### Pillar 4 closure synthesis — three layers of phage evidence

NB12 + NB13 + NB14 together provide three complementary phage-evidence layers for Pillar-5 cocktail design:

1. **NB12 — Curated literature foundation** (12 organisms × phage availability score 0-3): *E. coli* AIEC = clinical-trial-stage; *M. gnavus* = temperate-only; *H. hathewayi* / *F. plautii* = phage GAP.
2. **NB13 — PhageFoundry quantitative experimental susceptibility** (96 phages × 188 *E. coli* strains): 5-phage cocktail covers 95 % of strains; 65/94 phages (69 %) AIEC-relevant phylogroup.
3. **NB14 — HMP2 in-vivo endogenous phageome** (630 samples × 21 families): Gokushovirus CD-DOWN cross-ecotype; modest *E. coli* × Podoviridae/Myoviridae positive correlation; in-vivo phage signal weak relative to species-level CD signal.

**Combined Pillar-4 verdict**: phage-therapy feasibility for E. coli is high (research-collection cocktail + in-vivo Podoviridae correlation); for M. gnavus / H. hathewayi / F. plautii the evidence base is the GAP confirmed across all three layers. **External DB queries (INPHARED + IMG/VR) for the 3 gut-anaerobe gaps remain the highest-priority Pillar-4 follow-up before Pillar 5 cocktail drafts**.

### Limitations

- VirMAP family-level classification gap (80 % of phages unclassified) limits the species × family correlation analysis.
- Per-ecotype DA power is asymmetric: E1 has 231 CD samples, but E0/E2/E3 have 12-30 — limits within-ecotype detection in the smaller ecotypes.
- No CRISPR-spacer-derived phage-host predictions in HMP2 viromics; would need IMG/VR-style spacer matching for Tier-A-host phage discovery.
- "Unknown" phage family dominates abundance; per-virus DA is more informative than per-family aggregation for IBD-relevant signals.

### Outputs

- `data/nb14_viromics_da_per_ecotype.tsv` — 85 (ecotype × virus) DA tests with cliff_delta + p + within-ecotype FDR
- `data/nb14_pathobiont_phage_family_corr.tsv` — 126 (Tier-A species × phage family) Spearman ρ
- `data/nb14_endogenous_phageome_verdict.json` — formal verdict
- `figures/NB14_endogenous_phageome.png` — 3-panel: ecotype × family abundance heatmap + top 12 DA viruses + species × family ρ heatmap
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
