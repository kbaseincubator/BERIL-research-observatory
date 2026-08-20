"""
NB02 univariate per-pathway tests.

For each of the 80 GapMind pathways, ask: is pathway completeness
significantly different between isolates and MAGs, both pooled and
within GTDB family (Mantel-Haenszel, controlling for phylogenetic
confounding)?
"""
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.contingency_tables import StratifiedTable

PROJ = Path(__file__).resolve().parent.parent
DATA = PROJ / "data"

feat = pd.read_parquet(DATA / "features.parquet")
pathway_cols = [c for c in feat.columns if c.startswith(("aa__", "carbon__"))]
print(f"Cohort: {len(feat):,} genomes ({int(feat['is_isolate'].sum()):,} isolates, {int((1-feat['is_isolate']).sum()):,} MAGs)")
print(f"Pathways: {len(pathway_cols)}")

# Restrict the within-family test to families with >= 5 of both labels
fam_counts = feat.groupby("family")["is_isolate"].agg(n_iso="sum", n_total="size")
fam_counts["n_mag"] = fam_counts["n_total"] - fam_counts["n_iso"]
balanced_fams = fam_counts[(fam_counts.n_iso >= 5) & (fam_counts.n_mag >= 5)].index.tolist()
feat_fam = feat[feat["family"].isin(balanced_fams)].copy()
print(f"Balanced family subset: {len(feat_fam):,} genomes across {len(balanced_fams)} families")

rows = []
for path in pathway_cols:
    # Pooled 2x2 table: pathway complete vs label
    iso_comp = int(((feat["is_isolate"] == 1) & (feat[path] == 1)).sum())
    iso_inc = int(((feat["is_isolate"] == 1) & (feat[path] == 0)).sum())
    mag_comp = int(((feat["is_isolate"] == 0) & (feat[path] == 1)).sum())
    mag_inc = int(((feat["is_isolate"] == 0) & (feat[path] == 0)).sum())

    # Pooled Fisher
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pooled_or, pooled_p = stats.fisher_exact([[iso_comp, iso_inc], [mag_comp, mag_inc]])
    iso_rate = iso_comp / (iso_comp + iso_inc) if (iso_comp + iso_inc) else float("nan")
    mag_rate = mag_comp / (mag_comp + mag_inc) if (mag_comp + mag_inc) else float("nan")

    # Within-family Mantel-Haenszel pooled OR (controls for phylogeny)
    tables = []
    for fam, sub in feat_fam.groupby("family"):
        a = int(((sub["is_isolate"] == 1) & (sub[path] == 1)).sum())
        b = int(((sub["is_isolate"] == 1) & (sub[path] == 0)).sum())
        c = int(((sub["is_isolate"] == 0) & (sub[path] == 1)).sum())
        d = int(((sub["is_isolate"] == 0) & (sub[path] == 0)).sum())
        if (a + b) > 0 and (c + d) > 0 and ((a + c) > 0 and (b + d) > 0):
            tables.append([[a, b], [c, d]])
    if len(tables) >= 5:
        try:
            arr = np.array(tables).transpose(1, 2, 0)  # (2,2,n_strata) shape required
            st = StratifiedTable(arr)
            mh_or = float(st.oddsratio_pooled)
            mh_p = float(st.test_null_odds().pvalue)
            mh_lo, mh_hi = (float(x) for x in st.oddsratio_pooled_confint())
        except Exception as exc:
            print(f"  [warn] StratifiedTable failed for {path}: {exc}")
            mh_or = mh_p = mh_lo = mh_hi = float("nan")
    else:
        mh_or = mh_p = mh_lo = mh_hi = float("nan")

    rows.append(
        dict(
            pathway=path,
            metabolic_category=path.split("__")[0],
            pathway_name=path.split("__", 1)[1],
            iso_complete_rate=iso_rate,
            mag_complete_rate=mag_rate,
            iso_minus_mag=iso_rate - mag_rate,
            pooled_or=pooled_or,
            pooled_p=pooled_p,
            mh_or=mh_or,
            mh_p=mh_p,
            mh_ci_lo=mh_lo,
            mh_ci_hi=mh_hi,
            n_strata=len(tables),
        )
    )

res = pd.DataFrame(rows)
# BH-FDR
res["pooled_q"] = multipletests(res["pooled_p"], method="fdr_bh")[1]
mh_p_valid = res["mh_p"].notna()
res["mh_q"] = np.nan
n_valid = int(mh_p_valid.sum())
print(f"\n{n_valid}/{len(res)} pathways had valid Mantel-Haenszel tests")
if n_valid > 0:
    res.loc[mh_p_valid, "mh_q"] = multipletests(res.loc[mh_p_valid, "mh_p"].values, method="fdr_bh")[1]
res = res.sort_values("iso_minus_mag", ascending=False)
res.to_csv(DATA / "per_pathway_or.tsv", sep="\t", index=False, float_format="%.4g")

print("\nTop 10 pathways by iso-vs-MAG completeness gap:")
print(
    res[["metabolic_category", "pathway_name", "iso_complete_rate", "mag_complete_rate", "iso_minus_mag", "pooled_or", "pooled_q", "mh_or", "mh_q"]]
    .head(10)
    .to_string(index=False)
)

print("\nSummary by category (MH-significant at q<0.05, mh_or>1 means isolate-enriched):")
for cat in ["aa", "carbon"]:
    sub = res[res.metabolic_category == cat]
    sig_iso = int(((sub.mh_q < 0.05) & (sub.mh_or > 1)).sum())
    sig_mag = int(((sub.mh_q < 0.05) & (sub.mh_or < 1)).sum())
    ns = int((sub.mh_q >= 0.05).sum()) + int(sub.mh_q.isna().sum())
    print(f"  {cat}: {sig_iso} isolate-enriched, {sig_mag} MAG-enriched, {ns} ns/missing (of {len(sub)} pathways)")

print(f"\nWrote data/per_pathway_or.tsv ({len(res)} rows)")
