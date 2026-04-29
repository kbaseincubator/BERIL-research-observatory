"""NB29 / REVIEW_9 I10 response — recompute Mycobacteriaceae mycolic Cohen's d
on mycolic-positive sub-clade (using leaf_consistency to identify the sub-clade).

The S7 finding (LC=0.15 for Mycobacteriaceae × mycolic) showed that the family-rank
NB12 effect (d=0.31) is a population-mixture average across mycolic-positive and
mycolic-negative members. This script recomputes the effect on the mycolic-positive
sub-clade only (defined as Mycobacteriaceae genera with mean LC ≥ 0.5 for mycolic KOs).
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"

t0 = time.time()
def tprint(msg):
    print(f"[{time.time()-t0:.1f}s] {msg}", flush=True)

tprint("=== NB29 — Mycobacteriaceae mycolic-positive sub-clade Cohen's d ===")

# Load substrates
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
leaf = pd.read_parquet(DATA_DIR / "p4_leaf_consistency_lookup.parquet")
atlas = pd.read_parquet(DATA_DIR / "p4_deep_rank_pp_atlas.parquet")

# Mycolic KO panel (same as NB12)
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
tprint(f"  mycolic KO panel: {len(mycolic_kos)}")

# Mycobacteriaceae genera
myco_genera = species[species["family"] == "f__Mycobacteriaceae"]["genus"].dropna().unique().tolist()
tprint(f"  Mycobacteriaceae genera: {len(myco_genera)}")

# Per-genus mean leaf_consistency for mycolic KOs at genus rank
leaf_genus = leaf[(leaf["rank"] == "genus") & leaf["clade_id"].isin(myco_genera) & leaf["ko"].isin(mycolic_kos)]
genus_lc = leaf_genus.groupby("clade_id")["leaf_consistency"].agg(["mean", "median", "count"]).reset_index()
genus_lc = genus_lc.rename(columns={"clade_id": "genus", "mean": "mean_lc", "median": "median_lc",
                                     "count": "n_mycolic_kos_observed"})
print("\nMycobacteriaceae genera × mycolic-KO leaf_consistency:")
print(genus_lc.sort_values("mean_lc", ascending=False).to_string(index=False))

# Split into mycolic-positive (mean_lc ≥ 0.5) and mycolic-low sub-clades
threshold = 0.5
genus_lc["sub_clade"] = np.where(genus_lc["mean_lc"] >= threshold,
                                  "mycolic-positive", "mycolic-low")
print(f"\nThreshold mean_lc ≥ {threshold}:")
print(genus_lc.groupby("sub_clade").size().to_dict())

mycolic_pos_genera = set(genus_lc[genus_lc["sub_clade"] == "mycolic-positive"]["genus"])
mycolic_low_genera = set(genus_lc[genus_lc["sub_clade"] == "mycolic-low"]["genus"])
tprint(f"  mycolic-positive: {sorted(mycolic_pos_genera)}")
tprint(f"  mycolic-low: {sorted(mycolic_low_genera)}")

# Recompute Cohen's d on producer_z + consumer_z for:
#   - Mycobacteriaceae × mycolic-acid (population-mixture, original NB12)
#   - mycolic-positive sub-clade × mycolic-acid (sub-clade specific)
#   - mycolic-low sub-clade × mycolic-acid (negative sub-clade)
# All against same reference: non-housekeeping atlas at genus rank

HOUSEKEEPING_M21 = {"neg_trna_synth", "neg_rnap_core", "neg_ribosomal",
                    "neg_trna_synth_strict", "neg_rnap_core_strict", "neg_ribosomal_strict"}
ko_class = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
hk_kos = set(ko_class[ko_class["control_class"].isin(HOUSEKEEPING_M21)]["ko"])
non_hk_atlas = atlas[~atlas["ko"].isin(hk_kos)]

def cohens_d(a, b):
    a = np.asarray(a, float); a = a[~np.isnan(a)]
    b = np.asarray(b, float); b = b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2: return np.nan, np.nan
    pooled_sd = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
    if pooled_sd == 0: return 0.0, np.nan
    d = (a.mean() - b.mean()) / pooled_sd
    return d, pooled_sd

def bootstrap_d_ci(a, b, n_boot=200, seed=42):
    """Bootstrap Cohen's d CI. Subsample reference to ≤100K to keep tractable."""
    rng = np.random.default_rng(seed)
    a = np.asarray(a, float); a = a[~np.isnan(a)]
    b = np.asarray(b, float); b = b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2:
        return None
    if len(b) > 100_000:
        b = rng.choice(b, 100_000, replace=False)
    boots = []
    for _ in range(n_boot):
        as_ = rng.choice(a, len(a), replace=True)
        bs_ = rng.choice(b, len(b), replace=True)
        d, _ = cohens_d(as_, bs_)
        boots.append(d)
    boots = np.array(boots)
    return (np.percentile(boots, 2.5), np.percentile(boots, 97.5))

results = []

# (1) Family-rank Mycobacteriaceae × mycolic — population mixture (replicates NB12 framing)
fam_atlas = atlas[(atlas["rank"] == "family") & (atlas["clade_id"] == "f__Mycobacteriaceae")
                   & (atlas["ko"].isin(mycolic_kos))]
