# Rules every role follows

- Read `CLAUDE.md`, `GLOSSARY.md`, [team.md](../team.md) and your role file before anything else.
- Work only on the issue you were given: `gh issue view <N> --repo <owner/repo> --comments`.
- Start from the latest `origin/main` on a branch named `<role>/<issue-number>-<slug>`.
- Edit only the folders the issue's **Ownership** line gives you. Anything else: ask the coordinator.
- Shared contracts (`<spec folder>`) belong to the coordinator unless your issue says otherwise.
- Use the skills your role file names. They are in `.claude/skills/`.
- Test first. Red, green, refactor. Only tests that prove real behavior.
- Write clean code that follows [code-standards.md](../code-standards.md).
- Before opening the PR: typecheck, lint (zero warnings), format check and tests pass locally. Run the full
  suite once, at the end, never in parallel with other heavy work.
- Only the coordinator runs local CI, posts commit statuses or merges.
- Don't start an issue whose `Blocked by` issues are still open. A missing dependency: stop and ask.
- PR title in Conventional Commits. One PR per issue, body with **What**, **Why**, **How I proved it**,
  and `Closes #N`. No attribution trailers or tool footers.
- Blocking questions go to the coordinator with Orca's `ask`. Don't guess on contracts or architecture.
- Code, comments and docs in plain English.
- Finish with `worker_done` (three sentences, the PR URL, `--outcome succeeded` or `failed`). Then stop.
