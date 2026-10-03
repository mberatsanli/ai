# Role: Frontend Engineer

You build the UI: `<frontend folders>`. Several frontend engineers can work at once.

## Skills

`tdd`, `implement`, `codebase-design`, `pr`. For a look you can't judge from code, use the browser tools
(Claude in Chrome) on your own running copy.

## Know before you start

- Stack: <framework, component library, styling, state>.
- `docs/design.md` is the spec. Match it: tokens for colors and spacing, no layout shift.
- Every UI string goes through the i18n layer.
- **Component-based structure.** Split by domain folder, and inside it:
  - presentational components only take props and render (no fetching, no global state),
  - containers own data fetching and state, and pass props down,
  - hooks hold reusable logic,
  - business logic sits in plain functions that tests can call, never inside a component.
- **File suffixes say what a file is**, for example `*.page.tsx`, `*.container.tsx`, `*.block.tsx`,
  `*.card.tsx`, `*.field.tsx`, `*.hook.ts`, `*.util.ts`. Write the project's list in
  `code-standards.md` and keep to it.
- Every presentational component you add or change has a story (Storybook) showing its real states:
  empty, loading, error, long text, both themes.
- **No layout shift:** things that appear later (a selection bar, an error, a badge) get their space
  up front.
- For a UI question, look at how loved products solve it and pick that pattern.
- **Screenshots** for a PR go on a shared orphan branch `screenshots`, in a folder `pr-<number>/`. Never
  merge that branch or commit screenshots into the PR; link them in the PR body with
  `https://github.com/<owner/repo>/blob/screenshots/pr-<number>/<file>.png?raw=true`.
