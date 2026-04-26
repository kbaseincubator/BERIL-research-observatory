"""Build NB05_tier_a_scoring.ipynb with pre-populated outputs from run_nb05.py section logs.

Avoids nbconvert entirely because this environment has a numpy.bool_ serialization
bug in nbconvert's notebook JSON save path. The underlying analysis was executed
via run_nb05.py; this script just re-hydrates a clean .ipynb from the captured
stdout + figure + TSV outputs.
"""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB05_tier_a_scoring.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb05_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB05_tier_a_scored.png'

# Load figure as base64 for embedding as notebook cell output
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

cells.append(nbf.v4.new_markdown_cell("""# NB05 — Tier-A Scoring Pipeline

**Project**: `ibd_phage_targeting` — Pillar 2 close-out
**Depends on**: NB04c (within-substudy meta), NB04e (ecotype-specific Tier-A), NB04h (HMP2 external replication), and the CrohnsPhage mart reference tables (BGC catalog, Kumbhari strain-adaptation, species-IBD associations, phage biology curation).

## Purpose

NB04d and NB04e produced the rigor-controlled input candidate set. NB05 applies the Tier-A criteria A3 – A6 from `RESEARCH_PLAN.md` to produce a scored + ranked target list for Pillar 4 (phage targetability) and Pillar 5 (per-patient cocktails).

## Criteria

| Criterion | Source | Scoring |
|---|---|---|
| A3 Literature + cohort CD-association | NB04c meta + HMP2 replication + `ref_cd_vs_hc_differential` + `ref_species_ibd_associations` + `ref_phage_biology` | 0–5 |
| A4 Protective-analog exclusion | NB04c within-substudy sign + curated protective-species list | 0 or 1 |
| A5 Engraftment / strain adaptation | Donor 2708 + `fact_strain_competition` + Kumbhari gene-strain | 0 / 0.5 / 1 |
| A6 BGC inflammatory mediator | `ref_bgc_catalog` + `ref_cborf_enrichment` | 0 / 0.5 / 1 |

## Execution note

This notebook was run via `run_nb05.py` (standalone script) rather than nbconvert
because of an environment-specific numpy.bool serialization issue in the
nbconvert notebook-save path. Outputs are authoritative and written to
`data/nb05_tier_a_scored.tsv`, `data/nb05_tier_a_verdict.json`, and
`figures/NB05_tier_a_scored.png`.
"""))

