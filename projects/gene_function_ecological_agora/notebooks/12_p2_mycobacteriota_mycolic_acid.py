"""NB12 — Phase 2 Mycobacteriota mycolic-acid Innovator-Isolated test.

Pre-registered hypothesis (RESEARCH_PLAN.md v2):
  Mycobacteriota (= GTDB o__Mycobacteriales / f__Mycobacteriaceae) → Innovator-Isolated
  on the mycolic-acid pathway KO set, at deep ranks (family, order).

Innovator-Isolated = high producer + low participation = the deep-rank analog of
Closed Innovator (high producer + low outflow).

Falsification criteria (q < 0.0125 = α/4 Bonferroni for 4 focal tests):
  - producer score on mycolic-acid KOs falls below atlas median for non-housekeeping KOs, OR
  - participation score above atlas median (suggesting cross-clade exchange we don't expect)

KO set definition: KEGG_Pathway containing any of:
  - ko00061 (Fatty acid biosynthesis — FAS-II)
  - ko00071 (Fatty acid degradation)
  - ko01040 (Biosynthesis of unsaturated fatty acids)
  - ko00540 (the plan's literal spec — actually Lipopolysaccharide biosynthesis in KEGG;
    included for plan-faithfulness with caveat)
  PLUS curated mycolic-acid-specific KEGG-KOs:
  - K11212, K11211 (Ag85A/B mycolyltransferase)
  - K11778 (Pks13 polyketide synthase)
  - K11533, K11534 (KasA, KasB mycolic-acid synthesis)
  - K00208 (InhA enoyl-ACP reductase)
  - K20274, K11782 (mycolic acid methyl transferases MmaA1-4)
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
print("=== NB12 — Mycobacteriota mycolic-acid Innovator-Isolated test ===", flush=True)

atlas = pd.read_parquet(DATA_DIR / "p2_ko_atlas.parquet")
ko_pwbr = pd.read_csv(DATA_DIR / "p2_ko_pathway_brite.tsv", sep="\t")
attributed = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
ko_class = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
print(f"Atlas: {len(atlas):,} | KO pathway: {len(ko_pwbr):,} | M22 gains: {len(attributed):,}", flush=True)

# ============================================================================
# Mycolic-acid KO set definition
# ============================================================================
MYCOLIC_PATHWAYS = {"ko00061", "ko00071", "ko01040", "ko00540"}  # broad fatty-acid pathways
MYCOLIC_SPECIFIC_KOS = {
    "K11212", "K11211",  # Ag85A/B/C mycolyltransferases
    "K11778",            # Pks13 polyketide synthase
    "K11533", "K11534",  # KasA, KasB
    "K00208",            # InhA enoyl-ACP reductase
    "K20274", "K11782",  # MmaA methyl transferases
    "K01205",            # Ag85
    "K00667",            # FabH-like
    "K00507",            # DesA desaturase
}

def is_mycolic_ko(row):
    if row["ko"] in MYCOLIC_SPECIFIC_KOS:
        return True
    pwys = row.get("pathway_ids", "")
    if not isinstance(pwys, str) or pwys == "":
        return False
    return bool(set(pwys.split(",")) & MYCOLIC_PATHWAYS)

ko_pwbr["is_mycolic"] = ko_pwbr.apply(is_mycolic_ko, axis=1)
mycolic_kos = set(ko_pwbr[ko_pwbr["is_mycolic"]]["ko"])
print(f"Mycolic-acid candidate KO set: {len(mycolic_kos):,} KOs", flush=True)
print(f"  Curated specific KOs in pool: {len(mycolic_kos & MYCOLIC_SPECIFIC_KOS)}/{len(MYCOLIC_SPECIFIC_KOS)}", flush=True)

# ============================================================================
# Mycobacteriota clade definition (GTDB)
# ============================================================================
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
mycobacterial_species = species_df[species_df["family"] == "f__Mycobacteriaceae"]
print(f"Mycobacteriaceae species: {len(mycobacterial_species):,}", flush=True)
mycobacterial_orders = species_df[species_df["order"] == "o__Mycobacteriales"]
print(f"Mycobacteriales species: {len(mycobacterial_orders):,}", flush=True)

# ============================================================================
# Atlas filter: Mycobacteriota × mycolic-acid KOs
# ============================================================================
atlas_mycolic = atlas[atlas["ko"].isin(mycolic_kos)].copy()
print(f"Atlas rows for mycolic-acid KOs: {len(atlas_mycolic):,}", flush=True)

mycob_atlas = atlas_mycolic[atlas_mycolic["clade_id"].isin(
    set(species_df[species_df["family"] == "f__Mycobacteriaceae"]["family"].unique()) |
    set(species_df[species_df["order"] == "o__Mycobacteriales"]["order"].unique())
)].copy()

# Better: filter atlas by rank+clade combination
atlas_mycolic_at_family = atlas_mycolic[
    (atlas_mycolic["rank"] == "family") & (atlas_mycolic["clade_id"] == "f__Mycobacteriaceae")
].copy()
atlas_mycolic_at_order = atlas_mycolic[
    (atlas_mycolic["rank"] == "order") & (atlas_mycolic["clade_id"] == "o__Mycobacteriales")
].copy()
print(f"Mycobacteriaceae × mycolic at family rank: {len(atlas_mycolic_at_family):,}", flush=True)
print(f"Mycobacteriales × mycolic at order rank: {len(atlas_mycolic_at_order):,}", flush=True)

# ============================================================================
# Compute the comparison: Mycobacteriota × mycolic vs atlas non-housekeeping median
# ============================================================================
# Define non-housekeeping KOs: exclude any KO classified as ribosomal, tRNA-synth, RNAP core
HOUSEKEEPING = set(ko_class[ko_class["control_class"].isin(["neg_ribosomal", "neg_trna_synth", "neg_rnap_core"])]["ko"])
non_hk_atlas = atlas[~atlas["ko"].isin(HOUSEKEEPING)]

results = []
for rank, target_clade, mycolic_subset in [
    ("family", "f__Mycobacteriaceae", atlas_mycolic_at_family),
    ("order", "o__Mycobacteriales", atlas_mycolic_at_order),
]:
    if len(mycolic_subset) == 0:
        results.append({"rank": rank, "clade": target_clade, "n_kos_present": 0,
                       "verdict": "no_data"})
        continue
    # Atlas-wide non-housekeeping reference at this rank
    ref_at_rank = non_hk_atlas[non_hk_atlas["rank"] == rank]
    ref_producer_median = ref_at_rank["producer_z"].median()
    ref_consumer_median = ref_at_rank["consumer_z"].median()

    target_producer = mycolic_subset["producer_z"].dropna().values
    target_consumer = mycolic_subset["consumer_z"].dropna().values
    target_producer_median = float(np.median(target_producer)) if len(target_producer) > 0 else np.nan
    target_consumer_median = float(np.median(target_consumer)) if len(target_consumer) > 0 else np.nan

    # Pre-registered criteria:
    #   producer ABOVE atlas median (high producer), AND consumer BELOW atlas median (low participation = MORE clumped)
    # Cohen's d on (target distribution vs atlas-wide non-housekeeping at this rank)
    producer_d = (target_producer.mean() - ref_at_rank["producer_z"].dropna().mean()) / ref_at_rank["producer_z"].dropna().std() if len(target_producer) > 1 else np.nan
    consumer_d = (target_consumer.mean() - ref_at_rank["consumer_z"].dropna().mean()) / ref_at_rank["consumer_z"].dropna().std() if len(target_consumer) > 1 else np.nan

    # Mann-Whitney
    u_p, mw_p_p = stats.mannwhitneyu(target_producer, ref_at_rank["producer_z"].dropna().values, alternative="greater") if len(target_producer) > 1 else (np.nan, np.nan)
    u_c, mw_p_c = stats.mannwhitneyu(target_consumer, ref_at_rank["consumer_z"].dropna().values, alternative="less") if len(target_consumer) > 1 else (np.nan, np.nan)

    # Verdict logic
    bonferroni_alpha = 0.05 / 4  # 4 focal tests across project
    producer_high = (target_producer_median > ref_producer_median) and (mw_p_p < bonferroni_alpha)
    consumer_low = (target_consumer_median < ref_consumer_median) and (mw_p_c < bonferroni_alpha)

    if producer_high and consumer_low:
        verdict = "INNOVATOR-ISOLATED (H1 supported)"
    elif producer_high and not consumer_low:
        verdict = "INNOVATOR-EXCHANGE (high producer + high participation)"
    elif not producer_high and consumer_low:
        verdict = "STABLE-or-Sink-Closed (low producer + low participation)"
    else:
        verdict = "STABLE / REFRAMED (no significant differentiation)"

    results.append({
        "rank": rank,
        "clade": target_clade,
        "n_mycolic_kos_present": len(target_producer),
        "ref_producer_median": round(float(ref_producer_median), 4),
        "target_producer_median": round(target_producer_median, 4),
        "ref_consumer_median": round(float(ref_consumer_median), 4),
        "target_consumer_median": round(target_consumer_median, 4),
        "producer_cohens_d": round(producer_d, 4) if not np.isnan(producer_d) else np.nan,
        "consumer_cohens_d": round(consumer_d, 4) if not np.isnan(consumer_d) else np.nan,
        "mw_p_producer_greater": round(float(mw_p_p), 6) if not np.isnan(mw_p_p) else np.nan,
        "mw_p_consumer_less": round(float(mw_p_c), 6) if not np.isnan(mw_p_c) else np.nan,
        "producer_high": bool(producer_high),
        "consumer_low": bool(consumer_low),
        "verdict": verdict,
    })

results_df = pd.DataFrame(results)
results_df.to_csv(DATA_DIR / "p2_nb12_mycolic_acid_test.tsv", sep="\t", index=False)
print("\n=== Mycobacteriota × mycolic-acid pre-registered hypothesis test ===", flush=True)
print(results_df.to_string(index=False), flush=True)

# ============================================================================
# Producer × Participation category breakdown for Mycobacteriota × mycolic KOs
# ============================================================================
pp_breakdown = pd.concat([atlas_mycolic_at_family, atlas_mycolic_at_order])
pp_dist = pp_breakdown.groupby(["rank", "pp_category"]).size().unstack(fill_value=0)
print("\n=== Producer × Participation distribution for Mycobacteriota × mycolic ===", flush=True)
print(pp_dist.to_string(), flush=True)
pp_dist.to_csv(DATA_DIR / "p2_nb12_pp_distribution.tsv", sep="\t")

# ============================================================================
# Acquisition-depth profile for Mycobacteriota recipient × mycolic-acid gains
# ============================================================================
mycolic_gains = attributed[attributed["ko"].isin(mycolic_kos)].copy()
mycob_recipient = mycolic_gains[
    (mycolic_gains["recipient_family"] == "f__Mycobacteriaceae") |
    (mycolic_gains["recipient_order"] == "o__Mycobacteriales")
]
print(f"\nMycolic-acid gain events recipient = Mycobacteriaceae or Mycobacteriales: {len(mycob_recipient):,}", flush=True)
mycob_depth = mycob_recipient["depth_bin"].value_counts().reindex(["recent", "older_recent", "mid", "older", "ancient"], fill_value=0)
total_mycob = mycob_depth.sum()
mycob_pct = (mycob_depth / max(total_mycob, 1) * 100).round(2)
print(f"Mycobacteriota mycolic-acid acquisition-depth: {dict(mycob_depth)}", flush=True)
print(f"  pct: {dict(mycob_pct)}", flush=True)

# Reference: all mycolic-acid gain events depth distribution
mycolic_total_depth = mycolic_gains["depth_bin"].value_counts().reindex(["recent", "older_recent", "mid", "older", "ancient"], fill_value=0)
mycolic_total_pct = (mycolic_total_depth / max(mycolic_total_depth.sum(), 1) * 100).round(2)
print(f"All mycolic-acid gains acquisition-depth: {dict(mycolic_total_depth)}", flush=True)
print(f"  pct: {dict(mycolic_total_pct)}", flush=True)

# ============================================================================
# Figure: Mycobacteriota × mycolic-acid summary
# ============================================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel A: target vs reference distributions at each rank
ax = axes[0]
data, labels, colors = [], [], []
for _, row in results_df.iterrows():
    if row["n_mycolic_kos_present"] == 0: continue
    rank = row["rank"]
    clade = row["clade"]
    ref_at_rank = non_hk_atlas[non_hk_atlas["rank"] == rank]
    target = atlas_mycolic[(atlas_mycolic["rank"] == rank) & (atlas_mycolic["clade_id"] == clade)]
    data.extend([target["producer_z"].dropna().values, ref_at_rank["producer_z"].dropna().sample(min(5000, len(ref_at_rank)), random_state=42).values])
    labels.extend([f"{rank}\n{clade.replace('f__','').replace('o__','')}\n(producer)", f"{rank}\nref\n(producer)"])
    colors.extend(["#d62728", "lightgray"])
bp = ax.boxplot(data, tick_labels=labels, showfliers=False, patch_artist=True)
for p, c in zip(bp["boxes"], colors):
    p.set_facecolor(c); p.set_alpha(0.6)
ax.axhline(0, color='black', lw=0.5)
ax.set_ylabel("Producer z")
ax.set_title("Mycobacteriota × mycolic vs reference\n(producer score)")
ax.tick_params(axis='x', labelsize=7)
ax.grid(axis="y", alpha=0.3)

# Panel B: Producer × Participation pie at family rank
ax = axes[1]
if "family" in pp_dist.index:
    family_dist = pp_dist.loc["family"]
    family_dist = family_dist[family_dist > 0]
    ax.pie(family_dist.values, labels=family_dist.index, autopct="%.1f%%", startangle=90,
           colors=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"][:len(family_dist)])
    ax.set_title(f"P × P distribution\nMycobacteriaceae × mycolic-acid (family rank)\nn={family_dist.sum()}")
else:
    ax.text(0.5, 0.5, "no data at family rank", ha="center")

# Panel C: Acquisition-depth comparison
ax = axes[2]
DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
x = np.arange(len(DEPTH_ORDER))
w = 0.35
mycob_pcts = [mycob_pct.get(d, 0) for d in DEPTH_ORDER]
total_pcts = [mycolic_total_pct.get(d, 0) for d in DEPTH_ORDER]
ax.bar(x - w/2, mycob_pcts, w, label="Mycobacteriota recipient", color="#d62728", alpha=0.8)
ax.bar(x + w/2, total_pcts, w, label="all mycolic-acid", color="lightgray", alpha=0.8)
ax.set_xticks(x); ax.set_xticklabels(DEPTH_ORDER, rotation=15)
ax.set_ylabel("% of mycolic-acid gain events")
ax.set_title(f"Mycobacteriota acquisition-depth\nfor mycolic-acid KOs (n={len(mycob_recipient):,} gains)")
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p2_nb12_mycobacteriota_mycolic.png", dpi=120, bbox_inches='tight')
print(f"Figure written ({time.time()-t0:.1f}s elapsed)", flush=True)

# ============================================================================
# Diagnostics
# ============================================================================
diagnostics = {
    "phase": "2", "notebook": "NB12",
    "hypothesis": "Mycobacteriota → Innovator-Isolated on mycolic-acid pathway KOs",
    "n_mycolic_candidate_kos": len(mycolic_kos),
    "n_curated_specific_kos": len(MYCOLIC_SPECIFIC_KOS),
    "n_mycobacteriaceae_species": int(len(mycobacterial_species)),
    "n_mycobacteriales_species": int(len(mycobacterial_orders)),
    "alpha_bonferroni": 0.05 / 4,
    "test_results": results_df.to_dict(orient="records"),
    "mycob_recipient_depth_distribution": dict(mycob_pct),
    "all_mycolic_depth_distribution": dict(mycolic_total_pct),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p2_nb12_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"Diagnostics written ({time.time()-t0:.1f}s elapsed)", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
