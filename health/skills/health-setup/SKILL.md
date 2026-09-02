---
name: health-setup
description: Guided zero-command onboarding of the family health system for a new family — Google Drive integration (desktop app, offline mode, Drive connector so cloud sessions read/write the same archive), root folder and root CLAUDE.md from the template, plugin install tied to the repository, the weekly archive-audit routine, and a live verification with a first document. Also seeds the fictional demo family for learning and demos. Use when the user says "quiero instalarlo", "install this", "monta el sistema de salud", "configurar el agente de salud", "puebla el sistema con la familia de ejemplo", "seed the demo family", "quiero probarlo con datos de ejemplo", or when another skill of this agent can't find a health folder that follows the pattern.
---

# Health Setup — guided onboarding (zero commands for the user)

Mounts the complete family health system. When it finishes: a health folder in Google Drive following the documentary pattern, readable and writable from **every surface** (local Claude Code, claude.ai web, mobile), with the weekly audit scheduled.

## Guiding principle
**The user does NOT run commands, create folders, or edit files.** Claude executes everything executable and creates every folder and file. The user only does the clicks that require their identity (installing apps, signing in, authorizing connectors), guided step by step. Claude **never** asks for or types passwords. With a browser available, Claude performs the clicks and hands control to the user at login/authorization steps.

**Idempotent**: Phase 0 detects what already exists and skips it.

## Phase 0 — Diagnosis (silent)
- Does a health folder following the pattern already exist (root CLAUDE.md with "Quién es quién")? → already mounted; offer `add-family-member` or the audit instead.
- Is Google Drive for Desktop installed and syncing? Is the Drive connector available in cloud sessions? Is the plugin installed?
- Present the map: "We'll do 4 things: Google Drive, the folder, the plugin, and the weekly routine."

## Phase 1 — Google Drive integration (the storage backbone)
The archive lives in Google Drive so the SAME files are available to every surface:

1. **Google account**: if they don't have one, guide its creation (accounts.google.com). Never handle their password.
2. **Google Drive for Desktop** (for local Claude Code work): guide the install (google.com/drive/download), sign-in, and locating the mounted drive (e.g. `G:\My Drive\`).
3. **Create the root folder** (e.g. `Salud\`) — Claude creates it via the file system once Drive is mounted.
4. **Mark it "Available offline"** in Drive (right-click → Offline access) — guide the click. This makes local sessions robust to connectivity.
5. **Connect the Google Drive connector** in the Claude app (Settings → Connectors → Google Drive → authorize — the user's click). This is what lets **cloud sessions (claude.ai web/mobile) read and write the same archive via the Drive API, even with the computer off**.
6. Explain the sync contract (it's root policy 10 of the template): cloud is the source of truth on doubt; `(1)` duplicates after a sync are name clashes — keep the newest under the canonical name; every document arriving by chat/phone/email gets archived per the pattern so any session finds it.

## Phase 2 — Root context from the template
1. Create the root `CLAUDE.md` from [templates/CLAUDE.root.template.md](../../templates/CLAUDE.root.template.md): fill the owner's name/email and the "Quién es quién" table conversationally (ask who the family members are — name, ID, birth date, relationship, insurer). This is **context**, personal by design — it lives in the family's folder, never in the agent.
2. Create empty `MEMORY.md` and `TAREAS.md` with their headers.
3. For each member named now, run the `add-family-member` flow (Phase's sibling skill) — or leave it for later; members can be added any time by just asking.

## Phase 3 — Install the plugin tied to the repo
Same pattern as the methodology (see the index repo):
- **Claude Code** (Claude runs it, the user never types a command): `claude plugin marketplace add Ntobon/agents` + `claude plugin install health@ntobon-agents`. In the Claude desktop app's Code tab the user just asks in the chat ("instala el plugin health del marketplace Ntobon/agents") and approves the permission prompt; the click alternative is `/plugin` → Marketplaces → Add → `Ntobon/agents` → Discover → health → Install.
- **claude.ai** (web + mobile): Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → **Add**. If "Repository not accessible": "Install the Claude GitHub App" (the user's click; may require a GitHub account — guide its creation if needed).

## Phase 4 — Schedule the weekly audit
Create a scheduled task on the platform whose prompt is: run the `archive-audit` skill over the whole health folder (reading the root `CLAUDE.md` first). Suggested cadence: weekly; raise to 2-3 times a week during acute clinical phases. Claude creates the task with the platform's scheduling tool; the user only confirms the time slot.

## Phase 5 — Live verification (the system's first heartbeat)
Ask the user for any first document (any lab PDF, even an old one) and archive it end to end: raw to `06 - Originales\<year>\` + renamed copy + transcription + line in the member's index. **If that works, the system is alive.** Then show what they can ask for from now on: "archívame este examen", "hazme el informe de salud", "el paquete para la cita", "mi tablero".

## Demo mode — seed the fictional family (no real data needed)
Trigger: "puebla el sistema con la familia de ejemplo", "seed the demo family", "quiero probarlo con datos de ejemplo", or a user who wants to learn or demo the agent before having real documents. Everything in [demo/](../../demo/README.md) is invented (people, doctors, IDs, values), so it can be shown to anyone.

1. Locate the plugin's `demo/` folder (next to `skills/` in the installed plugin) and copy `demo/family/` into the user's Drive as `Salud (demo)\` (or inside their real health root if they already have one, as a sibling of the real members — never inside a real member's folder). Copy `demo/inbox/` next to it as `Bandeja de entrada (demo)\`.
2. Do not edit the copied files beyond the Drive path line in the root `CLAUDE.md`; the folder is already consistent (index, trend, pendings).
3. Say what is there and what to try, in this order: archive the two inbox documents (each closes a pending), generate the health report, the medical package, the dashboard, then add a member. The full list is in `demo/README.md`.
4. When the user is done: offer to delete `Salud (demo)\` and the inbox; nothing else references them. A demo folder never mixes with a real family's audit or reports.

## Error handling
- **Drive not mounted locally**: the cloud-only mode still works (connector); note that local sessions need Drive for Desktop and continue.
- **Connector not authorized**: return to Phase 1.5; cloud sessions can't reach the archive without it.
- **Plugin install fails on permissions**: check repo access / GitHub App grant.
- **User gets lost on a web step**: ask for a screenshot and guide from what they see.
