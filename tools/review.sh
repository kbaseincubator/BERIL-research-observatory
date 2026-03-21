#!/usr/bin/env bash
# Usage: tools/review.sh <project_id> [--type project|plan] [--reviewer claude|codex] [--model <model_id>] [--output <path>]
#
# Invoke a CLI reviewer agent to review a BERDL analysis project or research plan.
# Supports Claude Code and Codex CLI as reviewer backends.

set -euo pipefail

# --- Defaults ---
REVIEWER="claude"
MODEL=""
PROJECT_ID=""
REVIEW_TYPE="project"
OUTPUT_FILE=""

CLAUDE_DEFAULT_MODEL="claude-sonnet-4-20250514"
CODEX_DEFAULT_MODEL="gpt-5.4"

# --- Usage ---
usage() {
  local exit_code="${1:-0}"
  cat <<EOF
Usage: tools/review.sh <project_id> [--type project|plan] [--reviewer claude|codex] [--model <model_id>] [--output <path>]

Arguments:
  project_id              Project directory name under projects/

Options:
  --type project|plan     Review type (default: project)
  --reviewer claude|codex Reviewer backend (default: claude)
  --model <model_id>      Model override (default: claude-sonnet-4-20250514 for claude, gpt-5.4 for codex)
  --output <path>         Output file path (default: auto-numbered REVIEW_N.md in project dir)
  --help                  Show this help message

Examples:
  tools/review.sh bacdive_metal_validation
  tools/review.sh bacdive_metal_validation --type plan
  tools/review.sh bacdive_metal_validation --type plan --reviewer codex
  tools/review.sh bacdive_metal_validation --reviewer codex --model gpt-5.4-mini
  tools/review.sh bacdive_metal_validation --output projects/bacdive_metal_validation/REVIEW.md
EOF
  exit "$exit_code"
}

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)
      [[ -z "${2:-}" ]] && { echo "Error: --type requires a value" >&2; usage 1; }
      REVIEW_TYPE="$2"
      shift 2
      ;;
    --reviewer)
      [[ -z "${2:-}" ]] && { echo "Error: --reviewer requires a value" >&2; usage 1; }
      REVIEWER="$2"
      shift 2
      ;;
    --model)
      [[ -z "${2:-}" ]] && { echo "Error: --model requires a value" >&2; usage 1; }
      MODEL="$2"
      shift 2
      ;;
    --output)
      [[ -z "${2:-}" ]] && { echo "Error: --output requires a value" >&2; usage 1; }
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --help)
      usage
      ;;
    -*)
      echo "Error: Unknown option $1" >&2
      usage 1
      ;;
    *)
      if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID="$1"
      else
        echo "Error: Unexpected argument $1" >&2
        usage 1
      fi
      shift
      ;;
  esac
done

# --- Validate inputs ---
if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: project_id is required" >&2
  usage 1
fi

if [[ "$REVIEW_TYPE" != "project" && "$REVIEW_TYPE" != "plan" ]]; then
  echo "Error: --type must be 'project' or 'plan', got '$REVIEW_TYPE'" >&2
  exit 1
fi

if [[ "$REVIEWER" != "claude" && "$REVIEWER" != "codex" ]]; then
  echo "Error: --reviewer must be 'claude' or 'codex', got '$REVIEWER'" >&2
  exit 1
fi

# Navigate to repo root (parent of tools/)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

PROJECT_DIR="projects/${PROJECT_ID}"
if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Error: Project directory '$PROJECT_DIR' does not exist" >&2
  exit 1
fi

# --- Resolve model ---
if [[ -z "$MODEL" ]]; then
  if [[ "$REVIEWER" == "claude" ]]; then
    MODEL="$CLAUDE_DEFAULT_MODEL"
  else
    MODEL="$CODEX_DEFAULT_MODEL"
  fi
fi

# --- Resolve output file ---
# If --output not provided, auto-number: REVIEW_1.md, REVIEW_2.md, etc.
if [[ -z "$OUTPUT_FILE" ]]; then
  if [[ "$REVIEW_TYPE" == "project" ]]; then
    PREFIX="REVIEW"
  else
    PREFIX="PLAN_REVIEW"
  fi

  # Find the next available number
  NEXT_N=1
  while [[ -f "${PROJECT_DIR}/${PREFIX}_${NEXT_N}.md" ]]; do
    NEXT_N=$(( NEXT_N + 1 ))
  done
  OUTPUT_FILE="${PROJECT_DIR}/${PREFIX}_${NEXT_N}.md"
fi

# --- Write placeholder to claim the output file (prevents race conditions) ---
echo "<!-- Review in progress by ${REVIEWER} (${MODEL}) — started $(date -u +%Y-%m-%dT%H:%M:%SZ) -->" > "$OUTPUT_FILE"

# --- Check CLI tool is installed ---
if ! command -v "$REVIEWER" &>/dev/null; then
  echo "Error: '$REVIEWER' CLI is not installed or not in PATH" >&2
  rm -f "$OUTPUT_FILE"
  exit 1
fi

