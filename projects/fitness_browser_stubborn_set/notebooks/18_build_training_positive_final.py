"""
Build training_positive_final.jsonl — the Claude ∩ Codex agreement set
where both LLMs called the gene `already_correctly_named`.

Mirrors the slim schema of training_recalcitrant_final.jsonl:
  orgId, locusId, verdict, proposed_annotation, ec_number, rationale,
  confidence, papers_consulted, codex_verdict, codex_confidence,
  codex_rationale
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"

VERDICTS = PROJECT_DATA / "positive_sample_500.jsonl"
XCHECK_DIR = PROJECT_DATA / "codex_xcheck_positive"
OUT_PATH = PROJECT_DATA / "training_positive_final.jsonl"
ALL_OUT = PROJECT_DATA / "training_positive_xcheck.jsonl"  # all 500 with merged Codex


def main() -> None:
    claude = {}
    with open(VERDICTS) as fh:
        for line in fh:
            r = json.loads(line)
            claude[(r["orgId"], r["locusId"])] = r
    print(f"Claude positive verdicts: {len(claude)}", file=sys.stderr)

    codex = {}
    for path in sorted(glob.glob(str(XCHECK_DIR / "batch_P*" / "output.jsonl"))):
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            codex[(r["orgId"], r["locusId"])] = r
    print(f"Codex xcheck verdicts: {len(codex)}", file=sys.stderr)

    n_all = 0
    n_agree = 0
    with open(ALL_OUT, "w") as fall, open(OUT_PATH, "w") as fagree:
        for k, c in claude.items():
            x = codex.get(k)
            row = {
                "orgId": c["orgId"],
                "locusId": c["locusId"],
                "verdict": c["verdict"],
                "proposed_annotation": c.get("proposed_annotation", "") or "",
                "ec_number": c.get("ec_number", "") or "",
                "rationale": c.get("rationale", ""),
                "confidence": c.get("confidence", ""),
                "papers_consulted": c.get("papers_consulted", []),
                "codex_verdict": x["verdict"] if x else None,
                "codex_confidence": x.get("confidence") if x else None,
                "codex_rationale": x.get("rationale") if x else None,
                "codex_proposed_annotation": x.get("proposed_annotation") if x else None,
            }
            fall.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_all += 1
            if x and x["verdict"] == "already_correctly_named":
                fagree.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_agree += 1

    print(f"\nWrote {ALL_OUT}: {n_all} rows (all positive + Codex)", file=sys.stderr)
    print(f"Wrote {OUT_PATH}: {n_agree} rows (Claude ∩ Codex agreement)", file=sys.stderr)


if __name__ == "__main__":
    main()
