"""NB14 — Phase 3 candidate KO selection (v2 — atlas-only filter).

Filter the Phase 2 atlas to KOs eligible for the architectural deep-dive:
  (1) at least one (rank, clade, KO) tuple has off-(low,low) Producer × Participation
      (i.e., pp_category in {Innovator-Exchange, Innovator-Isolated, Sink/Broker-Exchange})

Architecture-count filter (≥2 distinct Pfam architectures) deferred to NB15 architecture
census, which computes architectures per-KO directly from interproscan_domains. The
833M-row IPS scan via Spark Connect was too heavy at NB14 stage; pushing it to NB15
where the architecture data is the actual deliverable, not a filter intermediate.

This is consistent with the plan v2.11 spirit: 10,750 candidate KOs is tractable for
Phase 3 architectural deep-dive, and the architecture diversity will emerge naturally
from NB15's per-KO census.

Outputs:
  data/p3_candidate_set.tsv — KO + best P×P signal per rank + atlas-side metadata
  data/p3_candidate_diagnostics.json
"""
import os, json, time
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
print("=== NB14 v2 — Phase 3 candidate KO selection (atlas-only) ===", flush=True)

atlas = pd.read_parquet(DATA_DIR / "p2_ko_atlas.parquet")
print(f"Atlas: {len(atlas):,} (rank, clade, KO) rows", flush=True)

OFF_LOW_LOW = {"Innovator-Exchange", "Innovator-Isolated", "Sink/Broker-Exchange"}
off_atlas = atlas[atlas["pp_category"].isin(OFF_LOW_LOW)].copy()
print(f"Off-(low,low) tuples: {len(off_atlas):,}", flush=True)

# Per-KO summary
ko_summary = (off_atlas
    .groupby("ko")
    .agg(
        n_off_stable_tuples=("rank", "count"),
        max_abs_producer_z=("producer_z", lambda x: x.abs().max()),
        max_consumer_z=("consumer_z", "max"),
        min_consumer_z=("consumer_z", "min"),
        n_innovator_exchange=("pp_category", lambda x: (x == "Innovator-Exchange").sum()),
        n_innovator_isolated=("pp_category", lambda x: (x == "Innovator-Isolated").sum()),
        n_sink_broker=("pp_category", lambda x: (x == "Sink/Broker-Exchange").sum()),
    )
    .reset_index()
)
print(f"Candidate KOs: {len(ko_summary):,}", flush=True)

# Per-KO best rank summary (where the strongest off-Stable signal is)
def best_rank_signal(group):
    # Prioritize Innovator-Exchange > Innovator-Isolated > Sink/Broker-Exchange
    priority = {"Innovator-Exchange": 3, "Innovator-Isolated": 2, "Sink/Broker-Exchange": 1, "Stable": 0}
    group = group.copy()
    group["priority"] = group["pp_category"].map(priority)
    best = group.loc[group["priority"].idxmax()]
    return pd.Series({
        "best_rank": best["rank"],
        "best_clade": best["clade_id"],
        "best_pp_category": best["pp_category"],
        "best_producer_z": best["producer_z"],
        "best_consumer_z": best.get("consumer_z", float("nan")),
    })

print("Computing per-KO best rank signal...", flush=True)
ko_best = off_atlas.groupby("ko", as_index=False).apply(best_rank_signal, include_groups=False).reset_index(drop=True)
ko_summary = ko_summary.merge(ko_best, on="ko", how="left")
print(f"  done ({time.time()-t0:.1f}s)", flush=True)

# Add KO control_class + KEGG category
ko_class = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
ko_summary = ko_summary.merge(ko_class[["ko", "control_class"]], on="ko", how="left")

ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
REG_PATHWAY_PREFIXES = {f"ko03{n:03d}" for n in range(0, 100)}
REG_PATHWAY_RANGES = {f"ko0{n:04d}" for n in [2010, 2020, 2024, 2025, 2026, 2030, 2040, 2060, 2065]}
REG_PATHWAYS = REG_PATHWAY_PREFIXES | REG_PATHWAY_RANGES

def is_metabolic(p):
    if not p.startswith("ko"): return False
    try: n = int(p[2:])
    except ValueError: return False
    return n < 2000

def classify(pathways_str):
    if not isinstance(pathways_str, str) or pathways_str == "": return "unannotated"
    pwys = set(pathways_str.split(","))
    n_reg = sum(1 for p in pwys if p in REG_PATHWAYS)
    n_met = sum(1 for p in pwys if is_metabolic(p))
    if n_reg > 0 and n_met == 0: return "regulatory"
    if n_met > 0 and n_reg == 0: return "metabolic"
    if n_reg > 0 and n_met > 0: return "mixed"
    return "other"

ko_pwbr["category"] = ko_pwbr["pathway_ids"].apply(classify)
ko_summary = ko_summary.merge(ko_pwbr[["ko", "category", "pathway_ids"]], on="ko", how="left")

# Selection score for ordering
ko_summary["selection_score"] = (
    ko_summary["n_innovator_exchange"] * 3 +
    ko_summary["n_innovator_isolated"] * 2 +
    ko_summary["n_sink_broker"] * 1
)
ko_summary = ko_summary.sort_values(["selection_score", "n_off_stable_tuples"], ascending=False)

out_cols = ["ko", "control_class", "category", "n_off_stable_tuples",
            "n_innovator_exchange", "n_innovator_isolated", "n_sink_broker",
            "max_abs_producer_z", "max_consumer_z", "min_consumer_z",
            "best_rank", "best_clade", "best_pp_category", "best_producer_z", "best_consumer_z",
            "pathway_ids", "selection_score"]
ko_summary[out_cols].to_csv(DATA_DIR / "p3_candidate_set.tsv", sep="\t", index=False)
print(f"Wrote p3_candidate_set.tsv ({len(ko_summary):,} candidate KOs)", flush=True)

# Distribution by category and control class
cat_dist = ko_summary["category"].value_counts().to_dict()
cc_dist = ko_summary["control_class"].value_counts().to_dict()
print(f"\n=== Candidate KO category distribution ===", flush=True)
for k, v in sorted(cat_dist.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v:,}", flush=True)
print(f"\n=== Candidate KO control class distribution ===", flush=True)
for k, v in sorted(cc_dist.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v:,}", flush=True)

# Top-20 by selection_score
print(f"\n=== Top 20 candidates by Innovator-Exchange weight ===", flush=True)
top = ko_summary.head(20)[["ko", "control_class", "category", "n_innovator_exchange",
                            "n_innovator_isolated", "n_sink_broker", "best_pp_category", "best_clade"]]
print(top.to_string(index=False), flush=True)

# Diagnostics
diagnostics = {
    "phase": "3", "notebook": "NB14",
    "version": "v2 — atlas-only filter (architecture count deferred to NB15)",
    "n_atlas_rows": int(len(atlas)),
    "n_off_low_low_tuples": int(len(off_atlas)),
    "n_candidate_kos": int(len(ko_summary)),
    "category_distribution": cat_dist,
    "control_class_distribution": cc_dist,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p3_candidate_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"\nWrote p3_candidate_diagnostics.json ({time.time()-t0:.1f}s)", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
