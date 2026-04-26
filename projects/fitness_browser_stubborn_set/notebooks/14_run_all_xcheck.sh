#!/bin/bash
# Launch Codex cross-check on all 49 batches in parallel.
# Usage: 14_run_all_xcheck.sh [--parallel N]
set -e

PARALLEL=8
if [ "$1" = "--parallel" ]; then
  PARALLEL="$2"
fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export XCHECK_DIR="${XCHECK_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_xcheck}"
BATCH_PREFIX="${BATCH_PREFIX:-batch_X}"

# Build TODO list of batch IDs
TODO=""
SKIPPED=0
for d in "$XCHECK_DIR"/${BATCH_PREFIX}*; do
  bid=$(basename "$d" | sed 's/batch_//')
  if [ -f "$d/output.jsonl" ] && [ -s "$d/output.jsonl" ]; then
    SKIPPED=$((SKIPPED+1))
    continue
  fi
  TODO="$TODO $bid"
done
N=$(echo "$TODO" | wc -w)
echo "Already done: $SKIPPED"
echo "To run: $N (parallel: $PARALLEL)"

echo "$TODO" | tr ' ' '\n' | grep -v '^$' | \
  xargs -n1 -P "$PARALLEL" "$REPO_ROOT/projects/fitness_browser_stubborn_set/notebooks/13_run_codex_xcheck.sh"
