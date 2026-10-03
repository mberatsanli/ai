# How the team runs Scrum

The agent team follows Scrum. Agents don't work in hours, so a sprint ends when its committed issues
are done or dropped, not when a calendar says so. Everything else follows the Scrum Guide.

## Roles

| Scrum role | Who |
|---|---|
| **Product Owner** | The [Project Manager](roles/project-manager.md) agent. Owns the Product Backlog and its order |
| **Scrum Master** | The coordinator (`MAIN` session). Runs the events, removes blockers, guards the process |
| **Developers** | Backend, Frontend, DevOps, QA and UX agents, plus the Reviewer |
| **Stakeholder** | The human owner. Gets the Sprint Review report; isn't asked to approve code |

## Artifacts on GitHub

- **Product Backlog:** all open issues on `<owner/repo>`, ordered by the Product Owner.
- **Sprint Backlog:** issues in the current milestone (`Sprint N`). The milestone description holds the
  **Sprint Goal**.
- **Increment:** what's merged to `main` during the sprint and passes the Definition of Done.
- **Story points:** one `points:*` label per issue (1, 2, 3, 5, 8). Anything bigger gets split.
- **Order inside a sprint:** a `Priority: N` line at the top of each issue body, plus `Blocked by: #N`.

## Definition of Ready

An issue can enter a sprint only when:

- it uses the task spec format (Target, Change, Constraints, Ownership, Acceptance, Docs),
- its Ownership doesn't overlap with another issue in the same sprint, unless they're chained with `Blocked by`,
- its Acceptance can be checked by a test or a command,
- its dependencies are listed,
- it has `points:*`, `role:*`, `wave:*`, `ready-for-agent` and a milestone.

## Definition of Done

An issue is done only when:

- the code was written test-first and CI is green (typecheck, lint, tests, conformance),
- the Reviewer approved the latest commit,
- `scripts/merge-gate` merged it into `main`,
- the issue is closed by the PR,
- docs changed with it, if the behavior it describes changed.

## Events

**Sprint Planning** (Scrum Master + Product Owner). The Product Owner proposes the Sprint Goal and the
top of the backlog. The team's capacity is what the machine allows (default: one agent at a time). The Scrum Master checks
every issue against the Definition of Ready, then the milestone is set.

**Daily Scrum** (every coordinator checkpoint: each time a worker finishes, or at least every two hours of
work). Each active worker answers three questions as a comment on the sprint's `Daily Scrum` issue:
what I finished, what I'm doing next, what blocks me. The Scrum Master resolves blockers and updates
the Orca workspace cards.

**Backlog Refinement** (during the sprint). The Product Owner splits, clarifies and estimates the issues
for the next sprint, so the next Sprint Planning is short.

**Sprint Review** (when the Sprint Backlog is done). QA demos the increment against the Sprint Goal
using the real app. The Scrum Master writes `docs/sprints/sprint-N.md`: goal, what's done, what isn't and
why, points planned vs done, and links to PRs. The stakeholder gets this report.

**Sprint Retrospective** (right after the review). Every agent that worked in the sprint adds what went
well, what didn't, and one improvement to `docs/sprints/sprint-N.md`. The Scrum Master turns the
improvements into real changes: role files, `CLAUDE.md`, lint rules or scripts, so the lesson is in the
structure, not just in a note.

## Sprint flow in Orca

1. Sprint Planning sets the milestone.
2. The Scrum Master starts one worker per ready issue (as capacity allows), each in its own worktree, with its role
   file and issue number in the task spec.
3. Each worker opens a PR and sends `worker_done`. The Scrum Master starts a Reviewer on that PR.
4. Changes requested: the original worker (or a new one with the same role) fixes them, and the Reviewer
   checks again.
5. Approved and green: `scripts/merge-gate` merges. The next ready issue gets the free slot.
   Cleanup right after: every settled worker is released and its terminal closed as soon as it sends
   `worker_done`. When the PR is merged, the implementer's and the Reviewer's worktrees and local
   branches are removed too. No idle agent stays open.
6. Sprint Backlog done: Sprint Review, Retrospective, then the next Sprint Planning.
