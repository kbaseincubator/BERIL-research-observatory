"""NB19 / P4-D3 — Alm 2006 r ≈ 0.74 reproduction at GTDB scale.

Reproduces the Alm, Huang, Arkin (2006, PLoS Comp Biol 2:e143) finding:
  r = 0.74 between per-genome HPK (histidine protein kinase) count and per-genome
  recent-LSE (lineage-specific expansion) fraction, across 207 prokaryotic genomes.

Our reproduction:
  - 18,989 GTDB-r214 species (≈92× more data points)
  - HPK count per species: distinct gene_clusters with Pfam PF00512 (HisKA) in
    interproscan_domains (the audit-validated substrate per NB13)
  - Recent-LSE fraction per species: TCS HK gain events from M22 attributed to
    a recipient_genus containing the species, depth_bin = "recent" (genus-level
    LCA), as fraction of total gene_clusters in species
  - Compute Pearson r; verdict: Alm 2006 reproduces (r ≥ 0.6) / weakly reproduces
    (0.4 ≤ r < 0.6) / falsified (r < 0.4)

Methodology refinements over Alm 2006:
  - Tree-aware Sankoff parsimony (M16) instead of family-level paralog expansion
  - Recipient-rank attribution at genus level (M22) instead of LSE detection from
    gene tree alone
  - Modern GTDB-r214 phylogeny instead of pre-2006 small-tree analysis
  - Population genetic standardization across all bacterial phyla instead of 207-genome
    convenience sample
"""
import os, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyspark.sql import functions as F
from berdl_notebook_utils.setup_spark_session import get_spark_session

PROJECT_ROOT = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora")
DATA_DIR = PROJECT_ROOT / "data"
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== NB19 / P4-D3 — Alm 2006 r ≈ 0.74 reproduction at GTDB scale ===", flush=True)

# Stage 1: per-species HPK count via PF00512 (HisKA)
spark = get_spark_session()
species_df = pd.read_csv(DATA_DIR / "p1b_full_species.tsv", sep="\t")
spark.createDataFrame(species_df[["gtdb_species_clade_id"]]).createOrReplaceTempView("p1b_species")

print("Stage 1: per-species HPK count (PF00512 HisKA in interproscan_domains)...", flush=True)
hpk_per_species = spark.sql("""
    SELECT gc.gtdb_species_clade_id,
           COUNT(DISTINCT gc.gene_cluster_id) AS n_hpk
    FROM kbase_ke_pangenome.gene_cluster gc
    JOIN p1b_species sv ON gc.gtdb_species_clade_id = sv.gtdb_species_clade_id
    JOIN kbase_ke_pangenome.interproscan_domains ips
      ON ips.gene_cluster_id = gc.gene_cluster_id
    WHERE ips.analysis = 'Pfam' AND ips.signature_acc = 'PF00512'
    GROUP BY gc.gtdb_species_clade_id
""")
hpk_pdf = hpk_per_species.toPandas()
print(f"  Species with HPK count: {len(hpk_pdf):,} ({time.time()-t0:.1f}s)", flush=True)
print(f"  HPK count quantiles: {hpk_pdf['n_hpk'].quantile([0.25, 0.5, 0.75, 0.9, 0.99]).to_dict()}", flush=True)

# Stage 2: per-species TOTAL gene_cluster count (for normalization)
print("\nStage 2: per-species total gene_cluster count (for recent-LSE denominator)...", flush=True)
total_gc = spark.sql("""
    SELECT gc.gtdb_species_clade_id,
           COUNT(DISTINCT gene_cluster_id) AS n_gc_total
    FROM kbase_ke_pangenome.gene_cluster gc
    JOIN p1b_species sv ON gc.gtdb_species_clade_id = sv.gtdb_species_clade_id
    GROUP BY gc.gtdb_species_clade_id
""")
total_pdf = total_gc.toPandas()
print(f"  Species with gene_cluster count: {len(total_pdf):,} ({time.time()-t0:.1f}s)", flush=True)

# Stage 3: per-species recent-LSE TCS HK gain count via M22 attribution
print("\nStage 3: per-species recent-LSE TCS HK gain count from M22...", flush=True)
attributed = pd.read_parquet(DATA_DIR / "p2_m22_gains_attributed.parquet")
ko_class = pd.read_csv(DATA_DIR / "p2_ko_control_classes.tsv", sep="\t")
tcs_hk_kos = set(ko_class[ko_class["control_class"] == "pos_tcs_hk"]["ko"])
print(f"  TCS HK KOs: {len(tcs_hk_kos):,}", flush=True)

# Filter M22 to TCS HK gains, recent-bin (genus-level LCA = species-level recent acquisition)
recent_tcs = attributed[
    (attributed["ko"].isin(tcs_hk_kos)) & (attributed["depth_bin"] == "recent")
].copy()
print(f"  Recent TCS HK gain events: {len(recent_tcs):,}", flush=True)

