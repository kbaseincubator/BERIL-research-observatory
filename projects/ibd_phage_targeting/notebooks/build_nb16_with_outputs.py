"""Hydrate NB16_longitudinal_dosing.ipynb."""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB16_longitudinal_dosing.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb16_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB16_longitudinal_dosing.png'
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


cells.append(nbf.v4.new_markdown_cell("""# NB16 — Patient 6967 Longitudinal Stability + State-Dependent Dosing Strategy

**Project**: `ibd_phage_targeting` — Pillar 5 second notebook
**Depends on**: NB02 per-sample ecotype projection (Kuehl_WGS); NB15 per-patient cocktail draft framework; NB06 H2d ecotype-specific modules; NB07c E1_CD vs E3_CD module priority targets

## Purpose

Patient 6967 is the **only multi-timepoint UC Davis CD patient with documented E1↔E3 ecotype drift** (NB02). NB16 is the central per-patient longitudinal stability test for the project — does ecotype drift imply state-dependent cocktail dosing?

## Tests

1. **Patient 6967 per-visit comparison**: ecotype call + Tier-A pathobiont abundance + cocktail composition shift between visit 1 (E1) and visit 2 (E3)
2. **Cocktail-shift score** (Jaccard between per-visit cocktails) — quantifies how much the cocktail composition would change with ecotype drift
3. **Patient 1112 technical replicate concordance** — patient 1112 has 2 reseq samples of the same biological sample; serves as Kaiju reliability validation
4. **State-dependent dosing rule** for Pillar 5 — concrete clinical recommendation set

Per plan v1.9 no raw reads.
"""))

