#!/usr/bin/env python3
"""
NB07 Benchmarking: Module-Based Predictions vs Baselines

Evaluates module-based function predictions against three baselines:
1. Cofitness voting: top-N cofit partners → majority vote
2. Ortholog transfer: BBH annotation transfer
3. Domain-only: TIGRFam/PFam → KEGG mapping

Evaluation (two levels):
A. Strict: hold out 20% of KEGG-annotated genes, predict exact KO, measure
   precision/coverage/F1 at KEGG KO (kgroup) level.
B. Neighborhood: check if the held-out gene's KO appears anywhere in the
   method's predicted functional neighborhood (all KOs in the module, top-N
   cofit partners, ortholog's KOs, or domain-associated KOs).

Validation:
- Within-module cofitness density (per-module enrichment test)
- Genomic adjacency (operon proximity enrichment)

Run locally — no Spark needed (uses extracted data files).

Usage:
    python src/run_benchmark.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from collections import Counter
from scipy import stats
import time
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODULE_DIR = DATA_DIR / "modules"
ANNOT_DIR = DATA_DIR / "annotations"
ORTHO_DIR = DATA_DIR / "orthologs"
PRED_DIR = DATA_DIR / "predictions"
MAT_DIR = DATA_DIR / "matrices"
FIG_DIR = BASE_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)
PRED_DIR.mkdir(exist_ok=True)

pilots = pd.read_csv(DATA_DIR / "pilot_organisms.csv")
org_ids = pilots["orgId"].tolist()

print(f"Benchmarking {len(org_ids)} organisms")
print("=" * 70)

# ── Helpers ──────────────────────────────────────────────────────────────────

def compute_corr_matrix(fit_matrix_values):
    """Vectorized Pearson correlation matrix from fitness matrix rows."""
    X = fit_matrix_values.astype(np.float64)
    X_c = X - X.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(X_c, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X_n = X_c / norms
    return X_n @ X_n.T


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Held-Out Evaluation
# ═══════════════════════════════════════════════════════════════════════════

print("\n## Section 1: Held-Out Evaluation (4 methods × 32 organisms)")
print("=" * 70)

# 1a. Build gold standard from KEGG annotations
gold_standard = {}
for org_id in org_ids:
    kegg_file = ANNOT_DIR / f"{org_id}_kegg.csv"
    if not kegg_file.exists():
        continue
    kegg = pd.read_csv(kegg_file)
    kegg["locusId"] = kegg["locusId"].astype(str)
    gene_kegg = kegg.groupby("locusId")["kgroup"].apply(set).to_dict()
    gold_standard[org_id] = gene_kegg

print(f"Gold standard: {len(gold_standard)} organisms, "
      f"{sum(len(v) for v in gold_standard.values())} annotated genes")

# 1b. Hold-out split
np.random.seed(42)
HOLDOUT_FRAC = 0.2
train_genes = {}
test_genes = {}

for org_id, gene_kegg in gold_standard.items():
    all_loci = list(gene_kegg.keys())
    train_loci, test_loci = train_test_split(
        all_loci, test_size=HOLDOUT_FRAC, random_state=42
    )
    train_genes[org_id] = {l: gene_kegg[l] for l in train_loci}
    test_genes[org_id] = {l: gene_kegg[l] for l in test_loci}

print(f"Train/test split: {HOLDOUT_FRAC:.0%} holdout, seed=42")


# ── Prediction Methods ──────────────────────────────────────────────────────

def module_predict(org_id, test_loci, train_kegg, membership, weights):
    """Predict KEGG group for test genes using module enrichment (train only)."""
    # Build module → enriched KEGG terms using TRAINING genes only
    module_kegg = {}
    for mod in membership.columns:
        mod_genes = set(membership.index[membership[mod] == 1])
        mod_train = mod_genes & set(train_kegg.keys())
        if not mod_train:
            continue
        kegg_counts = Counter()
        for g in mod_train:
            for kg in train_kegg[g]:
                kegg_counts[kg] += 1
        if kegg_counts:
            module_kegg[mod] = kegg_counts.most_common(1)[0][0]

    predictions = {}
    for locus in test_loci:
        if locus not in membership.index:
            continue
        gene_mods = membership.columns[membership.loc[locus] == 1]
        if len(gene_mods) == 0:
            continue
        # Pick module with highest |weight| that has a KEGG enrichment
        best_mod = None
        best_weight = 0
        for mod in gene_mods:
            w = abs(weights.loc[locus, mod])
            if w > best_weight and mod in module_kegg:
                best_weight = w
                best_mod = mod
        if best_mod:
            predictions[locus] = module_kegg[best_mod]
    return predictions


def cofit_predict(org_id, test_loci, train_kegg, corr_matrix, gene_index, top_n=6):
    """Predict KEGG group using top-N cofitness partners (vectorized)."""
    train_loci = [l for l in train_kegg if l in gene_index]
    if not train_loci:
        return {}

    train_idx = np.array([gene_index[l] for l in train_loci])

    predictions = {}
    for locus in test_loci:
        if locus not in gene_index:
            continue
        test_idx = gene_index[locus]
        # Get correlations with all training genes
        corrs = np.abs(corr_matrix[test_idx, train_idx])
        # Top-N by absolute correlation
        top_pos = np.argsort(corrs)[-top_n:]
        kegg_votes = Counter()
        for pos in top_pos:
            partner = train_loci[pos]
            for kg in train_kegg[partner]:
                kegg_votes[kg] += 1
        if kegg_votes:
            predictions[locus] = kegg_votes.most_common(1)[0][0]
    return predictions


def ortholog_predict(org_id, test_loci, all_train_kegg, bbh_pairs):
    """Predict KEGG group by transferring from BBH ortholog."""
    if len(bbh_pairs) == 0:
        return {}
    org_bbh = bbh_pairs[bbh_pairs["orgId1"] == org_id]
    if len(org_bbh) == 0:
        return {}

    # Pre-index for faster lookup
    org_bbh_indexed = org_bbh.set_index("locusId1")

    predictions = {}
    for locus in test_loci:
        if locus not in org_bbh_indexed.index:
            continue
        hits = org_bbh_indexed.loc[[locus]]
        for _, hit in hits.iterrows():
            other_org = hit["orgId2"]
            other_locus = str(hit["locusId2"])
            if other_org in all_train_kegg and other_locus in all_train_kegg[other_org]:
                predictions[locus] = list(all_train_kegg[other_org][other_locus])[0]
                break
    return predictions


def domain_predict(org_id, test_loci, train_kegg, domains_df):
    """Predict KEGG group from domain → KEGG mapping (train genes only)."""
    if domains_df is None or len(domains_df) == 0:
        return {}

    # Build domain → KEGG mapping from training genes
    domain_kegg = {}
    for locus, kegg_groups in train_kegg.items():
        gene_doms = domains_df[domains_df["locusId"] == locus]["domainId"].tolist()
        for dom in gene_doms:
            if dom not in domain_kegg:
                domain_kegg[dom] = Counter()
            for kg in kegg_groups:
                domain_kegg[dom][kg] += 1

    predictions = {}
    for locus in test_loci:
        gene_doms = domains_df[domains_df["locusId"] == locus]["domainId"].tolist()
        kegg_votes = Counter()
        for dom in gene_doms:
            if dom in domain_kegg:
                kegg_votes.update(domain_kegg[dom])
        if kegg_votes:
            predictions[locus] = kegg_votes.most_common(1)[0][0]
    return predictions


def evaluate(preds, true_labels, n_test):
    """Compute precision, coverage, F1 for single-KO predictions."""
    n_correct = 0
    n_predicted = 0
    for locus, pred_kg in preds.items():
        if locus in true_labels:
            n_predicted += 1
            if pred_kg in true_labels[locus]:
                n_correct += 1
    precision = n_correct / n_predicted if n_predicted > 0 else 0.0
    coverage = n_predicted / n_test if n_test > 0 else 0.0
    f1 = (2 * precision * coverage / (precision + coverage)
          if (precision + coverage) > 0 else 0.0)
    return n_predicted, n_correct, precision, coverage, f1


def evaluate_neighborhood(neighborhoods, true_labels, n_test):
    """Compute precision, coverage, F1 for neighborhood (set) predictions.

    A prediction is correct if any of the gene's true KOs appears in the
    method's predicted neighborhood (set of KOs).
    """
    n_correct = 0
    n_predicted = 0
    for locus, ko_set in neighborhoods.items():
        if locus in true_labels and ko_set:
            n_predicted += 1
            if true_labels[locus] & ko_set:  # any overlap
                n_correct += 1
    precision = n_correct / n_predicted if n_predicted > 0 else 0.0
    coverage = n_predicted / n_test if n_test > 0 else 0.0
    f1 = (2 * precision * coverage / (precision + coverage)
          if (precision + coverage) > 0 else 0.0)
    return n_predicted, n_correct, precision, coverage, f1


# ── Neighborhood Prediction Functions ────────────────────────────────────────
# These return locus → set of KOs (the "functional neighborhood") instead of
# a single predicted KO.

def module_neighborhood(org_id, test_loci, train_kegg, membership):
    """Return all KOs present in the test gene's module(s) from training genes."""
    # Build module → set of KOs from training genes
    module_kos = {}
    for mod in membership.columns:
        mod_genes = set(membership.index[membership[mod] == 1])
        mod_train = mod_genes & set(train_kegg.keys())
        kos = set()
        for g in mod_train:
            kos |= train_kegg[g]
        if kos:
            module_kos[mod] = kos

    neighborhoods = {}
    for locus in test_loci:
        if locus not in membership.index:
            continue
        gene_mods = membership.columns[membership.loc[locus] == 1]
        all_kos = set()
        for mod in gene_mods:
            if mod in module_kos:
                all_kos |= module_kos[mod]
        if all_kos:
            neighborhoods[locus] = all_kos
    return neighborhoods


