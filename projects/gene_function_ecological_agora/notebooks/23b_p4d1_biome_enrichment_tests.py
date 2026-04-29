"""NB23b / P4-D1 — biome enrichment for pre-registered atlas findings.

Three pre-registered hypothesis tests using the per-species env substrate from NB23:

  H1 NB16 confirmed: Cyanobacteriia × PSII Innovator-Exchange (class rank).
     Test: are Cyanobacteriia species enriched in marine/photic biomes vs the atlas?

  H2 NB12 confirmed: Mycobacteriaceae × mycolic-acid Innovator-Isolated (family rank).
     Test: are Mycobacteriaceae species enriched in soil + host-pathogen biomes vs the atlas?

  H3 Phase 1B Bacteroidota PUL (qualified): Bacteroidota × PUL Innovator-Exchange.
     Test: are Bacteroidota species enriched in gut + rumen biomes vs the atlas?

Plus T0 atlas-wide enrichment: per (function-class × biome), is recent-gain rate
elevated in the expected biome?

Outputs:
  data/p4d1_biome_enrichment_tests.tsv — per-test enrichment statistics
  data/p4d1_diagnostics.json — full results
  figures/p4d1_clade_biome_panel.png — 3-panel hypothesis figure
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
print("=== NB23b / P4-D1 — biome enrichment tests ===", flush=True)

env = pd.read_parquet(DATA_DIR / "p4d1_env_per_species.parquet")
print(f"Per-species env table: {len(env):,} × {env.shape[1]} cols", flush=True)

# Build a unified biome label per species: prefer MGnify, fall back to env_broad_scale, then isolation_source
def normalize_text(s):
    return s.lower() if isinstance(s, str) else ""

# Define biome groups for the three pre-registered tests
MARINE_PATTERNS = ["marine", "ocean", "sea", "saline", "saltwater", "estuar"]
PHOTIC_PATTERNS = MARINE_PATTERNS + ["lake", "freshwater", "river", "stream", "pond"]
SOIL_PATTERNS = ["soil", "rhizosphere", "sediment", "permafrost", "peat", "compost"]
HOSTPATH_PATTERNS = ["lung", "sputum", "tuberc", "leprosy", "host_disease", "human-skin", "respiratory"]
GUT_PATTERNS = ["gut", "rumen", "feces", "fecal", "intestin", "stomach", "rectum", "colon", "cecum", "gastrointestinal"]

def classify_biome(row, patterns):
    """Return True if any of the env-attribute strings contain any of the patterns."""
    text_blob = " ".join([
        normalize_text(row.get("mgnify_biomes")),
        normalize_text(row.get("env_broad_scale")),
        normalize_text(row.get("env_local_scale")),
        normalize_text(row.get("env_medium")),
        normalize_text(row.get("isolation_source")),
        normalize_text(row.get("host")),
        normalize_text(row.get("sample_type")),
        normalize_text(row.get("host_disease")),
    ])
    return any(p in text_blob for p in patterns)

print("\nClassifying species into biome categories...", flush=True)
env["is_marine"] = env.apply(lambda r: classify_biome(r, MARINE_PATTERNS), axis=1)
env["is_photic_aquatic"] = env.apply(lambda r: classify_biome(r, PHOTIC_PATTERNS), axis=1)
env["is_soil"] = env.apply(lambda r: classify_biome(r, SOIL_PATTERNS), axis=1)
env["is_hostpath"] = env.apply(lambda r: classify_biome(r, HOSTPATH_PATTERNS), axis=1)
env["is_gut_or_rumen"] = env.apply(lambda r: classify_biome(r, GUT_PATTERNS), axis=1)

# Atlas-wide biome fractions
atlas_n = len(env)
atlas_marine = env["is_marine"].sum()
atlas_photic = env["is_photic_aquatic"].sum()
atlas_soil = env["is_soil"].sum()
atlas_hostpath = env["is_hostpath"].sum()
atlas_gut = env["is_gut_or_rumen"].sum()
print(f"\nAtlas-wide biome fractions:", flush=True)
print(f"  marine: {atlas_marine:,} ({100*atlas_marine/atlas_n:.1f}%)", flush=True)
print(f"  photic aquatic (marine + freshwater): {atlas_photic:,} ({100*atlas_photic/atlas_n:.1f}%)", flush=True)
print(f"  soil: {atlas_soil:,} ({100*atlas_soil/atlas_n:.1f}%)", flush=True)
print(f"  host-pathogen: {atlas_hostpath:,} ({100*atlas_hostpath/atlas_n:.1f}%)", flush=True)
print(f"  gut/rumen: {atlas_gut:,} ({100*atlas_gut/atlas_n:.1f}%)", flush=True)

def fisher_enrichment(n_focal_in, n_focal_out, n_atlas_in, n_atlas_out, label):
    """Fisher's exact test for enrichment of focal clade in expected biome vs atlas."""
    # Build contingency: rows = (focal, atlas\focal), cols = (in_biome, out_biome)
    n_other_in = n_atlas_in - n_focal_in
    n_other_out = n_atlas_out - n_focal_out
    table = np.array([[n_focal_in, n_focal_out], [n_other_in, n_other_out]])
    odds, p = stats.fisher_exact(table, alternative="greater")
    pct_focal = 100 * n_focal_in / max(n_focal_in + n_focal_out, 1)
    pct_atlas = 100 * n_atlas_in / atlas_n
    return {
        "label": label,
        "n_focal_in_biome": int(n_focal_in),
        "n_focal_total": int(n_focal_in + n_focal_out),
        "pct_focal_in_biome": round(pct_focal, 1),
        "n_atlas_in_biome": int(n_atlas_in),
        "n_atlas_total": int(atlas_n),
        "pct_atlas_in_biome": round(pct_atlas, 1),
        "fold_enrichment": round(pct_focal / pct_atlas if pct_atlas > 0 else float("nan"), 2),
        "fisher_odds_ratio": round(float(odds), 3),
        "fisher_p_one_sided": float(p),
    }

