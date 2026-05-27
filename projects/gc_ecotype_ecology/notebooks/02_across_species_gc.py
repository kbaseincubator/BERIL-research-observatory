# %%
"""
Notebook 02: Across-Species GC Patterns (Sanity Check)

Goal: Reproduce the established literature finding that GC tracks environmental
niche at the cross-species level. This functions as a positive control: if we
can't see GC × environment patterns when pooling across species, the dataset or
labels are too noisy for the within-species analysis.

Approach: Use isolation_source (highest coverage at 84%) plus env_broad_scale.
Compute per-species mean GC, then group species by their dominant environmental
category and compare distributions. Also report overall genome-level patterns.

Outputs:
  - data/02_isolation_source_categories.csv  (harmonized iso source labels)
  - data/02_gc_by_isolation_source.csv
  - data/02_gc_by_env_broad_scale.csv
  - figures/02_gc_vs_isolation_source.png
  - figures/02_gc_vs_env_broad_scale.png
  - figures/02_gc_vs_genome_size.png  (Wallace's "GC ~ genome size" classic)
"""

# %%
import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# %%
PROJECT_DIR = "/home/justaddcoffee/BERIL-research-observatory/projects/gc_ecotype_ecology"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
FIG_DIR = os.path.join(PROJECT_DIR, "figures")

# %%
df = pd.read_parquet(os.path.join(DATA_DIR, "genome_gc_env.parquet"))
print(f"Loaded {len(df):,} genomes")
qual = df[df["passes_quality"] & df["gc_pct"].notna()].copy()
print(f"After quality filter: {len(qual):,}")

# %%
# -----------------------------------------------------------------------------
# Step 1: Harmonize isolation_source into broad categories
# -----------------------------------------------------------------------------
# isolation_source is free-text. Build a regex-based mapper to coarse buckets.
# We err on the side of "unknown" — only confident matches get a label.
CATEGORY_RULES = [
    ("human_clinical", r"\b(human|patient|hospital|clinical|sputum|blood|urine|stool|wound|cerebrospinal|csf|nasal|throat|swab|abscess|pus|biopsy)\b"),
    ("animal_host",    r"\b(cow|cattle|bovine|pig|swine|porcine|chicken|poultry|sheep|ovine|goat|horse|equine|dog|canine|cat|feline|mouse|rat|rodent|fish|salmon|trout|shrimp|insect|tick|mosquito|primate|monkey|bat|bird|veterinary)\b"),
    ("plant_host",     r"\b(plant|leaf|leaves|root|rhizosphere|rhizoplane|phyllosphere|seed|fruit|stem|wheat|rice|maize|corn|tomato|tree|forest litter|crop|grass|moss|legume|tuber|flower)\b"),
    ("soil",           r"\b(soil|sediment|loam|tundra|permafrost|peat|paddy|compost|rhizosphere)\b"),
    ("marine",         r"\b(marine|seawater|ocean|sea water|coastal|pelagic|deep sea|coral|sponge|estuarine|brine|saltwater|salt marsh)\b"),
    ("freshwater",     r"\b(freshwater|fresh water|lake|river|pond|stream|spring|aquifer|groundwater|drinking water|tap water)\b"),
    ("wastewater",     r"\b(wastewater|sewage|sludge|effluent|treatment plant|activated sludge|biofilm reactor|anaerobic digest)\b"),
    ("food",           r"\b(food|cheese|yogurt|milk|dairy|meat|beef|pork|poultry product|chicken meat|salami|sausage|fermented|kimchi|kombucha|wine|beer|bread|fish product|seafood)\b"),
    ("built_env",      r"\b(built environment|hospital surface|indoor|building|surface swab|public transit|subway|air conditioner|shower|toilet|catheter|implant|prosthesis|dust|HVAC)\b"),
    ("industrial",     r"\b(bioreactor|fermentor|fermenter|industrial|oil|petroleum|hydrocarbon|mining|tailings|coal|landfill|contamin)\b"),
    ("extreme",        r"\b(hot spring|thermal|hydrothermal|geyser|hypersaline|salt lake|brine|acid mine|acidic|alkaline|desert|cave|subsurface|deep subsurface)\b"),
    ("plant_microbiome", r"\b(endophyte|nodule|mycorrhiz|phylloplane)\b"),
    ("gut_environmental", r"\b(gut|fecal|feces|faec|caecum|cecum|intestin|rumen|colon|gastrointestinal)\b"),
]

# %%
def categorize(text):
    if pd.isna(text) or not isinstance(text, str):
        return None
    s = text.lower().strip()
    if not s or s in {"missing", "not applicable", "not available", "n/a", "na",
                      "unknown", "not collected", "not specified", "none", "not provided"}:
        return None
    for cat, pat in CATEGORY_RULES:
        if re.search(pat, s):
            return cat
    return "other"

# %%
qual["iso_category"] = qual["isolation_source"].apply(categorize)
qual["env_broad_simple"] = qual["env_broad_scale"].apply(categorize)

# %%
# -----------------------------------------------------------------------------
# Step 2: Distribution of isolation_source categories
# -----------------------------------------------------------------------------
iso_counts = qual["iso_category"].value_counts(dropna=False)
print("\n=== Isolation source category coverage (genome-level) ===")
print(iso_counts.to_string())
iso_counts.to_csv(os.path.join(DATA_DIR, "02_isolation_source_categories.csv"))

