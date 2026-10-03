# Phase 4: Sprint planning and assignment

Goal: a milestone `Sprint N` with a goal and an ordered list of ready issues, each with its role.

## Steps

1. The PM (an agent on a "Plan Sprint N" issue, or you with the PM's ranking) proposes the **Sprint
   Goal** and the top of the backlog.
2. Check each issue against the **Definition of Ready** (`docs/agents/scrum.md`): task spec format,
   no Ownership overlap unless chained, checkable Acceptance, dependencies listed, labels `points:*`,
   `role:*`, `wave:*`, `ready-for-agent`, and the milestone.
3. **Capacity.** One agent at a time on a quiet machine (or what the stakeholder allows). Plan points
   from the last sprint's velocity, not hope.
4. **Order.** A `Priority: N` line at the top of each issue body. Blockers of other issues and bugs that
   break `main` come first. Group small issues that touch the same screen or folder so one agent does them
   in one PR.
5. **Assignment.** The `role:*` label is the assignment: it picks the role file and skills the agent
   gets. Create the milestone with the goal in its description and put the issues in it.
6. Show the stakeholder the goal and the list in a short table. Start phase 5 on their yes.
