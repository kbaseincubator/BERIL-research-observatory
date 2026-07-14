"""NB17 — Phase 3 TCS HK architectural Alm 2006 back-test.

Test whether the Alm 2006 finding (HPK paralog expansion in specific lineages, with
r ≈ 0.74 between HPK count and recent-LSE fraction at full GTDB scale) is reproducible
at *Pfam architectural resolution* — the resolution Alm 2006 actually used (single-domain
IPR005467 ≈ HisKA Pfam, PF00512).

Architectural-level analysis (not a full Alm r=0.74 reproduction — that's deferred to
Phase 4 P4-D3 which scopes per-genome HPK count + per-genome recent-LSE fraction):
  (1) For each TCS HK architecture, aggregate the atlas KO-level producer/consumer scores
  (2) Per-architecture acquisition-depth from M22 (recipient_clade × architecture)
  (3) Identify which TCS HK architectures show strongest Innovator patterns at deep ranks
  (4) Compare the architectural signal to the NB10 KO-level signal (concordance check)

Subset: 292 TCS HK candidate KOs from NB14, 15 architectures/KO median per NB15,
~700-1000 distinct architectures.

Outputs:
  data/p3_nb17_tcs_hk_architectural.tsv — per-architecture producer/consumer aggregates
  data/p3_nb17_acquisition_depth_per_arch.tsv — per-architecture × depth gain counts
  data/p3_nb17_diagnostics.json
  figures/p3_nb17_tcs_hk_architectural.png
"""
import os, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== NB17 — TCS HK architectural Alm 2006 back-test ===", flush=True)

# Load all inputs
arch_census = pd.read_csv(DATA_DIR / "p3_architecture_census_per_ko.tsv", sep="\t")
arch_summary = pd.read_csv(DATA_DIR / "p3_architecture_summary_per_ko.tsv", sep="\t")
atlas = pd.read_parquet(DATA_DIR / "p2_ko_atlas.parquet")
attributed = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
candidates = pd.read_csv(DATA_DIR / "p3_candidate_set.tsv", sep="\t")
print(f"Architecture census: {len(arch_census):,} (subset, KO, architecture) rows", flush=True)
print(f"Atlas: {len(atlas):,} | M22 gains: {len(attributed):,}", flush=True)

# Filter to TCS HK subset
tcs_hk_kos = set(candidates[candidates["control_class"] == "pos_tcs_hk"]["ko"])
print(f"TCS HK KOs: {len(tcs_hk_kos):,}", flush=True)

tcs_arch = arch_census[(arch_census["subset"] == "tcs_hk")].copy()
print(f"TCS HK (KO, architecture) rows: {len(tcs_arch):,}", flush=True)
print(f"Unique TCS HK architectures: {tcs_arch['architecture'].nunique():,}", flush=True)

# Stage 1: aggregate atlas KO-level scores per (architecture, rank, clade)
# For each architecture, look up the producer/consumer scores of its KOs in the atlas
# Weighted by n_gene_clusters per (KO, architecture) — this captures architectural dominance
atlas_tcs = atlas[atlas["ko"].isin(tcs_hk_kos)].copy()
print(f"Atlas rows for TCS HK KOs: {len(atlas_tcs):,}", flush=True)

# Join: for each architecture, weighted producer/consumer median across constituent KOs
# Approach: per (architecture, rank, clade): take the weighted median of producer_z, consumer_z
# Weight = n_gene_clusters from the architecture census

# Step 1: build (KO, architecture) → n_gene_clusters lookup
ko_arch_weight = tcs_arch.groupby(["ko", "architecture"])["n_gene_clusters"].sum().reset_index()
ko_arch_weight.columns = ["ko", "architecture", "n_gc_for_arch"]

# Per-architecture: distribution of producer_z, consumer_z aggregated across KOs (weighted by n_gc)
# Take for each architecture: the union of all (rank, clade) tuples its constituent KOs cover
arch_atlas = (atlas_tcs
    .merge(ko_arch_weight, on="ko", how="inner")
)
print(f"Arch-atlas join: {len(arch_atlas):,} (rank, clade, KO, architecture) rows", flush=True)

