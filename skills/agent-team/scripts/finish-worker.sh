#!/bin/sh
# usage: finish-worker.sh <dispatch id> [rm]
# Releases a settled worker, kills its leftover processes and closes every terminal in its worktree.
# With "rm" it also removes the worktree and its local branches: use it for reviewers, or once the PR
# merged. Without "rm" the worktree stays, so a fixer can continue the branch.
. "$(dirname "$0")/env.sh"
D=$1
INFO=$(orca orchestration worker-show --dispatch "$D" --json)
field() { echo "$INFO" | python3 -c "import json,sys;print(json.loads(sys.stdin.read(),strict=False)['result']['worker'].get('$1') or '')"; }
TERM_H=$(field agentTerminalHandle); WT=$(field worktreeId)
orca orchestration worker-release --dispatch "$D" --json >/dev/null 2>&1
[ -n "$TERM_H" ] && orca terminal close --terminal "$TERM_H" --json >/dev/null 2>&1
P=${WT#*::}
if [ -n "$WT" ] && [ "$P" != "$ROOT" ]; then
  sh "$SKILL_DIR/killwt.sh" "$P"
  sh "$SKILL_DIR/close-terminals.sh" "$P"
  if [ "$2" = rm ]; then
    B=$(git -C "$P" branch --show-current 2>/dev/null)
    orca worktree rm --worktree "path:$P" --force --json >/dev/null 2>&1
    git worktree prune
    git branch -D $B "$(git config user.name | tr 'A-Z' 'a-z')/$(basename "$P")" >/dev/null 2>&1
  fi
fi
echo "finished $D term=${TERM_H:-none} wt=$(basename "${P:-none}")"
