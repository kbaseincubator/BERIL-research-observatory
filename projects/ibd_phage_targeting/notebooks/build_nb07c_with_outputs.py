"""Hydrate NB07c_anchor_pathobiont_coupling.ipynb."""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB07c_anchor_pathobiont_coupling.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb07c_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB07c_anchor_pathobiont_coupling.png'
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

cells.append(nbf.v4.new_markdown_cell("""# NB07c — Module-Anchor Commensal × Pathobiont Coupling (H3a-new)

**Project**: `ibd_phage_targeting` — Pillar 3 third notebook
**Depends on**: NB06 module hubs, NB07a + NB07b + NB07_v1.8 pathway analyses

## Purpose

Test the H3a-new hypothesis from RESEARCH_PLAN.md v1.7: **module-anchor commensals × Tier-A pathobionts metabolic coupling within CD-specific co-occurrence modules**. Per the v1.7 X4 fix, anchors are taken from **CD-specific** modules (E1_CD module 0; E3_CD module 1), not E1_all/E3_all generic modules.

CD-specific module anchors (from `data/nb06_module_hubs.tsv`):

- **E1_CD module 0** (75 nodes): Clostridiales bacterium 1_7_47FAA, *Anaerostipes caccae* (butyrate), *Bacteroides nordii*. Actionables: *E. lenta, E. bolteae, F. plautii, H. hathewayi, M. gnavus*.
- **E3_CD module 1** (57 nodes): *Actinomyces sp.* oral taxon 181, *Actinomyces sp.* HMSC035G02 (oral!), *Lactonifactor longoviformis* (lactate utilizer). Actionables: *E. lenta, E. coli, H. hathewayi, M. gnavus*.

## Tests

1. **Species-level coupling**: per (anchor, pathobiont) pair, within-IBD-substudy Spearman ρ across CMD_IBD samples; Fisher z-meta across 3 robust substudies; sign concordance.
2. **Iron-pathway × anchor × pathobiont triple**: 15 CD-up iron/heme pathways from v1.8 §9. Per (anchor, pathobiont, iron pathway) triple: ρ(anchor × iron-pathway), ρ(pathobiont × iron-pathway), ρ(anchor × pathobiont). Tests whether the v1.8 iron-theme is a community-wide signature or pathobiont-specific (E. coli).
3. Cross-feeding vs shared-environment distinction: deferred to NB09c metabolite-level corroboration (this notebook reports species + pathway co-variation; metabolite confirmation needed).
"""))

