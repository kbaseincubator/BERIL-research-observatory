# %%
"""
Notebook 06: Addressing reviewer suggestions (REVIEW_1)

Three orthogonal robustness tests for the 40 species declared significant
by notebook 03 (within-species GC × iso_category | ANI cluster, FDR < 0.05):

(A) **Phylogenetic regression** (review suggestion #4) — replace the connected-
    components ANI cluster fixed effect with continuous principal coordinates
    derived from per-species pairwise branch distances in
    `kbase_ke_pangenome.phylogenetic_tree_distance_pairs`. If the iso_category
    effect survives this stricter control, the original finding does not depend
    on the clone-cluster definition.

(B) **Geographic-bias sensitivity** (review suggestion #2) — add parsed lat/lon
    (where available) as continuous covariates to the alt model. If iso_category
    still explains residual GC, the signal is not just geography.

(C) **AlphaEarth PC interpretation** (review suggestion #5) — for the top
    AlphaEarth-significant species, take the AE dimensions with the largest
    loadings on the most-correlated PC, and ask what categorical environment
    those dimensions discriminate. This gives a semantic anchor to the
    otherwise-opaque embedding axis.

Outputs:
  - data/06_phylo_regression_results.csv
  - data/06_geographic_sensitivity_results.csv
  - data/06_alphaearth_pc_interpretation.csv
  - figures/06_phylo_vs_ani_R2.png
  - figures/06_iso_effect_vs_lat_lon_control.png
  - figures/06_ae_pc_loadings.png
"""

# %%
import os
import re
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy import stats as scistats
from sklearn.decomposition import PCA
from berdl_notebook_utils.setup_spark_session import get_spark_session

# %%
warnings.filterwarnings("ignore")

# %%
PROJECT_DIR = "/home/justaddcoffee/BERIL-research-observatory/projects/gc_ecotype_ecology"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
FIG_DIR = os.path.join(PROJECT_DIR, "figures")

# %%
ANI_THRESHOLD = 99.0
N_PHYLO_PCS = 10           # # of phylogenetic PCoA axes to use as continuous control
MIN_TOTAL = 50
MIN_PER_CAT = 10
MAX_GENOMES = 1000          # phylo-regression is per-species O(N^2), cap at 1000

# %%
# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def design_categorical(s):
    cats = pd.Categorical(s)
    codes = cats.codes
    n, k = len(codes), len(cats.categories)
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
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    rss = float(np.sum(resid ** 2))
    rank = int(np.linalg.matrix_rank(X))
    return rss, len(y) - rank, rank

# %%
def partial_F(X_null, X_alt, y):
    rss_null, df_null, rank_null = ols_rss(X_null, y)
    rss_alt,  df_alt,  rank_alt  = ols_rss(X_alt,  y)
    df_diff = rank_alt - rank_null
    if df_diff <= 0 or df_alt <= 0 or rss_alt <= 0:
        return float("nan"), float("nan"), float("nan")
    f = ((rss_null - rss_alt) / df_diff) / (rss_alt / df_alt)
    p = float(scistats.f.sf(f, df_diff, df_alt))
    partial_r2 = (rss_null - rss_alt) / rss_null if rss_null > 0 else float("nan")
    return float(f), p, partial_r2

# %%
def cluster_by_ani(genome_ids, ani_pairs):
    id_to_idx = {g: i for i, g in enumerate(genome_ids)}
    n = len(genome_ids)
    if not ani_pairs:
        return np.arange(n)
    rows, cols = [], []
    for g1, g2 in ani_pairs:
        i, j = id_to_idx.get(g1), id_to_idx.get(g2)
        if i is None or j is None or i == j:
            continue
        rows.append(i); cols.append(j); rows.append(j); cols.append(i)
    if not rows:
        return np.arange(n)
    g = csr_matrix((np.ones(len(rows), dtype=np.int8), (rows, cols)), shape=(n, n))
    _, labels = connected_components(g, directed=False)
    return labels