# Aggregate to per (architecture, rank): atlas-level signal (weighted by n_gene_clusters)
def weighted_median(values, weights):
    if len(values) == 0:
        return np.nan
    sorter = np.argsort(values)
    sorted_v = values[sorter]
    sorted_w = weights[sorter]
    cumw = np.cumsum(sorted_w)
    cutoff = sorted_w.sum() / 2.0
    return sorted_v[np.searchsorted(cumw, cutoff)]

per_arch_rank = []
for (arch, rank), grp in arch_atlas.groupby(["architecture", "rank"]):
    pz = grp["producer_z"].dropna().values
    cz = grp["consumer_z"].dropna().values
    pz_w = grp.dropna(subset=["producer_z"])["n_gc_for_arch"].values.astype(float)
    cz_w = grp.dropna(subset=["consumer_z"])["n_gc_for_arch"].values.astype(float)
    per_arch_rank.append({
        "architecture": arch, "rank": rank,
        "n_clade_ko_tuples": len(grp),
        "n_distinct_kos": grp["ko"].nunique(),
        "n_distinct_clades": grp["clade_id"].nunique(),
        "weighted_median_producer_z": weighted_median(pz, pz_w) if len(pz) > 0 else np.nan,
        "weighted_median_consumer_z": weighted_median(cz, cz_w) if len(cz) > 0 else np.nan,
        "frac_innovator_exchange": (grp["pp_category"] == "Innovator-Exchange").sum() / max(len(grp), 1),
        "frac_innovator_isolated": (grp["pp_category"] == "Innovator-Isolated").sum() / max(len(grp), 1),
        "frac_sink_broker": (grp["pp_category"] == "Sink/Broker-Exchange").sum() / max(len(grp), 1),
        "frac_stable": (grp["pp_category"] == "Stable").sum() / max(len(grp), 1),
        "n_gc_total": int(grp["n_gc_for_arch"].sum()),
    })
arch_rank_df = pd.DataFrame(per_arch_rank)
arch_rank_df.to_csv(DATA_DIR / "p3_nb17_tcs_hk_architectural.tsv", sep="\t", index=False)
print(f"Wrote p3_nb17_tcs_hk_architectural.tsv: {len(arch_rank_df):,} (architecture × rank) rows", flush=True)

# Top architectures by weighted producer signal at family rank
print(f"\n=== Top-10 TCS HK architectures by producer_z (family rank) ===", flush=True)
top_prod = arch_rank_df[arch_rank_df["rank"] == "family"].nlargest(10, "weighted_median_producer_z")
print(top_prod[["architecture", "n_clade_ko_tuples", "n_distinct_kos", "weighted_median_producer_z",
                "weighted_median_consumer_z", "frac_innovator_exchange", "frac_innovator_isolated",
                "frac_sink_broker", "n_gc_total"]].to_string(index=False), flush=True)

print(f"\n=== Top-10 TCS HK architectures by Innovator-Exchange fraction (family rank) ===", flush=True)
top_ie = arch_rank_df[arch_rank_df["rank"] == "family"].nlargest(10, "frac_innovator_exchange")
print(top_ie[["architecture", "n_clade_ko_tuples", "frac_innovator_exchange",
              "frac_innovator_isolated", "frac_sink_broker", "n_gc_total"]].to_string(index=False), flush=True)

# Stage 2: per-architecture acquisition-depth from M22
# Map gain events to architectures via KO assignment
gains_tcs = attributed[attributed["ko"].isin(tcs_hk_kos)].copy()
print(f"\nTCS HK gain events: {len(gains_tcs):,}", flush=True)

# Per-(KO, architecture) gain count: weight by n_gc per KO×arch since architectures aren't directly tagged on gains
# Approximate: distribute KO gains across its architectures proportionally to n_gc_for_arch
ko_to_archs = ko_arch_weight.groupby("ko")["architecture"].apply(list).to_dict()
ko_to_arch_weights = (ko_arch_weight
    .groupby("ko")
    .apply(lambda g: dict(zip(g["architecture"], g["n_gc_for_arch"])), include_groups=False)
    .to_dict()
)