# === H1: NB16 — Cyanobacteriia × marine ===
print("\n--- H1: NB16 Cyanobacteriia × marine/photic biome enrichment ---", flush=True)
cyano = env[env["class"] == "c__Cyanobacteriia"]
print(f"  Cyanobacteriia species: {len(cyano):,}", flush=True)
h1a = fisher_enrichment(
    cyano["is_marine"].sum(), (~cyano["is_marine"]).sum(),
    atlas_marine, atlas_n - atlas_marine,
    "Cyanobacteriia × marine"
)
print(f"  {h1a}", flush=True)
h1b = fisher_enrichment(
    cyano["is_photic_aquatic"].sum(), (~cyano["is_photic_aquatic"]).sum(),
    atlas_photic, atlas_n - atlas_photic,
    "Cyanobacteriia × photic aquatic"
)
print(f"  {h1b}", flush=True)

# === H2: NB12 — Mycobacteriaceae × soil + host-pathogen ===
print("\n--- H2: NB12 Mycobacteriaceae × soil + host-pathogen biome enrichment ---", flush=True)
myco = env[env["family"] == "f__Mycobacteriaceae"]
print(f"  Mycobacteriaceae species: {len(myco):,}", flush=True)
h2a = fisher_enrichment(
    myco["is_soil"].sum(), (~myco["is_soil"]).sum(),
    atlas_soil, atlas_n - atlas_soil,
    "Mycobacteriaceae × soil"
)
print(f"  {h2a}", flush=True)
h2b = fisher_enrichment(
    myco["is_hostpath"].sum(), (~myco["is_hostpath"]).sum(),
    atlas_hostpath, atlas_n - atlas_hostpath,
    "Mycobacteriaceae × host-pathogen"
)
print(f"  {h2b}", flush=True)
# Combined: soil OR host-pathogen
myco_combined_in = (myco["is_soil"] | myco["is_hostpath"]).sum()
atlas_combined = (env["is_soil"] | env["is_hostpath"]).sum()
h2c = fisher_enrichment(
    myco_combined_in, len(myco) - myco_combined_in,
    atlas_combined, atlas_n - atlas_combined,
    "Mycobacteriaceae × (soil OR host-pathogen)"
)
print(f"  {h2c}", flush=True)

# === H3: Phase 1B Bacteroidota × gut/rumen ===
print("\n--- H3: Bacteroidota × gut/rumen biome enrichment ---", flush=True)
bact = env[env["phylum"] == "p__Bacteroidota"]
print(f"  Bacteroidota species: {len(bact):,}", flush=True)
h3 = fisher_enrichment(
    bact["is_gut_or_rumen"].sum(), (~bact["is_gut_or_rumen"]).sum(),
    atlas_gut, atlas_n - atlas_gut,
    "Bacteroidota × gut/rumen"
)
print(f"  {h3}", flush=True)

