---
name: imaging-3d
description: Turns a diagnostic imaging study (CT or MRI DICOM, as a folder or .zip) into three things, all locally — an own reading focused on one concrete question (what the image shows and what it cannot, with slices and approximate measurements), a 3D model in Blender (stills and a turntable video) and a single-file interactive 3D viewer that explains the disease to the family: where the lesion is and how big, what it would look like without it, how contents pass through a narrowing, how it grows, what the treatment does and what surgery removes and leaves. Use when the user says "analiza el DICOM", "mira el TAC / la resonancia tú mismo", "haz un modelo 3D", "dónde está el tumor", "simula cómo pasa la comida", "hazme un visor", "explícame la cirugía en 3D" (or the English equivalents), or when a decision depends on something the images could show and the report does not say.
---

# Imaging in 3D: from DICOM to a viewer that explains

## What it is for

A radiology report answers what the radiologist chose to answer. The family arrives with other questions: "does food get through?", "where exactly is it, and is it big?", "what will they remove, and how will it end up?". With the DICOM on disk you can do three things:

1. **Look at the study with one concrete question.**
2. **Rebuild the anatomy in 3D.**
3. **Turn each of the family's questions into a view, an animation or a card** in an interactive viewer.

The viewer becomes the tool the family uses to understand the disease and to prepare what they will ask the doctors.

The skill is **agnostic**: CT or MRI, any organ, any pathology. Everything case-specific (patient, question, recipes, colours, texts) lives in the patient's context files and in the deliverable's folder, never here.

**Priority order:** first the answer to the question (steps 0-4, with 1-3 slices in the case dashboard), then the model. While Blender renders in the background, keep working on the dashboard; don't wait.

**Language note:** the scripts are shared verbatim with the Spanish-language instance of this agent. They keep Spanish identifiers, CLI verbs, JSON keys and comments, and the viewer UI is in Spanish, because the families it serves read Spanish. The file contracts are documented in the references.

## Hard limits

1. **Everything stays local.** DICOM, volumes, masks and renders never leave the machine: no third-party web viewers, no cloud segmentation services.
   - If the study is only on a portal, the user downloads it and does the login.
   - Research subagents get de-identified questions (age, sex and generic diagnosis; never name or ID).
2. **An own reading is not a report.** Looking at slices, segmenting or measuring gives a private, approximate assessment: thresholds, partial volume, a single contrast phase.
   - It is for understanding and for asking better questions.
   - It never goes into the medical record, the medical package or any document for doctors as if it were a finding.
   - When it changes a decision, it goes to a radiologist or the treating team as a concrete question.
3. **Segmented and drawn are always distinguishable.** Some anatomy is drawn to complete the picture: a collapsed segment, an organ that isn't visible, the reconstruction after surgery. The legend marks it "drawn", not "from the study".
4. **No identifiers in the images or in the copy that circulates.**
   - Slices are rendered from the array, without the text the scanner burns into the image; PACS screenshots are cropped.
   - The viewer needs no name or ID.
   - The share copy carries the minimum identifiers.
5. **Nothing is published or shared without an explicit request.** The artifact is published private, and sharing it is the user's call.
6. **Permanent disclaimer** in the viewer and in every document: informational, it does not replace the treating doctor.
7. **Every clinical number has a source and context.** This covers typical sizes, growth speed, treatment response and survival.
   - Write "out of every 100…".
   - Say these are group data, not a deadline or a prognosis for one person.
   - Flag it when the patient's subtype differs from the study population.

## Inputs

