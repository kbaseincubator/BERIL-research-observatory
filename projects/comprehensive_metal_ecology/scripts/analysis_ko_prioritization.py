"""
KO prioritization for functional validation.

Steps:
  1. Rank 118 KOs by single-KO CatBoost LOPO rho (best abs across all env responses)
  2. Cross-check with PGLS per-KO results on the 3 overlapping responses
  3. Query KEGG REST API for pathway membership of top KOs
  4. Identify coherent KEGG modules / pathways among top KOs
  5. Output prioritization table + recommendation of 3-5 KOs
"""

import pandas as pd
import numpy as np
import urllib.request
import urllib.error
import time
import sys

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 140)

# ─── Load data ──────────────────────────────────────────────────────────────────

print("Loading data...")
cb_single  = pd.read_csv("data/catboost_single_ko_ranking.csv")
cb_shap    = pd.read_csv("data/catboost_within_subset_shap.csv")
pgls_ko    = pd.read_csv("data/per_ko_env_prediction.csv")
ko_meta    = pd.read_csv("data/curated_mrg_ko_ids_v2.csv")
cb_lopo    = pd.read_csv("data/catboost_lopo_results.csv")

# Normalise column name discrepancy in ko_meta (KO vs ko)
if "KO" in ko_meta.columns:
    ko_meta = ko_meta.rename(columns={"KO": "ko"})

print(f"  CatBoost single-KO: {len(cb_single):,} rows, {cb_single.ko.nunique()} KOs, "
      f"{cb_single.env_response.nunique()} responses")
print(f"  PGLS per-KO:        {len(pgls_ko):,} rows, {pgls_ko.ko.nunique()} KOs, "
      f"{pgls_ko.env_response.nunique()} responses")
print(f"  KO metadata:        {len(ko_meta):,} KOs")

# ─── Step 1: CatBoost KO ranking ────────────────────────────────────────────────

print("\n--- Step 1: CatBoost single-KO ranking ---")

# Compute per-KO summary across all 15 env responses
cb_summary = (
    cb_single.groupby("ko", as_index=False).agg(
        primary_category=("primary_category", "first"),
        best_abs_rho=("avg_rho", lambda x: x.abs().max()),
        mean_abs_rho=("avg_rho", lambda x: x.abs().mean()),
        n_positive_responses=("avg_rho", lambda x: (x > 0).sum()),
        n_significant_responses=("avg_rho", lambda x: (x.abs() > 0.10).sum()),
    )
)
# Compute best_response and best_rho separately (avoids abs() on string column)
best_idx = cb_single.groupby("ko")["avg_rho"].apply(lambda x: x.abs().idxmax())
best_rows = cb_single.loc[best_idx.values, ["ko", "env_response", "avg_rho"]].rename(
    columns={"env_response": "best_response", "avg_rho": "best_rho"}
)
cb_summary = cb_summary.merge(best_rows, on="ko", how="left")
cb_summary["pseudo_r2_best"] = cb_summary["best_abs_rho"] ** 2

# Top 20 by best absolute rho
top20 = cb_summary.nlargest(20, "best_abs_rho").reset_index(drop=True)
print("\n  Top 20 KOs by best single-response |rho| (CatBoost LOPO):")
print(f"  {'Rank':<5} {'KO':<10} {'Category':<28} {'Best rho':>9} {'Best response':<20} "
      f"{'pseudo-R2':>10} {'n_sig':>6}")
print(f"  {'-'*5} {'-'*10} {'-'*28} {'-'*9} {'-'*20} {'-'*10} {'-'*6}")
for i, row in top20.iterrows():
    print(f"  {i+1:<5} {row.ko:<10} {row.primary_category:<28} {row.best_rho:>+9.4f} "
          f"{row.best_response:<20} {row.pseudo_r2_best:>10.4f} {row.n_significant_responses:>6.0f}")

# Also rank by mean_abs_rho (more stable)
top20_mean = cb_summary.nlargest(20, "mean_abs_rho")
print(f"\n  Top 10 by mean |rho| across all 15 responses:")
print(f"  {'KO':<10} {'Category':<28} {'mean |rho|':>10} {'n sig >0.10':>12}")
for _, row in top20_mean.head(10).iterrows():
    print(f"  {row.ko:<10} {row.primary_category:<28} {row.mean_abs_rho:>10.4f} "
          f"{row.n_significant_responses:>12.0f}")

