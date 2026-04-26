#!/bin/bash
# Run Codex cross-check on a single batch.
# Usage: 05_run_codex_batch.sh <batch_id>
set -e
ID="$1"
if [ -z "$ID" ]; then echo "Usage: $0 <batch_id>"; exit 1; fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DIR="$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_check/batch_$ID"
INPUT="$DIR/input.md"
OUT="$DIR/output.jsonl"
PROMPT_FILE="$DIR/prompt.txt"
LOG="$DIR/log.txt"

if [ ! -f "$INPUT" ]; then echo "Missing $INPUT"; exit 1; fi

# Build prompt with dossiers + verdict instructions
{
  cat "$INPUT"
  echo ""
  echo "TASK: For each dossier above, output ONE JSONL line classifying the gene by annotation quality. Use exactly this schema:"
  echo '{"orgId":"...","locusId":"...","verdict":"improvable_new|improvable_correction|already_correctly_named|recalcitrant","confidence":"high|medium|low","proposed_annotation":"...","rationale":"2-3 sentences"}'
  echo ""
  echo "Verdict options:"
  echo "- improvable_new: hypothetical/DUF/vague but evidence supports a specific name"
  echo "- improvable_correction: existing name is wrong, better name is supported"
  echo "- already_correctly_named: existing name is supported by the evidence"
  echo "- recalcitrant: signal exists but evidence cannot pin down a specific function — cite the gap"
  echo ""
  echo "Be honest. If you cannot pin down a specific function, say recalcitrant. Output ONLY the JSONL lines, no preamble or commentary. proposed_annotation: new name for improvable_*; echo existing for already_correctly_named; null/\"\" for recalcitrant."
} > "$PROMPT_FILE"

codex exec --output-last-message "$OUT" < "$PROMPT_FILE" > "$LOG" 2>&1
echo "DONE $ID"
