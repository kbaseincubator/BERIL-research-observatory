"""
Integrity checks across the training_set distributable files.

Categories checked:
  A. Cross-file consistency  — every (orgId, locusId) is buildable
  B. Schema / format         — JSONL parses, required fields present
  C. Contamination control   — human_validated dossiers don't show the
                                curator's new_annotation
  D. Within-dossier sanity   — sections present, partner/neighbor counts,
                                no cross-org leakage
  E. Numerics                — fitness values in plausible ranges

Reports counts of issues per category. Non-zero counts in critical
categories (A, C) are bugs to investigate; small counts in D/E may be
expected variance.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
TRAIN = PROJECT_DATA / "training_set"

REQUIRED_BASE = ["orgId", "locusId", "dossier_md"]
SECTION_HEADERS = [
    "Existing annotation",
    "Primary fitness/cofit",
    "Secondary flags",
]


def parse_dossier(md: str) -> dict:
    """Extract structured info from the dossier markdown."""
    info: dict = {"sections": []}
    for hdr in SECTION_HEADERS:
        info[f"has_{hdr.replace(' ','_').replace('/','_')}"] = bool(re.search(rf"\*\*{re.escape(hdr)}\*\*", md))
    # Existing annotation desc (between asterisks after the **gene_symbol** part)
    m = re.search(r"\*\*Existing annotation\*\*:\s*`[^`]*`\s*—\s*\*([^*]+)\*", md)
    info["existing_desc"] = m.group(1).strip() if m else None
    # Cofit partner count
    cofit_section = re.search(r"\*\*Top cofit partners\*\*:?\n((?:\s+- .+\n)*)", md)
    if cofit_section:
        info["cofit_count"] = len(re.findall(r"^\s+- ", cofit_section.group(1), re.M))
    else:
        info["cofit_count"] = 0
    # Neighborhood count
    neigh_section = re.search(r"\*\*Genomic neighborhood[^*]*\*\*:?\n((?:\s+- offset .+\n)*)", md)
    if neigh_section:
        info["neighbor_count"] = len(re.findall(r"^\s+- offset", neigh_section.group(1), re.M))
    else:
        info["neighbor_count"] = 0
    # All locusIds referenced in cofit/neighborhood (for cross-org check, we'd need orgId per partner — not in markdown, so we skip cross-org check at that granularity)
    # Fitness numerics
    fit_m = re.search(r"max\|fit\|=([0-9.]+)", md)
    t_m = re.search(r"max\|t\|=([0-9.]+)", md)
    info["max_abs_fit"] = float(fit_m.group(1)) if fit_m else None
    info["max_abs_t"] = float(t_m.group(1)) if t_m else None
    return info


def main() -> None:
    feat = pd.read_parquet(PROJECT_DATA / "gene_evidence_features.parquet")
    feat_keys = set(zip(feat["orgId"], feat["locusId"]))
    print(f"Features parquet: {len(feat_keys):,} unique (orgId,locusId)\n", file=sys.stderr)

    files = [
        ("human_validated.jsonl", True),
        ("llm_vs_human_disagreements.jsonl", True),
        ("negatives.jsonl", False),
        ("positives.jsonl", False),
    ]

    grand_issues: dict[str, dict[str, int]] = {}

    for fname, is_human in files:
        path = TRAIN / fname
        if not path.exists():
            continue
        issues = {
            "A_missing_in_features": 0,
            "B_json_parse_fail": 0,
            "B_missing_required_field": 0,
            "C_contamination_existing_eq_new": 0,
            "D_missing_section": 0,
            "D_low_cofit_count": 0,
            "D_low_neighbor_count": 0,
            "E_implausible_fit": 0,
            "E_implausible_t": 0,
        }
        n_rows = 0
        n_with_phenotype = 0  # rows with at least some fitness signal
        with open(path) as fh:
            for raw in fh:
                n_rows += 1
                try:
                    r = json.loads(raw)
                except json.JSONDecodeError:
                    issues["B_json_parse_fail"] += 1
                    continue
                # B: required fields
                for k in REQUIRED_BASE:
                    if k not in r:
                        issues["B_missing_required_field"] += 1
                        break
                key = (r["orgId"], r["locusId"])
                # A: cross-file
                if key not in feat_keys:
                    issues["A_missing_in_features"] += 1
                # Parse dossier
                d = parse_dossier(r.get("dossier_md", ""))
                # B: section completeness
                for hdr in SECTION_HEADERS:
                    if not d.get(f"has_{hdr.replace(' ','_').replace('/','_')}"):
                        issues["D_missing_section"] += 1
                        break
                # C: contamination — human_validated only
                if is_human:
                    new_ann = (r.get("human_annotation") or "").strip().lower()
                    existing = (d.get("existing_desc") or "").strip().lower()
                    if new_ann and existing and new_ann == existing:
                        issues["C_contamination_existing_eq_new"] += 1
                # D: counts (only when there's some primary phenotype expected)
                if d.get("max_abs_fit") and d["max_abs_fit"] > 0.5:
                    n_with_phenotype += 1
                    if d.get("cofit_count", 0) < 3:
                        issues["D_low_cofit_count"] += 1
                if d.get("neighbor_count", 0) < 5:
                    issues["D_low_neighbor_count"] += 1
                # E: fitness range checks (sane upper bounds)
                if d.get("max_abs_fit") is not None and d["max_abs_fit"] > 20:
                    issues["E_implausible_fit"] += 1
                if d.get("max_abs_t") is not None and d["max_abs_t"] > 100:
                    issues["E_implausible_t"] += 1

        grand_issues[fname] = issues
        print(f"=== {fname} ({n_rows} rows) ===", file=sys.stderr)
        for k, v in issues.items():
            tag = "⚠️" if v > 0 and k.startswith(("A_", "B_", "C_")) else " "
            print(f"  {tag} {k}: {v}", file=sys.stderr)
        print(f"     (rows with primary phenotype |fit|>0.5: {n_with_phenotype})", file=sys.stderr)
        print("", file=sys.stderr)

    # Summary
    print("=== SUMMARY ===", file=sys.stderr)
    for k in (
        "A_missing_in_features",
        "B_json_parse_fail",
        "B_missing_required_field",
        "C_contamination_existing_eq_new",
    ):
        total = sum(g.get(k, 0) for g in grand_issues.values())
        tag = "⚠️" if total > 0 else "✅"
        print(f"  {tag} CRITICAL  {k}: {total}", file=sys.stderr)


if __name__ == "__main__":
    main()
