#!/bin/bash
# Ensure OpenViking server is running. Called by Claude Code hook.
# Exits silently if healthy; starts server in background if not.

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HEALTH_URL="http://127.0.0.1:1933/health"
HOOK_PID_FILE="$REPO_ROOT/data/.openviking-hook.pid"
LOG_FILE="$REPO_ROOT/data/.openviking.log"

# Fast path: server already healthy
if curl -sf --max-time 1 "$HEALTH_URL" > /dev/null 2>&1; then
  exit 0
fi

# Check if another instance is already starting
if [ -f "$HOOK_PID_FILE" ] && kill -0 "$(cat "$HOOK_PID_FILE")" 2>/dev/null; then
  # Process exists but health check failed — still starting up
  exit 0
fi

# Clean stale OpenViking lock file if the owning process is dead
OV_LOCK="$REPO_ROOT/data/.openviking.pid"
if [ -f "$OV_LOCK" ]; then
  STALE_PID=$(cat "$OV_LOCK" 2>/dev/null)
  if [ -n "$STALE_PID" ] && ! kill -0 "$STALE_PID" 2>/dev/null; then
    rm -f "$OV_LOCK"
  fi
fi

# Start the server
cd "$REPO_ROOT" || exit 1

CONFIG_FILE="$REPO_ROOT/config/openviking/ov.conf"
if [ -f "$CONFIG_FILE" ]; then
  export OPENVIKING_CONFIG_FILE="$CONFIG_FILE"
fi

nohup uv run openviking-server --config "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
echo $! > "$HOOK_PID_FILE"

# Wait briefly for startup
for i in 1 2 3 4 5; do
  sleep 1
  if curl -sf --max-time 1 "$HEALTH_URL" > /dev/null 2>&1; then
    echo '{"systemMessage": "OpenViking server started automatically."}'
    exit 0
  fi
done

echo '{"systemMessage": "OpenViking server is starting (may take a few more seconds)..."}'
exit 0