# %%
def phylo_pcoa(genome_ids, pairs_df, n_components=N_PHYLO_PCS):
    """Classical MDS / PCoA on pairwise branch distances. Returns array (n, n_components)."""
    id_to_idx = {g: i for i, g in enumerate(genome_ids)}
    n = len(genome_ids)
    D = np.zeros((n, n))
    for g1, g2, d in zip(pairs_df["genome1_id"].to_numpy(),
                         pairs_df["genome2_id"].to_numpy(),
                         pairs_df["branch_distance"].to_numpy()):
        i, j = id_to_idx.get(g1), id_to_idx.get(g2)
        if i is None or j is None or i == j:
            continue
        D[i, j] = d
        D[j, i] = d
    # Classical scaling: B = -0.5 * J * D^2 * J, where J = I - 1/n
    D2 = D ** 2
    H = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * H @ D2 @ H
    # Symmetric eigendecomposition
    try:
        w, V = np.linalg.eigh(B)
    except np.linalg.LinAlgError:
        return None
    # Sort descending
    idx = np.argsort(-w)
    w, V = w[idx], V[:, idx]
    k = min(n_components, n - 1)
    # Keep only positive eigenvalues
    keep = w[:k] > 1e-9
    if keep.sum() == 0:
        return None
    coords = V[:, :k][:, keep] * np.sqrt(w[:k][keep])
    return coords  # (n, k_effective)

# %%
LAT_LON_RE = re.compile(
    r"^\s*([-+]?\d+(?:\.\d+)?)\s*([NS])?\s*[,\s]\s*([-+]?\d+(?:\.\d+)?)\s*([EW])?\s*$",
    re.IGNORECASE
)

# %%
def parse_lat_lon(s):
    if not isinstance(s, str):
        return None, None
    m = LAT_LON_RE.match(s.strip())
    if not m:
        # try "39.123 N 76.7 W" form (whitespace separators with cardinals)
        toks = re.findall(r"([-+]?\d+(?:\.\d+)?)\s*([NSEW])?", s.upper())
        if len(toks) >= 2:
            try:
                lat = float(toks[0][0]) * (-1 if toks[0][1] == "S" else 1)
                lon = float(toks[1][0]) * (-1 if toks[1][1] == "W" else 1)
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            except Exception:
                pass
        return None, None
    lat = float(m.group(1)) * (-1 if (m.group(2) or "").upper() == "S" else 1)
    lon = float(m.group(3)) * (-1 if (m.group(4) or "").upper() == "W" else 1)
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None, None


# %%
# -----------------------------------------------------------------------------
# Load
# -----------------------------------------------------------------------------
df = pd.read_parquet(os.path.join(DATA_DIR, "genome_gc_env_categorized.parquet"))
sig = pd.read_csv(os.path.join(DATA_DIR, "03_significant_species.csv"))
ae = pd.read_csv(os.path.join(DATA_DIR, "04_alphaearth_results.csv"))
spark = get_spark_session()

# %%
# Parse lat_lon
lats, lons = [], []
for v in df["lat_lon"].to_list():
    la, lo = parse_lat_lon(v)
    lats.append(la); lons.append(lo)
df["lat"] = lats
df["lon"] = lons
n_geo = int(df["lat"].notna().sum())
print(f"lat/lon parse: {n_geo:,} / {len(df):,} genomes ({100*n_geo/len(df):.1f}%) yielded valid coordinates")

# %%
# -----------------------------------------------------------------------------
# (A) Phylogenetic regression — per-species PCoA from branch_distance
# -----------------------------------------------------------------------------
print(f"\n=== (A) Phylogenetic regression vs (B) Geographic sensitivity ===")
sig_species = sig["species"].tolist()

