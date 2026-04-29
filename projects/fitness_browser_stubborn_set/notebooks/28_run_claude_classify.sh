#!/bin/bash
# Run Claude (Sonnet 4.6) classification on one reannotation calibration batch.
# Usage: 28_run_claude_classify.sh <batch_id>
# Reads:  data/batches_reann/batch_<id>/input.md
# Writes: data/batches_reann/batch_<id>/output.jsonl
#         data/batches_reann/batch_<id>/log.txt
set -e
ID="$1"
if [ -z "$ID" ]; then echo "Usage: $0 <batch_id>"; exit 1; fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DIR="${BATCHES_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/batches_reann}/batch_$ID"
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
N_DOSSIERS=$(grep -c '^## Dossier ' "$INPUT")
{
  cat "$INPUT"
  echo ""
  echo "TASK: For EACH of the $N_DOSSIERS dossiers above, output ONE JSONL line classifying the gene by annotation quality."
  echo ""
  echo 'Output schema (one line per gene, no preamble, no commentary, no markdown — only JSONL):'
  echo '{"orgId":"...","locusId":"...","verdict":"improvable_new|improvable_correction|already_correctly_named|recalcitrant","confidence":"high|medium|low","proposed_annotation":"...","ec_number":"...","rationale":"2-3 sentences citing specific evidence","papers_consulted":["PMID ..."]}'
  echo ""
  echo "Verdict definitions:"
  echo "- improvable_new: existing annotation is hypothetical / DUF / vague / blank, AND evidence supports a specific name"
  echo "- improvable_correction: existing name is wrong; evidence supports a better one"
  echo "- already_correctly_named: existing name is supported by the evidence"
  echo "- recalcitrant: real fitness/cofit signal exists but evidence cannot pin down a specific function"
  echo ""
  echo "Use the dossier evidence — primary fitness, cofit partners, neighborhood, SwissProt, KEGG, SEED, domains, PaperBLAST hits + papers. Be honest about confidence."
  echo "proposed_annotation: new name for improvable_*; echo existing for already_correctly_named; null/empty for recalcitrant."
  echo "ec_number: include if known (e.g. \"3.5.1.2\"), else null."
  echo "papers_consulted: list of PMID strings from the dossier you actually used in reasoning; [] if none."
  echo ""
  echo "Output exactly $N_DOSSIERS JSONL lines, one per dossier, in the order presented. No code fences, no preamble, no trailing summary."
} > "$PROMPT_FILE"

RAW="$DIR/raw.txt"
MODEL="${CLAUDE_MODEL:-sonnet}"
claude -p --model "$MODEL" --no-session-persistence < "$PROMPT_FILE" > "$RAW" 2> "$LOG"

# Strip markdown code fences and any non-JSON lines.
# Keep only lines that look like JSONL ({...}).
grep -E '^[[:space:]]*\{.*\}[[:space:]]*$' "$RAW" > "$OUT" || true

echo "DONE $ID  ($(wc -l < "$OUT") JSONL lines)"
