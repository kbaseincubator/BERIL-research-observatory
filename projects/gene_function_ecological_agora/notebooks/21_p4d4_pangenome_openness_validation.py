"""NB21 / P4-D4 — Within-species pangenome openness vs M22 recent-acquisition.

Per the v2.9 plan:
  > "Per-species openness from kbase_ke_pangenome.pangenome cross-correlated with
  >  M22 recent-acquisition rate per (clade × function-class). Validates M22 against
  >  an independent substrate."

M22 detects recent-rank gain events on the species tree via Sankoff parsimony.
Pangenome openness is per-species via motupan output (aux_genome / gene_clusters).
The two are independent measurement substrates: M22 uses the GTDB species tree
+ KO presence/absence; pangenome openness uses within-species genome-set diversity.
If they correlate at the per-genus level, that's an independent-substrate validation
of the M22 recent-acquisition signal.

Substrate filter: only species with no_genomes >= 3 (pangenome meaningful only with
multi-genome species). Per-genus aggregation: mean openness across constituent species
with no_genomes >= 3.

Tests:
  T1 atlas-wide  — per-genus: mean openness vs total recent gains (all KOs, all classes)
  T2 class-stratified — does the T1 correlation differ between regulatory KOs and
     metabolic KOs (NB11 reframe)?
  T3 hypothesis-targeted — does Mycobacteriaceae × mycolic-acid show stronger openness-
     gain coupling than the genus-rank atlas average? Does Cyanobacteriia × PSII at
     class rank?

Outputs:
  data/p4d4_pangenome_openness_per_genus.tsv
  data/p4d4_recent_acquisition_vs_openness.tsv
  data/p4d4_diagnostics.json
  figures/p4d4_openness_vs_acquisition.png
"""
import json, time
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
print("=== NB21 / P4-D4 — pangenome openness vs M22 recent-acquisition ===", flush=True)

# Stage 1: per-species openness
species = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
print(f"P1B species: {len(species):,}", flush=True)
multi = species[species["no_genomes"] >= 3].copy()
print(f"  with no_genomes >= 3: {len(multi):,}", flush=True)
multi["aux_fraction"] = multi["no_aux_genome"] / multi["no_gene_clusters"]
multi["singleton_fraction"] = multi["no_singleton_gene_clusters"] / multi["no_gene_clusters"]
multi["core_fraction"] = multi["no_core"] / multi["no_gene_clusters"]
multi["openness"] = 1.0 - multi["core_fraction"]  # primary metric

# Stage 2: per-genus aggregate openness
genus_open = (multi
    .groupby("genus")
    .agg(
        n_species_multi=("gtdb_species_clade_id", "count"),
        mean_openness=("openness", "mean"),
        mean_aux_fraction=("aux_fraction", "mean"),
        mean_singleton_fraction=("singleton_fraction", "mean"),
        mean_no_genomes=("no_genomes", "mean"),
        mean_genome_size=("genome_size", "mean"),
    )
    .reset_index()
)
genus_open.to_csv(DATA_DIR / "p4d4_pangenome_openness_per_genus.tsv", sep="\t", index=False)
print(f"Per-genus openness: {len(genus_open):,} genera with at least one multi-genome species", flush=True)

# Stage 3: M22 recent gains per genus (all KOs)
gains = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
print(f"M22 gains: {len(gains):,}", flush=True)
recent_genus_gains = (gains[gains["depth_bin"] == "recent"]
    .dropna(subset=["recipient_genus"])
    .groupby("recipient_genus")
    .size()
    .reset_index(name="recent_gain_count_all")
    .rename(columns={"recipient_genus": "genus"})
)
print(f"Recent gains attributed to a genus: {recent_genus_gains['recent_gain_count_all'].sum():,}", flush=True)

# Join atlas-wide
atlas_test = genus_open.merge(recent_genus_gains, on="genus", how="left")
atlas_test["recent_gain_count_all"] = atlas_test["recent_gain_count_all"].fillna(0)
atlas_test["recent_gain_log10"] = np.log10(atlas_test["recent_gain_count_all"] + 1)

