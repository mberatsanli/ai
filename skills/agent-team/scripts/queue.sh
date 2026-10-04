#!/bin/sh
# usage: queue.sh <pr>... — merges each PR in turn through the merge gate, never any other way.
# Runs "$GATE <pr> --update": merges main in, waits for CI, then merges. With local CI on
# (mergeGate.localCiOnUpdate in agent-team.json, or AGENT_TEAM_LOCAL_CI=1), the gate runs $LOCAL_CI
# on the head itself instead of waiting for GitHub Actions.
# Pulls main after each merge. Stops at the first PR that doesn't merge.
# RERUN=1 uses --update --rerun: local CI runs again even on a head that has results (the one flaky retry).
. "$(dirname "$0")/env.sh"
MODE=--update; [ "${RERUN:-0}" = 1 ] && MODE="--update --rerun"
for P in "$@"; do
  echo "=== #$P"
  OUT=$(MERGE_GATE_LOCAL_CI="$LOCAL_CI" $GATE "$P" $MODE 2>&1); echo "$OUT" | tail -8
  if echo "$OUT" | grep -qi "conflict"; then echo "STOP at #$P: conflicts with main"; exit 1; fi
  gh pr view "$P" --json state -q .state | grep -q MERGED || { echo "STOP at #$P"; exit 1; }
  git pull -q; echo "merged #$P -> $(git log --oneline -1)"
done
