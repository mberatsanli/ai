#!/bin/sh
# usage: queue.sh <pr>... — merges each PR in turn through the merge gate, never any other way.
# First "$GATE <pr> --update" (merges main in, waits for CI, merges). If the gate refuses an
# already-current branch and $LOCAL_CI exists, runs local CI on the head and asks the gate again.
# Pulls main after each merge. Stops at the first PR that doesn't merge.
. "$(dirname "$0")/env.sh"
for P in "$@"; do
  echo "=== #$P"
  OUT=$(env $GATE_ENV $GATE "$P" --update 2>&1); echo "$OUT" | tail -8
  if echo "$OUT" | grep -qi "conflict"; then echo "STOP at #$P: conflicts with main"; exit 1; fi
  if ! gh pr view "$P" --json state -q .state | grep -q MERGED && [ -x "$LOCAL_CI" ] && ! echo "$OUT" | grep -q "Running CI"; then
    echo "--- running local CI"
    $LOCAL_CI "$P" 2>&1 | tail -6; env $GATE_ENV $GATE "$P" 2>&1 | tail -4
  fi
  gh pr view "$P" --json state -q .state | grep -q MERGED || { echo "STOP at #$P"; exit 1; }
  git pull -q; echo "merged #$P -> $(git log --oneline -1)"
done
