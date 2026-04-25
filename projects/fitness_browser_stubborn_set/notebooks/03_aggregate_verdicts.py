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
DEFAULT_VERDICTS_PATH = PROJECT_DATA / "llm_verdicts.jsonl"


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verdicts-file", default=str(DEFAULT_VERDICTS_PATH),
                        help="output JSONL (default: llm_verdicts.jsonl)")
    parser.add_argument("--batch-prefix", default=None,
                        help="if set, only aggregate batches whose dir name "
                             "starts with batch_<prefix> (e.g. 'B' for priority, "
                             "'R' for random sample)")
    args = parser.parse_args()
    verdicts_path = Path(args.verdicts_file)
    if not verdicts_path.is_absolute():
        verdicts_path = PROJECT_DATA / verdicts_path

    seen: set = set()
    rows: list = []

    # Pull existing aggregated file (preserve any manual edits)
    if verdicts_path.exists():
        with open(verdicts_path) as fh:
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
            if args.batch_prefix is not None:
                if not batch.name.startswith(f"batch_{args.batch_prefix}"):
                    continue
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
    with open(verdicts_path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    print(f"Total verdicts: {len(rows):,} (added {new_count} new)")
    print(f"Wrote {verdicts_path}")

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
