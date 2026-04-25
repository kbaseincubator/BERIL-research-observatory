"""Hydrate NB12_phage_targetability.ipynb."""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB12_phage_targetability.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb12_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB12_phage_targetability.png'
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


cells.append(nbf.v4.new_markdown_cell("""# NB12 — Pathobiont × phage targetability matrix (Pillar 4 opener)

**Project**: `ibd_phage_targeting` — Pillar 4 first notebook
**Depends on**: `ref_phage_biology` (12-organism literature-curated phage synthesis); NB05 actionable Tier-A scoring; Pillar-3 per-target mechanism profile (iron / bile-acid / mediation)

## Purpose

Build a per-pathobiont **phage-targetability profile** (Tier-B in the project's 4-tier rubric) for the 6 actionable Tier-A core species, combining NB05 Tier-A scoring (criteria A3-A6) with literature-curated phage availability + Pillar-3 mechanism profile to produce per-target priority classification for Pillar-5 cocktail design.

## Method

Per plan v1.9 (no raw reads):

1. **`ref_phage_biology`** (12 organisms, indicator_taxa_literature_review) — literature-curated phage info per Tier-1/Tier-2 pathobiont (known_phages, therapeutic_targets, lifestyle, clinical trial status)
2. **NB05 Tier-A scoring** (71 candidates × A3-A6 criteria + total_score)
3. **Pillar-3 per-target mechanism profile** (iron specialization, bile-acid coupling cost, mechanism mediation — from REPORT §closure cocktail-design table)
4. **Phage-availability score (Tier-B)**: 0-3 ordinal scale
   - **0** = no known phages OR only historical phage-like particles
   - **1** = temperate / prophage only, or limited characterization
   - **2** = lytic phage(s) characterized in literature, but not in clinical trials
   - **3** = clinical trial / commercial cocktail OR published efficacy data

External phage DB queries (PhageFoundry BERDL, INPHARED, IMG/VR, NCBI Phage RefSeq, PhagesDB) flagged for follow-up — BERDL Spark auth currently blocks direct PhageFoundry query, so this NB12 establishes the curated-literature-based foundation.

## Tests

1. Per-pathobiont phage-availability score
2. Combined Tier-A × Tier-B × Pillar-3 mechanism profile → Pillar-5 cocktail-design priority class
3. Coverage gap analysis: which actionable Tier-A core have NO phage-therapy options?
4. External phage DB references for follow-up
"""))

