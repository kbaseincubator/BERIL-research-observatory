# %%
"""
Notebook 03: Within-Species GC vs Environment (Core Analysis)

For each candidate species, test whether within-species GC content varies with
environmental category AFTER controlling for intra-species phylogenetic
structure (ANI clusters at 99% threshold).

Method per species:
  1. Restrict to quality-passing genomes with non-null iso_category.
  2. Require >= 50 genomes total AND >= 2 iso categories each with >= 10 genomes.
  3. Pull within-species ANI pairs from genome_ani where ANI >= 99.
  4. Build a sparse graph; ANI cluster = connected component.
  5. Fit two OLS models on residual GC variation:
       null: gc_pct ~ C(ani_cluster)
       alt : gc_pct ~ C(ani_cluster) + C(iso_category)
     Compute partial F-test for the iso_category effect.
  6. Multiple-testing correction (Benjamini–Hochberg) across species.

Outputs:
  - data/03_within_species_results.csv (one row per species)
  - data/03_significant_species.csv
  - figures/03_volcano.png
  - figures/03_top_species_panels.png
"""

# %%
import os
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy import stats as scistats


# %%
def benjamini_hochberg(pvals):
    """BH-FDR adjusted q-values."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / (np.arange(1, n + 1))
    # enforce monotonicity from the right
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0, 1)
    out = np.empty(n)
    out[order] = q
    return out


# %%
def design_categorical(series):
    """Return a one-hot dummy matrix (n x k-1 + intercept) like statsmodels."""
    cats = pd.Categorical(series)
    codes = cats.codes
    n = len(codes)
    k = len(cats.categories)
    if k <= 1:
        return np.ones((n, 1))
    X = np.zeros((n, k - 1))
    for j in range(1, k):
        X[codes == j, j - 1] = 1.0
    return X


# %%
def design(*blocks):
    parts = [np.ones((blocks[0].shape[0], 1))]
    parts.extend(blocks)
    return np.hstack(parts)


# %%
def ols_rss(X, y):
    """Fit OLS via least-squares; return (rss, df_resid, rank)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    resid = y - yhat
    rss = float(np.sum(resid ** 2))
    # rank-based df
    rank = int(np.linalg.matrix_rank(X))
    df_resid = len(y) - rank
    return rss, df_resid, rank


# %%
def partial_F(X_null, X_alt, y):
    """Nested-model partial F-test. X_alt must contain X_null as subspace."""
    rss_null, df_null, rank_null = ols_rss(X_null, y)
    rss_alt,  df_alt,  rank_alt  = ols_rss(X_alt,  y)
    df_diff = rank_alt - rank_null
    if df_diff <= 0 or df_alt <= 0 or rss_alt <= 0:
        return float("nan"), float("nan"), rss_null, rss_alt
    f = ((rss_null - rss_alt) / df_diff) / (rss_alt / df_alt)
    p = float(scistats.f.sf(f, df_diff, df_alt))
    return float(f), p, rss_null, rss_alt

# %%
from berdl_notebook_utils.setup_spark_session import get_spark_session

# %%
warnings.filterwarnings("ignore")

# %%
PROJECT_DIR = "/home/justaddcoffee/BERIL-research-observatory/projects/gc_ecotype_ecology"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
FIG_DIR = os.path.join(PROJECT_DIR, "figures")

# %%
ANI_THRESHOLD = 99.0          # clone-cluster threshold
MIN_TOTAL_GENOMES = 50
MIN_PER_CATEGORY = 10
MIN_CATEGORIES = 2
MAX_GENOMES_PER_SPECIES = 5000  # subsample very large species for tractability

# %%
# -----------------------------------------------------------------------------
# Load categorized master table
# -----------------------------------------------------------------------------
df = pd.read_parquet(os.path.join(DATA_DIR, "genome_gc_env_categorized.parquet"))
print(f"Loaded {len(df):,} quality-passing genomes")

# %%
# Restrict to genomes with a categorical iso assignment
df = df[df["iso_category"].notna() & (df["iso_category"] != "other")]
print(f"After dropping 'other' / NaN iso_category: {len(df):,}")

# %%
# -----------------------------------------------------------------------------
# Pick candidate species
# -----------------------------------------------------------------------------
cat_counts = (
    df.groupby(["gtdb_species_clade_id", "iso_category"])
    .size()
    .reset_index(name="n")
)
# Species-level filter
candidates = []
for sp, sub in cat_counts.groupby("gtdb_species_clade_id"):
    qualifying_cats = sub[sub["n"] >= MIN_PER_CATEGORY]
    if len(qualifying_cats) >= MIN_CATEGORIES and qualifying_cats["n"].sum() >= MIN_TOTAL_GENOMES:
        candidates.append({
            "species": sp,
            "n_categories": len(qualifying_cats),
            "n_genomes_qualifying": int(qualifying_cats["n"].sum()),
            "categories": ",".join(sorted(qualifying_cats["iso_category"].tolist())),
        })
