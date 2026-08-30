# Methodology: personal agents packaged as plugins

Distilled from converting the **finance-tracker** (August 2026) into a self-contained, shareable, auto-updating agent. This is the canonical way to build, package, and share my Claude agents.

## 1. What an agent is here

An agent = **a folder that is both a git repo and a Claude plugin**:

- A `CLAUDE.md` that orchestrates (context, rules, skill catalog, bootstrap).
- Skills under `skills/`, one per activity.
- Plugin manifests under `.claude-plugin/` so it installs and updates from the repo.
- A `setup/` folder with everything needed to self-provision (schemas, scripts).
- A `local/` layer (gitignored) holding everything personal to each installation.

## 2. Three-layer architecture (the golden rule)

| Layer | What it is | Where it lives | Shared? |
|---|---|---|---|
| **The engine** | Skills, CLAUDE.md, schema, docs | The repo (everything except `local/`) | ✅ 100% agnostic, zero personal data |
| **The instance** | Per-installation config (project IDs, emails, exports) | `local/` (gitignored) | ❌ Never |
| **The data** | The user's data and personal rules | Their backend (e.g. their Supabase project, `system_prompt` field) | ❌ Each user provisions their own |

**Nothing personal outside `local/` and the backend.** If a skill needs a personal fact (mappings, rules, preferences), that fact lives in the user's configuration (DB or `local/`), never hardcoded in a skill. That's what makes the engine shareable and updatable without dragging anyone's information along.

Repo language: **everything committed to the repo is written in English**. The language the agent speaks to each user is a runtime preference (config / `system_prompt`); literal user trigger phrases and output examples stay in the users' language because they are data, not documentation.

## 3. Standard repo layout for an agent

```
my-agent/
├── CLAUDE.md                  → orchestrator (see §7)
├── README.md                  → what it is, zero-command install, update cycle
├── config.example.json        → template for the local config
├── .gitignore                 → local/ and dist/
├── .claude-plugin/
│   ├── plugin.json            → { name, description, version, author }
│   └── marketplace.json       → { name, owner, plugins: [{ name, source: "./" }] }
├── skills/
│   ├── <agent>-setup/         → guided zero-command onboarding (see §6)
│   └── <activity>/SKILL.md    → one skill per activity
├── setup/
│   ├── schema.sql             → if there's a DB: full schema for self-provisioning
│   └── package-skills.ps1     → packages zips (frozen fallback only)
└── local/                     → personal layer, NEVER in git
    └── config.json
```

## 4. Distribution: plugin tied to the repository

Two possible modes; **the standard is the second**:

1. **Zip (Upload plugin)**: uploaded once, frozen, no updates. Only for edge cases.
2. **Tied to the repository** ✅: the plugin is associated with the GitHub repo with automatic sync — every push updates the skills in every installation.

Installation per surface (flow verified live):

| Surface | How | Update after a push |
|---|---|---|
| **claude.ai** (covers web **and** mobile) | Customize → Plugins → Add → Add marketplace → *Add from a repository* → pick the repo → enable **Sync automatically** → Sync → Browse tab → **Add** | Automatic |
| **Claude Code** | `claude plugin marketplace add <owner>/<repo>` + `claude plugin install <plugin>@<marketplace>` | `claude plugin update <plugin>` (or `git pull` if the marketplace points at a local folder) |

Known gotchas:
- Private repo on claude.ai → **"Repository not accessible"**: the user clicks **"Install the Claude GitHub App"** and grants it access to the repo (Only select repositories). That click is always the user's.
- Installing the plugin on claude.ai replaces same-named account skills; manually remove any leftovers (Customize → Skills → ⋮ → Remove).
- The owner maintains with: edit → commit → push. Nothing else.

## 5. Sharing

- **The unit of sharing is the repo**: giving someone the agent = inviting them as a collaborator (private repo) or making the repo public.
- The repo contains nothing personal (layer 1), so sharing it exposes nothing.
- Each person provisions their own backend with the setup skill; data never crosses.

## 6. Zero-command onboarding (the `*-setup` skill pattern)