# ─── Step 2: PGLS cross-check ───────────────────────────────────────────────────

print("\n--- Step 2: PGLS per-KO cross-check (3 overlapping responses) ---")

# Responses where both methods available: GEOROC_Co, GEOROC_Pb, Soil_pH
overlap_responses = ["GEOROC_Co", "GEOROC_Pb", "Soil_pH"]

for resp in overlap_responses:
    cb_resp   = cb_single[cb_single.env_response == resp].set_index("ko")["avg_rho"]
    pgls_resp = pgls_ko[pgls_ko.env_response == resp].set_index("ko")[["beta", "q"]]

    merged = cb_resp.to_frame("cb_rho").join(pgls_resp, how="inner")
    merged["cb_rho2"] = merged["cb_rho"] ** 2
    merged["pgls_sig"] = merged["q"] < 0.05
    merged["sign_agree"] = np.sign(merged["cb_rho"]) == np.sign(merged["beta"])

    n_both_sig = ((merged["cb_rho"].abs() > 0.10) & (merged["q"] < 0.05)).sum()
    n_sign_agree = merged.loc[merged["cb_rho"].abs() > 0.05, "sign_agree"].mean()
    rho_corr = merged["cb_rho"].corr(merged["beta"], method="spearman")

    print(f"\n  {resp}:  n={len(merged)} KOs in both methods")
    print(f"    Both methods significant (|rho|>0.10 + q<0.05): {n_both_sig}")
    print(f"    Sign agreement (|cb_rho|>0.05): {n_sign_agree:.0%}")
    print(f"    Spearman rank correlation (cb_rho vs PGLS beta): {rho_corr:+.3f}")

    # Top KOs where both methods agree
    top_agree = (
        merged[merged["cb_rho"].abs() > 0.05]
        .assign(composite=lambda df: df["cb_rho"].abs() + df["beta"].abs() * 10)
        .nlargest(8, "composite")
    )
    if len(top_agree):
        print(f"    Top KOs with strongest agreement:")
        print(f"    {'KO':<10} {'cb_rho':>8} {'PGLS_beta':>10} {'PGLS_q':>10} {'sign_agree':>12}")
        for ko, row in top_agree.iterrows():
            sa = "YES" if row["sign_agree"] else "NO"
            print(f"    {ko:<10} {row.cb_rho:>+8.4f} {row.beta:>+10.5f} "
                  f"{row.q:>10.4f} {sa:>12}")

# Build a cross-method score for the overlapping responses
pgls_pivot = (
    pgls_ko[pgls_ko.env_response.isin(overlap_responses)]
    .pivot_table(index="ko", columns="env_response", values=["beta", "q"])
)
pgls_pivot.columns = [f"{m}_{r}" for m, r in pgls_pivot.columns]

cb_pivot = (
    cb_single[cb_single.env_response.isin(overlap_responses)]
    .pivot_table(index="ko", columns="env_response", values="avg_rho")
)
cb_pivot.columns = [f"cb_{c}" for c in cb_pivot.columns]

# ─── Step 3: KEGG module/pathway lookup via REST API ────────────────────────────

print("\n--- Step 3: KEGG pathway membership for top KOs ---")

# Candidate KOs: top 25 by best_abs_rho from CatBoost
candidate_kos = top20.head(25)["ko"].tolist()

def kegg_get(url, retries=3, delay=0.35):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(delay * (attempt + 1))
    return None

def get_ko_pathways(ko, delay=0.35):
    """Return list of (pathway_id, pathway_name) for a KO."""
    url = f"https://rest.kegg.jp/link/pathway/{ko}"
    raw = kegg_get(url)
    if not raw or not raw.strip():
        return []
    pathways = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) == 2:
            path_id = parts[1].strip()          # e.g. path:ko00920
            if "map" in path_id or "ko" in path_id:
                pathways.append(path_id.replace("path:", ""))
    return pathways

