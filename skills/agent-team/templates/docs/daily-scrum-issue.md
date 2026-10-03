<!-- Title: "Daily Scrum: Sprint N". Label: role:pm. Milestone: Sprint N. Keep it open for the sprint. -->

Every agent adds one comment before it sends `worker_done`, and whenever it is blocked:

```
**<role> #<issue>**
- Done: <what I finished, with the PR link>
- Next: <what I do next, or "nothing, finishing">
- Blocked by: <issue, question or "nothing">
```

The coordinator reads this at each checkpoint, clears blockers, and closes the issue in the sprint
review.
