"""Compare genome-wide KO content between ORR isolates and lab reference strains.

ORR = Oak Ridge Reservation (ORFRC) contaminated-site isolates, identified
      from strain names with FW*/GW*/MT* prefixes in enigma_fitprivate.

Queries full KO annotation per organism from enigma_fitprivate (all KOs, not
filtered to metal conditions), then overlays our curated 730 metal-associated
KO list to compare accessory metal gene enrichment.

Phylogenetic ordering uses NCBI/GTDB taxonomy from the organism table (manual
ordering within broad groups; formal GTDB-Tk would require genome assemblies).

Questions answered
------------------
1. Are ORR isolates enriched for curated metal KOs (fraction of genome)?
2. Which functional categories (Resistance, Transport, Cofactor…) drive enrichment?
3. Are metal KOs that are absent from Keio (ORR-specific) enriched in resistance genes?
4. Phylogenetically: which clades are most enriched?

Outputs
-------
data/enigma_genome_ko_content.csv        per-organism genome KO summary
data/enigma_orr_specific_kos.csv         KOs in ≥2 ORR isolates but absent from Keio
figures/fig_enigma_phylo_enrichment.pdf  phylo-ordered bar chart
figures/fig_enigma_metal_fraction.pdf    scatter genome size vs metal fraction
figures/fig_enigma_orr_heatmap.pdf       organism × ORR-specific KO heatmap
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path("/home/hmacgregor/BERIL-research-observatory")
PROJ = ROOT / "projects/per_ko_metal_associations"
DATA = PROJ / "data"
FIGS = PROJ / "figures"
FIGS.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "tools"))
from figure_style import apply_style, save, PALETTE, METAL_COLORS, FIGW, ROW_H
apply_style()

# ── Spark setup ──────────────────────────────────────────────────────────────

try:
    from berdl_notebook_utils.setup_spark_session import get_spark_session
    spark = get_spark_session()
    print("Spark connected via get_spark_session()")
except ImportError:
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    print("Spark connected via SparkSession.builder")

# ── 1. Organism metadata from both DBs ───────────────────────────────────────

e_org = spark.sql("SELECT * FROM enigma_fitprivate.organism").toPandas()
e_org["source_db"] = "enigma_fitprivate"

# ORR classification: FW/GW/MT strain prefixes = contaminated ORFRC wells
# Exceptions: KT2440 (Putida lab strain), VPI-5482 (Btheta gut), BW25113 (Keio)
NON_ORR_STRAINS = {"BW25113", "VPI-5482", "KT2440"}
def classify_orr(row):
    if row["strain"] in NON_ORR_STRAINS:
        return "lab/reference"
    strain = str(row["strain"])
    if (strain.startswith(("FW", "GW", "MT", "EB")) or
        any(s in strain for s in ("FHT", "N1B", "N2E", "N2C", "GW456", "GW460", "GW821", "GW822", "GW823"))):
        return "ORR"
    return "other"

e_org["site"] = e_org.apply(classify_orr, axis=1)

print(f"\nENIGMA organisms: {len(e_org)} total")
print(e_org[["orgId", "genus", "species", "strain", "division", "site"]].to_string())

# ── 2. Full genome KO content query (enigma_fitprivate, no metal filter) ─────

print("\nQuerying full genome KO content from enigma_fitprivate …")
genome_ko = spark.sql("""
    SELECT
        bk.orgId,
        km.kgroup       AS ko_id,
        COUNT(DISTINCT bk.locusId) AS n_genes
    FROM enigma_fitprivate.besthitkegg bk
    JOIN enigma_fitprivate.keggmember  km
         ON bk.keggOrg = km.keggOrg AND bk.keggId = km.keggId
    GROUP BY bk.orgId, km.kgroup
