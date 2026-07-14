"""NB20 / P4-D5 — D2 annotation-density residualization.

Per the v2 plan D2 spec (long-standing pre-registration, repeatedly flagged in adversarial
reviews as deferred):
  > "Per-genome annotated-fraction regressed out as nuisance covariate
  >  (OLS with clade-size, annotated-fraction, GC%, genome-size as predictors)"

Strategy:
  (1) For each clade in the atlas at each rank, compute aggregate covariates from
      the species-level metadata (mean annotated_fraction, mean GC%, mean genome_size,
      clade_size = number of species in clade)
  (2) Run separate OLS regressions of producer_z and consumer_z on these covariates
  (3) Compute residuals as the D2-residualized scores
  (4) Compare raw vs residualized across the project's hypothesis-test verdicts:
      - Does NB11 (regulatory-vs-metabolic) verdict survive? (still H1 REFRAMED with small effect?)
      - Does NB12 (Mycobacteriaceae × mycolic-acid Innovator-Isolated) survive?
      - Does NB16 (Cyanobacteriia × PSII Innovator-Exchange) survive?

Outputs:
  data/p4d5_residualized_atlas.parquet — atlas with raw + residualized scores
  data/p4d5_residualization_diagnostics.json — coefficients, R², hypothesis-test re-runs
  data/p4d5_hypothesis_replication.tsv — pre-registered hypothesis verdicts on residualized scores
  figures/p4d5_residualization_panel.png — raw vs residualized score distributions
"""
import os, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class OLSResult:
    """Minimal OLS result mimicking the statsmodels API surface used here."""
    def __init__(self, X, y):
        self.X = X
        self.y = y
        # solve normal equations via lstsq for numerical stability
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        self.params = beta
        y_hat = X @ beta
        self.resid = y - y_hat
        ss_res = float(np.sum(self.resid ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        self.rsquared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        n, k = X.shape
        # k includes intercept; adj = 1 - (1-R²)*(n-1)/(n-k)
        self.rsquared_adj = 1.0 - (1.0 - self.rsquared) * (n - 1) / (n - k) if n > k else float("nan")


def ols_add_const_fit(X, y):
    Xc = np.column_stack([np.ones(len(X)), X])
    return OLSResult(Xc, y)

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== NB20 / P4-D5 — D2 annotation-density residualization ===", flush=True)

atlas = pd.read_parquet(DATA_DIR / "p2_ko_atlas.parquet")
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
ko_class = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
print(f"Atlas: {len(atlas):,} (rank, clade, ko) rows", flush=True)
print(f"Species: {len(species_df):,}", flush=True)

# Stage 1: per-clade aggregate covariates
print("\nStage 1: per-clade aggregate covariates...", flush=True)
covariates_per_rank = {}
for rank in ["genus", "family", "order", "class", "phylum"]:
    grp = (species_df
        .groupby(rank)
        .agg(
            clade_size=("gtdb_species_clade_id", "count"),
            mean_annotated_fraction=("annotated_fraction", "mean"),
            mean_gc=("gc_percentage", "mean"),
            mean_genome_size=("genome_size", "mean"),
            mean_n_clusters=("n_clusters_total", "mean"),
        )
        .reset_index()
        .rename(columns={rank: "clade_id"})
    )
    covariates_per_rank[rank] = grp
    print(f"  {rank}: {len(grp):,} clades", flush=True)

# Stage 2: join atlas with per-clade covariates
print("\nStage 2: join atlas with covariates...", flush=True)
atlas_with_cov = []
for rank, cov in covariates_per_rank.items():
    sub = atlas[atlas["rank"] == rank].merge(cov, on="clade_id", how="left")
    atlas_with_cov.append(sub)
atlas_aug = pd.concat(atlas_with_cov, ignore_index=True)
print(f"  joined atlas: {len(atlas_aug):,}", flush=True)
print(f"  Coverage of covariates: annotated_fraction = {atlas_aug['mean_annotated_fraction'].notna().mean()*100:.1f}%, "
      f"gc = {atlas_aug['mean_gc'].notna().mean()*100:.1f}%, "
      f"genome_size = {atlas_aug['mean_genome_size'].notna().mean()*100:.1f}%", flush=True)

# Stage 3: residualize producer_z and consumer_z via OLS
print("\nStage 3: OLS residualization...", flush=True)
COVARIATES = ["clade_size", "mean_annotated_fraction", "mean_gc", "mean_genome_size"]

# Standardize covariates (z-score) for stable regression
for c in COVARIATES:
    atlas_aug[f"{c}_z"] = (atlas_aug[c] - atlas_aug[c].mean()) / atlas_aug[c].std()

# Producer residualization
mask_p = atlas_aug["producer_z"].notna() & atlas_aug[[f"{c}_z" for c in COVARIATES]].notna().all(axis=1)
X_p_raw = atlas_aug.loc[mask_p, [f"{c}_z" for c in COVARIATES]].values
y_p = atlas_aug.loc[mask_p, "producer_z"].values
ols_p = ols_add_const_fit(X_p_raw, y_p)
print(f"\nProducer OLS (n = {mask_p.sum():,}):")
print(f"  R² = {ols_p.rsquared:.4f}, adj R² = {ols_p.rsquared_adj:.4f}", flush=True)
print(f"  coefficients (z-scaled covariates):", flush=True)
for name, coef in zip(["const"] + [f"{c}_z" for c in COVARIATES], ols_p.params):
    print(f"    {name}: {coef:+.4f}", flush=True)

atlas_aug["producer_z_residualized"] = np.nan
atlas_aug.loc[mask_p, "producer_z_residualized"] = ols_p.resid

# Consumer residualization
mask_c = atlas_aug["consumer_z"].notna() & atlas_aug[[f"{c}_z" for c in COVARIATES]].notna().all(axis=1)
X_c_raw = atlas_aug.loc[mask_c, [f"{c}_z" for c in COVARIATES]].values
y_c = atlas_aug.loc[mask_c, "consumer_z"].values
ols_c = ols_add_const_fit(X_c_raw, y_c)
print(f"\nConsumer OLS (n = {mask_c.sum():,}):")
print(f"  R² = {ols_c.rsquared:.4f}, adj R² = {ols_c.rsquared_adj:.4f}", flush=True)
print(f"  coefficients (z-scaled covariates):", flush=True)
for name, coef in zip(["const"] + [f"{c}_z" for c in COVARIATES], ols_c.params):
    print(f"    {name}: {coef:+.4f}", flush=True)

atlas_aug["consumer_z_residualized"] = np.nan
atlas_aug.loc[mask_c, "consumer_z_residualized"] = ols_c.resid

# Save residualized atlas
out_cols = ["rank", "clade_id", "ko", "producer_z", "consumer_z",
            "producer_z_residualized", "consumer_z_residualized",
            "pp_category", "n_clades_with",
            "mean_annotated_fraction", "mean_gc", "mean_genome_size", "clade_size"]
atlas_aug[out_cols].to_parquet(DATA_DIR / "p4d5_residualized_atlas.parquet", index=False)
print(f"\nWrote p4d5_residualized_atlas.parquet ({len(atlas_aug):,} rows)", flush=True)

# Stage 4: Re-run hypothesis tests on residualized scores
print(f"\nStage 4: re-test hypotheses on residualized scores...", flush=True)

def cohens_d(a, b):
    a = np.asarray(a, float); a = a[~np.isnan(a)]
    b = np.asarray(b, float); b = b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2: return np.nan
    sd = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1)) / (len(a)+len(b)-2))
    return (a.mean() - b.mean()) / sd if sd > 0 else 0.0