cand_df = pd.DataFrame(candidates).sort_values("n_genomes_qualifying", ascending=False)
print(f"\nCandidate species (>= {MIN_TOTAL_GENOMES} genomes across >= {MIN_CATEGORIES} categories with >= {MIN_PER_CATEGORY} each):")
print(f"  {len(cand_df)} species")
cand_df.to_csv(os.path.join(DATA_DIR, "03_candidate_species.csv"), index=False)

# %%
# -----------------------------------------------------------------------------
# Per-species analysis loop
# -----------------------------------------------------------------------------
spark = get_spark_session()

# %%
def cluster_by_ani(genome_ids, ani_pairs, threshold=ANI_THRESHOLD):
    """Connected components of the ANI graph at the given threshold."""
    id_to_idx = {g: i for i, g in enumerate(genome_ids)}
    n = len(genome_ids)
    if len(ani_pairs) == 0:
        return np.arange(n)
    rows, cols = [], []
    for g1, g2 in ani_pairs:
        i, j = id_to_idx.get(g1), id_to_idx.get(g2)
        if i is None or j is None or i == j:
            continue
        rows.append(i); cols.append(j)
        rows.append(j); cols.append(i)
    if not rows:
        return np.arange(n)
    data = np.ones(len(rows), dtype=np.int8)
    g = csr_matrix((data, (rows, cols)), shape=(n, n))
    _, labels = connected_components(g, directed=False)
    return labels


# %%
def fit_species(species, sub):
    """Returns dict of results for one species."""
    # Filter to qualifying categories only
    cat_counts_sp = sub["iso_category"].value_counts()
    keep_cats = cat_counts_sp[cat_counts_sp >= MIN_PER_CATEGORY].index.tolist()
    sub = sub[sub["iso_category"].isin(keep_cats)].copy()
    if len(sub) < MIN_TOTAL_GENOMES:
        return None

    # Subsample if too large
    if len(sub) > MAX_GENOMES_PER_SPECIES:
        # Stratified: keep min(MAX/n_cats, available) per category
        per_cat = MAX_GENOMES_PER_SPECIES // len(keep_cats)
        parts = []
        for c in keep_cats:
            s = sub[sub["iso_category"] == c]
            if len(s) > per_cat:
                s = s.sample(per_cat, random_state=42)
            parts.append(s)
        sub = pd.concat(parts, ignore_index=True)

    genome_ids = sub["genome_id"].tolist()
    if len(genome_ids) < MIN_TOTAL_GENOMES:
        return None

    # Pull ANI pairs for these genomes at >= threshold
    # genome_ani is within-species by construction; IN-clause on both ids restricts
    # to the chosen subset. Column is `ANI` (uppercase) and table lacks species clade column.
    gid_list = "','".join(genome_ids)
    try:
        ani = spark.sql(f"""
            SELECT genome1_id, genome2_id
            FROM kbase_ke_pangenome.genome_ani
            WHERE ANI >= {ANI_THRESHOLD}
              AND genome1_id IN ('{gid_list}')
              AND genome2_id IN ('{gid_list}')
        """).toPandas()
    except Exception as e:
        return {"species": species, "error": f"ani_query_failed: {type(e).__name__}: {str(e)[:160]}"}

    ani_pairs = list(zip(ani["genome1_id"].tolist(), ani["genome2_id"].tolist())) if len(ani) else []
    sub["ani_cluster"] = cluster_by_ani(genome_ids, ani_pairs)
    n_clusters = sub["ani_cluster"].nunique()

    # Require multi-cluster, multi-category structure
    if n_clusters < 2:
        return {"species": species, "n_genomes": len(sub), "n_clusters": n_clusters,
                "n_categories": len(keep_cats),
                "categories": ",".join(keep_cats),
                "skipped": "single_ani_cluster"}

    # Fit nested OLS models on GC content (manual via numpy/scipy)
    try:
        y = sub["gc_pct"].to_numpy(dtype=float)
        X_ani = design_categorical(sub["ani_cluster"])
        X_iso = design_categorical(sub["iso_category"])
        X_null = design(X_ani)
        X_alt  = design(X_ani, X_iso)
        f_stat, p_value, rss_null, rss_alt = partial_F(X_null, X_alt, y)

        tss = float(np.sum((y - y.mean()) ** 2))
        r2_null = 1 - rss_null / tss if tss > 0 else float("nan")
        r2_alt  = 1 - rss_alt  / tss if tss > 0 else float("nan")
        partial_r2 = (rss_null - rss_alt) / rss_null if rss_null > 0 else float("nan")

        cat_means = sub.groupby("iso_category")["gc_pct"].mean()
        eff_range = float(cat_means.max() - cat_means.min())

        return {
            "species": species,
            "n_genomes": len(sub),
            "n_clusters": int(n_clusters),
            "n_categories": len(keep_cats),
            "categories": ",".join(keep_cats),
            "category_n": ",".join(f"{c}:{int(cat_counts_sp[c])}" for c in keep_cats),
            "mean_gc": float(sub["gc_pct"].mean()),
            "f_iso_given_ani": f_stat,
            "p_iso_given_ani": p_value,
            "partial_r2_iso": partial_r2,
            "effect_range_pct": eff_range,
            "rss_null": rss_null,
            "rss_alt": rss_alt,
            "r2_null": r2_null,
            "r2_alt": r2_alt,
        }
    except Exception as e:
        return {"species": species, "error": f"model_failed: {e}"[:200]}


