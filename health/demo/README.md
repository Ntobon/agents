# Demo family (100% fictional data)

A ready-made family health folder to learn, test and demo the agent **without touching anyone's real data**. Every person, doctor, institution, ID number and lab value here is invented; every PDF carries a "DOCUMENTO FICTICIO" notice.

## What is inside

| Path | What it is |
|---|---|
| `family/` | A health root folder ("Salud (demo)") already following the pattern: root `CLAUDE.md` (from the template, filled for the fictional family), `MEMORY.md`, `TAREAS.md`, and one member `Papá\` (Jorge Restrepo Vélez, 71, type 2 diabetes + hypertension) with **4 archived documents**: two lab panels (nov-2025 and may-2026, transcribed, with the trend table), one internal-medicine consult note and one signed ultrasound order. Folders 01 and 04 are empty on purpose (`00 Sin documentos aún.md`), the index carries three open clinical pendings. |
| `inbox/` | **2 raw documents not yet archived**, to be ingested live: the 3-month control labs (20-aug-2026) and the renal ultrasound report (21-aug-2026). Archiving them closes the two open pendings of the index. That is the demo's "before/after". |
| `build_demo_pdfs.py` | Regenerates every PDF (requires `reportlab`). Edit the values there if you want a different story. |

The story is deliberately small and clinically boring: a father whose diabetes improves across two panels, a mildly rising creatinine, an ultrasound that turns out to be a simple cyst. It exercises every mechanism (trend, pending, signed order, closing a pending with an incoming report) without drama.

## How to use it

Ask the agent: **"puebla el sistema con la familia de ejemplo"** (or "seed the demo family"). The `health-setup` skill copies `family/` into your Google Drive as `Salud (demo)\` and leaves `inbox/` next to it as `Bandeja de entrada (demo)\`. Then run the use cases:

1. "archívame los laboratorios que están en la bandeja" — raw to `06 - Originales\2026\`, renamed copy + transcription in `03 - Laboratorios`, third column in the trend table, pending 2 closed in the index.
2. "archiva el informe de la ecografía" — lands in `04 - Imágenes diagnósticas`, closes pending 1, updates the order's state in folder 05.
3. "hazme el informe de salud de Papá" — the plain-language PDF in folder 01.
4. "el paquete para el control con medicina interna" — the paginated facts-only package.
5. "mi tablero de Papá" — the owner's private HTML dashboard.
6. "quiero agregar un nuevo miembro: Camila" — the owner's own folder, created from the template.

Delete `Salud (demo)\` whenever you are done; nothing else references it.