def get_pathway_name(path_id, delay=0.35):
    url = f"https://rest.kegg.jp/list/{path_id}"
    raw = kegg_get(url)
    if not raw or not raw.strip():
        return path_id
    parts = raw.strip().split("\t")
    return parts[1] if len(parts) >= 2 else path_id

print(f"  Querying KEGG REST API for {len(candidate_kos)} KOs...")
ko_pathways = {}
for ko in candidate_kos:
    paths = get_ko_pathways(ko)
    ko_pathways[ko] = paths
    time.sleep(0.35)

# Collect unique pathway IDs
all_path_ids = set()
for paths in ko_pathways.values():
    all_path_ids.update(p for p in paths if p.startswith("ko"))

print(f"  Unique pathways across top-25 KOs: {len(all_path_ids)}")

# Fetch pathway names
print("  Fetching pathway names...")
path_names = {}
for pid in sorted(all_path_ids):
    name = get_pathway_name(pid)
    path_names[pid] = name
    time.sleep(0.35)

# Pathway enrichment: which pathways contain the most top KOs?
path_ko_count = {}
for ko, paths in ko_pathways.items():
    for p in paths:
        if p.startswith("ko"):
            path_ko_count[p] = path_ko_count.get(p, []) + [ko]

# Sort by number of top KOs in each pathway
sorted_paths = sorted(path_ko_count.items(), key=lambda x: len(x[1]), reverse=True)

print("\n  Pathways containing the most top-25 CatBoost KOs:")
print(f"  {'Pathway':<12} {'n KOs':>6}  {'Name':<55} {'KOs'}")
print(f"  {'-'*12} {'-'*6}  {'-'*55} {'-'*30}")
for pid, kos in sorted_paths[:20]:
    name = path_names.get(pid, pid)[:54]
    ko_str = ", ".join(kos[:6])
    if len(kos) > 6:
        ko_str += f"... (+{len(kos)-6})"
    print(f"  {pid:<12} {len(kos):>6}  {name:<55} {ko_str}")

# ─── Step 4: Module-level view from existing annotation ─────────────────────────

print("\n--- Step 4: KEGG module annotation (from curated list) ---")

top_kos_meta = ko_meta[ko_meta["ko"].isin(candidate_kos)].copy()
top_kos_meta = top_kos_meta.merge(
    cb_summary[["ko", "best_abs_rho", "best_rho", "best_response",
                "mean_abs_rho", "n_significant_responses"]],
    on="ko", how="left"
).sort_values("best_abs_rho", ascending=False)

print("\n  Top-25 KOs with module annotations and CatBoost scores:")
print(f"  {'KO':<10} {'gene':<10} {'metals':<18} {'module':<25} {'best_rho':>9} {'best_response':<20}")
print(f"  {'-'*10} {'-'*10} {'-'*18} {'-'*25} {'-'*9} {'-'*20}")
for _, row in top_kos_meta.iterrows():
    mod = str(row.get("source_kegg_module", ""))[:24] if pd.notna(row.get("source_kegg_module")) else ""
    metals = str(row.get("metals", ""))[:17] if pd.notna(row.get("metals")) else ""
    gene = str(row.get("gene_name", ""))[:9] if pd.notna(row.get("gene_name")) else ""
    print(f"  {row.ko:<10} {gene:<10} {metals:<18} {mod:<25} {row.best_rho:>+9.4f} "
          f"{row.best_response:<20}")

# ─── Step 5: Final prioritization ───────────────────────────────────────────────

print("\n" + "=" * 70)
print("Step 5: Prioritized KOs for functional validation")
print("=" * 70)

# Build composite score:
#   (a) CatBoost pseudo-R² (best response)
#   (b) PGLS FDR significance in any overlapping response
#   (c) Sign agreement between methods
#   (d) Number of env responses with |rho| > 0.10 (breadth of signal)

# Join CatBoost summary with PGLS pivot
priority = cb_summary.copy()
priority = priority.merge(pgls_pivot.reset_index(), on="ko", how="left")
priority = priority.merge(
    ko_meta[["ko", "gene_name", "definition", "metals", "source_kegg_module",
             "primary_category"]].rename(columns={"primary_category": "cat_meta"}),
    on="ko", how="left"
)

