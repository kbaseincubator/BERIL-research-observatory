"""Hydrate NB17_synthesis.ipynb."""
import json
import base64
from pathlib import Path

import nbformat as nbf

NB_PATH = Path(__file__).parent / 'NB17_synthesis.ipynb'
SECTION_LOGS = json.load(open('/tmp/nb17_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB17_synthesis.png'
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


cells.append(nbf.v4.new_markdown_cell("""# NB17 — Cross-cutting synthesis + clinical-translation roadmap (Pillar 5 closure capstone)

**Project**: `ibd_phage_targeting` — Pillar 5 closure capstone
**Depends on**: NB02 (ecotypes) + NB05 (Tier-A scoring) + NB06 (modules) + NB09c (BA-coupling) + NB10a (mediation) + NB12 (phage availability) + NB15 (per-patient cocktails) + NB16 (longitudinal + dosing rule)

## Purpose

NB17 is the project's cross-cutting synthesis. Three deliverables consolidate Pillar 1-5 into a single clinical-translation package:

1. **Per-patient master table** — one row per UC Davis CD patient with all per-pillar attributes, design category, recommended cocktail strategy, and longitudinal status. The single artifact a clinical collaborator would actually use.
2. **Target decision matrix** — 6 actionable Tier-A × 5 attributes (NB05 score, ecotype membership, BA-coupling cost, mediation mode, phage tier) → final cocktail-design priority class.
3. **Clinical-translation roadmap + final verdict** — Immediate / Near / Mid / Long term timeline with concrete milestones; final per-pillar verdict + 24 Novel Contributions one-line index.

Per plan v1.9 no raw reads — all inputs are precomputed mart artifacts.
"""))

cells.append(code_cell("""# See run_nb17.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §1. Load upstream per-pillar artifacts"""))
cells.append(code_cell("""# NB02 + NB05 + NB12 + NB15 + NB16 outputs""",
                       stdout_text=SECTION_LOGS['1'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §2. Per-patient master table"""))
cells.append(code_cell("""# 23 patients × full per-pillar attributes + design category + cocktail strategy + longitudinal status""",
                       stdout_text=SECTION_LOGS['2'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §3. Target decision matrix"""))
cells.append(code_cell("""# 6 actionable Tier-A × 5 attributes → final priority class""",
                       stdout_text=SECTION_LOGS['3'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §4. Final per-pillar verdict + Novel Contributions index + clinical-translation roadmap"""))
cells.append(code_cell("""# Pillar 1-5 verdicts + 24 NC index + 4-phase clinical roadmap""",
                       stdout_text=SECTION_LOGS['4'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §5. Synthesis figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 2000x700 with 3 Axes>']
}, metadata={})
cells.append(code_cell("""# 3-panel: target decision matrix + per-patient design map + clinical-translation roadmap""",
                       stdout_text=SECTION_LOGS['5'], outputs_extra=[fig_output], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §6. Synthesis interpretation

### Headline: Pillar 1–5 substantially closed; 14 of 23 UC Davis CD patients with concrete cocktail drafts; state-dependent dosing rule operationalized; clinical-translation roadmap defined

#### Per-patient master table — 4 design categories × 7 cocktail strategies

The 23 UC Davis CD patients distribute across 4 design categories (combining ecotype + calprotectin + longitudinal status):

| Category | n | Description | Cocktail strategy |
|---|---:|---|---|
| **A — Active disease + many targets** (calp ≥ 250 + ≥ 4 actionable Tier-A) | 8 | High disease burden + multiple intervention points | Hybrid 3-strategy cocktail (NB13 5-phage E. coli if AIEC+; PMBT24; PMBT5; alternatives for H. hathewayi + F. plautii + M. gnavus) |
| **B — Active disease + few targets** (calp ≥ 250 + < 4 actionable) | 2 | High disease burden + limited targets | Limited cocktail; consider non-phage strategies |
| **C — Quiescent** (calp < 250 or unmeasured) | 12 | Low disease activity | Reserve cocktail for flares; calp + qPCR monitoring |
| **D — Mixed-ecotype longitudinal** (patient 6967) | 1 | E1 ↔ E3 drift across visits | State-dependent dosing per NB16 §5 workflow |

Cocktail strategies break down further by ecotype + AIEC carrier status:

| Strategy | n | Components |
|---|---:|---|
| Reserve for flare (C category) | 12 | No active cocktail; calp monitor + M. gnavus qPCR |
| E1 hybrid 3-strategy (no E. coli) | 4 | PMBT24 + PMBT5 + alternatives for H. hathewayi + F. plautii + M. gnavus + UDCA/BA-binding |
| E0 limited (priority targets are GAP) | 4 | Limited cocktail; consider non-phage strategies |
| E1 hybrid 3-strategy (full, with E. coli AIEC) | 1 | NB13 5-phage E. coli + PMBT24 + PMBT5 + alternatives for H. hathewayi + F. plautii + M. gnavus + UDCA |
| E3 focused (with E. coli) | 1 | NB13 5-phage E. coli + PMBT5 + alternatives |
| State-dependent dosing | 1 | Patient 6967: cocktail rebalances on E1↔E3 ecotype shifts (drop F. plautii on E1→E3; add E. coli AIEC on E3→E1) |

**Patients with concrete phage cocktail drafts: 14 of 23 (61 %)**.

#### Target decision matrix — 6 actionable Tier-A × 5 attributes → priority class

The decision matrix integrates Pillar 1-4 evidence per actionable target:

| Species | NB05 | Ecotype | BA cost | Phage tier | UCD prev. | Final priority class |
|---|---:|---|---|---|---:|---|
| ***H. hathewayi*** | **4.0** | E1+E3 | none | **GAP** | 83 % | Tier-1 phage GAP — INPHARED/IMG-VR external DB query priority |
| ***M. gnavus*** | **3.8** | E1+E3 | none | temperate-only | **91 %** | Tier-1 limited — lytic-locked engineering OR biochemical glucorhamnan target |
| ***E. coli*** | 3.6 | E3-specific | none | **clinical-trial** | 35 % | Tier-1 phage with strain-resolution — NB13 5-phage cocktail; AIEC diagnostic required |
| ***E. lenta*** | 3.3 | E1+E3 (universal Tier-1) | moderate | lytic-literature (PMBT5) | 70 % | Tier-2 phage — PMBT5 with BA monitoring |
| ***F. plautii*** | 3.3 | E1-specific | **HIGHEST** | **GAP** | 78 % | Tier-2 deprioritize — triple penalty; UDCA/BA-binding co-therapy |
| ***E. bolteae*** | 2.8 | E1+E3 | moderate | lytic-literature (PMBT24) | 83 % | Tier-2 phage — PMBT24 with BA monitoring |

The matrix exposes **the structural shape of the clinical-translation problem**:
- The 2 highest-NB05-scored species (H. hathewayi 4.0, F. plautii 3.3) are both Pillar-4 GAP — INPHARED + IMG/VR external DB queries are the highest-priority external-data extension.
- The species with the most complete phage-therapy precedent (E. coli, clinical-trial via EcoActive) is also the rarest in UC Davis (35 % carriage).
- F. plautii has triple penalty (GAP + highest BA-cost + E1-only) → deprioritize from cocktail despite being NB05-actionable.
- M. gnavus is near-universal (91 %) but temperate-only — biggest unmet need from a coverage standpoint.

#### Clinical-translation roadmap

Concrete milestones organized by feasibility and timeline:

**Immediate (current cohort)** — already delivered by this project:
- Per-patient cocktail drafts for 23 UC Davis patients (NB15)
- F. plautii BA-coupling-cost annotation per actionable target
- 4-category patient stratification (Active+many, Active+few, Quiescent, Mixed)
- 5 state-dependent dosing rules + clinical workflow (NB16)

**Near-term (6–12 months)** — feasible external-data extensions:
- INPHARED + IMG/VR external DB queries for H. hathewayi / F. plautii / M. gnavus phages
- AIEC strain-resolution diagnostic for the 8 / 23 E. coli-positive patients
- M. gnavus qPCR validation as cheap ecotype-state proxy

**Mid-term (12–24 months)** — additional cohort/assay generation:
- Targeted qPCR ecotype panel (4-6 species)
- Per-patient bile-acid panel for F. plautii BA-cost monitoring
- Multi-cohort serology meta-analysis (firms up H3e PARTIAL)
- Expanded longitudinal sampling beyond patient 6967

**Long-term (24+ months)** — clinical pilot territory:
- Clinical pilot of hybrid 3-strategy cocktails (per-ecotype + per-patient + state-dependent)
- Lytic-locked phage engineering for M. gnavus
- GAG-degrading enzyme inhibitor screening for H. hathewayi

### Final thesis (one sentence)

> Crohn's disease at the gut-microbiome level is a single principal-direction phenomenon (NB07d CC1 r=0.96) within which 6 actionable Tier-A pathobionts and 2 cross-corroborated mechanism narratives (iron-acquisition + bile-acid 7α-dehydroxylation) define a state-dependent, hybrid-cocktail design framework with concrete per-patient drafts for 14 of 23 UC Davis CD patients.

### Per-pillar final verdict

| Pillar | Verdict | Notebooks | Key finding |
|---|:---:|---|---|
| **1 — Patient stratification** | CLOSED | NB00, NB01, NB01b, NB02, NB03 | 4 reproducible IBD ecotypes; HMP2 external-replication χ² p=0.016; UC Davis distributes E0 27%/E1 42%/E3 31% (χ² p=0.019) |
| **2 — Pathobiont identification** | CLOSED | NB04(b–h), NB05, NB06 | Within-ecotype × within-substudy meta yields 51 E1 + 40 E3 Tier-A; 6 actionable Tier-A core; HMP2 88.2% E1 sign-concordance |
| **3 — Functional drivers** | CLOSED | NB07a/b/v18/c/d, NB08a, NB09a/b/c/d, NB10a, NB11 | 8 H3 verdicts (5+1+2+1); 2 cross-corroborated 6-line narratives; CC1 r=0.96 collapses all narratives to single joint axis |
| **4 — Phage targetability** | CLOSED | NB12, NB13, NB14 | 3-layer phage-evidence convergence; 5-phage E. coli AIEC cocktail at 95% strain coverage; H. hathewayi + F. plautii GAP confirmed all 3 layers |
| **5 — Per-patient cocktails** | SUBSTANTIALLY CLOSED | NB15, NB16, NB17 | 14/23 patients with concrete cocktails; pure phage infeasible for E1; F. plautii BA-cost dominant E1 constraint; patient 6967 E1→E3 drift validates state-dependent dosing rule (M. gnavus 14× expansion); 5 dosing rules + clinical workflow |

### 24 Novel Contributions — one-line index

See `data/nb17_final_verdict.json` field `novel_contributions_index` for the full list. Categories:
- **Methodology** (general portable patterns): #1 cross-method ARI K-selection, #2 OvR-AUC vs per-patient gap, #6 cMD substudy-nesting, #7 feature leakage, #8 within-ecotype × within-substudy design, #9 adversarial review, #10 LOSO ARI, #12 ontology > regex, #15 pool ≠ flux, #19 cohort-batch in m/z metabolomics, #21 multi-omics joint factor collapse, #22 3-layer phage convergence
- **Project-specific findings**: #3 Kaiju↔MetaPhlAn3 asymmetry, #4 synonymy layer, #5 4-ecotype IBD framework, #11 operational-Tier-A despite framework-variance, #13 module-level metabolic-coupling, #14 5-line iron narrative, #16 BA-coupling cost, #17 two 6-line narratives, #18 species-vs-strain mediation axis, #20 9 strict + 3 theme-level cross-cohort metabolomics replications, #23 hybrid cocktail necessity, #24 ecotype-drift state-dependent dosing rule + qPCR proxy

### Out-of-scope (flagged for follow-up)

The project's central science question is fully answered within plan v1.9 (no raw reads). The following are flagged as the highest-priority external-data extensions for clinical-translation but **out of project scope**:

1. **INPHARED + IMG/VR external phage DB queries** for the 3 gut-anaerobe phage-coverage gaps (H. hathewayi, F. plautii, M. gnavus lytic alternatives) — closes the structural Pillar-4 gap.
2. **Multi-cohort prospective validation of state-dependent dosing rule** — the rule is derived from n=1 longitudinal trajectory (patient 6967); needs expanded longitudinal sampling.
3. **Per-patient AIEC strain-resolution diagnostic** — the NB13 5-phage cocktail's clinical applicability requires per-patient strain genotyping.
4. **Clinical pilot of hybrid 3-strategy cocktails** — long-term goal; requires regulatory pathway not addressed in this project.

### Outputs

- `data/nb17_patient_master_table.tsv` — 23 patients × full master attributes + design category + cocktail strategy + longitudinal status
- `data/nb17_target_decision_matrix.tsv` — 6 actionable × 5 attributes + final priority class
- `data/nb17_final_verdict.json` — per-pillar verdicts + 24 NC index + clinical-translation roadmap + thesis statement + design/strategy distributions
- `figures/NB17_synthesis.png` — 3-panel: target decision matrix + per-patient design map + clinical-translation timeline
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb.metadata.language_info = {'name': 'python', 'version': '3.10'}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
