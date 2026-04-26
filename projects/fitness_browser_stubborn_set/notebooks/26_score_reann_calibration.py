"""
Score the LLM verdicts on the reannotation calibration set against the
human curators' annotations.

Inputs:
  data/reannotation_set.parquet                  — human ground truth
  data/batches_reann/batch_RA*/output.jsonl      — Claude verdicts
  data/codex_xcheck_reann/batch_RA*/output.jsonl — Codex cross-check verdicts

Output:
  data/reann_calibration.tsv  — per-gene comparison row
  + headline metrics printed to stderr (also captured in REPORT.md update)
"""
from __future__ import annotations

import csv
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

REANN = PROJECT_DATA / "reannotation_set.parquet"
CLAUDE_GLOB = str(PROJECT_DATA / "batches_reann" / "batch_RA*" / "output.jsonl")
CODEX_GLOB = str(PROJECT_DATA / "codex_xcheck_reann" / "batch_RA*" / "output.jsonl")
OUT = PROJECT_DATA / "reann_calibration.tsv"

TOKEN_RE = re.compile(r"[a-z0-9]+")
EC_RE = re.compile(r"\b\d+\.\d+\.\d+\.\d+\b")


def tokens(s: str) -> set:
    return set(TOKEN_RE.findall((s or "").lower()))


def derive_human_category(original: str) -> str:
    """Match what NB01's category logic would say about the pre-curation desc."""
    o = (original or "").lower()
    if not o or "hypothetical" in o or "uncharacterized" in o:
        return "improvable_new"
    if re.search(r"duf\d+|domain of unknown function|upf\d+", o):
        return "improvable_new"
    if re.search(r"\bputative\b|\bpredicted\b|\bprobable\b", o):
        return "improvable_new"
    return "improvable_correction"


def name_match(human: str, llm: str) -> bool:
    """Token-set Jaccard ≥ 0.5 OR EC equality."""
    if not human or not llm:
        return False
    h_ec = set(EC_RE.findall(human))
    l_ec = set(EC_RE.findall(llm))
    if h_ec and l_ec and (h_ec & l_ec):
        return True
    h, l = tokens(human), tokens(llm)
    if not h or not l:
        return False
    j = len(h & l) / len(h | l)
    return j >= 0.5


def load_verdicts(glob_pat: str) -> dict:
    out = {}
    for f in sorted(glob.glob(glob_pat)):
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "orgId" in r and "locusId" in r:
                out[(r["orgId"], r["locusId"])] = r
    return out


def main() -> None:
    reann = pd.read_parquet(REANN).dropna(subset=["orgId", "locusId"]).reset_index(drop=True)
    print(f"Human reannotations: {len(reann)}", file=sys.stderr)

    claude = load_verdicts(CLAUDE_GLOB)
    codex = load_verdicts(CODEX_GLOB)
    print(f"Claude verdicts: {len(claude)}", file=sys.stderr)
    print(f"Codex verdicts:  {len(codex)}", file=sys.stderr)

    rows = []
    for _, hr in reann.iterrows():
        k = (hr["orgId"], hr["locusId"])
        c = claude.get(k, {})
        x = codex.get(k, {})
        human_ann = hr.get("new_annotation") or ""
        c_ann = c.get("proposed_annotation") or ""
        x_ann = x.get("proposed_annotation") or ""
        c_verdict = c.get("verdict") or "missing"
        x_verdict = x.get("verdict") or "missing"
        human_cat = derive_human_category(hr.get("original_description") or "")

        # Agreement classification
        c_match = name_match(human_ann, c_ann)
        x_match = name_match(human_ann, x_ann)

        if c_verdict in ("improvable_new", "improvable_correction"):
            if c_match:
                claude_class = "recovered"
            else:
                claude_class = "right_type_wrong_name"
        elif c_verdict == "recalcitrant":
            claude_class = "false_negative"
        elif c_verdict == "already_correctly_named":
            claude_class = "false_positive_named"
        else:
            claude_class = "missing"

        if x_verdict in ("improvable_new", "improvable_correction"):
            codex_class = "recovered" if x_match else "right_type_wrong_name"
        elif x_verdict == "recalcitrant":
            codex_class = "false_negative"
        elif x_verdict == "already_correctly_named":
            codex_class = "false_positive_named"
        else:
            codex_class = "missing"

        rows.append({
            "orgId": k[0],
            "locusId": k[1],
            "original_description": hr.get("original_description") or "",
            "human_annotation": human_ann,
            "human_category": human_cat,
            "human_comment": (hr.get("comment") or "").replace("\n", " ").replace("\t", " "),
            "claude_verdict": c_verdict,
            "claude_proposal": c_ann,
            "claude_confidence": c.get("confidence", ""),
            "claude_name_match": int(c_match),
            "claude_class": claude_class,
            "codex_verdict": x_verdict,
            "codex_proposal": x_ann,
            "codex_confidence": x.get("confidence", ""),
            "codex_name_match": int(x_match),
            "codex_class": codex_class,
        })

    fields = list(rows[0].keys())
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT} ({len(rows)} rows)", file=sys.stderr)

    # Headline metrics
    print("\n=== Claude (alone) ===", file=sys.stderr)
    cc = Counter(r["claude_class"] for r in rows)
    for k in ("recovered", "right_type_wrong_name", "false_negative", "false_positive_named", "missing"):
        v = cc.get(k, 0)
        print(f"  {v:5d}  ({100*v/len(rows):4.1f}%)  {k}", file=sys.stderr)
    recall_type = (cc["recovered"] + cc["right_type_wrong_name"]) / len(rows)
    recall_name = cc["recovered"] / len(rows)
    print(f"  Recall@type: {100*recall_type:.1f}%", file=sys.stderr)
    print(f"  Recall@name: {100*recall_name:.1f}%", file=sys.stderr)

    print("\n=== Codex (after cross-check) ===", file=sys.stderr)
    xc = Counter(r["codex_class"] for r in rows)
    for k in ("recovered", "right_type_wrong_name", "false_negative", "false_positive_named", "missing"):
        v = xc.get(k, 0)
        print(f"  {v:5d}  ({100*v/len(rows):4.1f}%)  {k}", file=sys.stderr)
    recall_type_x = (xc["recovered"] + xc["right_type_wrong_name"]) / len(rows)
    recall_name_x = xc["recovered"] / len(rows)
    print(f"  Recall@type: {100*recall_type_x:.1f}%", file=sys.stderr)
    print(f"  Recall@name: {100*recall_name_x:.1f}%", file=sys.stderr)

    # Both-LLMs-agree (apples-to-apples with the 1,200 distributable set)
    print("\n=== Both Claude+Codex agree (training-filter equivalent) ===", file=sys.stderr)
    both_recovered = sum(1 for r in rows if r["claude_class"] == "recovered" and r["codex_class"] == "recovered")
    both_right_type = sum(1 for r in rows if r["claude_class"] in ("recovered", "right_type_wrong_name")
                          and r["codex_class"] in ("recovered", "right_type_wrong_name"))
    both_false_neg = sum(1 for r in rows if r["claude_class"] == "false_negative" and r["codex_class"] == "false_negative")
    print(f"  both recovered (name match):   {both_recovered}  ({100*both_recovered/len(rows):.1f}%)", file=sys.stderr)
    print(f"  both right_type:               {both_right_type}  ({100*both_right_type/len(rows):.1f}%)", file=sys.stderr)
    print(f"  both false_negative:           {both_false_neg}  ({100*both_false_neg/len(rows):.1f}%)  ← humans annotated, both LLMs said recalcitrant", file=sys.stderr)


if __name__ == "__main__":
    main()
