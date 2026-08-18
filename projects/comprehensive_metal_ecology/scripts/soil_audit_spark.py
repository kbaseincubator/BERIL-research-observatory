#!/usr/bin/env python3
"""soil_audit_spark.py — Spark-dependent soil-only analyses for the audit.

Runs A4 (category), A5 (tier), A6 (per-metal), A10 (cofactor jackknife),
A17 (comparator), A21 (functional landscape), A22 (interaction), and
A24 (conditional models) for the soil-restricted genus set (n≈162).

A17 and A21 reuse existing landscape density CSVs (no new Spark queries).
A4, A5, A6, A10, A22 require Spark → kescience_mgnify.

Outputs: appends/replaces soil_only rows in data/AUDIT_soil_comparison.csv.
Run on-cluster (no proxy needed).
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")

PROJECT = Path(__file__).resolve().parent.parent
DATA    = PROJECT / "data"
TREE    = DATA / "gtdb_bac_genus_pruned.tree"
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "scripts"))

import numpy as np
import pandas as pd
from scripts.pgls_utils import run_pgls
from scripts.gene_list_utils import (
    load_gene_list, get_ko_set, get_metal_subset, list_metals_with_min_kos
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _z(s):
    return (s - s.mean()) / s.std()

# ── Spark ─────────────────────────────────────────────────────────────────────
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()
print("Spark ready")

# ── Soil genus set ────────────────────────────────────────────────────────────
soil_frac   = pd.read_csv(DATA / "genus_soil_fraction.csv")
soil_genera = set(soil_frac.loc[soil_frac["frac_soil"] > 0.5, "genus_lower"])
print(f"Soil genera: {len(soil_genera)}")

# ── PGLS trait data ───────────────────────────────────────────────────────────
bac_base = pd.read_csv(DATA / "01_pgls_input_bacteria.csv")
pgls_soil = bac_base[bac_base["genus_lower"].isin(soil_genera)].copy()
pgls_soil["predictor_z"] = _z(pgls_soil["ko_per_mb_primary"])
pgls_soil["genome_mb_z"] = _z(pgls_soil["mean_genome_mb"])
print(f"Soil PGLS input: {len(pgls_soil)} genera")

# ── Gene list ─────────────────────────────────────────────────────────────────
gene_df = load_gene_list(DATA / "curated_mrg_ko_ids_v2.csv")


def spark_density(ko_ids):
    """Per-genus mean KO density (distinct KOs / Mb) from kescience_mgnify."""
    ko_prefixed = [f"ko:{k}" for k in ko_ids]
    quoted = ", ".join(f"'{k}'" for k in ko_prefixed)
    sql = f"""
        SELECT gm.genome_id,
               regexp_extract(gm.lineage, 'g__([^;]+)', 1) AS genus,
               COUNT(DISTINCT koid.ko)                      AS n_ko,
               gm.length                                    AS genome_length_bp
        FROM kescience_mgnify.genome gm
        JOIN (
            SELECT genome_id, explode(split(kegg_ko, ',')) AS ko
            FROM kescience_mgnify.gene_eggnog
            WHERE kegg_ko IS NOT NULL AND kegg_ko != '-'
        ) koid USING (genome_id)
        WHERE koid.ko IN ({quoted})
        GROUP BY gm.genome_id, gm.lineage, gm.length
    """
    pm = spark.sql(sql).toPandas()
    pm["genus_lower"] = pm["genus"].str.lower().str.strip()
    pm["ko_per_mb"]   = pm["n_ko"] / (pm["genome_length_bp"] / 1e6)
    return pm.groupby("genus_lower", as_index=False).agg(
        ko_per_mb=("ko_per_mb", "mean"), n_mags=("genome_id", "count")
    )


def soil_pgls(density_df, label, response="mean_levins_B_std", min_n=20):
    """Merge density with soil pgls_soil, re-z-score, run PGLS. Returns result dict."""
    merged = pgls_soil.merge(
        density_df[["genus_lower", "ko_per_mb"]], on="genus_lower", how="inner"
    ).copy()
    merged["predictor_z"] = (merged["ko_per_mb"] - merged["ko_per_mb"].mean()) / merged["ko_per_mb"].std()
    valid = merged.dropna(subset=["predictor_z", response])
    if len(valid) < min_n:
        return {"label": label, "n": len(valid),
                "status": f"SKIPPED (n={len(valid)} < {min_n})"}
    return run_pgls(valid, TREE, response=response, predictors=["predictor_z"],
                    taxon_col="genus_lower", label=label, min_n=min_n)


def extract1(res):
    """Pull scalar beta/SE/p/lambda from single-predictor result dict."""
    return (res.get("beta", float("nan")),
            res.get("SE", float("nan")),
            res.get("p_value", float("nan")),
            res.get("lambda_est", float("nan")),
            res.get("n", float("nan")),
            res.get("r2", float("nan")),
            res.get("status", "OK"))


# ── Accumulate results ────────────────────────────────────────────────────────
existing = pd.read_csv(DATA / "AUDIT_soil_comparison.csv")
new_rows = []

TARGET_PREFIXES = ("A4_", "A5_", "A6_", "A10_", "A17_", "A21_", "A22_", "A24_")

def add(analysis, beta, SE, p, lam, n, r2, status="OK"):
    new_rows.append({"analysis": analysis, "dataset": "soil_only",
                     "n": n, "beta": beta, "SE": SE, "p": p,
                     "lambda": lam, "r2": r2, "status": status})


# ═══════════════════════════════════════════════════════════════════════════════
# A4 – Category breakdown
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A4: Category breakdown ===")
for cat_name, tag in [("resistance", "F1.1"), ("transport", "F1.2"),
                       ("sensing",    "F1.3"), ("cofactor", "F1.4"),
                       ("metabolism", "F1.5")]:
    density = spark_density(get_ko_set(cat_name, gene_df))
    res = soil_pgls(density, f"A4_{tag}_{cat_name}_soil")
    beta, SE, p, lam, n, r2, status = extract1(res)
    print(f"  {cat_name:12s}: n={n}, β={beta:.4f}, p={p:.3e}")
    add(f"A4_category_{tag}_{cat_name}", beta, SE, p, lam, n, r2, status)


# ═══════════════════════════════════════════════════════════════════════════════
# A5 – Tier breakdown
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A5: Tier breakdown ===")
for subset_name, tag in [("all_non_ambiguous", "T1.4"), ("bacmet_only", "T1.5")]:
    density = spark_density(get_ko_set(subset_name, gene_df))
    res = soil_pgls(density, f"A5_{tag}_{subset_name}_soil")
    beta, SE, p, lam, n, r2, status = extract1(res)
    print(f"  {subset_name:20s}: n={n}, β={beta:.4f}, p={p:.3e}")
    add(f"A5_tier_{tag}_{subset_name}", beta, SE, p, lam, n, r2, status)


# ═══════════════════════════════════════════════════════════════════════════════
# A6 – Per-metal PGLS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A6: Per-metal PGLS ===")
metals = list_metals_with_min_kos(gene_df, min_kos=20)
for metal_sym, n_kos in metals.items():
    ko_ids = list(get_metal_subset(metal_sym, gene_df)["KO"])
    density = spark_density(ko_ids)
    res = soil_pgls(density, f"A6_metal_{metal_sym}_soil", min_n=15)
    beta, SE, p, lam, n, r2, status = extract1(res)
    print(f"  {metal_sym:4s} ({n_kos:3d} KOs): n={n}, β={beta:.4f}, p={p:.3e}")
    add(f"A6_metal_M_{metal_sym}", beta, SE, p, lam, n, r2, status)


# ═══════════════════════════════════════════════════════════════════════════════
# A10 – Cofactor jackknife
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A10: Cofactor jackknife ===")
jk_full    = pd.read_csv(DATA / "cofactor_jackknife_results.csv")
cofactor_all = list(get_ko_set("cofactor", gene_df))
print(f"  Cofactor KOs: {cofactor_all}")
for _, row in jk_full.iterrows():
    excl_ko = row["excluded_ko"]
    subset_kos = [k for k in cofactor_all if k != excl_ko]
    if not subset_kos:
        continue
    density = spark_density(subset_kos)
    res = soil_pgls(density, f"A10_jk_excl_{excl_ko}_soil", min_n=15)
    beta, SE, p, lam, n, r2, status = extract1(res)
    sign_change = row.get("beta_sign_change", "?")
    print(f"  Excl {excl_ko}: n={n}, β={beta:.4f}, p={p:.3e}  (full_env sign_change={sign_change})")
    add(f"A10_cofactor_jk_excl_{excl_ko}", beta, SE, p, lam, n, r2, status)


# ═══════════════════════════════════════════════════════════════════════════════
# A17 – Comparator PGLS  (reuse existing landscape density CSVs)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A17: Comparator PGLS (from existing density files) ===")
COMP_FILE = {
    "carbohydrate_metabolism": "landscape_carbohydrate_metab_density.csv",
    "amino_acid_metabolism":   "landscape_aa_metab_density.csv",
    "energy_metabolism":       "landscape_energy_metab_density.csv",
    "membrane_transport_ABC":  "landscape_abc_transporters_density.csv",
    "translation":             "landscape_translation_density.csv",
    "transcription":           "landscape_transcription_density.csv",
}
comp_full = pd.read_csv(DATA / "comparator_pgls_results.csv")
for _, row in comp_full.iterrows():
    comp_name = row["comparator"]
    dfile = COMP_FILE.get(comp_name)
    if not dfile or not (DATA / dfile).exists():
        print(f"  {comp_name}: density file missing; SKIPPED")
        add(f"A17_comparator_{comp_name}", float("nan"), float("nan"), float("nan"),
            float("nan"), float("nan"), float("nan"),
            status="SKIPPED (no density file)")
        continue

    density_df = pd.read_csv(DATA / dfile)
    merged = pgls_soil.merge(
        density_df[["genus_lower", "ko_per_mb"]].rename(
            columns={"ko_per_mb": "comp_ko_per_mb"}),
        on="genus_lower", how="inner"
    ).copy()
    merged["metal_z"] = _z(merged["ko_per_mb_primary"])
    merged["comp_z"]  = _z(merged["comp_ko_per_mb"])
    valid = merged.dropna(subset=["metal_z", "comp_z", "mean_levins_B_std"])

    if len(valid) < 20:
        print(f"  {comp_name}: n={len(valid)} too small; SKIPPED")
        add(f"A17_comparator_{comp_name}", float("nan"), float("nan"), float("nan"),
            float("nan"), float("nan"), float("nan"),
            status=f"SKIPPED (n={len(valid)} < 20)")
        continue

    res = run_pgls(valid, TREE, response="mean_levins_B_std",
                   predictors=["metal_z", "comp_z"],
                   taxon_col="genus_lower",
                   label=f"A17_{comp_name}_soil", min_n=20)

    metal_beta = res["betas"].get("metal_z", float("nan"))
    metal_SE   = res["SEs"].get("metal_z", float("nan"))
    metal_p    = res["p_values"].get("metal_z", float("nan"))
    comp_beta  = res["betas"].get("comp_z", float("nan"))
    comp_p     = res["p_values"].get("comp_z", float("nan"))
    n          = res.get("n", float("nan"))
    lam        = res.get("lambda_est", float("nan"))
    r2         = res.get("r2", float("nan"))
    print(f"  {comp_name}: n={n}, metal_β={metal_beta:.4f}(p={metal_p:.3e}), comp_β={comp_beta:.4f}(p={comp_p:.3e})")
    add(f"A17_comparator_{comp_name}", metal_beta, metal_SE, metal_p, lam, n, r2,
        status=f"comp_beta={comp_beta:.4f},comp_p={comp_p:.3e}")


# ═══════════════════════════════════════════════════════════════════════════════
# A21 – Functional landscape  (reuse existing landscape density CSVs)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A21: Functional landscape (from existing density files) ===")
fl_full    = pd.read_csv(DATA / "functional_landscape_results.csv")
fl_summary = []

for _, row in fl_full.iterrows():
    cat_key = row["category"]
    if cat_key == "metal_genes_p1":
        continue
    dfile = DATA / f"landscape_{cat_key}_density.csv"
    if not dfile.exists():
        print(f"  {cat_key}: no density file; SKIPPED")
        fl_summary.append({"category": cat_key, "status": "NO_FILE"})
        add(f"A21_landscape_{cat_key}", float("nan"), float("nan"), float("nan"),
            float("nan"), float("nan"), float("nan"), status="SKIPPED (no density file)")
        continue

    density_df = pd.read_csv(dfile)
    res = soil_pgls(density_df, f"A21_{cat_key}_soil", min_n=20)
    beta, SE, p, lam, n, r2, status = extract1(res)
    print(f"  {cat_key:25s}: n={n}, β={beta:.4f}, p={p:.3e}")
    fl_summary.append({"category": cat_key, "beta": beta, "p": p, "n": n, "status": status})
    add(f"A21_landscape_{cat_key}", beta, SE, p, lam, n, r2, status)

n_sig_fl = sum(
    1 for r in fl_summary
    if pd.notna(r.get("p", float("nan"))) and r.get("p", 1) < 0.05
)
print(f"  A21 summary: {len(fl_summary)} categories; {n_sig_fl} p<0.05")
add("A21_functional_landscape_summary",
    float("nan"), float("nan"), float("nan"), float("nan"), len(fl_summary), float("nan"),
    status=f"{len(fl_summary)} categories run; {n_sig_fl} p<0.05 (uncorrected)")


# ═══════════════════════════════════════════════════════════════════════════════
# A22 – Interaction test: joint cofactor + resistance
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A22: Interaction (joint cofactor + resistance) ===")
resist_density  = spark_density(get_ko_set("resistance", gene_df))
cofactor_density = spark_density(get_ko_set("cofactor", gene_df))

merged_int = pgls_soil.copy()
merged_int = merged_int.merge(
    resist_density[["genus_lower", "ko_per_mb"]].rename(columns={"ko_per_mb": "resist_ko_per_mb"}),
    on="genus_lower", how="inner"
)
merged_int = merged_int.merge(
    cofactor_density[["genus_lower", "ko_per_mb"]].rename(columns={"ko_per_mb": "cofactor_ko_per_mb"}),
    on="genus_lower", how="inner"
)
merged_int["resist_z"]  = _z(merged_int["resist_ko_per_mb"])
merged_int["cofactor_z"] = _z(merged_int["cofactor_ko_per_mb"])
valid_int = merged_int.dropna(subset=["resist_z", "cofactor_z", "mean_levins_B_std"])
print(f"  Joint model n={len(valid_int)}")

if len(valid_int) >= 20:
    res_int = run_pgls(valid_int, TREE, response="mean_levins_B_std",
                       predictors=["resist_z", "cofactor_z"],
                       taxon_col="genus_lower",
                       label="A22_interaction_soil", min_n=20)
    r_beta = res_int["betas"].get("resist_z", float("nan"))
    r_p    = res_int["p_values"].get("resist_z", float("nan"))
    c_beta = res_int["betas"].get("cofactor_z", float("nan"))
    c_SE   = res_int["SEs"].get("cofactor_z", float("nan"))
    c_p    = res_int["p_values"].get("cofactor_z", float("nan"))
    n      = res_int.get("n", float("nan"))
    lam    = res_int.get("lambda_est", float("nan"))
    r2     = res_int.get("r2", float("nan"))
    print(f"  resist β={r_beta:.4f}(p={r_p:.3e}), cofactor β={c_beta:.4f}(p={c_p:.3e}), n={n}")
    add("A22_interaction_cofactor_vs_resistance", c_beta, c_SE, c_p, lam, n, r2,
        status=f"resist_beta={r_beta:.4f},resist_p={r_p:.3e}")
else:
    print(f"  SKIPPED (n={len(valid_int)} < 20)")
    add("A22_interaction_cofactor_vs_resistance",
        float("nan"), float("nan"), float("nan"), float("nan"), len(valid_int), float("nan"),
        status=f"SKIPPED (n={len(valid_int)} < 20)")


# ═══════════════════════════════════════════════════════════════════════════════
# A24 – Category conditional models (local variables only: baseline + genome_size)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== A24: Category conditional models ===")
for model_name, predictors in [("baseline",       ["predictor_z"]),
                                ("+ genome_size_z", ["predictor_z", "genome_mb_z"])]:
    valid_cond = pgls_soil.dropna(subset=predictors + ["mean_levins_B_std"]).copy()
    if len(valid_cond) < 20:
        print(f"  {model_name}: n={len(valid_cond)} too small; SKIPPED")
        continue
    res = run_pgls(valid_cond, TREE, response="mean_levins_B_std",
                   predictors=predictors, taxon_col="genus_lower",
                   label=f"A24_{model_name.replace(' ', '_').replace('+', 'plus')}_soil",
                   min_n=20)
    if len(predictors) == 1:
        beta = res.get("beta", float("nan"))
        SE   = res.get("SE", float("nan"))
        p    = res.get("p_value", float("nan"))
    else:
        beta = res["betas"].get("predictor_z", float("nan"))
        SE   = res["SEs"].get("predictor_z", float("nan"))
        p    = res["p_values"].get("predictor_z", float("nan"))
    n   = res.get("n", float("nan"))
    lam = res.get("lambda_est", float("nan"))
    r2  = res.get("r2", float("nan"))
    print(f"  {model_name}: metal β={beta:.4f}, p={p:.3e}, n={n}")
    safe_name = model_name.strip().replace(" ", "_").replace("+", "plus")
    add(f"A24_cond_{safe_name}", beta, SE, p, lam, n, r2)

# annotation-depth models require Spark — mark as NOT_RUN with explanation
for model_name in ["+ ann_depth_z", "+ ko_breadth_z", "+ depth+breadth"]:
    add(f"A24_cond_{model_name}", float("nan"), float("nan"), float("nan"),
        float("nan"), float("nan"), float("nan"),
        status="NOT_RUN (annotation depth not in local pgls_input; needs Spark total-KO query)")


# ═══════════════════════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== Saving ===")
# Drop old NOT_RUN soil rows for target analyses
keep_mask = ~(
    existing["dataset"].eq("soil_only") &
    existing["analysis"].str.match(r"^(" + "|".join(TARGET_PREFIXES) + r")")
)
cleaned   = existing[keep_mask]
new_df    = pd.DataFrame(new_rows)
combined  = pd.concat([cleaned, new_df], ignore_index=True)
combined.to_csv(DATA / "AUDIT_soil_comparison.csv", index=False)
print(f"Saved {len(combined)} rows → data/AUDIT_soil_comparison.csv")
print(f"  ({len(new_df)} new soil rows, {len(existing) - len(cleaned)} old NOT_RUN removed)")

# ── Summary print (paste into AUDIT_REPORT.md) ───────────────────────────────
print("\n" + "=" * 80)
print("AUDIT_REPORT.md UPDATE — soil-only Spark results")
print("=" * 80)
for prefix_label, prefix in [
    ("A4 CATEGORY BREAKDOWN", "A4_"),
    ("A5 TIER BREAKDOWN", "A5_"),
    ("A6 PER-METAL PGLS", "A6_"),
    ("A10 COFACTOR JACKKNIFE", "A10_"),
    ("A17 COMPARATOR PGLS", "A17_"),
    ("A21 FUNCTIONAL LANDSCAPE", "A21_"),
    ("A22 INTERACTION TEST", "A22_"),
    ("A24 CONDITIONAL MODELS", "A24_"),
]:
    subset = new_df[new_df["analysis"].str.startswith(prefix)]
    if subset.empty:
        continue
    print(f"\n--- {prefix_label} ---")
    for _, r in subset.iterrows():
        try:
            b = float(r["beta"]); p = float(r["p"]); n = int(float(r["n"]))
            sig = "**" if p < 0.05 else "  "
            print(f"  {sig} {r['analysis']:55s}: β={b:+.4f}, p={p:.3e}, n={n}")
        except (ValueError, TypeError):
            print(f"     {r['analysis']:55s}: {r.get('status', '')}")
