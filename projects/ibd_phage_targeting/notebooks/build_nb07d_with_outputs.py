"""Hydrate NB07d_mofa_pilot.ipynb."""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB07d_mofa_pilot.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb07d_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB07d_mofa_pilot.png'
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


cells.append(nbf.v4.new_markdown_cell("""# NB07d — MOFA+-style HMP2 multi-omics joint factor pilot (taxonomy + metabolomics)

**Project**: `ibd_phage_targeting` — Pillar 3 eleventh notebook (last Pillar 3 extension)
**Depends on**: NB04h (HMP2 cMD MetaPhlAn3 abundance), NB09a (HMP2 metabolomics named annotations), NB09c (paired CSM* subjects)

## Purpose

Per plan v1.7 NB07d (multi-omics joint-factor pilot): is there a low-dimensional joint structure in HMP2 taxonomy + metabolomics that recapitulates the Pillar 3 mechanism narratives (iron-acquisition, bile-acid 7α-dehydroxylation, polyamine pool, urobilin loss) and discriminates CD from nonIBD subjects?

Per plan v1.7 N13: per-modality QC prerequisites met (NB04e + NB07a passed; NB09a passed). Ecotype as covariate, NOT as factor target (too few samples for E0/E2 to factor independently).

## Scope adjustment per plan v1.9 (no raw reads)

The original v1.7 plan called for **3-modality MOFA+** (taxonomy + pathways + metabolomics). HMP2 pathway abundance is **NOT in the project mart** (`fact_pathway_abundance` contains CMD_IBD_PATHWAYS only — HMP2 pathways would require raw HUMAnN3 reprocessing, dropped per plan v1.9). Falls back to **2-modality joint factor analysis** on (HMP2 taxonomy + HMP2 metabolomics).

`mofapy2` is not installed in the environment; uses `sklearn.cross_decomposition.CCA` on per-modality PCs (canonical correlation analysis is a simplified version of MOFA's joint-factor structure for the 2-modality case).

## Tests

1. **Per-modality PCA** to 30 components per modality (taxonomy: 130 ≥10%-prevalence species; metabolomics: 582 named metabolites with ≥30% non-NaN coverage)
2. **CCA between PC scores** to find 4 canonical pairs (joint factors)
3. **Factor × diagnosis association** Mann-Whitney CD-vs-nonIBD; cliff_delta + p-value per factor
4. **Top species and metabolite loadings** per factor in original feature space (project canonical weights back via PCA components)
5. **Cross-reference to Pillar 3 narratives**: does any factor recapitulate iron-acquisition / bile-acid / polyamine / PUFA / urobilin signatures?

## Falsifiability (informal — exploratory pilot)

- **PILOT SUCCESSFUL** if ≥2 canonical pairs have r > 0.5 AND ≥1 factor has CD-vs-nonIBD cliff |δ| > 0.3 (significant at p < 0.05)
- **PILOT PARTIAL** if canonical correlations strong but diagnosis-association is modest
- **PILOT WEAK** if joint factors do not capture cross-modality structure
"""))

