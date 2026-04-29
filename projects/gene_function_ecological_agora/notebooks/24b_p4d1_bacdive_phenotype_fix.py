"""NB24b — fix NB24's column-candidate bug. Use the actual columns:
  physiology: gram_stain, cell_shape, motility, oxygen_tolerance, predicted_oxygen
  metabolite_utilization: compound_name, utilization
  enzyme: ec_number (already worked)
"""
import json, time
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/data")
FIG_DIR = Path("/home/aparkin/BERIL-research-observatory/projects/gene_function_ecological_agora/figures")

t0 = time.time()
print("=== NB24b — BacDive phenotype anchor (fixed) ===", flush=True)

phys = pd.read_parquet(DATA_DIR / "p4d1_bacdive_physiology_per_species.parquet")
mut = pd.read_parquet(DATA_DIR / "p4d1_bacdive_metabolite_utilization_per_species.parquet")
enz = pd.read_parquet(DATA_DIR / "p4d1_bacdive_enzyme_per_species.parquet")
print(f"physiology: {len(phys):,}, metabolite: {len(mut):,}, enzyme: {len(enz):,}", flush=True)

# EC number → enzyme name mapping (lookup)
EC_NAMES = {
    "1.11.1.6": "catalase (aerobic marker)",
    "3.2.1.21": "β-glucosidase",
    "3.2.1.22": "α-galactosidase",
    "3.2.1.23": "β-galactosidase",
    "3.2.1.24": "α-mannosidase",
    "3.2.1.31": "β-glucuronidase",
    "3.2.1.51": "α-L-fucosidase",
    "3.2.1.52": "β-N-acetylhexosaminidase",
    "3.4.11.1": "leucyl-aminopeptidase",
    "3.4.11.3": "cystinyl-aminopeptidase",
    "3.4.21.1": "chymotrypsin",
    "3.4.21.4": "trypsin",
    "3.5.1.5": "urease",
    "3.1.3.1": "alkaline phosphatase",
    "3.1.3.2": "acid phosphatase",
    "1.9.3.1": "cytochrome c oxidase (aerobic marker)",
}
def annotate_ec(ec):
    return f"{ec} ({EC_NAMES.get(ec, '?')})"

focal_clades = {
    "Mycobacteriaceae": ("family", "f__Mycobacteriaceae"),
    "Cyanobacteriia": ("class", "c__Cyanobacteriia"),
    "Bacteroidota": ("phylum", "p__Bacteroidota"),
}

clade_summaries = {}
for clade_name, (col, val) in focal_clades.items():
    print(f"\n--- {clade_name} ({col}={val}) ---", flush=True)

    summary = {}

    # Physiology
    p_focal = phys[phys[col] == val]
    n_phys = p_focal["gtdb_species_clade_id"].nunique()
    print(f"  Physiology (n_species={n_phys}):")
    for c in ["gram_stain", "cell_shape", "motility", "oxygen_tolerance", "predicted_oxygen", "predicted_motility"]:
        if c not in p_focal.columns: continue
        vc = p_focal[c].value_counts().head(8)
        if len(vc) > 0:
            top_str = ", ".join(f"{v}={n}" for v, n in vc.items())
            print(f"    {c}: {top_str}")
            summary[f"physiology_{c}"] = vc.to_dict()

    # Metabolite utilization
    m_focal = mut[mut[col] == val]
    n_mut = m_focal["gtdb_species_clade_id"].nunique()
    print(f"  Metabolite utilization (n_species={n_mut}, n_rows={len(m_focal):,}):")
    # Top compounds with utilization status
    top_compounds = m_focal["compound_name"].value_counts().head(15)
    print(f"    Top 15 tested compounds (across all utilization statuses):")
    for cmpd, n in top_compounds.items():
        print(f"      {cmpd}: {n}")
    summary["metabolite_top_compounds"] = top_compounds.to_dict()

    # Utilization-status breakdown for top compounds
    print(f"    Utilization status for top 5:")
    for cmpd in top_compounds.head(5).index:
        sub = m_focal[m_focal["compound_name"] == cmpd]
        util_breakdown = sub["utilization"].value_counts().to_dict()
        print(f"      {cmpd}: {util_breakdown}")

    # Enzyme
    e_focal = enz[enz[col] == val]
    n_enz = e_focal["gtdb_species_clade_id"].nunique()
    top_ecs = e_focal["ec_number"].value_counts().head(10)
    print(f"  Enzyme (n_species={n_enz}):")
    for ec, n in top_ecs.items():
        print(f"    {annotate_ec(ec)}: {n}")
    summary["enzyme_top_ecs"] = top_ecs.to_dict()

    summary["n_species_physiology"] = int(n_phys)
    summary["n_species_metabolite"] = int(n_mut)
    summary["n_species_enzyme"] = int(n_enz)
    clade_summaries[clade_name] = summary

