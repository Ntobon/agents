---
name: eps-status-package
description: Builds the "EPS package" — the administrative status-of-proceedings document to circulate to the health insurer (EPS) or its case managers, for any patient in the family health folder. A factual summary of filing numbers (radicados), authorizations, orders, and appointments with their states, plus annexes that are already inside the insurer's circuit, merged into one PDF that can be forwarded verbatim to an insurer coordinator. Use when the user asks for "paquete para la EPS", "estado de gestiones", "los radicados", "un PDF para el gestor/coordinador de la EPS", "cómo van las autorizaciones (para enviar)", or when an external case manager asks for filing numbers or process status.
---

# EPS status package (proceedings status for the insurer)

## For whom and why

The reader is **administrative**: an insurer coordinator, an IPS scheduler, or a case manager inside a network hospital. The document must work **forwarded verbatim to the insurer** — always assume it will end up there, even when the immediate recipient is a trusted manager. Therefore:

1. **It is as objective as a clinical record.** Facts: filing numbers, authorization numbers, procedure codes (CUPS), dates, states. No editorializing ("the missing piece", "what matters most"), no added context beyond what is necessary, no adjectives.
2. **Zero family strategy.** Nothing like "the family wants / proposes / can pay privately to speed up", no legal-action mentions (tutela), no leverage arguments (e.g. priority-classification discrepancies). All of that lives in the management log and management files (the "family plans never contaminate" root policy, extended to insurer-facing documents), never here.
3. **States are written as the insurer/IPS lives them**, not as the family interprets them: "authorization not yet issued", "the IPS has no schedule availability", "no date assigned", "in process (response due by N)". Confirm every state with the user before recording it — the family's reading and the real administrative state often differ.
4. **Every blocked item is chained to its exact administrative cause**: if labs cannot be scheduled because their authorization has not been issued, the row says so and cites the filing number that covers them. The reader sees where the delay sits inside their own system — that traceability is the document's strength.
5. **No AI mentions**, no generated-report mentions.

## Names and personal data

- **The only proper name in the title and filename is implicitly the patient's** (via the folder it is archived in). The filename carries NO names of managers, relatives, or recipients: `AAAA-MM-DD Estado de gestiones EPS <insurer>.pdf` (date = cut-off date).
- Inside the document only these appear: the patient (name, ID, contract, clinical-record number), professionals and institutions **as they appear in the insurer-circuit documents** (the physician who signs an order is a fact), and the **appointments contact defined in the patient's or root context files** — never other family phone numbers.

## Inputs

- **Patient:** from the working folder or context; ask if ambiguous.
- **Cut-off:** today unless another is requested.
- **Sources:** the patient's management log (folder 05), the order-status files, the patient's `CLAUDE.md` (insurer, contract, clinical-record number), and the original receipts in folders 02-06. Root policy: no number or date is invented — everything traces to a document.

## Summary structure (max 2 pages)

1. **Header:** patient, ID, insurer, contract/plan, clinical-record number, cut-off date, and the line that the supporting documents are annexed in this same PDF.
2. **Filings and authorizations** — table: number · what it is (service, who originated it, annex reference) · date · administrative state (with the response deadline and where it is checked, when applicable).
3. **Open orders, state one by one** — table: # · CUPS · service · state at cut-off. Scheduled items with date, time, venue, and appointment code; blocked items with their blocking filing number; delay facts stated cold (e.g. "N days after the order").
4. **Pending critical result** (pathology, specialist concept, etc., if applicable): what it is, filing number, estimated date, and which order depends on it — all as facts.
5. **Studies already performed** that appear in the institutional clinical record — table: study · date · where, citing the annex of the record that transcribes them.
6. **Annex index** with the exact page where each one starts.
7. **Fixed footer:** the appointments contact (as defined in context) + "Los números y fechas provienen de los documentos anexos y de los comprobantes originales."

## Annexes: insurer circuit only

Only documents **already inside the insurer's circuit** are annexed: the network institution's clinical record, the signed orders issued through the insurer, the insurer's filing and approval receipts, assigned-appointment confirmations, and the patient's ID document.

**Documents from the private (out-of-pocket) track are NEVER annexed** — they invite "this doesn't belong in this process". Those studies **count** because the network institution transcribed them into its clinical record — the summary lists them citing that annex, it does not attach them. If a key private study has not yet been transcribed into the institutional record, flag that to the user as a pending errand (take it to a network consult), don't annex it.

Rules inherited from the medical package (`medical-record-package`): signed documents go as scans, never transcriptions; every page normalized to portrait letter 612×792 (scale and center with pypdf, never rotate); the annex index is computed in two passes (count annex pages → generate the summary with the references → verify the summary's page count didn't change).

## Delivery and archiving

- **One single PDF**: summary + annexes merged. Deliver it to the user and archive it in the patient's folder with its **source next to it** (`.md` with the summary's content — never a PDF without a source).
- **The same day**, record it in the patient's management log: what was delivered, whom the user will send it to, and any new state that surfaced in the conversation.
- If the document is corrected (states, new facts), regenerate **over the same canonical name** — no version suffixes.

## Verification before delivering

- [ ] Zero occurrences of: the family as an actor with plans, legal-action mentions, manager/relative names, editorializing, AI mentions.
- [ ] Every state was confirmed with the user and is written as an administrative state, not an interpretation.
- [ ] Every blocked item cites the filing/authorization that blocks it.
- [ ] No annex comes from the private track; private studies are cited via the institutional record.
- [ ] The annex index points to the real pages of the merged PDF (verify at least two).
- [ ] Every page measures 612×792 (portrait letter).
- [ ] The filename is `AAAA-MM-DD Estado de gestiones EPS <insurer>.pdf`, with no third-party names.