# PGLS significance in any overlapping response
pgls_min_q = pgls_ko[pgls_ko.env_response.isin(overlap_responses)].groupby("ko")["q"].min()
priority["pgls_min_q"] = priority["ko"].map(pgls_min_q)
priority["pgls_any_sig"] = priority["pgls_min_q"] < 0.05

# Composite score: weight CatBoost ρ² most heavily, bonus for PGLS concordance
priority["composite"] = (
    priority["pseudo_r2_best"] * 3.0
    + priority["mean_abs_rho"] * 2.0
    + priority["n_significant_responses"] * 0.01
    + priority["pgls_any_sig"].astype(float) * 0.02
)

top_priority = priority.nlargest(15, "composite")

print("\n  Final prioritization table (top 15):")
print(f"  {'Rank':<5} {'KO':<10} {'gene':<10} {'cat':<28} {'metals':<18} "
      f"{'best_rho':>9} {'n_sig':>5} {'PGLS_sig':>9} {'composite':>10}")
print(f"  {'-'*5} {'-'*10} {'-'*10} {'-'*28} {'-'*18} {'-'*9} {'-'*5} {'-'*9} {'-'*10}")
for i, (_, row) in enumerate(top_priority.iterrows()):
    gene = str(row.gene_name)[:9] if pd.notna(row.gene_name) else ""
    metals = str(row.metals)[:17] if pd.notna(row.metals) else ""
    cat = str(row.primary_category)[:27] if pd.notna(row.primary_category) else ""
    pgls_flag = "YES" if row.pgls_any_sig else ("—" if pd.isna(row.pgls_min_q) else "NO")
    print(f"  {i+1:<5} {row.ko:<10} {gene:<10} {cat:<28} {metals:<18} "
          f"{row.best_rho:>+9.4f} {row.n_significant_responses:>5.0f} "
          f"{pgls_flag:>9} {row.composite:>10.4f}")

# ─── Top recommendations ─────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("RECOMMENDED KOs for functional validation (3-5 KOs)")
print("=" * 70)

top5 = top_priority.head(5)
for i, (_, row) in enumerate(top5.iterrows()):
    gene = str(row.gene_name) if pd.notna(row.gene_name) else row.ko
    defn = str(row.definition)[:80] if pd.notna(row.definition) else ""
    metals = str(row.metals) if pd.notna(row.metals) else "unknown"
    mod = str(row.source_kegg_module) if pd.notna(row.source_kegg_module) else "—"
    pgls_str = f"q={row.pgls_min_q:.3f}" if pd.notna(row.pgls_min_q) else "no PGLS"

    # Get pathway names for this KO
    paths_for_ko = ko_pathways.get(row.ko, [])
    path_str = "; ".join(path_names.get(p, p) for p in paths_for_ko[:3] if p.startswith("ko"))

    print(f"\n  #{i+1}: {row.ko} ({gene})")
    print(f"       Definition:  {defn}")
    print(f"       Category:    {row.primary_category}  |  Metals: {metals}")
    print(f"       KEGG module: {mod}")
    print(f"       Pathways:    {path_str[:90] if path_str else '(not in KEGG pathway DB)'}")
    print(f"       Best response: {row.best_response}  rho={row.best_rho:+.4f}  "
          f"(pseudo-R²={row.pseudo_r2_best:.4f})")
    print(f"       n responses |rho|>0.10: {row.n_significant_responses:.0f}/15  "
          f"| PGLS: {pgls_str}")

# Save outputs
priority.sort_values("composite", ascending=False).to_csv(
    "data/ko_prioritization_scores.csv", index=False
)
print(f"\n  Saved → data/ko_prioritization_scores.csv")

# Pathway summary
path_df = pd.DataFrame([
    {"pathway_id": pid, "pathway_name": path_names.get(pid, pid),
     "n_top_kos": len(kos), "top_kos": "; ".join(kos)}
    for pid, kos in sorted_paths
]).sort_values("n_top_kos", ascending=False)
path_df.to_csv("data/kegg_pathway_overlay.csv", index=False)
print(f"  Saved → data/kegg_pathway_overlay.csv")

print("\nDone.")
