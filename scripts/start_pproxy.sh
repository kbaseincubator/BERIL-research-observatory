#!/usr/bin/env bash
# Start pproxy HTTP-to-SOCKS5 bridge on port 8123
# This bridges HTTP requests (used by Spark Connect and MinIO) to the SSH SOCKS5 tunnel on port 1338.
# Prerequisites: SSH tunnels on ports 1337 and 1338 must be running.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PATH="${REPO_ROOT}/.venv-berdl"

if [[ ! -d "${VENV_PATH}" ]]; then
  echo "Error: .venv-berdl not found. Run: bash scripts/bootstrap_client.sh" >&2
  exit 1
fi

# Check if SSH tunnel on 1338 is up
if ! lsof -i :1338 2>/dev/null | grep -q LISTEN; then
  echo "Warning: SSH tunnel on port 1338 not detected." >&2
  echo "Start it with: ssh -f -N -o ServerAliveInterval=60 -D 1338 ac.<username>@login1.berkeley.kbase.us" >&2
  echo "Continuing anyway..." >&2
fi

# Check if pproxy is already running
if lsof -i :8123 2>/dev/null | grep -q LISTEN; then
  echo "pproxy is already running on port 8123." >&2
  exit 0
fi

echo "Starting pproxy on port 8123..."
echo "Routes HTTP → SOCKS5 (127.0.0.1:1338)"
echo "Press Ctrl+C to stop."
echo ""

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

python -c "
import sys, asyncio
sys.argv = ['pproxy', '-l', 'http://:8123', '-r', 'socks5://127.0.0.1:1338', '-v']
asyncio.set_event_loop(asyncio.new_event_loop())
from pproxy.server import main
main()
"