# For each gain event, assign it to the architecture(s) of its KO weighted by gene_cluster fraction
arch_depth_rows = []
for ko, depth_counts in gains_tcs.groupby("ko")["depth_bin"].value_counts().groupby(level=0):
    weights = ko_to_arch_weights.get(ko, {})
    total_weight = sum(weights.values()) or 1
    for arch, w in weights.items():
        frac = w / total_weight
        for depth, n_gains in depth_counts.items():
            depth_label = depth[1] if isinstance(depth, tuple) else depth
            arch_depth_rows.append({
                "architecture": arch, "depth_bin": depth_label,
                "ko": ko, "weighted_gains": frac * n_gains
            })
arch_depth = pd.DataFrame(arch_depth_rows)
if len(arch_depth) > 0:
    arch_depth_agg = arch_depth.groupby(["architecture", "depth_bin"])["weighted_gains"].sum().unstack(fill_value=0)
    DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
    for d in DEPTH_ORDER:
        if d not in arch_depth_agg.columns: arch_depth_agg[d] = 0
    arch_depth_agg = arch_depth_agg[DEPTH_ORDER]
    arch_depth_agg["total"] = arch_depth_agg.sum(axis=1)
    for d in DEPTH_ORDER:
        arch_depth_agg[f"{d}_pct"] = (arch_depth_agg[d] / arch_depth_agg["total"].clip(lower=1) * 100).round(2)
    arch_depth_agg = arch_depth_agg.sort_values("total", ascending=False)
    arch_depth_agg.to_csv(DATA_DIR / "p3_nb17_acquisition_depth_per_arch.tsv", sep="\t")
    print(f"Wrote p3_nb17_acquisition_depth_per_arch.tsv: {len(arch_depth_agg):,} architectures", flush=True)

    print(f"\n=== Acquisition depth: top-10 TCS HK architectures by total gain events ===", flush=True)
    print(arch_depth_agg.head(10)[["recent_pct", "older_recent_pct", "mid_pct",
                                  "older_pct", "ancient_pct", "total"]].to_string(), flush=True)

# Stage 3: concordance check — KO-level vs architectural signal for TCS HK
# Concordance: how well does architectural-level signal recover KO-level pp_category at family rank?
# For each TCS HK KO at family rank: pick the dominant architecture (highest n_gc) and check if its
# weighted-median producer/consumer agrees with the KO-level scores.

ko_level_family = atlas_tcs[atlas_tcs["rank"] == "family"].copy()
arch_level_family = arch_rank_df[arch_rank_df["rank"] == "family"].copy()

# Per-KO dominant architecture (NB15-derived)
arch_summary_tcs = arch_summary[arch_summary["subset"] == "tcs_hk"]
ko_to_dominant_arch = dict(zip(arch_summary_tcs["ko"], arch_summary_tcs["dominant_architecture"]))

# Map each KO-level (KO, clade) to its dominant architecture's signal
ko_level_family["dominant_arch"] = ko_level_family["ko"].map(ko_to_dominant_arch)
arch_signal_lookup = arch_level_family.set_index("architecture")[
    ["weighted_median_producer_z", "weighted_median_consumer_z"]
].to_dict(orient="index")

ko_level_family["arch_producer_z"] = ko_level_family["dominant_arch"].map(
    lambda a: arch_signal_lookup.get(a, {}).get("weighted_median_producer_z", np.nan))
ko_level_family["arch_consumer_z"] = ko_level_family["dominant_arch"].map(
    lambda a: arch_signal_lookup.get(a, {}).get("weighted_median_consumer_z", np.nan))

# Concordance: corr(producer_z, arch_producer_z) and corr(consumer_z, arch_consumer_z)
mask = ko_level_family[["producer_z", "arch_producer_z"]].notna().all(axis=1)
if mask.sum() >= 10:
    r_prod = ko_level_family.loc[mask, "producer_z"].corr(ko_level_family.loc[mask, "arch_producer_z"])
else:
    r_prod = np.nan
mask = ko_level_family[["consumer_z", "arch_consumer_z"]].notna().all(axis=1)
if mask.sum() >= 10:
    r_cons = ko_level_family.loc[mask, "consumer_z"].corr(ko_level_family.loc[mask, "arch_consumer_z"])
