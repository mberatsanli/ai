# CLAUDE.md

This repo shares an AI setup: skills, docs, scripts, plugins and agent configs for Claude Code and
other coding agents. Others install from it, so everything here is a published artifact, not a
personal scratch space.

## Layout

```
skills/<name>/    one folder per skill; SKILL.md at its root (installable with `npx skills`)
plugins/          Claude Code plugins (planned)
agents/           agent and subagent configs (planned)
docs/             write-ups and guides that aren't part of a skill (create when needed)
```

A new kind of thing gets its own top-level folder. Add it to the layout block in `README.md` when it lands.

## Skills

- `skills/<name>/SKILL.md` starts with frontmatter: `name` (same as the folder) and `description`.
  The description says when to use the skill and lists trigger phrases. It decides whether the skill
  loads, so write it for the matcher, not for a human browsing.
- Keep `SKILL.md` short and route to detail files (`phases/`, `references/`, `templates/`) that the
  agent reads only when it needs them.
- Everything a skill uses ships inside its folder: scripts, templates, tests. A skill must not depend
  on files elsewhere in this repo, because it is installed alone.
- Name every external tool and skill it depends on, with an install command, in its `README.md`.
- A skill with code ships tests for that code next to it (`skills/<name>/tests/`).

## agent-team

The one skill so far. Shell scripts in `scripts/`, a Python merge gate and local CI in
`templates/scripts/` (Python 3.9+, standard library only, no packages). Tests run the scripts as
commands against a fake `gh` and recorded GitHub data in `tests/fixtures/`:

```sh
python3 -m unittest discover -s skills/agent-team/tests
```

Run them after any change to `templates/scripts/` or `tests/`. A new merge-gate case gets a fixture
folder (see `tests/fixtures/README.md`).

## Writing

- English for everything in the repo: skills, docs, comments, commits.
- Plain, short sentences. Say what a thing does and when to use it. No marketing words.
- Paths and commands in backticks. Examples must run as written.

## Commits

Conventional Commits with the skill as scope: `feat(agent-team): ...`, `fix(agent-team): ...`,
`docs: ...` for repo-wide changes. Subject in imperative, lower case, no trailing period.

## Install check

After a new or renamed skill is pushed, confirm it is listed (this reads GitHub, not the local tree):

```sh
npx skills add mberatsanli/ai --list
```
