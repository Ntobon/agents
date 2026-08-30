---
name: <agent>-setup
description: Guided zero-command onboarding for <agent> — walks a non-technical person through accounts, plugin install tied to the repository, backend provisioning, and local config. Use when the user says "quiero instalarlo", "install this", "instalar", "setup inicial", or when another skill of this agent can't find its configuration.
---

# <Agent> Setup — guided onboarding (zero commands for the user)

## Guiding principle
**The user does NOT run commands or edit files.** Everything executable is executed by Claude. The user is only asked for the clicks that require their identity (creating accounts, signing in, authorizing), guided step by step, waiting for confirmation at each one. Claude **never** asks for or types passwords. When a browser is available, Claude can perform the clicks itself and hand control to the user at the login/authorization steps; if the user gets lost, ask for a screenshot and guide them from what they see.

**Idempotent**: in Phase 0 detect what's already done and skip it.

## Phase 0 — Diagnosis (silent)
- Does `local/config.json` exist and does the backend respond? → already installed; show config and exit.
- Plugin installed? Required connectors connected? Accounts created?
- Present the map: "We'll do N things: … I'll guide you through each one."

## Phase 1 — Accounts and repo access
1. Do they have a GitHub account? If not → guide them to create one (github.com/signup).
2. Ask for their username → the owner invites them to the repo → accept the invitation.

## Phase 2 — Install the plugin tied to the repo
- **Claude Code** (Claude runs it): `claude plugin marketplace add <owner>/<repo>` + `claude plugin install <plugin>@<marketplace>`.
- **claude.ai** (covers web and mobile): Customize → Plugins → Add → Add marketplace → *Add from a repository* → pick the repo → enable **Sync automatically** → Sync → Browse → **Add**. If "Repository not accessible" appears → "Install the Claude GitHub App" (the user's click).

## Phase 3 — Backend and connectors
<Guide the backend account creation and connector connection in Claude. Claude verifies with a listing call.>

## Phase 4 — Provision (Claude does everything)
<Create the project/resource, apply `setup/schema.sql` as a migration, seed defaults, create the user. Only ask the human questions.> Finally, write `local/config.json` (explain that `local/` is private and never shared).

## Phase 5 — Verify and first use
<Verification call + one example first use.>

## Error handling
- Connector not connected → return to the corresponding phase; don't continue without it.
- Plugin install fails on permissions → check the repo invitation / the GitHub App.
- Provisioning fails halfway → inspect what got created and continue piecewise.
- The user gets lost on a web step → ask for a screenshot and guide from what they see.