def cofit_neighborhood(org_id, test_loci, train_kegg, corr_matrix, gene_index,
                       top_n=6):
    """Return all KOs from top-N cofitness partners."""
    train_loci = [l for l in train_kegg if l in gene_index]
    if not train_loci:
        return {}
    train_idx = np.array([gene_index[l] for l in train_loci])

    neighborhoods = {}
    for locus in test_loci:
        if locus not in gene_index:
            continue
        test_idx = gene_index[locus]
        corrs = np.abs(corr_matrix[test_idx, train_idx])
        top_pos = np.argsort(corrs)[-top_n:]
        kos = set()
        for pos in top_pos:
            kos |= train_kegg[train_loci[pos]]
        if kos:
            neighborhoods[locus] = kos
    return neighborhoods


def ortholog_neighborhood(org_id, test_loci, all_train_kegg, bbh_pairs):
    """Return all KOs from BBH orthologs."""
    if len(bbh_pairs) == 0:
        return {}
    org_bbh = bbh_pairs[bbh_pairs["orgId1"] == org_id]
    if len(org_bbh) == 0:
        return {}
    org_bbh_indexed = org_bbh.set_index("locusId1")

    neighborhoods = {}
    for locus in test_loci:
        if locus not in org_bbh_indexed.index:
            continue
        hits = org_bbh_indexed.loc[[locus]]
        kos = set()
        for _, hit in hits.iterrows():
            other_org = hit["orgId2"]
            other_locus = str(hit["locusId2"])
            if other_org in all_train_kegg and other_locus in all_train_kegg[other_org]:
                kos |= all_train_kegg[other_org][other_locus]
        if kos:
            neighborhoods[locus] = kos
    return neighborhoods