# %%
combined_results = []
for i, sp in enumerate(sig_species):
    sub = df[(df["gtdb_species_clade_id"] == sp) & df["iso_category"].notna()].copy()
    sub = sub[sub["iso_category"] != "other"]
    cat_counts = sub["iso_category"].value_counts()
    keep = cat_counts[cat_counts >= MIN_PER_CAT].index.tolist()
    sub = sub[sub["iso_category"].isin(keep)].copy()
    if len(sub) < MIN_TOTAL or len(keep) < 2:
        continue

    if len(sub) > MAX_GENOMES:
        # Stratified by category
        per_cat = MAX_GENOMES // len(keep)
        parts = []
        for c in keep:
            s = sub[sub["iso_category"] == c]
            if len(s) > per_cat:
                s = s.sample(per_cat, random_state=42)
            parts.append(s)
        sub = pd.concat(parts, ignore_index=True)

    genome_ids = sub["genome_id"].tolist()
    gid_list = "','".join(genome_ids)

    # --- ANI cluster recompute (so RSS comparable to phylo-PCoA model) ---
    try:
        ani = spark.sql(f"""
            SELECT genome1_id, genome2_id
            FROM kbase_ke_pangenome.genome_ani
            WHERE ANI >= {ANI_THRESHOLD}
              AND genome1_id IN ('{gid_list}')
              AND genome2_id IN ('{gid_list}')
        """).toPandas()
    except Exception:
        continue

    pairs = list(zip(ani["genome1_id"].tolist(), ani["genome2_id"].tolist()))
    sub["ani_cluster"] = cluster_by_ani(genome_ids, pairs)
    if sub["ani_cluster"].nunique() < 2:
        continue

    # --- Phylo branch distances ---
    # phylogenetic_tree_distance_pairs uses bare GCF_/GCA_ accessions (no RS_/GB_ prefix).
    # Build a mapping so we can query and remap back.
    def strip_prefix(g):
        if g.startswith("RS_"):
            return g[3:]
        if g.startswith("GB_"):
            return g[3:]
        return g
    stripped_to_full = {strip_prefix(g): g for g in genome_ids}
    stripped_ids = list(stripped_to_full.keys())
    strip_list = "','".join(stripped_ids)
    try:
        pairs_df = spark.sql(f"""
            SELECT genome1_id, genome2_id, branch_distance
            FROM kbase_ke_pangenome.phylogenetic_tree_distance_pairs
            WHERE genome1_id IN ('{strip_list}')
              AND genome2_id IN ('{strip_list}')
        """).toPandas()
        pairs_df = pd.DataFrame({c: pairs_df[c].to_numpy() for c in pairs_df.columns})
        # Remap to full IDs for PCoA matching
        if len(pairs_df) > 0:
            pairs_df["genome1_id"] = pairs_df["genome1_id"].map(stripped_to_full)
            pairs_df["genome2_id"] = pairs_df["genome2_id"].map(stripped_to_full)
            pairs_df = pairs_df.dropna(subset=["genome1_id", "genome2_id"])
    except Exception:
        continue

    if len(pairs_df) < 10:
        # phylo tree may not cover this species
        phylo_pcs = None
    else:
        phylo_pcs = phylo_pcoa(genome_ids, pairs_df, n_components=N_PHYLO_PCS)

    y = sub["gc_pct"].to_numpy(dtype=float)
    X_iso = design_categorical(sub["iso_category"])
    X_ani_cat = design_categorical(sub["ani_cluster"])

    # --- ANI-controlled (the original test) ---
    X_null_ani = design(X_ani_cat)
    X_alt_ani  = design(X_ani_cat, X_iso)
    f_ani, p_ani, r2_ani = partial_F(X_null_ani, X_alt_ani, y)

    # --- Phylo-PCoA controlled ---
    if phylo_pcs is not None and phylo_pcs.shape[1] >= 2:
        X_null_phylo = design(phylo_pcs)
        X_alt_phylo  = design(phylo_pcs, X_iso)
        f_phylo, p_phylo, r2_phylo = partial_F(X_null_phylo, X_alt_phylo, y)
        n_pcs_used = int(phylo_pcs.shape[1])
    else:
        f_phylo, p_phylo, r2_phylo = float("nan"), float("nan"), float("nan")
        n_pcs_used = 0

    # --- Geographic sensitivity: ANI + lat/lon controlled ---
    # Don't require 50% geo coverage — just enough to fit. lat/lon is sparse (~28% global).
    has_geo = sub["lat"].notna() & sub["lon"].notna()
    if has_geo.sum() >= 30:
        sub_g = sub[has_geo].copy()
        # require still >=2 categories with >= MIN_PER_CAT among geo-bearing
        cc = sub_g["iso_category"].value_counts()
        keep_g = cc[cc >= MIN_PER_CAT].index.tolist()
        if len(keep_g) >= 2:
            sub_g = sub_g[sub_g["iso_category"].isin(keep_g)].copy()
            y_g = sub_g["gc_pct"].to_numpy(dtype=float)
            X_iso_g = design_categorical(sub_g["iso_category"])
            X_ani_g = design_categorical(sub_g["ani_cluster"])
            X_geo = sub_g[["lat", "lon"]].to_numpy(dtype=float)
            X_null_g = design(X_ani_g, X_geo)
            X_alt_g  = design(X_ani_g, X_geo, X_iso_g)
            f_geo, p_geo, r2_geo = partial_F(X_null_g, X_alt_g, y_g)
            n_geo_sub = int(len(sub_g))
        else:
            f_geo, p_geo, r2_geo, n_geo_sub = (float("nan"),)*4
            n_geo_sub = 0
    else:
        f_geo, p_geo, r2_geo, n_geo_sub = (float("nan"),)*4
        n_geo_sub = 0

    combined_results.append({
        "species": sp,
        "n_genomes": len(sub),
        "n_ani_clusters": int(sub["ani_cluster"].nunique()),
        "f_ani": f_ani,    "p_ani": p_ani,    "partial_r2_ani": r2_ani,
        "n_phylo_pcs": n_pcs_used,
        "f_phylo": f_phylo, "p_phylo": p_phylo, "partial_r2_phylo": r2_phylo,
        "n_genomes_with_geo": n_geo_sub,
        "f_geo": f_geo,    "p_geo": p_geo,    "partial_r2_geo": r2_geo,
    })

    if (i + 1) % 5 == 0:
        print(f"  {i+1}/{len(sig_species)} processed")

