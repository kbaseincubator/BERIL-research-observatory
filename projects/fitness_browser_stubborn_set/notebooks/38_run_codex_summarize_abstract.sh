#!/bin/bash
# Run codex to summarize a paper from its PubMed abstract (used when full
# PMC text is unavailable). Same per-(homolog, paper) output schema as
# 08_run_codex_summarize.sh.
#
# Usage: 38_run_codex_summarize_abstract.sh <pmid>
# Reads:
#   $SUM_DIR/tasks.jsonl                  — gene_identifiers per pmId
#   $SUM_DIR/abstracts/<pmid>.txt         — PubMed abstract plain text
#   $SUM_DIR/abstract_index.tsv           — pmId, has_abstract flag
# Writes:
#   $SUM_DIR/per_paper/<pmid>.tsv         — same 4-col TSV
#   $SUM_DIR/per_paper/<pmid>.log         — codex stderr
set -e
PMID="$1"
if [ -z "$PMID" ]; then echo "Usage: $0 <pmid>"; exit 1; fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SUM_DIR="${SUM_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_summaries_abstracts}"
PER_PAPER_DIR="$SUM_DIR/per_paper"
ABSTRACT_DIR="$SUM_DIR/abstracts"
mkdir -p "$PER_PAPER_DIR"

OUT_TSV="$PER_PAPER_DIR/${PMID}.tsv"
LOG="$PER_PAPER_DIR/${PMID}.log"

if [ -f "$OUT_TSV" ] && [ -s "$OUT_TSV" ]; then
  echo "SKIP $PMID (already summarized)"; exit 0
fi

ABSTRACT="$ABSTRACT_DIR/${PMID}.txt"
if [ ! -f "$ABSTRACT" ] || [ ! -s "$ABSTRACT" ]; then
  echo "NOABSTRACT $PMID"; : > "$OUT_TSV"; exit 0
fi

# Look up gene_identifiers for this paper from tasks.jsonl
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

# Build prompt
PROMPT_FILE="$PER_PAPER_DIR/${PMID}.prompt.txt"
{
  echo "You are an expert microbial gene curator."
  echo ""
  echo "TASK: Read the PubMed abstract below and write a per-gene summary for each of the following gene identifiers. Focus on experimental evidence, gene function, gene products, mutational/fitness impacts, and anything else useful for describing function. The abstract is short — if the abstract adds nothing of value about a particular gene, output 'null' for that gene's summary."
  echo ""
  echo "Gene identifiers to summarize (tab-separated: geneId, organism, paperblast_description):"
  echo "$GENE_LIST"
  echo ""
  echo "OUTPUT FORMAT — output exactly one TSV row per gene_identifier above, no preamble or commentary, columns separated by literal tab characters:"
  echo "manuscript_id<TAB>source_type<TAB>gene_identifier<TAB>summary"
  echo ""
  echo "Where manuscript_id = '$PMID', source_type = 'pubmed_abstract', gene_identifier = the geneId from the input list, and summary = your gene-specific summary (one paragraph, ~2-4 sentences) or the literal string 'null' if the abstract is not relevant. Do NOT print any header line."
  echo ""
  echo "=== PUBMED ABSTRACT ==="
  cat "$ABSTRACT"
} > "$PROMPT_FILE"

# Run codex from isolated workdir (no workspace exploration)
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
  if [ $WAITED -ge $TIMEOUT_S ]; then
    kill -9 $CPID 2>/dev/null; break
  fi
  sleep 5
  WAITED=$((WAITED + 5))
done
wait $CPID 2>/dev/null

if [ -s "$OUT_TSV" ]; then
  echo "DONE $PMID"
else
  echo "FAILED $PMID" >&2
  exit 1
fi