# Build KO category map (regulatory / metabolic / mixed) for NB11 retest
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
ko_to_cat = dict(zip(ko_pwbr["ko"], ko_pwbr["category"]))

# Reproduce NB11 Tier-1 test on residualized scores
hypothesis_results = []
for score_type, raw_col, resid_col in [
    ("producer", "producer_z", "producer_z_residualized"),
    ("consumer", "consumer_z", "consumer_z_residualized"),
]:
    # Per-KO median score across atlas (raw vs residualized)
    raw_per_ko = atlas_aug.groupby("ko")[raw_col].median().reset_index()
    raw_per_ko["category"] = raw_per_ko["ko"].map(ko_to_cat).fillna("unannotated")
    resid_per_ko = atlas_aug.groupby("ko")[resid_col].median().reset_index()
    resid_per_ko["category"] = resid_per_ko["ko"].map(ko_to_cat).fillna("unannotated")

    reg_raw = raw_per_ko[raw_per_ko["category"] == "regulatory"][raw_col].dropna().values
    met_raw = raw_per_ko[raw_per_ko["category"] == "metabolic"][raw_col].dropna().values
    reg_resid = resid_per_ko[resid_per_ko["category"] == "regulatory"][resid_col].dropna().values
    met_resid = resid_per_ko[resid_per_ko["category"] == "metabolic"][resid_col].dropna().values

    d_raw = cohens_d(reg_raw, met_raw)
    d_resid = cohens_d(reg_resid, met_resid)
    _, p_raw = stats.mannwhitneyu(reg_raw, met_raw, alternative="two-sided")
    _, p_resid = stats.mannwhitneyu(reg_resid, met_resid, alternative="two-sided")

    hypothesis_results.append({
        "test": f"NB11 {score_type}_z regulatory vs metabolic",
        "d_raw": round(d_raw, 4), "p_raw": round(float(p_raw), 6),
        "d_residualized": round(d_resid, 4), "p_residualized": round(float(p_resid), 6),
        "n_reg": len(reg_raw), "n_met": len(met_raw),
    })

