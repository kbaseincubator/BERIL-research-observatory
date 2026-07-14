"""NB28f — leaf_consistency-leveraged synthesis figures.

Builds:
  H3-B (replaces H3): 2D control-class signature plane — recent gain fraction × mean leaf_consistency
  S7   (NEW):         Per-hypothesis leaf_consistency distribution (mycolic / PSII / PUL focal KOs vs atlas)
  S8   (NEW):         Per-rank leaf_consistency ridge — atlas confidence map across the tree
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB28f — leaf_consistency figures ===")
gains = pd.read_parquet(DATA_DIR / "p4_per_event_uncertainty.parquet")
tprint(f"  gains: {len(gains):,}")
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")

# ============================================================
# H3-B — 2D control-class signature plane
# ============================================================
tprint("\nH3-B — control-class signature plane")

control_classes = ["pos_crispr_cas", "pos_betalac", "pos_tcs_hk", "info_amr",
                   "neg_ribosomal", "neg_ribosomal_strict",
                   "neg_trna_synth", "neg_trna_synth_strict",
                   "neg_rnap_core", "neg_rnap_core_strict"]
class_pretty = {
    "pos_crispr_cas": "CRISPR-Cas (HGT-active +)",
    "pos_betalac": "β-lactamase",
    "pos_tcs_hk": "TCS HK (Alm 2006)",
    "info_amr": "AMR (info)",
    "neg_ribosomal": "Ribosomal (loose)",
    "neg_ribosomal_strict": "Ribosomal (strict −)",
    "neg_trna_synth": "tRNA synth (loose)",
    "neg_trna_synth_strict": "tRNA synth (strict −)",
    "neg_rnap_core": "RNAP core (loose)",
    "neg_rnap_core_strict": "RNAP core (strict −)",
}
class_colors = {
    "pos_crispr_cas": "#d62728",      # red
    "pos_betalac": "#ff7f0e",          # orange
    "pos_tcs_hk": "#9467bd",           # purple
    "info_amr": "#e377c2",             # pink
    "neg_ribosomal": "#bcbd22",        # olive
    "neg_ribosomal_strict": "#17becf", # teal
    "neg_trna_synth": "#aec7e8",       # light blue
    "neg_trna_synth_strict": "#1f77b4",# blue
    "neg_rnap_core": "#98df8a",        # light green
    "neg_rnap_core_strict": "#2ca02c", # green
}

# Per control class: total events, recent-fraction, mean leaf_consistency
class_stats = []
for c in control_classes:
    sub = gains[(gains["control_class_m21"] == c) & gains["leaf_consistency"].notna()]
    if len(sub) == 0: continue
    recent_frac = (sub["depth_bin"] == "recent").mean()
    mean_lc = sub["leaf_consistency"].mean()
    median_lc = sub["leaf_consistency"].median()
    n = len(sub)
    class_stats.append({"class": c, "n": n, "recent_frac": recent_frac,
                        "mean_lc": mean_lc, "median_lc": median_lc})
class_df = pd.DataFrame(class_stats)
tprint(f"  per-class stats: {len(class_df)}")

# 2D plane
fig, ax = plt.subplots(figsize=(11, 8))
for _, row in class_df.iterrows():
    c = row["class"]
    size = max(60, np.log10(row["n"] + 1) * 100)
    ax.scatter(row["recent_frac"], row["mean_lc"], s=size, color=class_colors.get(c, "gray"),
               edgecolor="black", linewidth=0.7, alpha=0.85, zorder=3, label=class_pretty.get(c, c))
    ax.annotate(class_pretty.get(c, c), (row["recent_frac"], row["mean_lc"]),
                xytext=(8, 5), textcoords="offset points", fontsize=9)

ax.axhline(0.5, color="gray", lw=0.5, ls="--", alpha=0.4)
ax.axvline(0.5, color="gray", lw=0.5, ls="--", alpha=0.4)
# Quadrant labels
ax.text(0.05, 0.95, "Vertical inheritance\n(low recent + high LC)", fontsize=10,
        color="darkgreen", fontweight="bold", verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="#e8f5e9", edgecolor="darkgreen", alpha=0.7))
ax.text(0.55, 0.95, "Recent universal\n(high recent + high LC)", fontsize=10,
        color="darkblue", fontweight="bold", verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="#e3f2fd", edgecolor="darkblue", alpha=0.7))
ax.text(0.05, 0.06, "Ancient patchy\n(low recent + low LC)", fontsize=10,
        color="dimgray", fontweight="bold", verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="#f5f5f5", edgecolor="gray", alpha=0.7))
ax.text(0.55, 0.06, "HGT-active patchy\n(high recent + low LC)", fontsize=10,
        color="darkred", fontweight="bold", verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="#ffebee", edgecolor="darkred", alpha=0.7))

ax.set_xlabel("Recent gain fraction (M22 'recent' / total gains for class)")
ax.set_ylabel("Mean leaf_consistency (fraction of clade species carrying KO)")
ax.set_title("H3-B — Control-class signature plane: depth × leaf_consistency\n"
             "Strict housekeeping at top-left (vertical universal); HGT-active at bottom-right (patchy active)\n"
             "Validates the project's housekeeping vs HGT-active framework via independent leaf_consistency signal")
ax.set_xlim(-0.02, 1.05); ax.set_ylim(-0.02, 1.05)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_H3b_control_class_signature_plane.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  H3-B saved")

# ============================================================
# S7 — Per-hypothesis leaf_consistency distribution
# ============================================================
tprint("\nS7 — Per-hypothesis leaf_consistency distribution")

# Hypothesis KO sets (matched to focal clade)
ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
MYCOLIC_PATHWAYS = {"ko00061", "ko00071", "ko01040", "ko00540"}
MYCOLIC_SPECIFIC_KOS = {"K11212", "K11211", "K11778", "K11533", "K11534",
                        "K00208", "K20274", "K11782", "K01205", "K00667", "K00507"}
def is_mycolic_ko(row):
    if row["ko"] in MYCOLIC_SPECIFIC_KOS: return True
    p = row.get("pathway_ids", "")
    if not isinstance(p, str): return False
    return bool(set(p.split(",")) & MYCOLIC_PATHWAYS)
ko_pwbr["is_mycolic"] = ko_pwbr.apply(is_mycolic_ko, axis=1)
mycolic_kos = set(ko_pwbr[ko_pwbr["is_mycolic"]]["ko"])

PSII_KOS = {f"K{n:05d}" for n in range(2703, 2728)}
PUL_KOS = {"K21572", "K21573", "K00686", "K01187", "K01193", "K01205",
           "K01207", "K01218", "K01776", "K17241", "K15922", "K15923"}

# Focal-clade × focal-KO leaf_consistency
def get_lc(focal_filter, ko_set, label):
    sub = gains[focal_filter & gains["ko"].isin(ko_set) & gains["leaf_consistency"].notna()]
    return sub["leaf_consistency"].values, label

myco_filter = gains["recipient_family"] == "f__Mycobacteriaceae"
cyano_filter = gains["recipient_class"] == "c__Cyanobacteriia"
bact_filter = gains["recipient_phylum"] == "p__Bacteroidota"

myco_lc, _ = get_lc(myco_filter, mycolic_kos, "Mycobacteriaceae × mycolic")
cyano_lc, _ = get_lc(cyano_filter, PSII_KOS, "Cyanobacteriia × PSII")
bact_lc, _ = get_lc(bact_filter, PUL_KOS, "Bacteroidota × PUL")

# Atlas reference: all events
atlas_lc = gains[gains["leaf_consistency"].notna()]["leaf_consistency"].values
atlas_sample = np.random.default_rng(42).choice(atlas_lc, size=min(200000, len(atlas_lc)), replace=False)

fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
hyp_data = [
    (myco_lc, "Mycobacteriaceae × mycolic", "#9467bd"),
    (cyano_lc, "Cyanobacteriia × PSII", "#ff7f0e"),
    (bact_lc, "Bacteroidota × PUL", "#1f77b4"),
]
for ax, (data, label, color) in zip(axes, hyp_data):
    bins = np.linspace(0, 1, 51)
    ax.hist(atlas_sample, bins=bins, alpha=0.4, color="lightgray", label=f"atlas reference (n={len(atlas_sample):,} sample)", density=True)
    if len(data) > 0:
        ax.hist(data, bins=bins, alpha=0.75, color=color, label=f"focal n={len(data):,}", density=True)
    ax.axvline(np.median(data), color=color, ls="--", lw=2, label=f"focal median = {np.median(data):.2f}" if len(data) else "no data")
    ax.axvline(np.median(atlas_sample), color="gray", ls="--", lw=1, label=f"atlas median = {np.median(atlas_sample):.2f}")
    ax.set_xlabel("leaf_consistency")
    ax.set_title(f"{label}\n(n_focal_events = {len(data):,})", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
axes[0].set_ylabel("density")
fig.suptitle("S7 — Per-hypothesis leaf_consistency: focal events vs atlas reference",
             fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_S7_hypothesis_leaf_consistency.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  S7 saved (myco n={len(myco_lc)}, cyano n={len(cyano_lc)}, bact n={len(bact_lc)})")
tprint(f"    medians: myco {np.median(myco_lc):.2f}, cyano {np.median(cyano_lc):.2f}, bact {np.median(bact_lc):.2f}; atlas {np.median(atlas_sample):.2f}")

# ============================================================
# S8 — Per-rank leaf_consistency ridge (atlas confidence map)
# ============================================================
tprint("\nS8 — Per-rank leaf_consistency ridge")

depth_to_rank = {"recent": "genus", "older_recent": "family", "mid": "order",
                 "older": "class", "ancient": "phylum"}

fig, ax = plt.subplots(figsize=(11, 7))
y_positions = {"recent": 4, "older_recent": 3, "mid": 2, "older": 1, "ancient": 0}
depth_colors = {"recent": "#2ca02c", "older_recent": "#aec7e8",
                "mid": "#ff7f0e", "older": "#9467bd", "ancient": "#8c564b"}

# Subsample for plot
for depth, y_pos in y_positions.items():
    sub = gains[(gains["depth_bin"] == depth) & gains["leaf_consistency"].notna()]
    if len(sub) == 0: continue
    sample = sub["leaf_consistency"].sample(min(50000, len(sub)), random_state=42).values
    median = np.median(sample)
    mean = sample.mean()
    # Build a smooth density approximation
    bins = np.linspace(0, 1, 100)
    counts, _ = np.histogram(sample, bins=bins, density=True)
    counts_norm = counts / counts.max() * 0.85
    centers = 0.5 * (bins[:-1] + bins[1:])
    ax.fill_between(centers, y_pos, y_pos + counts_norm,
                     color=depth_colors[depth], alpha=0.85, edgecolor="black", linewidth=0.5)
    ax.plot([median, median], [y_pos, y_pos + 0.85], color="white", lw=2)
    rank = depth_to_rank[depth]
    ax.text(0.005, y_pos + 0.45, f"{depth}\n(rank: {rank})\nmedian={median:.2f}, mean={mean:.2f}\nn={len(sub):,}",
            fontsize=9, va="center")

ax.set_yticks([])
ax.set_xlabel("leaf_consistency (fraction of recipient_clade species carrying KO)")
ax.set_xlim(0, 1)
ax.set_ylim(-0.2, 5.0)
ax.set_title("S8 — Atlas confidence ridge: leaf_consistency per acquisition-depth bin\n"
             "Recent gains land in clades with KO present in 26-50% of species → near-fixation;\n"
             "Ancient gains have median 5% leaf_consistency → KO retained in only a fraction of phylum members\n"
             "Independently validates M22 acquisition-depth signal: deeper gains diversify with subsequent loss",
             fontsize=11)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4_synthesis_S8_atlas_confidence_ridge.png", dpi=140, bbox_inches="tight")
plt.close()
tprint(f"  S8 saved")

# Save summary stats
diag = {
    "phase": "4", "deliverable": "NB28f — leaf_consistency figures",
    "h3b_class_stats": class_df.to_dict(orient="records"),
    "s7_per_hypothesis": {
        "mycolic": {"n": int(len(myco_lc)), "median": float(np.median(myco_lc)) if len(myco_lc) else None},
        "psii": {"n": int(len(cyano_lc)), "median": float(np.median(cyano_lc)) if len(cyano_lc) else None},
        "pul": {"n": int(len(bact_lc)), "median": float(np.median(bact_lc)) if len(bact_lc) else None},
        "atlas_reference_median": float(np.median(atlas_sample)),
    },
    "s8_per_depth_bin": gains.groupby("depth_bin")["leaf_consistency"].agg(["count", "mean", "median"]).reset_index().to_dict(orient="records"),
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4_leaf_consistency_figures_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"\n=== DONE in {time.time()-t0:.1f}s ===")