- **The study.** The DICOM, as a folder or a `.zip` exported from the portal, usually in `06 - Originales\<year>\`. Also the reports of the study and of related studies (endoscopy, ultrasound, pathology): read them first, to know what each one said and didn't say.
- **The question.** What needs to be understood or decided. Without a question the model is decoration; if it isn't clear, ask.
- **The audience.** The user (private version), the family (plain language) or a trusted doctor (share copy).

## The flow

All heavy work goes in a **work folder outside Drive**: the session scratchpad. Volumes weigh hundreds of MB and are health data. Drive keeps only the deliverables and the configuration needed to regenerate them.

### 0. Context

Read the patient's `CLAUDE.md` and `00 Índice general.md` and the reports, and note three things:

- what the report said;
- what it didn't say;
- what each other source saw, and how. Direct vision (endoscopy) doesn't weigh the same as a static image.

### 1. Series

```
python scripts/dicom_series.py listar "<zip or folder>"
python scripts/dicom_series.py cargar "<zip or folder>" --serie <N> --salida "<work>"
```

Pick the thinnest axial series with contrast and full coverage. For MRI, the sequence where the target shows best.

`volumen.json` stores no identifiers.

### 2. Look before segmenting

1. `scripts/cortes_qa.py montaje` (with a coordinate grid) and `reformat` (coronal or sagittal) to find the region.
2. `muestrear` to read HU or intensities and check seeds and ranges.
3. **Answer the concrete question here, with slices**: is there a lumen? how big is it? what does it touch?
4. Save 1-3 cropped slices for the case dashboard.

### 3. Segment

1. Write a JSON recipe starting from `scripts/recetas/`. Thresholds by modality and phase are in `references/segmentation.md`.
2. Run `segmentar.py`.
3. Check with `cortes_qa.py superponer`.
4. Fix and repeat until every mask matches the slices.

**Hollow organs and wall lesions:**

- `trazar_luz.py ruta` traces the lumen by air or contrast. Where the lumen collapses, give it waypoints.
- `manga` extracts the wall or lesion around the lumen.
- `medir` gives length × thickness and the minimum lumen.

### 4. Own reading

What the image shows, what it cannot show and how certain that is, compared with the other sources. Example of that contrast: air in the lumen on CT does not say whether the wall distends; endoscopy saw that directly.

If a doubt that matters remains: **3-5 concrete questions for a radiologist**, each with series and slice number so they can find it in a minute.

The reading goes into the case dashboard and the deliverable's `00 Léeme.md`, never into the clinical folders 02-05.

### 5. Model

1. `mallas.py` builds the meshes from the style file. Colour rules are in `references/blender-model.md`.
   ```
   blender -b -P scripts/blender/mallas.py -- --trabajo "<work>" --estilo estilo.json --salida modelo.blend
   ```
2. `render.py` renders one still per camera and the turntable video for WhatsApp.
3. `glb.py` exports the web model with its `centros.json`.

### 6. Viewer

1. Start from the skeleton:
   ```
   python scripts/visor/armar_visor.py --glb modelo.glb --esqueleto visor.json --estilo estilo.json
   ```
   It inherits the Blender palette: one palette for stills, video and viewer. `--listar` gives each node's centre and size, for views and hotspots.
2. Complete the configuration:
   - views, hotspots and modes;
   - the route (`"archivo": "ruta.json"` from `trazar_luz.py`) with its `estrechez`;
   - the modules that apply: flow, stages, resection;
   - the content tabs and the glossary.
3. Build both variants with `armar_visor.py`: the private one and `--variante compartir`. The builder validates the config against the GLB and writes nothing if there are errors.
4. Run `probar_visor.py` **from the PowerShell tool**.
5. Look at the screenshots of every mode, in both themes and at narrow width.

Technical detail in `references/viewer.md`; what content goes in, in `references/explaining.md`.

### 7. Archive and publish

See "Deliverables".

### 8. Iterate with the questions

Every new question from the user becomes a permanent block of the viewer (view, mode, animation or card). Then:

- republish to the same URL;
- regenerate the share copy with every version.

The questions that are known to come are in `references/explaining.md`: version 1 should already answer most of them.

## Adapting to the case

**By modality**

| Modality | What changes |
| --- | --- |
| Contrast CT | Absolute HU. The phase rules: measure the aorta and the portal vein to tell arterial, portal or delayed, and adjust the ranges. |
| Non-contrast CT | No enhancement: vessels ≈ muscle. Segment fewer structures and draw more. |
| MRI | No absolute units; normalise by percentiles. Pick the sequence per structure: T2 for fluid and walls, contrast T1 for what enhances, diffusion for cellularity. Local seeds and ranges, more manual review. Sometimes segment on one sequence and show another (same geometry). |
| PET-CT | CT gives the anatomy; PET would be a heat layer in SUV. **Not implemented**: say so. |
| Ultrasound, X-ray, endoscopy | Not volumes. They enter as 2D images in the dashboard, next to the model. |

**By type of problem**

| Problem | What to segment | Viewer modules | Typical questions |
| --- | --- | --- | --- |
| Narrowing of a hollow organ (GI tract, bile duct, ureter, airway) | Lumen (air or contrast), thickened wall (`manga`), neighbours | flow · tube stages · resection | Does it get through? What if it closes? How does it end up afterwards? |
| Mass in a solid organ (liver, kidney, pancreas, lung, brain) | Organ, lesion and nearby critical structures (distances) | scale stages · plane resection | How big is it? Does it touch anything important? What part is removed? |
| Vascular (aneurysm, stenosis) | Contrast lumen: `trazar_luz ruta` with a contrast criterion, diameters along it | tube stages · repair as a new tube | How much does it grow per year? When is it operated on? |
| Bone (fracture, lesion, osteoporosis) | Bone with a bone window; implants cause metal artefacts | resection or fixation | Where is it? What gets fixed? |
| What another test saw and the study doesn't show | Nothing: draw it | — | Label it "drawn from <source>" and say the study doesn't show it. |

## Deliverables

One folder inside the patient's folder:

```
<Patient>\<YYYY-MM-DD> Modelo 3D de <study>\
├── 00 Léeme.md                        what it is, the question, the own reading and its limits, how to regenerate
├── Visor 3D.html                      private version (the user's)
├── Visor 3D (para <doctor>).html      share copy, only if requested
├── 01 <view>.png … 0N <view>.png      renders
├── giro_completo.mp4 · giro_detalle.mp4
├── <Model>.blend
└── scripts\                           the case's concrete configuration: recipe, style, cameras, visor.json, tabs, glossary
```

- **Archive first, publish after.** The `.html` is saved in the folder before it is published as a private artifact. Updates are republished **to the same URL**, kept in the patient's `MEMORY.md`. The MP4s are published as supporting files of the artifact.
- **Share copy.** Its own banner, its own `localStorage` prefix, and no private tabs. The video tab goes when the HTML will travel on its own: the MP4s aren't inside the file and are sent separately. Sharing it is the user's call.
- **Context.** One line per deliverable in the patient's `00 Índice general.md`, and the URL in their `MEMORY.md`. If the environment has an artifact registry (the user's global instructions), register the published viewer and the local files.
- **Clinical decision.** If the question led to a decision, the case dashboard is built with `internal-html-dashboard` and embeds the key slices and renders.
- **Document for doctors.** If one is needed on the topic, it goes through `medical-record-package`: documented facts only, without the own reading or the model.

## Check before delivering

- [ ] The question is answered on the first screen (dashboard or Explore tab), with its certainty and its limits.
- [ ] Every mask passed the `superponer` review; the lesion's extent was checked slice by slice against the report.
- [ ] Own measurements say "approximate" and sit next to the report's when they exist (if they differ, give both).
- [ ] Orientation: in the front view, the patient's left is on the screen's right and the head is up; sides are named from the patient.
- [ ] The legend is unambiguous:
  - one colour, one meaning;
  - the lesion has the only saturated colour;
  - drawn parts are marked.
- [ ] Every mode was tested in headless screenshots: zero JS errors, both themes, narrow width.
- [ ] Without JS, the viewer shows every section and the tabs work as anchors.
- [ ] Every clinical number has a source and an explanation; survival numbers say they are group data.
- [ ] The share copy is regenerated, with the right banner, no private tabs and minimum identifiers.
- [ ] Each HTML weighs < 16 MB. The GLB grows ×1.33 as base64.
- [ ] Everything was archived in the patient's folder before publishing. Index and `MEMORY.md` are up to date. The configuration is in the deliverable's `scripts\`.

## Known pitfalls

**Windows and tools**

- **Launch headless Edge only from the PowerShell tool.** From Bash it doesn't write files.
  - Use `Start-Process -Wait`, a fresh `--user-data-dir` for every run, and `--use-angle=swiftshader --enable-unsafe-swiftshader` for WebGL.
  - The minimum headless window width is ~500 px.
- The app's built-in browser can't open large Drive files: test with headless Edge or by publishing.
- Write `.py` scripts with the Write tool, not heredocs.
- In Python, build Windows paths with `os.path.join` or `chr(92)`: `"\2026"` is an octal escape.
- Read CRLF files with `newline=''`. Write shared files (the index) atomically.
- The PowerShell tool may block long commands as a false positive: split them.

**Segmentation**

- Smooth (3×3×3) before thresholding: without it, erosion wipes out noisy masks and the seed falls outside.
- Segment first the organ that sticks to a neighbour, then subtract it (e.g. spleen before kidney).
- If an organ leaks into its neighbour: narrow the range and erode more.
- Check every seed with `muestrear` before growing.

**Blender**

- Always run in background mode.
- Before the turntable, call `scene.timeline_markers.clear()`: markers bound to cameras freeze the rotation.
- Convert hex colours from sRGB to linear.
- 1 unit = 1 cm.

**three.js**

- `color.convertSRGBToLinear()`: without it, colours look washed out.
- The camera tween uses `performance.now()` with a clamp: with the rAF timestamp, the camera flies away in headless.
- `renderer.localClippingEnabled = true` for the resection cuts.
- `depthWrite: false` on transparent layers.
- Hotspot text changes per mode.
- **Comparison alignment.** The "without lesion" lumen comes from the same route indices as the diseased segment; otherwise it looks longer or shifted.
- In the "after surgery" modes, hide what no longer exists: the air of the resected segment, the removed organ.
- **Slow animations.** About 6.5 s per stage, with «Etapa X de N» in the caption; the first, faster version couldn't be read.

**PDF and artifacts**

- In PDF captions made with PyMuPDF, use an ASCII hyphen, not the Unicode minus (it prints "?").
- Artifacts: 16 MB limit. Same `file_path` = same URL. Videos go as supporting files.

## References and scripts

| File | What it is |
| --- | --- |
| `references/explaining.md` | What content the viewer carries: the questions that always come, the tabs, how to present evidence and numbers, and how the original viewer was refined. |
| `references/segmentation.md` | Choosing the series, windows, review workflow, recipe schema, HU ranges by tissue and phase, MRI, lumen, wall and measurements. |
| `references/blender-model.md` | Meshes, style and colours, cameras, video and the GLB budget. |
| `references/viewer.md` | Viewer architecture, config schema, modules (flow, stages, resection), build, share copy and tests. |
| `scripts/coords.py` | The shared coordinate conventions (voxel ↔ LPS ↔ Blender ↔ glTF) and a command-line converter. |
| `scripts/dicom_series.py` · `cortes_qa.py` · `segmentar.py` · `trazar_luz.py` | The chain DICOM → volume → review → masks → lumen, wall and measurements. `morfologia.py` holds the operations they share (dilate, erode, grow, components), in pure numpy. |
| `scripts/recetas/` | Starting segmentation recipes (thresholds get tuned to the case; seeds always do). |
| `scripts/blender/` | `mallas.py`, `render.py`, `glb.py`, with example style and cameras. |
| `scripts/visor/` | `plantilla.html`, `armar_visor.py`, `probar_visor.py`, a fictional example and `demo/crear_demo.py`. |