# NB12 Mycobacteriaceae × mycolic-acid retest
MYCOLIC_PATHWAYS = {"ko00061", "ko00071", "ko01040", "ko00540"}
MYCOLIC_SPECIFIC_KOS = {"K11212", "K11211", "K11778", "K11533", "K11534", "K00208", "K20274", "K11782", "K01205", "K00667", "K00507"}
def is_mycolic_ko(row):
    if row["ko"] in MYCOLIC_SPECIFIC_KOS: return True
    p = row.get("pathway_ids", "")
    if not isinstance(p, str): return False
    return bool(set(p.split(",")) & MYCOLIC_PATHWAYS)
ko_pwbr["is_mycolic"] = ko_pwbr.apply(is_mycolic_ko, axis=1)
mycolic_kos = set(ko_pwbr[ko_pwbr["is_mycolic"]]["ko"])

HOUSEKEEPING = set(ko_class[ko_class["control_class"].isin(["neg_ribosomal", "neg_trna_synth", "neg_rnap_core"])]["ko"])
non_hk_atlas = atlas_aug[~atlas_aug["ko"].isin(HOUSEKEEPING)]

for rank, target_clade, label in [
    ("family", "f__Mycobacteriaceae", "NB12 Mycobacteriaceae × mycolic family"),
    ("order", "o__Mycobacteriales", "NB12 Mycobacteriales × mycolic order"),
]:
    target_subset = atlas_aug[
        (atlas_aug["rank"] == rank) & (atlas_aug["clade_id"] == target_clade) & (atlas_aug["ko"].isin(mycolic_kos))
    ]
    ref_at_rank = non_hk_atlas[non_hk_atlas["rank"] == rank]

    for score_type, raw_col, resid_col in [("producer", "producer_z", "producer_z_residualized"),
                                            ("consumer", "consumer_z", "consumer_z_residualized")]:
        target_raw = target_subset[raw_col].dropna().values
        target_resid = target_subset[resid_col].dropna().values
        ref_raw = ref_at_rank[raw_col].dropna().values
        ref_resid = ref_at_rank[resid_col].dropna().values

        d_raw = cohens_d(target_raw, ref_raw)
        d_resid = cohens_d(target_resid, ref_resid)
        if len(target_raw) >= 2 and len(ref_raw) >= 2:
            _, p_raw = stats.mannwhitneyu(target_raw, ref_raw, alternative="greater" if score_type == "producer" else "less")
            _, p_resid = stats.mannwhitneyu(target_resid, ref_resid, alternative="greater" if score_type == "producer" else "less")
        else:
            p_raw = p_resid = np.nan

        hypothesis_results.append({
            "test": f"{label} {score_type}_z",
            "d_raw": round(d_raw, 4) if not np.isnan(d_raw) else np.nan,
            "p_raw": round(float(p_raw), 6) if not np.isnan(p_raw) else np.nan,
            "d_residualized": round(d_resid, 4) if not np.isnan(d_resid) else np.nan,
            "p_residualized": round(float(p_resid), 6) if not np.isnan(p_resid) else np.nan,
            "n_target": len(target_raw), "n_ref": len(ref_raw),
        })

# NB16 Cyanobacteria × PSII at class rank
PSII_KOS = {f"K{n:05d}" for n in range(2703, 2728)}
psii_atlas = atlas_aug[(atlas_aug["rank"] == "class") & (atlas_aug["clade_id"] == "c__Cyanobacteriia") & (atlas_aug["ko"].isin(PSII_KOS))]
ref_class = non_hk_atlas[non_hk_atlas["rank"] == "class"]

for score_type, raw_col, resid_col in [("producer", "producer_z", "producer_z_residualized"),
                                        ("consumer", "consumer_z", "consumer_z_residualized")]:
    target_raw = psii_atlas[raw_col].dropna().values
    target_resid = psii_atlas[resid_col].dropna().values
    ref_raw = ref_class[raw_col].dropna().values
    ref_resid = ref_class[resid_col].dropna().values
    d_raw = cohens_d(target_raw, ref_raw)
    d_resid = cohens_d(target_resid, ref_resid)
    if len(target_raw) >= 2 and len(ref_raw) >= 2:
        _, p_raw = stats.mannwhitneyu(target_raw, ref_raw, alternative="greater")
        _, p_resid = stats.mannwhitneyu(target_resid, ref_resid, alternative="greater")
    else:
        p_raw = p_resid = np.nan
    hypothesis_results.append({
        "test": f"NB16 Cyanobacteriia × PSII {score_type}_z (class rank)",
        "d_raw": round(d_raw, 4) if not np.isnan(d_raw) else np.nan,
        "p_raw": round(float(p_raw), 6) if not np.isnan(p_raw) else np.nan,
        "d_residualized": round(d_resid, 4) if not np.isnan(d_resid) else np.nan,
        "p_residualized": round(float(p_resid), 6) if not np.isnan(p_resid) else np.nan,
        "n_target": len(target_raw), "n_ref": len(ref_raw),
    })

