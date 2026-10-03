#!/usr/bin/env bash
# The `dev-smoke` CI job: runs the README's "Run it locally" steps from a fresh clone and checks the app
# answers, so a PR that breaks local development can't merge. It picks its own free port, so dev servers
# that agents keep running don't get in the way.
# Set DEV_COMMAND (how the README starts the app; it must read PORT) and HEALTH_PATH, or edit the
# defaults below.
set -euo pipefail

readonly dev_command=${DEV_COMMAND:-"npm run dev"}
readonly health_path=${HEALTH_PATH:-"/"}
readonly start_timeout_seconds=${DEV_SMOKE_TIMEOUT_SECONDS:-180}

port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
log=$(mktemp)

PORT=$port bash -c "$dev_command" >"$log" 2>&1 &
readonly dev_pid=$!
# Stop the whole process group the dev command started, not just its shell.
trap 'kill -- -"$dev_pid" 2>/dev/null || kill "$dev_pid" 2>/dev/null || true' EXIT

for ((waited = 0; waited < start_timeout_seconds; waited++)); do
  if curl --silent --fail "http://127.0.0.1:${port}${health_path}" >/dev/null; then
    echo "dev-smoke: the app answers on :${port}${health_path} after ${waited}s"
    exit 0
  fi
  if ! kill -0 "$dev_pid" 2>/dev/null; then
    echo "::error::the dev command exited before the app answered. Its output:"
    cat "$log"
    exit 1
  fi
  sleep 1
done

echo "::error::the app didn't answer on :${port}${health_path} within ${start_timeout_seconds}s. Its output:"
cat "$log"
exit 1
