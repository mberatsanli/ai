# Merge gate and local CI

Two scripts that guard `main`. Copy this folder's files into your project's `scripts/` and write an
`agent-team.json` at the repo root (start from `templates/agent-team.json` in the agent-team skill).

They need Python 3.9 or newer, `git`, and `gh` logged in to the repo. No other packages.

| File | What it is |
|---|---|
| `merge-gate` | the only way into `main` |
| `local-ci` | runs the CI jobs on your machine when GitHub Actions can't |
| `agent_team_config.py` | reads `agent-team.json`; both scripts use it |

## merge-gate

```sh
scripts/merge-gate <PR>             # merge if allowed
scripts/merge-gate <PR> --dry-run   # only say if it would merge
scripts/merge-gate <PR> --update    # bring the PR up to date, wait for CI, then merge if allowed
```

It squash-merges a PR and deletes its branch only when all of this is true:

- The PR is open, and its head contains every commit of the base branch.
- Every check in `requiredChecks` ran on the head and passed. Any other check that ran passed too.
  A re-run replaces the older run. A commit status counts like a check run, but a passed status for a
  required check counts only if `local-ci` posted it on this head (its description starts with
  `local-ci <host> <sha7>: `).
- The newest review whose first line starts with `REVIEW:` says exactly `REVIEW: APPROVED`, and it was
  made on the head.

An approval on an older commit **carries over** to the head when every commit after it is a merge
from the base branch, and those merges left the PR's own diff as it was: the same files, renamed from
the same place, with the same content and the same mode. A file in `carryOverLockFiles` may differ in
content, because CI fails on a lock file that doesn't match the manifests. Anything else needs a new
review: a new commit by the author, a merge from another branch, or a merge that touched one of the
PR's files. So does a PR with 300 or more changed files, because GitHub lists only 300.

`--update` runs `gh pr update-branch` on a PR that is behind, waits for CI on the new head (up to
`ciTimeoutMinutes`), then decides. With local CI on, it runs `scripts/local-ci` on the new head
instead of waiting for Actions. It also runs it on a head that is up to date but has no local-ci
results yet, or whose last run errored. So one command is enough.

GitHub merges only if the head is still the one the gate checked (`--match-head-commit`).

| Exit code | Meaning |
|---|---|
| 0 | merged (or, with `--dry-run`, would merge) |
| 1 | refused; the output lists every reason |
| 2 | could not check: bad arguments, bad config, or `gh` failed |

## local-ci

```sh
scripts/local-ci <PR>
```

Run it from a clean checkout of the repo. It checks the PR's head out into a temporary worktree, runs
`localCi.setup`, then every job in `localCi.jobs`, one after another, and posts each result as a
commit status named after the job. Your own checkout is never touched. Logs stay in a temporary folder
that the output and each status name.

- First it posts every job as `pending`. A run that stops early (a signal, a failed `gh` or `git`
  command) posts `error` on every job that has no result yet, so nothing stays pending forever.
- Each job runs with `/bin/sh -c` in the worktree, with `CI=true`, the `localCi.env` variables,
  `PR_NUMBER`, `PR_TITLE` and `PR_HEAD_SHA`, and without the variables in `localCi.unsetEnv`.
- A job that exits with **75** says "this machine broke, not the PR" (for example its database
  container never got ready). It is posted as `error`, not `failure`, and `merge-gate --update` runs
  local CI again.
- It refuses to start, and posts nothing, when the checkout has uncommitted changes, when a job has
  `needsDocker` and Docker isn't running, or when another run holds the lock (one run at a time per
  clone).

| Exit code | Meaning |
|---|---|
| 0 | every job passed |
| 1 | a job (or the setup) failed |
| 2 | bad arguments or config, dirty checkout, no Docker, lock held, a signal, a job errored, or `gh` or `git` failed |

## agent-team.json

```json
{
  "requiredChecks": ["checks", "e2e", "pr-title"],
  "reviewMarker": "REVIEW:",
  "carryOverLockFiles": ["package-lock.json"],
  "mergeGate": { "pollIntervalSeconds": 15, "ciTimeoutMinutes": 30, "localCiOnUpdate": false },
  "localCi": {
    "setup": "npm ci",
    "env": {},
    "unsetEnv": ["DATABASE_URL"],
    "jobs": [
      { "name": "checks", "command": "scripts/ci/checks.sh" },
      { "name": "e2e", "command": "scripts/ci/e2e.sh", "needsDocker": true, "artifacts": ["test-results"] },
      { "name": "pr-title", "command": "scripts/ci/pr-title.sh \"$PR_TITLE\"" }
    ]
  }
}
```

| Field | Default | Meaning |
|---|---|---|
| `requiredChecks` | (required) | check names that must pass on the head; use your CI job names |
| `reviewMarker` | `REVIEW:` | the first word of a verdict review; the approval is `<marker> APPROVED` |
| `carryOverLockFiles` | `[]` | paths from the repo root whose content may change in a carried-over merge |
| `mergeGate.pollIntervalSeconds` | `15` | how often `--update` asks GitHub about CI |
| `mergeGate.ciTimeoutMinutes` | `30` | how long `--update` waits for CI on the new head |
| `mergeGate.localCiOnUpdate` | `false` | `--update` runs `local-ci` instead of waiting for Actions |
| `localCi.setup` | none | a command run once before the jobs, like `npm ci`; if it fails, every job fails |
| `localCi.env` | `{}` | extra variables for every job |
| `localCi.unsetEnv` | `[]` | variables removed from every job, so a job can't reach what it wasn't given |
| `localCi.jobs[].name` | (required) | the commit status name; match the check name in GitHub Actions |
| `localCi.jobs[].command` | (required) | what to run, from the repo root of the PR's head |
| `localCi.jobs[].needsDocker` | `false` | refuse to start when Docker isn't running |
| `localCi.jobs[].artifacts` | `[]` | paths to copy next to the job's log before the worktree goes away |

Unknown keys are an error, so a typo can't switch a rule off. Keys that start with `$` are ignored.
`local-ci` reads the file from your checkout, not from the PR, so a PR can't change what proves it.

Environment variables:

| Variable | Meaning |
|---|---|
| `AGENT_TEAM_LOCAL_CI=1` / `=0` | turn local CI on `--update` on or off for one run |
| `AGENT_TEAM_CONFIG` | read another config file |
| `MERGE_GATE_POLL_INTERVAL_MS`, `MERGE_GATE_CI_TIMEOUT_MS` | override the waits (tests) |
| `MERGE_GATE_LOCAL_CI` | the local CI command `--update` runs (default: `local-ci` next to `merge-gate`) |

## Keep CI and local CI the same

Put each job's commands in a script, like `scripts/ci/checks.sh`, and call that same script from
your GitHub Actions job and from `localCi.jobs`. Give the Actions job the same name as the local job,
so the gate sees one check either way.

## Tests

The tests live in the agent-team skill, not in your project:

```sh
cd <agent-team skill>/tests && python3 -B -m unittest
```