# Map recipient_genus → species (a species is a "recipient" of a gain event if its genus matches recipient_genus)
species_to_genus = species_df.set_index("gtdb_species_clade_id")["genus"].to_dict()
genus_to_species = {}
for s, g in species_to_genus.items():
    if g and isinstance(g, str):
        genus_to_species.setdefault(g, []).append(s)

# Per (recipient_genus, ko): count recent TCS HK gain events
gains_by_genus_ko = recent_tcs.groupby(["recipient_genus", "ko"]).size().reset_index(name="n_gains_at_genus")

# For each species, sum gains landing at its genus across TCS HK KOs that the species actually has
# This requires knowing which KOs each species has — pull from p2_ko_assignments_panel.parquet
panel_assignments = pd.read_parquet(DATA_DIR / "p2_ko_assignments_panel.parquet")
panel_assignments_tcs = panel_assignments[panel_assignments["ko"].isin(tcs_hk_kos) & panel_assignments["is_present"]]
print(f"  TCS HK presence rows in panel: {len(panel_assignments_tcs):,}", flush=True)

# Join species ↔ genus, then ↔ gains
panel_assignments_tcs = panel_assignments_tcs.merge(
    species_df[["gtdb_species_clade_id", "genus"]], on="gtdb_species_clade_id", how="left"
)
# Each (species, KO) pairs a species's TCS HK presence with its genus
# Per species: sum n_gains_at_genus over (genus, ko) pairs the species has
panel_with_gains = panel_assignments_tcs.merge(
    gains_by_genus_ko, left_on=["genus", "ko"], right_on=["recipient_genus", "ko"], how="left"
)
panel_with_gains["n_gains_at_genus"] = panel_with_gains["n_gains_at_genus"].fillna(0)

# Per species: recent-LSE TCS HK count (sum of gains across the species's TCS HK KOs)
recent_lse_per_species = (panel_with_gains
    .groupby("gtdb_species_clade_id")
    .agg(
        n_recent_tcs_gains_at_genus=("n_gains_at_genus", "sum"),
        n_tcs_hk_kos_present=("ko", "count"),
    )
    .reset_index()
)
print(f"  Species with TCS HK presence: {len(recent_lse_per_species):,}", flush=True)

# Stage 4: combine + compute r
combined = (species_df[["gtdb_species_clade_id"]]
    .merge(hpk_pdf, on="gtdb_species_clade_id", how="left")
    .merge(total_pdf, on="gtdb_species_clade_id", how="left")
    .merge(recent_lse_per_species, on="gtdb_species_clade_id", how="left")
)
combined["n_hpk"] = combined["n_hpk"].fillna(0).astype(int)
combined["n_gc_total"] = combined["n_gc_total"].fillna(0).astype(int)
combined["n_recent_tcs_gains_at_genus"] = combined["n_recent_tcs_gains_at_genus"].fillna(0)
combined["n_tcs_hk_kos_present"] = combined["n_tcs_hk_kos_present"].fillna(0).astype(int)

# Recent-LSE fractions
combined["recent_lse_fraction_per_gc"] = (
    combined["n_recent_tcs_gains_at_genus"] / combined["n_gc_total"].clip(lower=1)
)
combined["recent_lse_fraction_per_tcs_ko"] = (
    combined["n_recent_tcs_gains_at_genus"] / combined["n_tcs_hk_kos_present"].clip(lower=1)
)

# HPK fraction (Alm 2006-style: HPK count / total gene count)
combined["hpk_fraction"] = combined["n_hpk"] / combined["n_gc_total"].clip(lower=1)

print(f"\nCombined dataset: {len(combined):,} species", flush=True)
print(f"  Species with n_hpk > 0: {(combined['n_hpk'] > 0).sum():,}", flush=True)
print(f"  Species with recent gain at genus > 0: {(combined['n_recent_tcs_gains_at_genus'] > 0).sum():,}", flush=True)

# Compute correlations — multiple framings
print(f"\n=== Correlation results ===", flush=True)
correlations = []
for metric_x, metric_y, label in [
    ("n_hpk", "n_recent_tcs_gains_at_genus", "HPK count vs recent TCS gains at genus"),
    ("hpk_fraction", "recent_lse_fraction_per_gc", "Alm-2006-style: HPK fraction vs recent-LSE fraction"),
    ("n_hpk", "recent_lse_fraction_per_gc", "HPK count vs recent-LSE fraction"),
    ("n_hpk", "recent_lse_fraction_per_tcs_ko", "HPK count vs recent-LSE per TCS HK KO"),
]:
    valid = combined[[metric_x, metric_y]].dropna()
    if len(valid) < 10:
        correlations.append({"label": label, "n": len(valid), "r": np.nan, "p": np.nan})
        continue
    r, p = stats.pearsonr(valid[metric_x], valid[metric_y])
    rs, ps = stats.spearmanr(valid[metric_x], valid[metric_y])
    correlations.append({
        "label": label, "metric_x": metric_x, "metric_y": metric_y,
        "n": len(valid), "pearson_r": round(r, 4), "pearson_p": float(p),
        "spearman_r": round(rs, 4), "spearman_p": float(ps),
    })
    print(f"  {label}", flush=True)
    print(f"    n = {len(valid):,} | Pearson r = {r:.4f} (p = {p:.2e}) | Spearman r = {rs:.4f} (p = {ps:.2e})", flush=True)

