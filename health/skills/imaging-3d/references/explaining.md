# What the viewer explains, and how

The viewer is not a pretty model: it is the tool the family uses to understand the disease. **The family's questions drive the content.** Every question that comes in becomes a permanent block (a view, mode, animation or card), not a one-off answer in the chat.

Form rules, inherited from the glance dashboards:

- **Few words, big visuals.** Each card says one thing in ≤ 2 lines.
- **A tooltip on every technical term.** The glossary is the single source.
- **Slow animations.** About 6.5 s per stage, with «Etapa X de N · …» in the caption bar.
- **The 3D scene is the protagonist of Explore.** The other tabs combine buttons that switch the scene to the relevant mode (`data-ver`), SVG drawings and big numbers.
- **Sides are named from the patient.** The patient's left is on the screen's right, as in every radiological image, and the viewer says so.

## The questions that always come (checklist for version 1)

| # | The question, as it arrives | What answers it | Watch out |
| --- | --- | --- | --- |
| 1 | "What is each colour? Is everything in this colour the lesion?" | Legend generated from the config; hotspot 1 = the lesion | The lesion gets the only saturated colour and nothing else is close in hue. One neighbour organ in a nearby hue (violet next to magenta) is enough to confuse. |
| 2 | "Where exactly is it, and how big? Is that area <structure>?" | Hotspot with the measurement (length × thickness, minimum lumen); labels for the landmarks the family names | If the family mixes up two neighbouring regions, say which is which with an arrow. Own measurements say "approx." and sit next to the report's. |
| 3 | "Is that big or small?" | Context with references: the typical range in published series | Make clear that stage depends on depth and extent, not only on size. |
| 4 | "What is the white part? What is narrowing it?" | An explicit sentence: **the lesion is the wall; the white is the lumen**, the space the contents pass through | The hotspot text changes in the without-lesion comparison. |
| 5 | "What would it look like without the lesion?" | A "normal" mode that works like a filter: same view, same framing | The normal lumen comes from the **same route indices**. Otherwise it looks longer or shifted, and the family notices. |
| 6 | "What comes before and after? How does it connect?" | Neighbouring segments drawn and labelled "drawn" | Never pass off drawn anatomy as segmented. |
| 7 | "How does food (bile, urine, air, blood) get through?" | Flow simulation: liquids versus solids | The simulation is honest only when it rests on a physiological fact with a source: which particle size passes, what pressure, what calibre. |
| 8 | "How does it grow? How fast?" | Growth-speed block at the **top** of the tab. Slow stages: inward (the wall thickens, the lumen narrows) and outward (through the wall, nodes) | Published ranges with their variability, never a single number. |
| 9 | "So the danger is that it closes?" | Confirm or correct the family's mental model with the real mechanism | E.g. it does not squeeze from outside: it infiltrates the wall and makes it rigid. |
| 10 | "What does the treatment do? When do we know if it works?" | Response stages (shrinking) + a timeline of when response is assessed | Control imaging versus pathology of the specimen: how reliable each one is. |
| 11 | "Why not do <the alternative> right away?" | The logic of the sequence, with the numbers of the trial behind it, explained | The arguments against it for this patient stay in view. Close with "the sequence is the treating team's decision". |
| 12 | "What do they remove? What decides how much? How does it end up, and how does it work afterwards?" | Surgery tab: "removed" / "remains" modes for each option; side-by-side drawing of the margin logic; reconstruction; nodes; flow afterwards | "Remains" modes hide everything that no longer exists. |
| 13 | "Is it advanced? What stage is it?" | What is known and what isn't until pathology | Separate "advanced by depth" from "spread". Point to the scenarios if a prognosis dashboard exists. |
| 14 | "Send it to me so I can see it on my phone / for the doctor" | Turntable video (WhatsApp) + share copy | The share copy has its own banner and drops the private tabs. |

## Base tabs

