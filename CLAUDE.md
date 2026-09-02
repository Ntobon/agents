# Agent Builder — agent factory and index

This folder is the `Ntobon/agents` repo: the index of my Claude agents and the place where new ones get built and packaged.

**When working here, the source of truth for the craft is [METHODOLOGY.md](METHODOLOGY.md).** Every creation, conversion, or packaging of an agent follows that methodology: three-layer architecture (shareable engine / instance in `local/` / data in the user's backend), plugin tied to the repository with Sync automatically, zero-command onboarding, and the §10 checklist.

Rules for this folder:
- **Lightweight** agents (CLAUDE.md + skills only) live here as subfolders and are registered in `.claude-plugin/marketplace.json` (`source: "./<folder>"`). **Deep-setup** agents (own backend) live in their own repo and are only cataloged in the README.
- Never put personal data in an agent's engine: it goes in `local/` (gitignored) or in the user's backend.
- **Everything committed to this repo is written in English.** The language each agent speaks is a runtime user preference; literal user trigger phrases and output examples may stay in the users' language (they are data).
- Every new agent starts from `template/`.
- After any change: commit + push (the personal git identity is configured locally in this working copy, never written here), and update the README catalog if the agent list changed.
- Living reference for the full pattern: the [Ntobon/agentic-finance-tracker](https://github.com/Ntobon/agentic-finance-tracker) repo (first converted agent; working copy at `E:\Claude\Finance`).
