#!/usr/bin/env bash
# chromium-cdp-service.sh — pm2 wrapper for Chromium with CDP remote debugging
# Crostini: requires DISPLAY=:0 (headless broken on this setup)

set -euo pipefail

PORT=9222
USER_DATA_DIR="$HOME/.config/chromium-cdp"
PORT_FILE="$USER_DATA_DIR/DevToolsActivePort"
LOG_PREFIX="[chromium-cdp]"

mkdir -p "$USER_DATA_DIR"

# Kill any stale Chromium on this port before starting
pkill -f "remote-debugging-port=$PORT" 2>/dev/null || true
sleep 1

echo "$LOG_PREFIX Starting Chromium on port $PORT..."

DISPLAY=:0 /usr/bin/chromium \
  --remote-debugging-port=$PORT \
  --no-first-run \
  --no-default-browser-check \
  --disable-background-networking \
  --disable-sync \
  --disable-extensions \
  --disable-default-apps \
  --disable-translate \
  --disable-web-security=false \
  --user-data-dir="$USER_DATA_DIR" \
  about:blank &

CHROME_PID=$!
echo "$LOG_PREFIX PID=$CHROME_PID"

# Wait for CDP endpoint to respond (max 30s)
for i in $(seq 1 30); do
  WS_URL=$(curl -sf "http://127.0.0.1:$PORT/json/version" 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('webSocketDebuggerUrl',''))" 2>/dev/null || true)

  if [ -n "$WS_URL" ]; then
    PATH_PART="${WS_URL#ws://127.0.0.1:$PORT}"
    printf '%s\n%s\n' "$PORT" "$PATH_PART" > "$PORT_FILE"
    echo "$LOG_PREFIX DevTools ready: $WS_URL"
    echo "$LOG_PREFIX DevToolsActivePort written to $PORT_FILE"
    break
  fi

  echo "$LOG_PREFIX Waiting for CDP... ($i/30)"
  sleep 1
done

if [ ! -f "$PORT_FILE" ]; then
  echo "$LOG_PREFIX ERROR: CDP never became available after 30s"
  kill $CHROME_PID 2>/dev/null || true
  exit 1
fi

# Stay alive as long as Chromium runs (pm2 tracks this PID)
wait $CHROME_PID
EXIT_CODE=$?
rm -f "$PORT_FILE"
echo "$LOG_PREFIX Chromium exited with code $EXIT_CODE"
exit $EXIT_CODE