# %%
# -----------------------------------------------------------------------------
# Step 3: GC by isolation_source category (genome-level)
# -----------------------------------------------------------------------------
gc_by_iso = (
    qual.dropna(subset=["iso_category"])
    .groupby("iso_category")["gc_pct"]
    .agg(["count", "mean", "std", "median"])
    .sort_values("count", ascending=False)
    .round(2)
)
print("\n=== GC% by isolation_source category (genome-level) ===")
print(gc_by_iso.to_string())
gc_by_iso.to_csv(os.path.join(DATA_DIR, "02_gc_by_isolation_source.csv"))

# %%
# -----------------------------------------------------------------------------
# Step 4: GC by env_broad_scale (raw + simplified)
# -----------------------------------------------------------------------------
gc_by_envb = (
    qual.dropna(subset=["env_broad_scale"])
    .assign(env_broad_lc=lambda d: d["env_broad_scale"].str.lower())
    .groupby("env_broad_lc")["gc_pct"]
    .agg(["count", "mean", "std", "median"])
    .query("count >= 30")
    .sort_values("count", ascending=False)
    .round(2)
    .head(40)
)
print("\n=== GC% by env_broad_scale (top 40 with N >= 30) ===")
print(gc_by_envb.to_string())
gc_by_envb.to_csv(os.path.join(DATA_DIR, "02_gc_by_env_broad_scale.csv"))

# %%
# -----------------------------------------------------------------------------
# Step 5: Species-level test — collapse to per-species mean GC × dominant category
# -----------------------------------------------------------------------------
# For each species, what is its dominant iso_category, and the mean GC across
# its genomes? This decouples from genome-count weighting.
sp_summary = []
for sp, sub in qual.groupby("gtdb_species_clade_id"):
    sub_cat = sub.dropna(subset=["iso_category"])
    if len(sub_cat) < 5:
        continue
    dom_cat = sub_cat["iso_category"].mode().iloc[0]
    sp_summary.append({
        "species": sp,
        "n_genomes": len(sub),
        "mean_gc": sub["gc_pct"].mean(),
        "median_gc": sub["gc_pct"].median(),
        "dominant_iso_category": dom_cat,
        "mean_genome_size": sub["genome_size"].mean(),
    })
sp_df = pd.DataFrame(sp_summary)
print(f"\n=== Species-level summary: {len(sp_df):,} species with dominant iso category ===")
gc_by_iso_sp = (
    sp_df.groupby("dominant_iso_category")["mean_gc"]
    .agg(["count", "mean", "std", "median"])
    .sort_values("count", ascending=False)
    .round(2)
)
print(gc_by_iso_sp.to_string())
gc_by_iso_sp.to_csv(os.path.join(DATA_DIR, "02_gc_by_iso_species_level.csv"))
sp_df.to_csv(os.path.join(DATA_DIR, "02_species_summary.csv"), index=False)

# %%
# -----------------------------------------------------------------------------
# Step 6: Figures
# -----------------------------------------------------------------------------
# Fig 1: GC by isolation_source (genome-level) — boxplot
fig, ax = plt.subplots(figsize=(11, 5))
order = gc_by_iso.index.tolist()
data = [qual.loc[qual["iso_category"] == c, "gc_pct"].values for c in order]
bp = ax.boxplot(data, tick_labels=order, showfliers=False, patch_artist=True)
for p in bp["boxes"]:
    p.set(facecolor="#4c72b0", alpha=0.7)
ax.set_ylabel("GC content (%)")
ax.set_xlabel("Isolation source category")
ax.set_title("GC content by isolation source category (genome-level, all species pooled)")
plt.xticks(rotation=30, ha="right")
for i, c in enumerate(order):
    ax.text(i + 1, 85, f"n={gc_by_iso.loc[c, 'count']:.0f}",
            ha="center", fontsize=8, color="grey")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "02_gc_vs_isolation_source.png"), dpi=150)
plt.close()

# %%
# Fig 2: Species-level boxplot
fig, ax = plt.subplots(figsize=(11, 5))
order = gc_by_iso_sp.index.tolist()
data = [sp_df.loc[sp_df["dominant_iso_category"] == c, "mean_gc"].values for c in order]
bp = ax.boxplot(data, tick_labels=order, showfliers=True, patch_artist=True)
for p in bp["boxes"]:
    p.set(facecolor="#55a868", alpha=0.7)
ax.set_ylabel("Per-species mean GC content (%)")
ax.set_xlabel("Dominant isolation source category for the species")
ax.set_title(f"Per-species mean GC by dominant isolation source (n={len(sp_df):,} species)")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "02_gc_vs_iso_species_level.png"), dpi=150)
plt.close()

# %%
# Fig 3: GC vs genome size — classic Wallace pattern
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(qual["genome_size"] / 1e6, qual["gc_pct"], s=2, alpha=0.05, color="#444")
ax.set_xlabel("Genome size (Mbp)")
ax.set_ylabel("GC content (%)")
ax.set_title(f"GC vs genome size across {len(qual):,} bacterial genomes")
ax.set_xlim(0, 15)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "02_gc_vs_genome_size.png"), dpi=150)
plt.close()

# %%
# Save categorized master for downstream notebooks
qual.to_parquet(os.path.join(DATA_DIR, "genome_gc_env_categorized.parquet"), index=False)
print("\nNotebook 02 complete.")