| Tab | Contents |
| --- | --- |
| **Explore** | Big scene; layer chips per group; views (front, side, detail); modes (with lesion, without lesion, flow…); numbered hotspots; legend. Answers "where and how big?" in one screen. |
| **How it grows** | Speed first, with sources; animated stages; inward and outward; what is dangerous and why. |
| **Treatment** (under its real name: chemo, radiotherapy…) | What it aims for; how it goes (cycles or sessions on a timeline); when you know if it works; why this order; response stages. |
| **Surgery** | The options; what is removed ("removed") and what remains ("remains"); what decides the extent (margin drawing); reconstruction; nodes; how it works afterwards (flow). |
| **Video** (private) | The turntable MP4s: full and detail. |
| **How to read it** | Full legend; what is segmented and what is drawn; orientation; limits of the own reading; disclaimer. |
| **Glossary** | The single source of the tooltips. |

A tab exists only when it has content for the case: a mass with no surgical indication has no "Surgery" tab.

## Evidence and numbers

- **Research before writing.**
  - Sources: guidelines (international and national societies), the trial behind each approach, and series for the patient's subtype; ≥ 2 sources.
  - Every number is checked against the source text, not against a subagent's summary.
  - Subagents get de-identified questions.
- **Format of a number:** a big number + one line of reading + "Sources:" at the foot of the block (author, journal, year).
- **Decisions:** two numbers facing each other (A > B, A ≈ B). **Time:** a bar or timeline with the references marked.
- **Survival and percentages:** always "out of every 100…", and always "these are group data, not a deadline for one person".
- **Different subtype:** if the patient's subtype or age differs from the trial population, say so in the same block.
- **Critical thinking:** show the other option's arguments too, without tilting the balance with adjectives. The decision belongs to the patient, the family and their doctor.

## Language

- For the user: the real terms, with tooltips. For the family: plain language, in the same calm tone the doctor uses.
- One card, one thing. No ornaments or transition sentences.
- What the image **cannot** say is said too, and certainty is named ("the image shows…, it cannot show…").

## The case dashboard (when the question leads to a decision)

The viewer explains; the dashboard decides. When the own reading changes a course of action (what to eat, what to ask, whom to consult), build a dashboard with `internal-html-dashboard` using this pattern:

- **Answer:** the conclusion, the risks and plan B, on the first screen.
- **Do they know?:** what the team received in writing, and what the report leaves out.
- **Images:** the sources side by side.
  - Each one with what it shows and what it doesn't: the cropped CT slice, the ultrasound, the model render.
  - The specific questions for the radiologist, each with its series and slice number.
- **What to ask for:** what to request from the treating team.

## How the original viewer was refined

The first version had the model, the layers and the hotspots. Each round came from one question from the user and stayed in the viewer:

1. **"Is everything in this colour the lesion?"** A neighbouring organ had a hue close to the lesion's. It was changed to grey-blue, and the unique-colour rule was set.
2. **"Where is it, how big is it, is that area this structure?"** Hotspot with the measurement, anatomical labels, and a clarification of which region is which.
3. **"Is that big or small?"** A context block with references.
4. **"Can we see what comes next? How does food go down? Is the white the structure that widens?"** The neighbouring segments were drawn and the flow simulation was added. The viewer now says explicitly that the white is the lumen.
5. **"An example without the lesion, like a filter."** The normal mode was added.
6. **"In the no-lesion view the white is wider and reaches further."** An alignment bug: the normal lumen is now generated from the same route indices.
7. **"How does it grow? How is the operation — total or partial — and the nodes?"** How-it-grows and Surgery tabs, with removed/remains modes and nodes.
8. **"Food after surgery; what decides total or partial; what the treatment does; growth rates; slower."** Added:
   - post-op flow;
   - the margin drawing;
   - the treatment tab with response stages;
   - the speed block;
   - 6.5 s stages.
9. **"Show the growth speed; when do we know if it responds; why wait if they will operate anyway?"** Speed moved to the top of How it grows. Added the response timeline and "why not operate right away?", with the trial numbers and the counter-arguments.
10. **"Is it advanced?"** A stage answer: what is known and what isn't. A candidate for a permanent block.
11. **"I want to share it with a doctor friend."** A copy with its own banner, no video tab and its own `localStorage`. The user shared it.

**Lesson:** the table above anticipates these rounds. A version 1 that already answers 1-8 saves the user half the iterations. Whatever the new case adds goes into that table.
