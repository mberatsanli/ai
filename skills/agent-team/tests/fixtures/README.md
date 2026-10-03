# Recorded `gh` output

These cases were recorded on a real project and copied here with its repo renamed to
`octo-org/octo-repo`. That project required the checks `checks`, `test-postgres`, `pr-title` and
`dev-smoke`, and let `bun.lock` differ on carry-over: [../agent-team.json](../agent-team.json) is its
config, and the tests run the gate with it. The file paths and review texts inside the data are left
as recorded.

Each folder holds what `scripts/merge-gate` reads for one case: `pr.json` from
`gh pr view <PR> --json state,baseRefName,headRefOid,statusCheckRollup`,
`compare.json` from `gh api repos/octo-org/octo-repo/compare/main...<head>` and
`reviews.json` from `gh api repos/octo-org/octo-repo/pulls/<PR>/reviews --paginate --slurp`.
A case with commit statuses also holds `status.json` from
`gh api repos/octo-org/octo-repo/commits/<head>/status`, cut down to each status's
`context` and `description`: `statusCheckRollup` leaves the description out.
Review user objects are cut down to `login`, and `compare.json` to its counts
(the gate asks gh for `behind_by` only).

The cases where the approval is on an older commit also hold `commits.json` from
`gh api repos/octo-org/octo-repo/pulls/<PR>/commits --paginate --slurp`, cut down to
each commit's `sha` and its parents, and a `compare/<sha>.json` for every commit
the gate compares with `main`, cut down to the counts, `status` and each file's
`filename`, `status`, `sha` and `previous_filename`, and a `trees/<sha>.json`
from `gh api repos/octo-org/octo-repo/git/trees/<sha>?recursive=1` cut down to the
PR's files, for the file modes. `--update` cases play CI over time: the nth
`gh pr view` answers with `pr.<n>.json`, or with the newest earlier one.
Recorded `behind_by` values are set to what they were when the gate would have
run, because `main` has moved on since. A `gh-error.txt` makes the fake
`gh pr view` fail with that message on stderr, and a `merge-error.txt` does the
same for `gh pr merge`. The gate doesn't compare a PR that isn't open, so the
merged and closed cases have no `compare.json`.

The cases recorded before the gate read `state`, `baseRefName` and the comparison
got `"state": "OPEN"`, `"baseRefName": "main"` and a `compare.json` that is
up to date with `main` (`behind_by: 0`).

The cases recorded before CI had a `dev-smoke` job got a `dev-smoke` run copied
from their newest `checks` run, since both are jobs of the same CI workflow. In
`check-failed` the copy passed, so only `checks` fails there.

| Case                               | Source                                                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `approved-on-head`                 | PR #68 as recorded. `pr-title` ran four times; the newest run passed.                                         |
| `checks-never-ran`                 | PR #67 as recorded. Approved on its head, but it was merged before CI existed.                                |
| `carried-over`                     | PR #69, keeping only the approval of its first commit. The merge from `main` after it left the diff as it was. |
| `merge-changed-only-bun-lock`      | PR #92 after its update: approved on `1c18ad3`, and the merge from `main` changed only `bun.lock` of its files. |
| `merge-changed-bun-lock-and-pr-file` | `merge-changed-only-bun-lock` where the merge also changed `packages/http/package.json`.                     |
| `rename-source-swapped`            | `carried-over` where `schema/api.def` is renamed from `schema/main.def` at the approved commit and from `schema/types.def` at the head. |
| `mode-changed`                     | `carried-over` where the merge made `schema/scripts/generate.ts` executable (`100755`).                          |
| `too-many-files`                   | `carried-over` where the head's diff lists 300 files, GitHub's limit.                                          |
| `pushed-after-approval`            | PR #82's commits, with a `REVIEW: APPROVED` on `6051a70`. The author pushed `096b783` after it.               |
| `merged-other-branch`              | `carried-over` where the merged commit `8c724a6` is not on `main` (`status: diverged`).                       |
| `approved-commit-gone`             | `carried-over` with the approved commit gone from the PR, as after a force push.                              |
| `update-then-merge`                | PR #82 before (`pr.json`, 1 behind, approved on `3468ba3`) and after `gh pr update-branch` made `edb9829`: CI running (`pr.2.json`), then green (`pr.3.json`). |
| `update-ci-never-finishes`         | PR #92 before its update, then CI that keeps running on the new head `1b17d05`.                               |
| `changes-requested-after-approval` | PR #69 with a `REVIEW: CHANGES_REQUESTED` review added after the approval.                                    |
| `checks-pending`                   | PR #69 with `test-postgres` still in progress.                                                                |
| `check-failed`                     | PR #69 with `checks` failed.                                                                                  |
| `no-review`                        | PR #69 with no reviews.                                                                                       |
| `check-requeued`                   | PR #68 with a re-run of `pr-title` queued after its passed runs.                                              |
| `status-context-passed`            | PR #68 with a passed commit status (`StatusContext`) recorded from kubernetes/kubernetes#142605.              |
| `status-context-pending`           | `status-context-passed` with the commit status still `PENDING`.                                               |
| `behind-main`                      | `approved-on-head` with the comparison of PR #76's head against `main` after newer commits landed (2 behind). |
| `already-merged`                   | PR #76 as recorded after it was merged: green and approved on its head, `state: MERGED`.                      |
| `closed-unmerged`                  | `approved-on-head` with `state: CLOSED`.                                                                      |
| `unknown-pr`                       | The error `gh pr view 99999` prints for a PR number that doesn't exist.                                       |
| `merge-refused`                    | `approved-on-head` where `gh pr merge` fails because the head moved after the gate checked it.                |
| `dev-smoke-passed`                 | PR #125 as recorded before it merged: `checks`, `test-postgres`, `pr-title` and `dev-smoke` passed, approved on its head. |
| `dev-smoke-failed`                 | `dev-smoke-passed` with `dev-smoke` failed.                                                                   |
| `dev-smoke-pending`                | `dev-smoke-passed` with `dev-smoke` still in progress.                                                        |
| `dev-smoke-never-ran`              | `dev-smoke-passed` without its `dev-smoke` run.                                                               |
| `status-beats-failed-check`        | PR #171 as recorded while Actions couldn't start jobs (every check run `FAILURE`), plus a newer passed commit status for each required check whose description starts with the `local-ci coordinator-mac 80f967a: ` marker, approved on its head. |
| `status-failed`                    | `status-beats-failed-check` with the `checks` commit status failed.                                           |
| `status-without-marker`            | `status-beats-failed-check` where the `checks` commit status says only `success`, as if posted by hand.       |
| `status-marker-other-head`         | `status-beats-failed-check` where the `checks` commit status carries the `local-ci` marker of `3468ba3`.      |
| `update-then-local-ci`             | `update-then-merge` where Actions failed on the new head (`pr.2.json`) and `scripts/local-ci` then posted passed commit statuses with its marker (`pr.3.json`). |
| `up-to-date-without-local-ci`      | `status-beats-failed-check` before `scripts/local-ci` ran: only the failed Actions runs (`pr.json`), then the passed commit statuses with its marker (`pr.2.json`). |
| `local-ci-errored`                 | `up-to-date-without-local-ci` after a `scripts/local-ci` run whose Postgres container did not start: `test-postgres` and `dev-smoke` are `ERROR` (`pr.json`), then every status passed after the re-run (`pr.2.json`). `status.json` keeps the error descriptions, since the gate reads only their marker. |
