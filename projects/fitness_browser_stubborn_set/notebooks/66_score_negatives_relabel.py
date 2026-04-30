"""
Score the Opus + Codex 5.5 relabel of the v1 755 negatives, broken down
by signal_class (stubborn vs no_signal).

For each of the 755 v1 negatives we have:
  v1 verdict (always "recalcitrant" — that's why they're in negatives.jsonl)
  Opus verdict (relabel under augmented dossier)
  Codex verdict (relabel under augmented dossier)
  signal_class (stubborn or no_signal, from notebook 65)

Categorize:
  confirmed_stubborn: BOTH Opus and Codex still say "recalcitrant"
  flipped:            BOTH agree on a non-recalcitrant verdict
  inconclusive:       LLMs disagree (no two-LLM agreement)

For confirmed_stubborn rows, signal_class = "stubborn" gives the
project's gold-standard negatives. signal_class = "no_signal" gives the
fallback "absence of evidence" negatives.

Output:
  data/relabel_negatives/relabel_results.tsv  - per-gene join
  prints headline tables to stderr
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
NEG_JSONL = PROJECT_DATA / "training_set" / "negatives.jsonl"
OPUS_DIR = PROJECT_DATA / "relabel_negatives" / "batches_claude"
CODEX_DIR = PROJECT_DATA / "relabel_negatives" / "batches_codex"
OUT_TSV = PROJECT_DATA / "relabel_negatives" / "relabel_results.tsv"


def load_verdicts(glob_pat: str) -> dict:
    out = {}
    for f in sorted(glob.glob(glob_pat)):
        for line in open(f):
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except json.JSONDecodeError: continue
            if "orgId" in r and "locusId" in r:
                out[(r["orgId"], r["locusId"])] = r
    return out


def main() -> None:
    # Load v1 negatives with signal_class
    negs = []
    with open(NEG_JSONL) as fh:
        for line in fh:
            r = json.loads(line)
            negs.append({
                "orgId": r["orgId"], "locusId": r["locusId"],
                "signal_class": r.get("signal_class", "unknown"),
                "v1_confidence": r.get("confidence", ""),
                "v1_codex_confidence": r.get("codex_confidence", ""),
            })
    print(f"v1 negatives: {len(negs)}", file=sys.stderr)

    opus = load_verdicts(str(OPUS_DIR / "batch_RN*" / "output.jsonl"))
    codex = load_verdicts(str(CODEX_DIR / "batch_RN*" / "output.jsonl"))
    print(f"Opus verdicts:  {len(opus)}", file=sys.stderr)
    print(f"Codex verdicts: {len(codex)}", file=sys.stderr)

    rows = []
    for n in negs:
        k = (n["orgId"], n["locusId"])
        ov = opus.get(k, {}); cv = codex.get(k, {})
        op_v = ov.get("verdict", "MISSING")
        cx_v = cv.get("verdict", "MISSING")
        # Categorize
        if op_v == "MISSING" or cx_v == "MISSING":
            cat = "missing_verdict"
        elif op_v == "recalcitrant" and cx_v == "recalcitrant":
            cat = "confirmed_stubborn"
        elif op_v == cx_v:
            cat = "flipped_agree"
        else:
            cat = "inconclusive"
        rows.append({
            "orgId": n["orgId"], "locusId": n["locusId"],
            "signal_class": n["signal_class"],
            "v1_confidence": n["v1_confidence"],
            "v1_codex_confidence": n["v1_codex_confidence"],
            "opus_verdict": op_v,
            "opus_confidence": ov.get("confidence", ""),
            "opus_proposed": ov.get("proposed_annotation", ""),
            "codex_verdict": cx_v,
            "codex_confidence": cv.get("confidence", ""),
            "codex_proposed": cv.get("proposed_annotation", ""),
            "category": cat,
        })

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote {OUT_TSV}", file=sys.stderr)

    # Headline tables
    print("\n=== category distribution ===", file=sys.stderr)
    print(f"  {'CATEGORY':<22} {'TOTAL':>6} {'STUBBORN':>10} {'NO_SIGNAL':>10}", file=sys.stderr)
    cat_total = Counter(r["category"] for r in rows)
    cat_by_sig = Counter((r["category"], r["signal_class"]) for r in rows)
    for cat in ["confirmed_stubborn", "flipped_agree", "inconclusive", "missing_verdict"]:
        n = cat_total[cat]
        ns = cat_by_sig.get((cat, "stubborn"), 0)
        nn = cat_by_sig.get((cat, "no_signal"), 0)
        print(f"  {cat:<22} {n:>6} {ns:>10} {nn:>10}", file=sys.stderr)

    print("\n=== Opus verdict distribution ===", file=sys.stderr)
    op_dist = Counter(r["opus_verdict"] for r in rows)
    for k, v in sorted(op_dist.items(), key=lambda x: -x[1]):
        print(f"  {k:<26} {v:>5}", file=sys.stderr)

    print("\n=== Codex verdict distribution ===", file=sys.stderr)
    cx_dist = Counter(r["codex_verdict"] for r in rows)
    for k, v in sorted(cx_dist.items(), key=lambda x: -x[1]):
        print(f"  {k:<26} {v:>5}", file=sys.stderr)

    # Critical: stubborn-grade survival rate
    print("\n=== STUBBORN-GRADE SUBSET (signal_class == stubborn) ===", file=sys.stderr)
    stub_rows = [r for r in rows if r["signal_class"] == "stubborn"]
    print(f"  total: {len(stub_rows)}", file=sys.stderr)
    stub_cat = Counter(r["category"] for r in stub_rows)
    for cat in ["confirmed_stubborn", "flipped_agree", "inconclusive", "missing_verdict"]:
        n = stub_cat[cat]
        if n: print(f"    {cat:<22} {n:>4} ({100*n/len(stub_rows):.0f}%)", file=sys.stderr)

    print("\n=== NO-SIGNAL SUBSET (signal_class == no_signal) ===", file=sys.stderr)
    ns_rows = [r for r in rows if r["signal_class"] == "no_signal"]
    print(f"  total: {len(ns_rows)}", file=sys.stderr)
    ns_cat = Counter(r["category"] for r in ns_rows)
    for cat in ["confirmed_stubborn", "flipped_agree", "inconclusive", "missing_verdict"]:
        n = ns_cat[cat]
        if n: print(f"    {cat:<22} {n:>4} ({100*n/len(ns_rows):.0f}%)", file=sys.stderr)

    # Recommendation
    new_neg = sum(1 for r in rows if r["category"] == "confirmed_stubborn")
    new_neg_stub = sum(1 for r in rows if r["category"] == "confirmed_stubborn" and r["signal_class"] == "stubborn")
    new_neg_nosig = new_neg - new_neg_stub
    print(f"\n=== confirmed v2 negatives: {new_neg} "
          f"(stubborn={new_neg_stub}, no_signal={new_neg_nosig}) ===", file=sys.stderr)
    print(f"  v1 had 755; lost {755-new_neg} to flips/inconclusive/missing", file=sys.stderr)


if __name__ == "__main__":
    main()
