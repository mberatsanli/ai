# Phase 2: Team setup

Goal: everything agents need to work alone and safely: role files, skills, standards, labels, CI, the
merge gate and an Orca run.

## Steps

1. **Repo.** A GitHub repo with `main`. Note the `owner/name`.
2. **Agent docs.** Copy [../templates/agents/](../templates/agents/) to `docs/agents/` and fill in
   every `<...>`: repo, stack, folders per role, test commands, CI job names. Keep only the roles the
   project needs. Add a `docs/agents/agent-rules.md` for project-only rules every agent must follow
   (it is added to every spec), for example "never use the database `x`".
3. **Skills.** For you (once per machine): `orca skills install --skill orca-cli --skill orchestration`.
   For every agent, in the project, so each worktree has them:
   `npx skills add mattpocock/skills --skill grilling --skill to-spec --skill to-tickets --skill triage
   --skill tdd --skill implement --skill pr --skill research --skill codebase-design
   --skill domain-modeling --skill improve-codebase-architecture`. Commit them. Check that
   `.claude/skills/` lists them (the CLI links them from `.agents/skills/`).
4. **Labels.** `gh label create` for: `role:*` (one per role), `wave:0..2`, `points:1,2,3,5,8`,
   `epic`, `type:bug`, `type:ux`, and the triage labels (`needs-triage`, `needs-info`,
   `ready-for-agent`, `ready-for-human`, `wontfix`).
5. **Merge gate and local CI.** Copy them from this skill; don't write your own:
   ```sh
   mkdir -p scripts
   for f in merge-gate local-ci agent_team_config.py; do
     cp ~/.claude/skills/agent-team/templates/scripts/$f scripts/
   done
   cp ~/.claude/skills/agent-team/templates/agent-team.json .
   ```
   Fill in `agent-team.json` (fields: [templates/scripts/README.md](../templates/scripts/README.md)):
   - `requiredChecks`: the CI job names. Pick them now; they don't change later.
   - `localCi.jobs`: the same jobs, each calling the same `scripts/ci/<job>.sh` the CI workflow calls.
     `needsDocker` for jobs that start containers. `localCi.setup` is the install step (`npm ci`,
     `bun install --frozen-lockfile`, `uv sync --locked`, ...).
   - `carryOverLockFiles`: the package manager's lock file, if CI installs from it in a strict mode.
   - `mergeGate.localCiOnUpdate`: `true` if GitHub Actions can't run (billing), else `false`.

   The GitHub Actions workflow runs the same commands: one job per `requiredChecks` name, with the
   same name, each running its `scripts/ci/<job>.sh` after the setup step. Give the PR title job
   `PR_TITLE: ${{ github.event.pull_request.title }}`, like local CI does. Commit the scripts and the
   config. Once the first PR is open, check them with `scripts/merge-gate <PR> --dry-run`.
6. **Wave 0 issues by hand** (or by the PM in phase 3, before anything else): the DevOps work that
   everything else needs: repo skeleton, strict lint and format, test runner, the `scripts/ci/*.sh`
   jobs and the CI workflow with the job names from `agent-team.json`, and a Conventional Commits PR
   title check.
7. **Orca run.** Load the `orca-cli` skill, then create the run with an objective and note its id
   (see [orca.md](orca.md#the-run)): `export ORCA_RUN=run_...`.
8. **Daily Scrum issue.** One issue per sprint where agents comment Done / Next / Blocked by
   (`SCRUM_ISSUE`).