else:
    r_cons = np.nan

# Concordance >= 0.6 = "confirmatory" per plan v2.11
concord_label_prod = "confirmatory" if not np.isnan(r_prod) and r_prod >= 0.6 else "exploratory"
concord_label_cons = "confirmatory" if not np.isnan(r_cons) and r_cons >= 0.6 else "exploratory"

print(f"\n=== KO ↔ architectural concordance (family rank, TCS HK) ===", flush=True)
print(f"Producer correlation r = {r_prod:.4f} ({concord_label_prod})", flush=True)
print(f"Consumer correlation r = {r_cons:.4f} ({concord_label_cons})", flush=True)

# Figure
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel A: top architectures by producer signal at family rank
ax = axes[0]
top10 = arch_rank_df[arch_rank_df["rank"] == "family"].nlargest(10, "weighted_median_producer_z")
labels = [a.replace("PF", "")[:25] for a in top10["architecture"].tolist()]
y = np.arange(len(labels))
ax.barh(y, top10["weighted_median_producer_z"].values, color="#2ca02c", alpha=0.7)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=7)
ax.set_xlabel("Weighted median producer z (family rank)")
ax.set_title("Top-10 TCS HK architectures\nby producer signal")
ax.axvline(0, color="black", lw=0.5)
ax.grid(axis="x", alpha=0.3)
ax.invert_yaxis()

# Panel B: KO ↔ architectural concordance scatter
ax = axes[1]
mask = ko_level_family[["producer_z", "arch_producer_z"]].notna().all(axis=1)
if mask.sum() > 0:
    ax.scatter(ko_level_family.loc[mask, "producer_z"], ko_level_family.loc[mask, "arch_producer_z"],
               alpha=0.4, s=10, color="#1f77b4")
    lim = [-3, 3]
    ax.plot(lim, lim, "k--", lw=0.5, alpha=0.5)
    ax.axhline(0, color="black", lw=0.5); ax.axvline(0, color="black", lw=0.5)
    ax.set_xlabel("KO-level producer z (NB10 atlas)")
    ax.set_ylabel("Architectural producer z (NB17)")
    ax.set_title(f"KO ↔ architectural concordance\nr = {r_prod:.3f} ({concord_label_prod})")
    ax.grid(alpha=0.3)

# Panel C: acquisition depth profile of dominant TCS HK architectures
ax = axes[2]
if len(arch_depth) > 0:
    top_archs_by_total = arch_depth_agg.nlargest(5, "total").index.tolist()
    DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
    x = np.arange(len(top_archs_by_total))
    bottom = np.zeros(len(top_archs_by_total))
    colors = {"recent": "#d62728", "older_recent": "#ff7f0e", "mid": "#bcbd22",
              "older": "#17becf", "ancient": "#1f77b4"}
    for d in DEPTH_ORDER:
        pct = [arch_depth_agg.loc[a, f"{d}_pct"] for a in top_archs_by_total]
        ax.bar(x, pct, bottom=bottom, label=d, color=colors[d], alpha=0.85)
        bottom += pct
    ax.set_xticks(x)
    ax.set_xticklabels([a.replace("PF", "")[:18] for a in top_archs_by_total], rotation=20, ha="right", fontsize=7)
    ax.set_ylabel("% of gain events at depth")
    ax.set_title("Top-5 TCS HK architectures\nacquisition-depth distribution")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p3_nb17_tcs_hk_architectural.png", dpi=120, bbox_inches="tight")
print(f"Wrote figure ({time.time()-t0:.1f}s)", flush=True)

diagnostics = {
    "phase": "3", "notebook": "NB17",
    "n_tcs_hk_kos": len(tcs_hk_kos),
    "n_tcs_hk_architectures": int(tcs_arch["architecture"].nunique()),
    "n_arch_rank_rows": int(len(arch_rank_df)),
    "concordance_producer_r": float(r_prod) if not np.isnan(r_prod) else None,
    "concordance_consumer_r": float(r_cons) if not np.isnan(r_cons) else None,
    "concordance_producer_label": concord_label_prod,
    "concordance_consumer_label": concord_label_cons,
    "concordance_threshold_v2_11": 0.6,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p3_nb17_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
