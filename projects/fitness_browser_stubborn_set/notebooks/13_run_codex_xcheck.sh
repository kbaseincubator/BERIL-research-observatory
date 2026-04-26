#!/bin/bash
# Run Codex cross-check on one augmented batch.
# Usage: 13_run_codex_xcheck.sh <batch_id>
# Reads:  data/codex_xcheck/batch_<id>/input.md
# Writes: data/codex_xcheck/batch_<id>/output.jsonl
#         data/codex_xcheck/batch_<id>/log.txt
set -e
ID="$1"
if [ -z "$ID" ]; then echo "Usage: $0 <batch_id>"; exit 1; fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DIR="$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_xcheck/batch_$ID"
INPUT="$DIR/input.md"
OUT="$DIR/output.jsonl"
PROMPT_FILE="$DIR/prompt.txt"
LOG="$DIR/log.txt"

if [ ! -f "$INPUT" ]; then echo "Missing $INPUT"; exit 1; fi

# Skip if already done
if [ -f "$OUT" ] && [ -s "$OUT" ]; then
  echo "SKIP $ID (already done)"
  exit 0
fi

# Build prompt
{
  cat "$INPUT"
  echo ""
  echo "TASK: For EACH of the 25 dossiers above, output ONE JSONL line classifying the gene by annotation quality. Each dossier now includes per-paper PaperBLAST literature summaries (where available). Use those summaries as evidence."
  echo ""
  echo "Output schema (one line per gene, no extra commentary, no preamble):"
  echo '{"orgId":"...","locusId":"...","verdict":"improvable_new|improvable_correction|already_correctly_named|recalcitrant","confidence":"high|medium|low","proposed_annotation":"...","rationale":"2-3 sentences citing specific evidence"}'
  echo ""
  echo "Verdict definitions:"
  echo "- improvable_new: gene was hypothetical/DUF/vague, evidence (including the literature summaries) supports a specific name"
  echo "- improvable_correction: existing name is wrong, evidence supports a better one"
  echo "- already_correctly_named: existing name is supported by the evidence"
  echo "- recalcitrant: real fitness/cofit signal exists but evidence (INCLUDING the PaperBLAST literature summaries) cannot pin down a specific function. Cite the gap explicitly."
  echo ""
  echo "Be honest. Use the literature summaries — they are the key new evidence. If summaries identify a specific function for the homolog, this is likely improvable_new or improvable_correction. If summaries also fail to pin down the function (or summaries are absent because no homolog was characterized), recalcitrant is appropriate. proposed_annotation: new name for improvable_*; echo existing for already_correctly_named; null/\"\" for recalcitrant."
} > "$PROMPT_FILE"

"${CODEX_BIN:-codex}" exec --model gpt-5.5 --sandbox workspace-write --ephemeral --output-last-message "$OUT" < "$PROMPT_FILE" > "$LOG" 2>&1
echo "DONE $ID"
