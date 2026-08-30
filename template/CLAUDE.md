# <Agent name> — <what it is>

<Short description of the agent and its domain.>

**Three-layer architecture**: the engine (this repo, 100% agnostic) / the instance (`local/`, gitignored) / the data (the user's backend). Golden rule: **nothing personal outside `local/` and the backend** — the user's personal rules live in their configuration, never hardcoded in a skill.

Repo language: everything committed here is in English. The language the agent speaks is a runtime user preference.

## Session bootstrap (required before operating)

1. If `local/config.json` exists in the working directory → read it.
2. Anywhere else (claude.ai, mobile, Claude Code via plugin in another folder) → look for the config in Claude memory; if missing, ask once and save it.
3. No config anywhere → offer the `<agent>-setup` skill.

<If there's a backend: one context call per conversation, cache it, and treat the user's personal rules as session instructions.>

## Skills

| Skill | When |
|---|---|
| `<agent>-setup` | Install/provision a new instance |
| `<activity>` | <triggers> |

## Conventions

- <Formats, confirmations, language.>
- Files generated for the user go in `local/exports/`.
