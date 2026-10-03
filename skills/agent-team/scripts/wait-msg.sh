#!/bin/sh
# usage: wait-msg.sh — blocks until a worker sends something other than a heartbeat, prints it.
# Heartbeats are acked on the way. Run it in the background; only one waiter may exist at a time.
# Ack the printed delivery yourself after reading it: orca orchestration check --run $ORCA_RUN --ack <deliveryId>
. "$(dirname "$0")/env.sh"
while :; do
  O=$(orca orchestration check --run "$ORCA_RUN" --wait --json 2>&1 | grep -v _keepalive)
  R=$(echo "$O" | python3 -c "
import json,sys
try: d=json.loads(sys.stdin.read(),strict=False)['result']
except Exception: print('ERR'); sys.exit()
m=d.get('messages') or []
if not m: print('NONE'); sys.exit()
if all(x.get('type')=='heartbeat' for x in m): print('HB', d.get('deliveryId')); sys.exit()
print('MSG', d.get('deliveryId'))")
  case "$R" in
    HB*) orca orchestration check --run "$ORCA_RUN" --ack "${R#HB }" --json >/dev/null 2>&1 ;;
    MSG*) echo "$O" | grep -E '"deliveryId"|"id": "msg|"subject"|"body"|"type"|"payload"'; exit 0 ;;
    ERR) echo "$O" | head -20; sleep 30 ;;
  esac
done
