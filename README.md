# ai

My AI setup, shared: skills, plugins and agent configs for Claude Code and other coding agents.

```
skills/     one folder per skill, each with a SKILL.md (works with `npx skills`)
plugins/    Claude Code plugins (coming)
agents/     agent and subagent configs (coming)
```

## Install a skill

With the [skills](https://www.npmjs.com/package/skills) CLI:

```sh
npx skills add mberatsanli/ai --list                 # see what's here
npx skills add mberatsanli/ai --skill agent-team     # install one
```

Or by hand: copy or link `skills/<name>` into `~/.claude/skills/<name>`.

## agent-team

Build a project with an autonomous agent team through Orca, from the
first idea to merged sprints, the Scrum way:

1. **Intake:** grill the idea into docs (`CLAUDE.md`, architecture, decisions, roadmap with an MVP done list).
2. **Team setup:** role files, skills for each role, code standards, labels, CI, a merge gate, an Orca run.
3. **Backlog:** a Project Manager agent splits the work into epics and tickets.
4. **Sprint planning:** goal, order, capacity, roles.
5. **Run the sprint:** one implementer at a time, an Opus reviewer on every PR, merges only through the gate.
6. **Review and retro:** a QA demo, a human review freeze, and lessons turned into rules.

It keeps the machine quiet (one agent and one CI run at a time by default) and cleans up every worktree
it no longer needs.

What's inside:

- `SKILL.md` and `phases/`: what the coordinator does in each phase, and `phases/orca.md`: how every role runs as its own Orca worker and how questions reach the stakeholder through the coordinator.
- `templates/agents/`: team, Scrum, issue tracker, code standards and role files (PM, backend, frontend,
  DevOps, QA, UX, reviewer, researcher), each naming the skills that role uses.
- `scripts/`: shell scripts for the loop: start a worker or a reviewer, wait for messages, release and
  clean up, merge PRs in a queue, wait for a low load.

You bring your own `scripts/merge-gate` (and `scripts/local-ci` if GitHub Actions can't run). The setup
phase says what they must do.

### Needs

- Orca with orchestration, `gh`, `git`, `python3`, a POSIX shell.
- The role skills it names (`tdd`, `implement`, `pr`, `to-spec`, `to-tickets`, `triage`, `grilling`,
  `research`, `codebase-design`), installed in the project.

## License

MIT
