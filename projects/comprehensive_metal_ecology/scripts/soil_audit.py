"""
soil_audit.py — Comprehensive full-env vs soil-only comparison audit.

Runs all analyses that can be computed from local files (no Spark needed).
For Spark-dependent analyses, reads pre-computed full-env results and flags
soil-only as "NOT_RUN (requires BERDL)".

Output: data/AUDIT_soil_comparison.csv + report/AUDIT_REPORT.md
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

PROJECT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT))
DATA = PROJECT / "data"
REPORT_DIR = PROJECT / "report"
REPORT_DIR.mkdir(exist_ok=True)

from scripts.pgls_utils import run_pgls, load_tree

TREE = DATA / "gtdb_bac_genus_pruned.tree"
MICROBEATLAS = PROJECT.parent / "microbeatlas_metal_ecology" / "data"

SOIL_ENVS = {"soil", "agricultural", "farm", "field", "paddy", "peatland", "desert", "shrub"}

# ── helpers ──────────────────────────────────────────────────────────────────

def z_score(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def fmt_result(res: dict) -> dict:
    return {
        "n": res.get("n"),
        "beta": round(res.get("beta", float("nan")), 6),
        "SE": round(res.get("SE", float("nan")), 6),
        "p": res.get("p_value", float("nan")),
        "lambda": round(res.get("lambda_est", float("nan")), 4),
        "r2": round(res.get("r2", float("nan")), 4),
    }


def _pgls(df, label, predictor="predictor_z", response="mean_levins_B_std",
          fix_lambda=None, min_n=30):
    """Wrapper that catches errors and returns a uniform dict."""
    try:
        v = df.dropna(subset=[predictor, response]).copy()
        if len(v) < min_n:
            return {"status": f"SKIP (n={len(v)} < {min_n})", "n": len(v)}
        if fix_lambda is not None:
            res = run_pgls(v, TREE, response=response, predictors=[predictor],
                           label=label, fix_lambda=fix_lambda)
        else:
            res = run_pgls(v, TREE, response=response, predictors=[predictor],
                           label=label)
        return {**fmt_result(res), "status": "OK"}
    except Exception as e:
        return {"status": f"ERROR: {e}", "n": len(df)}


# ── Step 0: Build genus sets ──────────────────────────────────────────────────

print("=== Step 0: Building genus sets ===")

otu_env = pd.read_csv(
    MICROBEATLAS / "otu_env_matrix.csv",
    usecols=["otu_id", "Env_Level_1", "n_samples_detected"],
)
otu_link = pd.read_csv(
    MICROBEATLAS / "otu_pangenome_link_v2.csv",
    usecols=["otu_id", "genus_lower"],
).dropna(subset=["genus_lower"])

dom_env = otu_env.loc[
    otu_env.groupby("otu_id")["n_samples_detected"].idxmax(),
    ["otu_id", "Env_Level_1"],
].copy()
dom_env["is_soil"] = dom_env["Env_Level_1"].str.lower().isin(SOIL_ENVS)

otu_genus_env = dom_env.merge(otu_link.drop_duplicates("otu_id"), on="otu_id", how="inner")
genus_soil = (
    otu_genus_env.groupby("genus_lower")["is_soil"]
    .agg(["sum", "count"])
    .assign(frac_soil=lambda x: x["sum"] / x["count"])
    .reset_index()
)
soil_genera = set(genus_soil.loc[genus_soil["frac_soil"] > 0.5, "genus_lower"])

pgls_full = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
pgls_soil = pgls_full[pgls_full["genus_lower"].isin(soil_genera)].copy()
pgls_soil["predictor_z"] = z_score(pgls_soil["ko_per_mb_primary"])

n_full = len(pgls_full)
n_soil = len(pgls_soil)
print(f"Full-env genera: {n_full}")
print(f"Soil-only genera (>50% soil OTUs): {n_soil}")
print(f"Soil phylum breakdown:\n{pgls_soil['phylum'].value_counts().head(8)}\n")

# ── Collect results ───────────────────────────────────────────────────────────

rows = []

def add_row(analysis, dataset, result_dict):
    rows.append({"analysis": analysis, "dataset": dataset, **result_dict})

# ── A1: Primary PGLS ─────────────────────────────────────────────────────────

print("=== A1: Primary PGLS ===")
p1_full = pd.read_csv(DATA / "01_primary_pgls_results.csv")
p1_bac = p1_full[p1_full["label"] == "P1_bacteria_primary"].iloc[0]
add_row("A1_primary_pgls", "full_env", {
    "n": int(p1_bac["n"]), "beta": float(p1_bac["beta"]), "SE": float(p1_bac["SE"]),
    "p": float(p1_bac["p_value"]), "lambda": float(p1_bac["lambda_est"]),
    "r2": float(p1_bac["r2"]), "status": "OK (pre-computed)",
})

p1_soil_pre = pd.read_csv(DATA / "01_soil_restricted_pgls_results.csv").iloc[0]
add_row("A1_primary_pgls", "soil_only", {
    "n": int(p1_soil_pre["n"]), "beta": float(p1_soil_pre["beta"]),
    "SE": float(p1_soil_pre["SE"]), "p": float(p1_soil_pre["p_value"]),
    "lambda": float(p1_soil_pre["lambda_est"]), "r2": float(p1_soil_pre["r2"]),
    "status": "OK (pre-computed)",
})
print(f"  full β={float(p1_bac['beta']):.4f} p={float(p1_bac['p_value']):.2e} n={int(p1_bac['n'])}")
print(f"  soil β={float(p1_soil_pre['beta']):.4f} p={float(p1_soil_pre['p_value']):.2e} n={int(p1_soil_pre['n'])}\n")

# ── A2: AusMicrobiome replication ─────────────────────────────────────────────

print("=== A2: AusMicrobiome density replication ===")
aus = pd.read_csv(DATA / "pgls_ausmicrobiome_density_replication.csv").iloc[0]
add_row("A2_ausmicrobiome_density", "full_env", {
    "n": int(aus["n"]), "beta": float(aus["beta"]), "SE": float(aus["SE"]),
    "p": float(aus["p_value"]), "lambda": float(aus["lambda_est"]),
    "r2": float(aus["r2"]), "status": "OK (pre-computed, already soil-biased)",
})
aus_soil = pd.read_csv(DATA / "02_p3b_soil_pgls_results.csv").iloc[0]
add_row("A2_ausmicrobiome_density", "soil_only", {
    "n": int(aus_soil["n"]), "beta": float(aus_soil["beta"]), "SE": float(aus_soil["SE"]),
    "p": float(aus_soil["p_value"]), "lambda": float(aus_soil["lambda_est"]),
    "r2": float(aus_soil["r2"]), "status": "OK (pre-computed, soil genera only)",
})
print(f"  AusMicrobiome full β={float(aus['beta']):.4f} p={float(aus['p_value']):.2e} n={int(aus['n'])}")
print(f"  AusMicrobiome soil β={float(aus_soil['beta']):.4f} p={float(aus_soil['p_value']):.2e} n={int(aus_soil['n'])}\n")

# ── A3: NGSA proper replication ───────────────────────────────────────────────

print("=== A3: NGSA proper replication ===")
ngsa = pd.read_csv(DATA / "ngsa_replication_proper_comprehensive.csv")
for _, row in ngsa.iterrows():
    add_row(f"A3_ngsa_{row['metal']}", "full_env", {
        "n": int(row["n_genera"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p_raw"]), "lambda": float(row["lambda_est"]),
        "r2": float("nan"), "status": "OK (pre-computed, AusMicrobiome soil)",
    })
    # NGSA already soil-restricted by nature — flag
    add_row(f"A3_ngsa_{row['metal']}", "soil_only", {
        "n": int(row["n_genera"]), "beta": float("nan"), "SE": float("nan"),
        "p": float("nan"), "lambda": float("nan"), "r2": float("nan"),
        "status": "NOT_APPLICABLE (NGSA already soil dataset)",
    })

# ── A4: Category breakdown ────────────────────────────────────────────────────

print("=== A4: Category breakdown ===")
cat = pd.read_csv(DATA / "03_category_pgls_results.csv")
for _, row in cat.iterrows():
    add_row(f"A4_category_{row['label']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p_value"]), "lambda": float(row["lambda_est"]),
        "r2": float(row["r2"]), "status": "OK (pre-computed)",
    })
    add_row(f"A4_category_{row['label']}", "soil_only", {
        "n": float("nan"), "beta": float("nan"), "SE": float("nan"),
        "p": float("nan"), "lambda": float("nan"), "r2": float("nan"),
        "status": "NOT_RUN (requires BERDL Spark for category KO subsets)",
    })

# ── A5: Tier breakdown ────────────────────────────────────────────────────────

print("=== A5: Tier breakdown ===")
tier = pd.read_csv(DATA / "03_tier_pgls_results.csv")
for _, row in tier.iterrows():
    add_row(f"A5_tier_{row['label']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p_value"]), "lambda": float(row["lambda_est"]),
        "r2": float(row["r2"]), "status": "OK (pre-computed)",
    })
    add_row(f"A5_tier_{row['label']}", "soil_only", {
        "n": float("nan"), "beta": float("nan"), "SE": float("nan"),
        "p": float("nan"), "lambda": float("nan"), "r2": float("nan"),
        "status": "NOT_RUN (requires BERDL Spark for tier KO subsets)",
    })

# ── A6: Per-metal PGLS ───────────────────────────────────────────────────────

print("=== A6: Per-metal PGLS ===")
metal = pd.read_csv(DATA / "03_metal_pgls_results.csv")
for _, row in metal.iterrows():
    add_row(f"A6_metal_{row['label']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p_value"]), "lambda": float(row["lambda_est"]),
        "r2": float(row["r2"]), "status": "OK (pre-computed)",
    })
    add_row(f"A6_metal_{row['label']}", "soil_only", {
        "n": float("nan"), "beta": float("nan"), "SE": float("nan"),
        "p": float("nan"), "lambda": float("nan"), "r2": float("nan"),
        "status": "NOT_RUN (requires BERDL Spark for per-metal KO subsets)",
    })

# ── A7: Confounder checks ─────────────────────────────────────────────────────

print("=== A7: Confounder checks ===")
conf = pd.read_csv(DATA / "04_confounder_results.csv")
for _, row in conf.iterrows():
    add_row(f"A7_confounder_{row['confounder'].replace(' ','_')}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta_with_conf"]), "SE": float("nan"),
        "p": float(row["p_with_conf"]), "lambda": float("nan"),
        "r2": float("nan"), "status": "OK (pre-computed)",
    })

# Load latitude covariate for soil-only confounder checks
print("  Running soil-only confounder checks ...")
lat_df = pd.read_csv(DATA / "genus_lat_env_covariates.csv",
                     usecols=["genus_lower", "lat_abs", "median_era5_temp_C"])

# Genome size confounder
soil_conf = pgls_soil.merge(lat_df, on="genus_lower", how="left")
soil_conf["genome_mb_z"] = z_score(soil_conf["mean_genome_mb"])
soil_conf["lat_z"] = z_score(soil_conf["lat_abs"].dropna() if "lat_abs" in soil_conf else pd.Series())

# A7.1 Genome size
df_ = soil_conf.dropna(subset=["predictor_z", "mean_levins_B_std", "genome_mb_z"]).copy()
try:
    r = run_pgls(df_, TREE, "mean_levins_B_std", ["predictor_z", "genome_mb_z"],
                 label="soil_genome_size")
    add_row("A7_confounder_Genome_size", "soil_only", {
        "n": r["n"], "beta": round(r["betas"].get("predictor_z", float("nan")), 6),
        "SE": round(r["SEs"].get("predictor_z", float("nan")), 6),
        "p": r["p_values"].get("predictor_z", float("nan")),
        "lambda": round(r["lambda_est"], 4), "r2": round(r.get("r2", float("nan")), 4),
        "status": "OK",
    })
    print(f"  Genome size soil: β_metal={r['betas'].get('predictor_z', float('nan')):.4f} p={r['p_values'].get('predictor_z', float('nan')):.3f}")
except Exception as e:
    add_row("A7_confounder_Genome_size", "soil_only", {"n": len(df_), "status": f"ERROR: {e}"})

# A7.2 Latitude
df_ = soil_conf.dropna(subset=["predictor_z", "mean_levins_B_std", "lat_abs"]).copy()
df_["lat_z"] = z_score(df_["lat_abs"])
try:
    r = run_pgls(df_, TREE, "mean_levins_B_std", ["predictor_z", "lat_z"],
                 label="soil_latitude")
    add_row("A7_confounder_Mean_latitude", "soil_only", {
        "n": r["n"], "beta": round(r["betas"].get("predictor_z", float("nan")), 6),
        "SE": round(r["SEs"].get("predictor_z", float("nan")), 6),
        "p": r["p_values"].get("predictor_z", float("nan")),
        "lambda": round(r["lambda_est"], 4), "r2": round(r.get("r2", float("nan")), 4),
        "status": "OK",
    })
    print(f"  Latitude soil: β_metal={r['betas'].get('predictor_z', float('nan')):.4f} p={r['p_values'].get('predictor_z', float('nan')):.3f}")
except Exception as e:
    add_row("A7_confounder_Mean_latitude", "soil_only", {"n": len(df_), "status": f"ERROR: {e}"})

# A7.3 Dominant biome (soil ↔ env is the classification variable; skip as tautological)
add_row("A7_confounder_Dominant_biome", "soil_only", {
    "n": n_soil, "beta": float("nan"), "SE": float("nan"),
    "p": float("nan"), "lambda": float("nan"), "r2": float("nan"),
    "status": "NOT_APPLICABLE (soil-only set is uniform for biome)",
})

# A7.4 GC content — need separate file
add_row("A7_confounder_GC_content", "soil_only", {
    "n": float("nan"), "beta": float("nan"), "SE": float("nan"),
    "p": float("nan"), "lambda": float("nan"), "r2": float("nan"),
    "status": "NOT_RUN (GC content data not in local joined file)",
})

# A7.5 Isolation source — binary env text flag; soil already stratified
add_row("A7_confounder_Isolation_source", "soil_only", {
    "n": n_soil, "beta": float("nan"), "SE": float("nan"),
    "p": float("nan"), "lambda": float("nan"), "r2": float("nan"),
    "status": "NOT_APPLICABLE (soil-only set controls isolation source by design)",
})

# ── A8: Sensitivity analyses ──────────────────────────────────────────────────

print("=== A8: Sensitivity analyses ===")
sens = pd.read_csv(DATA / "05_sensitivity_results.csv")
for _, row in sens.iterrows():
    add_row(f"A8_sensitivity_{row['label']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p_value"]), "lambda": float(row["lambda_est"]),
        "r2": float(row["r2"]), "status": "OK (pre-computed)",
    })

# Run S1 (λ=0) and S2 (λ=1) for soil
for lam, label in [(0.0, "S1_lambda0"), (1.0, "S2_lambda1")]:
    r = _pgls(pgls_soil, f"soil_{label}", fix_lambda=lam)
    add_row(f"A8_sensitivity_{label}", "soil_only", {**r})
    print(f"  {label} soil: {r}")

# S3 archaea — skip (no soil archaea set available)
add_row("A8_sensitivity_S3_archaea", "soil_only", {
    "n": float("nan"), "status": "NOT_APPLICABLE (soil archaea n too small)",
})

# S4/S5 sample depth — essentially same as P1 soil (sample depth criteria already met)
niche_s = pd.read_csv(DATA / "niche_breadth_sensitivity.csv")
for thresh in [10, 20, 50]:
    label = f"S{4 if thresh==10 else (5 if thresh==20 else 'X')}_min{thresh}"
    soil_filt = pgls_soil.copy()
    sample_counts = pd.read_csv(DATA / "genus_microbeatlas_sample_counts.csv")
    soil_filt = soil_filt.merge(sample_counts, on="genus_lower", how="inner")
    soil_filt = soil_filt[soil_filt["n_samples"] >= thresh].copy()
    soil_filt["predictor_z"] = z_score(soil_filt["ko_per_mb_primary"])
    r = _pgls(soil_filt, f"soil_sample_depth_{thresh}")
    add_row(f"A8_sensitivity_sample_depth_{thresh}", "full_env", {
        "n": niche_s[niche_s["analysis"] == f"sample_depth_{thresh}"]["n_genera"].values[0]
             if f"sample_depth_{thresh}" in niche_s["analysis"].values else n_full,
        "beta": niche_s[niche_s["analysis"] == f"sample_depth_{thresh}"]["beta"].values[0]
                if f"sample_depth_{thresh}" in niche_s["analysis"].values else p1_bac["beta"],
        "status": "OK (pre-computed)",
    })
    add_row(f"A8_sensitivity_sample_depth_{thresh}", "soil_only", {**r})
    print(f"  Sample depth {thresh} soil: n={r.get('n')} β={r.get('beta', 'err')}")

# S6 raw Levins B
pgls_soil_raw = pgls_soil.copy()
pgls_full_b = pd.read_csv(DATA / "genus_bootstrap_niche.csv",
                           usecols=["genus_lower", "mean_levins_B_std", "n_otus"])
# Need raw B — compute from boot data (not available separately), skip
add_row("A8_sensitivity_S6_raw_levinsB", "soil_only", {
    "n": float("nan"), "status": "NOT_RUN (raw Levins B not in soil input file)",
})

# ── A9: Clade stratification ──────────────────────────────────────────────────

print("=== A9: Clade stratification ===")
clade = pd.read_csv(DATA / "clade_stratified_pgls_results.csv")
for _, row in clade.iterrows():
    add_row(f"A9_clade_{row['label']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p"]), "lambda": float(row["lambda_est"]),
        "r2": float(row.get("r2", float("nan"))), "status": "OK (pre-computed)",
    })

phyla_to_run = ["Firmicutes", "Actinobacteria", "Proteobacteria", "Bacteroidetes"]
for phylum in phyla_to_run:
    soil_p = pgls_soil[pgls_soil["phylum"] == phylum].copy()
    soil_p["predictor_z"] = z_score(soil_p["ko_per_mb_primary"])
    r = _pgls(soil_p, f"soil_{phylum}", min_n=20)
    add_row(f"A9_clade_{phylum}", "soil_only", {**r})
    print(f"  {phylum} soil: n={r.get('n')} β={r.get('beta', 'err')} p={r.get('p', 'err')}")

# ── A10: Cofactor jackknife ───────────────────────────────────────────────────

print("=== A10: Cofactor jackknife ===")
jk = pd.read_csv(DATA / "cofactor_jackknife_results.csv")
for _, row in jk.iterrows():
    add_row(f"A10_cofactor_jk_excl_{row['excluded_ko']}", "full_env", {
        "n": int(row["n_kos_remaining"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p"]), "lambda": float("nan"), "r2": float("nan"),
        "status": "OK (pre-computed)",
    })
    add_row(f"A10_cofactor_jk_excl_{row['excluded_ko']}", "soil_only", {
        "status": "NOT_RUN (requires BERDL Spark for cofactor-only KO subset)",
    })

# ── A11: Coreness permutation ─────────────────────────────────────────────────

print("=== A11: Coreness permutation ===")
perm = pd.read_csv(DATA / "coreness_permutation_results.csv")
obs_beta = -0.020700
perm_betas = perm["beta"].values
emp_p = (np.sum(perm_betas <= obs_beta) / len(perm_betas))
add_row("A11_coreness_permutation", "full_env", {
    "n": int(perm["n_genera"].iloc[0]), "beta": obs_beta,
    "SE": float("nan"), "p": float(emp_p),
    "lambda": float("nan"), "r2": float("nan"),
    "status": f"OK (pre-computed; empirical p={emp_p:.4f} from 1000 perms)",
})
add_row("A11_coreness_permutation", "soil_only", {
    "status": "NOT_RUN (1000-perm full coreness sweep; requires re-run for soil)",
})

# ── A12: Negative controls ────────────────────────────────────────────────────

print("=== A12: Negative controls ===")
nc_df = pd.read_csv(DATA / "negative_control_pgls_results.csv")
nc_named = nc_df[nc_df["control_type"] == "named_negative_control"]

nc_files = {
    "ribosomal_proteins": "nc_ribosomal_proteins_density.csv",
    "aa_biosynthesis":    "nc_aa_biosynthesis_density.csv",
    "dna_repair":         "nc_dna_repair_density.csv",
}

for nc_name, nc_file in nc_files.items():
    row = nc_named[nc_named["label"] == nc_name]
    if len(row):
        add_row(f"A12_negctrl_{nc_name}", "full_env", {
            "n": int(row.iloc[0]["n_genera"]), "beta": float(row.iloc[0]["beta"]),
            "SE": float(row.iloc[0]["SE"]), "p": float(row.iloc[0]["p_parametric"]),
            "lambda": float(row.iloc[0]["lambda_est"]), "r2": float("nan"),
            "status": "OK (pre-computed)",
        })

    nc_dens = pd.read_csv(DATA / nc_file)
    soil_nc = nc_dens[nc_dens["genus_lower"].isin(soil_genera)].copy()
    merged = pgls_soil[["genus_lower", "mean_levins_B_std", "phylum"]].merge(
        soil_nc[["genus_lower", "ko_per_mb"]], on="genus_lower", how="inner")
    merged["predictor_z"] = z_score(merged["ko_per_mb"])
    r = _pgls(merged, f"soil_nc_{nc_name}", min_n=30)
    add_row(f"A12_negctrl_{nc_name}", "soil_only", {**r})
    print(f"  {nc_name} soil: n={r.get('n')} β={r.get('beta', 'err')} p={r.get('p', 'err')}")

# ── A13: MAG quality sensitivity ─────────────────────────────────────────────

print("=== A13: MAG quality sensitivity ===")
mq = pd.read_csv(DATA / "mag_quality_sensitivity.csv")
for _, row in mq.iterrows():
    add_row(f"A13_mag_quality_{row['model']}", "full_env", {
        "n": int(row["n_genera"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p"]), "lambda": float(row["lambda_est"]),
        "r2": float("nan"), "status": "OK (pre-computed)",
    })

mag_q = pd.read_csv(DATA / "genus_mag_quality.csv")
if "genus_lower" not in mag_q.columns:
    mag_q = mag_q.rename(columns={"genus": "genus_lower"})
mag_q["genus_lower"] = mag_q["genus_lower"].astype(str).str.lower().str.strip()
soil_mq = pgls_soil.merge(
    mag_q[["genus_lower", "mean_completeness", "mean_contamination"]],
    on="genus_lower", how="inner",
)
soil_mq["completeness_z"] = z_score(soil_mq["mean_completeness"])
soil_mq["contamination_z"] = z_score(soil_mq["mean_contamination"])

# Baseline with MAG-quality genera
soil_mq["predictor_z"] = z_score(soil_mq["ko_per_mb_primary"])
r = _pgls(soil_mq, "soil_mq_baseline")
add_row("A13_mag_quality_baseline", "soil_only", {**r})
print(f"  MAG quality baseline soil: n={r.get('n')} β={r.get('beta', 'err')}")

# Completeness covariate
df_ = soil_mq.dropna(subset=["predictor_z", "mean_levins_B_std", "completeness_z"]).copy()
try:
    r2 = run_pgls(df_, TREE, "mean_levins_B_std", ["predictor_z", "completeness_z"],
                  label="soil_completeness")
    add_row("A13_mag_quality_completeness_covariate", "soil_only", {
        "n": r2["n"],
        "beta": round(r2["betas"].get("predictor_z", float("nan")), 6),
        "SE": round(r2["SEs"].get("predictor_z", float("nan")), 6),
        "p": r2["p_values"].get("predictor_z", float("nan")),
        "lambda": round(r2["lambda_est"], 4), "r2": round(r2.get("r2", float("nan")), 4),
        "status": "OK",
    })
    print(f"  Completeness covariate soil: β_metal={r2['betas'].get('predictor_z', float('nan')):.4f}")
except Exception as e:
    add_row("A13_mag_quality_completeness_covariate", "soil_only",
            {"n": len(df_), "status": f"ERROR: {e}"})

# HQ restricted (≥90% complete, ≤5% contamination)
hq = soil_mq[
    (soil_mq["mean_completeness"] >= 90) & (soil_mq["mean_contamination"] <= 5)
].copy()
if len(hq) >= 30:
    hq["predictor_z"] = z_score(hq["ko_per_mb_primary"])
    r3 = _pgls(hq, "soil_hq_restricted")
    add_row("A13_mag_quality_hq_restricted", "soil_only", {**r3})
    print(f"  HQ-restricted soil: n={r3.get('n')} β={r3.get('beta', 'err')}")
else:
    add_row("A13_mag_quality_hq_restricted", "soil_only",
            {"n": len(hq), "status": f"SKIP (n={len(hq)} < 30 after HQ filter)"})

# ── A14: Niche breadth sensitivity ───────────────────────────────────────────

print("=== A14: Niche breadth sensitivity ===")
ns = pd.read_csv(DATA / "niche_breadth_sensitivity.csv")
for _, row in ns.iterrows():
    add_row(f"A14_niche_{row['analysis']}", "full_env", {
        "n": int(row["n_genera"]), "beta": float(row["beta"]),
        "SE": float(row["SE"]) if pd.notna(row["SE"]) else float("nan"),
        "p": float(row["p_value"]), "lambda": float(row["lambda_est"])
              if pd.notna(row["lambda_est"]) else float("nan"),
        "r2": float("nan"), "status": row["status"],
    })

# Bootstrap mean B_std: use existing boot data
boot = pd.read_csv(DATA / "genus_bootstrap_niche.csv",
                   usecols=["genus_lower", "boot_mean_B_std"])
soil_boot = pgls_soil.merge(boot, on="genus_lower", how="inner")
soil_boot["predictor_z"] = z_score(soil_boot["ko_per_mb_primary"])
r_boot = _pgls(soil_boot.rename(columns={"boot_mean_B_std": "_resp"}),
               "soil_bootstrap", response="_resp")
add_row("A14_niche_bootstrap_mean_B_std", "soil_only", {**r_boot})
print(f"  Bootstrap niche soil: n={r_boot.get('n')} β={r_boot.get('beta', 'err')}")

# ── A15: BacDive niche validation ─────────────────────────────────────────────

print("=== A15: BacDive validation ===")
bac_pre = pd.read_csv(DATA / "bacdive_niche_pgls_comprehensive.csv").iloc[0]
add_row("A15_bacdive", "full_env", {
    "n": int(bac_pre["n"]), "beta": float(bac_pre["beta"]), "SE": float(bac_pre["SE"]),
    "p": float(bac_pre["p_value"]), "lambda": float(bac_pre["lambda_est"]),
    "r2": float(bac_pre["r2"]), "status": "OK (pre-computed; NOTE β positive)",
})

bac_input = pd.read_csv(DATA / "bacdive_niche_pgls_input.csv")
soil_bac = bac_input[bac_input["genus_lower"].isin(soil_genera)].copy()
soil_bac["predictor_z"] = z_score(soil_bac["ko_per_mb_primary"])
r_bac = _pgls(soil_bac, "soil_bacdive", response="bacdive_B_std")
add_row("A15_bacdive", "soil_only", {**r_bac})
print(f"  BacDive soil: n={r_bac.get('n')} β={r_bac.get('beta', 'err')} p={r_bac.get('p', 'err')}")

# ── A16: EMP niche validation ─────────────────────────────────────────────────

print("=== A16: EMP validation ===")
emp_pre = pd.read_csv(DATA / "emp_niche_pgls_comprehensive.csv").iloc[0]
add_row("A16_emp", "full_env", {
    "n": int(emp_pre["n"]), "beta": float(emp_pre["beta"]), "SE": float(emp_pre["SE"]),
    "p": float(emp_pre["p_value"]), "lambda": float(emp_pre["lambda_est"]),
    "r2": float(emp_pre["r2"]), "status": "OK (pre-computed; p=0.099, trend only)",
})

emp_input = pd.read_csv(DATA / "emp_niche_pgls_input.csv")
soil_emp = emp_input[emp_input["genus_lower"].isin(soil_genera)].copy()
if "ko_per_mb_primary" not in soil_emp.columns:
    # Merge primary KO density from full input
    soil_emp = soil_emp.merge(pgls_full[["genus_lower", "ko_per_mb_primary"]],
                              on="genus_lower", how="inner")
soil_emp["predictor_z"] = z_score(soil_emp["ko_per_mb_primary"])
r_emp = _pgls(soil_emp, "soil_emp", response="emp_levins_B_std")
add_row("A16_emp", "soil_only", {**r_emp})
print(f"  EMP soil: n={r_emp.get('n')} β={r_emp.get('beta', 'err')} p={r_emp.get('p', 'err')}")

# ── A17: Comparator PGLS ─────────────────────────────────────────────────────

print("=== A17: Comparator PGLS ===")
comp = pd.read_csv(DATA / "comparator_pgls_results.csv")
for _, row in comp.iterrows():
    add_row(f"A17_comparator_{row['comparator']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["metal_beta"]), "SE": float(row["metal_SE"]),
        "p": float(row["metal_p"]), "lambda": float(row["lambda_est"]),
        "r2": float("nan"), "status": "OK (pre-computed)",
    })
    add_row(f"A17_comparator_{row['comparator']}", "soil_only", {
        "status": "NOT_RUN (requires BERDL Spark for comparator KO density)",
    })

# ── A18: Inverse PGLS ────────────────────────────────────────────────────────

print("=== A18: Inverse PGLS ===")
inv = pd.read_csv(DATA / "inverse_pgls_results.csv")
for _, row in inv.iterrows():
    add_row(f"A18_inverse_{row['label']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p_value"]), "lambda": float(row["lambda_est"]),
        "r2": float(row["r2"]), "status": "OK (pre-computed)",
    })
    add_row(f"A18_inverse_{row['label']}", "soil_only", {
        "status": "NOT_RUN (inverse PGLS uses environmental covariate data)",
    })

# ── A19: Internal structure ───────────────────────────────────────────────────

print("=== A19: Internal structure ===")
internal = pd.read_csv(DATA / "internal_structure_results.csv")
for _, row in internal.iterrows():
    add_row(f"A19_internal_{row['parent_category']}_{row['subcategory'][:20]}", "full_env", {
        "n": int(row["n_genera"]), "beta": float(row["beta"]), "SE": float(row["SE"]),
        "p": float(row["p_raw"]), "lambda": float(row["lambda_est"]),
        "r2": float(row["partial_R2"]), "status": "OK (pre-computed)",
    })
    add_row(f"A19_internal_{row['parent_category']}_{row['subcategory'][:20]}", "soil_only", {
        "status": "NOT_RUN (requires BERDL Spark for subcategory KO subsets)",
    })

# ── A20: Latitude mechanism ───────────────────────────────────────────────────

print("=== A20: Latitude mechanism ===")
lat_mech = pd.read_csv(DATA / "latitude_mechanism_results.csv")
# Just record the first core model (A_metal_lat) for brevity
for model_label in ["A_metal_lat", "B_metal_lat_georoc"]:
    row_ = lat_mech[lat_mech["model"] == model_label]
    if len(row_):
        r_ = row_.iloc[0]
        add_row(f"A20_lat_mech_{model_label}", "full_env", {
            "n": int(r_["n_pgls"]), "beta": float(r_["beta_metal"]), "SE": float(r_["SE_metal"]),
            "p": float(r_["p_metal"]), "lambda": float(r_["lambda_est"]),
            "r2": float("nan"), "status": "OK (pre-computed)",
        })
        add_row(f"A20_lat_mech_{model_label}", "soil_only", {
            "status": "NOT_RUN (lat mechanism requires GeoROC/env covariates for soil subset)",
        })

# ── A21: Functional landscape ────────────────────────────────────────────────

print("=== A21: Functional landscape ===")
fl = pd.read_csv(DATA / "functional_landscape_results.csv")
add_row("A21_functional_landscape_summary", "full_env", {
    "n": int(fl[fl["category"] == "metal_genes_p1"]["n_genera"].iloc[0]),
    "beta": float(fl[fl["category"] == "metal_genes_p1"]["beta"].iloc[0]),
    "SE": float(fl[fl["category"] == "metal_genes_p1"]["SE"].iloc[0]),
    "p": float(fl[fl["category"] == "metal_genes_p1"]["p_raw"].iloc[0]),
    "lambda": float("nan"), "r2": float("nan"),
    "status": f"OK (20 KEGG cats tested; metal P1 reference shown)",
})
add_row("A21_functional_landscape_summary", "soil_only", {
    "status": "NOT_RUN (requires BERDL Spark for 20 KEGG category KO densities)",
})

# ── A22: Interaction test ─────────────────────────────────────────────────────

print("=== A22: Interaction test ===")
inter = pd.read_csv(DATA / "interaction_test_results.csv")
r_cofactor = inter[inter["model"] == "separate_cofactor"].iloc[0]
add_row("A22_interaction_cofactor_vs_resistance", "full_env", {
    "n": float("nan"),
    "beta": float(r_cofactor["beta"]), "SE": float(r_cofactor["SE"]),
    "p": float(r_cofactor["p"]), "lambda": float("nan"), "r2": float("nan"),
    "status": "OK (pre-computed; cofactor β significant, resistance NS)",
})
add_row("A22_interaction_cofactor_vs_resistance", "soil_only", {
    "status": "NOT_RUN (requires BERDL Spark for category-specific KO subsets)",
})

# ── A23: ENIGMA FRC replication ───────────────────────────────────────────────

print("=== A23: ENIGMA FRC replication ===")
enigma = pd.read_csv(DATA / "enigma_frc_replication.csv")
for _, row in enigma.iterrows():
    add_row(f"A23_enigma_{row['metal']}_{row['level']}", "full_env", {
        "n": int(row["n_mags"]) if pd.notna(row["n_mags"]) else float("nan"),
        "beta": float(row["rho"]), "SE": float("nan"),
        "p": float(row["p_two_tailed"]), "lambda": float("nan"), "r2": float("nan"),
        "status": "OK (pre-computed; Spearman rho, not PGLS)",
    })
    add_row(f"A23_enigma_{row['metal']}_{row['level']}", "soil_only", {
        "status": "NOT_APPLICABLE (ENIGMA FRC = specific groundwater site, not soil-biome sens.)",
    })

# ── A24: Category conditional models ─────────────────────────────────────────

print("=== A24: Category conditional models ===")
cond = pd.read_csv(DATA / "category_conditional_models.csv")
for _, row in cond.iterrows():
    add_row(f"A24_cond_{row['model']}", "full_env", {
        "n": int(row["n"]), "beta": float(row["beta_density"]), "SE": float(row["SE"]),
        "p": float(row["p"]), "lambda": float(row["lambda_est"]),
        "r2": float("nan"), "status": "OK (pre-computed)",
    })
    add_row(f"A24_cond_{row['model']}", "soil_only", {
        "status": "NOT_RUN (requires BERDL Spark for annotation-depth KO counts)",
    })

# ── A25: BacDive geographic niche (alternative) ───────────────────────────────

print("=== A25: BacDive geographic niche ===")
bac_geo = pd.read_csv(DATA / "bacdive_geocat_pgls.csv").iloc[0]
add_row("A25_bacdive_geocat", "full_env", {
    "n": int(bac_geo["n"]), "beta": float(bac_geo["beta"]), "SE": float(bac_geo["SE"]),
    "p": float(bac_geo["p_value"]), "lambda": float(bac_geo["lambda_est"]),
    "r2": float(bac_geo["r2"]), "status": "OK (pre-computed; n_countries as niche proxy)",
})
bac_geo_input = pd.read_csv(DATA / "bacdive_genus_country_counts.csv")
soil_bg = bac_geo_input[bac_geo_input["genus_lower"].isin(soil_genera)].merge(
    pgls_soil[["genus_lower", "ko_per_mb_primary", "phylum"]], on="genus_lower", how="inner")
soil_bg["predictor_z"] = z_score(soil_bg["ko_per_mb_primary"])
soil_bg["n_countries_std"] = z_score(soil_bg["n_countries"])
r_bg = _pgls(soil_bg, "soil_bacdive_geocat", response="n_countries_std")
add_row("A25_bacdive_geocat", "soil_only", {**r_bg})
print(f"  BacDive geocat soil: n={r_bg.get('n')} β={r_bg.get('beta', 'err')} p={r_bg.get('p', 'err')}")

# ── Save results ──────────────────────────────────────────────────────────────

results_df = pd.DataFrame(rows)
results_df.to_csv(DATA / "AUDIT_soil_comparison.csv", index=False)
print(f"\nSaved AUDIT_soil_comparison.csv ({len(results_df)} rows)")

# ── Print summary table ───────────────────────────────────────────────────────

print("\n=== SUMMARY: analyses run for both datasets ===")
pivot = results_df[results_df["status"] == "OK"].pivot_table(
    index="analysis", columns="dataset", values=["n", "beta", "p"], aggfunc="first"
)
print(pivot.to_string())