# === Bonus: phylum-level biome distribution heat map ===
print("\n--- Phylum-level biome distribution (top 10 phyla) ---", flush=True)
top_phyla = env["phylum"].value_counts().head(10).index.tolist()
biome_cols = ["is_marine", "is_photic_aquatic", "is_soil", "is_hostpath", "is_gut_or_rumen"]
phylum_biome = pd.DataFrame(index=top_phyla, columns=biome_cols, dtype=float)
for phy in top_phyla:
    sub = env[env["phylum"] == phy]
    for col in biome_cols:
        phylum_biome.loc[phy, col] = 100 * sub[col].sum() / max(len(sub), 1)
print(phylum_biome.round(1).to_string(), flush=True)

# === MGnify biome × focal clade direct counts ===
print("\n--- MGnify biome distribution for focal clades (clean categorical) ---", flush=True)
def mgnify_biome_breakdown(focal_df, label):
    biomes_only = focal_df[focal_df["mgnify_biomes"].notna()]
    print(f"  {label} (n={len(focal_df)}, {len(biomes_only)} with MGnify biome):")
    if len(biomes_only) == 0:
        print(f"    no MGnify biome assignments")
        return {}
    biome_counts = {}
    for biome_str in biomes_only["mgnify_biomes"]:
        for b in biome_str.split(";"):
            biome_counts[b] = biome_counts.get(b, 0) + 1
    sorted_b = sorted(biome_counts.items(), key=lambda x: -x[1])
    for b, n in sorted_b[:8]:
        print(f"    {b}: {n}")
    return dict(sorted_b)

mg_cyano = mgnify_biome_breakdown(cyano, "Cyanobacteriia")
mg_myco = mgnify_biome_breakdown(myco, "Mycobacteriaceae")
mg_bact = mgnify_biome_breakdown(bact, "Bacteroidota")

# Save results
all_tests = [h1a, h1b, h2a, h2b, h2c, h3]
hyp_df = pd.DataFrame(all_tests)
hyp_df.to_csv(DATA_DIR / "p4d1_biome_enrichment_tests.tsv", sep="\t", index=False)

diagnostics = {
    "phase": "4", "deliverable": "P4-D1 NB23",
    "purpose": "Biome enrichment for pre-registered atlas findings",
    "n_species": int(atlas_n),
    "atlas_biome_fractions": {
        "marine": int(atlas_marine), "photic_aquatic": int(atlas_photic),
        "soil": int(atlas_soil), "hostpath": int(atlas_hostpath), "gut_or_rumen": int(atlas_gut),
    },
    "h1_cyanobacteriia": {"marine": h1a, "photic_aquatic": h1b, "mgnify_biomes": mg_cyano},
    "h2_mycobacteriaceae": {"soil": h2a, "hostpath": h2b, "soil_or_hostpath": h2c, "mgnify_biomes": mg_myco},
    "h3_bacteroidota": {"gut_or_rumen": h3, "mgnify_biomes": mg_bact},
    "phylum_biome_pct_distribution": phylum_biome.round(2).to_dict(),
    "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(DATA_DIR / "p4d1_diagnostics.json", "w") as f:
    json.dump(diagnostics, f, indent=2, default=str)

# Figure: 3-panel hypothesis enrichment
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

def plot_enrichment(ax, tests, title):
    labels = [t["label"].split(" × ")[1][:25] for t in tests]
    focal_pcts = [t["pct_focal_in_biome"] for t in tests]
    atlas_pcts = [t["pct_atlas_in_biome"] for t in tests]
    x = np.arange(len(labels)); w = 0.35
    ax.bar(x - w/2, focal_pcts, w, label="focal clade", color="#1f77b4")
    ax.bar(x + w/2, atlas_pcts, w, label="atlas-wide", color="lightgray")
    for i, t in enumerate(tests):
        sig = "***" if t["fisher_p_one_sided"] < 1e-10 else "**" if t["fisher_p_one_sided"] < 1e-3 else "*" if t["fisher_p_one_sided"] < 0.05 else "ns"
        ax.text(i, max(focal_pcts[i], atlas_pcts[i]) + 2, f"{sig}\n{t['fold_enrichment']:.1f}×",
                ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=15, fontsize=9)
    ax.set_ylabel("% species in biome")
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

plot_enrichment(axes[0], [h1a, h1b], f"H1: Cyanobacteriia (n={len(cyano)})")
plot_enrichment(axes[1], [h2a, h2b, h2c], f"H2: Mycobacteriaceae (n={len(myco)})")
plot_enrichment(axes[2], [h3], f"H3: Bacteroidota (n={len(bact)})")

plt.tight_layout()
plt.savefig(FIG_DIR / "p4d1_clade_biome_panel.png", dpi=120, bbox_inches="tight")
print(f"\nWrote figure", flush=True)
print(f"=== DONE in {time.time()-t0:.1f}s ===", flush=True)
