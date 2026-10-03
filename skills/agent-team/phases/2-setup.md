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
5. **Wave 0 issues by hand** (or by the PM in phase 3, before anything else): the DevOps work that
   everything else needs: repo skeleton, strict lint and format, test runner, CI with stable job names,
   a PR title check, and **`scripts/merge-gate <pr> [--update]`**: merge only when every required check
   passed on the head and the newest `REVIEW:` comment review says `APPROVED` on the head (or carries
   over a merge from `main` that touched none of the PR's files). If GitHub Actions can't run, also a
   `scripts/local-ci <pr>` that runs the same jobs locally and posts commit statuses. Copy and adapt
   them from a project that has them.
6. **Orca run.** Load the `orca-cli` skill, then create the run with an objective and note its id
   (see [orca.md](orca.md#the-run)): `export ORCA_RUN=run_...`.
7. **Daily Scrum issue.** One issue per sprint where agents comment Done / Next / Blocked by
   (`SCRUM_ISSUE`).