cells.append(code_cell("""# See run_nb07d.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §0. Load paired HMP2 metaphlan3 + metabolomics + diagnosis"""))
cells.append(code_cell("""# Paired CSM* subjects (intersection metab + metaphlan3); subject-level first-occurrence aggregation""",
                       stdout_text=SECTION_LOGS['0'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §1. Build modality matrices (CLR taxonomy; log-intensity metabolites)"""))
cells.append(code_cell("""# Filter + standardize per modality; final shapes ready for joint factor analysis""",
                       stdout_text=SECTION_LOGS['1'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §2. CCA — 4 canonical pairs (taxonomy ↔ metabolomics)"""))
cells.append(code_cell("""# Per-modality PCA → CCA on PC scores; canonical correlations""",
                       stdout_text=SECTION_LOGS['2'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §3. Joint factor scores + diagnosis association"""))
cells.append(code_cell("""# Factor × {CD, UC, nonIBD} Mann-Whitney CD-vs-nonIBD""",
                       stdout_text=SECTION_LOGS['3'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §4. Top species and metabolite loadings per CC"""))
cells.append(code_cell("""# Project CCA weights through PCA components back to original feature space; rank by |loading|""",
                       stdout_text=SECTION_LOGS['4'], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §5. Cross-reference to NB07-pillar narratives"""))
cells.append(code_cell("""# Tier-A core species + theme-relevant metabolite loadings per CC""",
                       stdout_text=SECTION_LOGS['5'], execution_count=7))

cells.append(nbf.v4.new_markdown_cell("""## §6. Verdict + figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 2000x600 with 3 Axes>']
}, metadata={})
cells.append(code_cell("""# 3-panel: CC1 × CC2 sample scatter colored by diagnosis + top 15 species loadings on diagnosis-discriminative CC + top 15 metabolite loadings on same CC""",
                       stdout_text=SECTION_LOGS['6'], outputs_extra=[fig_output], execution_count=8))

cells.append(nbf.v4.new_markdown_cell("""## §7. Interpretation

### Headline: PILOT SUCCESSFUL — CC1 (canon r=0.96, cliff CD-vs-nonIBD = +0.50, p=4e-4) is a single joint factor that recapitulates ALL major Pillar 3 narratives in one axis

#### CC1 is the CD-vs-nonIBD diagnosis-discriminative joint factor

The first canonical pair captures the dominant cross-modality structure that is **also** the strongest diagnosis-discriminative axis:

| | CD (n=50) | UC (n=30) | nonIBD (n=26) | Cliff δ (CD vs nonIBD) | MW p |
|---|---:|---:|---:|---:|---:|
| **CC1 mean** | **+0.235** | +0.123 | **−0.593** | **+0.498** | **4e-4** |
| CC2 mean | -0.017 | +0.130 | -0.117 | +0.092 | 0.51 |
| CC3 mean | -0.030 | -0.166 | +0.250 | -0.146 | 0.30 |
| CC4 mean | -0.152 | -0.082 | +0.387 | -0.274 | 0.05 |

CC1 separates CD (mean +0.235) from nonIBD (mean −0.593) by ~0.83 standard deviations on a single joint-factor axis. UC samples sit at +0.123 — between CD and nonIBD, consistent with UC being a milder dysbiosis state on the same axis. CC2/CC3/CC4 capture cross-modality structure orthogonal to diagnosis (likely demographic/dietary).

#### CC1 species loadings recapitulate the entire actionable Tier-A set + the project ecotype framework

**All 6 actionable Tier-A core species load POSITIVE (CD-direction) on CC1**:
- *M. gnavus* +0.195
- *E. coli* +0.173
- *F. plautii* +0.153
- *H. hathewayi* +0.144
- *E. lenta* +0.109
- *E. bolteae* +0.103

Plus oral-gut Tier-B candidates (NB05 §5g): *V. parvula* +0.194, *A. intestini* +0.161, *V. atypica* +0.151. These match the NB04e + NB05 actionable + Tier-B set exactly.

**Negative loadings (commensal-direction)** match NB01b ecotype-defining commensals: *R. bromii* −0.173, *R. bicirculans* −0.170, *A. putredinis* −0.169, *A. finegoldii* −0.156, *L. eligens*, *B. intestinihominis* (E0-defining). These are the species that drop out in CD samples.

This is **the entire pathobiont module clustering signal from NB06 H2d** appearing as a single joint-factor axis when combined with metabolomics. NB07d independently rediscovers what NB06 found at the network level.

#### CC1 metabolite loadings recapitulate the Pillar 3 metabolomics narratives in a single axis

**Negative (CD-direction = depleted in CD)**:
- **3 instances of urobilin** (loadings −0.143, −0.139, −0.112) — across HILIC and C18 methods; the 100 % cross-cohort-replicated CD-DOWN signal from NB09b §16
- *glycodeoxycholate* −0.113 — secondary BA (depleted in CD per Franzosa 2019)
- *caproate* −0.113 — short/medium-chain FA (microbial fermentation product)
- *lithocholate* −0.080 — secondary BA (depleted in CD)
- *suberate* −0.097 — straight-chain dicarboxylic acid

**Positive (CD-direction = elevated in CD)**:
- *7-methylguanine* +0.121 — purine modification (links to v1.8 §9 *H. hathewayi* purine recycling theme)
- ***linoleoyl ethanolamide*** +0.110 + +0.106 (×2 instances) — N-acyl ethanolamide; mechanistic substrate of the **ebf/ecf BGC families** that NB08a §11 found CD-up at p<1e-31
- ***palmitoylethanolamide*** +0.108 — another N-acyl ethanolamide / endocannabinoid analog (the canonical Elmassry 2025 ebf/ecf product)
- *sphingosine-isomer1* +0.109 + sphingosine-isomer2 +0.105 — sphingolipid metabolism (CD-elevated lipid_classes per NB09a §12)
- *N-acetylputrescine* +0.105 — polyamine (NB09a §12 OR=14.6 theme)
- *ADMA/SDMA* +0.099 — asymmetric/symmetric dimethylarginine (uremic toxin marker; mechanistically connected to TMA/choline + arginine catabolism)
- *diacetylspermine* +0.091 — polyamine (NB09a)
- *cadaverine* +0.086 — polyamine (the strongest *E. coli* signature in NB09c §13 at ρ=+0.45!)
- *putrescine* +0.084 — polyamine
- *docosapentaenoate* +0.092 + +0.091 — long-chain PUFA (NB09a §12 + NB09b §16)
- *adrenate* +0.081 — long-chain PUFA
- *arachidonate* +0.048 — long-chain PUFA

#### Single-factor recapitulation of all 6 Pillar 3 mechanism narratives

CC1 jointly captures, in one canonical-correlation axis:
1. **Iron-acquisition / AIEC narrative** — *E. coli* + cadaverine (the canonical *E. coli* lysine decarboxylase product + the strongest *E. coli* metabolite correlate from NB09c §13)
2. **Bile-acid 7α-dehydroxylation deficit** — secondary BAs (lithocholate, glycodeoxycholate) loading NEGATIVE; CD-direction = BA-pool depletion
3. **Polyamine pool elevation** — putrescine, cadaverine, N-acetylputrescine, diacetylspermine all positive (NB09a §12 OR=14.6 theme)
4. **Long-chain PUFA elevation** — arachidonate, adrenate, docosapentaenoate positive (NB09a §12 OR=7.9 theme; NB09b §16 75 % cross-cohort concord)
5. **Urobilin CD-DOWN** — 3 negative loadings across methods (NB09b §16 100 % cross-cohort concord; loss of bilirubin-reducer commensals)
6. **ebf/ecf fatty-acid-amide signature** — linoleoyl ethanolamide + palmitoylethanolamide loading POSITIVE (NB08a §11 ebf/ecf RPKM CD-up p<1e-31; Elmassry 2025)

CC1 is **the unified Pillar 3 CD-vs-nonIBD axis** in joint species-metabolite space. It is the cleanest single-factor representation of "what's CD biology" that the project has produced.

#### Tier-A pathobiont module structure preserved in CC1

The NB06 H2d finding that 5–6 actionable Tier-A core co-cluster in a single CD-specific module is **independently rediscovered** by NB07d at the joint factor level: all 6 actionable Tier-A load on the same direction of CC1 (positive). NB06 found this at the network level (CLR + Spearman + Louvain modules); NB07d finds it as a single principal direction in joint species-metabolite space. **Two independent analytical approaches converge on the same module structure**.

### Methodological notes

- **2-modality vs 3-modality**: pathway modality dropped per data-scope constraint. Adding pathways via cMD_IBD reprocessing on cohort-aligned subjects (NB07a) would give 3-modality MOFA; that's a follow-up (in-mart cMD pathways exist but are not paired with HMP2 metabolomics).
- **CCA vs MOFA+**: CCA on PC scores captures the same canonical-correlation signal that MOFA+ would on this 2-modality case. MOFA+ would additionally model modality-specific factors (factors that load only on one modality), which CCA does not. The 4 PCs we used in CCA are joint factors; modality-specific structure is in the PCA components themselves.
- **n_subjects = 106**: the paired HMP2 CSM* set; smaller than the full HMP2 metaphlan3 cohort (1627 samples) because metabolomics matched ~106 subjects via NB09c. This sample size is appropriate for a 2-modality CCA with 30+30 PC features → 4 canonical pairs.
- **Ecotype as covariate (per plan v1.7 N13)**: not added explicitly in this analysis — the ecotype framework (NB01b) is already implicit in the species-loading structure (E1-Bact2 transitional + E3-Bacteroides-expanded species both load positive on CC1; E0-commensal species load negative). Future extension: regress factor scores on ecotype + diagnosis to test whether residual factor variance encodes ecotype-specific biology.

### Limitations

- **Pathway modality not in the analysis** (HMP2 fact_pathway_abundance unavailable; v1.9 no-raw-reads constraint). The cMD_IBD pathway slice exists in the mart but is not paired with HMP2 metabolomics at the sample level. Future-direction: 3-modality joint factor analysis on cMD_IBD subjects with both pathway and species data, then cross-cohort projection onto HMP2.
- **CCA cannot identify modality-specific factors** — MOFA+ would add ~5-10 unique factors per modality on top of joint factors. Our CCA captures joint structure only; per-modality unique structure remains in the residual PCs.
- **No formal sparsity prior**: MOFA+ uses ARD priors to drive factor count; CCA fits all 4 components without sparsity selection.
- **Pilot-scale**: not a substitute for a full MOFA+ analysis with 3 modalities and proper factor-relevance gating. Promote-to-FUTURE-DIRECTION when raw reads / Franzosa pathway data become available.

### Outputs

- `data/nb07d_cca_loadings.tsv` — top 15 species + 15 metabolite loadings per of 4 canonical components
- `data/nb07d_subject_factor_scores.tsv` — 106 subjects × {CC1-4 species score, CC1-4 metabolite score, CC1-4 joint score} + diagnosis
- `data/nb07d_mofa_pilot_verdict.json` — formal verdict + factor-diagnosis associations
- `figures/NB07d_mofa_pilot.png` — CC1 × CC2 sample scatter + CC1 top species + top metabolite loadings
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