cells.append(code_cell("""# See run_nb12.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §0. Load ref_phage_biology + NB05 Tier-A scoring + Pillar-3 mechanism profile"""))
cells.append(code_cell("""# 12 organisms in ref_phage_biology; 6 actionable + 9 Tier-B candidates from NB05""",
                       stdout_text=SECTION_LOGS['0'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §1. Per-pathobiont phage-availability scoring (Tier-B)"""))
cells.append(code_cell("""# 0-3 ordinal scale based on lifestyle + clinical status""",
                       stdout_text=SECTION_LOGS['1'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §2. Combined Tier-A × Tier-B × Pillar-3 priority for Pillar-5 cocktail design"""))
cells.append(code_cell("""# Per-actionable-target full profile + Pillar-5 priority class""",
                       stdout_text=SECTION_LOGS['2'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §3. Coverage gap analysis"""))
cells.append(code_cell("""# Pathobionts with phage-availability score = 0 or unknown""",
                       stdout_text=SECTION_LOGS['3'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §4. External phage DB references for follow-up"""))
cells.append(code_cell("""# PhageFoundry, INPHARED, IMG/VR, NCBI Phage RefSeq, PhagesDB""",
                       stdout_text=SECTION_LOGS['4'], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §5. Verdict + figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 1500x700 with 2 Axes>']
}, metadata={})
cells.append(code_cell("""# 2-panel: Tier-A × Tier-B scatter + per-actionable Pillar-5 priority bar""",
                       stdout_text=SECTION_LOGS['5'], outputs_extra=[fig_output], execution_count=7))

cells.append(nbf.v4.new_markdown_cell("""## §6. Interpretation

### Headline: Phage availability stratifies the 6 actionable Tier-A core into 4 priority classes; H. hathewayi (highest NB05) and F. plautii (highest BA-cost) are coverage gaps requiring external DB queries

#### Per-actionable Tier-A phage-targetability profile

| Pathobiont | NB05 score | Phage score | Lifestyle | BA cost | Pillar-5 class |
|---|---:|---:|---|---|---|
| ***H. hathewayi*** | **4.0** | **0** | none | low | **GAP**: highest NB05 but no known phages — external DB query (INPHARED + IMG/VR) priority |
| ***M. gnavus*** | **3.8** | 1 | temperate | low | **Limited**: 6 known phages all temperate — lytic-locked engineering OR biochemical glucorhamnan-synthesis target as alternatives |
| ***E. coli*** (AIEC) | **3.6** | **3** | lytic + clinical | low | **Tier-1 clinical**: EcoActive cocktail (7 lytic phages, clinical trials); HER259 (FimH-targeting, attenuates virulence). Most advanced. Strain-resolution requirement (AIEC subset) per NB07b/NB08a |
| ***E. lenta*** | 3.3 | 2 | lytic literature | moderate | **Tier-2**: PMBT5 siphovirus characterized; non-BGC drug-metabolism mechanism (Koppel 2018 Cgr2) — moderate-priority target |
| ***F. plautii*** | 3.3 | **0** | unknown (not in ref) | **HIGHEST** | **GAP + HIGH cost**: not in ref_phage_biology; HIGHEST BA-coupling cost (active 7α-dehydroxylator). Phage targeting deprioritized in favor of bile-acid-pool monitoring or biochemical alternatives |
| ***E. bolteae*** | 2.8 | 2 | lytic literature | moderate | **Tier-2**: PMBT24 (virulent, 99,962 bp Kielviridae) — best-characterized lytic phage among gut-anaerobe Tier-A |

#### Stratification — four phage-availability classes among 6 actionable Tier-A:

- **Class 3 (clinical trial)**: 1 species — *E. coli* (EcoActive cocktail; Galtier 2017 mouse model precedent)
- **Class 2 (lytic literature)**: 2 species — *E. lenta* (PMBT5), *E. bolteae* (PMBT24)
- **Class 1 (temperate / limited)**: 1 species — *M. gnavus* (6 temperate siphoviruses; lifestyle limits therapy)
- **Class 0 (gap)**: 2 species — *H. hathewayi* (no specific phages identified), *F. plautii* (not in ref_phage_biology)

#### Critical observations

1. **The 2 highest-NB05-scored species (*H. hathewayi* 4.0, *M. gnavus* 3.8) have the WEAKEST phage availability**. Phage-therapy success requires resolving these gaps (INPHARED / IMG/VR for H. hathewayi; lytic-locked phage engineering or biochemical alternatives for M. gnavus).

2. ***F. plautii* has both phage GAP AND highest BA-coupling cost** (NB09c §13: active 7α-dehydroxylator, depletion shifts BA pool toward inflammatory primary tauro-conjugated forms). This makes *F. plautii* a **lowest-priority Pillar-5 target** despite NB05 score 3.3 — first decision is whether to target at all (BA pool consequence) before phage selection. Alternative strategies: (a) co-administer UDCA / BA-binding agent; (b) target downstream of *F. plautii* (e.g., bile-acid-pool replenishment); (c) accept partial *F. plautii* depletion with clinical BA monitoring.

3. ***E. coli* AIEC is the highest-Pillar-5-feasibility target**: clinical-trial-stage phage cocktail (EcoActive — 7 lytic phages), low BA-coupling cost, mechanism well-characterized (NB05 §5g + NB07c §2 + NB08a §2 iron-acquisition narrative). The Pillar-4-feasibility decision for E. coli is sharpened by the AIEC strain-content requirement: target Yersiniabactin/Enterobactin/Colibactin-positive strains specifically (per NB08a) — generic E. coli phages may not deplete the right subset.

4. ***E. bolteae* + *E. lenta* are mid-tier targets** with lytic literature phages and moderate BA-coupling cost. Both are realistic Pillar-5 phage-cocktail components subject to BA pool monitoring.

### Pillar 4 → Pillar 5 hand-off framework

The 6 actionable Tier-A core stratify into **3 Pillar-5 design strategies**:

1. **Direct phage targeting (Tier-1)**: *E. coli* (AIEC subset, clinical-trial cocktail) → use EcoActive or build similar 7-phage cocktail; require strain-resolution diagnostic.
2. **Phage targeting with monitoring (Tier-2)**: *E. lenta* (PMBT5), *E. bolteae* (PMBT24) → include in cocktail with BA-pool monitoring; M. gnavus is here too if lytic-locked engineering succeeds.
3. **Phage GAP — alternative strategies needed**:
   - *H. hathewayi*: highest priority for external DB query (INPHARED / IMG/VR) — if no phages found, fall back to GAG-degrading enzyme inhibitors per ref_phage_biology therapeutic_targets.
   - *F. plautii*: lowest Pillar-5 priority due to highest BA-cost — consider deprioritizing or replacing phage approach with BA-binding co-therapy.
   - *M. gnavus* if lytic-locked engineering fails: biochemical glucorhamnan-synthesis targets (Henke 2019).

### Limitations

- **BERDL Spark auth blocked at NB12 execution** (KBASE_AUTH_TOKEN stale) — PhageFoundry collections (`phagefoundry_strain_modelling`, `phagefoundry_ecoliphages_genomedepot`, `phagefoundry_klebsiella_*`) not directly queried. Refresh token + re-query as Pillar-4 follow-up. Direct PhageFoundry coverage would primarily augment *E. coli* (genomes + host-range CDS + receptor-binding-domain diversity) and *K. oxytoca* (Tier-2).
- **External phage DB queries** (INPHARED ~25K phages with host predictions; IMG/VR ~3M UViGs from metagenomes; NCBI Phage RefSeq ~5K curated) are out-of-BERDL and not run in NB12. The 2 actionable Tier-A coverage gaps (*F. plautii*, *H. hathewayi*) require these queries — this is the highest-priority Pillar-4 follow-up.
- **`ref_phage_biology` has 12 organisms** — *F. plautii* not in the curated set (5 of 6 actionable Tier-A core covered).
- **Phage-availability scoring is qualitative ordinal** (0-3) based on lifestyle + clinical status. Quantitative coverage metrics (n_phages, host-range CDS, receptor-binding-domain diversity, plaque burst size, pH stability) require PhageFoundry / INPHARED genomic data.

### Outputs

- `data/nb12_phage_targetability_matrix.tsv` — per-pathobiont scoring matrix (NB05 Tier-A score + phage Tier-B score + lifestyle + Pillar-5 class)
- `data/nb12_phage_targetability_verdict.json` — formal verdict + Pillar-4/5 hand-off note + limitations
- `figures/NB12_phage_targetability.png` — 2-panel: Tier-A × Tier-B scatter + per-actionable Pillar-5 priority bar
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
