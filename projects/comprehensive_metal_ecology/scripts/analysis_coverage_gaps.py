"""
Coverage gap investigation: resistance/cofactor subset coverage and unmatched genera.
"""
import pandas as pd
import numpy as np
from scipy import stats

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)

# ─── Load data ─────────────────────────────────────────────────────────────────

soil = pd.read_csv("data/soil_sample_pgls_dataset.csv")
trait = pd.read_csv("data/genus_trait_table.csv")
samples = pd.read_csv("data/genus_microbeatlas_sample_counts.csv")  # all 3,433 MA genera

print(f"soil_sample_pgls_dataset: {len(soil):,} genera")
print(f"genus_trait_table:        {len(trait):,} genera")
print(f"genus_microbeatlas_sample_counts: {len(samples):,} genera")

# ─── GAP 1: Resistance / cofactor subset coverage ──────────────────────────────

print("\n" + "=" * 70)
print("GAP 1 — Functional subset coverage (within 1,543-genus PGLS panel)")
print("=" * 70)

# Who is present vs absent in each subset
has_res = soil["resistance_per_mb"].notna()
has_cof = soil["cofactor_per_mb"].notna()

print(f"\n  resistance_per_mb: {has_res.sum()} present, {(~has_res).sum()} absent "
      f"({has_res.mean():.1%} coverage)")
print(f"  cofactor_per_mb:   {has_cof.sum()} present, {(~has_cof).sum()} absent "
      f"({has_cof.mean():.1%} coverage)")

def compare_groups(df, mask, label):
    """Compare present vs absent groups on key variables."""
    present = df[mask]
    absent  = df[~mask]

    numeric_cols = [
        ("mean_levins_B_std",  "B_std"),
        ("mean_genome_mb",     "genome_Mb"),
        ("ko_per_mb_primary",  "ko_per_mb"),
        ("n_soil_samples",     "n_soil_samples"),
    ]

    print(f"\n  === {label} ===")
    print(f"  {'Variable':<20} {'Present (n={:,})'.format(len(present)):>22}"
          f"{'Absent (n={:,})'.format(len(absent)):>22}  {'Mann–Whitney p':>14}")
    print(f"  {'-'*20}  {'-'*20}  {'-'*20}  {'-'*14}")

    for col, name in numeric_cols:
        if col not in df.columns:
            continue
        p_vals = present[col].dropna()
        a_vals = absent[col].dropna()
        if len(p_vals) < 5 or len(a_vals) < 5:
            continue
        stat, pval = stats.mannwhitneyu(p_vals, a_vals, alternative="two-sided")
        p_str = f"{pval:.3e}" if pval < 0.001 else f"{pval:.3f}"
        print(f"  {name:<20}  "
              f"median={np.median(p_vals):>8.3f} IQR={np.percentile(p_vals,25):.2f}–{np.percentile(p_vals,75):.2f}  "
              f"median={np.median(a_vals):>8.3f} IQR={np.percentile(a_vals,25):.2f}–{np.percentile(a_vals,75):.2f}  "
              f"{p_str:>14}")

    # Phylum distribution
    print(f"\n  Phylum distribution (top 6):")
    phy_p = present["phylum"].value_counts(normalize=True).head(6)
    phy_a = absent["phylum"].value_counts(normalize=True).head(6)
    all_phy = pd.Index(phy_p.index.tolist() + phy_a.index.tolist()).unique()
    print(f"  {'Phylum':<22} {'Present %':>10} {'Absent %':>10}")
    for phy in all_phy[:8]:
        pp = phy_p.get(phy, 0) * 100
        ap = phy_a.get(phy, 0) * 100
        print(f"  {phy:<22} {pp:>9.1f}% {ap:>9.1f}%")

compare_groups(soil, has_res, "Resistance subset (resistance_per_mb)")
compare_groups(soil, has_cof, "Cofactor subset (cofactor_per_mb)")

# Are absent genera enriched in zero-density KO sets?
# Check ko_per_mb_primary for absent genera — low KO density → fewer resistance KOs detected
print("\n  Fraction with ko_per_mb_primary = 0:")
print(f"    Resistance absent: {(soil.loc[~has_res, 'ko_per_mb_primary'] == 0).mean():.1%}")
print(f"    Cofactor absent:   {(soil.loc[~has_cof, 'ko_per_mb_primary'] == 0).mean():.1%}")
print(f"    All present:       {(soil.loc[has_res & has_cof, 'ko_per_mb_primary'] == 0).mean():.1%}")