# Compare oxygen tolerance across clades
print("\n--- Comparison: oxygen_tolerance distribution ---", flush=True)
ox_compare = {}
for clade_name, (col, val) in focal_clades.items():
    p_focal = phys[phys[col] == val]
    if "oxygen_tolerance" in p_focal.columns:
        ox = p_focal["oxygen_tolerance"].value_counts(normalize=True).head(5)
        ox_compare[clade_name] = ox.to_dict()
        print(f"  {clade_name}: {ox.to_dict()}")

# Also compare to atlas-wide
ox_atlas = phys["oxygen_tolerance"].value_counts(normalize=True).head(8)
print(f"  ATLAS: {ox_atlas.to_dict()}")
ox_compare["atlas"] = ox_atlas.to_dict()

# Save updated diagnostics
diag = {
    "phase": "4", "deliverable": "P4-D1 NB24b",
    "purpose": "BacDive phenotype anchoring (NB24 column fix)",
    "n_species_physiology": int(phys["gtdb_species_clade_id"].nunique()),
    "n_species_metabolite": int(mut["gtdb_species_clade_id"].nunique()),
    "n_species_enzyme": int(enz["gtdb_species_clade_id"].nunique()),
    "focal_clade_summaries": clade_summaries,
    "oxygen_tolerance_compare": ox_compare,
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d1_bacdive_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2, default=str)
print(f"\nUpdated p4d1_bacdive_diagnostics.json", flush=True)

# Figure: 3-clade oxygen-tolerance + top-EC heatmap
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Panel A: oxygen tolerance bar
ax = axes[0]
ox_keys = ["aerobe", "anaerobe", "facultative anaerobe", "microaerophile", "obligate aerobe", "obligate anaerobe"]
clades = list(focal_clades.keys()) + ["atlas"]
mat = np.zeros((len(clades), len(ox_keys)))
for i, cl in enumerate(clades):
    for j, k in enumerate(ox_keys):
        mat[i, j] = ox_compare.get(cl, {}).get(k, 0) * 100
x = np.arange(len(ox_keys)); w = 0.18
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "lightgray"]
for i, (cl, color) in enumerate(zip(clades, colors)):
    ax.bar(x + (i-1.5)*w, mat[i], w, label=cl, color=color)
ax.set_xticks(x); ax.set_xticklabels(ox_keys, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("% of species in category")
ax.set_title("BacDive oxygen tolerance by focal clade (anchor expectation: Cyano aerobic, Bacteroidota anaerobic)")
ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)

# Panel B: top 10 EC numbers across focal clades — heatmap
ax = axes[1]
all_ecs = set()
for cl, summ in clade_summaries.items():
    all_ecs.update(summ["enzyme_top_ecs"].keys())
all_ecs = sorted(all_ecs)
ec_mat = np.zeros((len(focal_clades), len(all_ecs)))
ec_norm = {cl: max(summ["enzyme_top_ecs"].values()) if summ["enzyme_top_ecs"] else 1 for cl, summ in clade_summaries.items()}
for i, (cl, summ) in enumerate(clade_summaries.items()):
    for j, ec in enumerate(all_ecs):
        ec_mat[i, j] = summ["enzyme_top_ecs"].get(ec, 0) / ec_norm[cl] if ec_norm[cl] else 0
im = ax.imshow(ec_mat, aspect="auto", cmap="Blues")
ax.set_xticks(range(len(all_ecs)))
ax.set_xticklabels([annotate_ec(e)[:30] for e in all_ecs], rotation=60, ha="right", fontsize=7)
ax.set_yticks(range(len(focal_clades))); ax.set_yticklabels(list(focal_clades.keys()))
ax.set_title("Top BacDive EC enzymes per focal clade (normalized to within-clade max)")
plt.colorbar(im, ax=ax)

plt.tight_layout()
plt.savefig(FIG_DIR / "p4d1_bacdive_phenotype_panel.png", dpi=120, bbox_inches="tight")
print(f"Wrote figure", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)
