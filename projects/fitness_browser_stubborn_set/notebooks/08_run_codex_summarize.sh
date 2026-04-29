#!/bin/bash
# Run Codex (gpt-5.4pro) to summarize one PMC paper for one or more gene_identifiers.
# Usage: 08_run_codex_summarize.sh <pmid>
# Reads:
#   data/codex_summaries/tasks.jsonl   — to find gene_identifiers for this pmId
#   data/codex_summaries/pmc_index.tsv — to find pmcId
#   data/codex_summaries/pmc/<pmcid>.xml
# Writes:
#   data/codex_summaries/per_paper/<pmid>.tsv (4-col: manuscript_id\tsource_type\tgene_identifier\tsummary)
#   data/codex_summaries/per_paper/<pmid>.log
set -e
PMID="$1"
if [ -z "$PMID" ]; then echo "Usage: $0 <pmid>"; exit 1; fi

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SUM_DIR="${SUM_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_summaries}"
PMC_DIR="${PMC_DIR:-$REPO_ROOT/projects/fitness_browser_stubborn_set/data/codex_summaries/pmc}"
PER_PAPER_DIR="$SUM_DIR/per_paper"
mkdir -p "$PER_PAPER_DIR"

OUT_TSV="$PER_PAPER_DIR/${PMID}.tsv"
LOG="$PER_PAPER_DIR/${PMID}.log"

# Skip if already done
if [ -f "$OUT_TSV" ] && [ -s "$OUT_TSV" ]; then
  echo "SKIP $PMID (already summarized)"
  exit 0
fi

# Look up pmcId
PMCID=$(awk -F'\t' -v p="$PMID" '$1==p {print $2}' "$SUM_DIR/pmc_index.tsv" | head -1)
if [ -z "$PMCID" ]; then
  echo "NOPMC $PMID"
  : > "$OUT_TSV"  # empty TSV = no PMC available
  exit 0
fi

XML="$PMC_DIR/${PMCID}.xml"
if [ ! -f "$XML" ]; then
  echo "NOXML $PMID ($PMCID)"
  : > "$OUT_TSV"
  exit 0
fi

# Look up gene_identifiers for this paper from tasks.jsonl
GENE_LIST=$(python3 -c "
import json, sys
pmid = '$PMID'
with open('$SUM_DIR/tasks.jsonl') as fh:
    for line in fh:
        r = json.loads(line)
        if str(r['pmId']) == pmid:
            for g in r['gene_identifiers']:
                print(f\"{g['geneId']}\t{g.get('pb_organism','')}\t{g.get('pb_desc','')}\")
            break
" )

if [ -z "$GENE_LIST" ]; then
  echo "NOGENES $PMID"
  : > "$OUT_TSV"
  exit 0
fi

# Build prompt
PROMPT_FILE="$PER_PAPER_DIR/${PMID}.prompt.txt"
{
  echo "You are an expert microbial gene curator."
  echo ""
  echo "TASK: Read the manuscript below (PMC XML) and write a per-gene summary for each of the following gene identifiers. Focus on experimental evidence, gene function, gene products, mutational/fitness impacts, and anything else useful for describing function. If the manuscript adds nothing of value about a particular gene, output 'null' for that gene's summary."
  echo ""
  echo "Gene identifiers to summarize (tab-separated: geneId, organism, paperblast_description):"
  echo "$GENE_LIST"
  echo ""
  echo "OUTPUT FORMAT — output exactly one TSV row per gene_identifier above, no preamble or commentary, columns separated by literal tab characters:"
  echo "manuscript_id<TAB>source_type<TAB>gene_identifier<TAB>summary"
  echo ""
  echo "Where manuscript_id = '$PMID', source_type = 'pubmed', gene_identifier = the geneId from the input list, and summary = your gene-specific summary (one paragraph, ~3–6 sentences) or the literal string 'null' if the manuscript is not relevant to this gene's function. Do NOT print any header line. Do NOT include extra fields."
  echo ""
  echo "=== MANUSCRIPT (PMC XML) ==="
  cat "$XML"
} > "$PROMPT_FILE"

# Run codex from an EMPTY working directory so its workspace-write sandbox
# has nothing to grep/explore. Without this, codex spends minutes traversing
# the project tree instead of summarizing the paper.
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

# Poll for completion or timeout. No backgrounded sleep => no orphan sleeps.
TIMEOUT_S="${CODEX_TIMEOUT:-900}"
WAITED=0
while kill -0 $CPID 2>/dev/null; do
  if [ $WAITED -ge $TIMEOUT_S ]; then
    kill -9 $CPID 2>/dev/null
    break
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
