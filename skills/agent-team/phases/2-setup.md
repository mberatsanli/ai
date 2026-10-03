# Phase 2: Team setup

Goal: everything agents need to work alone and safely: role files, skills, standards, labels, CI, the
merge gate and an Orca run.

## Steps

1. **Repo.** A GitHub repo with `main`. Note the `owner/name`.
2. **Agent docs.** Copy [../templates/agents/](../templates/agents/) to `docs/agents/` and fill in
   every `<...>`: repo, stack, folders per role, test commands, CI job names. Keep only the roles the
   project needs. Add a `docs/agents/agent-rules.md` for project-only rules every agent must follow
   (it is added to every spec), for example "never use the database `x`".
3. **Skills for agents.** Install the skills the role files name into the project, so every worker
   finds them: put them in `.agents/skills/<name>/` and link each from `.claude/skills/<name>`
   (`ln -s ../../.agents/skills/<name> .claude/skills/<name>`). Copy them from a project that already
   has them, or install them with the `find-skills` skill. At least: `tdd`, `implement`, `pr`,
   `to-spec`, `to-tickets`, `triage`, `grilling`, `research`, `codebase-design`.
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
6. **Orca run.** Load the `orca-cli` skill. Create an orchestration run for the project and note its
   id: `export ORCA_RUN=run_...`.
7. **Daily Scrum issue.** One issue per sprint where agents comment Done / Next / Blocked by
   (`SCRUM_ISSUE`).