# --- Select system prompt based on type ---
if [[ "$REVIEW_TYPE" == "project" ]]; then
  SYSTEM_PROMPT_FILE=".claude/reviewer/SYSTEM_PROMPT.md"
else
  SYSTEM_PROMPT_FILE=".claude/reviewer/PLAN_REVIEW_PROMPT.md"
fi

if [[ ! -f "$SYSTEM_PROMPT_FILE" ]]; then
  echo "Error: System prompt not found at $SYSTEM_PROMPT_FILE" >&2
  rm -f "$OUTPUT_FILE"
  exit 1
fi
SYSTEM_PROMPT="$(cat "$SYSTEM_PROMPT_FILE")"

# --- Build reviewer label for metadata ---
if [[ "$REVIEWER" == "claude" ]]; then
  REVIEWER_LABEL="Claude"
else
  REVIEWER_LABEL="Codex"
fi

# --- Build the review prompt based on type ---
if [[ "$REVIEW_TYPE" == "project" ]]; then
  REVIEW_PROMPT="Review the project at ${PROJECT_DIR}/. Read all files in the project directory — especially README.md, RESEARCH_PLAN.md, and REPORT.md. Also read docs/pitfalls.md for known issues. Write your review to ${OUTPUT_FILE}. In the Review Metadata section, set the Reviewer line to: **Reviewer**: BERIL Automated Review (${REVIEWER_LABEL}, ${MODEL}). In the YAML frontmatter, set reviewer to: BERIL Automated Review (${REVIEWER_LABEL}, ${MODEL})."
else
  REVIEW_PROMPT="Review the research plan at ${PROJECT_DIR}/. Read ${PROJECT_DIR}/RESEARCH_PLAN.md and ${PROJECT_DIR}/README.md. Also read docs/pitfalls.md, docs/performance.md, docs/collections.md, and PROJECT.md. Check docs/schemas/ for any tables referenced in the plan. Read README.md files of related existing projects to check for overlap. Write your plan review to ${OUTPUT_FILE}. At the end, note: Plan reviewed by ${REVIEWER_LABEL} (${MODEL})."
fi

# --- Invoke reviewer ---
echo "Invoking ${REVIEWER_LABEL} ${REVIEW_TYPE} reviewer (model: ${MODEL}) for project '${PROJECT_ID}'..."
echo "Output: ${OUTPUT_FILE}"

REVIEW_EXIT=0
REVIEW_STDERR=""
if [[ "$REVIEWER" == "claude" ]]; then
  CLAUDECODE= claude -p \
    --model "$MODEL" \
    --system-prompt "$SYSTEM_PROMPT" \
    --allowedTools "Read,Write" \
    --dangerously-skip-permissions \
    "$REVIEW_PROMPT" || REVIEW_EXIT=$?
else
  # Codex has no --system-prompt flag; prepend system prompt to user prompt
  FULL_PROMPT="${SYSTEM_PROMPT}

---

${REVIEW_PROMPT}"

  REVIEW_STDERR=$(codex exec \
    --model "$MODEL" \
    --sandbox workspace-write \
    --ephemeral \
    "$FULL_PROMPT" 2>&1) || REVIEW_EXIT=$?

  # --- Friendly codex error messages ---
  if [[ $REVIEW_EXIT -ne 0 && -n "$REVIEW_STDERR" ]]; then
    if echo "$REVIEW_STDERR" | grep -qi "sign in again\|refresh token\|token.*expired\|401 Unauthorized"; then
      echo "Error: Codex authentication expired. Run 'codex login' to re-authenticate." >&2
      rm -f "$OUTPUT_FILE"
      exit 1
    elif echo "$REVIEW_STDERR" | grep -qi "not supported when using Codex with a ChatGPT account"; then
      echo "Error: Model '${MODEL}' is not available with your Codex account. Try a different model or check 'codex' for available models." >&2
      rm -f "$OUTPUT_FILE"
      exit 1
    fi
  fi
fi

# --- Post-run validation ---
if [[ $REVIEW_EXIT -ne 0 ]]; then
  echo "Error: Reviewer exited with code $REVIEW_EXIT" >&2
  [[ -n "$REVIEW_STDERR" ]] && echo "$REVIEW_STDERR" >&2
  rm -f "$OUTPUT_FILE"
  exit $REVIEW_EXIT
fi

# Check output file has real content (not just the placeholder)
if [[ ! -s "$OUTPUT_FILE" ]] || ! grep -q '^---' "$OUTPUT_FILE" 2>/dev/null; then
  # Check if it's still just the placeholder
  if grep -q '<!-- Review in progress' "$OUTPUT_FILE" 2>/dev/null && [[ $(wc -l < "$OUTPUT_FILE") -le 1 ]]; then
    echo "Error: Reviewer did not write to the output file: $OUTPUT_FILE" >&2
  else
    echo "Error: Review output is empty or missing: $OUTPUT_FILE" >&2
  fi
  rm -f "$OUTPUT_FILE"
  exit 1
fi

echo "Review written to: $OUTPUT_FILE"
