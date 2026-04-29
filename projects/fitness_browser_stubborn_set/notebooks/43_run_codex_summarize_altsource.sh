#!/bin/bash
# Codex-summarize from alt-source text (Europe PMC full text or any abstract).
# Schema is the same 4-col TSV.
# Usage: 43_run_codex_summarize_altsource.sh <pmid>
set -e
PMID="$1"
if [ -z "$PMID" ]; then echo "Usage: $0 <pmid>"; exit 1; fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SUM_DIR="${SUM_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_summaries_altsource}"
PER_PAPER_DIR="$SUM_DIR/per_paper"
TEXT_DIR="$SUM_DIR/text"
mkdir -p "$PER_PAPER_DIR"

OUT_TSV="$PER_PAPER_DIR/${PMID}.tsv"
LOG="$PER_PAPER_DIR/${PMID}.log"
TEXT="$TEXT_DIR/${PMID}.txt"

if [ -f "$OUT_TSV" ] && [ -s "$OUT_TSV" ]; then
  echo "SKIP $PMID"; exit 0
fi
if [ ! -f "$TEXT" ] || [ ! -s "$TEXT" ]; then
  echo "NOTEXT $PMID"; : > "$OUT_TSV"; exit 0
fi

GENE_LIST=$(python3 -c "
import json
pmid = '$PMID'
with open('$SUM_DIR/tasks.jsonl') as fh:
    for line in fh:
        r = json.loads(line)
        if str(r['pmId']) == pmid:
            for g in r['gene_identifiers']:
                print(f\"{g['geneId']}\t{g.get('pb_organism','')}\t{g.get('pb_desc','')}\")
            break
")
if [ -z "$GENE_LIST" ]; then
  echo "NOGENES $PMID"; : > "$OUT_TSV"; exit 0
fi

PROMPT_FILE="$PER_PAPER_DIR/${PMID}.prompt.txt"
{
  echo "You are an expert microbial gene curator."
  echo ""
  echo "TASK: Read the article text below and write a per-gene summary for each of the following gene identifiers. Focus on experimental evidence, gene function, gene products, mutational/fitness impacts, and anything else useful for describing function. The text may be a full article, just the abstract, or a structured summary — work with what's available. If the text adds nothing of value about a particular gene, output 'null'."
  echo ""
  echo "Gene identifiers to summarize (tab-separated: geneId, organism, paperblast_description):"
  echo "$GENE_LIST"
  echo ""
  echo "OUTPUT FORMAT — one TSV row per gene_identifier above, no preamble or commentary:"
  echo "manuscript_id<TAB>source_type<TAB>gene_identifier<TAB>summary"
  echo ""
  echo "Where manuscript_id = '$PMID', source_type = 'altsource' (we'll record the actual source separately), gene_identifier = the geneId, and summary = your gene-specific summary or 'null'."
  echo ""
  echo "=== ARTICLE TEXT ==="
  cat "$TEXT"
} > "$PROMPT_FILE"

CODEX_WORKDIR="${CODEX_WORKDIR:-/tmp/codex_summarize_workdir}"
mkdir -p "$CODEX_WORKDIR"

(cd "$CODEX_WORKDIR" && "${CODEX_BIN:-codex}" exec \
  --model gpt-5.5 \
  --sandbox workspace-write \
  --ephemeral \
  --skip-git-repo-check \
  --output-last-message "$OUT_TSV" \
  < "$PROMPT_FILE" > "$LOG" 2>&1) &
CPID=$!

TIMEOUT_S="${CODEX_TIMEOUT:-600}"
WAITED=0
while kill -0 $CPID 2>/dev/null; do
  if [ $WAITED -ge $TIMEOUT_S ]; then kill -9 $CPID 2>/dev/null; break; fi
  sleep 5
  WAITED=$((WAITED + 5))
done
wait $CPID 2>/dev/null

if [ -s "$OUT_TSV" ]; then
  echo "DONE $PMID"
else
  echo "FAILED $PMID" >&2; exit 1
fi
