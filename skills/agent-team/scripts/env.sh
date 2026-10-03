# Shared settings for the agent-team scripts. Source it; don't run it.
# ORCA_RUN    the Orca orchestration run id (required)
# SPRINT      the sprint name agents see, like "Sprint 5" (optional)
# SCRUM_ISSUE the issue that holds Daily Scrum comments (optional)
# REPO        owner/name on GitHub (default: the current repo)
# GATE        the merge gate command (default: scripts/merge-gate)
# LOCAL_CI    the local CI command the gate runs on --update (default: scripts/local-ci)
# AGENT_TEAM_LOCAL_CI=1 (or =0) turns local CI on --update on (or off), whatever agent-team.json says
: "${ORCA_RUN:?set ORCA_RUN to the Orca run id (orca orchestration run-list)}"
ROOT=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
SKILL_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT" || exit 1
: "${REPO:=$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
: "${GATE:=scripts/merge-gate}"
: "${LOCAL_CI:=scripts/local-ci}"

# The rules every agent spec carries: the skill's own, then the project's (docs/agents/agent-rules.md).
agent_rules() {
  cat "$SKILL_DIR/rules.txt"
  [ -f "$ROOT/docs/agents/agent-rules.md" ] && cat "$ROOT/docs/agents/agent-rules.md"
}

# Prints "ok dispatchId error" from a worker-start answer.
dispatch_line() {
  python3 -c "import json,sys;d=json.load(sys.stdin);r=d.get('result',{});print(d.get('ok'),r.get('dispatchId'),d.get('error'))"
}
