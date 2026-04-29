"""
Score the v2 sample reclassification (40-gene sample, dossier augmented
with InterPro union + cross-organism ortholog fitness on top of the v1
augmented paper summaries).

Identical structure to 51_score_sample_reclass.py; just points at the v2
batch directories. Output:
  data/sample_reclass_v2/reclass_results.tsv
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
SAMPLE_DIR = PROJECT_DATA / "sample_reclass_v2"
KEYS_TSV = SAMPLE_DIR / "sample_keys.tsv"


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
    sample = []
    with open(KEYS_TSV) as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            sample.append(r)

    claude = load_verdicts(str(SAMPLE_DIR / "batches_claude" / "batch_SV*" / "output.jsonl"))
    codex  = load_verdicts(str(SAMPLE_DIR / "batches_codex"  / "batch_SV*" / "output.jsonl"))
    print(f"sample size: {len(sample)}", file=sys.stderr)
    print(f"new Claude verdicts: {len(claude)}", file=sys.stderr)
    print(f"new Codex verdicts:  {len(codex)}", file=sys.stderr)
    print()

    flips_claude: Counter = Counter()
    flips_codex: Counter = Counter()
    rows = []
    for s in sample:
        k = (s["orgId"], s["locusId"])
        orig = s["original_verdict"]
        c = claude.get(k, {}).get("verdict") or "MISSING"
        x = codex.get(k, {}).get("verdict") or "MISSING"
        c_flip = (c != orig and c != "MISSING")
        x_flip = (x != orig and x != "MISSING")
        if c_flip:
            flips_claude[(orig, c, s["source"])] += 1
        if x_flip:
            flips_codex[(orig, x, s["source"])] += 1
        rows.append({
            "orgId": s["orgId"], "locusId": s["locusId"],
            "source": s["source"],
            "original_verdict": orig,
            "new_claude": c, "new_codex": x,
            "claude_flipped": c_flip, "codex_flipped": x_flip,
            "both_agree_flip": c_flip and x_flip and c == x,
        })

    out_tsv = SAMPLE_DIR / "reclass_results.tsv"
    with open(out_tsv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_tsv}\n", file=sys.stderr)

    # Drop rows where verdicts are MISSING — incomplete batches shouldn't
    # bias the rate downward. Report covered/uncovered separately.
    covered = [r for r in rows if r["new_claude"] != "MISSING" and r["new_codex"] != "MISSING"]
    uncovered = len(rows) - len(covered)
    print(f"covered (both LLMs returned a verdict): {len(covered)}/{len(rows)} "
          f"(uncovered: {uncovered})", file=sys.stderr)

    by_source: dict[str, dict] = {"negatives": {"n":0,"claude_flip":0,"codex_flip":0,"both_flip":0},
                                   "positives": {"n":0,"claude_flip":0,"codex_flip":0,"both_flip":0}}
    for r in covered:
        s = r["source"]
        by_source[s]["n"] += 1
        if r["claude_flipped"]: by_source[s]["claude_flip"] += 1
        if r["codex_flipped"]:  by_source[s]["codex_flip"]  += 1
        if r["both_agree_flip"]: by_source[s]["both_flip"]  += 1

    print("\n=== flip rates (covered subset) ===", file=sys.stderr)
    for src, d in by_source.items():
        if d["n"] == 0: continue
        print(f"\n{src} (n={d['n']}):", file=sys.stderr)
        print(f"  Claude flipped:           {d['claude_flip']}/{d['n']} ({100*d['claude_flip']/d['n']:.0f}%)", file=sys.stderr)
        print(f"  Codex flipped:            {d['codex_flip']}/{d['n']} ({100*d['codex_flip']/d['n']:.0f}%)", file=sys.stderr)
        print(f"  Both flipped + agree:     {d['both_flip']}/{d['n']} ({100*d['both_flip']/d['n']:.0f}%)", file=sys.stderr)

    print(f"\n=== flip directions (Claude) ===", file=sys.stderr)
    for (orig, new, src), n in sorted(flips_claude.items(), key=lambda x: -x[1]):
        print(f"  [{src}]  {orig} -> {new}: {n}", file=sys.stderr)
    print(f"\n=== flip directions (Codex) ===", file=sys.stderr)
    for (orig, new, src), n in sorted(flips_codex.items(), key=lambda x: -x[1]):
        print(f"  [{src}]  {orig} -> {new}: {n}", file=sys.stderr)

    total_n = sum(d["n"] for d in by_source.values())
    total_both = sum(d["both_flip"] for d in by_source.values())
    if total_n == 0:
        print("\nNo covered rows; cannot compute headline rate.", file=sys.stderr)
        return
    rate = 100 * total_both / total_n
    print(f"\n=== overall: both-LLM-agreement flip rate = {rate:.1f}% "
          f"({total_both}/{total_n}, covered subset) ===", file=sys.stderr)
    if rate >= 5:
        print(f"-> RECOMMEND full re-run (flip rate >= 5% justifies the work)", file=sys.stderr)
    else:
        print(f"-> Original labels stable under the augmented dossier; full re-run not warranted", file=sys.stderr)


if __name__ == "__main__":
    main()