# %%
cr = pd.DataFrame(combined_results)
print(f"\nCombined robustness results: {len(cr)} species")

# %%
# Survival rates
n_orig_sig = (cr["p_ani"] < 0.05).sum()
n_phylo_sig = (cr["p_phylo"].notna() & (cr["p_phylo"] < 0.05)).sum()
n_geo_sig = (cr["p_geo"].notna() & (cr["p_geo"] < 0.05)).sum()
phylo_testable = cr["p_phylo"].notna().sum()
geo_testable = cr["p_geo"].notna().sum()

# %%
print(f"\nWith ANI control (reproducing notebook 03):  {n_orig_sig}/{len(cr)} significant @ p<0.05")
print(f"With phylogenetic PCoA control:              {n_phylo_sig}/{phylo_testable} (of testable) @ p<0.05")
print(f"With ANI + lat/lon control:                  {n_geo_sig}/{geo_testable} (of testable) @ p<0.05")

# %%
cr.to_csv(os.path.join(DATA_DIR, "06_phylo_geographic_combined.csv"), index=False)

# %%
# Figure: scatter of partial R^2 ANI vs phylo
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax = axes[0]
m = cr["partial_r2_phylo"].notna()
ax.scatter(cr.loc[m, "partial_r2_ani"]*100, cr.loc[m, "partial_r2_phylo"]*100,
           s=30, alpha=0.7, color="#4c72b0")
mx = max(cr.loc[m, "partial_r2_ani"].max(), cr.loc[m, "partial_r2_phylo"].max())*100
ax.plot([0, mx], [0, mx], "k--", alpha=0.3, label="y=x")
ax.set_xlabel("Partial R² with ANI cluster control (%)")
ax.set_ylabel("Partial R² with phylogenetic PCoA control (%)")
ax.set_title(f"Effect size under two phylogenetic controls\n({int(m.sum())} species testable)")
ax.legend()

# %%
ax = axes[1]
mg = cr["partial_r2_geo"].notna()
ax.scatter(cr.loc[mg, "partial_r2_ani"]*100, cr.loc[mg, "partial_r2_geo"]*100,
           s=30, alpha=0.7, color="#c44e52")