cells.append(code_cell("""# See run_nb16.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §0. Load Kuehl_WGS + NB02 ecotype projection + identify multi-timepoint patients"""))
cells.append(code_cell("""# 4 multi-sample patients in Kuehl_WGS; 6967 is the only true longitudinal (others are tech replicates)""",
                       stdout_text=SECTION_LOGS['0'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §1. Patient 6967 longitudinal deep dive"""))
cells.append(code_cell("""# Per-visit Tier-A abundance comparison + fold-change calculation""",
                       stdout_text=SECTION_LOGS['1'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §2. Per-visit cocktail composition (would cocktail change?)"""))
cells.append(code_cell("""# E1_CD vs E3_CD priority targets × per-visit Tier-A presence; Jaccard between visits""",
                       stdout_text=SECTION_LOGS['2'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §3. Technical replicate concordance — patient 1112"""))
cells.append(code_cell("""# Tech replicates of same biological sample; Kaiju reliability check""",
                       stdout_text=SECTION_LOGS['3'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §4. State-dependent dosing rule for Pillar 5"""))
cells.append(code_cell("""# 5 concrete clinical recommendations""",
                       stdout_text=SECTION_LOGS['4'], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §5. Verdict + figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 1800x600 with 3 Axes>']
}, metadata={})
cells.append(code_cell("""# 3-panel: 6967 per-visit Tier-A abundance + 1112 tech replicate scatter + cocktail composition shift""",
                       stdout_text=SECTION_LOGS['5'], outputs_extra=[fig_output], execution_count=7))

cells.append(nbf.v4.new_markdown_cell("""## §6. Interpretation

### Headline: Patient 6967 ecotype drift E1→E3 drives 14× M. gnavus expansion + cocktail Jaccard 0.60; Kaiju calls reliable across reseq (ρ=1.000); state-dependent dosing rule established

#### Patient 6967 longitudinal — clear E1→E3 transition with M. gnavus dominant

| Tier-A | Visit 1 (E1, conf 0.64) | Visit 2 (E3, conf 0.41) | Fold change |
|---|---:|---:|---:|
| H. hathewayi | 0.27 | 0.36 | 1.3× |
| ***M. gnavus*** | 0.53 | **7.45** | **14.0×** |
| E. coli | 0.00 | 0.00 | — |
| E. lenta | 0.40 | 1.24 | 3.1× |
| F. plautii | 0.84 | 1.62 | 1.9× |
| E. bolteae | 0.25 | 0.54 | 2.1× |

**M. gnavus 14× expansion is the dominant signature of the E1→E3 transition**. All other Tier-A pathobionts also expand (1.3–3.1×), reflecting general dysbiosis worsening, but the *M. gnavus* fold-change dominates. *E. coli* remains absent in both visits — patient 6967 is not an AIEC carrier.

This matches the NB01b ecotype framework biology: E3 = severe Bacteroides-expanded with *M. gnavus* as a dominant expansion axis; E1 = Bact2-transitional with milder pathobiont burden. Patient 6967's ecotype drift is mechanistically interpretable as *M. gnavus* outgrowth.

#### Per-visit cocktail composition — shifts but with substantial overlap

**Visit 1 (E1)**: 5 priority targets (E1_CD module 0), all 5 present → cocktail = {H. hathewayi, M. gnavus, E. bolteae, E. lenta, F. plautii}.

**Visit 2 (E3)**: 4 priority targets (E3_CD module 1), 3 present (E. coli absent in this patient) → cocktail = {E. lenta, H. hathewayi, M. gnavus}.

**Cocktail shift**:
- Shared (both visits): H. hathewayi, M. gnavus, E. lenta — **universal Tier-1 trio**
- Visit-1-only: E. bolteae, F. plautii — E1-specific (would be deprioritized on E3 transition)
- Visit-2-only: none (E. coli would be added if patient carried it; this patient does not)
- **Jaccard (visit 1 × visit 2) = 0.60** — cocktail overlap is moderate; ecotype drift implies non-trivial cocktail re-design.

#### Technical replicate concordance — patient 1112 validates Kaiju reliability

| Tier-A | Reads_1112-1 | Reads_1112_reseq-1 | Difference |
|---|---:|---:|---:|
| H. hathewayi | 0.445 | 0.436 | 2 % |
| M. gnavus | 7.916 | 7.792 | 1.6 % |
| E. coli | 0.000 | 0.000 | — |
| E. lenta | 0.712 | 0.642 | 10 % |
| F. plautii | 2.019 | 1.994 | 1.2 % |
| E. bolteae | 0.864 | 0.862 | 0.2 % |

**Spearman ρ = 1.000 (p < 0.001) on 6 Tier-A** — perfect rank concordance across reseq replicates. Kaiju calls are highly reliable for the actionable Tier-A pathobionts in UC Davis samples.

### State-dependent dosing rule (5 concrete recommendations)

Based on patient 6967 trajectory + NB07c ecotype-specific module structure:

1. **Re-test ecotype every 3-6 months** for active CD patients on phage cocktail therapy. Patient 6967 demonstrates ecotype is dynamic, not static.
2. ***F. plautii* inclusion is E1-specific** — if patient transitions E1→E3, deprioritize F. plautii from cocktail. This also reduces BA-coupling-cost concern (NB09c). Per NB07c, F. plautii is an E1_CD module 0 species, not an E3_CD module 1 species.
3. ***E. coli* inclusion is E3-specific** — if patient transitions E3→E1, deprioritize E. coli from cocktail (subject to AIEC strain detection per NB07b/NB08a). E. coli is in E3_CD module 1 priority list, not E1_CD.
4. **Universal Tier-1 trio** (M. gnavus, H. hathewayi, E. lenta) span both E1 and E3 ecotypes — these don't need re-evaluation on ecotype shift; they are the cocktail backbone for any active-disease CD patient.
5. ***M. gnavus* qPCR as cheap ecotype-state indicator** — the 14× expansion in patient 6967's E3 transition suggests *M. gnavus* abundance via qPCR could serve as a clinical proxy for ecotype shift, **avoiding the need for full metagenomics re-test at every visit**. A 5-fold change in M. gnavus abundance might be the threshold for triggering full ecotype re-evaluation.

### Pillar 5 hand-off — clinical workflow recommendation

Combining NB15 + NB16 produces a concrete clinical-translation workflow:

```
Initial visit:
  └─ Stool metagenomics → ecotype assignment
      ├─ E0: limited cocktail, flare reserve
      ├─ E1: full hybrid 3-strategy cocktail (NB13 5-phage E. coli if AIEC+;
      │       PMBT24; PMBT5; alternatives for H. hathewayi + F. plautii)
      └─ E3: focused cocktail (E. coli if present; PMBT5; alternatives)

Follow-up visits (3-6 month):
  ├─ Calprotectin: assess disease activity
  ├─ M. gnavus qPCR: cheap ecotype-state indicator
  │   └─ if 5-fold change → trigger full ecotype re-test
  └─ If full re-test shows ecotype shift:
      ├─ E1 → E3: drop F. plautii; consider adding E. coli cocktail
      ├─ E3 → E1: add F. plautii alternative; reassess E. coli targeting
      └─ Stable ecotype: continue current cocktail
```

### Limitations

- **Patient 6967 is the only multi-timepoint patient** with biological replicate samples in the UC Davis cohort. The ecotype-drift conclusions are based on n=1 longitudinal trajectory.
- **Visit 1 ecotype confidence (0.64) and visit 2 confidence (0.41)** are both moderate — the ecotype call shift could partly reflect classifier uncertainty rather than biological drift. However, the 14× M. gnavus expansion and 3× E. lenta expansion are quantitative biological observations independent of the ecotype label.
- **No timing information** between the 2 patient 6967 visits — duration of the E1→E3 drift is unknown, limiting clinical-workflow timing recommendations.
- **State-dependent dosing rule is theoretical** — not yet validated in clinical practice.
- **Cocktail Jaccard 0.60** is moderate (3 of 5 components shared); whether this implies clinically-meaningful cocktail re-design depends on patient response heterogeneity, which is out of project scope.

### Outputs

- `data/nb16_p6967_tier_a_longitudinal.tsv` — patient 6967 per-visit Tier-A abundance + fold change
- `data/nb16_longitudinal_verdict.json` — formal verdict + state-dependent dosing rules
- `figures/NB16_longitudinal_dosing.png` — 3-panel: per-visit Tier-A + tech replicate scatter + cocktail shift
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
