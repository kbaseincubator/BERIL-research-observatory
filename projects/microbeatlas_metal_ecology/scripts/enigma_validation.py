#!/usr/bin/env python3
"""
ENIGMA Validation Analysis (Production Version)
==============================================
Track A: Global Groundwater Enrichment (BERDL Delta Lake)
Track B: Site-Specific Validation (Delta Lake + NCBI Fallback)
  - Addresses Reviewer #2's Redox vs. Metal concerns.
  - Addresses "Dark Matter" mapping via Pessimistic CWM.

Dependencies: pip install requests pandas numpy scipy pingouin matplotlib seaborn
"""

import os
import sys
import json
import time
import io
import urllib.request
from pathlib import Path

import requests
import pandas as pd
import numpy as np
from scipy import stats
import pingouin as pg

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

# ============================================================
# Configuration
# ============================================================
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
FIG_DIR = PROJECT_DIR / "figures"
ENV_FILE = PROJECT_DIR.parent.parent / ".env"

BERDL_QUERY_URL = "https://hub.berdl.kbase.us/apis/mcp/delta/tables/query"
SRA_RUNINFO_URL = "https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi"

N_TOTAL_SAMPLES = 463_972   
N_GW_SAMPLES    = 1_624     
N_NON_GW        = N_TOTAL_SAMPLES - N_GW_SAMPLES

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ============================================================
# Helpers & Auth
# ============================================================
def get_auth_token():
    # Print exactly where we are looking
    print(f"DEBUG: Looking for token in: {ENV_FILE.resolve()}")
    
    if not ENV_FILE.exists():
        print(f"❌ ERROR: File does not exist at {ENV_FILE.resolve()}")
        raise FileNotFoundError

    try:
        with open(ENV_FILE) as f:
            for line in f:
                if "KBASE_AUTH_TOKEN" in line:
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    # Print the last 4 chars to verify it's the NEW one
                    print(f"DEBUG: Token loaded (ends in ...{token[-4:]})")
                    return token
    except Exception as e:
        raise ValueError(f"Could not read token: {e}")

