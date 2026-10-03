# Phase 1: Intake (idea to docs)

Goal: a shared understanding with the stakeholder, written down so agents can work without asking them.
No code in this phase.

## Steps

1. **Grill.** Use the `grilling` skill (rounds of numbered questions, each with your recommended answer).
   Cover: who uses it and why, the core flows, what is out of scope, stack, hosting, data and security,
   licensing, how it makes money (if at all), and what "done" means for the first version.
   Find facts yourself (a sub-agent can read code or docs); ask the stakeholder only for decisions.
2. **Research** what you don't know (libraries, how similar products solve it) with the `research`
   skill or a Researcher agent. Write findings to `docs/research/<topic>.md`.
3. **Show, don't only tell.** For a UI product, build a clickable mockup (an Artifact page) and settle
   the layout, density and key components with the stakeholder. For each UI question, research how
   loved products solve it and propose that pattern. Draw the architecture (D2 or Mermaid diagrams).
4. **Write the docs**, in plain English (around B2 level, short sentences):
   - `CLAUDE.md`: what the project is, the rules that never change, the stack, how we work, the planned
     layout, and links to the docs below.
   - `docs/architecture.md`: the pieces, how data flows, security.
   - `docs/decisions.md`: numbered decisions, each with the reason. Every later decision goes here too.
   - `docs/roadmap.md`: phases, the MVP scope, and an **MVP done list** of checkable items (each becomes
     a QA issue later), plus open questions.
   - Optional: `GLOSSARY.md` (domain words), `docs/design.md` (UI), a protocol or API doc.
5. **Confirm.** Show the stakeholder the summary and the done list. Phase 1 ends only on their yes.
