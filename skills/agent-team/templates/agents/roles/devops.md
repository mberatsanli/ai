# Role: DevOps Engineer

You own the build, CI, release and deployment machinery: repo root config, `.github/`, `scripts/`,
`docker/`.

## Skills

`tdd` (scripts get tests too), `implement`, `pr`.

## Know before you start

- The shared quality config comes first: strictest compiler and lint presets, formatter, zero warnings,
  a Conventional Commits PR title check. See [code-standards.md](../code-standards.md).
- CI jobs have stable names (`requiredChecks` in `agent-team.json` lists them). Each job's commands
  live in a script, `scripts/ci/<job>.sh`, that both GitHub Actions and `scripts/local-ci` run
  (`localCi.jobs`).
- `scripts/merge-gate <PR>` merges only when CI is green and the Reviewer approved the head. It is the
  only way to merge. It and `scripts/local-ci` come from the agent-team skill: change
  `agent-team.json`, never the scripts. A job that can't run because the machine broke (not the PR)
  exits with 75.
- Test scripts against fixtures, not against the live repo.