def query_berdl(query_sql, auth_token, limit=1000, offset=0):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    payload = {"query": query_sql, "limit": limit, "offset": offset}
    resp = requests.post(BERDL_QUERY_URL, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json()

def fetch_all_pages(query_sql, auth_token, limit=1000):
    all_rows, offset = [], 0
    while True:
        res = query_berdl(query_sql, auth_token, limit=limit, offset=offset)
        rows = res.get("result", [])
        all_rows.extend(rows)
        if not res.get("pagination", {}).get("has_more", False): break
        offset += limit
        time.sleep(0.2)
    return all_rows

def find_col(df, patterns):
    for p in patterns:
        for col in df.columns:
            if p.lower() in col.lower(): return col
    return None

# ============================================================
# Track A: Global Groundwater
# ============================================================
def track_a(auth_token):
    print("\n=== Track A: BERDL Groundwater Enrichment ===")
    
    sql = """
        SELECT ocl.otu_id, COUNT(DISTINCT ocl.sample_id) AS n_gw
        FROM arkinlab_microbeatlas.otu_counts_long ocl
        JOIN arkinlab_microbeatlas.sample_metadata sm ON ocl.sample_id = sm.sample_id
        WHERE sm.Env_Level_2 = 'groundwater' AND ocl.count > 0 AND ocl.otu_id != 'Unmapped'
        GROUP BY ocl.otu_id
    """
    rows = fetch_all_pages(sql, auth_token)
    gw_df = pd.DataFrame(rows)
    gw_df.columns = [c.lower() for c in gw_df.columns] # Fix case sensitivity

    link_df = pd.read_csv(DATA_DIR / "otu_pangenome_link.csv")
    link_df.columns = [c.lower() for c in link_df.columns]

    merged = gw_df.merge(link_df[["otu_id", "genus_clean", "n_cells_by_counts"]], on="otu_id", how="inner")
    
    merged["gw_prev"] = (merged["n_gw"] / N_GW_SAMPLES) * 100
    merged["non_gw_prev"] = ((merged["n_cells_by_counts"] - merged["n_gw"]) / N_NON_GW) * 100
    merged["fold_enr"] = merged["gw_prev"] / (merged["non_gw_prev"] + 1e-4)

    genus_gw = merged.groupby("genus_clean").agg(
        mean_gw_prev=("gw_prev", "mean"),
        mean_fold_enr=("fold_enr", "mean")
    ).reset_index()

    trait_df = pd.read_csv(DATA_DIR / "genus_trait_table.csv")
    trait_df["genus_lower"] = trait_df["otu_genus"].str.lower().str.strip()
    genus_gw["genus_lower"] = genus_gw["genus_clean"].str.lower().str.strip()

    analysis = genus_gw.merge(trait_df, on="genus_lower", how="inner").dropna(subset=["mean_n_metal_types"])

    rho, pval = stats.spearmanr(analysis["mean_n_metal_types"], analysis["mean_gw_prev"])
    q75, q25 = analysis["mean_n_metal_types"].quantile(0.75), analysis["mean_n_metal_types"].quantile(0.25)
    
    print(f"  ✓ Spearman rho: {rho:.3f} (p={pval:.2e})")
    return {"data": analysis, "rho": rho, "pval": pval, "q25": q25, "q75": q75}

# ============================================================
# Track B: Site-Specific (Delta + NCBI)
# ============================================================
def track_b(auth_token):
    print("\n=== Track B: Site-Specific Validation ===")
    cwm_path = DATA_DIR / "enigma_pessimistic_cwm_results.csv"
    if not cwm_path.exists(): return None, None, None
    
    cwm_df = pd.read_csv(cwm_path)
    cwm_df.columns = [c.lower() for c in cwm_df.columns]
    srr_col = find_col(cwm_df, ['srr', 'unnamed', 'index'])
    srr_list = tuple(cwm_df[srr_col].astype(str).tolist())

    # Plan A: Delta Lake (Geological Background)
    print("  Plan A: Querying Delta for GeoROC...")
    sql = f"SELECT accession_id as srr, CAST(GeoROC_Rocks_georoc_U_ppm AS DOUBLE) as u_ppm, CAST(GeoROC_Rocks_georoc_Ni_ppm AS DOUBLE) as ni_ppm FROM arkinlab_microbeatlas.enriched_metadata WHERE accession_id IN {srr_list}"
    rows = fetch_all_pages(sql, auth_token)
    
    if rows:
        df = pd.merge(cwm_df, pd.DataFrame(rows), left_on=srr_col, right_on='srr').dropna(subset=['pessimistic_cwm', 'u_ppm'])
        if len(df) > 5:
            print(f"    ✓ Delta Success ({len(df)} samples)")
            stats_res = pg.partial_corr(data=df, x='pessimistic_cwm', y='u_ppm', covar='ni_ppm', method='spearman')
            return df, stats_res, {"source": "Delta (Geological)", "x": "u_ppm", "lbl": "Uranium (ppm)", "cov": "Ni"}

    # Plan B: NCBI Fallback (SRA Metadata)
    print("  Plan B: Fetching NCBI SRA RunInfo...")
    params = {"save": "efetch", "rettype": "runinfo", "term": "PRJNA1084851"}
    try:
        r = requests.get(SRA_RUNINFO_URL, params=params, timeout=60)
        if "Run" in r.text:
            ncbi_df = pd.read_csv(io.StringIO(r.text))
            ncbi_df.columns = [c.lower() for c in ncbi_df.columns]
            df = pd.merge(cwm_df, ncbi_df, left_on=srr_col, right_on='run')
            u_col = find_col(df, ['uranium', 'u_mg'])
            so4_col = find_col(df, ['sulfate', 'so4'])
            if u_col:
                df[u_col] = pd.to_numeric(df[u_col], errors='coerce')
                df = df.dropna(subset=['pessimistic_cwm', u_col])
                if so4_col:
                    df[so4_col] = pd.to_numeric(df[so4_col], errors='coerce')
                    stats_res = pg.partial_corr(data=df, x='pessimistic_cwm', y=u_col, covar=so4_col, method='spearman')
                    return df, stats_res, {"source": "NCBI (Sample)", "x": u_col, "lbl": f"{u_col}", "cov": so4_col}
    except Exception as e: print(f"    ✗ NCBI failed: {e}")

    print("  ❌ Track B Failed.")
    return None, None, None

# ============================================================
# Figure Generation
# ============================================================
def make_figure(res_a, df_b, stats_b, meta_b):
    print("\n=== Generating 3-Panel Figure ===")
    fig = plt.figure(figsize=(18, 6), layout="constrained")
    gs = gridspec.GridSpec(1, 3, figure=fig)

    # Panel A: Scatter
    ax = fig.add_subplot(gs[0, 0])
    d = res_a["data"]
    sc = ax.scatter(d["mean_n_metal_types"], d["mean_gw_prev"], c=d["mean_fold_enr"].clip(upper=15), cmap="YlOrRd", s=25, alpha=0.6)
    ax.set_title("A. Global Groundwater Prevalence", fontweight="bold")
    ax.set_xlabel("Metal Diversity (n types)")
    ax.set_ylabel("GW Prevalence (%)")
    plt.colorbar(sc, ax=ax, label="Fold Enrichment")

    # Panel B: Boxplot
    ax = fig.add_subplot(gs[0, 1])
    top = d[d["mean_n_metal_types"] >= res_a["q75"]]["mean_gw_prev"]
    bot = d[d["mean_n_metal_types"] <= res_a["q25"]]["mean_gw_prev"]
    ax.boxplot([bot, top], tick_labels=["Bottom Q", "Top Q"], patch_artist=True)
    ax.set_title("B. Prevalence by Diversity Tier", fontweight="bold")
    ax.set_ylabel("GW Prevalence (%)")

    # Panel C: Site Specific
    ax = fig.add_subplot(gs[0, 2])
    if df_b is not None:
        sns.regplot(data=df_b, x=meta_b["x"], y='pessimistic_cwm', ax=ax, color='seagreen')
        ax.set_title(f"C. {meta_b['source']} Validation", fontweight="bold")
        ax.set_xlabel(meta_b["lbl"])
        ax.set_ylabel("Pessimistic CWM")
        rho, p = stats_b['r'].values[0], stats_b['p-val'].values[0]
        ax.text(0.05, 0.95, f"Partial Spearman\nrho={rho:.2f}, p={p:.2e}\nctrl for {meta_b['cov']}", transform=ax.transAxes, va='top', bbox=dict(facecolor='white', alpha=0.7))
    else:
        ax.text(0.5, 0.5, "Track B Data Missing", ha='center')

    plt.savefig(FIG_DIR / "fig_enigma_validation_3panel.png", dpi=300)
    print(f"  ✓ Saved: figures/fig_enigma_validation_3panel.png")

if __name__ == "__main__":
    token = get_auth_token()
    results_a = track_a(token)
    data_b, res_b, metadata_b = track_b(token)
    make_figure(results_a, data_b, res_b, metadata_b)
    print("\n✅ Analysis Complete.")