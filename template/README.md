# <Agent name>

<One sentence: what this agent does and for whom.>

## Installation (zero commands)

1. You get access to this agent (folder or repo) and open it in Claude.
2. Say: **"install this"** (or "quiero instalarlo") → the `<agent>-setup` skill guides everything. You only create accounts and authorize with clicks; Claude runs the commands.
3. Try it with: <example first use>.

## The three layers

| Layer | Where it lives | Shared? |
|---|---|---|
| The engine (skills, CLAUDE.md, setup) | This repo | ✅ |
| Your instance (config) | `local/` (gitignored) | ❌ |
| Your data | <your backend> | ❌ |

## How it updates

Plugin tied to the repository with Sync automatically: every push updates the skills in every installation. See the methodology in the index repo `Ntobon/agents`.

## What it can do

| You say | Skill |
|---|---|
| <typical phrase> | <skill> |
