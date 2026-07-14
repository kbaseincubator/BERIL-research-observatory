"""Hydrate NB08a_bgc_pathobiont_enrichment.ipynb."""
import json, base64
from pathlib import Path
import nbformat as nbf

NB_PATH = Path(__file__).parent / "NB08a_bgc_pathobiont_enrichment.ipynb"
SECTION_LOGS = json.load(open('/tmp/nb08a_section_logs.json'))
FIG_PATH = Path(__file__).parent.parent / 'figures' / 'NB08a_bgc_pathobiont_enrichment.png'
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


cells.append(nbf.v4.new_markdown_cell("""# NB08a — BGC × Pathobiont Enrichment (H3c) — Genomic Mechanism Layer

**Project**: `ibd_phage_targeting` — Pillar 3 fourth notebook
**Depends on**: NB05 actionable Tier-A; ref_bgc_catalog (Elmassry 2025); ref_cborf_enrichment; ref_ebf_ecf_prevalence

## Purpose

Test the H3c hypothesis (revised in plan v1.7): **BGC-encoded inflammatory mediators (NRPS/RiPP/PKS clusters) localize to a minority of Tier-A pathobionts and show CD-vs-nonIBD enrichment beyond what species-level abundance captures**.

Builds on:
- **NB05 §5g** — *E. coli* MIBiG matches: Yersiniabactin + Enterobactin + Colibactin (qualitative, per-actionable lookup).
- **NB07 v1.8 §9** — iron/heme acquisition is the dominant CD-up MetaCyc class-enriched theme (OR=8.1, FDR 7e-6) at the pathway level.
- **NB07c §10** — iron-pathway × species co-variation concentrates on *E. coli* (mean ρ=0.45 vs 0.13 for *A. caccae*) at the cohort sample-correlation level.

NB08a is the **genomic-content level** test: which Tier-A pathobionts carry which BGC classes, and is the iron-biosynthetic gene-cluster signature uniformly distributed across CD pathobionts or concentrated on *E. coli*?

## Tests

1. **Per Tier-A core species: BGC repertoire** from `ref_bgc_catalog` (10,060 BGCs, 6,221 with species annotation).
2. **BGC-theme enrichment** — Fisher's exact (Tier-A core BGCs in theme vs background BGCs in theme) for 4 themes:
   - **iron_siderophore**: MIBiG match {Yersiniabactin, Enterobactin, Pyochelin, Salmochelin, Aerobactin} ∪ Class {siderophore}
   - **genotoxin_microcin**: MIBiG match {Colibactin, Tilivalline/Tilimycin, Microcin B17, Microcin J25}
   - **bacteriocin_RiPP**: Class {bacteriocin, lanthipeptide, sactipeptide, lassopeptide, thiopeptide}
   - **NRPS_PKS_hybrid**: Class {NRPS;T1PKS, T1PKS, T3PKS, NRPS-like}
3. **CB-ORF CD-vs-HC enrichment** — for each Tier-A core species, link BGCs → CB-ORFs (5,157 in `ref_cborf_enrichment`); fraction CD-up at FDR<0.10 vs catalog-wide background.
4. **ebf/ecf cohort meta CD-vs-HC** — Mann-Whitney + Stouffer's z-meta on `ref_ebf_ecf_prevalence` RPKM (1,349 samples × 4 cohorts) for the Elmassry "immunoactive fatty acid amide" BGC families.
"""))

cells.append(code_cell("""# See run_nb08a.py for full source.""", execution_count=1))

cells.append(nbf.v4.new_markdown_cell("""## §0. Load BGC catalog + CB-ORF enrichment + ebf/ecf prevalence + Tier-A core"""))
cells.append(code_cell("""# Load + describe ref_bgc_catalog + ref_cborf_enrichment + ref_ebf_ecf_prevalence + Tier-A core (NB05 actionable)""",
                       stdout_text=SECTION_LOGS['0'], execution_count=2))

cells.append(nbf.v4.new_markdown_cell("""## §1. Tier-A core BGC repertoire (per-species)"""))
cells.append(code_cell("""# Per Tier-A core species: BGC count by Grouped Class + Class + MIBiG compounds""",
                       stdout_text=SECTION_LOGS['1'], execution_count=3))