cells.append(code_cell("""# Imports and constants (see run_nb05.py for full execution)
import warnings; warnings.filterwarnings('ignore')
from pathlib import Path
import json, numpy as np, pandas as pd
import matplotlib.pyplot as plt
DATA_MART = Path.home() / 'data' / 'CrohnsPhage'
DATA_OUT = Path('../data'); FIG_OUT = Path('../figures')

PROTECTIVE_REFERENCE = {
    'Faecalibacterium prausnitzii', 'Akkermansia muciniphila',
    'Roseburia intestinalis', 'Roseburia hominis', 'Lachnospira eligens',
    'Agathobacter rectalis', 'Clostridium scindens', 'Coprococcus eutactus',
    'Bifidobacterium adolescentis', 'Bifidobacterium longum',
}
ENGRAFTED = ['Mediterraneibacter gnavus', 'Eggerthella lenta', 'Escherichia coli',
             'Enterocloster bolteae', 'Hungatella hathewayi', 'Klebsiella oxytoca']
""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §1. Build candidate set"""))
cells.append(code_cell("""# See run_nb05.py for full source. Loads NB04e E1 + E3 Tier-A and NB04c engraftment candidates.
# Dedups to unique species with multi-category ecotype_membership string.""",
                       stdout_text=SECTION_LOGS['1'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §2. Invert synonymy layer (canonical → aliases)"""))
cells.append(code_cell("""# Required because ref_bgc_catalog, ref_cd_vs_hc_differential etc. use pre-GTDB-r214 names.""",
                       stdout_text=SECTION_LOGS['2'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §3. A3 — Literature + cohort CD-association scoring

Five independent signals (each 0 or 1): NB04c confound-free meta, HMP2 external replication concordance, `ref_cd_vs_hc_differential` (log2FC > 0.5 + FDR < 0.10), `ref_species_ibd_associations` (dxIBD coefficient > 0 + p < 0.05), `ref_phage_biology` curated target flag."""))
cells.append(code_cell("""# A3 = sum of the 5 signals""",
                       stdout_text=SECTION_LOGS['3'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §4. A4 — Protective-analog exclusion

Binary gate: pass (1) unless the candidate has a negative within-IBD-substudy CD-vs-nonIBD effect (confound-free protective-analog signal) OR sits on the curated protective-species list."""))
cells.append(code_cell("""# A4 = 0 (protective-analog risk) or 1 (pass)""",
                       stdout_text=SECTION_LOGS['4'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §5. A5 — Engraftment / strain adaptation

Three evidence tiers: direct donor 2708 engraftment (1.0), Kumbhari strain-competition disease-dominance (0.5), Kumbhari IBD-adapted-strain gene signal (0.5)."""))
cells.append(code_cell("""# A5 = 0.0 / 0.5 / 1.0""",
                       stdout_text=SECTION_LOGS['5'], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §6. A6 — BGC inflammatory mediator

For each candidate, look up BGCs in `ref_bgc_catalog` (via synonymy-inverted matching), count total BGCs and those containing CD-enriched CB-ORFs (from `ref_cborf_enrichment`, effect > 0.5 + FDR < 0.05). Report MIBiG-matched compound names where available (e.g., *E. coli* → Colibactin, Yersiniabactin, Enterobactin)."""))
cells.append(code_cell("""# A6 = 0.0 (no BGC), 0.5 (BGC but no CD-enriched), 1.0 (BGC with CD-enriched CB-ORFs)""",
                       stdout_text=SECTION_LOGS['6'], execution_count=7))

cells.append(nbf.v4.new_markdown_cell("""## §7. Aggregate + rank"""))
cells.append(code_cell("""# Total Tier-A = A3/5 + A4 + A5 + A6 (0-4 range); actionable threshold = 2.5""",
                       stdout_text=SECTION_LOGS['7'], execution_count=8))

cells.append(nbf.v4.new_markdown_cell("""## §8. Scoring matrix heatmap"""))
# Figure cell with embedded image output
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 1600x1000 with 2 Axes>']
}, metadata={})
cells.append(code_cell("""# Scoring matrix heatmap (top 30) + total-score bar chart.
# Generated by run_nb05.py; saved to figures/NB05_tier_a_scored.png.""",
                       outputs_extra=[fig_output], execution_count=9))

cells.append(nbf.v4.new_markdown_cell("""## §9. Summary

The scored Tier-A list in `data/nb05_tier_a_scored.tsv` is the final prioritized target set for Pillar 4 (phage targetability) and Pillar 5 (UC Davis per-patient cocktail drafts).

**Top 6 actionable candidates (total_score ≥ 2.5, out of 71 scored)**:

| Rank | Species | Ecotype membership | A3 | A4 | A5 | A6 | Total | Notes |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | *Hungatella hathewayi* | E1 \\| engraftment | 5 | 1 | 1.0 | 1.0 | **4.0** | all five A3 signals pass |
| 2 | *Mediterraneibacter gnavus* | E1 \\| E3_prov \\| engraftment | 4 | 1 | 1.0 | 1.0 | **3.8** | 39 BGCs, 26 CD-enriched CB-ORFs |
| 3 | *Escherichia coli* | E1 \\| engraftment | 3 | 1 | 1.0 | 1.0 | **3.6** | MIBiG: Colibactin, Yersiniabactin, Enterobactin |
| 4 | *Eggerthella lenta* | E1 \\| engraftment | 4 | 1 | 1.0 | 0.5 | **3.3** | engrafts + wide IBD literature |
| 5 | *Flavonifractor plautii* | E1 \\| E3_prov | 4 | 1 | 0.5 | 1.0 | **3.3** | Kumbhari strain-competition + BGC |
| 6 | *Enterocloster bolteae* | E1 \\| engraftment | 4 | 1 | 1.0 | 0.0 | **2.8** | engrafts; no BGC hit |

**Tier-B candidates (score 2.2–2.4, actionable with strain-level or A5 boost)**: *Enterocloster asparagiformis*, *Streptococcus salivarius* (Salivaricin 9/A / Cochonodin I MIBiG matches), *E. citroniae*, *E. clostridioformis*, *Blautia coccoides*, *Veillonella atypica*, *S. parasanguinis*, *Actinomyces oris*, *V. parvula*.

**Candidates failing A4 (protective-analog risk)**: *Anaerostipes hadrus* (confound-free effect −0.32), *Clostridium scindens* (curated protective list), *Roseburia faecis* (confound-free effect −2.74). These are flagged for strain-level scrutiny before any phage targeting — species-level call alone is insufficient to distinguish pathobiont from protective in these cases.

**Caveats** (see REPORT.md §5f for full discussion):
- E3 provisional candidates carry single-study (HallAB_2017) evidence within cMD.
- Cross-ecotype engraftment pathobionts are cohort-level; for ecotype-specific dosing, use the ecotype_membership annotation.
- The A3 `phage_biology_curated` signal catches only 3/71 candidates (curated list is small); most A3 score comes from cross-cohort concordance.
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}

with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH} with pre-populated outputs (nbconvert bypassed)')
