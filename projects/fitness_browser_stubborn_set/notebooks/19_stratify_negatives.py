"""
Stratify the 755 final-recalcitrant negatives by evidence tier, organism,
intake confidence, and fitness strength. Writes a per-gene TSV with tier
labels plus a strong-phenotype wet-lab-target shortlist.

Outputs:
  data/negatives_stratified.tsv          — all 755, one row per gene
  data/negatives_strong_targets.tsv      — strong-phenotype subset (|fit|≥2 & |t|≥5)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

FINAL = PROJECT_DATA / "training_recalcitrant_final.jsonl"
FULL = PROJECT_DATA / "training_recalcitrant.jsonl"
OUT_ALL = PROJECT_DATA / "negatives_stratified.tsv"
OUT_STRONG = PROJECT_DATA / "negatives_strong_targets.tsv"

FIT_RE = re.compile(r"max\|fit\|=([0-9.]+)")
T_RE = re.compile(r"max\|t\|=([0-9.]+)")


def evidence_tier(n_hits: int, n_summ: int) -> str:
    if n_hits == 0:
        return "orphan"
    if n_summ == 0:
        return "hits_no_summaries"
    return "hits_with_summaries"


def main() -> None:
    final = [json.loads(l) for l in open(FINAL)]
    full = {(r["orgId"], r["locusId"]): r for r in (json.loads(l) for l in open(FULL))}
    print(f"Final negatives: {len(final)}", file=sys.stderr)

    rows = []
    for f in final:
        k = (f["orgId"], f["locusId"])
        u = full.get(k, {})
        md = u.get("dossier_md", "") or ""
        fit_m = FIT_RE.search(md)
        t_m = T_RE.search(md)
        fit = float(fit_m.group(1)) if fit_m else 0.0
        tt = float(t_m.group(1)) if t_m else 0.0
        n_hits = u.get("n_paperblast_hits", 0)
        n_summ = u.get("n_papers_with_summaries", 0)
        rows.append({
            "orgId": f["orgId"],
            "locusId": f["locusId"],
            "claude_confidence": f.get("confidence", ""),
            "codex_confidence": f.get("codex_confidence", ""),
            "both_high": int(f.get("confidence") == "high" and f.get("codex_confidence") == "high"),
            "n_paperblast_hits": n_hits,
            "n_papers_with_summaries": n_summ,
            "evidence_tier": evidence_tier(n_hits, n_summ),
            "max_abs_fit": round(fit, 3),
            "max_abs_t": round(tt, 3),
            "strong_phenotype": int(fit >= 2 and tt >= 5),
        })

    fieldnames = list(rows[0].keys())
    with open(OUT_ALL, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    strong = [r for r in rows if r["strong_phenotype"]]
    strong.sort(key=lambda r: (-r["max_abs_fit"], -r["max_abs_t"]))
    with open(OUT_STRONG, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(strong)

    # Summary to stderr
    print("\n=== Evidence tier ===", file=sys.stderr)
    for k, v in Counter(r["evidence_tier"] for r in rows).most_common():
        print(f"  {v:4d}  {k}", file=sys.stderr)
    print(f"\nBoth Claude & Codex high-confidence: {sum(r['both_high'] for r in rows)}", file=sys.stderr)
    print(f"\n=== Claude intake confidence ===", file=sys.stderr)
    for k, v in Counter(r["claude_confidence"] for r in rows).most_common():
        print(f"  {v:4d}  {k}", file=sys.stderr)
    print(f"\n=== Fitness strength ===", file=sys.stderr)
    print(f"  {sum(r['strong_phenotype'] for r in rows):4d}  strong (|fit|≥2 & |t|≥5)", file=sys.stderr)
    print(f"\nWrote {OUT_ALL} ({len(rows)} rows)", file=sys.stderr)
    print(f"Wrote {OUT_STRONG} ({len(strong)} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
