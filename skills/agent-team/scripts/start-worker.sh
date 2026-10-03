#!/bin/sh
# usage: start-worker.sh <role> <issue> <slug> ["extra spec text"]
# Starts one agent in its role (pm, backend, frontend, devops, qa, ux, ...) on one issue, in a new
# worktree, on branch <role>/<issue>-<slug>. Every job is an issue, also the PM's (backlog, planning,
# refinement) and QA's (demo, exploratory test). The extra text is added to the spec: group issues
# that touch the same screen into one PR, or continue an existing branch to fix review findings.
. "$(dirname "$0")/env.sh"
ROLE=$1; N=$2; SLUG=$3; EXTRA=$4
ROLE_FILE=$ROLE; [ "$ROLE" = pm ] && ROLE_FILE=project-manager
orca orchestration worker-start --run "$ORCA_RUN" --worktree new-top-level --name "$ROLE-$N-$SLUG" \
  --agent claude --setup run --task-title "$ROLE #$N" --spec "You are the ${ROLE} on the team (Scrum${SPRINT:+, $SPRINT}). Read docs/agents/roles/_common.md, docs/agents/roles/${ROLE_FILE}.md and docs/agents/code-standards.md first (if they exist), then CLAUDE.md and the docs your issue links. Use the skills your role file names.
Your issue: ${REPO} #${N} (gh issue view ${N} --repo ${REPO} --comments). Do exactly that issue, nothing outside its Ownership. Its Blocked-by issues are closed.
${EXTRA}
$(agent_rules)
Branch: ${ROLE}/${N}-${SLUG} from origin/main (git fetch first), unless told above to continue an existing branch. For code: test first (red, green, refactor), and the project's typecheck, lint, format and test commands must pass.
One PR if you change files: Conventional Commits title, body with What, Why, How I proved it, and 'Closes #${N}'.
${SCRUM_ISSUE:+Add a Daily Scrum comment on issue #${SCRUM_ISSUE} (Done / Next / Blocked by) before finishing.}
Blocking questions: orca orchestration ask. Finish with worker_done: three sentences and the PR URL." --json | dispatch_line
