# Agents — index and agent factory

Catalog of my Claude agents, the [methodology](METHODOLOGY.md) to build and share them, and the [template](template/) to start a new one. This repo is also a **plugin marketplace**: lightweight agents live here as subfolders; agents with deep setup live in their own repo and are referenced from this index.

## Catalog

| Agent | What it does | Where it lives | Status |
|---|---|---|---|
| **finance-tracker** | Personal finances on Supabase: natural-language expense tracking, recurring payments, card statements, reports | [Ntobon/agentic-finance-tracker](https://github.com/Ntobon/agentic-finance-tracker) (own repo — deep backend & provisioning) | ✅ Packaged, in production |
| **compras** | Purchase research: multi-angle search, real verification, value matrix, shareable HTML comparison | [`compras/`](compras/) in this repo | ✅ Packaged |
| **salud** | Personalized printable health reports (PDF) per family member, age-adapted, Colombian EPS context | [`salud/`](salud/) in this repo | ✅ Packaged |

## Installing an agent

Every agent installs as a **plugin synced to its repository** — it updates itself on every push. For non-technical people: open the agent's folder in Claude and say **"quiero instalarlo"** / "install this"; the setup skill guides everything with zero commands. Per-surface details (claude.ai / Claude Code) are in [METHODOLOGY.md §4](METHODOLOGY.md).

To install the agents living in THIS repo:
- claude.ai: Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → Add.
- Claude Code: `claude plugin marketplace add Ntobon/agents`, then `claude plugin install <agent>@ntobon-agents`.

## Sharing an agent

Invite the person to the corresponding repo (or make it public). The repos contain nothing personal — three-layer architecture: shareable engine / gitignored local instance / data in each person's own backend. See [METHODOLOGY.md §2 and §5](METHODOLOGY.md).

## Creating a new agent

1. Copy `template/` (as a subfolder here if lightweight, or as its own repo if it will have a backend — criteria in [METHODOLOGY.md §9](METHODOLOGY.md)).
2. Follow the checklist in [METHODOLOGY.md §10](METHODOLOGY.md).
3. Register it in this README's catalog and, if it lives here, in `.claude-plugin/marketplace.json`.