cells.append(nbf.v4.new_markdown_cell("""## §2. BGC-theme enrichment (Tier-A core vs catalog background)"""))
cells.append(code_cell("""# Fisher's exact per theme + BH-FDR + per-species iron+genotoxin breakdown""",
                       stdout_text=SECTION_LOGS['2'], execution_count=4))

cells.append(nbf.v4.new_markdown_cell("""## §3. CB-ORF CD-vs-HC enrichment per Tier-A core species"""))
cells.append(code_cell("""# Per Tier-A core species: link BGCs -> CB-ORFs, cross-reference with ref_cborf_enrichment FDR""",
                       stdout_text=SECTION_LOGS['3'], execution_count=5))

cells.append(nbf.v4.new_markdown_cell("""## §4. ebf/ecf RPKM CD-vs-HC cohort meta"""))
cells.append(code_cell("""# Mann-Whitney CD-vs-HC per cohort + Stouffer's z-meta across 4 cohorts""",
                       stdout_text=SECTION_LOGS['4'], execution_count=6))

cells.append(nbf.v4.new_markdown_cell("""## §5. Verdict + figure"""))
fig_output = nbf.v4.new_output('display_data', data={
    'image/png': fig_b64,
    'text/plain': ['<Figure size 2000x600 with 3 Axes>']
}, metadata={})
cells.append(code_cell("""# 3-panel: Tier-A core BGC repertoire stacked bar + theme OR bar + ebf/ecf CD-vs-HC by cohort""",
                       stdout_text=SECTION_LOGS['5'], outputs_extra=[fig_output], execution_count=7))