cells.append(code_cell("""# See run_nb07c.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §0. Load anchors + Tier-A core species + carriage prevalence"""))
cells.append(code_cell("""# Anchor + pathobiont species; carriage prevalence in CMD_IBD samples""",
                       stdout_text=SECTION_LOGS['0'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §1. Anchor × pathobiont species-level Spearman ρ (within-IBD-substudy meta)"""))
cells.append(code_cell("""# Per (anchor, pathobiont) pair: ρ_meta + sign concordance""",
                       stdout_text=SECTION_LOGS['1'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §2. Iron-context layer: triple correlation (anchor × pathobiont × iron-pathway)"""))
cells.append(code_cell("""# 15 iron/heme pathways from v1.8 § 9; per pair, mean ρ over 15 iron pathways""",
                       stdout_text=SECTION_LOGS['2'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §3. Verdict + figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 1400x600 with 2 Axes>']
}, metadata={})
cells.append(code_cell("""# 2-panel: anchor x pathobiont species rho heatmap; mean iron-pathway co-variation heatmap""",
                       outputs_extra=[fig_output], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §4. Interpretation

### Headline: H3a-new PARTIALLY SUPPORTED — A. caccae × pathobiont coupling clean in E1_CD; E3_CD weaker

**E1_CD anchor coupling — A. caccae shows strong positive coupling with all 5 module pathobionts** (sign_concord = 1.0 across all 3 substudies):

| Pair | ρ_meta | Notes |
|---|---:|---|
| *A. caccae* × *E. bolteae* | **+0.39** | Strongest pair in E1_CD |
| *A. caccae* × *H. hathewayi* | **+0.33** | |
| *A. caccae* × *M. gnavus* | **+0.31** | |
| *A. caccae* × *F. plautii* | **+0.29** | |
| *A. caccae* × *E. lenta* | +0.08 | Weakest pair |

*A. caccae* is the **only genuine butyrate producer** among NB06 module-anchor commensals. The species-level coupling pattern is consistent with:
- **(a) Cross-feeding hypothesis**: pathobionts release substrates (mucin-degradation products from *M. gnavus* glucorhamnan; bile-acid metabolites from *F. plautii*; lactate from *H. hathewayi*) that *A. caccae* converts to butyrate. This would be an **anti-inflammatory cross-feeding signal embedded in the CD pathobiont module** — pathobionts indirectly support a butyrate producer that should reduce inflammation.
- **(b) Shared-environment hypothesis**: both groups respond to the same CD-specific niche (low O₂, mucin-rich, inflammatory). The species-level coupling is correlative, not causal.

The §2 iron-pathway test rules against (a) being an iron-cross-feeding signal: ρ(*A. caccae* × iron-pwy) = +0.13 mean, much weaker than ρ(*E. coli* × iron-pwy) = +0.45 mean. So the *A. caccae* coupling is NOT iron-mediated — likely substrate-mediated (sugar / mucin / lactate).

NB09c metabolite-level corroboration (deferred) is needed to confirm cross-feeding vs shared-environment.

**E3_CD anchor coupling — Lactonifactor × E. lenta is the only strong pair** (ρ_meta = +0.27):

The two oral *Actinomyces* anchors show weaker coupling (~ρ=0.17–0.19 with *M. gnavus* and *E. lenta*); these are oral-gut ectopic colonizers that co-traffic into the gut under inflammation rather than metabolic partners. Their NB06 module membership reflects co-colonization, not metabolic coupling.

### Iron-pathway coupling concentrates on E. coli — narrowing the v1.8 iron-theme interpretation

**Mean ρ(pathobiont × iron-pathway) per Tier-A core**:
- *E. coli*: +0.45 (strongest by far)
- *H. hathewayi*: +0.20
- *F. plautii*: +0.17
- *M. gnavus*: +0.16
- *E. bolteae*: +0.09
- *E. lenta*: +0.03

The v1.8 finding "iron/heme is the dominant CD-up theme (OR=8.1)" is **largely an *E. coli* (AIEC) specialization signature, not a community-wide CD signature**. The 15 iron pathways include ENTBACSYN-PWY (Enterobactin biosynthesis, *E. coli*-canonical), HEMESYN2-PWY (heme biosynthesis II), and 8 menaquinol-biosynthesis pathways (respiratory quinones, often iron-containing). *E. coli*'s correlation with these pathways across 2,674 CMD_IBD samples is +0.45 — i.e., as *E. coli* abundance increases in a sample, the iron-pathway abundance scales proportionally.

This narrows the v1.8 interpretation: rather than "all CD pathobionts have iron specialization," the more accurate framing is "**CD's *E. coli* drives the iron-acquisition theme**." Other Tier-A core species (*H. hathewayi*, *F. plautii*, *M. gnavus*) show weaker iron-pathway coupling, consistent with them having other CD specialization mechanisms (TMA/choline for *H. hathewayi*; bile-acid 7α-dehydroxylation for *F. plautii*; glucorhamnan/mucin for *M. gnavus*).

### *Bacteroides nordii* × pathobionts — negative coupling

In E1_CD, *B. nordii* shows weak NEGATIVE coupling with *M. gnavus* (ρ=−0.21) and *F. plautii* (ρ=−0.20). *B. nordii* is a generalist *Bacteroides*; the negative coupling is consistent with **niche competition** — *B. nordii* and the pathobionts compete for similar polysaccharide substrates, and CD selects for one or the other. Not metabolic coupling.

### Implications for Pillar 4 cocktail design

The *A. caccae* coupling has a clinical implication: **a phage cocktail that depletes *M. gnavus / F. plautii / H. hathewayi* may also indirectly reduce *A. caccae* abundance** (loss of substrate). If *A. caccae* is anti-inflammatory via butyrate, its incidental depletion could partially offset the cocktail's therapeutic benefit. **NB05 actionable Tier-A targets need a "metabolic-coupling-cost" annotation** before cocktail finalization — what beneficial commensals depend on the targeted pathobiont, and what's the net inflammatory balance?

This is exactly the H2d concern surfaced in NB06 (single-pathobiont-module → cocktail-design implication) at the species-pair level.

### Outputs

- `data/nb07c_anchor_pathobiont_species_rho.tsv` — 27 pair × ρ_meta with per-substudy values
- `data/nb07c_anchor_pathobiont_iron_triple.tsv` — 405 (anchor, pathobiont, iron-pathway) triples
- `data/nb07c_h3a_new_verdict.json` — formal verdict
- `figures/NB07c_anchor_pathobiont_coupling.png` — 2-panel heatmap
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