# Filter for genera with sufficient species support (≥3 multi-genome species)
solid_genera = atlas_test[atlas_test["n_species_multi"] >= 3].copy()
print(f"Genera with ≥3 multi-genome species (T1 substrate): {len(solid_genera):,}", flush=True)

# Stage 4: T1 atlas-wide correlation
def corr_with_ci(x, y, n_boot=2000, seed=42):
    """Pearson + Spearman with bootstrap 95% CI."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]; y = y[mask]
    if len(x) < 5:
        return {"n": len(x), "pearson_r": np.nan, "pearson_ci": (np.nan, np.nan),
                "spearman_r": np.nan, "spearman_ci": (np.nan, np.nan), "p": np.nan}
    pr = float(stats.pearsonr(x, y).statistic)
    sr = float(stats.spearmanr(x, y).statistic)
    p = float(stats.spearmanr(x, y).pvalue)
    rng = np.random.default_rng(seed)
    pr_boot = []; sr_boot = []
    n = len(x)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        pr_boot.append(stats.pearsonr(x[idx], y[idx]).statistic)
        sr_boot.append(stats.spearmanr(x[idx], y[idx]).statistic)
    return {
        "n": n,
        "pearson_r": round(pr, 4),
        "pearson_ci": (round(float(np.percentile(pr_boot, 2.5)), 4),
                       round(float(np.percentile(pr_boot, 97.5)), 4)),
        "spearman_r": round(sr, 4),
        "spearman_ci": (round(float(np.percentile(sr_boot, 2.5)), 4),
                        round(float(np.percentile(sr_boot, 97.5)), 4)),
        "spearman_p": p,
    }

print("\nStage 4: T1 atlas-wide — mean openness vs recent gains (per genus)", flush=True)
t1_results = []
for x_col, x_label in [("mean_openness", "openness (1 - core_fraction)"),
                         ("mean_aux_fraction", "aux_fraction"),
                         ("mean_singleton_fraction", "singleton_fraction")]:
    for y_col, y_label in [("recent_gain_count_all", "recent_gain_count"),
                             ("recent_gain_log10", "log10(recent_gain_count+1)")]:
        r = corr_with_ci(solid_genera[x_col], solid_genera[y_col])
        result = {"x": x_label, "y": y_label, **r}
        t1_results.append(result)
        print(f"  {x_label} vs {y_label}: pearson r = {r['pearson_r']:+.3f} {r['pearson_ci']}, "
              f"spearman r = {r['spearman_r']:+.3f} {r['spearman_ci']}, p = {r['spearman_p']:.2e}", flush=True)

# Stage 5: T2 class-stratified — regulatory vs metabolic
print("\nStage 5: T2 class-stratified — regulatory vs metabolic", flush=True)
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

t2_results = []
for cat in ["regulatory", "metabolic"]:
    cat_kos = {k for k, c in ko_to_cat.items() if c == cat}
    cat_gains = (gains[(gains["depth_bin"] == "recent") & gains["ko"].isin(cat_kos)]
        .dropna(subset=["recipient_genus"])
        .groupby("recipient_genus").size().reset_index(name=f"recent_gains_{cat}")
        .rename(columns={"recipient_genus": "genus"})
    )
    sub = solid_genera.merge(cat_gains, on="genus", how="left")
    sub[f"recent_gains_{cat}"] = sub[f"recent_gains_{cat}"].fillna(0)
    sub[f"log_{cat}"] = np.log10(sub[f"recent_gains_{cat}"] + 1)
    r = corr_with_ci(sub["mean_openness"], sub[f"log_{cat}"])
    result = {"category": cat, "n_kos": len(cat_kos), **r}
    t2_results.append(result)
    print(f"  {cat} ({len(cat_kos):,} KOs): pearson = {r['pearson_r']:+.3f} {r['pearson_ci']}, "
          f"spearman = {r['spearman_r']:+.3f} {r['spearman_ci']}", flush=True)

# Stage 6: T3 hypothesis-targeted
print("\nStage 6: T3 hypothesis-targeted (Mycobacteriaceae × mycolic; Cyanobacteriia × PSII)", flush=True)

# Mycobacteriaceae × mycolic — at genus rank within family Mycobacteriaceae
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
print(f"  Mycolic KO panel: {len(mycolic_kos)} KOs", flush=True)

# species in family Mycobacteriaceae
myco_species = multi[multi["family"] == "f__Mycobacteriaceae"].copy()
myco_genera = myco_species["genus"].dropna().unique().tolist()
print(f"  Mycobacteriaceae multi-genome species: {len(myco_species)} across {len(myco_genera)} genera", flush=True)

myco_genus_open = (myco_species.groupby("genus")
    .agg(n_species_multi=("gtdb_species_clade_id", "count"),
         mean_openness=("openness", "mean"))
    .reset_index()
)
myco_recent_mycolic = (gains[(gains["depth_bin"] == "recent") & gains["ko"].isin(mycolic_kos)]
    .dropna(subset=["recipient_genus"])
    .query("recipient_genus in @myco_genera")
    .groupby("recipient_genus").size().reset_index(name="recent_mycolic_gains")
    .rename(columns={"recipient_genus": "genus"})
)
myco_test = myco_genus_open.merge(myco_recent_mycolic, on="genus", how="left").fillna({"recent_mycolic_gains": 0})
myco_test["log_mycolic"] = np.log10(myco_test["recent_mycolic_gains"] + 1)

t3_myco = corr_with_ci(myco_test["mean_openness"], myco_test["log_mycolic"])
print(f"  Mycobacteriaceae mean_openness vs log_mycolic_recent_gains (n_genera = {len(myco_test)}): "
      f"pearson = {t3_myco['pearson_r']:+.3f} {t3_myco['pearson_ci']}, "
      f"spearman = {t3_myco['spearman_r']:+.3f} {t3_myco['spearman_ci']}", flush=True)

# Cyanobacteriia × PSII — at class rank, since NB16 supported only at class
PSII_KOS = {f"K{n:05d}" for n in range(2703, 2728)}
print(f"  PSII KO panel: {len(PSII_KOS)} KOs", flush=True)

# species in class Cyanobacteriia
cyano_species = multi[multi["class"] == "c__Cyanobacteriia"].copy()
cyano_genera = cyano_species["genus"].dropna().unique().tolist()
print(f"  Cyanobacteriia multi-genome species: {len(cyano_species)} across {len(cyano_genera)} genera", flush=True)

cyano_genus_open = (cyano_species.groupby("genus")
    .agg(n_species_multi=("gtdb_species_clade_id", "count"),
         mean_openness=("openness", "mean"))
    .reset_index()
)
cyano_recent_psii = (gains[(gains["depth_bin"] == "recent") & gains["ko"].isin(PSII_KOS)]
    .dropna(subset=["recipient_genus"])
    .query("recipient_genus in @cyano_genera")
    .groupby("recipient_genus").size().reset_index(name="recent_psii_gains")
    .rename(columns={"recipient_genus": "genus"})
)
cyano_test = cyano_genus_open.merge(cyano_recent_psii, on="genus", how="left").fillna({"recent_psii_gains": 0})
cyano_test["log_psii"] = np.log10(cyano_test["recent_psii_gains"] + 1)

t3_cyano = corr_with_ci(cyano_test["mean_openness"], cyano_test["log_psii"])
print(f"  Cyanobacteriia mean_openness vs log_psii_recent_gains (n_genera = {len(cyano_test)}): "
      f"pearson = {t3_cyano['pearson_r']:+.3f} {t3_cyano['pearson_ci']}, "
      f"spearman = {t3_cyano['spearman_r']:+.3f} {t3_cyano['spearman_ci']}", flush=True)

# Stage 7: write atlas-level join
print("\nStage 7: write per-genus joined table", flush=True)
solid_genera.to_csv(DATA_DIR / "p4d4_recent_acquisition_vs_openness.tsv", sep="\t", index=False)

# Stage 8: figure
print("\nStage 8: figure", flush=True)
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Panel A: atlas-wide (all KOs)
ax = axes[0, 0]
ax.scatter(solid_genera["mean_openness"], solid_genera["recent_gain_log10"],
           alpha=0.3, s=8, color="#1f77b4")
ax.set_xlabel("Mean pangenome openness (1 − core fraction) per genus")
ax.set_ylabel("log₁₀(recent gains + 1) per genus")
ax.set_title(f"T1 atlas-wide (n_genera = {len(solid_genera)})\n"
             f"Spearman r = {t1_results[1]['spearman_r']:+.3f} {t1_results[1]['spearman_ci']}")
ax.grid(alpha=0.3)

# Panel B: regulatory vs metabolic
ax = axes[0, 1]
positions = [0, 1]
for cat, color, pos in [("regulatory", "#d62728", 0), ("metabolic", "#2ca02c", 1)]:
    cat_data = next(r for r in t2_results if r["category"] == cat)
    ax.bar(pos, cat_data["spearman_r"],
           yerr=[[cat_data["spearman_r"] - cat_data["spearman_ci"][0]],
                 [cat_data["spearman_ci"][1] - cat_data["spearman_r"]]],
           capsize=8, color=color, alpha=0.7)
ax.set_xticks(positions); ax.set_xticklabels(["regulatory", "metabolic"])
ax.set_ylabel("Spearman r (openness vs class-stratified recent gains)")
ax.set_title("T2 class-stratified")
ax.axhline(0, color="black", lw=0.5); ax.grid(axis="y", alpha=0.3)

# Panel C: Mycobacteriaceae × mycolic
ax = axes[1, 0]
ax.scatter(myco_test["mean_openness"], myco_test["log_mycolic"], alpha=0.6, s=40, color="#9467bd")
ax.set_xlabel("Mean openness per Mycobacteriaceae genus")
ax.set_ylabel("log₁₀(recent mycolic-acid gains + 1)")
ax.set_title(f"T3a Mycobacteriaceae × mycolic (n_genera = {len(myco_test)})\n"
             f"Spearman r = {t3_myco['spearman_r']:+.3f} {t3_myco['spearman_ci']}")
ax.grid(alpha=0.3)

# Panel D: Cyanobacteriia × PSII
ax = axes[1, 1]
ax.scatter(cyano_test["mean_openness"], cyano_test["log_psii"], alpha=0.6, s=40, color="#ff7f0e")
ax.set_xlabel("Mean openness per Cyanobacteriia genus")
ax.set_ylabel("log₁₀(recent PSII gains + 1)")
ax.set_title(f"T3b Cyanobacteriia × PSII (n_genera = {len(cyano_test)})\n"
             f"Spearman r = {t3_cyano['spearman_r']:+.3f} {t3_cyano['spearman_ci']}")
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "p4d4_openness_vs_acquisition.png", dpi=120, bbox_inches="tight")
print(f"Wrote figure", flush=True)

# Diagnostics
diagnostics = {
    "phase": "4", "deliverable": "P4-D4",
    "purpose": "M22 recent-acquisition vs pangenome openness cross-validation",
    "n_species_p1b": int(len(species)),
    "n_species_multi_genome": int(len(multi)),
    "n_genera_with_multi_species": int(len(genus_open)),
    "n_genera_solid_substrate": int(len(solid_genera)),
    "t1_atlas_wide": [{**r, "pearson_ci": list(r["pearson_ci"]),
                       "spearman_ci": list(r["spearman_ci"])} for r in t1_results],
    "t2_class_stratified": [{**r, "pearson_ci": list(r["pearson_ci"]),
                             "spearman_ci": list(r["spearman_ci"])} for r in t2_results],
    "t3_mycobacteriaceae_mycolic": {**t3_myco,
                                     "pearson_ci": list(t3_myco["pearson_ci"]),
                                     "spearman_ci": list(t3_myco["spearman_ci"]),
                                     "n_genera": int(len(myco_test))},
    "t3_cyanobacteriia_psii": {**t3_cyano,
                                "pearson_ci": list(t3_cyano["pearson_ci"]),
                                "spearman_ci": list(t3_cyano["spearman_ci"]),
                                "n_genera": int(len(cyano_test))},
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d4_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"Wrote p4d4_diagnostics.json", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
