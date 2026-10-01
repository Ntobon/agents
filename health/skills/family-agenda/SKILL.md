---
name: family-agenda
description: Creates or updates a patient's "family agenda", a published claude.ai artifact with a shared database and two views — the administrative errands numbered in priority order, each with an owner, and the appointments with a month calendar. The family adds, reorders, assigns and closes items from their phones; Claude reads and writes the same rows with no Drive connector. Use when the user asks for "un calendario con las citas", "un tablero de tareas para la familia", "algo para que todos sepamos el cronograma", "asígnale esto a…", "actualiza la agenda", "qué gestiones faltan", or when a relative asks in the chat for a calendar or a shared to-do list.
---

# Family agenda (errands + appointments)

A **simple** board for whoever runs the patient's paperwork, and so the whole family knows the appointments. A tool, not a report: two tabs, few words, **light** theme by default with a button to switch to dark.

> Language note: the page template (`assets/plantilla.html`) keeps its Spanish interface, identifiers and placeholder names, the same convention as `imaging-3d`'s scripts — the families using this agent read Spanish, and copying the file as-is keeps the local and mirrored versions in sync.

## What goes in and what does not (hard rule)

- **In:** administrative errands (request and confirm appointments, authorizations, filings, receipts, orders to reconcile) and the appointments with date, time, place and who goes along.
- **Out, even if it sits in `TAREAS.md`:** anything clinical (vitals, symptoms, medications, priority consultations, urgent appointment requests, questions for the doctor — the person running the clinical side handles those directly), anything about expenses, payments or settlements, anything from the legal front (tutela, appeals, contempt), and stale items with no clear action. Root policy on family plans: the board is seen by other relatives and carries no strategy.
- **Less is more:** at most 5-8 open errands when seeding. Anything that is not a concrete action for the errand runner stays in `TAREAS.md`.
- **Each errand:** a title starting with a verb (≤ 10 words), at most a one-line note (the authorization or filing number it needs), an owner and, if any, a due date.

## Configuration (lives in the context, never in the skill)

In the patient's `CLAUDE.md`, section **"Agenda familiar"**: the artifact URL, the people who may own items (only those who actually run errands; ask when unsure), who runs errands by default, and the patient's short name for the title. If the section does not exist, create it on first publish.

## Create (first time)

1. Read the patient's `CLAUDE.md`, `TAREAS.md`, `00 Índice general.md` and errands log; pick errands and appointments per the rule above. Appointments come from archived documents or confirmations (folder 05), with date and time exactly as recorded.
2. Copy `assets/plantilla.html` to `<Patient>\00 Agenda y tareas de la familia.html` (living document, fixed name) and replace the placeholders:
   - `{{TITULO}}` board name, 2-4 words (e.g. "Agenda de <short name>").
   - `{{EYEBROW}}` mono line above the title (e.g. "Familia · <short name>").
   - `{{CLAVE}}` stable key for local storage (e.g. `agenda-<short-name>`); never change it later.
   - `{{PERSONAS_JSON}}` JS array of possible owners, errand runner first (e.g. `['Ana', 'Luis']`).
   - `{{RESPONSABLE_GESTIONES}}` default owner of a new errand.
   - `{{PACIENTE}}` how rows name the patient.
   Check that no `{{` remains.
3. Publish with the Artifact tool: `capabilities: {"db": {}, "user": {}}`, `icon: "calendar"`, a one-line description. The artifact starts private: tell the user to share it from the Share menu with the relatives who edit (Contributor or above), never by public link.
4. Seed with `ArtifactData` in **one `batch`**:
   - `config/equipo` → `{"personas": [...]}` (same list as step 2).
   - `items/<id>` per row. Errand: `{tipo:"tarea", titulo, fecha:"YYYY-MM-DD"|"", hora:"", lugar:"", responsable, nota, estado:"pendiente", orden:1..n, prioridad:"alta"|"media", paciente, creado, actualizado}`. Appointment: `{tipo:"cita", titulo, fecha, hora:"HH:MM", lugar, responsable (who goes along, or ""), nota, estado:"pendiente", paciente, creado, actualizado}`. Readable, stable ids: `t-<topic>` for errands, `c-<topic>` for appointments.
   - `orden` is the priority: 1 = do first. Near due dates and items that block others (an authorization without which there is no appointment) go on top.
5. One functional check: `ArtifactData list items` with `as_level: "view"` must return the rows. Look once at the local HTML in the browser (no console errors). Say in one line what was exercised and what was not.
6. Archive and register: the HTML stays in the patient's folder (root policy on HTML reports); a line in `00 Índice general.md`; the "Agenda familiar" section in the patient's `CLAUDE.md`; artifact registration per the global instructions.

## Update

- **Read before writing:** `ArtifactData list items` — the family edits rows (closes, reorders, adds). Their changes win; do not revert them.
- Always write with `if_version` (the version read) and in a `batch` when several rows change.
- An errand Claude sees fulfilled in the archive (authorization arrived, appointment assigned): `update` with `estado:"hecha"`; if it produced an appointment, create the appointment.
- New confirmed appointment: create it; if its date changes, `update` the same row (never duplicate).
- What the user asks to remove gets deleted, and if the exclusion is a whole kind of topic, note it in the "Agenda familiar" section of `CLAUDE.md` so it does not come back.
- Design changes: edit the patient's file and republish to the same URL **without** passing `capabilities` (they are kept). Never change `{{CLAVE}}` or the row shape without migrating existing rows.

## The page (what the template does)

- **Gestiones:** list numbered by `orden`; ▲▼ to reorder, ✎ to edit, "Hecha ✓" to close (closed ones fold below). "+ Gestión" button (assigned to the default errand runner).
- **Citas:** a band with the next appointment, the upcoming list with a large date, who goes along and place; month calendar with appointments marked; "+ Cita".
- Without a database connection (file opened from Drive or WhatsApp) it shows explained empty states; the data only lives in the published artifact.
- View-only viewers do not see edit controls.
- No `alert`/`confirm` (the viewer blocks them): deleting asks for a second tap.

## Check before delivering

- [ ] Zero clinical, expense or legal rows; ≤ 8 open errands; titles start with a verb; one-line notes.
- [ ] Owners only from the configured list; the default errand runner owns the errands that are theirs.
- [ ] Appointments with date and time exactly as in the archived document.
- [ ] Light theme by default; no `{{` in the published HTML; `node --check` of the script passes.
- [ ] A read with `as_level: "view"` returns the rows.
- [ ] HTML archived in the patient's folder, index and `CLAUDE.md` updated, artifact registered.