def domain_neighborhood(org_id, test_loci, train_kegg, domains_df):
    """Return all KOs associated with the test gene's domains."""
    if domains_df is None or len(domains_df) == 0:
        return {}
    domain_kegg = {}
    for locus, kegg_groups in train_kegg.items():
        gene_doms = domains_df[domains_df["locusId"] == locus]["domainId"].tolist()
        for dom in gene_doms:
            if dom not in domain_kegg:
                domain_kegg[dom] = set()
            domain_kegg[dom] |= kegg_groups

    neighborhoods = {}
    for locus in test_loci:
        gene_doms = domains_df[domains_df["locusId"] == locus]["domainId"].tolist()
        kos = set()
        for dom in gene_doms:
            if dom in domain_kegg:
                kos |= domain_kegg[dom]
        if kos:
            neighborhoods[locus] = kos
    return neighborhoods


# ── Run all methods ──────────────────────────────────────────────────────────

bbh_file = ORTHO_DIR / "pilot_bbh_pairs.csv"
bbh_pairs = pd.read_csv(bbh_file) if bbh_file.exists() else pd.DataFrame()
if len(bbh_pairs) > 0:
    bbh_pairs["locusId1"] = bbh_pairs["locusId1"].astype(str)
    bbh_pairs["locusId2"] = bbh_pairs["locusId2"].astype(str)