Installation is designed for **non-technical people**. Guiding principle of the setup skill:

> The user does NOT run commands or edit files. Everything executable is executed by Claude. The user is only asked for the clicks that require their identity (creating accounts, signing in, authorizing), guided step by step, waiting for confirmation at each one.

Setup skill structure:
1. **Phase 0 — Silent diagnosis**: detect what's missing (local config, plugin, connectors, accounts) and skip what's already done. Idempotent.
2. **Accounts** (GitHub, backend): guide their creation with links and simple steps. **Claude never asks for or types passwords.**
3. **Repo access**: the user sends their username to the owner → invitation → accept.
4. **Plugin**: Claude runs the commands (Claude Code) or performs the clicks (claude.ai) — see §4.
5. **Backend**: Claude creates the project, applies `setup/schema.sql` as a migration, seeds defaults, creates the user, writes `local/config.json`. It only asks the human questions (name, email, currency…).
6. **Verify and first use**: one verification call + one example first use.

**Assisted-browser mode**: when a browser is available, Claude opens the pages and performs the clicks itself, **handing control to the user** exactly at the login/authorization steps. If the user gets lost, ask for a screenshot and guide them from what they see.

## 7. The agent's CLAUDE.md

It must declare:
- What the agent is and what it is NOT (removed legacies, canonical sources).
- The three-layer architecture and the "nothing personal outside local/ and the backend" rule.
- **Multi-surface session bootstrap** (critical so it works the same in the folder, as a plugin, on web and mobile):
  1. If `local/config.json` exists in the working directory → use it.
  2. Anywhere else (claude.ai, mobile, Claude Code via plugin in another folder) → Claude memory; if missing, ask once and save.
- Skill catalog (activity → skill table).
- Conventions (formats, confirmations, where generated files go).

## 8. Personalization without touching the engine

The user's personal rules live in THEIR configuration (e.g. a `system_prompt` field in their DB, loaded by every skill at bootstrap). Examples: merchant mappings, language, categorization rules. One skill of the agent (`*-settings`) manages them. The engine never changes because of one person's preferences.

## 9. Own repo or index repo? (decision criteria)

A marketplace can host **multiple plugins** (subfolders, `source: "./<folder>"`), so an agent has two possible homes:

**Its own repo** when any of these hold:
- Deep setup: its own backend, schema, provisioning (e.g. finance-tracker with Supabase).
- Different audience/privacy: access is granted per repo — sharing the repo shares EVERYTHING in it.
- Its own release cadence or high blast radius (a push to a mono-repo updates every plugin for everyone synced).

**Inside the index repo (`Ntobon/agents`)** when:
- It's lightweight: just CLAUDE.md + skills, no backend of its own.
- It shares its audience with the other agents in the index.
- It changes rarely or its blast radius is low.

The index repo always also plays the **catalog** role: it lists every agent (wherever it lives) with its link and install instructions.

## 10. Checklist: converting an existing agent to this format

- [ ] Audit the current folder: separate engine / instance / data.
- [ ] Pull EVERYTHING personal out of skills and CLAUDE.md → move it to `local/` or the backend (`system_prompt`).
- [ ] If there's a DB: extract the real schema (tables, functions, indexes, constraints) into a self-contained `setup/schema.sql`.
- [ ] Rewrite each skill's bootstrap to the multi-surface pattern (§7).
- [ ] Remove dead dependencies (old sync mechanisms, abandoned services) from the code AND the accounts.
- [ ] Create `.claude-plugin/plugin.json` + `marketplace.json` (or register the subfolder in the index marketplace).
- [ ] Write the zero-command `*-setup` onboarding skill (§6).
- [ ] README with install, layers, and update cycle.
- [ ] `.gitignore`: `local/`, `dist/`.
- [ ] Translate any repo content to English (§2); keep user trigger phrases/examples in the users' language.
- [ ] git init/commit with the personal identity (`Ntobon` / gmail) → push.
- [ ] Install the plugin on claude.ai (Sync automatically) and in Claude Code; remove old duplicate account skills.
- [ ] Register the agent in the index repo's catalog.
