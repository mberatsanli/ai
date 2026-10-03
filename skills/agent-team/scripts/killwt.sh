#!/bin/sh
# usage: killwt.sh <worktree path> — kills leftover processes (vitest, dev servers) whose cwd is inside it.
# Never touches the main checkout.
P=$1
[ -z "$P" ] && exit 0
ROOT=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
case "$P" in "$ROOT"|"$ROOT"/*) exit 0;; esac
PIDS=$(lsof -nP -d cwd -Fpn 2>/dev/null | awk -v p="$P" '/^p/{pid=substr($0,2)} /^n/{if (index(substr($0,2),p)==1) print pid}' | sort -u)
[ -n "$PIDS" ] && kill $PIDS 2>/dev/null && sleep 2 && kill -9 $PIDS 2>/dev/null
exit 0