# What fraction of absent genera have PRIMARY KO density < 5 KOs/Mb?
thresh = 5.0
print(f"\n  Fraction with ko_per_mb_primary < {thresh} KO/Mb:")
print(f"    Resistance absent: {(soil.loc[~has_res, 'ko_per_mb_primary'] < thresh).mean():.1%}")
print(f"    Cofactor absent:   {(soil.loc[~has_cof, 'ko_per_mb_primary'] < thresh).mean():.1%}")
print(f"    All present:       {(soil.loc[has_res & has_cof, 'ko_per_mb_primary'] < thresh).mean():.1%}")

# B_std distribution check: do missing genera bias toward specialist or generalist?
bstd_res_absent = soil.loc[~has_res, "mean_levins_B_std"].dropna()
bstd_res_present = soil.loc[has_res, "mean_levins_B_std"].dropna()
pct_specialist_absent  = (bstd_res_absent  < 0.1).mean()
pct_specialist_present = (bstd_res_present < 0.1).mean()
print(f"\n  B_std < 0.1 (extreme specialists):")
print(f"    Resistance absent:  {pct_specialist_absent:.1%}")
print(f"    Resistance present: {pct_specialist_present:.1%}")

# ─── GAP 2: Unmatched MicrobeAtlas genera ──────────────────────────────────────

print("\n" + "=" * 70)
print("GAP 2 — Unmatched genera (MicrobeAtlas present, GTDB absent)")
print("=" * 70)

# The PGLS panel (1,543 genera) = matched genera
pgls_genera = set(soil["genus_lower"].dropna())
print(f"\n  PGLS panel genera: {len(pgls_genera):,}")

# genus_trait_table has 2,851 genera with B_std data (≥5 samples)
# Many of these lack GTDB KO data → unmatched
trait_genera = set(trait["genus_lower"].dropna())
matched_in_trait   = trait_genera & pgls_genera
unmatched_in_trait = trait_genera - pgls_genera
print(f"  genus_trait_table genera: {len(trait_genera):,}")
print(f"    → matched to PGLS:    {len(matched_in_trait):,}  ({len(matched_in_trait)/len(trait_genera):.1%})")
print(f"    → unmatched (no GTDB KO): {len(unmatched_in_trait):,}  ({len(unmatched_in_trait)/len(trait_genera):.1%})")

# All MicrobeAtlas genera (including those below the ≥5-sample filter)
all_ma_genera = set(samples["genus_lower"].dropna())
print(f"\n  genus_microbeatlas_sample_counts genera: {len(all_ma_genera):,}")
unmatched_all = all_ma_genera - pgls_genera
print(f"    → unmatched (no PGLS entry):   {len(unmatched_all):,}  ({len(unmatched_all)/len(all_ma_genera):.1%})")

# ─── Characterize unmatched genera ─────────────────────────────────────────────

# Use genus_trait_table for those with B_std (≥5 samples)
matched_trait   = trait[trait["genus_lower"].isin(pgls_genera)].copy()
unmatched_trait = trait[~trait["genus_lower"].isin(pgls_genera)].copy()

print(f"\n  Characterization via genus_trait_table (B_std-qualified genera):")
print(f"  matched n={len(matched_trait)}, unmatched n={len(unmatched_trait)}")

# B_std comparison
bstd_m = matched_trait["mean_levins_B_std"].dropna()
bstd_u = unmatched_trait["mean_levins_B_std"].dropna()
stat, pval = stats.mannwhitneyu(bstd_m, bstd_u, alternative="two-sided")
print(f"\n  B_std comparison:")
print(f"    Matched:   median={np.median(bstd_m):.4f}, IQR={np.percentile(bstd_m,25):.4f}–{np.percentile(bstd_m,75):.4f}")
print(f"    Unmatched: median={np.median(bstd_u):.4f}, IQR={np.percentile(bstd_u,25):.4f}–{np.percentile(bstd_u,75):.4f}")
print(f"    Mann–Whitney p = {pval:.3e}")

# Sample count comparison — use MicrobeAtlas sample counts file
# Join to get n_samples for both groups
samples_map = samples.set_index("genus_lower")["n_samples"]
matched_trait["n_samples"]   = matched_trait["genus_lower"].map(samples_map)
unmatched_trait["n_samples"] = unmatched_trait["genus_lower"].map(samples_map)

