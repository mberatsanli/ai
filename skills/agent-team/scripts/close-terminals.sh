#!/bin/sh
# usage: close-terminals.sh <worktree path> — closes every Orca terminal whose cwd is inside it.
# Orca can leave extra shells in a worktree, not only the agent's own.
P=$1
orca terminal list --json 2>/dev/null | python3 -c "
import json,sys
d=json.loads(sys.stdin.read(),strict=False)['result']
ts=d.get('terminals',d) if isinstance(d,dict) else d
for t in ts:
  if (t.get('worktreePath') or t.get('cwd') or '').startswith('$P'): print(t.get('handle') or t.get('id'))" |
while read -r T; do orca terminal close --terminal "$T" --json >/dev/null 2>&1; done
