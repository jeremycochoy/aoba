#!/usr/bin/env bash
# Launch a dedicated Chrome instance for the Matchaé marketing bot, with CDP enabled on :9336.
set -euo pipefail
PORT="${1:-9336}"
PROFILE_DIR="${HOME}/.matchae-bot/chrome-profile"
mkdir -p "$PROFILE_DIR"

# don't re-launch if already running on that port
if curl -sf "http://localhost:${PORT}/json/version" >/dev/null 2>&1; then
  echo "Chrome already running on :${PORT}"
  exit 0
fi

open -na "Google Chrome" --args \
  --user-data-dir="$PROFILE_DIR" \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins=* \
  --no-first-run \
  --no-default-browser-check \
  --disable-backgrounding-occluded-windows \
  --window-size=1400,1000 \
  --window-position=160,120 \
  about:blank

# wait for CDP to come up
for i in $(seq 1 30); do
  if curl -sf "http://localhost:${PORT}/json/version" >/dev/null 2>&1; then
    echo "Chrome up on :${PORT}"
    exit 0
  fi
  sleep 0.5
done
echo "Chrome did not come up on :${PORT}" >&2
exit 1
