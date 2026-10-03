# Phase 6: Sprint review, human review and retro

Goal: show what was built, learn from the stakeholder's eyes, and turn lessons into structure.

## Sprint review

1. A QA agent demos the increment against the Sprint Goal in the real app (an issue "Sprint N demo").
2. Write `docs/sprints/sprint-N.md`: goal, what's done, what isn't and why, points planned vs done,
   PR links. Send the stakeholder the short version.

## Human review (freeze)

When the stakeholder wants to review the product by hand:

- **Freeze:** start no agents and no implementation.
- Make the product easy to run for them (a demo stack on its own ports and database; give exact
  commands that you checked on `main`).
- Turn each finding into an issue right away (`type:ux` or `type:bug`, with Change, Ownership, Acceptance,
  points), or a comment on an existing one. For UX findings, compare how loved products solve it and
  propose that pattern.
- When the review ends, list the issues in a table and propose how they fit into the next sprints. Wait
  for a yes, then unfreeze.

## Retrospective

1. Every agent that worked in the sprint adds what went well, what didn't, and one improvement (start a
   worker on a "Sprint N retro" issue, or collect them from Daily Scrum comments).
2. Add your own: process problems you saw (load spikes, flaky tests, review rounds, stuck merges).
3. **Turn each improvement into structure**, not a note: a role file line, `rules.txt` or
   `agent-rules.md`, a lint rule, a script, a test. Then go to phase 4.