mx = max(cr.loc[mg, "partial_r2_ani"].max(), cr.loc[mg, "partial_r2_geo"].max())*100
ax.plot([0, mx], [0, mx], "k--", alpha=0.3, label="y=x")
ax.set_xlabel("Partial R² with ANI control (%)")
ax.set_ylabel("Partial R² with ANI + lat/lon control (%)")
ax.set_title(f"Effect size after adding geographic control\n({int(mg.sum())} species testable)")
ax.legend()

# %%
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "06_robustness_R2_comparison.png"), dpi=150)
plt.close()

# %%
# -----------------------------------------------------------------------------
# (C) AlphaEarth PC interpretation
# -----------------------------------------------------------------------------
# For the top AE-significant species, fit AE PCs and report:
#   1. Which AE dimensions load most heavily on the PC most correlated with GC.
#   2. Whether that PC discriminates iso_category (i.e. carries categorical signal).
# This gives a semantic anchor.
print("\n=== (C) AlphaEarth PC interpretation ===")
ae_sig = ae[ae["q_value_bh"] < 0.05].sort_values("best_p").head(20)
print(f"Interpreting top {len(ae_sig)} AE-significant species")

# %%
ae_cols = [f"A{i:02d}" for i in range(64)]
ae_select = ", ".join(ae_cols)
print("  Pulling AlphaEarth embeddings...")
ae_q = spark.sql(f"SELECT genome_id, {ae_select} FROM kbase_ke_pangenome.alphaearth_embeddings_all_years").toPandas()
ae_q = pd.DataFrame({c: ae_q[c].to_numpy() for c in ae_q.columns})
ae_df_per = ae_q.groupby("genome_id")[ae_cols].mean().reset_index()

# %%
interp_results = []
for sp in ae_sig["species"].tolist():
    sub = df.merge(ae_df_per, on="genome_id").query(f"gtdb_species_clade_id == @sp").copy()
    if len(sub) < 30:
        continue
    if len(sub) > 2000:
        sub = sub.sample(2000, random_state=42)
    genome_ids = sub["genome_id"].tolist()
    gid_list = "','".join(genome_ids)
    try:
        ani = spark.sql(f"""
            SELECT genome1_id, genome2_id FROM kbase_ke_pangenome.genome_ani
            WHERE ANI >= {ANI_THRESHOLD}
              AND genome1_id IN ('{gid_list}')
              AND genome2_id IN ('{gid_list}')
        """).toPandas()
    except Exception:
        continue
    pairs = list(zip(ani["genome1_id"].tolist(), ani["genome2_id"].tolist()))
    sub["ani_cluster"] = cluster_by_ani(genome_ids, pairs)
    if sub["ani_cluster"].nunique() < 2:
        continue

    sub["gc_resid"] = sub["gc_pct"] - sub.groupby("ani_cluster")["gc_pct"].transform("mean")
    ae_arr = sub[ae_cols].to_numpy().copy()
    cluster_arr = sub["ani_cluster"].to_numpy()
    for cluster in np.unique(cluster_arr):
        mask = cluster_arr == cluster
        if mask.sum() <= 1:
            continue
        ae_arr[mask] = ae_arr[mask] - ae_arr[mask].mean(axis=0)
    try:
        pca = PCA(n_components=min(5, ae_arr.shape[0]-1, 64))
        pcs = pca.fit_transform(ae_arr)
    except Exception:
        continue

    # Find PC most correlated with residual GC
    gc_resid = sub["gc_resid"].to_numpy()
    best_pc = -1; best_r = 0.0
    for k in range(pcs.shape[1]):
        if pcs[:, k].std() < 1e-9:
            continue
        r, p = scistats.pearsonr(gc_resid, pcs[:, k])
        if abs(r) > abs(best_r):
            best_pc, best_r = k, r

    if best_pc < 0:
        continue

    # Loadings of best PC on AE dimensions
    loadings = pca.components_[best_pc]
    top_dims_idx = np.argsort(-np.abs(loadings))[:5]
    top_dims = [(ae_cols[i], float(loadings[i])) for i in top_dims_idx]

    # Does the best PC discriminate iso_category?
    iso_pc_F = np.nan; iso_pc_p = np.nan
    sub_iso = sub[sub["iso_category"].notna() & (sub["iso_category"] != "other")]
    if len(sub_iso) >= 30:
        ic = sub_iso["iso_category"].value_counts()
        keep_ic = ic[ic >= 5].index.tolist()
        if len(keep_ic) >= 2:
            sub_iso = sub_iso[sub_iso["iso_category"].isin(keep_ic)]
            sub_iso_idx = sub_iso.index
            # Get PC values aligned
            pc_vals = pcs[sub.index.get_indexer(sub_iso_idx), best_pc]
            groups = [pc_vals[(sub_iso["iso_category"] == c).to_numpy()] for c in keep_ic]
            try:
                Fv, pv = scistats.f_oneway(*groups)
                iso_pc_F, iso_pc_p = float(Fv), float(pv)
            except Exception:
                pass

    interp_results.append({
        "species": sp,
        "species_short": sp.split("--")[0].replace("s__", ""),
        "best_pc": int(best_pc),
        "best_r": float(best_r),
        "expl_var_ratio": float(pca.explained_variance_ratio_[best_pc]),
        "top_dim_1": top_dims[0][0], "load_1": top_dims[0][1],
        "top_dim_2": top_dims[1][0], "load_2": top_dims[1][1],
        "top_dim_3": top_dims[2][0], "load_3": top_dims[2][1],
        "top_dim_4": top_dims[3][0], "load_4": top_dims[3][1],
        "top_dim_5": top_dims[4][0], "load_5": top_dims[4][1],
        "iso_anova_F_on_pc": iso_pc_F,
        "iso_anova_p_on_pc": iso_pc_p,
    })