ns_m = matched_trait["n_samples"].dropna()
ns_u = unmatched_trait["n_samples"].dropna()
stat2, pval2 = stats.mannwhitneyu(ns_m, ns_u, alternative="two-sided")
print(f"\n  MicrobeAtlas sample count comparison:")
print(f"    Matched:   median={np.median(ns_m):.0f}, IQR={np.percentile(ns_m,25):.0f}–{np.percentile(ns_m,75):.0f}")
print(f"    Unmatched: median={np.median(ns_u):.0f}, IQR={np.percentile(ns_u,25):.0f}–{np.percentile(ns_u,75):.0f}")
print(f"    Mann–Whitney p = {pval2:.3e}")

# Fraction of total reads in unmatched genera
total_samples_matched   = ns_m.sum()
total_samples_unmatched = ns_u.sum()
total_all = total_samples_matched + total_samples_unmatched
print(f"\n  Total 16S sample detections (proxy for abundance representation):")
print(f"    Matched genera:   {total_samples_matched:,.0f}  ({total_samples_matched/total_all:.1%})")
print(f"    Unmatched genera: {total_samples_unmatched:,.0f}  ({total_samples_unmatched/total_all:.1%})")

# Top unmatched genera by sample count (most common unmatched taxa)
top_unmatched = unmatched_trait.nlargest(20, "n_samples")[
    ["genus_lower", "phylum", "mean_levins_B_std", "n_samples"]
]
print(f"\n  Top 20 unmatched genera by sample count:")
print(top_unmatched.to_string(index=False))

# Phylum distribution
print(f"\n  Phylum distribution:")
phy_m = matched_trait["phylum"].value_counts(normalize=True)
phy_u = unmatched_trait["phylum"].value_counts(normalize=True)
all_phyla = pd.Index(phy_m.index[:8].tolist() + phy_u.index[:5].tolist()).unique()
print(f"  {'Phylum':<25} {'Matched %':>10} {'Unmatched %':>11}")
for phy in all_phyla[:10]:
    pm = phy_m.get(phy, 0) * 100
    pu = phy_u.get(phy, 0) * 100
    print(f"  {phy:<25} {pm:>9.1f}% {pu:>10.1f}%")

# Taxonomy name mismatch — does genus_trait_table have a GTDB column?
if "gtdb_genus_lower" in trait.columns:
    print(f"\n  SILVA vs GTDB name reconciliation:")
    # Among unmatched genera: do they have a GTDB genus name that IS in the PGLS panel?
    unmatched_with_gtdb = unmatched_trait[unmatched_trait["gtdb_genus_lower"].notna()].copy()
    print(f"    Unmatched genera with a gtdb_genus_lower entry: {len(unmatched_with_gtdb):,}")
    # Does that GTDB name appear in pgls_genera?
    crossover = unmatched_with_gtdb[unmatched_with_gtdb["gtdb_genus_lower"].isin(pgls_genera)]
    print(f"    Of those, gtdb_genus_lower IS in the PGLS panel: {len(crossover):,}")
    if len(crossover) > 0:
        print(f"    → These genera are matched under a different GTDB name (taxonomy gap).")
        print(f"\n    Examples (SILVA name → GTDB name):")
        ex = crossover[["genus_lower", "gtdb_genus_lower", "phylum", "mean_levins_B_std", "n_samples"]].head(15)
        print(ex.to_string(index=False))
    else:
        print(f"    → No crossover found: unmatched genera genuinely lack GTDB representatives.")

    # Also: among matched genera, how many have a DIFFERENT GTDB name?
    matched_with_gtdb = matched_trait[matched_trait["gtdb_genus_lower"].notna()].copy()
    name_diff = matched_with_gtdb[
        matched_with_gtdb["genus_lower"] != matched_with_gtdb["gtdb_genus_lower"]
    ]
    print(f"\n    Matched genera where SILVA name ≠ GTDB name: {len(name_diff):,} of {len(matched_with_gtdb):,}")
    if len(name_diff) > 0:
        print(f"    Examples:")
        print(name_diff[["genus_lower", "gtdb_genus_lower", "phylum"]].head(10).to_string(index=False))

# Rarity distribution
print(f"\n  Rarity profile of unmatched genera:")
for thresh in [10, 50, 100, 500]:
    frac = (ns_u < thresh).mean()
    print(f"    < {thresh:,} sample detections: {frac:.1%} of unmatched genera ({int(frac*len(ns_u)):,} genera)")

print(f"\n  For comparison, matched genera:")
for thresh in [10, 50, 100, 500]:
    frac = (ns_m < thresh).mean()
    print(f"    < {thresh:,} sample detections: {frac:.1%} of matched genera ({int(frac*len(ns_m)):,} genera)")

print("\nDone.")