hyp_df = pd.DataFrame(hypothesis_results)
hyp_df.to_csv(DATA_DIR / "p4d5_hypothesis_replication.tsv", sep="\t", index=False)
print(f"\n=== Hypothesis-test replication: raw vs D2-residualized ===", flush=True)
print(hyp_df.to_string(index=False), flush=True)

# Stage 5: figure
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel A: producer raw vs residualized
ax = axes[0]
mask = atlas_aug["producer_z"].notna() & atlas_aug["producer_z_residualized"].notna()
sample_idx = atlas_aug[mask].sample(min(50000, mask.sum()), random_state=42).index
ax.scatter(atlas_aug.loc[sample_idx, "producer_z"], atlas_aug.loc[sample_idx, "producer_z_residualized"],
           alpha=0.2, s=4, color="#2ca02c")
lim = [-3, 3]
ax.plot(lim, lim, "k--", lw=0.5)
ax.axhline(0, color="black", lw=0.5); ax.axvline(0, color="black", lw=0.5)
ax.set_xlabel("Raw producer_z"); ax.set_ylabel("Residualized producer_z")
ax.set_title(f"Producer: raw vs residualized\n(R² = {ols_p.rsquared:.3f})")
ax.set_xlim(lim); ax.set_ylim(lim); ax.grid(alpha=0.3)

# Panel B: consumer
ax = axes[1]
mask = atlas_aug["consumer_z"].notna() & atlas_aug["consumer_z_residualized"].notna()
sample_idx = atlas_aug[mask].sample(min(50000, mask.sum()), random_state=42).index
ax.scatter(atlas_aug.loc[sample_idx, "consumer_z"], atlas_aug.loc[sample_idx, "consumer_z_residualized"],
           alpha=0.2, s=4, color="#d62728")
lim = [-15, 5]
ax.plot(lim, lim, "k--", lw=0.5)
ax.axhline(0, color="black", lw=0.5); ax.axvline(0, color="black", lw=0.5)
ax.set_xlabel("Raw consumer_z"); ax.set_ylabel("Residualized consumer_z")
ax.set_title(f"Consumer: raw vs residualized\n(R² = {ols_c.rsquared:.3f})")
ax.set_xlim(lim); ax.set_ylim(lim); ax.grid(alpha=0.3)

# Panel C: per-test d comparison
ax = axes[2]
labels_short = [t.replace("NB11 ", "").replace("NB12 ", "").replace("NB16 ", "")[:30] for t in hyp_df["test"]]
x = np.arange(len(labels_short)); w = 0.35
ax.barh(x - w/2, hyp_df["d_raw"].values, w, label="raw", color="lightgray")
ax.barh(x + w/2, hyp_df["d_residualized"].values, w, label="D2-residualized", color="#1f77b4")
ax.axvline(0, color="black", lw=0.5)
ax.axvline(0.3, color="gray", ls="--", lw=0.5, label="d=0.3")
ax.axvline(-0.3, color="gray", ls="--", lw=0.5)
ax.set_yticks(x); ax.set_yticklabels(labels_short, fontsize=7)
ax.set_xlabel("Cohen's d"); ax.set_title("Hypothesis tests: raw vs D2-residualized")
ax.legend(loc="lower right", fontsize=8); ax.grid(axis="x", alpha=0.3)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig(FIG_DIR / "p4d5_residualization_panel.png", dpi=120, bbox_inches="tight")
print(f"Wrote figure ({time.time()-t0:.1f}s)", flush=True)

# Diagnostics
diagnostics = {
    "phase": "4", "deliverable": "P4-D5", "purpose": "D2 annotation-density residualization",
    "n_atlas_rows": int(len(atlas_aug)),
    "covariates": COVARIATES,
    "producer_ols_rsquared": float(ols_p.rsquared),
    "consumer_ols_rsquared": float(ols_c.rsquared),
    "producer_coefficients": {n: float(c) for n, c in zip(["const"] + [f"{c}_z" for c in COVARIATES], ols_p.params)},
    "consumer_coefficients": {n: float(c) for n, c in zip(["const"] + [f"{c}_z" for c in COVARIATES], ols_c.params)},
    "hypothesis_test_replication": hyp_df.to_dict(orient="records"),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d5_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"Wrote p4d5_diagnostics.json", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
