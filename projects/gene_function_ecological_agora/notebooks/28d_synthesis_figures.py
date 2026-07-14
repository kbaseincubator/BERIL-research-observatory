"""NB28 Stage 4 — 8 synthesis figures.

Heroes:
  H1 — Atlas Innovation Tree (per-class glyph map; tree topology approximated by phylum grouping for legibility)
  H2 — Three-Substrate Convergence Card (3 hypotheses × 3 substrates)
  H3 — Acquisition-Depth Function Spectrum (recent-to-ancient ratio per function class)

Supporting:
  S4 — PSII rank-dependence ladder (REVIEW_8 C9 response visualized)
  S5 — Hypothesis verdict card (tabular)
  S6 — Function × Environment Sankey (the user's interactions diagram)
  N7 — NB22 deliverable: atlas heatmap (clade × function-class P×P matrix)
  N8 — NB22 deliverable: four-quadrant summary at genus rank

All saved as p4_synthesis_*.png in figures/.
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

# Load substrates once
tprint("=== NB28 Stage 4 — synthesis figures ===")
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
atlas = pd.read_parquet(DATA_DIR / "p4_deep_rank_pp_atlas.parquet")
gains = pd.read_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet")
verdicts = pd.read_csv(DATA_DIR / "p4_pre_registered_verdicts.tsv", sep="\t")
quadrants = pd.read_csv(DATA_DIR / "p4_genus_rank_quadrants_tree_proxy.tsv", sep="\t")
env = pd.read_parquet(DATA_DIR / "p4d1_env_per_species.parquet")
tprint(f"  loaded substrates")

# KO categorization
ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
REG_PATHWAYS = {f"ko03{n:03d}" for n in range(0, 100)} | {f"ko0{n:04d}" for n in [2010, 2020, 2024, 2025, 2026, 2030, 2040, 2060, 2065]}
def is_metabolic(p):
    if not isinstance(p, str) or not p.startswith("ko"): return False
    try: return int(p[2:]) < 2000
    except ValueError: return False
def classify(s):
    if not isinstance(s, str) or s == "": return "unannotated"
    pwys = set(s.split(","))
    n_reg = sum(1 for p in pwys if p in REG_PATHWAYS)
    n_met = sum(1 for p in pwys if is_metabolic(p))
    if n_reg > 0 and n_met == 0: return "regulatory"
    if n_met > 0 and n_reg == 0: return "metabolic"
    if n_reg > 0 and n_met > 0: return "mixed"
    return "other"
ko_pwbr["category"] = ko_pwbr["pathway_ids"].apply(classify)
ko_to_cat = dict(zip(ko_pwbr["ko"], ko_pwbr["category"]))

# ====================================================================
# H3 — Acquisition-Depth Function Spectrum (build first, simpler)
# ====================================================================
tprint("\nH3 — Acquisition-Depth Function Spectrum")

# Per-control-class, depth_bin distribution
control_classes = ["pos_amr", "pos_crispr_cas", "pos_alm_2006_tcs",
                   "neg_ribosomal", "neg_trna_synth", "neg_rnap_core",
                   "neg_trna_synth_strict", "neg_rnap_core_strict"]
class_pretty = {
    "pos_amr": "AMR (positive control)",
    "pos_crispr_cas": "CRISPR-Cas (positive)",
    "pos_alm_2006_tcs": "Alm 2006 TCS (positive)",
    "neg_ribosomal": "Ribosomal (housekeeping)",
    "neg_trna_synth": "tRNA synthetase (housekeeping)",
    "neg_rnap_core": "RNAP core (housekeeping)",
    "neg_trna_synth_strict": "tRNA synth (strict)",
    "neg_rnap_core_strict": "RNAP core (strict)",
}
recent_per_class = (gains[gains["control_class_m21"].isin(control_classes)]
    .groupby(["control_class_m21", "depth_bin"]).size().unstack(fill_value=0))
# Compute recent-to-ancient ratio
if "ancient" in recent_per_class.columns and "recent" in recent_per_class.columns:
    recent_per_class["ratio"] = recent_per_class["recent"] / recent_per_class["ancient"].clip(lower=1)
    recent_per_class = recent_per_class.sort_values("ratio", ascending=True)

# Plot ridge / horizontal bar
fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(recent_per_class))
recent_per_class["recent_pct"] = 100 * recent_per_class["recent"] / recent_per_class[["recent", "older_recent", "mid", "older", "ancient"]].sum(axis=1)
recent_per_class["ancient_pct"] = 100 * recent_per_class["ancient"] / recent_per_class[["recent", "older_recent", "mid", "older", "ancient"]].sum(axis=1)
ax.barh(y - 0.2, recent_per_class["recent_pct"], 0.4, label="recent", color="#2ca02c")
ax.barh(y + 0.2, recent_per_class["ancient_pct"], 0.4, label="ancient", color="#8c564b")
ax.set_yticks(y); ax.set_yticklabels([class_pretty.get(c, c) for c in recent_per_class.index])
ax.set_xlabel("% of M22 gain events at this depth")
ax.set_title("H3 — Acquisition-Depth Function Spectrum (recent vs ancient by control class)")
for i, (idx, row) in enumerate(recent_per_class.iterrows()):
    ratio = row["ratio"]
    ax.text(max(row["recent_pct"], row["ancient_pct"]) + 1, i, f"r/a = {ratio:.1f}×",
            va="center", fontsize=9)
ax.legend(loc="lower right"); ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_H3_acquisition_depth_spectrum.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  H3 saved")

# ====================================================================
# H2 — Three-Substrate Convergence Card
# ====================================================================
tprint("\nH2 — Three-Substrate Convergence Card")

fig = plt.figure(figsize=(15, 9))
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.3)

hypotheses = [
    ("Mycobacteriaceae × mycolic", 0.31, 7.88, "host-pathogen", -45,
     {"Aerobic": 0.894, "Gram+": 0.994, "Non-motile": 0.995, "Catalase+": 1.00}),
    ("Cyanobacteriia × PSII (class)", 1.50, 2.77, "photic aquatic", -52,
     {"Marine cluster 0": 0.356, "Photic aquatic biome": 0.638, "Other": 0.006}),
    ("Bacteroidota × PUL", 0.21, 1.40, "gut/rumen", -35,
     {"Saccharolytic (maltose)": 230/291, "Saccharolytic (raffinose)": 155/284, "Anaerobe": 0.332}),
]

for i, (label, atlas_d, biome_fold, biome_name, biome_logp, phenotype) in enumerate(hypotheses):
    # Atlas effect size — bar with CI
    ax1 = fig.add_subplot(gs[i, 0])
    ax1.barh([0], [atlas_d], color="#1f77b4", alpha=0.8)
    ax1.axvline(0, color="black", lw=0.5)
    ax1.axvline(0.3, color="red", ls="--", lw=0.5, label="d=0.3")
    ax1.set_xlim(-0.5, 2.0)
    ax1.set_yticks([0]); ax1.set_yticklabels(["d (atlas)"])
    ax1.set_xlabel("Cohen's d (atlas effect size)")
    ax1.set_title(f"{label}\nAtlas: d = {atlas_d:+.2f}")
    if i == 0: ax1.legend(loc="lower right", fontsize=8)
    ax1.grid(axis="x", alpha=0.3)

    # Ecology grounding
    ax2 = fig.add_subplot(gs[i, 1])
    ax2.barh([0], [biome_fold], color="#2ca02c", alpha=0.8)
    ax2.axvline(1, color="red", ls="--", lw=0.5, label="no enrichment (1×)")
    ax2.set_xlim(0, max(biome_fold * 1.2, 2))
    ax2.set_yticks([0]); ax2.set_yticklabels([f"{biome_name}"])
    ax2.set_xlabel("Fold enrichment vs atlas")
    ax2.set_title(f"Ecology: {biome_fold:.2f}× p<10^{biome_logp}")
    if i == 0: ax2.legend(loc="lower right", fontsize=8)
    ax2.grid(axis="x", alpha=0.3)

    # Phenotype anchor
    ax3 = fig.add_subplot(gs[i, 2])
    pheno_keys = list(phenotype.keys()); pheno_vals = list(phenotype.values())
    ax3.barh(np.arange(len(pheno_keys)), [v*100 for v in pheno_vals], color="#9467bd", alpha=0.8)
    ax3.set_yticks(np.arange(len(pheno_keys))); ax3.set_yticklabels(pheno_keys, fontsize=9)
    ax3.set_xlabel("% with phenotype")
    ax3.set_xlim(0, 100)
    ax3.set_title(f"Phenotype anchor (BacDive)")
    ax3.grid(axis="x", alpha=0.3)

fig.suptitle("H2 — Three-Substrate Convergence: Atlas + Ecology + Phenotype",
             fontsize=14, y=1.0)
plt.savefig(FIG_DIR / "p4_synthesis_H2_three_substrate_convergence.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  H2 saved")

# ====================================================================
# S4 — PSII rank-dependence ladder
# ====================================================================
tprint("\nS4 — PSII rank-dependence ladder")
psii_ranks = [
    ("genus", 2350, 0.0776, "STABLE"),
    ("family", 705, 0.1994, "STABLE"),
    ("order", 301, 0.1906, "STABLE"),
    ("class", 21, 1.496, "INNOVATOR-EXCHANGE"),
    ("phylum", 21, 1.6033, "INNOVATOR-ISOLATED"),
]
fig, ax = plt.subplots(figsize=(10, 5))
ranks = [r[0] for r in psii_ranks]; ds = [r[2] for r in psii_ranks]
ns = [r[1] for r in psii_ranks]; verds = [r[3] for r in psii_ranks]
colors = {"STABLE": "lightgray", "INNOVATOR-EXCHANGE": "#1f77b4", "INNOVATOR-ISOLATED": "#d62728"}
bar_colors = [colors[v] for v in verds]
bars = ax.bar(ranks, ds, color=bar_colors, alpha=0.85)
for i, (rank, n, d, verd) in enumerate(psii_ranks):
    ax.text(i, d + 0.05, f"d = {d:.2f}\nn = {n}\n{verd}", ha="center", fontsize=9)
ax.axhline(0.3, color="red", ls="--", lw=0.5, label="d=0.3 (project threshold)")
ax.set_xlabel("Taxonomic rank")
ax.set_ylabel("Producer Cohen's d (PSII vs reference)")
ax.set_title("S4 — Cyanobacteriia × PSII rank-dependence (REVIEW_8 C9 response)\n"
             "Class rank is biologically appropriate per Cardona 2018: PSII is class-defining innovation")
ax.set_ylim(0, 2.0)
ax.legend(); ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_S4_psii_rank_dependence.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  S4 saved")

# ====================================================================
# S5 — Hypothesis Verdict Card (tabular figure)
# ====================================================================
tprint("\nS5 — Hypothesis Verdict Card")

verdict_summary = pd.DataFrame([
    {"H#": "H1", "Hypothesis": "Bacteroidota PUL Innovator-Exchange",
     "Atlas": "⚠ d=0.15 (small)", "Ecology": "✓ 1.40× gut/rumen", "Phenotype": "✓ saccharolytic", "MGE": "✓ 0% (ICE-mediated)", "Disposition": "Qualified pass"},
    {"H#": "H2", "Hypothesis": "Mycobacteriaceae mycolic-acid Innovator-Isolated",
     "Atlas": "✓ d=0.31", "Ecology": "✓ 7.88× host-pathogen", "Phenotype": "✓ aerobic-rod-catalase", "MGE": "✓ 0.57% (chromosomal)", "Disposition": "✅ SUPPORTED"},
    {"H#": "H3", "Hypothesis": "Cyanobacteriia PSII Innovator-Exchange (class)",
     "Atlas": "✓ d=1.50 (n=21)", "Ecology": "✓ 2.77× photic aquatic", "Phenotype": "⚠ thin (n=4 BacDive)", "MGE": "✓ 0% (chromosomal)", "Disposition": "✅ SUPPORTED at class"},
    {"H#": "H4", "Hypothesis": "Alm 2006 r ≈ 0.74 reproduction",
     "Atlas": "✗ r=0.10–0.29", "Ecology": "n/a", "Phenotype": "n/a", "MGE": "n/a", "Disposition": "✗ NOT REPRODUCED"},
    {"H#": "B", "Hypothesis": "NB11 Regulatory < Metabolic d≥0.3 (reframed)",
     "Atlas": "→ d=−0.21 (small)", "Ecology": "n/a (atlas-wide)", "Phenotype": "n/a", "MGE": "✓ 4.13% reg vs 0.37% met", "Disposition": "→ REFRAMED (Jain 1999)"},
])
fig, ax = plt.subplots(figsize=(16, 4.5))
ax.axis("off")
tab = ax.table(cellText=verdict_summary.values, colLabels=verdict_summary.columns,
               cellLoc="left", loc="center", colWidths=[0.04, 0.27, 0.13, 0.16, 0.14, 0.14, 0.20])
tab.auto_set_font_size(False); tab.set_fontsize(9)
tab.scale(1, 1.7)
# Color-code disposition cells
for i, r in enumerate(verdict_summary["Disposition"]):
    cell = tab[i+1, 6]
    if "SUPPORTED" in r: cell.set_facecolor("#c8e6c9")
    elif "Qualified" in r: cell.set_facecolor("#fff9c4")
    elif "REFRAMED" in r: cell.set_facecolor("#bbdefb")
    elif "NOT REPRODUCED" in r: cell.set_facecolor("#ffcdd2")
fig.suptitle("S5 — Pre-Registered Hypothesis Verdict Card", fontsize=13)
plt.savefig(FIG_DIR / "p4_synthesis_S5_hypothesis_verdict_card.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  S5 saved")

# ====================================================================
# H1 — Atlas Innovation Tree (per-phylum aggregation, glyph map; tree topology approximated)
# ====================================================================
tprint("\nH1 — Atlas Innovation Tree (per-phylum glyph map)")

# Per-phylum: mean producer_z (innovation), mean recent fraction, dominant biome, n_species
top_phyla = species["phylum"].value_counts().head(20).index.tolist()
phylum_stats = []
for phy in top_phyla:
    sp_phy = species[species["phylum"] == phy]
    n_sp = len(sp_phy)
    # innovation: mean producer_z at phylum rank from atlas
    phy_atlas = atlas[(atlas["rank"] == "phylum") & (atlas["clade_id"] == phy)]
    mean_prod = phy_atlas["producer_z"].mean() if len(phy_atlas) else np.nan
    # recent-acquisition fraction at phylum rank
    phy_gains = gains[(gains["recipient_phylum"] == phy)]
    n_gains = len(phy_gains)
    recent_frac = (phy_gains["depth_bin"] == "recent").mean() if n_gains else np.nan
    # dominant biome from env
    env_phy = env[env["phylum"] == phy]
    if len(env_phy) > 0:
        # Simple biome from blob
        def get_biome(row):
            cols = ["mgnify_biomes", "env_broad_scale", "env_local_scale", "isolation_source"]
            blob = " ".join(str(row.get(c, "")).lower() for c in cols if pd.notna(row.get(c)))
            if any(t in blob for t in ["marine", "ocean", "sea"]): return "marine"
            if any(t in blob for t in ["gut", "rumen", "feces", "intestin"]): return "gut"
            if any(t in blob for t in ["soil", "rhizosphere", "sediment"]): return "soil"
            if any(t in blob for t in ["lung", "sputum", "tuberc", "human-skin"]): return "host-pathogen"
            if any(t in blob for t in ["lake", "freshwater", "river"]): return "freshwater"
            return "other"
        env_phy = env_phy.copy()
        env_phy["biome"] = env_phy.apply(get_biome, axis=1)
        dom_biome = env_phy["biome"].value_counts().index[0] if len(env_phy) else "unknown"
    else:
        dom_biome = "unknown"
    phylum_stats.append({"phylum": phy, "n_species": n_sp, "mean_producer_z": mean_prod,
                         "recent_frac": recent_frac, "n_gains": n_gains, "dominant_biome": dom_biome})

phy_df = pd.DataFrame(phylum_stats)
biome_colors = {"marine": "#1f77b4", "gut": "#8c564b", "soil": "#9467bd",
                "host-pathogen": "#e377c2", "freshwater": "#17becf",
                "other": "lightgray", "unknown": "lightgray"}
phy_df["color"] = phy_df["dominant_biome"].map(biome_colors).fillna("lightgray")

# Highlight the 3 confirmed clades' phyla
highlight = {"p__Actinomycetota": "Mycobacteriaceae", "p__Cyanobacteriota": "Cyanobacteriia (PSII)",
             "p__Bacteroidota": "Bacteroidota (PUL)"}

fig, ax = plt.subplots(figsize=(12, 8))
phy_df = phy_df.sort_values("recent_frac", ascending=True)
y = np.arange(len(phy_df))
sizes = phy_df["n_species"].apply(lambda n: max(20, np.log10(max(n, 1)) * 100))
sc = ax.scatter(phy_df["recent_frac"], y, s=sizes, c=phy_df["color"],
                edgecolor="black", linewidth=0.5, alpha=0.85)
for i, (_, row) in enumerate(phy_df.iterrows()):
    label = row["phylum"].replace("p__", "")
    if row["phylum"] in highlight:
        label = f"{label} ★ {highlight[row['phylum']]}"
        ax.text(row["recent_frac"] + 0.005, i, label, va="center", fontsize=9, fontweight="bold")
    else:
        ax.text(row["recent_frac"] + 0.005, i, label, va="center", fontsize=8)
ax.set_yticks([])
ax.set_xlabel("Recent acquisition fraction (M22 recent gains / total gains)")
ax.set_title("H1 — Atlas Innovation Tree (top 20 phyla, point size = log species count)\n"
             "Color = dominant biome; ★ marks confirmed-hypothesis-bearing phyla")
# Legend for biomes
from matplotlib.lines import Line2D
legend_items = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=10, label=k)
                for k, c in biome_colors.items() if k != "unknown"]
ax.legend(handles=legend_items, loc="lower right", fontsize=9, title="Dominant biome")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_H1_innovation_tree.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  H1 saved")

# ====================================================================
# S6 — Function × Environment Sankey-like flow diagram
# ====================================================================
tprint("\nS6 — Function × Environment flow (parallel-coordinates style; Sankey replacement)")

# For each gain event: ko_category × dominant_phylum × dominant_biome
# Sample: top categories × top phyla × top biomes
gains_with_cat = gains[gains["depth_bin"] == "recent"].copy()
gains_with_cat["category"] = gains_with_cat["ko"].map(ko_to_cat).fillna("unannotated")

# Aggregate: (category × phylum × dominant_biome)
# Need to map gains to biome via species → genus → phylum → env
species_biome_map = {}
env_phy = env.copy()
def get_biome(row):
    cols = ["mgnify_biomes", "env_broad_scale", "env_local_scale", "isolation_source"]
    blob = " ".join(str(row.get(c, "")).lower() for c in cols if pd.notna(row.get(c)))
    if any(t in blob for t in ["marine", "ocean", "sea"]): return "marine"
    if any(t in blob for t in ["gut", "rumen", "feces", "intestin"]): return "gut"
    if any(t in blob for t in ["soil", "rhizosphere", "sediment"]): return "soil"
    if any(t in blob for t in ["lung", "sputum", "tuberc", "human-skin"]): return "host-pathogen"
    if any(t in blob for t in ["lake", "freshwater", "river"]): return "freshwater"
    return "other"
env_phy["biome"] = env_phy.apply(get_biome, axis=1)
phylum_dom_biome = env_phy.groupby("phylum")["biome"].agg(lambda x: x.value_counts().index[0]).to_dict()

gains_with_cat["dominant_biome"] = gains_with_cat["recipient_phylum"].map(phylum_dom_biome)
flow_df = (gains_with_cat[gains_with_cat["recipient_phylum"].notna()]
    .groupby(["category", "recipient_phylum", "dominant_biome"])
    .size().reset_index(name="n_gains"))
# Restrict to top 6 phyla for legibility
top_6_phyla = species["phylum"].value_counts().head(6).index.tolist()
flow_df = flow_df[flow_df["recipient_phylum"].isin(top_6_phyla)]

# Plot as parallel coordinates / 3-column flow
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 3)
categories = ["regulatory", "metabolic", "mixed", "other", "unannotated"]
biomes = ["marine", "gut", "soil", "host-pathogen", "freshwater", "other"]
phyla = top_6_phyla

# y positions
def pos(items): return {it: 0.9 - i*0.15 for i, it in enumerate(items)}
cat_y = pos(categories); phy_y = pos(phyla); biome_y = pos(biomes)

# Draw nodes
for cat in categories:
    ax.scatter([0], [cat_y[cat]], s=400, c="#d62728", zorder=3)
    ax.text(-0.05, cat_y[cat], cat, ha="right", va="center", fontsize=10, fontweight="bold")
for phy in phyla:
    ax.scatter([1.5], [phy_y[phy]], s=400, c="#9467bd", zorder=3)
    ax.text(1.5, phy_y[phy] - 0.04, phy.replace("p__", ""), ha="center", va="top", fontsize=9, fontweight="bold")
for biome in biomes:
    ax.scatter([3], [biome_y[biome]], s=400, c=biome_colors.get(biome, "gray"), zorder=3)
    ax.text(3.05, biome_y[biome], biome, ha="left", va="center", fontsize=10, fontweight="bold")

# Draw flows
max_flow = flow_df["n_gains"].max()
for _, row in flow_df.iterrows():
    cat = row["category"]; phy = row["recipient_phylum"]; biome = row["dominant_biome"]
    if cat not in cat_y or phy not in phy_y or biome not in biome_y: continue
    width = 0.5 + 6 * row["n_gains"] / max_flow
    alpha = 0.15 + 0.7 * row["n_gains"] / max_flow
    color = biome_colors.get(biome, "gray")
    # Two segments: cat→phy, phy→biome
    ax.plot([0, 1.5], [cat_y[cat], phy_y[phy]], color="gray", alpha=alpha, lw=width, zorder=1)
    ax.plot([1.5, 3], [phy_y[phy], biome_y[biome]], color=color, alpha=alpha, lw=width, zorder=2)

ax.set_ylim(-0.05, 1.05)
ax.set_xticks([0, 1.5, 3]); ax.set_xticklabels(["KO category", "Recipient phylum", "Dominant biome"], fontsize=11)
ax.set_yticks([])
ax.set_title("S6 — Function × Phylum × Environment flow (recent gain events)\n"
             "Line width ∝ event count; color = destination biome", fontsize=12)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_S6_function_env_flow.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  S6 saved")

# ====================================================================
# N7 — Atlas heatmap (clade × function-class P×P matrix)
# ====================================================================
tprint("\nN7 — Atlas heatmap")

# Top 30 phyla × control_class P×P category matrix at family rank
class_subset = ["pos_amr", "pos_crispr_cas", "pos_alm_2006_tcs",
                "neg_ribosomal", "neg_trna_synth_strict", "neg_rnap_core_strict"]
fam_atlas = atlas[(atlas["rank"] == "family") & (atlas["control_class"].isin(class_subset))]
# Map family → phylum
fam_to_phylum = species[["family", "phylum"]].drop_duplicates().dropna().set_index("family")["phylum"].to_dict()
fam_atlas = fam_atlas.copy()
fam_atlas["phylum"] = fam_atlas["clade_id"].map(fam_to_phylum)
fam_atlas = fam_atlas.dropna(subset=["phylum"])
top_phyla_n7 = fam_atlas["phylum"].value_counts().head(20).index.tolist()
fam_atlas = fam_atlas[fam_atlas["phylum"].isin(top_phyla_n7)]

# Per (phylum × control_class), fraction of (family × KO) tuples that are Innovator-* (positive)
piv = fam_atlas.copy()
piv["is_innovator"] = piv["pp_category"].isin(["Innovator-Isolated", "Innovator-Exchange"]).astype(int)
piv["is_sink_broker"] = piv["pp_category"].isin(["Sink-Broker-Exchange"]).astype(int)
mat_inn = (piv.groupby(["phylum", "control_class"])["is_innovator"].mean().unstack().fillna(0) * 100)
mat_inn = mat_inn.reindex(top_phyla_n7).reindex(columns=class_subset).fillna(0)

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(mat_inn.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=mat_inn.values.max())
ax.set_xticks(range(len(class_subset)))
ax.set_xticklabels([class_pretty.get(c, c) for c in class_subset], rotation=30, ha="right", fontsize=9)
ax.set_yticks(range(len(top_phyla_n7)))
ax.set_yticklabels([p.replace("p__", "") for p in top_phyla_n7], fontsize=9)
ax.set_title("N7 — Atlas heatmap: % Innovator-* tuples by (phylum × control class) at family rank")
for i in range(len(top_phyla_n7)):
    for j in range(len(class_subset)):
        v = mat_inn.values[i, j]
        if v > 0.5:
            ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                    color="white" if v > mat_inn.values.max() * 0.5 else "black", fontsize=7)
plt.colorbar(im, ax=ax, label="% Innovator-* tuples")
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_N7_atlas_heatmap.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  N7 saved")

# ====================================================================
# N8 — Four-quadrant summary at genus rank (tree-proxy)
# ====================================================================
tprint("\nN8 — Four-quadrant summary at genus rank")

# Filter quadrants to high+medium confidence and show distribution per phylum
quadrants_with_phylum = quadrants.copy()
genus_to_phylum = species[["genus", "phylum"]].drop_duplicates().dropna().set_index("genus")["phylum"].to_dict()
quadrants_with_phylum["phylum"] = quadrants_with_phylum["genus"].map(genus_to_phylum)
quadrants_with_phylum = quadrants_with_phylum.dropna(subset=["phylum"])
solid = quadrants_with_phylum[quadrants_with_phylum["confidence"].isin(["high", "medium"])]
top_8_phyla = solid["phylum"].value_counts().head(8).index.tolist()
solid_top = solid[solid["phylum"].isin(top_8_phyla)]

# Per phylum: count per quadrant
quadrant_order = ["Open-Innovator", "Broker", "Sink", "Closed-Stable"]
phylum_quadrants = solid_top.groupby(["phylum", "quadrant_proxy"]).size().unstack(fill_value=0).reindex(top_8_phyla)
phylum_quadrants = phylum_quadrants.reindex(columns=quadrant_order, fill_value=0)
phylum_quadrants_pct = phylum_quadrants.div(phylum_quadrants.sum(axis=1), axis=0) * 100

fig, axes = plt.subplots(1, 2, figsize=(15, 7))
# Panel A: stacked bar of percent
ax = axes[0]
quadrant_colors = {"Open-Innovator": "#2ca02c", "Broker": "#1f77b4",
                   "Sink": "#ff7f0e", "Closed-Stable": "#7f7f7f"}
bottom = np.zeros(len(top_8_phyla))
for q in quadrant_order:
    ax.barh(np.arange(len(top_8_phyla)), phylum_quadrants_pct[q].values,
            left=bottom, label=q, color=quadrant_colors[q])
    bottom += phylum_quadrants_pct[q].values
ax.set_yticks(np.arange(len(top_8_phyla)))
ax.set_yticklabels([p.replace("p__", "") for p in top_8_phyla], fontsize=10)
ax.set_xlabel("% of (genus × KO) tuples (high+medium confidence)")
ax.set_title("N8 — Genus-rank quadrant proxy distribution (top 8 phyla)")
ax.legend(loc="lower right", fontsize=9); ax.grid(axis="x", alpha=0.3)

# Panel B: highlight 3 confirmed clades' quadrant distributions
ax = axes[1]
hyp_clades = {
    "Mycobacteriaceae (family)": species[species["family"] == "f__Mycobacteriaceae"]["genus"].dropna().unique(),
    "Cyanobacteriia (class)": species[species["class"] == "c__Cyanobacteriia"]["genus"].dropna().unique(),
    "Bacteroidota (phylum)": species[species["phylum"] == "p__Bacteroidota"]["genus"].dropna().unique(),
}
hyp_data = {}
for label, gs in hyp_clades.items():
    sub = solid[solid["genus"].isin(gs)]
    counts = sub["quadrant_proxy"].value_counts().reindex(quadrant_order, fill_value=0)
    hyp_data[label] = (counts / counts.sum() * 100) if counts.sum() > 0 else counts
hyp_df = pd.DataFrame(hyp_data).T

bottom = np.zeros(len(hyp_df))
for q in quadrant_order:
    ax.barh(np.arange(len(hyp_df)), hyp_df[q].values, left=bottom, label=q, color=quadrant_colors[q])
    bottom += hyp_df[q].values
ax.set_yticks(np.arange(len(hyp_df))); ax.set_yticklabels(hyp_df.index, fontsize=10)
ax.set_xlabel("% of (genus × candidate KO) tuples")
ax.set_title("Confirmed-hypothesis clades — quadrant proxy at genus rank")
ax.legend(loc="lower right", fontsize=9); ax.grid(axis="x", alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_N8_four_quadrant_summary.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  N8 saved")

tprint(f"\n=== Stage 4 DONE in {time.time()-t0:.1f}s ===")
tprint(f"Saved 7 figures to figures/p4_synthesis_*.png")
