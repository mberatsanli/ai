# The agent team

<Project> is built by a team of AI agents run through Orca orchestration. No human reviews code; quality
comes from gates that machines check. The team runs **Scrum**: see [scrum.md](scrum.md).

## Roles

Roles are job descriptions, not single agents. Each role has a file in [roles/](roles/), and every agent
also follows [roles/_common.md](roles/_common.md).

| Role | Agent | Does |
|---|---|---|
| **Coordinator** (Scrum Master) | Claude, the main session | Runs the Scrum events, starts and supervises agents, answers their questions, owns shared contracts (`<spec folder>`), merges through the merge gate |
| [Project Manager](roles/project-manager.md) (Product Owner) | Claude | Owns and orders the backlog: issues, labels, epics, sprints, story points. Writes no code |
| [Backend Engineer](roles/backend.md) | Claude | `<backend folders>` |
| [Frontend Engineer](roles/frontend.md) | Claude | `<frontend folders>` |
| [DevOps Engineer](roles/devops.md) | Claude | Tooling, CI, merge gate, Docker |
| [QA Engineer](roles/qa.md) | Claude | e2e tests, exploratory testing in a real browser, bug issues |
| [UX Designer](roles/ux.md) | Claude | Walks the app, compares loved products, files UX issues |
| [Reviewer](roles/reviewer.md) | Claude Opus | Reviews every PR; never one it wrote |
| [Researcher](roles/researcher.md) | Codex or Claude | Research questions, written to `docs/research/` |

At most <N> agents run at the same time (default 1 on a shared machine).

## Waves

A wave starts only when the one before it is merged.

1. **Wave 0 (foundations):** repo skeleton, tooling, CI, merge gate, shared contracts.
2. **Wave 1 (parallel):** the main pieces, each against the shared contracts.
3. **Wave 2:** wiring the pieces together, e2e tests, Docker, and the MVP done list.

## Task specs

Every task is a GitHub issue (see [issue-tracker.md](issue-tracker.md)) that names:

- **Target:** the files or package in scope.
- **Change:** the result to produce.
- **Constraints:** rules from `CLAUDE.md` and `docs/` that apply, and what not to touch.
- **Ownership:** the folders this agent may edit. Agents never edit outside them.
- **Acceptance:** the tests or output that prove it's done.

## Merging

`scripts/merge-gate <PR>` merges a PR only when **every required check passed on the head** and **the
Reviewer approved the latest commit**. Nobody merges any other way. Merges are squash merges.

All agents share one GitHub account, which can't approve its own PR. So the Reviewer submits a comment
review whose first line is exactly `REVIEW: APPROVED` or `REVIEW: CHANGES_REQUESTED`. The gate takes the
newest `REVIEW:` review and merges only if it approves the head, or the approval carries over: every
commit after it is a merge from `main` that changed none of the PR's files.

The required checks are the `requiredChecks` in `agent-team.json`: <CI job names>. The gate refuses
while any of them failed, is still running, or never ran.

`scripts/merge-gate <PR> --update` merges `main` in, waits for CI, then applies the rules. If GitHub
Actions can't run, `scripts/local-ci <PR>` runs the same jobs locally and posts commit statuses; with
`mergeGate.localCiOnUpdate` on, `--update` runs it by itself. Only the coordinator runs it. Both scripts
come from the agent-team skill; change `agent-team.json`, not the scripts.

## What still needs a human

Only actions that can't be undone or that face the outside world: publishing packages, making the repo
public, buying things, and anything touching accounts. The coordinator asks first. Everything else is
reported, not asked.
