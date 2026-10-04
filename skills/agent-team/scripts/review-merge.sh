#!/bin/sh
# usage: review-merge.sh <pr> <issue> <worktree> [round] [-- <start-worker.sh args>]
# The loop's middle step in one go: starts the Reviewer, waits for its verdict, and on
# REVIEW: APPROVED merges the PR through queue.sh, removes the reviewer and the author's worktree,
# then starts the next worker (if given after --) and waits for its first real message.
# Stops and prints the message on anything else (CHANGES_REQUESTED, a question, a failed merge).
# After answering a reviewer's question, run it again with RESUME=1: it skips starting the reviewer.
. "$(dirname "$0")/env.sh"
S=$(dirname "$0")
PR=$1; N=$2; WT=$3; shift 3
ROUND=""; if [ $# -gt 0 ] && [ "$1" != "--" ]; then ROUND=$1; shift; fi
[ "${1:-}" = "--" ] && shift

if [ "${RESUME:-0}" != 1 ]; then sh "$S/wait-load.sh" && sh "$S/start-review.sh" "$PR" "$N" $ROUND || exit 1; fi
OUT=$(sh "$S/wait-msg.sh"); echo "$OUT"
DELIVERY=$(echo "$OUT" | grep -oE '"deliveryId": "[^"]+"' | head -1 | cut -d'"' -f4)
DISPATCH=$(echo "$OUT" | grep -oE 'dispatchId[^a-z]+ctx_[a-z0-9]+' | head -1 | grep -oE 'ctx_[a-z0-9]+')
if ! echo "$OUT" | grep -q '"type": "worker_done"' || ! echo "$OUT" | grep -qE '"subject": "[^"]*APPROVED' \
  || echo "$OUT" | grep -qE '"subject": "[^"]*CHANGES_REQUESTED'; then
  echo "STOP: not an approval. Read it, then ack $DELIVERY"; exit 1
fi
orca orchestration check --run "$ORCA_RUN" --ack "$DELIVERY" --json >/dev/null 2>&1
[ -n "$DISPATCH" ] && sh "$S/finish-worker.sh" "$DISPATCH" rm >/dev/null
sh "$S/wait-load.sh" && sh "$S/queue.sh" "$PR" || exit 1
sh "$S/cleanup-wt.sh" "$WT"
[ $# -eq 0 ] && exit 0
sh "$S/wait-load.sh" && sh "$S/start-worker.sh" "$@" && sh "$S/wait-msg.sh"
