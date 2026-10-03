# Issue tracker: GitHub Issues

Issues live in GitHub Issues on `<owner/repo>`. Use the `gh` CLI.

## Conventions

- One issue per task. A task is something one agent can finish and prove in one PR.
- Every issue body follows the task spec format in [team.md](team.md#task-specs): **Target**, **Change**,
  **Constraints**, **Ownership**, **Acceptance**, plus **Docs** (links to the parts of `docs/` that apply).
- Labels (see [triage-labels.md](triage-labels.md)):
  - one `role:*` label: `role:pm`, `role:backend`, `role:frontend`, `role:devops`, `role:qa`, `role:ux`
  - one `wave:*` label: `wave:0`, `wave:1`, `wave:2`
  - one status label: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`
- Blocking goes on its own line near the top of the body: `Blocked by: #12, #14`. An issue is ready only
  when every issue it lists is closed. Also record it as a GitHub issue dependency, so it shows on the issue:
  `gh api -X POST repos/<owner/repo>/issues/<N>/dependencies/blocked_by -F issue_id=<id of the blocker>`
  (the blocker's numeric `id`, not its number). The body line is the source of truth if the two differ.
- Dependencies must be real (B can't be built or tested without A) and form no cycles. Two issues that edit
  the same folders are chained with `Blocked by`, so they never run at the same time.
- Epics list their children as GitHub sub-issues:
  `gh api -X POST repos/<owner/repo>/issues/<epic>/sub_issues -F sub_issue_id=<id of the child>`.
- Bigger features get a tracking issue with the `epic` label and a task list of their child issues.
- A PR closes its issue with `Closes #N` in the PR body.

## When a skill says "publish to the issue tracker"

`gh issue create --repo <owner/repo> --title ... --body-file ... --label ...`

## When a skill says "fetch the relevant ticket"

`gh issue view <N> --repo <owner/repo> --comments`
