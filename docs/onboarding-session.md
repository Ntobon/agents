# Team onboarding session: install the health agent, seed it, demo it

A two-hour hands-on session for a team that will install the **health** agent on their own computers, populate it with the fictional demo family, run the small use cases, and leave able to demo it to a prospect. Facilitator: the agent's owner. Attendees: 3 to 8 people, each with their own laptop.

## Before the session (the day before)

Send this checklist; each item is the attendee's own click, Claude cannot do it for them:

1. A Claude account with **Claude Code** access, signed in on the **Claude desktop app** (the Code tab must be visible next to Chat). Nobody opens a terminal at any point.
2. **Google account + Google Drive for Desktop** installed and syncing (the drive letter or `~/Google Drive` visible).
3. **Python 3.10+** with `pymupdf opencv-python numpy pillow pypdf` (`pip install ...`), and **Node 18+**. Only needed for local sessions: scanning, paginating and merging PDFs, building the health report.
4. Windows: **Microsoft Word** (PDF export of the health report). macOS/Linux: LibreOffice. Without either, the report is delivered as `.docx`.
5. Nothing to clone: the repo `Ntobon/agents` is public and the plugin installs from it.

## Agenda (120 minutes)

| Block | Minutes | Outcome |
|---|---|---|
| 1. What it is | 10 | Facilitator demo on the demo family: one photo archived, one package produced. The three layers explained. |
| 2. Install | 25 | Every laptop has the plugin, a health root in Drive, and has run "quiero instalarlo" to the first heartbeat. |
| 3. Seed the demo family | 15 | "puebla el sistema con la familia de ejemplo": one archived member plus an inbox of two documents. |
| 4. Use cases | 40 | Each attendee runs at least four of the seven use cases below on their own machine. |
| 5. Surfaces | 15 | Facilitator shows the same folder from the phone (Drive connector) and the scheduled audit. |
| 6. Sales script | 15 | The five-minute pitch, the objections, and who will run the first prospect demo. |

## Block 2: install (zero commands, everything from the Code tab)

1. Create the root folder in Drive (e.g. `Salud\`) and mark it available offline.
2. Open the Claude desktop app, **Code** tab, *Open project*, pick that folder.
3. Paste this message in the chat and approve the permission prompt(s) that show the command Claude is about to run:

   > Instala el plugin health del marketplace Ntobon/agents (repositorio público de GitHub) y confírmame la versión instalada.

   Click alternative: type `/plugin` in the chat → Marketplaces → Add → `Ntobon/agents` → Discover → health → Install.
4. In the same chat say **"quiero instalarlo"**. The `health-setup` skill takes over: Drive integration, root `CLAUDE.md` from the template, weekly audit, first-document heartbeat. For claude.ai (web and mobile): Customize → Plugins → Add marketplace → *Add from a repository* → `Ntobon/agents` → Sync automatically → Add, plus the Google Drive connector.

After the owner pushes a change, ask in the chat: *actualiza el plugin health* (claude.ai syncs on its own).

## Block 4: the seven use cases (phrase → visible result)

| # | Say | What appears |
|---|---|---|
| 1 | "archívame los laboratorios que están en la bandeja" | raw copy in `06 - Originales\2026\`, renamed PDF + transcription in `03 - Laboratorios`, a third column in the trend table, pending 2 closed in the index |
| 2 | "archiva el informe de la ecografía" | report in `04 - Imágenes diagnósticas`, pending 1 closed, the order in folder 05 marked as done |
| 3 | "hazme el informe de salud de Papá" | plain-language PDF in `01 - Informe de salud` (docx kept as source) |
| 4 | "el paquete para el control con medicina interna" | one paginated PDF: facts-only summary + curated annexes, signed order as scan |
| 5 | "mi tablero de Papá" | private mobile-first HTML dashboard, archived in the folder and published |
| 6 | "quiero agregar un nuevo miembro: Camila" | the owner's folder with the full pattern and her `CLAUDE.md` |
| 7 | "organiza la carpeta" (or run the scheduled audit) | the audit report in `00 Auditorías\` |

Optional: "¿hay ensayos clínicos para la diabetes tipo 2 en Colombia?" (clinical-trials skill, family-only material).

## Block 5: surfaces

Google Drive is the backbone. Local Claude Code reads the mounted, offline-enabled folder; claude.ai web, the mobile app and Cowork sessions read and write the same folder through the Drive connector, even with the computer off; scheduled tasks run the weekly audit. Sync contract: cloud wins on doubt, `(1)` duplicates are name clashes, every incoming document is archived so any session finds it.

## Block 6: the five-minute pitch

1. The problem: a family's medical documents live in WhatsApp threads, email and paper; nobody can answer "what did the last labs say" in a waiting room.
2. Demo 1 (1 min): a photo of a lab result sent from the phone lands archived, transcribed and in the trend table.
3. Demo 2 (1 min): "the package for tomorrow's appointment" produces one paginated PDF the doctor can navigate.
4. Demo 3 (1 min): the private dashboard on the phone.
5. The three layers: the engine is shared and agnostic; the family's context and documents never leave their own Drive.

Objections that come up: privacy (nothing personal in the engine; data stays in the family's Drive), "what if Claude is wrong" (never invents clinical data, cites file and date, every document says it does not replace the doctor), cost (a Claude subscription and a Google account), "do I need a computer" (no: the cloud surfaces work alone; local sessions add PDF tooling).