results = []
t_total = time.time()

for org_id in org_ids:
    if org_id not in test_genes:
        continue

    t0 = time.time()
    test_loci = list(test_genes[org_id].keys())
    true_labels = test_genes[org_id]

    # Load module data (string indices)
    membership = pd.read_csv(MODULE_DIR / f"{org_id}_gene_membership.csv", index_col=0)
    membership.index = membership.index.astype(str)
    weights = pd.read_csv(MODULE_DIR / f"{org_id}_gene_weights.csv", index_col=0)
    weights.index = weights.index.astype(str)

    # Load fitness matrix and compute correlation matrix (vectorized)
    fit_file = MAT_DIR / f"{org_id}_fitness_matrix.csv"
    fit_matrix = pd.read_csv(fit_file, index_col=0)
    fit_matrix.index = fit_matrix.index.astype(str)
    gene_index = {g: i for i, g in enumerate(fit_matrix.index)}
    corr_matrix = compute_corr_matrix(fit_matrix.values)

    # Load annotations
    domain_file = ANNOT_DIR / f"{org_id}_domains.csv"
    domains = None
    if domain_file.exists():
        domains = pd.read_csv(domain_file)
        domains["locusId"] = domains["locusId"].astype(str)

    # Run 4 methods — strict (single KO prediction)
    preds_module = module_predict(org_id, test_loci, train_genes[org_id],
                                  membership, weights)
    preds_cofit = cofit_predict(org_id, test_loci, train_genes[org_id],
                                corr_matrix, gene_index)
    preds_ortho = ortholog_predict(org_id, test_loci, train_genes, bbh_pairs)
    preds_domain = domain_predict(org_id, test_loci, train_genes[org_id], domains)

    methods_strict = {
        "Module-ICA": preds_module,
        "Cofitness": preds_cofit,
        "Ortholog": preds_ortho,
        "Domain": preds_domain,
    }

    # Run 4 methods — neighborhood (set of KOs)
    nbr_module = module_neighborhood(org_id, test_loci, train_genes[org_id],
                                     membership)
    nbr_cofit = cofit_neighborhood(org_id, test_loci, train_genes[org_id],
                                    corr_matrix, gene_index)
    nbr_ortho = ortholog_neighborhood(org_id, test_loci, train_genes, bbh_pairs)
    nbr_domain = domain_neighborhood(org_id, test_loci, train_genes[org_id],
                                      domains)

    methods_nbr = {
        "Module-ICA": nbr_module,
        "Cofitness": nbr_cofit,
        "Ortholog": nbr_ortho,
        "Domain": nbr_domain,
    }

    elapsed = time.time() - t0
    print(f"\n{org_id} ({len(test_loci)} test genes, {elapsed:.1f}s):")

    # Strict evaluation
    for method_name, preds in methods_strict.items():
        n_pred, n_correct, prec, cov, f1 = evaluate(preds, true_labels, len(test_loci))
        results.append({
            "orgId": org_id,
            "method": method_name,
            "eval_level": "strict",
            "n_test": len(test_loci),
            "n_predicted": n_pred,
            "n_correct": n_correct,
            "precision": round(prec, 4),
            "coverage": round(cov, 4),
            "f1": round(f1, 4),
        })

    # Neighborhood evaluation
    for method_name, nbrs in methods_nbr.items():
        n_pred, n_correct, prec, cov, f1 = evaluate_neighborhood(
            nbrs, true_labels, len(test_loci))
        results.append({
            "orgId": org_id,
            "method": method_name,
            "eval_level": "neighborhood",
            "n_test": len(test_loci),
            "n_predicted": n_pred,
            "n_correct": n_correct,
            "precision": round(prec, 4),
            "coverage": round(cov, 4),
            "f1": round(f1, 4),
        })

    # Print summary for this organism
    print(f"  {'Method':12s}  {'Strict Prec':>11s} {'Nbr Prec':>9s} {'Coverage':>8s}")
    for method_name in ["Module-ICA", "Cofitness", "Ortholog", "Domain"]:
        strict = [r for r in results
                  if r["orgId"] == org_id and r["method"] == method_name
                  and r["eval_level"] == "strict"][-1]
        nbr = [r for r in results
               if r["orgId"] == org_id and r["method"] == method_name
               and r["eval_level"] == "neighborhood"][-1]
        print(f"  {method_name:12s}  {strict['precision']:11.3f} {nbr['precision']:9.3f} "
              f"{strict['coverage']:8.3f}")

