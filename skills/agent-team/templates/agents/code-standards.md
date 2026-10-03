# Code standards

Every agent writes clean code by today's industry standards. Tools check most of it in CI; the Reviewer
checks the rest. Code that is hard to read gets `REVIEW: CHANGES_REQUESTED` even when it works.

## Enforced by tools (CI fails)

- <Language> in its strictest mode: <compiler flags>.
- <Linter> with its strictest preset, zero warnings. A rule is turned off only in config, with a comment
  saying why, never inline.
- <Formatter> for formatting. Nobody argues about formatting in a review.
- Conventional Commits for PR titles. PRs are squash-merged, so the title becomes the commit message.
- Dependencies pinned by the lock file. No new dependency without a reason in the PR body.

## Checked by the Reviewer

- **Names** say what a thing is or does, using the words in `GLOSSARY.md`. No `data`, `info`, `tmp`.
- **Small units:** a function does one thing. Long functions, deep nesting and boolean flag parameters
  are findings.
- **Clear boundaries:** validate input at the edge, trust types inside. No business logic in route
  handlers or UI components.
- **Errors** are never swallowed. Expected failures are typed results; unexpected ones are logged once, at
  the edge.
- **No dead code**, no commented-out code, no `TODO` without an issue number.
- **Comments** explain why, not what.
- **No magic values:** named constants for timeouts, limits and sizes.
- **Tests** prove behavior through public interfaces, not implementation details.
