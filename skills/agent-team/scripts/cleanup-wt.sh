#!/bin/sh
# usage: cleanup-wt.sh <worktree name>... — closes terminals, kills leftovers, removes the worktree
# and its branches. For worktrees whose worker is already released (merged PRs, old reviewers).
# A fix round on the same slug gets a new worktree named <name>-2, <name>-3, ...; those go too.
. "$(dirname "$0")/env.sh"
SIBLINGS=$(for N in "$@"; do git worktree list --porcelain | awk -v n="/$N-[0-9]+$" '/^worktree /{w=substr($0,10); if (w ~ n) {sub(/.*\//, "", w); print w}}'; done)
for N in "$@" $SIBLINGS; do
  P=$(git worktree list --porcelain | awk -v n="/$N" '/^worktree /{w=substr($0,10)} w ~ n"$" {print w; exit}')
  [ -z "$P" ] && { echo "no worktree named $N"; continue; }
  [ "$P" = "$ROOT" ] && continue
  sh "$SKILL_DIR/close-terminals.sh" "$P"
  sh "$SKILL_DIR/killwt.sh" "$P"
  B=$(git -C "$P" branch --show-current 2>/dev/null)
  orca worktree rm --worktree "path:$P" --force --json >/dev/null 2>&1
  git worktree prune
  git branch -D $B "$(git config user.name | tr 'A-Z' 'a-z')/$N" >/dev/null 2>&1
  [ -d "$P" ] && echo "still there: $N" || echo "removed $N"
done