# %%
ir = pd.DataFrame(interp_results)
ir.to_csv(os.path.join(DATA_DIR, "06_alphaearth_pc_interpretation.csv"), index=False)
print(f"\nAE PC interpretation: {len(ir)} species")
if len(ir) > 0:
    n_pc_iso = (ir["iso_anova_p_on_pc"] < 0.05).sum()
    print(f"  Best AE PC discriminates iso_category (ANOVA p<0.05): {n_pc_iso}/{len(ir)}")
    # Which AE dims appear most often as top loadings?
    all_top_dims = []
    for k in range(1, 6):
        all_top_dims.extend(ir[f"top_dim_{k}"].tolist())
    top_counts = pd.Series(all_top_dims).value_counts().head(15)
    print(f"\n  Most frequently top-loading AE dimensions across {len(ir)} species:")
    print(top_counts.to_string())

# %%
# Figure: heatmap of top loadings across species
if len(ir) > 0:
    # Build matrix: rows = species, cols = AE dims that appear at least twice
    appearing = pd.Series(all_top_dims).value_counts()
    common_dims = appearing[appearing >= 2].index.tolist()
    if common_dims:
        mat = np.zeros((len(ir), len(common_dims)))
        for i, row in ir.iterrows():
            for k in range(1, 6):
                d = row[f"top_dim_{k}"]
                if d in common_dims:
                    j = common_dims.index(d)
                    mat[i, j] = row[f"load_{k}"]
        fig, ax = plt.subplots(figsize=(12, max(6, 0.32*len(ir))))
        im = ax.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=-0.5, vmax=0.5)
        ax.set_xticks(range(len(common_dims)))
        ax.set_xticklabels(common_dims, rotation=45, ha="right")
        ax.set_yticks(range(len(ir)))
        ax.set_yticklabels(ir["species_short"].str.replace("_", " ").tolist(), fontsize=8)
        ax.set_title("Top AlphaEarth dimensions loading on the GC-correlated PC\n"
                     "(within-cluster residuals; rows = species, cols = AE dims appearing in >=2 species)")
        plt.colorbar(im, ax=ax, label="PC loading")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, "06_ae_pc_loadings.png"), dpi=150)
        plt.close()

# %%
print("\nNotebook 06 complete.")