fam_ref = non_hk_atlas[non_hk_atlas["rank"] == "family"]
for score_type in ["producer_z", "consumer_z"]:
    target = fam_atlas[score_type].dropna().values
    ref = fam_ref[score_type].dropna().values
    d, _ = cohens_d(target, ref)
    ci = bootstrap_d_ci(target, ref)
    print(f"  Family-rank Mycobacteriaceae × mycolic {score_type}: d = {d:+.3f}, 95% CI = {ci}, n_target = {len(target)}")
    results.append({"sub_clade": "Mycobacteriaceae (family, all)", "score": score_type,
                    "d": float(d), "ci_lo": float(ci[0]) if ci else np.nan,
                    "ci_hi": float(ci[1]) if ci else np.nan, "n_target": int(len(target))})

# (2) Mycolic-positive sub-clade — recomputed at genus rank, only mycolic-positive genera × mycolic KOs
genus_atlas = atlas[(atlas["rank"] == "genus")
                     & (atlas["clade_id"].isin(mycolic_pos_genera))
                     & (atlas["ko"].isin(mycolic_kos))]
genus_ref = non_hk_atlas[non_hk_atlas["rank"] == "genus"]
for score_type in ["producer_z", "consumer_z"]:
    target = genus_atlas[score_type].dropna().values
    ref = genus_ref[score_type].dropna().values
    d, _ = cohens_d(target, ref)
    ci = bootstrap_d_ci(target, ref)
    print(f"  Mycolic-positive sub-clade × mycolic {score_type}: d = {d:+.3f}, 95% CI = {ci}, n_target = {len(target)}")
    results.append({"sub_clade": "mycolic-positive (genus, LC≥0.5)", "score": score_type,
                    "d": float(d), "ci_lo": float(ci[0]) if ci else np.nan,
                    "ci_hi": float(ci[1]) if ci else np.nan, "n_target": int(len(target))})

# (3) Mycolic-low sub-clade — recomputed at genus rank, only mycolic-low genera × mycolic KOs
genus_low_atlas = atlas[(atlas["rank"] == "genus")
                         & (atlas["clade_id"].isin(mycolic_low_genera))
                         & (atlas["ko"].isin(mycolic_kos))]
for score_type in ["producer_z", "consumer_z"]:
    target = genus_low_atlas[score_type].dropna().values
    ref = genus_ref[score_type].dropna().values
    d, _ = cohens_d(target, ref)
    ci = bootstrap_d_ci(target, ref)
    print(f"  Mycolic-low sub-clade × mycolic {score_type}: d = {d:+.3f}, 95% CI = {ci}, n_target = {len(target)}")
    results.append({"sub_clade": "mycolic-low (genus, LC<0.5)", "score": score_type,
                    "d": float(d), "ci_lo": float(ci[0]) if ci else np.nan,
                    "ci_hi": float(ci[1]) if ci else np.nan, "n_target": int(len(target))})

# (4) All Mycobacteriaceae genera (regardless of LC) × mycolic — for comparison
genus_all_atlas = atlas[(atlas["rank"] == "genus")
                         & (atlas["clade_id"].isin(myco_genera))
                         & (atlas["ko"].isin(mycolic_kos))]
for score_type in ["producer_z", "consumer_z"]:
    target = genus_all_atlas[score_type].dropna().values
    ref = genus_ref[score_type].dropna().values
    d, _ = cohens_d(target, ref)
    ci = bootstrap_d_ci(target, ref)
    print(f"  All Mycobacteriaceae genera × mycolic {score_type}: d = {d:+.3f}, 95% CI = {ci}, n_target = {len(target)}")
    results.append({"sub_clade": "all Mycobacteriaceae (genus, no LC filter)", "score": score_type,
                    "d": float(d), "ci_lo": float(ci[0]) if ci else np.nan,
                    "ci_hi": float(ci[1]) if ci else np.nan, "n_target": int(len(target))})

results_df = pd.DataFrame(results)
results_df.to_csv(DATA_DIR / "p4_review9_mycolic_subclade_d.tsv", sep="\t", index=False)
tprint(f"\n  saved p4_review9_mycolic_subclade_d.tsv")

# Save genus_lc for reference
genus_lc.to_csv(DATA_DIR / "p4_review9_mycolic_genus_lc.tsv", sep="\t", index=False)

# Summary
print("\n=== Summary table ===")
pivot = results_df.pivot_table(values="d", index="sub_clade", columns="score").round(3)
print(pivot.to_string())

diag = {
    "phase": "REVIEW_9 response",
    "deliverable": "I10 mycolic sub-clade Cohen's d recomputation",
    "threshold_lc": threshold,
    "n_genera_mycolic_positive": int(len(mycolic_pos_genera)),
    "n_genera_mycolic_low": int(len(mycolic_low_genera)),
    "mycolic_positive_genera": sorted(mycolic_pos_genera),
    "mycolic_low_genera": sorted(mycolic_low_genera),
    "results": results,
    "elapsed_s": round(time.time()-t0, 1),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4_review9_mycolic_subclade_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
tprint(f"=== DONE in {time.time()-t0:.1f}s ===")
