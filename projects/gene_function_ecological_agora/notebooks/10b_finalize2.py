"""NB10b finalize2 — load attributed parquet, write profile + figure + diagnostics."""
import os, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"

t0 = time.time()
print("=== NB10b finalize2 ===", flush=True)

attributed = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
print(f"Loaded attributed: {len(attributed):,} rows ({time.time()-t0:.1f}s)", flush=True)

RANKS_DEEP_TO_SHALLOW = ["genus", "family", "order", "class", "phylum"]

# Profile aggregation per rank
print("Computing per-rank profile...", flush=True)
profile_rows = []
for rank in RANKS_DEEP_TO_SHALLOW:
    col = f"recipient_{rank}"
    grp = attributed.dropna(subset=[col]).groupby([col, "ko", "control_class_m21", "depth_bin"]).size().reset_index(name="n_gains")
    grp["recipient_rank"] = rank
    grp = grp.rename(columns={col: "recipient_clade"})
    profile_rows.append(grp)
    print(f"  {rank}: {len(grp):,} rows ({time.time()-t0:.1f}s)", flush=True)
profile = pd.concat(profile_rows, ignore_index=True)
profile.to_parquet(DATA_DIR / "p2_m22_acquisition_profile.parquet", index=False)
print(f"Profile written: {len(profile):,} rows ({time.time()-t0:.1f}s)", flush=True)

# Figure
DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
summary = pd.read_csv(DATA_DIR / "p2_m22_class_depth_summary.tsv", sep="\t", index_col=0)
classes_for_fig = [c for c in ["pos_betalac", "pos_crispr_cas", "pos_tcs_hk",
                                "neg_trna_synth_strict", "neg_rnap_core_strict", "neg_ribosomal_strict"]
                   if c in summary.index]
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(classes_for_fig))
bottom = np.zeros(len(classes_for_fig))
colors = {"recent": "#d62728", "older_recent": "#ff7f0e", "mid": "#bcbd22",
          "older": "#17becf", "ancient": "#1f77b4"}
for depth in DEPTH_ORDER:
    pct = [summary.loc[c, f"{depth}_pct"] if c in summary.index else 0 for c in classes_for_fig]
    ax.bar(x, pct, bottom=bottom, label=depth, color=colors[depth], alpha=0.85)
    bottom += pct
ax.set_xticks(x); ax.set_xticklabels(classes_for_fig, rotation=30, ha="right")
ax.set_ylabel("% of gain events at depth")
ax.set_title("M22 — acquisition-depth distribution per control class\n(recent/genus → ancient/phylum-or-above)")
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p2_m22_acquisition_depth_per_class.png", dpi=120, bbox_inches='tight')
print(f"Figure written ({time.time()-t0:.1f}s)", flush=True)

# Diagnostics
diagnostics = {
    "phase": "2", "notebook": "NB10b", "methodology": "M22",
    "n_gains_attributed": int(len(attributed)),
    "n_profile_rows": int(len(profile)),
    "depth_bin_counts": attributed["depth_bin"].value_counts().to_dict(),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p2_m22_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"Diagnostics written ({time.time()-t0:.1f}s)", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
