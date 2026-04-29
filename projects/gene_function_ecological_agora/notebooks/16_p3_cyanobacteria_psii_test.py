"""NB16 — Phase 3 Cyanobacteria × PSII Innovator-Exchange test.

Pre-registered Phase 3 hypothesis (RESEARCH_PLAN.md v2 + v2.11 reframe per M25):
  Cyanobacteria → Innovator-Exchange (joint Broker OR Open Innovator,
  donor-undistinguished) at genus rank on PSII Pfam architectures.

The v2 plan pre-registered "Broker" specifically; v2.11 reframed to "Innovator-Exchange"
per M25 — composition-based donor inference at genus rank requires per-CDS sequence
data not in BERDL queryable schemas. Without donor inference we cannot distinguish
Broker (Cyanobacteria as donor) from Open Innovator (Cyanobacteria with paralog
expansion). The test verdict is the joint label.

Falsification criteria (q < 0.0125 = α/4 Bonferroni):
  - Cyanobacteria producer score below atlas non-housekeeping median (would shift
    to Sink/Broker-Exchange, low producer + high participation), OR
  - Cyanobacteria participation score above atlas median, i.e. consumer_z below median
    consumer_z (more cross-clade exchange than typical), OR
  - Both above the atlas median (Innovator-Isolated, low cross-clade exchange) — would
    falsify the Innovator-Exchange hypothesis.

PASS criteria: producer above atlas median + consumer_z below median (i.e., Cyanobacteria
PSII tuples cluster in the high-producer + high-participation quadrant) at q < 0.0125.

KO set: PSII KEGG-KOs K02703-K02727 (PsbA-Z, ~25 KOs; from NB15 architecture census,
PSII KOs are highly conserved single-architecture per KO).
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
print("=== NB16 — Cyanobacteria × PSII Innovator-Exchange test ===", flush=True)

# Load atlas + species + ko_class
atlas = pd.read_parquet(DATA_DIR / "p2_ko_atlas.parquet")
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
ko_class = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
print(f"Atlas: {len(atlas):,} | Species: {len(species_df):,}", flush=True)

# PSII KO set
PSII_KOS = {f"K{n:05d}" for n in range(2703, 2728)}  # K02703-K02727

# Cyanobacteria clade names (GTDB r214)
CYANO_PHYLUM = "p__Cyanobacteriota"
CYANO_CLASS = "c__Cyanobacteriia"
CYANO_ORDER = "o__Cyanobacteriales"

# Diagnostic: how many Cyanobacteriota species do we have?
n_cyano_species = (species_df["phylum"] == CYANO_PHYLUM).sum()
n_cyano_orders = species_df[species_df["phylum"] == CYANO_PHYLUM]["order"].nunique()
n_cyano_families = species_df[species_df["phylum"] == CYANO_PHYLUM]["family"].nunique()
n_cyano_genera = species_df[species_df["phylum"] == CYANO_PHYLUM]["genus"].nunique()
print(f"Cyanobacteriota species: {n_cyano_species:,} across {n_cyano_orders} orders, "
      f"{n_cyano_families} families, {n_cyano_genera} genera", flush=True)

# Filter atlas to PSII KOs
psii_atlas = atlas[atlas["ko"].isin(PSII_KOS)].copy()
print(f"Atlas rows for PSII KOs: {len(psii_atlas):,}", flush=True)
print(f"PSII KOs present in atlas: {psii_atlas['ko'].nunique()} / {len(PSII_KOS)}", flush=True)

# Define Cyanobacteria target sets per rank
# At each rank, collect the clade names that are Cyanobacterial
cyano_orders = set(species_df[species_df["phylum"] == CYANO_PHYLUM]["order"].dropna().unique())
cyano_families = set(species_df[species_df["phylum"] == CYANO_PHYLUM]["family"].dropna().unique())
cyano_genera = set(species_df[species_df["phylum"] == CYANO_PHYLUM]["genus"].dropna().unique())

print(f"Cyano genera count: {len(cyano_genera):,}", flush=True)
print(f"Cyano families count: {len(cyano_families):,}", flush=True)
print(f"Cyano orders count: {len(cyano_orders):,}", flush=True)

# Define housekeeping for non-housekeeping reference
HOUSEKEEPING = set(ko_class[ko_class["control_class"].isin(
    ["neg_ribosomal", "neg_trna_synth", "neg_rnap_core"])]["ko"])
non_hk_atlas = atlas[~atlas["ko"].isin(HOUSEKEEPING)]

# Run the test at multiple ranks
results = []
for rank, target_clades, target_clade_label in [
    ("genus", cyano_genera, "all-Cyano-genera-pooled"),
    ("family", cyano_families, "all-Cyano-families-pooled"),
    ("order", cyano_orders, "all-Cyano-orders-pooled"),
    ("class", {CYANO_CLASS}, "Cyanobacteriia"),
    ("phylum", {CYANO_PHYLUM}, "Cyanobacteriota"),
]:
    # Filter PSII atlas to target clades at this rank
    target_subset = psii_atlas[
        (psii_atlas["rank"] == rank) & (psii_atlas["clade_id"].isin(target_clades))
    ].copy()
    if len(target_subset) == 0:
        results.append({"rank": rank, "target_clades": target_clade_label,
                       "n_psii_kos_present": 0, "verdict": "no_data"})
        continue

    # Atlas non-housekeeping reference at this rank
    ref_at_rank = non_hk_atlas[non_hk_atlas["rank"] == rank]

    target_producer = target_subset["producer_z"].dropna().values
    target_consumer = target_subset["consumer_z"].dropna().values
    ref_producer = ref_at_rank["producer_z"].dropna().values
    ref_consumer = ref_at_rank["consumer_z"].dropna().values

    target_producer_median = float(np.median(target_producer)) if len(target_producer) else np.nan
    target_consumer_median = float(np.median(target_consumer)) if len(target_consumer) else np.nan
    ref_producer_median = float(np.median(ref_producer))
    ref_consumer_median = float(np.median(ref_consumer))

    # Cohen's d
    def cohens_d(a, b):
        a = np.asarray(a, float); b = np.asarray(b, float)
        if len(a) < 2 or len(b) < 2: return np.nan
        sd = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
        return (a.mean() - b.mean()) / sd if sd > 0 else 0.0

    producer_d = cohens_d(target_producer, ref_producer)
    consumer_d = cohens_d(target_consumer, ref_consumer)

    # Mann-Whitney
    if len(target_producer) >= 2 and len(ref_producer) >= 2:
        _, mw_p_p = stats.mannwhitneyu(target_producer, ref_producer, alternative="greater")
    else:
        mw_p_p = np.nan
    # Innovator-Exchange = high producer + high participation = LOW consumer_z (more clumped IS Stable; high participation = LESS clumped = consumer_z above ref)
    # Actually: consumer_z below 0 means more clumped (vertical), above 0 means less clumped (cross-clade).
    # high participation = consumer_z above reference (less clumped than typical non-housekeeping at this rank)
    if len(target_consumer) >= 2 and len(ref_consumer) >= 2:
        _, mw_p_c = stats.mannwhitneyu(target_consumer, ref_consumer, alternative="greater")
    else:
        mw_p_c = np.nan

    bonferroni_alpha = 0.05 / 4

    producer_high = (target_producer_median > ref_producer_median) and (mw_p_p < bonferroni_alpha)
    consumer_high = (target_consumer_median > ref_consumer_median) and (mw_p_c < bonferroni_alpha)

    if producer_high and consumer_high:
        verdict = "INNOVATOR-EXCHANGE (H1 supported, donor-undistinguished per M25)"
    elif producer_high and not consumer_high:
        verdict = "INNOVATOR-ISOLATED (high producer + low participation; H1 falsified — opposite quadrant)"
    elif not producer_high and consumer_high:
        verdict = "SINK/BROKER-EXCHANGE (low producer + high participation; H1 partially supported)"
    else:
        verdict = "STABLE (low producer + low participation; H1 falsified)"

    results.append({
        "rank": rank,
        "target_clades": target_clade_label,
        "n_psii_kos_present": int(len(target_producer)),
        "ref_producer_median": round(ref_producer_median, 4),
        "target_producer_median": round(target_producer_median, 4),
        "ref_consumer_median": round(ref_consumer_median, 4),
        "target_consumer_median": round(target_consumer_median, 4),
        "producer_cohens_d": round(producer_d, 4) if not np.isnan(producer_d) else np.nan,
        "consumer_cohens_d": round(consumer_d, 4) if not np.isnan(consumer_d) else np.nan,
        "mw_p_producer_greater": round(float(mw_p_p), 6) if not np.isnan(mw_p_p) else np.nan,
        "mw_p_consumer_greater": round(float(mw_p_c), 6) if not np.isnan(mw_p_c) else np.nan,
        "producer_high": bool(producer_high),
        "consumer_high": bool(consumer_high),
        "verdict": verdict,
    })

results_df = pd.DataFrame(results)
results_df.to_csv(DATA_DIR / "p3_nb16_cyanobacteria_psii_test.tsv", sep="\t", index=False)
print("\n=== Cyanobacteria × PSII Innovator-Exchange test ===", flush=True)
print(results_df.to_string(index=False), flush=True)

# Producer × Participation distribution within Cyanobacteria × PSII
pp_per_rank = []
for rank, target_clades in [
    ("genus", cyano_genera), ("family", cyano_families), ("order", cyano_orders),
    ("class", {CYANO_CLASS}), ("phylum", {CYANO_PHYLUM})
]:
    sub = psii_atlas[(psii_atlas["rank"] == rank) & (psii_atlas["clade_id"].isin(target_clades))]
    pp = sub["pp_category"].value_counts()
    for cat, n in pp.items():
        pp_per_rank.append({"rank": rank, "pp_category": cat, "n": n})
pp_df = pd.DataFrame(pp_per_rank)
pp_pivot = pp_df.pivot(index="rank", columns="pp_category", values="n").fillna(0).astype(int)
pp_pivot["total"] = pp_pivot.sum(axis=1)
pp_pivot.to_csv(DATA_DIR / "p3_nb16_pp_distribution.tsv", sep="\t")
print("\n=== Producer × Participation distribution: Cyanobacteria × PSII ===", flush=True)
print(pp_pivot.to_string(), flush=True)

# Acquisition-depth profile
attributed = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
psii_gains = attributed[attributed["ko"].isin(PSII_KOS)].copy()
psii_cyano_gains = psii_gains[
    (psii_gains["recipient_phylum"] == CYANO_PHYLUM) |
    (psii_gains["recipient_class"] == CYANO_CLASS) |
    (psii_gains["recipient_order"].isin(cyano_orders)) |
    (psii_gains["recipient_family"].isin(cyano_families)) |
    (psii_gains["recipient_genus"].isin(cyano_genera))
]
print(f"\nPSII gain events recipient = any Cyano clade: {len(psii_cyano_gains):,}", flush=True)
DEPTH_ORDER = ["recent", "older_recent", "mid", "older", "ancient"]
cyano_depth = psii_cyano_gains["depth_bin"].value_counts().reindex(DEPTH_ORDER, fill_value=0)
total_psii_depth = psii_gains["depth_bin"].value_counts().reindex(DEPTH_ORDER, fill_value=0)
cyano_depth_pct = (cyano_depth / max(cyano_depth.sum(), 1) * 100).round(2)
total_depth_pct = (total_psii_depth / max(total_psii_depth.sum(), 1) * 100).round(2)
print(f"Cyanobacteria PSII acquisition-depth: {dict(cyano_depth_pct)}", flush=True)
print(f"All PSII gains acquisition-depth: {dict(total_depth_pct)}", flush=True)

# Figure
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel A: producer + consumer Z by rank
ax = axes[0]
ranks = ["genus", "family", "order", "class", "phylum"]
prod_d = [r["producer_cohens_d"] for r in results if r["rank"] in ranks]
cons_d = [r["consumer_cohens_d"] for r in results if r["rank"] in ranks]
x = np.arange(len(ranks)); w = 0.35
ax.bar(x - w/2, prod_d, w, label="producer Cohen's d", color="#2ca02c", alpha=0.7)
ax.bar(x + w/2, cons_d, w, label="consumer Cohen's d", color="#d62728", alpha=0.7)
ax.axhline(0, color="black", lw=0.5)
ax.axhline(0.3, color="gray", ls="--", lw=0.5, label="d=0.3")
ax.axhline(-0.3, color="gray", ls="--", lw=0.5)
ax.set_xticks(x); ax.set_xticklabels(ranks, rotation=15)
ax.set_ylabel("Cohen's d (Cyano vs atlas non-housekeeping)")
ax.set_title("Cyanobacteria × PSII vs atlas\nproducer + consumer effect sizes")
ax.legend(loc="upper right", fontsize=8)
ax.grid(axis="y", alpha=0.3)

# Panel B: pp distribution at family rank
ax = axes[1]
if "family" in pp_pivot.index:
    family_dist = pp_pivot.loc["family"].drop("total")
    family_dist = family_dist[family_dist > 0]
    ax.pie(family_dist.values, labels=family_dist.index, autopct="%.1f%%", startangle=90,
           colors=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"][:len(family_dist)])
    ax.set_title(f"P × P distribution\nCyanobacteria families × PSII (n={int(family_dist.sum())})")

# Panel C: Acquisition depth comparison
ax = axes[2]
xpos = np.arange(len(DEPTH_ORDER))
ax.bar(xpos - w/2, [cyano_depth_pct.get(d, 0) for d in DEPTH_ORDER], w, label="Cyano recipient", color="#1f77b4", alpha=0.8)
ax.bar(xpos + w/2, [total_depth_pct.get(d, 0) for d in DEPTH_ORDER], w, label="all PSII", color="lightgray", alpha=0.8)
ax.set_xticks(xpos); ax.set_xticklabels(DEPTH_ORDER, rotation=15)
ax.set_ylabel("% of PSII gain events")
ax.set_title(f"Cyanobacteria PSII acquisition-depth\n(n={len(psii_cyano_gains):,} gains)")
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p3_nb16_cyanobacteria_psii.png", dpi=120, bbox_inches="tight")
print(f"Wrote figure ({time.time()-t0:.1f}s)", flush=True)

# Diagnostics
diagnostics = {
    "phase": "3", "notebook": "NB16",
    "hypothesis": "Cyanobacteria → Innovator-Exchange (donor-undistinguished per M25) on PSII at genus rank",
    "n_psii_kos_in_atlas": int(psii_atlas["ko"].nunique()),
    "n_cyano_species": int(n_cyano_species),
    "n_cyano_orders": int(n_cyano_orders),
    "n_cyano_families": int(n_cyano_families),
    "n_cyano_genera": int(n_cyano_genera),
    "alpha_bonferroni": 0.05 / 4,
    "test_results": results_df.to_dict(orient="records"),
    "pp_distribution_per_rank": pp_pivot.to_dict(orient="index"),
    "cyano_psii_acquisition_depth_pct": dict(cyano_depth_pct),
    "all_psii_acquisition_depth_pct": dict(total_depth_pct),
    "n_psii_gains_to_cyano": int(len(psii_cyano_gains)),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p3_nb16_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
