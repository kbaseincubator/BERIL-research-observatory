#!/bin/bash
set -eo pipefail

# Monitor all submitted Bakta CTS jobs
# Reads job_manifest.json and reports status of all jobs
#
# Usage: bash monitor_jobs.sh [--watch]
#   --watch: poll every 5 min until all jobs complete

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
JOB_MANIFEST="$SCRIPT_DIR/../job_manifest.json"

AUTH_TOKEN=$(grep "KBASE_AUTH_TOKEN" "$REPO_DIR/.env" | cut -d'"' -f2)

if [ ! -f "$JOB_MANIFEST" ]; then
    echo "ERROR: job_manifest.json not found. Run submit_all_chunks.sh first."
    exit 1
fi

WATCH=false
if [ "${1:-}" = "--watch" ]; then
    WATCH=true
fi

check_status() {
    python3 << PYEOF
import json, sys, os
import urllib.request

token = "$AUTH_TOKEN"
manifest = json.load(open("$JOB_MANIFEST"))
jobs = manifest["jobs"]

states = {}
for job in jobs:
    jid = job["job_id"]
    chunk = job["chunk"]
    try:
        req = urllib.request.Request(
            f"https://berdl.kbase.us/apis/cts/jobs/{jid}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        state = data["state"]
    except Exception as e:
        state = f"unknown ({e})"

    states.setdefault(state, []).append(chunk)

print(f"{'='*60}")
print(f"  Job Status Summary — {len(jobs)} jobs")
print(f"{'='*60}")
for state in sorted(states.keys()):
    chunks = states[state]
    print(f"  {state:30s}: {len(chunks):>4}")
    if len(chunks) <= 5:
        for c in chunks:
            print(f"    - {c}")

total = len(jobs)
complete = len(states.get("complete", []))
error = len(states.get("error", []))
running = total - complete - error
print(f"{'='*60}")
print(f"  Complete: {complete}/{total}  Error: {error}  Pending/Running: {running}")
print(f"{'='*60}")

# Return exit code 0 if all done, 1 if still running
if complete + error == total:
    sys.exit(0)
else:
    sys.exit(1)
PYEOF
}

if [ "$WATCH" = true ]; then
    while true; do
        echo ""
        echo "$(date -u)"
        check_status && break
        sleep 300
    done
    echo ""
    echo "All jobs reached terminal state."
else
    check_status
fi
