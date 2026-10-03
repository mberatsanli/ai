#!/bin/sh
# usage: start-review.sh <pr> <issue> [round]
# Starts the Reviewer (Opus) on a PR in a fresh worktree. Pass a round letter (b, c, ...) for a
# re-review: the reviewer then checks that its earlier findings are fixed.
. "$(dirname "$0")/env.sh"
PR=$1; N=$2; ROUND=$3
if [ -n "$ROUND" ]; then
  TASK="Re-review PR ${REPO} #${PR} (closes #${N}). Read your earlier REVIEW comment and the fixer's reply; verify each finding is fixed with a real test."
else
  TASK="Review PR ${REPO} #${PR} (closes #${N})."
fi
orca orchestration worker-start --run "$ORCA_RUN" --worktree new-top-level --name "review-${PR}${ROUND}" \
  --agent claude --model claude-opus-5-5 --task-title "Review PR #$PR" --spec "You are the Reviewer on the team. Read docs/agents/roles/reviewer.md, docs/agents/code-standards.md, docs/agents/roles/_common.md and CLAUDE.md first.
${TASK} gh pr checkout ${PR}. Read issue #${N}; verify every Acceptance item yourself on a clean install, and run the project's typecheck, lint, format and test commands once. Check correctness, tests that prove behavior, compatibility, security, clean code, and scope (nothing outside the issue's Ownership).
Submit on the current head: gh pr review ${PR} --comment --body with first line exactly 'REVIEW: APPROVED' or 'REVIEW: CHANGES_REQUESTED', then numbered findings (file, what's wrong, what to do). Don't push commits.
$(agent_rules)
Finish with worker_done: verdict, head sha, findings in short." --json | dispatch_line
