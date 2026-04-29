#!/bin/bash
# Parallel runner for alt-source codex summarization.
set -e
PARALLEL=4
if [ "$1" = "--parallel" ]; then PARALLEL="$2"; fi
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export SUM_DIR="${SUM_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_summaries_altsource}"
PER_PAPER_DIR="$SUM_DIR/per_paper"
mkdir -p "$PER_PAPER_DIR"

TODO=$(awk -F'\t' 'NR>1 && $2!="none" && $3>200 {print $1}' "$SUM_DIR/source_index.tsv")
TOTAL=$(echo "$TODO" | wc -w)
echo "Papers with alt-source text: $TOTAL"

TODO_FILTERED=""
for pmid in $TODO; do
  [ -f "$PER_PAPER_DIR/${pmid}.tsv" ] && [ -s "$PER_PAPER_DIR/${pmid}.tsv" ] && continue
  TODO_FILTERED="$TODO_FILTERED $pmid"
done
N=$(echo "$TODO_FILTERED" | wc -w)
echo "To run: $N (parallel: $PARALLEL)"

echo "$TODO_FILTERED" | tr ' ' '\n' | grep -v '^$' | \
  xargs -n1 -P "$PARALLEL" "$REPO_ROOT/projects/fitness_browser_stubborn_set/notebooks/43_run_codex_summarize_altsource.sh"