results_df = pd.DataFrame(results)
results_df.to_csv(PRED_DIR / "benchmark_results.csv", index=False)
print(f"\nTotal time: {time.time() - t_total:.1f}s")
print(f"Saved: {PRED_DIR / 'benchmark_results.csv'}")


# ── Aggregate and plot ───────────────────────────────────────────────────────

methods_order = ["Module-ICA", "Cofitness", "Ortholog", "Domain"]
colors = ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0"]

for level in ["strict", "neighborhood"]:
    level_df = results_df[results_df["eval_level"] == level]
    agg = level_df.groupby("method").agg(
        mean_precision=("precision", "mean"),
        std_precision=("precision", "std"),
        mean_coverage=("coverage", "mean"),
        std_coverage=("coverage", "std"),
        mean_f1=("f1", "mean"),
        std_f1=("f1", "std"),
        total_correct=("n_correct", "sum"),
        total_predicted=("n_predicted", "sum"),
        total_test=("n_test", "sum"),
    ).reset_index()
    agg["overall_precision"] = agg["total_correct"] / agg["total_predicted"]
    agg["overall_coverage"] = agg["total_predicted"] / agg["total_test"]

    print(f"\n{'=' * 70}")
    print(f"Aggregate Results — {level.upper()} (mean ± std across organisms):")
    print(f"{'=' * 70}")
    for _, row in agg.iterrows():
        print(f"  {row['method']:12s}: prec={row['mean_precision']:.3f}±{row['std_precision']:.3f} "
              f"cov={row['mean_coverage']:.3f}±{row['std_coverage']:.3f} "
              f"F1={row['mean_f1']:.3f}±{row['std_f1']:.3f}")

    # Bar chart
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f"KEGG Prediction Benchmark — {level.title()} Match", fontsize=14,
                 fontweight="bold")
    metrics = [
        ("mean_precision", "std_precision", "Precision"),
        ("mean_coverage", "std_coverage", "Coverage"),
        ("mean_f1", "std_f1", "F1 Score"),
    ]

    for ax, (mean_col, std_col, title) in zip(axes, metrics):
        vals, errs = [], []
        for method in methods_order:
            row = agg[agg["method"] == method]
            vals.append(row[mean_col].values[0] if len(row) > 0 else 0)
            errs.append(row[std_col].values[0] if len(row) > 0 else 0)
        ax.bar(range(len(methods_order)), vals, color=colors, yerr=errs, capsize=5)
        ax.set_xticks(range(len(methods_order)))
        ax.set_xticklabels(methods_order, rotation=30, ha="right")
        ax.set_ylabel(title)
        ax.set_title(title)
        ax.set_ylim(0, 1)

    plt.tight_layout()
    fname = f"benchmark_{level}.png"
    plt.savefig(FIG_DIR / fname, dpi=150, bbox_inches="tight")
    print(f"Saved: {FIG_DIR / fname}")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Within-Module Cofitness Validation
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n## Section 2: Within-Module Cofitness Validation")
print("=" * 70)

