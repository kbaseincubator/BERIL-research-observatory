#!/usr/bin/env bash
# Static checks for the BERDL skill hardening change.
# Exit non-zero on any violation.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

fail=0

echo "=== 1. No hardcoded BERDL row counts in skills/docs ==="
if grep -rEn "293,?059|1B genes|420M|671M|27,?690|1B rows" \
       .claude/skills/ docs/overview.md docs/research_ideas.md PROJECT.md 2>/dev/null \
       | grep -v "docs/pitfalls.md" \
       | grep -v "modules/query-patterns.md\|modules/cross-database.md"; then
  echo "VIOLATION: hardcoded row counts found above"
  fail=1
fi

echo "=== 2. No get_databases/get_tables/get_table_schema without return_json=False ==="
if grep -rn "berdl_notebook_utils\..*get_\(databases\|tables\|table_schema\)(" \
       .claude/skills/ 2>/dev/null \
       | grep -v "return_json=False"; then
  echo "VIOLATION: helper calls missing return_json=False"
  fail=1
fi

echo "=== 3. No hallucinated script paths ==="
known_scripts="berdl_env detect_berdl_environment run_sql export_sql get_minio_creds configure_mc get_spark_session bootstrap_client bootstrap_ingest ingest_lib ingest_preflight start_pproxy discover_berdl_collections build_data_cache"
if grep -rEn "scripts/[a-z_]+\.(py|sh)" .claude/skills/ 2>/dev/null \
       | grep -oE "scripts/[a-z_]+\.(py|sh)" \
       | sort -u \
       | while read path; do
            base="$(basename "$path" .py)"; base="${base%.sh}"
            if ! echo "$known_scripts" | grep -qw "$base"; then
              echo "  invented path: $path"
              exit 1
            fi
         done; then
  :  # all good
else
  echo "VIOLATION: invented script paths found"
  fail=1
fi

echo "=== 4. No off-cluster mechanics in general docs ==="
if grep -nE "https_proxy=http|--berdl-proxy|ssh -f -N -D|\.venv-berdl/bin/activate" \
       docs/pitfalls.md docs/performance.md docs/overview.md docs/research_ideas.md PROJECT.md 2>/dev/null \
       | grep -v "see .claude/skills/berdl-"; then
  echo "VIOLATION: off-cluster mechanics in general docs (only 'see ...' pointers allowed)"
  fail=1
fi

echo "=== 5. docs/schemas/ deleted ==="
if [ -d docs/schemas ]; then
  echo "VIOLATION: docs/schemas/ still exists"
  fail=1
fi

echo "=== 6. Deleted module files are gone ==="
for f in pangenome.md biochemistry.md paperblast.md; do
  if [ -f ".claude/skills/berdl/modules/$f" ]; then
    echo "VIOLATION: .claude/skills/berdl/modules/$f still exists"
    fail=1
  fi
done

echo "=== 7. Step 0 block present in every BERDL skill ==="
for skill in berdl_start berdl berdl-query berdl-minio berdl-discover berdl-ingest berdl-ingest-remote; do
  if ! grep -q "scripts/berdl_env.py" ".claude/skills/$skill/SKILL.md"; then
    echo "VIOLATION: $skill/SKILL.md does not reference scripts/berdl_env.py"
    fail=1
  fi
done

if [ $fail -eq 0 ]; then
  echo
  echo "All static checks passed."
fi
exit $fail
