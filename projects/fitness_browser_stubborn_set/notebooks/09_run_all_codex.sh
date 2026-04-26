#!/bin/bash
# Run Codex summarizer in parallel over all pmIds with cached PMC XML.
# Skips papers already summarized.
# Usage: 09_run_all_codex.sh [--parallel N]
set -e

PARALLEL=4
if [ "$1" = "--parallel" ]; then
  PARALLEL="$2"
fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export SUM_DIR="${SUM_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_summaries}"
export PMC_DIR="${PMC_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_summaries/pmc}"
PER_PAPER_DIR="$SUM_DIR/per_paper"
mkdir -p "$PER_PAPER_DIR"

# Build list of pmIds with cached XML
TODO=$(awk -F'\t' 'NR>1 && $3==1 {print $1}' "$SUM_DIR/pmc_index.tsv")
TOTAL=$(echo "$TODO" | wc -l)
echo "Papers with cached PMC XML: $TOTAL"

# Filter to those without an existing TSV
TODO_FILTERED=""
SKIPPED=0
for pmid in $TODO; do
  if [ -f "$PER_PAPER_DIR/${pmid}.tsv" ]; then
    SKIPPED=$((SKIPPED+1))
    continue
  fi
  TODO_FILTERED="$TODO_FILTERED $pmid"
done
N_TODO=$(echo "$TODO_FILTERED" | wc -w)
echo "Already summarized: $SKIPPED"
echo "To run: $N_TODO  (parallel: $PARALLEL)"

# Use xargs for parallelism
echo "$TODO_FILTERED" | tr ' ' '\n' | grep -v '^$' | \
  xargs -n1 -P "$PARALLEL" "$REPO_ROOT/projects/fitness_browser_stubborn_set/notebooks/08_run_codex_summarize.sh"
