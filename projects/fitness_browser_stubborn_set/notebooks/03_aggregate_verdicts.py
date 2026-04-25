"""
Aggregate per-batch verdicts (data/batches/*/output.jsonl) into a single
deduplicated data/llm_verdicts.jsonl. Idempotent — safe to run after every
batch.

Also reports current outcome distribution.
"""
import json
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DATA = REPO_ROOT / "projects" / "fitness_browser_stubborn_set" / "data"
BATCHES_DIR = PROJECT_DATA / "batches"
VERDICTS_PATH = PROJECT_DATA / "llm_verdicts.jsonl"


def main() -> None:
    seen: set = set()
    rows: list = []

    # Pull existing aggregated file (preserve any manual edits)
    if VERDICTS_PATH.exists():
        with open(VERDICTS_PATH) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                key = (r["orgId"], r["locusId"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(r)

    # Walk each batch dir
    new_count = 0
    if BATCHES_DIR.exists():
        for batch in sorted(BATCHES_DIR.iterdir()):
            out = batch / "output.jsonl"
            if not out.exists():
                continue
            with open(out) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    key = (r.get("orgId"), r.get("locusId"))
                    if not key[0] or not key[1] or key in seen:
                        continue
                    seen.add(key)
                    rows.append(r)
                    new_count += 1

    # Write back
    with open(VERDICTS_PATH, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    print(f"Total verdicts: {len(rows):,} (added {new_count} new)")
    print(f"Wrote {VERDICTS_PATH}")

    # Outcome distribution
    print("\nOutcome distribution:")
    counts = Counter(r["verdict"] for r in rows)
    for verdict, n in counts.most_common():
        print(f"  {verdict:30}: {n}")
    confidence = Counter(r.get("confidence", "?") for r in rows)
    print("\nConfidence distribution:")
    for c, n in confidence.most_common():
        print(f"  {c:10}: {n}")


if __name__ == "__main__":
    main()
