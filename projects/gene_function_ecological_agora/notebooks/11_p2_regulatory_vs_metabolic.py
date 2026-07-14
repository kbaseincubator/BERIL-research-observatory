"""NB11 — Phase 2 Tier-1 regulatory-vs-metabolic diagnostic.

Phase 2 headline test (RESEARCH_PLAN.md v2 / v2.9 reframe):
Do KOs in regulatory KEGG categories (ko03xxx Genetic IP + ko02010-ko02060 Environmental IP)
show different innovation/acquisition signatures than KOs in metabolic categories (ko00xxx)?

Tests:
  T1: Cohen's d on producer_z (regulatory vs metabolic), pooled across ranks
  T2: Cohen's d on consumer_z (regulatory vs metabolic), pooled across ranks
  T3: Cohen's d on recent-acquisition fraction per KO (M22-derived)
  T4: Cohen's d on n_clades_with (Innovator-Exchange + Sink/Broker-Exchange propensity)

Multiple testing: Bonferroni at α/4 = 0.0125 for the four headline tests.

M23 / M24 standards: minimum n ≥ 20 for primary tests (auto-satisfied for category-level pools);
Cohen's d + 95% bootstrap CI (B = 200) + Mann-Whitney p reported for every test.

Verdict criterion (per plan v2):
  H1 = "Innovation pattern differs between regulatory and metabolic at Cohen's d ≥ 0.3 on at least one of producer/participation score at FWER < 0.05"
  PASS if ≥ 1 of T1-T4 achieves d ≥ 0.3 with 95% CI lower bound > 0 AND Mann-Whitney p < 0.0125
  REFRAMED if statistically significant but d < 0.3
  H0 if all tests have d < 0.3 with CI crossing 0
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
print("=== NB11 — Phase 2 Tier-1 regulatory-vs-metabolic ===", flush=True)

# Load atlas + acquisition profile + pathway/BRITE annotations
atlas = pd.read_parquet(DATA_DIR / "p2_ko_atlas.parquet")
print(f"Atlas: {len(atlas):,} (rank, clade, ko) rows", flush=True)
ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
print(f"KO pathway/BRITE: {len(ko_pwbr):,} KOs", flush=True)
attributed = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
print(f"M22 attributed gains: {len(attributed):,}", flush=True)

# === Map KOs to KEGG functional categories ===
# Per RESEARCH_PLAN.md v2:
#   regulatory = 09120 Genetic Information Processing + 09130 Environmental Information Processing
#   metabolic = 09100 Metabolism
# Operationalized via KEGG pathway prefix:
#   - ko03xxx (Genetic IP — replication, transcription, translation, repair)
#   - ko02010-ko02060 (Environmental IP — membrane transport, signal transduction)
#   - ko00xxx-ko01xxx (Metabolism — ko0001x glycolysis through ko0099x; ko010xx-ko019xx pathway maps)

REG_PATHWAY_PREFIXES_GENETIC_IP = {f"ko03{n:03d}" for n in range(0, 100)}  # ko03000-ko03099
REG_PATHWAY_RANGES_ENV_IP = set(f"ko0{n:04d}" for n in [2010, 2020, 2024, 2025, 2026, 2030, 2040, 2060, 2065])  # signal transduction + transporters
REG_PATHWAYS = REG_PATHWAY_PREFIXES_GENETIC_IP | REG_PATHWAY_RANGES_ENV_IP

# Metabolism: pathway IDs ko00xxx through ko019xx
def is_metabolic_pathway(p):
    if not p.startswith("ko"): return False
    try:
        n = int(p[2:])
    except ValueError:
        return False
    return n < 2000  # ko00xxx-ko019xx

def classify_ko(pathways_str):
    if not isinstance(pathways_str, str) or pathways_str == "":
        return "unannotated"
    pwys = set(pathways_str.split(","))
    n_reg = sum(1 for p in pwys if p in REG_PATHWAYS)
    n_met = sum(1 for p in pwys if is_metabolic_pathway(p))
    n_other = sum(1 for p in pwys if p not in REG_PATHWAYS and not is_metabolic_pathway(p))
    # Exclusive classification: KO is "regulatory" iff regulatory pathways outnumber metabolic
    if n_reg > 0 and n_met == 0:
        return "regulatory"
    if n_met > 0 and n_reg == 0:
        return "metabolic"
    if n_reg > 0 and n_met > 0:
        return "mixed"
    return "other"

ko_pwbr["category"] = ko_pwbr["pathway_ids"].apply(classify_ko)
cat_counts = ko_pwbr["category"].value_counts().to_dict()
print(f"KO category distribution: {cat_counts}", flush=True)

# === Per-KO atlas summary stats ===
# Aggregate the (rank, clade, ko) atlas rows to one row per ko by taking medians across all (rank, clade) entries.
# This gives one summary per KO comparable across the regulatory/metabolic test.
atlas_per_ko = (atlas
    .groupby("ko")
    .agg(
        producer_z_median=("producer_z", "median"),
        producer_z_max=("producer_z", "max"),
        consumer_z_median=("consumer_z", "median"),
        consumer_z_max=("consumer_z", "max"),
        n_clades_with_max=("n_clades_with", "max"),
        n_atlas_rows=("rank", "count"),
    )
    .reset_index()
)
print(f"Per-KO summary: {len(atlas_per_ko):,} KOs", flush=True)

# === M22 acquisition-depth fraction per KO ===
depth_per_ko = (attributed
    .groupby(["ko", "depth_bin"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
for col in ["recent", "older_recent", "mid", "older", "ancient"]:
    if col not in depth_per_ko.columns:
        depth_per_ko[col] = 0
depth_per_ko["total_gains"] = depth_per_ko[["recent", "older_recent", "mid", "older", "ancient"]].sum(axis=1)
depth_per_ko["recent_pct"] = depth_per_ko["recent"] / depth_per_ko["total_gains"].clip(lower=1)
depth_per_ko["ancient_pct"] = depth_per_ko["ancient"] / depth_per_ko["total_gains"].clip(lower=1)
depth_per_ko = depth_per_ko[depth_per_ko["total_gains"] >= 5]  # min 5 gains per KO for stable fraction
print(f"Per-KO depth profile: {len(depth_per_ko):,} KOs (≥5 gain events each)", flush=True)

# === Merge all per-KO data with category ===
ko_summary = (atlas_per_ko
    .merge(depth_per_ko[["ko", "recent_pct", "ancient_pct", "total_gains"]], on="ko", how="left")
    .merge(ko_pwbr[["ko", "category"]], on="ko", how="left")
)
ko_summary["category"] = ko_summary["category"].fillna("unannotated")
print(f"Final ko_summary: {len(ko_summary):,} KOs", flush=True)
print("Category counts in summary:")
print(ko_summary["category"].value_counts().to_string(), flush=True)

# === Statistical tests ===
def cohens_d(a, b):
    a = np.asarray(a, float)[~np.isnan(np.asarray(a, float))]
    b = np.asarray(b, float)[~np.isnan(np.asarray(b, float))]
    if len(a) < 2 or len(b) < 2:
        return np.nan
    sd = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
    return (a.mean() - b.mean()) / sd if sd > 0 else 0.0

def boot_d_ci(a, b, B=200, alpha=0.05, seed=42):
    a_arr = np.asarray(a, float); a_arr = a_arr[~np.isnan(a_arr)]
    b_arr = np.asarray(b, float); b_arr = b_arr[~np.isnan(b_arr)]
    if len(a_arr) < 2 or len(b_arr) < 2:
        return (np.nan, np.nan, np.nan, len(a_arr), len(b_arr))
    rng = np.random.default_rng(seed)
    pt = cohens_d(a_arr, b_arr)
    bs = np.empty(B)
    for i in range(B):
        bs[i] = cohens_d(rng.choice(a_arr, len(a_arr), replace=True),
                         rng.choice(b_arr, len(b_arr), replace=True))
    return (pt, np.quantile(bs, alpha/2), np.quantile(bs, 1-alpha/2), len(a_arr), len(b_arr))

reg_kos = ko_summary[ko_summary["category"] == "regulatory"]
met_kos = ko_summary[ko_summary["category"] == "metabolic"]
print(f"\nRegulatory KOs: {len(reg_kos):,} | Metabolic KOs: {len(met_kos):,}", flush=True)

# Tier-1 tests (M24: Cohen's d + 95% bootstrap CI + Mann-Whitney p)
test_results = []
for test_name, col, alt_direction in [
    ("T1_producer_z_median", "producer_z_median", "two-sided"),
    ("T2_consumer_z_median", "consumer_z_median", "two-sided"),
    ("T3_recent_acquisition_pct", "recent_pct", "two-sided"),
    ("T4_n_clades_with_max", "n_clades_with_max", "two-sided"),
]:
    a = reg_kos[col].dropna().values
    b = met_kos[col].dropna().values
    d, lo, hi, n_a, n_b = boot_d_ci(a, b)
    if len(a) >= 2 and len(b) >= 2:
        u, p_two = stats.mannwhitneyu(a, b, alternative=alt_direction)
    else:
        p_two = np.nan
    # Bonferroni-corrected α (4 tests)
    alpha_bonf = 0.05 / 4
    sig_d = (not np.isnan(d)) and abs(d) >= 0.30 and lo > 0 if d > 0 else (not np.isnan(d)) and abs(d) >= 0.30 and hi < 0
    sig_p = (not np.isnan(p_two)) and p_two < alpha_bonf
    test_results.append({
        "test": test_name,
        "n_regulatory": int(n_a),
        "n_metabolic": int(n_b),
        "median_regulatory": round(float(np.median(a)), 4) if len(a) > 0 else np.nan,
        "median_metabolic": round(float(np.median(b)), 4) if len(b) > 0 else np.nan,
        "cohens_d": round(d, 4) if not np.isnan(d) else np.nan,
        "d_ci_lower": round(lo, 4) if not np.isnan(lo) else np.nan,
        "d_ci_upper": round(hi, 4) if not np.isnan(hi) else np.nan,
        "mw_p_two_sided": round(p_two, 6) if not np.isnan(p_two) else np.nan,
        "passes_d_threshold": bool(sig_d),
        "passes_p_bonferroni": bool(sig_p),
        "passes_both": bool(sig_d and sig_p),
    })

results_df = pd.DataFrame(test_results)
results_df.to_csv(DATA_DIR / "p2_nb11_tier1_results.tsv", sep="\t", index=False)
print("\n=== Tier-1 regulatory-vs-metabolic results ===", flush=True)
print(results_df.to_string(index=False), flush=True)

# === Verdict ===
n_passing = int(results_df["passes_both"].sum())
best = results_df.loc[results_df["cohens_d"].abs().idxmax()] if len(results_df) > 0 else None

if n_passing >= 1:
    verdict = "H1 SUPPORTED"
    decision = (
        f"H1 SUPPORTED: {n_passing}/4 tests achieve Cohen's d ≥ 0.3 with 95% CI excluding 0 AND Mann-Whitney p < α/4 = 0.0125. "
        f"Best test: {best['test']}, d = {best['cohens_d']} [CI {best['d_ci_lower']}, {best['d_ci_upper']}], p = {best['mw_p_two_sided']}. "
        f"The Phase 2 headline regulatory-vs-metabolic asymmetry claim is supported."
    )
elif (~results_df["cohens_d"].isna()).any() and (results_df["mw_p_two_sided"] < 0.05).any():
    verdict = "H1 REFRAMED"
    decision = (
        f"H1 REFRAMED: {(results_df['mw_p_two_sided'] < 0.05).sum()}/4 tests significant at uncorrected p < 0.05 "
        f"but no test achieves d ≥ 0.3 with both significance and effect-size criteria after Bonferroni. "
        f"Best test: {best['test']}, d = {best['cohens_d']} [{best['d_ci_lower']}, {best['d_ci_upper']}]. "
        f"Statistically detectable signal exists but below biological-significance threshold; treat as descriptive finding."
    )
else:
    verdict = "H0 NOT REJECTED"
    decision = (
        f"H0 NOT REJECTED: 0/4 tests achieve significance + effect-size threshold. "
        f"Best test: {best['test']}, d = {best['cohens_d']} [{best['d_ci_lower']}, {best['d_ci_upper']}]. "
        f"Project pivots to descriptive H0-atlas fallback per RESEARCH_PLAN.md."
    )

print(f"\n*** VERDICT: {verdict} ***\n", flush=True)
print(decision, flush=True)

# === Per-category Producer × Participation distribution ===
# Atlas pp_category × KO category cross-tab
ko_to_cat = dict(zip(ko_pwbr["ko"], ko_pwbr["category"]))
atlas_with_cat = atlas.copy()
atlas_with_cat["ko_category"] = atlas_with_cat["ko"].map(ko_to_cat).fillna("unannotated")
pp_xtab = atlas_with_cat.groupby(["ko_category", "pp_category"]).size().unstack(fill_value=0)
pp_xtab["total"] = pp_xtab.sum(axis=1)
for col in pp_xtab.columns:
    if col != "total":
        pp_xtab[f"{col}_pct"] = (pp_xtab[col] / pp_xtab["total"] * 100).round(2)
pp_xtab.to_csv(DATA_DIR / "p2_nb11_pp_category_xtab.tsv", sep="\t")
print("\n=== Producer × Participation × KO category cross-tab ===", flush=True)
print(pp_xtab.to_string(), flush=True)

# === M22 acquisition-depth profile per KO category ===
attributed_with_cat = attributed.copy()
attributed_with_cat["ko_category"] = attributed_with_cat["ko"].map(ko_to_cat).fillna("unannotated")
depth_xtab = attributed_with_cat.groupby(["ko_category", "depth_bin"]).size().unstack(fill_value=0)
DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
for col in DEPTH_ORDER:
    if col not in depth_xtab.columns: depth_xtab[col] = 0
depth_xtab = depth_xtab[DEPTH_ORDER]
depth_xtab["total"] = depth_xtab.sum(axis=1)
for col in DEPTH_ORDER:
    depth_xtab[f"{col}_pct"] = (depth_xtab[col] / depth_xtab["total"] * 100).round(2)
depth_xtab.to_csv(DATA_DIR / "p2_nb11_depth_xtab.tsv", sep="\t")
print("\n=== Acquisition-depth × KO category cross-tab ===", flush=True)
print(depth_xtab.to_string(), flush=True)

# === Figure: side-by-side comparison ===
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel A: producer_z + consumer_z box
ax = axes[0]
data = [reg_kos["producer_z_median"].dropna().values, met_kos["producer_z_median"].dropna().values,
        reg_kos["consumer_z_median"].dropna().values, met_kos["consumer_z_median"].dropna().values]
labels = ["reg producer", "met producer", "reg consumer", "met consumer"]
colors = ["#1f77b4", "#ff7f0e", "#1f77b4", "#ff7f0e"]
bp = ax.boxplot(data, tick_labels=labels, showfliers=False, patch_artist=True)
for p, c in zip(bp["boxes"], colors):
    p.set_facecolor(c); p.set_alpha(0.6)
ax.axhline(0, color="black", lw=0.5)
ax.set_ylabel("z-score median per KO")
ax.set_title("Producer / consumer z by category")
ax.tick_params(axis='x', rotation=30)
ax.grid(axis="y", alpha=0.3)

# Panel B: acquisition-depth distribution per category
ax = axes[1]
cats = [c for c in ["regulatory", "metabolic", "mixed", "other", "unannotated"] if c in depth_xtab.index]
x = np.arange(len(cats))
bottom = np.zeros(len(cats))
depth_colors = {"recent": "#d62728", "older_recent": "#ff7f0e", "mid": "#bcbd22",
                "older": "#17becf", "ancient": "#1f77b4"}
for d in DEPTH_ORDER:
    pct = [depth_xtab.loc[c, f"{d}_pct"] for c in cats]
    ax.bar(x, pct, bottom=bottom, label=d, color=depth_colors[d], alpha=0.85)
    bottom += pct
ax.set_xticks(x); ax.set_xticklabels(cats, rotation=30, ha="right")
ax.set_ylabel("% of gain events at depth")
ax.set_title("Acquisition-depth distribution by KO category")
ax.legend(loc="upper right", fontsize=8)
ax.grid(axis="y", alpha=0.3)

# Panel C: Cohen's d with CIs for all 4 tests
ax = axes[2]
ax.axhline(0, color='black', lw=0.5)
ax.axhline(0.3, color='gray', ls='--', lw=1, label="d ≥ 0.3 threshold")
ax.axhline(-0.3, color='gray', ls='--', lw=1)
xs = np.arange(len(results_df))
ax.errorbar(xs, results_df["cohens_d"],
            yerr=[results_df["cohens_d"] - results_df["d_ci_lower"],
                  results_df["d_ci_upper"] - results_df["cohens_d"]],
            fmt='o', capsize=3, color='#d62728', markersize=8)
ax.set_xticks(xs); ax.set_xticklabels([t.split("_", 1)[0] for t in results_df["test"]], rotation=0)
ax.set_ylabel("Cohen's d (regulatory − metabolic)")
ax.set_title(f"Tier-1 effect sizes\nVerdict: {verdict}")
ax.legend(loc='upper right', fontsize=9)
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p2_nb11_regulatory_vs_metabolic.png", dpi=120, bbox_inches='tight')
print(f"\nFigure written ({time.time()-t0:.1f}s elapsed)", flush=True)

# === Diagnostics ===
diagnostics = {
    "phase": "2", "notebook": "NB11", "test_name": "Tier-1 regulatory-vs-metabolic",
    "n_regulatory_kos": len(reg_kos),
    "n_metabolic_kos": len(met_kos),
    "n_mixed_kos": int((ko_summary["category"] == "mixed").sum()),
    "n_other_kos": int((ko_summary["category"] == "other").sum()),
    "n_unannotated_kos": int((ko_summary["category"] == "unannotated").sum()),
    "alpha_bonferroni": 0.05 / 4,
    "n_tests_passing": n_passing,
    "verdict": verdict,
    "decision": decision,
    "best_test": best.to_dict() if best is not None else None,
    "test_results": results_df.to_dict(orient="records"),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p2_nb11_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"Diagnostics written ({time.time()-t0:.1f}s elapsed)", flush=True)

print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