cofit_results = []

for org_id in org_ids:
    fit_file = MAT_DIR / f"{org_id}_fitness_matrix.csv"
    member_file = MODULE_DIR / f"{org_id}_gene_membership.csv"
    if not fit_file.exists() or not member_file.exists():
        continue

    fit_matrix = pd.read_csv(fit_file, index_col=0)
    fit_matrix.index = fit_matrix.index.astype(str)
    membership = pd.read_csv(member_file, index_col=0)
    membership.index = membership.index.astype(str)

    # Compute full correlation matrix (vectorized)
    corr = compute_corr_matrix(fit_matrix.values)
    gene_list = list(fit_matrix.index)
    gene_to_idx = {g: i for i, g in enumerate(gene_list)}
    n_genes = len(gene_list)

    # Sample background: mean correlation of random gene pairs
    rng = np.random.RandomState(42)
    n_bg_pairs = 10000
    bg_i = rng.randint(0, n_genes, n_bg_pairs)
    bg_j = rng.randint(0, n_genes, n_bg_pairs)
    # Avoid self-pairs
    mask = bg_i != bg_j
    bg_corrs = corr[bg_i[mask], bg_j[mask]]
    bg_mean = float(np.mean(np.abs(bg_corrs)))

    n_enriched = 0
    n_modules_tested = 0

    for mod in membership.columns:
        mod_genes = membership.index[membership[mod] == 1].tolist()
        mod_idx = [gene_to_idx[g] for g in mod_genes if g in gene_to_idx]

        if len(mod_idx) < 2:
            cofit_results.append({
                "orgId": org_id,
                "module": mod,
                "n_members": len(mod_idx),
                "n_pairs": 0,
                "mean_abs_corr": np.nan,
                "bg_mean_abs_corr": bg_mean,
                "enrichment_ratio": np.nan,
                "mann_whitney_p": np.nan,
                "enriched": False,
            })
            continue

        # Extract within-module pairwise correlations (upper triangle)
        mod_idx_arr = np.array(mod_idx)
        within_corrs = []
        for i in range(len(mod_idx_arr)):
            for j in range(i + 1, len(mod_idx_arr)):
                within_corrs.append(corr[mod_idx_arr[i], mod_idx_arr[j]])
        within_corrs = np.array(within_corrs)

        within_mean = float(np.mean(np.abs(within_corrs)))
        enrichment = within_mean / bg_mean if bg_mean > 0 else 0.0

        # Mann-Whitney U: within-module |corr| vs random |corr| of same size
        n_within = len(within_corrs)
        bg_sample = np.abs(bg_corrs[rng.choice(len(bg_corrs),
                                                min(n_within, len(bg_corrs)),
                                                replace=False)])
        try:
            _, p_val = stats.mannwhitneyu(
                np.abs(within_corrs), bg_sample, alternative="greater"
            )
        except ValueError:
            p_val = 1.0

        is_enriched = p_val < 0.05
        if is_enriched:
            n_enriched += 1
        n_modules_tested += 1

        cofit_results.append({
            "orgId": org_id,
            "module": mod,
            "n_members": len(mod_idx),
            "n_pairs": len(within_corrs),
            "mean_abs_corr": round(within_mean, 4),
            "bg_mean_abs_corr": round(bg_mean, 4),
            "enrichment_ratio": round(enrichment, 2),
            "mann_whitney_p": p_val,
            "enriched": is_enriched,
        })

    if n_modules_tested > 0:
        pct = 100 * n_enriched / n_modules_tested
        print(f"  {org_id}: {n_enriched}/{n_modules_tested} modules enriched "
              f"({pct:.1f}%), bg |r|={bg_mean:.4f}")

cofit_df = pd.DataFrame(cofit_results)
cofit_df.to_csv(PRED_DIR / "cofitness_validation.csv", index=False)

# Summary
tested = cofit_df[cofit_df["n_pairs"] > 0]
n_total_enriched = tested["enriched"].sum()
n_total_tested = len(tested)
pct_enriched = 100 * n_total_enriched / n_total_tested if n_total_tested > 0 else 0

