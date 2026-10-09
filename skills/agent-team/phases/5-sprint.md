# Phase 5: Run the sprint

Goal: every sprint issue merged through the gate, with nothing left running or lying around.

```sh
export ORCA_RUN=run_... SPRINT="Sprint N" SCRUM_ISSUE=<n>
S=~/.claude/skills/agent-team/scripts
```

## The loop

1. **Pick** the top `ready-for-agent` issue of the sprint whose `Blocked by` issues are all closed.
2. **Start** it: `sh $S/wait-load.sh && sh $S/start-worker.sh <role> <issue> <slug>`.
3. **Wait** in the background: `sh $S/wait-msg.sh`. On a message, ack it
   (`orca orchestration check --run $ORCA_RUN --ack <deliveryId>`). A question: answer with
   `orca orchestration reply --id <msg id>`; ask the stakeholder only for scope or product decisions.
4. **Release** on `worker_done`: `sh $S/finish-worker.sh <dispatch>` (the worktree stays for fixes).
5. **Review**: `sh $S/start-review.sh <pr> <issue>`, then wait.
   - `REVIEW: APPROVED`: `sh $S/finish-worker.sh <reviewer dispatch> rm`, then merge.
   - `REVIEW: CHANGES_REQUESTED`: start a fixer with the same role on the same branch
     (`start-worker.sh <role> <issue> <slug> "Continue branch <b>. Fix the findings in the latest REVIEW
     comment on PR <pr> and reply there."`), then `start-review.sh <pr> <issue> b`.
6. **Merge**: `sh $S/queue.sh <pr>` in the background, then `sh $S/cleanup-wt.sh <worktree>`. It runs
   `scripts/merge-gate <pr> --update`. While GitHub Actions can't run, turn on
   `mergeGate.localCiOnUpdate` in `agent-team.json` (or `export AGENT_TEAM_LOCAL_CI=1`): the gate then
   runs `scripts/local-ci` on the head itself. Never merge any other way.
7. **Report** to the stakeholder in a few lines: merged, running, next. Collect non-blocking review notes
   in a list; they become issues in refinement.
8. Once in a while: `git worktree list`. Anything whose PR is merged or closed goes.

**Shortcut for steps 5, 6 and the next 2:** after releasing a worker, run
`sh $S/review-merge.sh <pr> <issue> <worktree> -- <role> <next issue> <slug> ["extra"]` in the
background. It reviews, merges on `REVIEW: APPROVED`, cleans up, starts the next worker and waits for its
message. On a question or `CHANGES_REQUESTED` it stops and prints the message: answer the question and
run it again with `RESUME=1`, or start a fixer as in step 5.

## When more than one agent runs

`review-merge.sh` assumes one agent. Once the stakeholder allows more (say 3 agents and 1 local CI),
run the loop by hand:

- Keep **one** `wait-msg.sh` in the background and handle each message yourself: ack, release
  (`rm` for reviewers), then the next step (review, fixer, `queue.sh` or a reply). Start a new waiter
  after each one; a waiter started with a plain `&` is not tracked, so stop it by PID.
- Start each agent behind `wait-load.sh <cores>` and tell implementers to run only their own package's
  tests while working, the full suite once at the end.
- Run one `queue.sh` at a time. Chain the next merge behind the running gate:
  `while ps -eo command | grep -q "[m]erge-gate <pr>"; do sleep 20; done && sh $S/queue.sh <next>`.
- Gate chains with `&&`, not `;`, so a refused merge doesn't start the next worker.
- A new commit on an approved PR needs a new review. The gate only carries an approval over a merge of
  `main`.

## When the agents hit a usage limit

Workers stop mid-task and may leave a worktree half done (say, mid-rebase) with a handoff note. After the
limit resets:

1. Rebind the run: `orca orchestration run-use --id $ORCA_RUN`.
2. Check each running dispatch for progress (PR comments, commits). Release the stalled ones and start
   them again; a reviewer just starts over.
3. For a half-done fixer, keep its worktree, copy its handoff note somewhere stable and start a new fixer
   on the same branch that reads the note first.

## When the stakeholder adds a rule

During a sprint the stakeholder will say things like "clean code by industry standards", "issues depend
on each other", "component-based frontend with file suffixes", "close agents after merge". Each one:

1. Write it into the docs at once (`CLAUDE.md`, a role file, `code-standards.md`, `rules.txt` or
   `agent-rules.md`), so every new agent gets it.
2. Tell the running workers with `send --to dispatch:<id>` if it changes their current work.
3. Confirm to the stakeholder in one line where it now lives.

## When local CI fails

- Every commit status names its job's log (strip colors with `sed 's/\x1b\[[0-9;]*m//g'`).
- `error` (not `failure`) means the machine broke, not the PR: a job exited with 75 (say, its container
  never got ready) or the run was stopped. Fix the machine and run `queue.sh` again; the gate runs local
  CI again on its own. With Docker down, local CI posts nothing and says so.
- `error` with "slept": the machine went to sleep during the job. Keep it awake and run `queue.sh` again.
- A failure in a test the PR doesn't touch counts as flaky only after two checks: the test doesn't run
  code the PR changed (a shared helper can break it), and it passes alone on `main`. Otherwise it goes
  back to the author. Flaky: file a priority-1 bug at once, then retry **once** on a quiet machine with
  `RERUN=1 sh $S/queue.sh <pr>` (plain `queue.sh` re-reads the old failure). Fails again: fix the bug
  first, then retry.
- Never weaken a test to get a PR in. QA tests stay strict and merge after the bugs they catch are fixed.

## When the machine gets loud

Find the process (`ps -Ao pid,pcpu,etime,command -r | head`), stop only what you or an agent started (by
PID), and add a rule to `rules.txt` or the project's `agent-rules.md` so it doesn't happen again.
