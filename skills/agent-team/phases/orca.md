# How the team runs and talks in Orca

Every agent is its own Orca worker: its own worktree, its own terminal, its own card in Orca's sidebar.
The PM, each implementer, each reviewer, QA and UX all show up there side by side, and you (the main
chat) are the coordinator they all report to. Load the `orca-cli` skill once for exact flags.

## The run

```sh
orca orchestration run-create --objective "Build <project> MVP with an agent team: PM backlog, then sprints of implementers, reviewer, QA and UX, merged through scripts/merge-gate" --json
orca orchestration run-use --run <run id>      # later sessions: bind this chat to the same run
export ORCA_RUN=<run id>
```

## Starting agents

- `scripts/start-worker.sh <role> <issue> <slug>` and `scripts/start-review.sh <pr> <issue>` call
  `orca orchestration worker-start --worktree new-top-level --name ... --spec ...`. One worker, one
  issue, one worktree.
- The spec is short and points to files: the role file, `_common.md`, code standards, `CLAUDE.md`, the
  issue. Everything an agent needs to know lives in the repo, not in the spec.
- Reviewers run on Opus (`--model`). Everyone else on the default model.

## Messages

Orca puts "You have N orchestration messages" into the main chat when a worker writes. Read them with
`orca orchestration check --run $ORCA_RUN` (or keep `scripts/wait-msg.sh` running in the background), and
always ack the delivery (`check --ack <deliveryId>`).

| Message | What you do |
|---|---|
| `heartbeat` | Nothing; `wait-msg.sh` acks it. |
| `ask` (a question; the worker is blocked) | Answer with `orca orchestration reply --run $ORCA_RUN --id <msg id> --body "..."`. Answer from the docs and decisions yourself. Only product or scope questions go to the stakeholder. |
| `worker_done` | Release the worker, then review, merge or start the next step. |
| a failure or escalation | Read it, decide, reply or restart. |

## Asking the stakeholder

Agents never talk to the stakeholder directly. When a worker's question is a product decision (scope, a
user-facing behavior, money, a trade-off the docs don't settle):

1. Put it to the stakeholder in the main chat: short context, the options, your recommendation (use
   `AskUserQuestion` for a clear choice).
2. Send the answer back with `reply --id <msg id>`. If it is a real decision, add it to
   `docs/decisions.md` so the next agent doesn't ask again.

This is how the PM "asks permission": it raises the question, you bring it to the stakeholder, you pass
the yes or no back.

## Changing course mid-work

- New instruction for a running worker (the stakeholder changed something, or you spotted a gap):
  `orca orchestration send --run $ORCA_RUN --to dispatch:<dispatch id> --subject "..." --body "..."`.
  Example: telling the PM "we run Scrum now: milestones per sprint, points, Priority lines".
- A worker going the wrong way: `orca orchestration worker-stop --dispatch <id>`, fix the issue text, start
  again.
- See what a worker is doing: `orca orchestration worker-read --dispatch <id>`.

## Cleaning up

When a worker sends `worker_done`: `scripts/finish-worker.sh <dispatch>` (terminal closed, worktree kept
for fixes). When its PR merges: `scripts/cleanup-wt.sh <worktree>`. Reviewers: `finish-worker.sh <id> rm`
right after their verdict. The sidebar should only show agents that are working right now.