summary = {
    "total_modules_tested": n_total_tested,
    "total_modules_enriched": int(n_total_enriched),
    "pct_enriched": round(pct_enriched, 1),
    "mean_within_abs_corr": round(tested["mean_abs_corr"].mean(), 4),
    "mean_bg_abs_corr": round(tested["bg_mean_abs_corr"].mean(), 4),
    "mean_enrichment_ratio": round(tested["enrichment_ratio"].mean(), 1),
}
summary_df = pd.DataFrame([summary])
summary_df.to_csv(PRED_DIR / "cofitness_validation_summary.csv", index=False)

print(f"\n  OVERALL: {n_total_enriched}/{n_total_tested} modules enriched "
      f"({pct_enriched:.1f}%)")
print(f"  Mean within-module |r|: {summary['mean_within_abs_corr']}")
print(f"  Mean background |r|: {summary['mean_bg_abs_corr']}")
print(f"  Mean enrichment ratio: {summary['mean_enrichment_ratio']}×")
print(f"  Saved: {PRED_DIR / 'cofitness_validation.csv'}")
print(f"  Saved: {PRED_DIR / 'cofitness_validation_summary.csv'}")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: Genomic Adjacency Validation
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n## Section 3: Genomic Adjacency Validation")
print("=" * 70)

adj_results = []

for org_id in org_ids:
    gene_file = ANNOT_DIR / f"{org_id}_genes.csv"
    member_file = MODULE_DIR / f"{org_id}_gene_membership.csv"
    if not gene_file.exists() or not member_file.exists():
        continue

    genes = pd.read_csv(gene_file)
    genes["locusId"] = genes["locusId"].astype(str)
    membership = pd.read_csv(member_file, index_col=0)
    membership.index = membership.index.astype(str)

    # Sort by genomic position and assign order
    genes = genes.sort_values(["scaffoldId", "begin"])
    genes["gene_order"] = range(len(genes))
    # Map scaffold too so we only count adjacency within same scaffold
    locus_info = {
        row["locusId"]: (row["gene_order"], row["scaffoldId"])
        for _, row in genes.iterrows()
    }

    n_adjacent = 0
    n_pairs = 0
    n_total_genes = len(genes)

    for mod in membership.columns:
        mod_genes = membership.index[membership[mod] == 1].tolist()
        gene_info = [(locus_info[g][0], locus_info[g][1])
                     for g in mod_genes if g in locus_info]
        if len(gene_info) < 2:
            continue

        for i in range(len(gene_info)):
            for j in range(i + 1, len(gene_info)):
                n_pairs += 1
                order_i, scaff_i = gene_info[i]
                order_j, scaff_j = gene_info[j]
                if scaff_i == scaff_j and abs(order_i - order_j) <= 3:
                    n_adjacent += 1

    # Expected adjacency by chance (±3 neighbors on same scaffold)
    # Rough estimate: 6 / n_total_genes
    expected_rate = 6.0 / n_total_genes if n_total_genes > 0 else 0
    observed_rate = n_adjacent / n_pairs if n_pairs > 0 else 0
    enrichment = observed_rate / expected_rate if expected_rate > 0 else 0

    adj_results.append({
        "orgId": org_id,
        "n_adjacent_pairs": n_adjacent,
        "n_total_pairs": n_pairs,
        "observed_rate": round(observed_rate, 6),
        "expected_rate": round(expected_rate, 6),
        "enrichment": round(enrichment, 1),
    })
    print(f"  {org_id}: adjacency enrichment = {enrichment:.1f}× "
          f"(obs={observed_rate:.4f}, exp={expected_rate:.4f})")

adj_df = pd.DataFrame(adj_results)
adj_df.to_csv(PRED_DIR / "adjacency_validation.csv", index=False)
print(f"\n  Mean enrichment: {adj_df['enrichment'].mean():.1f}×")
print(f"  Saved: {PRED_DIR / 'adjacency_validation.csv'}")

print("\n" + "=" * 70)
print("BENCHMARKING COMPLETE")
print("=" * 70)
