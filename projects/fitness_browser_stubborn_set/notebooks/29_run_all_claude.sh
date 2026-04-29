#!/bin/bash
# Run Claude classification in parallel over all reann calibration batches.
# Skips batches whose output.jsonl already has >= EXPECTED_LINES lines.
# Usage: 29_run_all_claude.sh [--parallel N] [--expected-lines N]
set -e

PARALLEL=4
EXPECTED=10
while [ $# -gt 0 ]; do
  case "$1" in
    --parallel) PARALLEL="$2"; shift 2;;
    --expected-lines) EXPECTED="$2"; shift 2;;
    *) shift;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BATCHES_DIR="${BATCHES_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/batches_reann}"
BATCH_PREFIX="${BATCH_PREFIX:-batch_RA}"
RUNNER="$REPO_ROOT/projects/fitness_browser_stubborn_set/notebooks/28_run_claude_classify.sh"
export BATCHES_DIR

TODO=""
SKIPPED=0
for d in "$BATCHES_DIR"/${BATCH_PREFIX}*; do
  [ -d "$d" ] || continue
  bid=$(basename "$d" | sed 's/batch_//')
  if [ -f "$d/output.jsonl" ]; then
    lines=$(wc -l < "$d/output.jsonl" 2>/dev/null || echo 0)
    if [ "$lines" -ge "$EXPECTED" ]; then
      SKIPPED=$((SKIPPED+1))
      continue
    fi
  fi
  TODO="$TODO $bid"
done
N=$(echo "$TODO" | wc -w)
echo "Already complete: $SKIPPED"
echo "To run: $N (parallel: $PARALLEL, expected-lines: $EXPECTED)"

echo "$TODO" | tr ' ' '\n' | grep -v '^$' | \
  xargs -n1 -P "$PARALLEL" "$RUNNER"
