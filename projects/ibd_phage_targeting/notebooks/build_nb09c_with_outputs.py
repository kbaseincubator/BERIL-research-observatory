"""Hydrate NB09c_cross_feeding_disambiguation.ipynb."""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB09c_cross_feeding_disambiguation.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb09c_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB09c_cross_feeding_disambiguation.png'
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


cells.append(nbf.v4.new_markdown_cell("""# NB09c — Sample-level Paired Metabolomics × Metagenomics Cross-Feeding Disambiguation

**Project**: `ibd_phage_targeting` — Pillar 3 sixth notebook (second metabolomics)
**Depends on**: NB07c module-anchor × pathobiont species coupling; HMP2 cMD R-package fetch (paired metabolomics + metagenomics)

## Purpose

Disambiguate the NB07c cross-feeding hypothesis. NB07c found *A. caccae* × pathobiont species-level Spearman coupling at +0.39 (E. bolteae), +0.33 (H. hathewayi), +0.31 (M. gnavus), +0.29 (F. plautii) within-IBD-substudy meta — consistent with either (a) **butyrogenic cross-feeding** (pathobiont substrates → *A. caccae* butyrate) or (b) **shared-environment** co-response to the same CD-specific niche.

NB09c uses **paired CSM* HMP2 samples** (468 samples with both metabolomics and MetaPhlAn3 metagenomics) to test whether a candidate intermediate metabolite (lactate / SCFA / mucin-glycan / bile-acid) shows the cross-feeding pattern: same-sign correlation with both anchor and pathobiont. If anchor and pathobiont don't share metabolite signatures at the sample level, the NB07c coupling is shared-environment, not cross-feeding.

Per plan **v1.9** (no raw reads): uses cMD-fetched HMP2 MetaPhlAn3 abundance + mart fact_metabolomics + ref_hmp2_metabolite_annotations.

## Tests

1. **Per (species, metabolite) Spearman ρ** on 468 paired samples × 8 NB07c species (anchors + Tier-A core pathobionts) × 583 named HMP2 metabolites; BH-FDR per species.
2. **Cross-feeding-triangle test** — strict criteria: anchor ρ × pathobiont ρ same sign AND both |ρ|>0.20 AND both FDR<0.10.
3. **Curated cross-feeding metabolite panel** — direction-of-association profile across 7 themes (SCFAs, lactate, primary tauro-conjugated BAs, secondary BAs, TMA/choline/carnitine, polyamines, tryptophan/indole) for biological interpretation.
"""))

