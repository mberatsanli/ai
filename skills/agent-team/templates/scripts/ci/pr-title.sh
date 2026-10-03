#!/usr/bin/env bash
# The `pr-title` CI job. PRs are squash-merged, so the title becomes the commit message on main and must
# follow Conventional Commits. Run by .github/workflows/pr-title.yml and by scripts/local-ci, which passes
# the title in PR_TITLE.
# Usage: scripts/ci/pr-title.sh [title]
set -euo pipefail

readonly title=${1:-${PR_TITLE:?pass the title as an argument or in PR_TITLE}}
readonly pattern='^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9-]+\))?!?: [^ ].*$'

if [[ ! "$title" =~ $pattern ]]; then
  echo "::error::PR title '$title' does not follow Conventional Commits, for example 'feat(api): add the audit log'."
  exit 1
fi