""").toPandas()
genome_ko.attrs = {}
print(f"  Rows: {len(genome_ko):,}  (org × KO pairs)")

# ── 3. Load curated metal KO list ────────────────────────────────────────────

curated = pd.read_csv(DATA / "curated_mrg_ko_ids_v2.csv" if (DATA / "curated_mrg_ko_ids_v2.csv").exists()
                      else ROOT / "projects/comprehensive_metal_ecology/data/curated_mrg_ko_ids_v2.csv")
curated.columns = [c.strip() for c in curated.columns]
# normalise KO column name
if "KO" in curated.columns:
    curated = curated.rename(columns={"KO": "ko_id"})
elif "ko_id" not in curated.columns:
    curated = curated.rename(columns={curated.columns[0]: "ko_id"})

curated_kos = set(curated["ko_id"].dropna().unique())
print(f"\nCurated metal KOs: {len(curated_kos)}")

# Load summary for category info
summary = pd.read_csv(DATA / "all_ko_fitness_summary.csv")
ko_meta = summary[["ko_id", "category", "is_resistance", "is_transport", "is_cofactor",
                   "gene_name", "metals", "in_core94"]].drop_duplicates("ko_id")

# ── 4. Per-organism genome content statistics ─────────────────────────────────

org_stats = []
for org in genome_ko["orgId"].unique():
    sub = genome_ko[genome_ko["orgId"] == org]
    total_kos = sub["ko_id"].nunique()
    metal_kos = sub[sub["ko_id"].isin(curated_kos)]["ko_id"].nunique()

    # By category (only KOs in our meta)
    metal_sub = sub[sub["ko_id"].isin(curated_kos)].merge(ko_meta, on="ko_id", how="left")
    n_resist = metal_sub["is_resistance"].fillna(False).sum()
    n_trans  = metal_sub["is_transport"].fillna(False).sum()
    n_cofac  = metal_sub["is_cofactor"].fillna(False).sum()
    n_core94 = metal_sub["in_core94"].fillna(False).sum()

    org_stats.append({
        "orgId":          org,
        "total_kos":      total_kos,
        "metal_kos":      metal_kos,
        "metal_fraction": metal_kos / total_kos if total_kos > 0 else 0,
        "n_resistance":   n_resist,
        "n_transport":    n_trans,
        "n_cofactor":     n_cofac,
        "n_core94":       n_core94,
        "resist_frac":    n_resist / total_kos if total_kos > 0 else 0,
        "transport_frac": n_trans  / total_kos if total_kos > 0 else 0,
    })

org_df = pd.DataFrame(org_stats)
org_df = org_df.merge(e_org[["orgId", "genus", "species", "strain", "division", "site",
                               "taxonomyId"]], on="orgId", how="left")

org_df.to_csv(DATA / "enigma_genome_ko_content.csv", index=False)
print(f"\nSaved {DATA / 'enigma_genome_ko_content.csv'}")
print(org_df[["orgId","genus","site","total_kos","metal_kos","metal_fraction","n_resistance","n_transport"]].to_string())

# ── 5. Statistical test: ORR vs. non-ORR metal KO fraction ───────────────────

orr_frac = org_df[org_df["site"] == "ORR"]["metal_fraction"].values
lab_frac = org_df[org_df["site"] == "lab/reference"]["metal_fraction"].values

mw_stat, mw_p = stats.mannwhitneyu(orr_frac, lab_frac, alternative="greater")
print(f"\n=== ORR vs. lab metal_fraction Mann-Whitney U ===")
print(f"ORR   (n={len(orr_frac)}): {orr_frac.mean():.4f} ± {orr_frac.std():.4f}")
print(f"Lab   (n={len(lab_frac)}): {lab_frac.mean():.4f} ± {lab_frac.std():.4f}")
print(f"U = {mw_stat:.0f}, p = {mw_p:.4g} (one-sided: ORR > lab)")

# Resistance fraction
orr_rf = org_df[org_df["site"] == "ORR"]["resist_frac"].values
lab_rf = org_df[org_df["site"] == "lab/reference"]["resist_frac"].values
mw_r, mw_rp = stats.mannwhitneyu(orr_rf, lab_rf, alternative="greater")
print(f"\nResistance KO fraction: ORR {orr_rf.mean():.4f} vs. lab {lab_rf.mean():.4f}, p={mw_rp:.4g}")

# Transport fraction
orr_tf = org_df[org_df["site"] == "ORR"]["transport_frac"].values
lab_tf = org_df[org_df["site"] == "lab/reference"]["transport_frac"].values
mw_t, mw_tp = stats.mannwhitneyu(orr_tf, lab_tf, alternative="greater")
print(f"Transport  KO fraction: ORR {orr_tf.mean():.4f} vs. lab {lab_tf.mean():.4f}, p={mw_tp:.4g}")

# ── 6. ORR-specific curated KOs (present in ≥2 ORR, absent from Keio) ────────

# Build KO × organism presence matrix
pres = genome_ko.copy()
pres["present"] = 1
piv = pres.pivot_table(index="ko_id", columns="orgId", values="present", fill_value=0)

orr_orgs = org_df[org_df["site"] == "ORR"]["orgId"].tolist()
lab_orgs = org_df[org_df["site"] == "lab/reference"]["orgId"].tolist()

# Filter to curated KOs
piv_curated = piv[piv.index.isin(curated_kos)].copy()

# ORR-specific: in ≥2 ORR isolates AND absent from Keio
if "Keio" in piv_curated.columns:
    keio_absent = piv_curated["Keio"] == 0
else:
    keio_absent = pd.Series(True, index=piv_curated.index)

orr_cols_present = [c for c in orr_orgs if c in piv_curated.columns]
orr_count = piv_curated[orr_cols_present].sum(axis=1)
orr_specific_mask = (orr_count >= 2) & keio_absent

orr_specific = piv_curated[orr_specific_mask].copy()
orr_specific_kos = orr_specific.index.tolist()
print(f"\nORR-specific curated KOs (≥2 ORR, absent Keio): {len(orr_specific_kos)}")

orr_specific_df = (
    orr_specific.reset_index()
    .merge(ko_meta, on="ko_id", how="left")
)
orr_specific_df["orr_count"] = orr_count[orr_specific_mask].values
orr_specific_df.to_csv(DATA / "enigma_orr_specific_kos.csv", index=False)
print(f"Saved {DATA / 'enigma_orr_specific_kos.csv'}")

# Category breakdown of ORR-specific KOs
print("\nORR-specific KO categories:")
if "category" in orr_specific_df.columns:
    print(orr_specific_df["category"].value_counts())

# Fisher's exact: ORR-specific resistance KOs vs. background curated KOs
orr_resist = int(orr_specific_df["is_resistance"].fillna(False).sum())
orr_other  = len(orr_specific_df) - orr_resist
bg_resist  = int(ko_meta["is_resistance"].fillna(False).sum())
bg_other   = len(ko_meta) - bg_resist
fe_tab = [[orr_resist, orr_other], [bg_resist - orr_resist, bg_other - orr_other]]
fe_or, fe_p = stats.fisher_exact(fe_tab, alternative="greater")
print(f"\nFisher's exact (ORR-specific vs. all curated): Resistance OR={fe_or:.2f}, p={fe_p:.4g}")

# ── 7. Figure 1: Phylo-ordered bar chart ─────────────────────────────────────

# Manual GTDB-style phylogenetic order for enigma_fitprivate organisms
# Based on division + order + family from NCBI taxonomy
PHYLO_ORDER = [
    # Bacteroidetes
    "Btheta",           # Bacteroides (gut)
    "Pedo557",          # Pedobacter (ORR)
    # Betaproteobacteria
    "Phaga5",           # Hydrogenophaga (ORR, Comamonadaceae)
    "acidovorax_3H11",  # Acidovorax (ORR, Comamonadaceae)
    "Cup4G11",          # Cupriavidus (ORR, Burkholderiaceae)
    "Castellaniella_MT123",          # Castellaniella (ORR, Alcaligenaceae)
    "Collimonas_GW821-FHT01A05",    # Collimonas (ORR, Oxalobacteraceae)
    "Janthino_FHT05C05",            # Janthinobacterium (ORR, Oxalobacteraceae)
    "Janthinobacterium_agari",      # Janthinobacterium (ORR, Oxalobacteraceae)
    # Alphaproteobacteria
    "Brev2",            # Brevundimonas (ORR, Caulobacteraceae)
    # Gammaproteobacteria
    "Rhodanobacter_MT42",   # Xanthomonadales (ORR)
    "rhodanobacter_10B01",  # Xanthomonadales (ORR)
    "rhodanobacter_R12",    # Xanthomonadales (ORR)
    "rhodanobacter_T8",     # Xanthomonadales (ORR)
    "pseudo13_GW456_L13",   # Pseudomonadales (ORR)
    "pseudo1_N1B4",         # Pseudomonadales (ORR)
    "pseudo3_N2E3",         # Pseudomonadales (ORR)
    "pseudo5_N2C3_1",       # Pseudomonadales (ORR)
    "pseudo6_N2E2",         # Pseudomonadales (ORR)
    "PseudoFW215-L2",       # Pseudomonadales (ORR)
    "Putida",               # Pseudomonadales (lab reference)
    "MT049",    # Enterobacterales Serratia (ORR)
    "MT058",    # Enterobacterales Pantoea (ORR)
    "Enterobacter_XG201",   # Enterobacterales (ORR?)
    "Keio",     # Enterobacterales E. coli (lab)
]

# Only keep organisms we have data for
PHYLO_ORDER = [o for o in PHYLO_ORDER if o in org_df["orgId"].values]
# Add any missing organisms at end
for o in org_df["orgId"].values:
    if o not in PHYLO_ORDER:
        PHYLO_ORDER.append(o)

plot_df = org_df.set_index("orgId").loc[PHYLO_ORDER].reset_index()

# Labels: genus + strain abbreviation
def make_label(row):
    g = row["genus"] if pd.notna(row["genus"]) else ""
    s = row["strain"] if pd.notna(row["strain"]) else ""
    abbrev = s[:12] if len(s) > 12 else s
    return f"{g} [{abbrev}]"

plot_df["label"] = plot_df.apply(make_label, axis=1)

# Colors
SITE_COLOR = {"ORR": PALETTE[1], "lab/reference": PALETTE[0], "other": PALETTE[2]}

fig, axes = plt.subplots(1, 3, figsize=(FIGW["full"], max(len(PHYLO_ORDER) * 0.28, ROW_H)),
                          sharey=True)

y_pos = range(len(plot_df))

def _bars(ax, values, label, xlim=None, color_col="site"):
    colors = [SITE_COLOR.get(s, "gray") for s in plot_df["site"]]
    bars = ax.barh(list(y_pos), values, color=colors, edgecolor="k", linewidth=0.4, height=0.7)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(plot_df["label"], fontsize=7)
    ax.set_xlabel(label, fontsize=9)
    if xlim:
        ax.set_xlim(0, xlim)
    ax.axvline(0, color="k", lw=0.5)
    return bars

_bars(axes[0], plot_df["total_kos"],      "Total annotated KOs")
_bars(axes[1], plot_df["metal_kos"],      "Curated metal KOs")
_bars(axes[2], plot_df["metal_fraction"], "Metal KO fraction")
axes[2].set_xlim(0, 0.06)

# Add division background bands
division_groups = {
    "Bacteroidetes":        ["Btheta", "Pedo557"],
    "Beta-\nProteobacteria": ["Phaga5", "acidovorax_3H11", "Cup4G11", "Castellaniella_MT123",
                               "Collimonas_GW821-FHT01A05", "Janthino_FHT05C05", "Janthinobacterium_agari"],
    "Alpha-\nProteobacteria": ["Brev2"],
    "Gamma-\nProteobacteria": ["Rhodanobacter_MT42", "rhodanobacter_10B01", "rhodanobacter_R12",
                                "rhodanobacter_T8", "pseudo13_GW456_L13", "pseudo1_N1B4",
                                "pseudo3_N2E3", "pseudo5_N2C3_1", "pseudo6_N2E2", "PseudoFW215-L2",
                                "Putida", "MT049", "MT058", "Enterobacter_XG201", "Keio"],
}
band_alpha = 0.06
band_colors = ["#e8e8f0", "#f0e8e8", "#e8f0e8", "#f0f0e8"]
org_to_idx = {o: i for i, o in enumerate(plot_df["orgId"].tolist())}
for ax in axes:
    for (div_name, members), bc in zip(division_groups.items(), band_colors):
        idxs = [org_to_idx[m] for m in members if m in org_to_idx]
        if idxs:
            lo, hi = min(idxs) - 0.45, max(idxs) + 0.45
            ax.axhspan(lo, hi, color=bc, alpha=0.5, zorder=0)

# Division labels on rightmost panel
for (div_name, members), bc in zip(division_groups.items(), band_colors):
    idxs = [org_to_idx[m] for m in members if m in org_to_idx]
    if idxs:
        mid = (min(idxs) + max(idxs)) / 2
        axes[2].annotate(div_name, xy=(1.01, mid / len(plot_df)),
                         xycoords=("axes fraction", "data"),
                         xytext=(1.02, mid / len(plot_df)),
                         fontsize=6.5, color="#444444",
                         va="center", annotation_clip=False,
                         arrowprops=dict(arrowstyle="-", lw=0.5, color="#aaaaaa"))

handles = [mpatches.Patch(facecolor=SITE_COLOR["ORR"],           edgecolor="k", lw=0.4, label="ORR isolate (contaminated site)"),
           mpatches.Patch(facecolor=SITE_COLOR["lab/reference"],  edgecolor="k", lw=0.4, label="Lab/reference strain")]
fig.legend(handles=handles, loc="upper right", fontsize=8, frameon=False,
           bbox_to_anchor=(0.98, 1.0))
fig.suptitle("ENIGMA genome KO content: ORR contaminated-site isolates vs. lab strains\n(ordered by NCBI/GTDB taxonomy)", y=1.02)
save(fig, FIGS / "fig_enigma_phylo_enrichment")
print("\nSaved fig_enigma_phylo_enrichment.pdf")

# ── 8. Figure 2: Scatter genome size vs metal fraction ────────────────────────

fig, ax = plt.subplots(figsize=(FIGW["1.5col"], ROW_H))

for _, row in org_df.iterrows():
    col = SITE_COLOR.get(row["site"], "gray")
    ax.scatter(row["total_kos"], row["metal_fraction"],
               color=col, edgecolors="k", linewidths=0.4, s=45, zorder=3)

# Label a few key organisms
for _, row in org_df.iterrows():
    if row["orgId"] in {"Keio", "Rhodanobacter_MT42", "Cup4G11", "Putida", "Castellaniella_MT123"}:
        ax.annotate(row["genus"], xy=(row["total_kos"], row["metal_fraction"]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points")

ax.set_xlabel("Total annotated KOs (genome size proxy)", fontsize=9)
ax.set_ylabel("Curated metal KO fraction", fontsize=9)
ax.set_title("Genome size vs. metal gene enrichment", fontsize=10)

handles = [mpatches.Patch(facecolor=SITE_COLOR["ORR"],          edgecolor="k", lw=0.4, label=f"ORR isolate (n={len(orr_frac)})"),
           mpatches.Patch(facecolor=SITE_COLOR["lab/reference"], edgecolor="k", lw=0.4, label=f"Lab/reference (n={len(lab_frac)})")]
ax.legend(handles=handles, fontsize=8, frameon=False)

mw_txt = f"ORR vs lab\nMW p = {mw_p:.3g}"
ax.annotate(mw_txt, xy=(0.97, 0.97), xycoords="axes fraction",
            ha="right", va="top", fontsize=8, color="#808080")

save(fig, FIGS / "fig_enigma_metal_fraction")
print("Saved fig_enigma_metal_fraction.pdf")

# ── 9. Figure 3: ORR-specific KO heatmap ─────────────────────────────────────

# Top ORR-specific KOs by presence count and functional interest
top_orr = (
    orr_specific_df
    .assign(orr_n=orr_specific_df["orr_count"])
    .sort_values(["orr_n", "is_resistance"], ascending=[False, False])
    .head(40)
)
top_ko_ids = top_orr["ko_id"].tolist()

if len(top_ko_ids) > 0:
    # Pivot matrix: organisms × KOs
    piv_top = piv_curated.loc[piv_curated.index.isin(top_ko_ids)].copy()
    # Order columns by phylo order
    col_order = [c for c in PHYLO_ORDER if c in piv_top.columns]
    piv_top = piv_top[col_order]

    # Row labels: gene_name or ko_id
    row_labels = []
    for ko in piv_top.index:
        g = ko_meta.loc[ko_meta["ko_id"] == ko, "gene_name"]
        row_labels.append(g.values[0] if len(g) > 0 and pd.notna(g.values[0]) else ko)

    # Column labels
    col_labels = []
    for o in col_order:
        row = org_df[org_df["orgId"] == o].iloc[0]
        col_labels.append(f"{row['genus']}\n[{str(row['strain'])[:8]}]")

    site_colors_col = [SITE_COLOR.get(
        org_df[org_df["orgId"] == o]["site"].values[0], "gray")
        for o in col_order]

    h = max(len(top_ko_ids) * 0.23, 3.0)
    w = max(len(col_order) * 0.32, 4.0)
    fig, ax = plt.subplots(figsize=(min(w, FIGW["full"]), min(h, ROW_H * 2.5)))

    cmap = LinearSegmentedColormap.from_list("presence", ["#f5f5f5", PALETTE[1]])
    im = ax.imshow(piv_top.values.astype(float), aspect="auto", cmap=cmap,
                   vmin=0, vmax=1, interpolation="nearest")

    ax.set_xticks(range(len(col_order)))
    ax.set_xticklabels(col_labels, rotation=60, ha="right", fontsize=6)
    ax.set_yticks(range(len(top_ko_ids)))
    ax.set_yticklabels(row_labels, fontsize=7)

    # Colour xtick labels by site
    for tick, col in zip(ax.get_xticklabels(), site_colors_col):
        tick.set_color(col if col != "#f5f5f5" else "black")

    # Category stripes for y-axis
    cat_color = {"Resistance/Detoxification": "#ffe0e0",
                 "Transport/Homeostasis":      "#e0e8ff",
                 "Metal-dependent Metabolism": "#e8ffe0",
                 "Sensing/Regulation":         "#fff0d0",
                 "Cofactor Biosynthesis":      "#f0e8ff"}
    for i, ko in enumerate(piv_top.index):
        cat = ko_meta.loc[ko_meta["ko_id"] == ko, "category"]
        c = cat.values[0] if len(cat) > 0 else "Unknown"
        stripe_c = cat_color.get(c, "#f8f8f8")
        ax.axhspan(i - 0.45, i + 0.45, color=stripe_c, alpha=0.4, zorder=0)

    ax.set_title("ORR-specific curated KOs (≥2 ORR isolates, absent from E. coli)\n"
                 "rows = KO, columns = organism, shaded = present", fontsize=10)

    save(fig, FIGS / "fig_enigma_orr_heatmap")
    print("Saved fig_enigma_orr_heatmap.pdf")

# ── 10. Summary printout ──────────────────────────────────────────────────────

print("\n=== SUMMARY ===")
print(f"ORR isolates in enigma_fitprivate: {(org_df['site']=='ORR').sum()}")
print(f"Lab/reference strains: {(org_df['site']=='lab/reference').sum()}")
print(f"\nMean metal KO fraction: ORR={orr_frac.mean():.4f}, lab={lab_frac.mean():.4f}")
print(f"Mean resist KO fraction: ORR={orr_rf.mean():.4f}, lab={lab_rf.mean():.4f}")
print(f"ORR-specific curated KOs (≥2 ORR, absent Keio): {len(orr_specific_kos)}")
print(f"  of which resistance: {orr_resist} (Fisher OR={fe_or:.1f}, p={fe_p:.3g})")
print("\nDone.")