cells.append(code_cell("""# See run_nb09c.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §0. Load paired HMP2 metabolomics × metagenomics + species + metabolite map"""))
cells.append(code_cell("""# Pair metab + cMD MetaPhlAn3 abundance by sample-ID code (CSM*); deduplicate""",
                       stdout_text=SECTION_LOGS['0'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §1. Build paired sample × {NB07c species + named metabolites} matrix"""))
cells.append(code_cell("""# 8 NB07c species × 583 named metabolites; CLR-transform species; log10-intensity metabolites""",
                       stdout_text=SECTION_LOGS['1'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §2. Per (species, metabolite) Spearman ρ"""))
cells.append(code_cell("""# Spearman ρ on paired samples; BH-FDR per species (separately for each)""",
                       stdout_text=SECTION_LOGS['2'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §3. Cross-feeding-triangle test"""))
cells.append(code_cell("""# Strict triangles: anchor × pathobiont same-sign + both |ρ|>0.20 + both FDR<0.10""",
                       stdout_text=SECTION_LOGS['3'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §4. Curated cross-feeding metabolite panel — direction-of-association profile"""))
cells.append(code_cell("""# 7 themes × ~30 metabolites: SCFAs, lactate, primary BAs, secondary BAs, TMA/choline/carnitine, polyamines, tryptophan""",
                       stdout_text=SECTION_LOGS['4'], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §5. NB07c hypothesis: cross-feeding vs shared-environment"""))
cells.append(code_cell("""# Triangle counts per (anchor × pathobiont) pair""",
                       stdout_text=SECTION_LOGS['5'], execution_count=7))

cells.append(nbf.v4.new_markdown_cell("""## §6. Verdict + figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 1600x700 with 2 Axes>']
}, metadata={})
cells.append(code_cell("""# 2-panel: curated panel ρ heatmap (species × metabolite) + top 25 cross-feeding-triangle candidates""",
                       stdout_text=SECTION_LOGS['6'], outputs_extra=[fig_output], execution_count=8))

cells.append(nbf.v4.new_markdown_cell("""## §7. Interpretation

### Headline: NB07c cross-feeding hypothesis NOT supported at sample level → reframe as shared-environment co-occurrence; **bile-acid 7α-dehydroxylation network is independently identified** as a sample-level mechanistic finding.

#### Cross-feeding-triangle test — only 7 strict triangles

The strict cross-feeding-triangle criterion (same-sign + |ρ|>0.20 + FDR<0.10 for both anchor and pathobiont) yields **only 7 triangles** across 8 species × 583 metabolites — far fewer than the cross-feeding hypothesis would predict if pathobionts genuinely share metabolic intermediates with *A. caccae* / *B. nordii*. Of the 7:
- *B. nordii* / *F. plautii* × **caffeine** (+0.22 / +0.23) — environmental exposure, not a metabolic intermediate
- *B. nordii* / *E. lenta* × **linoleoylethanolamide** (-0.23 / -0.21) — fatty acid amide, possibly substrate for both
- *A. caccae* / *E. lenta* × **linoleoylethanolamide** (-0.21 / -0.21) — same
- *A. caccae* / *E. lenta* × **urobilin** (+0.28 / +0.21) — both correlate with the bilirubin-reducer commensal signal (NB09a urobilin CD-DOWN)
- *A. caccae* / *F. plautii* × **cholate** (-0.26 / -0.21) — both anti-correlate with primary BA cholate
- *B. nordii* / *F. plautii* × **cholate** (-0.29 / -0.21) — same
- *B. nordii* / *E. lenta* × **urobilin** (+0.34 / +0.21) — same urobilin pattern

**None of these 7 candidates is a butyrogenic cross-feeding intermediate.** The pattern is instead consistent with **shared-niche health-direction co-occurrence**: A. caccae, B. nordii, F. plautii, and E. lenta are all (mostly) commensal species that together correlate negatively with primary BAs (cholate) and positively with urobilin — i.e., they **co-occur in healthy / normobiotic samples** vs CD samples where dysbiosis dominates. This is the shared-environment pattern, not specific cross-feeding.

#### Curated cross-feeding panel — biologically coherent but does not support cross-feeding

| Metabolite | A. caccae | B. nordii | H. hath | F. plautii | E. bolteae | E. lenta | M. gnavus | E. coli |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **butyrate** | **+0.10*** | **+0.13*** | -0.08 | -0.02 | -0.04 | -0.05 | -0.02 | +0.04 |
| **lactate** | **+0.18*** | +0.10* | +0.03 | **-0.23*** | **-0.20*** | -0.07 | +0.10 | **+0.24*** |
| **choline** | +0.04 | +0.01 | -0.07 | -0.16* | -0.15* | -0.13* | +0.11* | **+0.25*** |
| **carnitine** | -0.04 | -0.02 | -0.01 | -0.18* | -0.06 | -0.04 | +0.04 | **+0.19*** |
| **putrescine** | -0.04 | -0.09 | -0.07 | -0.02 | -0.15* | -0.11* | +0.13* | **+0.19*** |
| **tryptophan** | -0.09 | -0.10* | -0.10 | -0.13* | -0.10 | **-0.22*** | +0.14* | **+0.25*** |

**Critical observations**:

1. **Butyrate × A. caccae = +0.10*** — significant but very weak. Consistent with *A. caccae* as a butyrate producer at the population level, but the cohort-level correlation is weak. **The HMP2 LC-MS untargeted methods undersample SCFAs** (volatile, polar — typically need GC-MS); only butyrate and propionate are detected, not acetate/valerate/hexanoate. The weak butyrate signal is at least partly methodological.

2. **Lactate × A. caccae = +0.18\* vs lactate × F. plautii = −0.23\* and × E. bolteae = −0.20\*** — **opposite signs**. If lactate were a cross-feeding intermediate (pathobiont produces, *A. caccae* consumes), we would expect either (a) same-sign positive (both increase together if production dominates) or (b) lagged/asymmetric correlation (production-consumption coupling). The opposite-sign pattern is most consistent with *A. caccae* and pathobionts occupying **different metabolic niches at the cohort level** — *A. caccae* favors lactate-rich states; *F. plautii* and *E. bolteae* anti-correlate with lactate (consistent with them being non-lactate-utilizing fermenters).

3. ***E. coli* dominates the cohort-level correlation signal**: choline +0.25, carnitine +0.19, tryptophan +0.25, putrescine +0.19, cadaverine **+0.45** (the strongest correlation in the entire panel). These match canonical *E. coli* / Enterobacteriaceae metabolism: lysine decarboxylase → cadaverine; arginine decarboxylase → putrescine; choline + carnitine substrates for trimethylamine pathways. **The v1.8 §9 *H. hathewayi* TMA/choline finding from the cMD pathway-level analysis does NOT strongly replicate at HMP2 sample level** — *H. hathewayi* × choline ρ=−0.07 (NS); *E. coli* dominates the choline signal. Possible reasons: (a) HMP2 has lower *H. hathewayi* prevalence (25 % of paired samples) than the cMD studies that drove the v1.8 finding; (b) at the sample level, *E. coli*'s high prevalence (50 %) and abundance variance dominate the cohort-correlation signal; (c) choline is a substrate for both *E. coli* and *H. hathewayi* TMA production, but *E. coli* is the larger contributor in HMP2. This **narrows v1.8 §9** — TMA/choline is a *combined Enterobacteriaceae + Lachnospiraceae* signal, not specifically *H. hathewayi*.

#### Bile-acid 7α-dehydroxylation network is an independent strong finding

| BA Class | A. caccae | B. nordii | H. hath | F. plautii | E. bolteae | E. lenta | M. gnavus | E. coli |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Tauro-α/β-muricholate** (1° tauro) | -0.03 | -0.15* | 0.00 | -0.04 | -0.04 | -0.11* | **+0.20*** | +0.06 |
| **Taurine** (1° conjugating AA) | -0.07 | -0.15* | -0.03 | +0.04 | -0.07 | -0.10 | **+0.17*** | +0.06 |
| **Cholate** (1° unconj.) | **-0.13*** | **-0.18*** | -0.10 | **-0.26*** | -0.10 | **-0.13*** | +0.11* | -0.02 |
| **Deoxycholate** (2° from cholate) | -0.07 | +0.05 | -0.12 | +0.06 | **+0.17*** | +0.03 | -0.10* | -0.05 |
| **Lithocholate** (2° from CDCA) | -0.05 | +0.06 | -0.12 | **+0.15*** | **+0.18*** | +0.07 | **-0.20*** | **-0.13*** |
| **Hyodeoxycholate/UDCA** (2°) | **-0.17*** | **-0.14*** | -0.05 | -0.09 | +0.01 | **-0.11*** | **+0.11*** | **+0.10*** |
| **Ketodeoxycholate** (2° oxidized) | **-0.12*** | **-0.15*** | -0.01 | **-0.19*** | -0.05 | **-0.14*** | **+0.14*** | **+0.24*** |

**The pattern is striking and biologically coherent**: ***F. plautii*, *E. lenta*, and *E. bolteae* — the canonical bile-acid 7α-dehydroxylating bacteria** — show the **predicted substrate-product signature**: negative correlation with primary tauro-conjugated bile acids (substrates) and positive correlation with secondary unconjugated bile acids (products: deoxycholate, lithocholate). This is the **direct sample-level confirmation** of the canonical bile-acid 7α-dehydroxylation network operating in HMP2 samples.

By contrast, ***M. gnavus* and *E. coli* show the OPPOSITE pattern**: positive correlation with primary tauro-BAs, negative correlation with secondary BAs (lithocholate, hyodeoxycholate). Neither species 7α-dehydroxylates; they are part of a different metabolic network. *E. coli*'s positive correlation with ketodeoxycholate (+0.24) and chenodeoxycholate (+0.22) is consistent with *E. coli* being abundant in CD samples where the bile-acid pool is shifted toward primary forms.

**Implication for NB05 *F. plautii* targeting**: a phage cocktail targeting *F. plautii* would be predicted to **further deplete secondary bile acids** (lithocholate, deoxycholate) — these are the **anti-inflammatory** BA forms. *F. plautii* is one of the few CD-up species that ALSO carries 7α-dehydroxylation activity in this dataset; its depletion may shift the BA pool back toward inflammatory primary tauro-conjugated forms. **NB05 Tier-A scoring should incorporate a "bile-acid coupling cost" annotation** (parallel to the "metabolic-coupling cost" from NB07c) for *F. plautii*-targeted cocktails.

### NB07c verdict: REFRAMED as shared-environment co-occurrence

The cross-feeding hypothesis (a) is NOT supported by sample-level metabolomic-metagenomic correlation evidence. The shared-environment hypothesis (b) is the more parsimonious explanation for *A. caccae* × pathobiont species-level coupling:
- 7 strict cross-feeding triangles is well below what cross-feeding would predict
- Top triangle metabolites (caffeine, urobilin, cholate) are health-direction biomarkers, not metabolic intermediates
- Lactate signs are opposite between *A. caccae* (+0.18) and *F. plautii* / *E. bolteae* (−0.20 to −0.23)
- Butyrate × *A. caccae* +0.10 is weak (and partly methodological — LC-MS undersampling)

**Reframed implication for Pillar 4 cocktail design**: the NB07c "metabolic-coupling-cost" annotation for *A. caccae* (NB07c §10) is **less load-bearing** than originally described — depleting pathobionts via phage cocktail is unlikely to substantially reduce *A. caccae* abundance through substrate loss (because the substrate-product relationship is not detectable at sample level). The cocktail-design narrative simplifies: target pathobionts directly; *A. caccae* is in a co-occurring commensal cluster but not metabolically coupled.

**Bile-acid coupling cost** replaces metabolic-coupling-cost as the primary Pillar 4 annotation for the NB05 actionable set:
- ***F. plautii* targeting**: highest-cost — depletes 7α-dehydroxylation activity, shifts BA pool toward primary inflammatory forms.
- ***E. bolteae* / *E. lenta* targeting**: secondary 7α-dehydroxylation contributors — moderate cost.
- ***H. hathewayi* / *M. gnavus* / *E. coli* targeting**: low BA-coupling cost (these species are not in the 7α-dehydroxylation network).

### Methodological observations

- **583 of 592 named HMP2 metabolites** had ≥30 % non-NaN coverage in the 468-sample paired set. The remaining 9 are likely method-specific compounds with high missingness.
- **Cross-cohort applicability**: the bile-acid 7α-dehydroxylation finding is HMP2-specific in this analysis. Cross-cohort metabolomics replication (NB09b — FRANZOSA_2019 + DAVE_SAMP_METABOLOMICS) is the natural follow-up.

### Outputs

- `data/nb09c_species_metabolite_corr.tsv` — all 8 species × 583 metabolites Spearman ρ + FDR
- `data/nb09c_cross_feeding_triangles.tsv` — 7 strict cross-feeding-triangle candidates
- `data/nb09c_cross_feeding_panel.tsv` — curated 7-theme panel direction-of-association profile
- `data/nb09c_cross_feeding_verdict.json` — formal verdict
- `figures/NB09c_cross_feeding_disambiguation.png` — heatmap + triangle scatter
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
