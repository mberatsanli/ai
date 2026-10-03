# Phase 3: Backlog (the PM splits the work)

Goal: epics and tickets that agents can pick up one by one, covering the whole MVP done list.

## Steps

1. Open an issue for the PM's job, for example "Backlog: split roadmap Phase 1 into issues" (label
   `role:pm`), with the docs to read and the output you expect.
2. Start the PM: `sh scripts/start-worker.sh pm <issue> backlog`. Its role file
   ([../templates/agents/roles/project-manager.md](../templates/agents/roles/project-manager.md)) says
   how to split work: one agent and one PR per issue (half a day to two days), the task spec format,
   labels, `Blocked by`, epics with sub-issues, a QA issue per done-list item, and `needs-info` issues for
   anything unclear in the docs.
3. When it sends `worker_done`, check its report yourself:
   - every done-list item has issues and a QA issue,
   - no two issues in the same wave own the same folders unless chained with `Blocked by`,
   - no dependency cycles,
   - Acceptance can be checked by a test or a command.
   Send findings back as a new PM issue, or fix small ones yourself.
4. Bring the `needs-info` questions to the stakeholder (grilling rounds), record the answers in
   `docs/decisions.md`, and let the PM update the issues.

## Refinement

During a sprint, when the next sprint's backlog is thin, start the PM again on a "Refine Sprint N+1"
issue: split big issues, estimate, clarify, and turn review findings into ready issues.
