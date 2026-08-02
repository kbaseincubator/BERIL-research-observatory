#!/usr/bin/env python3
"""
Publication-quality analysis overview flowchart.
Comprehensive Metal Ecology — MacGregor & Arkin (2026)
Output: figures/analyses_overview.pdf
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

# ── Figure ──────────────────────────────────────────────────────────────────────
FW, FH = 22, 15
fig = plt.figure(figsize=(FW, FH))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FW)
ax.set_ylim(0, FH)
ax.axis('off')
fig.patch.set_facecolor('white')

# ── Palette: (header_dark, band_bg, box_border) ─────────────────────────────────
PAL = [
    ('#1B4F72', '#D6EAF8', '#2471A3'),   # L1  blue       — core hypothesis
    ('#6C3483', '#F4ECF7', '#8E44AD'),   # L2  purple     — internal split
    ('#0E6655', '#D1F2EB', '#148F77'),   # L3  teal       — multi-axis
    ('#943126', '#FADBD8', '#C0392B'),   # L4  crimson    — mechanism
    ('#1A5E35', '#D5F5E3', '#239B56'),   # L5  green      — functional gen.
    ('#145A32', '#D5E8D4', '#1E8449'),   # L6  dark green — external valid.
    ('#7D6608', '#FEFDE7', '#9A7D0A'),   # L7  amber      — robustness
    ('#512E5F', '#EAD5F5', '#76448A'),   # L8  deep purple— catboost
    ('#6E2C00', '#FAE5D3', '#BA4A00'),   # L9  burnt org. — experimental
]

CENTRAL = {0, 1, 3, 5, 8}   # 0-indexed layers in central narrative

# ── Layout ──────────────────────────────────────────────────────────────────────
MX    = 0.22    # left/right margin
HW    = 1.52    # header strip width
BP    = 0.09    # vertical padding inside band (above/below item boxes)
IG    = 0.09    # gap between item boxes horizontally
CX0   = MX + HW + 0.06        # content area left edge
CW    = FW - MX - CX0         # content area width
AX    = MX + HW / 2           # x for inter-layer arrows

# Layer heights (inches)
LH = [1.44, 1.30, 1.44, 1.28, 1.38, 1.28, 1.44, 1.18, 1.08]
LG = 0.14    # gap between layers

# Compute y_top, y_bot from figure top
y_tops, y_bots = [], []
y = FH - MX - 0.52 - 0.08   # top of Layer 1
for h in LH:
    y_tops.append(y)
    y_bots.append(y - h)
    y -= h + LG

# ── Header labels ───────────────────────────────────────────────────────────────
HTXT = [
    'Layer 1\nCore Hypothesis\n& Primary Test',
    'Layer 2\nInternal\nFunctional Split',
    'Layer 3\nMulti-Axis\nNiche Framework',
    'Layer 4\nMechanism:\nTwo-Scale Phylo-D',
    'Layer 5\nFunctional\nGeneralisation',
    'Layer 6\nExternal\nValidation',
    'Layer 7\nRobustness\n& Sensitivity',
    'Layer 8\nCatBoost LOPO\nML Validation',
    'Layer 9\nExperimental\nProposal',
]

# ── Box content: list of (title, body_text, is_main) per layer ──────────────────
BOX = [
  # ── Layer 1: Core Hypothesis ──────────────────────────────────────────────────
  [
    ('Primary PGLS (H1 confirmed)',
     'Metal-gene density → cross-biome niche breadth\n'
     'β = −0.021 · SE = 0.0037 · p ≈ 2×10⁻⁸ · n = 1,574\n'
     "Pagel’s λ = 0.757 · ΔAIC = −29.4 · r² = 0.046\n"
     'Pre-registered; direction confirmed on GTDB r214', True),
    ('Archaeal replication',
     'n = 95 · β = −0.014 · p = 0.119\n'
     'Directionally consistent with H1\n'
     'Non-significant: underpowered (~40% power)\n'
     'Expanded archaeal dataset: future priority', False),
    ('Australia NGSA null test',
     'Soil metal conc. → niche breadth: β = −0.002, p = 0.755\n'
     'Predictor insensitivity, not population failure\n'
     'Soil conc. ≠ genomic KO density (different predictor)\n'
     'Per-metal Cu/Zn: FDR q = 0.041 (pH-controlled)', False),
    ('Confounder checks (5 pre-specified)',
     'Genome size: 47% attenuation → robust (p = 0.006)\n'
     'GC content: 24% attenuation → robust\n'
     'Latitude: amplified (−52%!) → suppressor variable\n'
     'Biome (6%) · isolation source (15%) → robust', False),
  ],
  # ── Layer 2: Internal Split ───────────────────────────────────────────────────
  [
    ('Resistance / Detoxification (106 KOs)',
     'β = +0.003 · p = 0.656 · null on cross-biome breadth\n'
     'Positive on geochemical breadth (β = +0.073**)\n'
     'Positive on co-occurrence degree (β = +4.1***)\n'
     'HGT-mobile; decoupled from genome streamlining', False),
    ('Cofactor biosynthesis (7 KOs)',
     'β = −0.033 · p = 5×10⁻⁹ · strongest subcategory\n'
     'Fe–S cluster · molybdopterin · cobalamin\n'
     'Constitutively expressed; vertically inherited\n'
     'Equal to housekeeping streamlining baseline', True),
    ('Split-magnitude permutation (Δβ = 0.035)',
     '1,000 random partitions of 140-KO set (106 vs 7)\n'
     'Δβ = 0.035259 exceeds ALL null splits · p < 0.001\n'
     '~6 SD above null median (SD = 0.007)\n'
     'ABC / AMR / TCS splits all smaller (Δβ ≤ 0.032)', True),
    ('Non-metal cofactor & cofactor jackknife',
     'Non-metal cofactor: β = −0.029 ≈ metal β = −0.033\n'
     '→ Biosynthetic cost drives signal, not metal identity\n'
     'Jackknife (leave-1-KO-out): all 3-KO remainders significant\n'
     'β range −0.016 to −0.029 · no sign changes', True),
  ],
  # ── Layer 3: Multi-Axis Framework ────────────────────────────────────────────
  [
    ('Cross-biome Levins’ B (primary axis)',
     'Cofactor: β = −0.033*** · Resistance: β ≈ 0 (null)\n'
     'Transport/homeostasis: β = −0.022**\n'
     'Sensing/regulation: β = −0.018** · Non-metal cofactor: β = −0.029***\n'
     'Polarity confirmed: cofactor specialist = generalist metabolically', True),
    ('Geochemical breadth (Env PC1)',
     'Within-genus SD across pH, temp., 5 GeoROC metals\n'
     'Resistance: β > 0 (positive) → wide chemical niche\n'
     'Cofactor: null on geochemical breadth\n'
     'Polarity inverted: resistance expands local niche only', False),
    ('Social niche breadth (co-occurrence degree)',
     'Phi-coefficient network · 162,022 soil samples, 3,149 genera\n'
     "Pagel’s λ = 0.48–0.57 (phylogenetically informative)\n"
     'Resistance: β = +4.1*** · metal-rich genera are hubs\n'
     '56% top-quartile partners also metal-rich; Firmicutes-biased', False),
    ('Scale boundary: CWM & within-soil',
     'Within-soil niche breadth (β_soil): null signal\n'
     'Community-weighted mean (3 metal sources, 7 covariates):\n'
     '|β| < 0.006 · all p > 0.2 → cross-biome phenomenon only\n'
     'Metal-gene / niche link undetectable at within-biome scale', False),
  ],
  # ── Layer 4: Mechanism — Two-Scale Phylo-D ───────────────────────────────────
  [
    ('Two-scale phylogenetic signal (275 KOs)',
     "Genus-level Pagel’s λ on continuous KO presence fractions\n"
     'Genome-level Fritz & Purvis D on binary presence (18,961 tips)\n'
     'Spearman ρ = −0.041 · p = 0.49 → orthogonal measures\n'
     'Capture distinct evolutionary processes (vertical vs HGT)', True),
    ('13 double-signal KOs (D > 0.2, λ < 0.3)',
     'Dispersed at BOTH evolutionary scales → repeated HGT\n'
     'Hg resistance: merD (λ = 0.165) · merE (λ = 0.102)\n'
     'As resistance: aoxB · gesA · gesB (gold/tellurite)\n'
     'Cu resistance: cusA λ = 0.79 (vertically inherited; negative control)', True),
    ('Differential mobility mechanism',
     'Cofactor (Fe–S, molybdopterin, cobalamin):\n'
     '  high λ + low D → vertically inherited; metabolically essential\n'
     'Resistance: low λ + high D → HGT-mobile; tracks local metal\n'
     'Pangenome coreness: cofactor 2.2× more prevalent than resistance', True),
  ],
  # ── Layer 5: Functional Generalisation ───────────────────────────────────────
  [
    ('KEGG functional landscape (19 categories)',
     '14/19 significant (BH-FDR q < 0.05) · Metal ranks 11th\n'
     'Streamlining baseline: β ≈ −0.030 to −0.035 (housekeeping)\n'
     '5 confirmed true-negative controls: ABC, AMR, motility, TCS, glycan\n'
     'Appropriate null = housekeeping baseline, not zero', False),
    ('Expanded KEGG cofactor set (47 KOs)',
     '8 KEGG modules: M00880 · M00121/926 · M00122/924\n'
     'M00846 · M00175/176 (Fe–S cluster assembly)\n'
     'Full set: β = −0.011 · p = 0.010\n'
     'Cobalamin (18 KOs) primary driver: β = −0.011 · p = 0.005', False),
    ('Non-exclusive KO classification (93 KOs)',
     'KOs assigned proportionally across functional categories\n'
     'Metal-dependent metabolism expanded: 1 → 93 KOs\n'
     'Still patterns with resistance (β ≈ 0), not cofactor\n'
     'Constitutive biosynthetic coupling is the key discriminant', False),
    ('Comparison gene families (ABC, AMR, TCS)',
     'ABC transporters: Lipid/LPS export only shows cofactor-like β\n'
     'AMR: all positive (β = +0.018 for efflux pumps)\n'
     'TCS: all positive · metal split is family-specific\n'
     'Requires constitutive metabolic coupling to target phenotype', False),
  ],
  # ── Layer 6: External Validation ──────────────────────────────────────────────
  [
    ('Frossard 2017 (Hg-contaminated soils, Switzerland)',
     'Industrial Hg contamination · bacterial niche breadth\n'
     'Hg-tolerant: B_std = 0.407 vs non-tolerant: 0.233 · p < 0.0001\n'
     'Effect size comparable to primary finding\n'
     'Independent replication: direction confirmed', True),
    ('Li 2022 (Hg field gradient, China)',
     'Long-term Hg-contaminated agricultural soils\n'
     'CWM niche breadth elevated: 0.365 vs control 0.233\n'
     'Community-level corroboration of genus-level pattern\n'
     'Direction consistent with H1 prediction', False),
    ('NGSA geochemical replication (soil Cu, Zn)',
     'NGSA ICP-MS metals · AMI 16S · 200 km join · n = 482\n'
     'Cu: β = −0.011 · FDR q = 0.041 · Zn: β = −0.011 · q = 0.041\n'
     'Pb: q = 0.057 · Ni: q = 0.061 · Co: reversed (β > 0)\n'
     'Partial replication (2/5 metals) · lower λ = 0.32–0.35', True),
    ('Mechanism boundaries (Goff 2024 · Frossard 2018)',
     'merA + merR on conjugative plasmids at Oak Ridge Reservation\n'
     'Abdelmageed 2021: anoxic specialists via hgcA Hg methylation\n'
     'Frossard 2018 field gradient: null · microcosm: null\n'
     '→ Boundary: aerobic tolerance ≠ anaerobic methylator specialism', False),
  ],
  # ── Layer 7: Robustness & Sensitivity ────────────────────────────────────────
  [
    ('8 pre-specified sensitivity analyses',
     '7/8 directionally consistent (all β < 0 except raw count)\n'
     'OLS: β = −0.032 · Brownian: β = −0.018\n'
     'Northern hemisphere: β = −0.030 · soil-restricted: β = −0.033\n'
     'Raw count (no per-Mb normalisation): NS → confirms per-Mb required', False),
    ('MAG quality & phylum stratification',
     'High-quality MAGs (≥90% comp., ≤5% contam., n = 511):\n'
     'β = −0.018 · p = 0.005 → signal not driven by low-quality MAGs\n'
     'Proteobacteria (n = 677) + Actinobacteria (n = 204): FDR significant\n'
     'Firmicutes borderline · Bacteroidetes high λ = 0.917 (near-Brownian)', False),
    ('Cofactor–housekeeping residualised (H4c)',
     'ρ(expanded cofactor density, translation density) = 0.038 ≈ 0\n'
     'Residualised β = −0.013 · p = 0.004 (stronger than naïve)\n'
     'Semi-partial R²: cofactor = 0.008 · genome size = 0.010\n'
     'Cofactor signal is independent of general metabolic investment', False),
    ('Niche-breadth metric & species-level',
     'Bootstrap (100 resamples): r = 0.999 vs original · Δβ = 0.00083\n'
     'EMP validation (n = 539): β = −0.019 · ρ = 0.211 (p < 10⁻⁶)\n'
     'Species-level (5 genera): 5/5 negative · 3/5 significant (p < 0.001)\n'
     'Coreness-matched permutation: emp p = 0.298 (landscape artefact ruled out)', False),
  ],
  # ── Layer 8: CatBoost LOPO ───────────────────────────────────────────────────
  [
    ('CatBoost LOPO · 15 environmental responses',
     '11 phyla (≥10 genera) · Leave-One-Phylum-Out cross-validation\n'
     '13/15 responses: positive average Spearman ρ\n'
     'Soil pH: ρ = 0.213 · CSU-As: ρ = 0.174 · Bedrock Co: ρ = 0.163\n'
     'Complements PGLS: non-linear signal, cross-phylum transferability', False),
    ('SHAP feature importance',
     'hemH + cobT: porphyrin/cobalamin biosynthesis cluster\n'
     'cusA (K07787): most consistent across PGLS and CatBoost\n'
     'emrB (K03446): highest mean |SHAP| across env. responses\n'
     'copA (K17686): specialist pattern · negative on metal axes', False),
    ('KO prioritisation (composite ranking)',
     'hemH (K01772) · ferrochelatase · porphyrin pathway\n'
     'cobT (K09883) · cobalamin adenosyltransferase\n'
     'cusC (K07796) · Cu/Ag efflux outer-membrane · bmrR (K19575)\n'
     'zur (K09823) · zinc uptake regulator · spans both sides of split', False),
  ],
  # ── Layer 9: Experimental Proposal ───────────────────────────────────────────
  [
    ('Cobalamin co-culture experiment',
     'Producer:auxotroph ratio varied in replicated gradient chambers\n'
     'Predict: community breadth ∝ cobalamin biosynthesis capacity\n'
     'Producers: P. stutzeri · S. meliloti (complete pathway)\n'
     'cobT knockout in producer: within-strain experimental control', True),
    ('HGT mechanism validation',
     'Resistance/niche assoc. weaker in HGT-acquired vs. vertical genera?\n'
     'Reconciliation-based gene-tree / species-tree analyses\n'
     'Plasmid localisation (PLSDB / PlasClass) across high-quality assemblies\n'
     'Synteny analyses of resistance gene neighbourhoods', True),
    ('Conjugation microcosm & KO follow-up',
     'Generalist vs specialist Burkholderiales + mer plasmid\n'
     'Fitness cost assay · transfer rate · retention without selection\n'
     'Transcriptomics across metal gradients\n'
     '5 prioritised KOs for functional follow-up (hemH·cobT·cusC·bmrR·zur)', False),
  ],
]

# ── Draw all layers ──────────────────────────────────────────────────────────────
for li in range(9):
    fg, bg, bd = PAL[li]
    yt, yb = y_tops[li], y_bots[li]
    h = yt - yb
    is_cen = li in CENTRAL

    # Band background (content area)
    ax.add_patch(mpatches.Rectangle(
        (MX + HW, yb), FW - 2*MX - HW, h,
        facecolor=bg, alpha=0.62 if is_cen else 0.28,
        edgecolor='none', zorder=1))

    # Header strip
    ax.add_patch(mpatches.Rectangle(
        (MX, yb), HW, h,
        facecolor=fg, edgecolor='none', linewidth=0, zorder=2))

    # Outer row border
    ax.add_patch(mpatches.Rectangle(
        (MX, yb), FW - 2*MX, h,
        fill=False,
        edgecolor=bd if is_cen else '#C0C0C0',
        linewidth=2.0 if is_cen else 0.8,
        zorder=6))

    # Header label
    ax.text(MX + HW / 2, yb + h / 2, HTXT[li],
            ha='center', va='center',
            fontsize=7.4, fontweight='bold',
            color='white', multialignment='center', zorder=3)

    # Content item boxes
    items = BOX[li]
    n = len(items)
    iw = (CW - IG * (n - 1)) / n
    x = CX0
    for title, body, is_main in items:
        bx_lw = 1.9 if is_main else 0.7
        bx_ec = bd if is_main else '#C8C8C8'
        ax.add_patch(FancyBboxPatch(
            (x + 0.05, yb + BP), iw - 0.10, h - 2*BP,
            boxstyle='round,pad=0.05',
            facecolor='white', edgecolor=bx_ec,
            linewidth=bx_lw, zorder=4))

        cx   = x + iw / 2
        bh   = h - 2 * BP
        cy   = yb + BP + bh / 2
        fst  = 7.1 if is_main else 6.8  # title fontsize
        fsb  = 6.2                       # body fontsize

        # bold title above centre
        ax.text(cx, cy + bh * 0.21, title,
                ha='center', va='center',
                fontsize=fst, fontweight='bold', color='#0A0A0A',
                multialignment='center', zorder=5)
        # body text below centre
        ax.text(cx, cy - bh * 0.21, body,
                ha='center', va='center',
                fontsize=fsb, color='#2C2C2C',
                multialignment='center', zorder=5)
        x += iw + IG

# ── Title ────────────────────────────────────────────────────────────────────────
ty = y_tops[0] + LG + 0.40
ax.text(FW / 2, ty,
        'Comprehensive Metal Ecology — Analysis Overview',
        ha='center', va='center',
        fontsize=13.5, fontweight='bold', color='#1A1A1A', zorder=10)
ax.text(FW / 2, ty - 0.28,
        'MacGregor & Arkin (2026)  ·  9 analytical layers  ·  '
        'Thick borders = central narrative (Layers 1 → 2 → 4 → 6 → 9)',
        ha='center', va='center',
        fontsize=8.5, color='#555555', zorder=10)

# ── Inter-layer arrows ───────────────────────────────────────────────────────────
# Central narrative pairs (0-indexed): 0→1, 1→3, 3→5, 5→8
MAIN_PAIRS = {(0, 1), (1, 3), (3, 5), (5, 8)}
for i in range(8):
    y_from = y_bots[i] - 0.01
    y_to   = y_tops[i + 1] + 0.01
    is_main_arr = (i, i + 1) in MAIN_PAIRS
    ax.annotate(
        '', xy=(AX, y_to), xytext=(AX, y_from),
        arrowprops=dict(
            arrowstyle='->',
            color='#2C2C2C' if is_main_arr else '#AAAAAA',
            lw=2.4 if is_main_arr else 1.1,
            mutation_scale=14 if is_main_arr else 9),
        zorder=10)

# ── Central narrative right-edge marker ─────────────────────────────────────────
cen_sorted = sorted(CENTRAL)
bx = FW - MX - 0.01
for li in cen_sorted:
    ax.add_patch(mpatches.Rectangle(
        (bx - 0.10, y_bots[li]), 0.10, y_tops[li] - y_bots[li],
        facecolor='#1A1A2E', edgecolor='none', zorder=7))

# Label the marker bar (rotated)
top_li = cen_sorted[0]
bot_li = cen_sorted[-1]
mid_y  = (y_tops[top_li] + y_bots[bot_li]) / 2
ax.text(bx - 0.05, mid_y, 'Central\nnarrative',
        ha='center', va='center',
        fontsize=6.3, fontweight='bold',
        color='white', rotation=90, zorder=8)

# ── Legend ───────────────────────────────────────────────────────────────────────
leg_y = y_bots[8] - 0.22
leg_x = CX0
ax.add_patch(FancyBboxPatch(
    (leg_x, leg_y - 0.17), 5.5, 0.28,
    boxstyle='round,pad=0.04',
    facecolor='white', edgecolor='#444444',
    linewidth=1.2, zorder=11))

# Main box swatch
ax.add_patch(FancyBboxPatch(
    (leg_x + 0.12, leg_y - 0.10), 0.55, 0.14,
    boxstyle='round,pad=0.02',
    facecolor='white', edgecolor='#2471A3',
    linewidth=1.9, zorder=12))
ax.text(leg_x + 0.75, leg_y - 0.03,
        'Thick border = central narrative box',
        va='center', fontsize=7.1, color='#111111', zorder=13)

# Supporting box swatch
ax.add_patch(FancyBboxPatch(
    (leg_x + 2.80, leg_y - 0.10), 0.55, 0.14,
    boxstyle='round,pad=0.02',
    facecolor='white', edgecolor='#C8C8C8',
    linewidth=0.7, zorder=12))
ax.text(leg_x + 3.43, leg_y - 0.03,
        'Thin border = supporting analysis',
        va='center', fontsize=7.1, color='#111111', zorder=13)

# ── Save ─────────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), 'analyses_overview.pdf')
plt.savefig(out, bbox_inches='tight', dpi=150, facecolor='white')
print(f'Saved: {out}')

# Also save PNG for quick preview
out_png = out.replace('.pdf', '.png')
plt.savefig(out_png, bbox_inches='tight', dpi=120, facecolor='white')
print(f'Saved: {out_png}')
plt.close()
