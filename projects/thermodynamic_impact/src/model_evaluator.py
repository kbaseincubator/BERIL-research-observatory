"""FBA/FVA comparison framework for evaluating thermodynamic impact on metabolic models."""


def classify_fva_results(fva_results, tol=1e-9):
    """Classify reactions from FVA into Blocked/Forward/Reverse/Reversible.

    Args:
        fva_results: dict[rxn_id -> {MIN: float, MAX: float}]
        tol: tolerance for zero-flux detection

    Returns:
        dict[rxn_id -> classification_string]
    """
    classes = {}
    for rxn_id, vals in fva_results.items():
        mn = vals.get("MIN", 0) or 0
        mx = vals.get("MAX", 0) or 0
        if abs(mn) < tol and abs(mx) < tol:
            classes[rxn_id] = "Blocked"
        elif mn >= -tol and mx > tol:
            classes[rxn_id] = "Forward"
        elif mn < -tol and mx <= tol:
            classes[rxn_id] = "Reverse"
        else:
            classes[rxn_id] = "Reversible"
    return classes


def compare_fva_classifications(old_classes, new_classes):
    """Compare two FVA classification dicts and count changes.

    Returns:
        dict with counts: newly_blocked, newly_unblocked, direction_changed, unchanged
    """
    common = set(old_classes.keys()) & set(new_classes.keys())
    counts = {
        "total": len(common),
        "newly_blocked": 0,
        "newly_unblocked": 0,
        "direction_changed": 0,
        "unchanged": 0,
    }

    changed_reactions = []
    for rxn_id in common:
        old = old_classes[rxn_id]
        new = new_classes[rxn_id]
        if old == new:
            counts["unchanged"] += 1
        elif old != "Blocked" and new == "Blocked":
            counts["newly_blocked"] += 1
            changed_reactions.append((rxn_id, old, new))
        elif old == "Blocked" and new != "Blocked":
            counts["newly_unblocked"] += 1
            changed_reactions.append((rxn_id, old, new))
        else:
            counts["direction_changed"] += 1
            changed_reactions.append((rxn_id, old, new))

    return counts, changed_reactions


def compute_phenotype_metrics(results_df):
    """Compute accuracy, sensitivity, specificity from phenotype results.

    Args:
        results_df: DataFrame with 'classification' column (CP/CN/FP/FN)

    Returns:
        dict with accuracy, sensitivity, specificity, cp, cn, fp, fn
    """
    cp = (results_df["classification"] == "CP").sum()
    cn = (results_df["classification"] == "CN").sum()
    fp = (results_df["classification"] == "FP").sum()
    fn = (results_df["classification"] == "FN").sum()
    total = cp + cn + fp + fn

    return {
        "cp": int(cp),
        "cn": int(cn),
        "fp": int(fp),
        "fn": int(fn),
        "total": int(total),
        "accuracy": (cp + cn) / total if total > 0 else 0,
        "sensitivity": cp / (cp + fn) if (cp + fn) > 0 else 0,
        "specificity": cn / (cn + fp) if (cn + fp) > 0 else 0,
    }
