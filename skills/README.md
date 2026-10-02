# Skills

General-purpose skills that are not tied to one agent. They work in any project and any folder.

## Installation

Installs from the `Ntobon/agents` marketplace:
- **claude.ai** (web + mobile): Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → Add.
- **Claude Code**: `claude plugin marketplace add Ntobon/agents` + `claude plugin install skills@ntobon-agents`.

## Catalog

| Skill | What it does | Try it with |
|---|---|---|
| [`artifact-ux`](skills/artifact-ux/SKILL.md) | Design system for every HTML artifact or page: a tool, not a document (tabs), a mandatory TL;DR on top, few words and big visuals, glossary tooltips, light/dark toggle, zero shadows, WCAG AA contrast. Includes a [reference dashboard](skills/artifact-ux/references/glance-board.html). | "hazme una página comparando X y Y", "mejora el diseño de este HTML" |

## Credits

`artifact-ux` is distilled from `molt-web-artifacts-builder`, itself derived from Anthropic's [`web-artifacts-builder`](https://github.com/anthropics/skills) (Apache-2.0).