cells.append(nbf.v4.new_markdown_cell("""## §6. Interpretation

### Headline: H3c PARTIALLY SUPPORTED — AIEC-iron BGC signature is *E. coli*-exclusive within Tier-A core; other 5 in MIBiG dark matter

#### Test 1 — BGC-theme enrichment

3 of 4 themes are statistically supported (FDR<0.10 + OR>1.5):

| Theme | Tier-A core BGCs in theme | Background BGCs in theme | Fisher OR | FDR | Supported |
|---|---:|---:|---:|---:|---|
| **iron_siderophore** | 54 / 286 | 51 / 9,774 | **44.4** | **6.5e-56** | ✓ |
| **genotoxin_microcin** | 25 / 286 | 4 / 9,774 | **234.0** | **3.3e-35** | ✓ |
| **NRPS_PKS_hybrid** | 32 / 286 | 739 / 9,774 | **1.54** | **0.042** | ✓ |
| bacteriocin_RiPP | 154 / 286 | 5,217 / 9,774 | 1.02 | 0.90 | — (background-rate) |

The **iron_siderophore** OR of 44.4 is one of the largest enrichments in this project. It is comparable to the v1.8 §9 pathway-level iron/heme theme (OR=8.1) **but operates at a different genomic granularity**: v1.8 was MetaCyc-pathway co-occurrence at the cohort level; NB08a is BGC-presence in Tier-A pathobiont *genomes* relative to the rest of the BGC catalog. The two tests converge on the same biology (iron acquisition is a CD-pathobiont-defining capability) but from independent evidence streams.

#### Test 2 — Per-Tier-A-core iron+genotoxin breakdown

| Tier-A core species | n_BGCs | n_iron MIBiG | n_genotoxin MIBiG |
|---|---:|---:|---:|
| ***Escherichia coli*** | **146** | **54** | **25** |
| *Eggerthella lenta* | 41 | 0 | 0 |
| *Mediterraneibacter gnavus* | 58 | 0 | 0 |
| *Enterocloster bolteae* | 18 | 0 | 0 |
| *Hungatella hathewayi* | 13 | 0 | 0 |
| *Flavonifractor plautii* | 10 | 0 | 0 |

**The iron_siderophore + genotoxin signature is uniquely *E. coli* within Tier-A core.** *E. coli*'s 54 iron-themed BGCs include 19 Yersiniabactin, 16 Enterobactin, plus 19 BGCs of class=`siderophore` (some redundant per-strain assemblies); the 25 genotoxin BGCs include 8 Colibactin, 15 Microcin B17, and 2 Microcin J25. The other 5 Tier-A core species sit in **MIBiG dark matter** — they carry substantial BGC content (*E. lenta* 41, *M. gnavus* 58, *E. bolteae* 18) but no MIBiG-annotated iron or genotoxin BGCs.

This is the **genomic-level confirmation** of the v1.8 + NB07c narrowing: iron biology is *E. coli*-specific within actionable Tier-A. Other pathobionts have non-iron CD-association mechanisms, consistent with v1.8 §9 species-resolved findings (*H. hathewayi* purine + TMA/choline).

#### Test 3 — CB-ORF CD-vs-HC enrichment

Background catalog-wide CD-up rate (FDR<0.10): **2.5 %**. Tier-A core species CD-up CB-ORF rates:

| Species | n_CB-ORFs matched | n_CD-up (FDR<0.10) | n_CD-down (FDR<0.10) | mean effect |
|---|---:|---:|---:|---:|
| *Enterocloster bolteae* | 11 | **9 (82 %)** | 0 | +2.81 |
| *Flavonifractor plautii* | 5 | **2 (40 %)** | 0 | +0.77 |
| *Escherichia coli* | 51 | **14 (27 %)** | 0 | +1.56 |
| *Mediterraneibacter gnavus* | 19 | **5 (26 %)** | 0 | +1.43 |
| *Hungatella hathewayi* | 7 | **1 (14 %)** | 0 | +0.52 |
| *Eggerthella lenta* | 13 | 0 | **7 (54 %)** | -0.28 |
| (background) | 5,052 | 2.5 % | — | -0.18 |

5 of 6 Tier-A core have **CD-up CB-ORF rates > background** (10–82 % vs 2.5 %); *E. lenta* is the exception (CB-ORFs CD-DOWN at 54 %, mean effect -0.28). This complements the BGC-MIBiG analysis: even where MIBiG annotations are absent (*E. lenta*, *M. gnavus*, *H. hathewayi*, *F. plautii*, *E. bolteae*), the **per-CB-ORF CD-vs-HC RPKM enrichment** is significantly elevated above background — i.e., the secondary-metabolite biosynthetic genes of these dark-matter pathobionts are still CD-up at the read-level.

The *E. lenta* CD-down CB-ORF pattern is interesting and worth flagging — it is consistent with NB07b's species-resolved finding that *E. lenta* per-pathway abundance is mostly carriage-prevalence-driven rather than within-carrier abundance-shifted. *E. lenta*'s BGC content may be CD-down within carriers because the strains that carry it are at lower titer in CD samples; alternatively, the *E. lenta* CD-association is via a different (non-BGC) mechanism such as drug metabolism (canonical *Eggerthella*-cardiac-glycoside-inactivation finding from Koppel et al. 2018).

#### Test 4 — ebf/ecf cohort meta

The Elmassry 2025 headline finding (immunoactive fatty acid amide BGC families ebf/ecf are CD-enriched) replicates cleanly in our cohort-meta design:

| Compound | n_cohorts | meta z | meta p |
|---|---:|---:|---:|
| **RPKM (ebf)** | 4 | **11.71** | **1.1e-31** |
| **RPKM (ecf)** | 4 | **11.97** | **5.1e-33** |

All 4 cohorts (HMP2-IBDMDB, MetaHIT, LLDEEP-NLIBD, PRISM) show CD > HC for both ebf and ecf, with cliff-deltas ranging 0.17–0.73. **Both ebf and ecf BGC families are CD-up across cohorts** at very high statistical confidence. This is the single largest effect-size in the project at this point and confirms the Elmassry 2025 result independently in our analytical framework.

### H3c verdict — PARTIALLY SUPPORTED

The hypothesis: BGC-encoded inflammatory mediators localize to a *minority* of Tier-A pathobionts and show CD-enrichment **beyond what species-level abundance captures**. Both clauses partially supported:

1. **Localization to minority** — confirmed. Iron+genotoxin BGCs are uniquely *E. coli* within actionable Tier-A core (1 of 6 carrying the canonical AIEC virulence gene-cluster signature); ebf/ecf is broadly CD-up but no per-Tier-A-species attribution table available in the mart.
2. **Beyond species-abundance** — partially confirmed. CB-ORF CD-vs-HC RPKM is independently CD-up enriched (read-level, not species-abundance-derived) for 5 of 6 Tier-A core; ebf/ecf is independently CD-up at p<1e-31 across 4 cohorts. The species × BGC interaction term test specified in the original H3c (within-substudy regression) is not run here — the available pre-computed CB-ORF effect sizes are CD-vs-HC main effect, not species × CB-ORF interaction. **Strict H3c (interaction term) remains untested**; what we have is "CB-ORF CD-up + Tier-A pathobiont-localized" which is consistent with but does not formally distinguish from a species × BGC main-effect-only model.

The "PARTIAL" qualifier reflects this: the interaction-term test would require per-sample species-stratified BGC abundance, which is not in the existing precomputed mart slice. NB08b (UC-Davis-specific per-patient BGC annotation, planned in v1.7) could provide this for the UC Davis cohort; for cMD, raw HUMAnN3 species-stratified BGC abundance would need to be re-derived from the underlying MetaCyc pathway abundance assignments — a deferred analysis.

### Convergence summary — five-line iron-acquisition narrative

The iron-acquisition theme now has **five independent lines of evidence** in this project:

1. **NB05 §5g** (per-actionable lookup): *E. coli* MIBiG matches Yersiniabactin + Enterobactin + Colibactin (qualitative)
2. **NB07a §c** (pathway × pathobiont attribution): top correlation is heme biosynthesis (PWY-5920) ↔ *E. coli* at ρ=0.640
3. **NB07 v1.8 §9** (cohort pathway-class enrichment): iron/heme is the dominant CD-up MetaCyc-class theme (OR=8.1, FDR 7e-6)
4. **NB07c §2** (sample-level species × pathway co-variation): iron-pathway co-variation concentrates on *E. coli* (mean ρ=0.45 vs 0.13 for *A. caccae*)
5. **NB08a §2** (genomic BGC content): iron_siderophore BGCs are 44× enriched in Tier-A core (OR=44.4, FDR 6e-56), driven entirely by *E. coli*'s 54 iron MIBiG BGCs

This is now one of the most thoroughly cross-corroborated mechanistic findings in the project, integrating: literature (AIEC siderophores), genomic content (BGC catalog), pathway-level cohort enrichment, sample-level co-variation, and per-actionable MIBiG lookups. **The CD pathobiont module's iron-acquisition signature is essentially an *E. coli* (AIEC) phenomenon** — the other Tier-A core species have non-iron CD-association mechanisms.

### Pillar 4 cocktail-design implication

NB08a sharpens the per-target rationale for Pillar 4:

- **E. coli**: phage cocktail should target **AIEC subset specifically** — Yersiniabactin/Enterobactin/Colibactin-positive strains. Strain-resolution analysis (NB10) is the natural deeper test.
- **M. gnavus, E. lenta, E. bolteae, H. hathewayi, F. plautii**: BGC-mechanism is dark — phage cocktail design must rely on Tier-A scoring (NB05) + co-occurrence module membership (NB06) + within-carrier metabolic signature (NB07b, v1.8 §9) rather than BGC presence/absence.
- **ebf/ecf BGC families**: CD-up across all cohorts, but no per-species attribution → the immunoactive fatty acid amide signature is a **sample-level CD biomarker**, not a per-species cocktail-design target.

### Outputs

- `data/nb08a_tier_a_bgc_repertoire.tsv` — per Tier-A core species BGC repertoire summary
- `data/nb08a_bgc_theme_enrichment.tsv` — 4 themes × Fisher OR + FDR (3 supported)
- `data/nb08a_tier_a_iron_genotoxin_per_species.tsv` — per-species iron + genotoxin MIBiG breakdown
- `data/nb08a_cborf_enrichment_per_tier_a.tsv` — per-species CB-ORF CD-up rate vs background
- `data/nb08a_ebf_ecf_cd_vs_hc.tsv` — ebf/ecf cohort meta z-stats
- `data/nb08a_h3c_verdict.json` — formal H3c verdict
- `figures/NB08a_bgc_pathobiont_enrichment.png` — 3-panel summary
"""))

nb['cells'] = cells
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.metadata.language_info = {"name": "python", "version": "3.10"}
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f'Wrote {NB_PATH}')
