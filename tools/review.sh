#!/usr/bin/env bash
# Usage: tools/review.sh <project_id> [--reviewer claude|codex] [--model <model_id>]
#
# Invoke a CLI reviewer agent to review a BERDL analysis project.
# Supports Claude Code and Codex CLI as reviewer backends.

set -euo pipefail

# --- Defaults ---
REVIEWER="claude"
MODEL=""
PROJECT_ID=""

CLAUDE_DEFAULT_MODEL="claude-sonnet-4-20250514"
CODEX_DEFAULT_MODEL="o3"

# --- Usage ---
usage() {
  local exit_code="${1:-0}"
  cat <<EOF
Usage: tools/review.sh <project_id> [--reviewer claude|codex] [--model <model_id>]

Arguments:
  project_id              Project directory name under projects/

Options:
  --reviewer claude|codex Reviewer backend (default: claude)
  --model <model_id>      Model override (default: claude-sonnet-4-20250514 for claude, o3 for codex)
  --help                  Show this help message

Examples:
  tools/review.sh bacdive_metal_validation
  tools/review.sh bacdive_metal_validation --reviewer codex
  tools/review.sh bacdive_metal_validation --reviewer claude --model claude-haiku-4-5-20251001
  tools/review.sh bacdive_metal_validation --reviewer codex --model gpt-4o-mini
EOF
  exit "$exit_code"
}

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --reviewer)
      REVIEWER="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
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

# --- Check CLI tool is installed ---
if ! command -v "$REVIEWER" &>/dev/null; then
  echo "Error: '$REVIEWER' CLI is not installed or not in PATH" >&2
  exit 1
fi

# --- Read system prompt ---
SYSTEM_PROMPT_FILE=".claude/reviewer/SYSTEM_PROMPT.md"
if [[ ! -f "$SYSTEM_PROMPT_FILE" ]]; then
  echo "Error: System prompt not found at $SYSTEM_PROMPT_FILE" >&2
  exit 1
fi
SYSTEM_PROMPT="$(cat "$SYSTEM_PROMPT_FILE")"

# --- Build reviewer label for metadata ---
if [[ "$REVIEWER" == "claude" ]]; then
  REVIEWER_LABEL="Claude"
else
  REVIEWER_LABEL="Codex"
fi

REVIEW_PROMPT="Review the project at ${PROJECT_DIR}/. Read all files in the project directory — especially README.md, RESEARCH_PLAN.md, and REPORT.md. Also read docs/pitfalls.md for known issues. Write your review to ${PROJECT_DIR}/REVIEW.md. In the Review Metadata section, set the Reviewer line to: **Reviewer**: BERIL Automated Review (${REVIEWER_LABEL}, ${MODEL}). In the YAML frontmatter, set reviewer to: BERIL Automated Review (${REVIEWER_LABEL}, ${MODEL})."

# --- Invoke reviewer ---
echo "Invoking ${REVIEWER_LABEL} reviewer (model: ${MODEL}) for project '${PROJECT_ID}'..."

if [[ "$REVIEWER" == "claude" ]]; then
  CLAUDECODE= claude -p \
    --model "$MODEL" \
    --system-prompt "$SYSTEM_PROMPT" \
    --allowedTools "Read,Write" \
    --dangerously-skip-permissions \
    "$REVIEW_PROMPT"
else
  # Codex has no --system-prompt flag; prepend system prompt to user prompt
  FULL_PROMPT="${SYSTEM_PROMPT}

---

${REVIEW_PROMPT}"

  codex exec \
    --model "$MODEL" \
    --sandbox read-only \
    --ephemeral \
    -o "${PROJECT_DIR}/REVIEW.md" \
    "$FULL_PROMPT"
fi