# %%
results = []
species_to_run = cand_df["species"].tolist()
print(f"\nRunning OLS pipeline on {len(species_to_run)} species...")
for i, sp in enumerate(species_to_run):
    sub = df[df["gtdb_species_clade_id"] == sp]
    out = fit_species(sp, sub)
    if out is None:
        continue
    results.append(out)
    if (i + 1) % 25 == 0:
        print(f"  {i+1}/{len(species_to_run)} processed")

# %%
res = pd.DataFrame(results)
print(f"\nResults rows: {len(res)}")
# Save raw results
res.to_csv(os.path.join(DATA_DIR, "03_within_species_results.csv"), index=False)

# %%
# Multiple-testing correction on species that have a valid p-value
has_p = res["p_iso_given_ani"].notna() if "p_iso_given_ani" in res.columns else pd.Series([False]*len(res))
res_p = res[has_p].copy()
if len(res_p) > 0:
    res_p["q_value_bh"] = benjamini_hochberg(res_p["p_iso_given_ani"].values)
    res = res.merge(res_p[["species", "q_value_bh"]], on="species", how="left")
    sig = res_p[res_p["q_value_bh"] < 0.05].sort_values("partial_r2_iso", ascending=False)
    print(f"\nSpecies with FDR < 0.05: {len(sig)} / {len(res_p)}")
    sig.to_csv(os.path.join(DATA_DIR, "03_significant_species.csv"), index=False)
    res.to_csv(os.path.join(DATA_DIR, "03_within_species_results.csv"), index=False)

    # -----------------------------------------------------------------------------
    # Volcano plot
    # -----------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 6))
    x = res_p["partial_r2_iso"].values * 100
    y = -np.log10(res_p["p_iso_given_ani"].clip(lower=1e-300).values)
    is_sig = res_p["q_value_bh"].values < 0.05
    ax.scatter(x[~is_sig], y[~is_sig], s=10, color="grey", alpha=0.4, label="not sig.")
    ax.scatter(x[is_sig],  y[is_sig],  s=18, color="#c44e52", alpha=0.8, label="FDR < 0.05")
    ax.set_xlabel("Partial R² of iso_category | ANI cluster (%)")
    ax.set_ylabel("-log10(p) for iso_category effect")
    ax.set_title(
        f"Within-species: does environment predict GC after ANI control?\n"
        f"({len(res_p):,} species tested, {is_sig.sum()} significant at FDR < 0.05)"
    )
    ax.legend()
    # annotate top hits
    top = res_p.nlargest(10, "partial_r2_iso")
    for _, row in top.iterrows():
        nm = row["species"].split("--")[0].replace("s__", "")
        ax.annotate(nm, xy=(row["partial_r2_iso"]*100,
                            -np.log10(max(row["p_iso_given_ani"], 1e-300))),
                    fontsize=7, alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "03_volcano.png"), dpi=150)
    plt.close()

    # -----------------------------------------------------------------------------
    # Top species panels — boxplots of GC by iso_category
    # -----------------------------------------------------------------------------
    top_species = sig.head(8)["species"].tolist() if len(sig) > 0 else \
                  res_p.nlargest(8, "partial_r2_iso")["species"].tolist()
    if top_species:
        ncol = 4
        nrow = (len(top_species) + ncol - 1) // ncol
        fig, axes = plt.subplots(nrow, ncol, figsize=(15, 3.5*nrow), squeeze=False)
        for k, sp in enumerate(top_species):
            ax = axes[k // ncol][k % ncol]
            sub = df[df["gtdb_species_clade_id"] == sp]
            cats = sub["iso_category"].value_counts()
            cats = cats[cats >= MIN_PER_CATEGORY]
            data = [sub.loc[sub["iso_category"] == c, "gc_pct"].values for c in cats.index]
            bp = ax.boxplot(data, tick_labels=cats.index, showfliers=False, patch_artist=True)
            for p in bp["boxes"]:
                p.set(facecolor="#4c72b0", alpha=0.6)
            nm = sp.split("--")[0].replace("s__", "")
            stats = res[res["species"] == sp].iloc[0]
            ax.set_title(f"{nm}\nR²={stats['partial_r2_iso']:.3f}, q={stats.get('q_value_bh', float('nan')):.2e}", fontsize=9)
            ax.tick_params(axis="x", rotation=30, labelsize=8)
            ax.set_ylabel("GC (%)", fontsize=8)
        for k in range(len(top_species), nrow*ncol):
            axes[k // ncol][k % ncol].axis("off")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "03_top_species_panels.png"), dpi=150)
        plt.close()

# %%
print("\nNotebook 03 complete.")
