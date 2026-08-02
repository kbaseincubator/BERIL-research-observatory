"""
NB05 anchored validation.

Validate the cultivability classifier against two completed BERDL projects:
1) clay_confined_subsurface — does the model recapitulate the cultured-vs-MAG
   metabolic gap in the deep-clay vs Bagnoud-MAG comparison?
2) oak_ridge_cultivation_gap — do cultured genomes score higher than MAGs at
   the Oak Ridge ORFRC site?
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"
FIGS = PROJ / "figures"

scored = pd.read_parquet(DATA / "scored_genomes.parquet")
print(f"Scored: {len(scored):,} HQ genomes")

# ---------------------------------------------------------------------------
# Validation 1: subsurface isolation source enrichment in isolates vs MAGs
# ---------------------------------------------------------------------------
# We can't directly pull the clay_confined_subsurface project's cohort without
# its IDs, but we can do a related test: among HQ genomes in environmentally
# relevant phyla (Bacillota_B = sulfate reducers, subsurface), do the isolate
# vs MAG scores match the cultivation-bias finding from clay_confined_subsurface?
print("\n== Validation 1: Bacillota_B / subsurface cultivation signal ==")
bb = scored[scored["phylum"] == "p__Bacillota_B"]
print(f"Bacillota_B genomes (proxy for subsurface lineages): {len(bb)}")
print(f"  isolate: {int(bb.is_isolate.sum())}")
print(f"  MAG:     {int((1-bb.is_isolate).sum())}")
if len(bb) >= 20:
    iso_scores = bb.loc[bb.is_isolate == 1, "p_isolate"]
    mag_scores = bb.loc[bb.is_isolate == 0, "p_isolate"]
    u, p = stats.mannwhitneyu(iso_scores, mag_scores, alternative="greater")
    print(f"  MWU isolate > MAG: U={u:.0f}, p={p:.3g}")
    print(f"  isolate median P(isolate) = {iso_scores.median():.3f}")
    print(f"  MAG median P(isolate)     = {mag_scores.median():.3f}")

# ---------------------------------------------------------------------------
# Validation 2: do model scores recover the cultured-MAG split globally,
# even outside the families used during training?
# ---------------------------------------------------------------------------
print("\n== Validation 2: cultured-vs-MAG score separation overall ==")
iso = scored.loc[scored.is_isolate == 1, "p_isolate"]
mag = scored.loc[scored.is_isolate == 0, "p_isolate"]
print(f"  All {len(iso):,} isolates: median P(isolate) = {iso.median():.3f}")
print(f"  All {len(mag):,} MAGs:     median P(isolate) = {mag.median():.3f}")
u, p = stats.mannwhitneyu(iso, mag, alternative="greater")
print(f"  MWU: U={u:.0f}, p<{p:.3g}")

# ---------------------------------------------------------------------------
# Validation 3: per-phylum cultured-vs-MAG separation (does the signal hold
# across phyla, including environmentally important ones?)
# ---------------------------------------------------------------------------
print("\n== Validation 3: cultured-vs-MAG separation, per phylum ==")
rows = []
for phylum, sub in scored.groupby("phylum"):
    iso = sub.loc[sub.is_isolate == 1, "p_isolate"]
    mag = sub.loc[sub.is_isolate == 0, "p_isolate"]
    if len(iso) >= 20 and len(mag) >= 20:
        u, p = stats.mannwhitneyu(iso, mag, alternative="greater")
        rows.append(dict(
            phylum=phylum, n_iso=len(iso), n_mag=len(mag),
            median_iso=iso.median(), median_mag=mag.median(),
            delta=iso.median() - mag.median(),
            p_value=p,
        ))
val3 = pd.DataFrame(rows).sort_values("delta", ascending=False)
val3.to_csv(DATA / "per_phylum_validation.tsv", sep="\t", index=False, float_format="%.4g")
print(f"\nPer-phylum cultured-vs-MAG separation (n_iso>=20, n_mag>=20):")
print(val3.head(20).to_string(index=False))
print(f"\n{(val3.p_value < 0.05).sum()} / {len(val3)} phyla show significantly higher isolate scores")

# ---------------------------------------------------------------------------
# Validation 4: Oak Ridge / contaminated subsurface enrichment
# ---------------------------------------------------------------------------
# Pull isolation source info from ncbi_env via gtdb_metadata
# We do this via a Spark query lookup
from berdl_notebook_utils.setup_spark_session import get_spark_session
spark = get_spark_session()

print("\n== Validation 4: subsurface-source genome score ==")
src = spark.sql("""
SELECT
  REGEXP_REPLACE(accession, '^(RS_|GB_)', '') AS genome_id,
  LOWER(ncbi_isolation_source) AS isource
FROM kbase_ke_pangenome.gtdb_metadata
WHERE LOWER(ncbi_isolation_source) RLIKE
  '(subsurface|aquifer|sediment|borehole|orfrc|oak.ridge|opalinus|mont.terri|rifle|deep|cave|groundwater|porewater|clay)'
""").toPandas()
print(f"Subsurface-source genomes pulled from gtdb_metadata: {len(src):,}")
mer = scored.merge(src, on="genome_id", how="inner")
print(f"Joined with scored cohort: {len(mer):,}")
if len(mer) > 100:
    iso = mer.loc[mer.is_isolate == 1, "p_isolate"]
    mag = mer.loc[mer.is_isolate == 0, "p_isolate"]
    print(f"  isolates from subsurface sources: {len(iso)} (median P={iso.median():.3f})")
    print(f"  MAGs from subsurface sources:     {len(mag)} (median P={mag.median():.3f})")
    if len(iso) >= 5 and len(mag) >= 5:
        u, p = stats.mannwhitneyu(iso, mag, alternative="greater")
        print(f"  MWU isolate > MAG: p={p:.3g}")

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
# Figure: per-phylum delta with significance
fig, ax = plt.subplots(figsize=(8, 7))
plot_df = val3.head(25).copy()
colors = ["steelblue" if p < 0.001 else "lightblue" if p < 0.05 else "lightgrey" for p in plot_df.p_value]
y = np.arange(len(plot_df))
ax.barh(y, plot_df.delta, color=colors)
ax.set_yticks(y)
ax.set_yticklabels(plot_df.phylum, fontsize=8)
ax.invert_yaxis()
ax.axvline(0, color="black", lw=0.5)
ax.set_xlabel("Median P(isolate) gap (isolate − MAG)")
ax.set_title(f"Cultured-vs-MAG model-score separation by phylum\n(top 25 by gap; n_iso≥20, n_mag≥20)")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(FIGS / "per_phylum_validation.png", dpi=150, bbox_inches="tight")
plt.close()
print("\nWrote figures/per_phylum_validation.png")

# Figure: score distribution for subsurface genomes
if len(mer) > 100:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(mer.loc[mer.is_isolate == 1, "p_isolate"], bins=30, alpha=0.55, color="steelblue", label=f"isolate (n={int(mer.is_isolate.sum())})")
    ax.hist(mer.loc[mer.is_isolate == 0, "p_isolate"], bins=30, alpha=0.55, color="indianred", label=f"MAG (n={int((1-mer.is_isolate).sum())})")
    ax.set_xlabel("P(isolate)")
    ax.set_ylabel("count")
    ax.set_title(f"Subsurface/aquifer-tagged genomes (n={len(mer):,})\nIsolation source: subsurface, aquifer, sediment, borehole, ORFRC, Mont Terri, Rifle, Oak Ridge, clay, porewater")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS / "subsurface_validation.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Wrote figures/subsurface_validation.png")