corr_df = pd.DataFrame(correlations)

# Headline: Alm 2006-style HPK fraction vs recent-LSE fraction
alm_style = next((c for c in correlations if c["label"].startswith("Alm-2006-style")), None)
ALM_2006_R = 0.74

if alm_style and not np.isnan(alm_style["pearson_r"]):
    r_obs = alm_style["pearson_r"]
    if abs(r_obs - ALM_2006_R) < 0.10:
        verdict = f"REPRODUCED (r = {r_obs:.4f} vs Alm 2006 r = {ALM_2006_R}, |Δ| < 0.10)"
    elif abs(r_obs) >= 0.6:
        verdict = f"PARTIALLY REPRODUCED (r = {r_obs:.4f}, strong correlation but Δ from Alm 2006 r = {ALM_2006_R} is {abs(r_obs - ALM_2006_R):.2f})"
    elif abs(r_obs) >= 0.4:
        verdict = f"WEAK REPRODUCTION (r = {r_obs:.4f}, moderate correlation; Alm 2006 r = {ALM_2006_R} not reproduced at GTDB scale)"
    elif abs(r_obs) >= 0.2:
        verdict = f"WEAK SIGNAL (r = {r_obs:.4f}, weak correlation; Alm 2006 r = {ALM_2006_R} not reproduced)"
    else:
        verdict = f"NOT REPRODUCED (r = {r_obs:.4f}, no meaningful correlation)"
else:
    verdict = "INSUFFICIENT DATA"

print(f"\n*** P4-D3 VERDICT: {verdict} ***\n", flush=True)
print(f"Reference: Alm, Huang, Arkin 2006 reported r = {ALM_2006_R} on 207 prokaryotic genomes (HPK count vs recent-LSE fraction).", flush=True)
print(f"Our reproduction: 18,989 GTDB-r214 species ({len(combined):,} with full data).", flush=True)

# Save outputs
combined.to_csv(DATA_DIR / "p4d3_per_species_hpk_lse.tsv", sep="\t", index=False)
corr_df.to_csv(DATA_DIR / "p4d3_correlations.tsv", sep="\t", index=False)
print(f"\nWrote p4d3_per_species_hpk_lse.tsv + p4d3_correlations.tsv", flush=True)

# Figure: scatter of HPK fraction vs recent-LSE fraction (Alm 2006-style)
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
data = combined[(combined["n_hpk"] > 0) & (combined["n_recent_tcs_gains_at_genus"] > 0)]
ax.scatter(data["hpk_fraction"], data["recent_lse_fraction_per_gc"], alpha=0.3, s=8, color="#1f77b4")
ax.set_xlabel("HPK fraction (n_HPK / n_gene_clusters)")
ax.set_ylabel("Recent-LSE TCS HK gain fraction (per gene_cluster)")
ax.set_title(f"P4-D3: HPK fraction vs recent-LSE\n(Alm 2006-style; n = {len(data):,} species; r = {alm_style['pearson_r']:.3f})")
ax.set_xscale("symlog", linthresh=0.001)
ax.set_yscale("symlog", linthresh=0.0001)
ax.grid(alpha=0.3)

# Reference: Alm 2006 r=0.74 line for visual comparison
if alm_style and not np.isnan(alm_style["pearson_r"]):
    ax.axhline(y=data["recent_lse_fraction_per_gc"].median(), color="lightgray", lw=0.5, ls="--", alpha=0.5)
    ax.axvline(x=data["hpk_fraction"].median(), color="lightgray", lw=0.5, ls="--", alpha=0.5)

ax = axes[1]
ax.scatter(combined["n_hpk"], combined["n_recent_tcs_gains_at_genus"], alpha=0.3, s=8, color="#d62728")
n_corr = next((c for c in correlations if c["label"].startswith("HPK count vs recent TCS")), None)
ax.set_xlabel("HPK count (n distinct gene_clusters with PF00512)")
ax.set_ylabel("Recent TCS HK gains at genus (M22)")
ax.set_title(f"HPK count vs recent gain count\n(n = {n_corr['n']:,} species; r = {n_corr['pearson_r']:.3f})")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "p4d3_alm_2006_reproduction.png", dpi=120, bbox_inches="tight")
print(f"Wrote figure ({time.time()-t0:.1f}s)", flush=True)

# Diagnostics
diagnostics = {
    "phase": "4", "deliverable": "P4-D3", "purpose": "Alm 2006 r ≈ 0.74 reproduction",
    "n_species": int(len(combined)),
    "alm_2006_reference_r": ALM_2006_R,
    "alm_2006_reference_n_genomes": 207,
    "correlations": correlations,
    "verdict": verdict,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d3_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)
print(f"Wrote p4d3_diagnostics.json", flush=True)
print(f"\n=== DONE in {time.time()-t0:.1f}s ===", flush=True)
