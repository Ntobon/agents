# 3D viewer: architecture, configuration and tests

A single `.html` the family opens on a phone: the 3D model with layers, views, numbered points and modes, plus content tabs. Everything case-specific lives in the configuration and the tab files. The template is generic and is not edited per case.

## Files (`scripts/visor/`)

| File | What it is |
| --- | --- |
| `plantilla.html` | The generic viewer, with placeholders the builder fills. The config schema is commented at the top. |
| `armar_visor.py` | Validates the config against the GLB, assembles the tabs and writes the HTML (private or share copy). |
| `probar_visor.py` | Headless screenshots of every mode (desktop and 375 px), both themes, the tabs and the no-JS page, with the JS errors. |
| `config-ejemplo.json` · `pestanas-ejemplo.html` · `glosario-ejemplo.html` · `video-ejemplo.html` | A fictional example that uses every module. `[COMPLETAR: …]` marks where the case's evidence goes. |
| `demo/crear_demo.py` → `demo.glb`, `demo-centros.json`, `demo-ruta.json` | The example's synthetic anatomy, built in Blender. |

## Flow

```
python armar_visor.py --glb modelo.glb --esqueleto visor.json --estilo estilo.json   # starter config with the Blender palette
python armar_visor.py --glb modelo.glb --listar                    # centre and size of every node (for hotspots and views)
python armar_visor.py --glb modelo.glb --config visor.json --pestanas pestanas.html --glosario glosario.html \
       [--video video.html] [--poster render.jpg] --salida "Visor 3D.html"
python armar_visor.py … --variante compartir --salida "Visor 3D (para <doctor>).html"
python probar_visor.py --visor "Visor 3D.html" --salida <screenshots folder>    # from PowerShell
```

With `--estilo` (the same `estilo.json` used by Blender), the skeleton inherits names, colours, alpha and groups: one palette for stills, video and viewer. It puts envelopes, nearly transparent layers and bone in `foco_ocultar`. Without `--estilo` it uses the colours of the known keys and a neutral palette with no violets or reds.

The example is built the same way with `--glb demo/demo.glb --config config-ejemplo.json --pestanas pestanas-ejemplo.html --glosario glosario-ejemplo.html --video video-ejemplo.html`. To regenerate the synthetic anatomy: `blender -b -P demo/crear_demo.py`.

## Page architecture

- **Tabs are anchors** (`<a href="#panel-x">`). Without JS the page stays stacked and navigable (WhatsApp and email previewers, QuickLook).
  - The `oculto` class is added by the script, never shipped in the HTML.
  - Without JS the 3D stage shrinks to a short notice, and a `<noscript>` shows the list of numbered points and the colour legend.
- **Light theme by default**, with a visible ☀/☾ button, saved in `localStorage` (inside `try/catch`) under `prefijo_storage`. The 3D stage is always dark.
- **Glossary.** `<dl id="dicc">` is the single source. Every alias in `data-terms` gets a tooltip on every occurrence. It runs in a separate script, so it works even if the 3D fails.
- **three.js r147 (UMD)** from jsdelivr (`three.min.js`, `OrbitControls.js`, `GLTFLoader.js`).
  - It is the only external service.
  - The GLB is embedded as base64 and loaded with `GLTFLoader.parse`.
  - System fonts only; no Google Fonts.
  - Without internet the 3D shows a notice and the rest of the page works.
- **Coordinates** (`scripts/coords.py`): glTF with +Y up, 1 unit = 1 cm, +X = the patient's left (screen right in the front view), +Z forward. The "patient's right / left" labels are projected and hidden in side views or when they cover a number.
- **Nodes without materials.** The viewer colours them from the config with `MeshStandardMaterial` and `color.convertSRGBToLinear()`. Transparent layers get `depthWrite: false` and are drawn from smallest to largest (or by `orden`).
- **Route.** The lumen route is densely sampled on **one** centripetal Catmull-Rom, with parallel-transport frames.
  - Everything placed on the route comes from those same samples: drawn tubes, the normal lumen, stages, cuts and particles. That is why the "without lesion" comparison sits exactly on the diseased stretch.
  - `crear_demo.py` uses the same formula, so the GLB meshes match the viewer's tubes.
- **Hooks:** `window.__modo3d(id)` (used by every `[data-ver]`), `window.__avanzar(sec)` and `window.__visor3d` (mode, view, flow, theme, tab, freeze, state). `probar_visor.py` uses them.

## Configuration (summary)

The detail is in the comment at the top of `plantilla.html` and in the example's `_doc` fields.

| Key | Defines |
| --- | --- |
| `titulo`, `subtitulo`, `eyebrow`, `banner`, `pie` (+ `<field>_compartir`) | Header and footer, plain text. |
| `prefijo_storage`, `explorar_titulo` | `localStorage` prefix; label of the first tab. |
| `estructuras[]` `{k, n, c, a, g, d, con, emis, orden, oculta, leyenda, tubo}` | One per GLB node (`k` ASCII = node name). `tubo {desde, hasta, radio}` or `{puntos, radio}` creates a **drawn** structure that isn't in the GLB. |
| `grupos[] {id, n}` · `foco_ocultar[]` | Chip and legend groups. `foco_ocultar` is what switches off in "Only what matters", in the detail view, and in modes or flows with focus. |
| `vistas {id: {n, dir, objetivo, radio, foco, boton}}` · `vista_inicial` | Camera: direction from the target (`[x,y,z]`, a key or `"ruta:N"`) and the radius to frame (`distFit`). `boton:false` = a view used only by modes. |
| `hotspots[] {n, t, d, p, k, color, desplazar, por_modo}` | Numbered points on the model. Hidden when their structure `k` is hidden, behind the camera, under the caption or under the buttons. `por_modo` gives a different (visible) text, or `false`. |
| `modos[] {id, n, grupo, leyenda, mostrar, ocultar, opacidad, vista, foco, puntos, modulo, secuencia, opcion, fase}` · `modo_inicial` | Visibility and opacity sets with their caption. `modulo`: `normal`, `etapas` or `reseccion`. |
| `ruta {puntos, radios, archivo, suavizado, vel, zonas, estrechez}` | The lumen: glTF points and radius (cm). `archivo` = the `ruta.json` from `trazar_luz.py` (`puntos_gltf` or `puntos`, plus `radios_mm`, optionally `estrechez`). `estrechez {desde, hasta, vel, luz_normal, pared_normal, color_normal, clave}` uses route indices. |
| `flujo {titulo, liquido, solido, textos, vista, opacidad, foco, vel_post}` | The flow simulation. |
| `secuencias {id: [stage]}` · `seg_etapa` (6.5) | Tube stages `{t, luz, pared, color, desde, hasta, escala}` or scale stages `{tipo:"escala", clave, factor, t}`. |
| `reseccion {color_saca, color_ganglios, radio_ganglio, ganglios, opciones}` | Per option: `saca`, `planos`, `ocultar_queda`, `ganglios`, `reconstruccion`, `uniones`, `post_ruta`, `texto_post`. |
| `orientacion` · `pestanas_privadas[]` | Labels for the patient's sides (on by default); tabs left out of the share copy. |

Points can be `[x,y,z]`, a key (the centre of its box), `"ruta:N"` (N may be fractional) and, in lists, `"ruta:A-B"`. With only `estructuras` the page works: three auto-framed views, chips and legend.

## Modules

- **normal** (with/without the lesion).
  - Normal wall and lumen are generated with the **same indices** as `ruta.estrechez`.
  - The mode hides the lesion and the lumen (`ocultar`), and hotspot texts change with `por_modo`.
- **etapas.**
  - Tubes are precomputed along the stretch (wall and lumen, a number or a list per point).
  - One shows every `seg_etapa` seconds, with «Etapa X de N · …» and ‹ Ⅱ › controls.
  - Scale stages animate around the mesh centre.
  - Used for growth and for treatment response.
- **reseccion.**
  - In "saca" (removed), what comes out is red and the nodes yellow.
  - In "queda" (remains), only the remnant, the reconstruction (tubes) and the joins (white dots) show. `saca` and `ocultar_queda` are hidden: no air, lumen or lesion of the removed stretch may be left.
  - Cuts use `renderer.localClippingEnabled`. `planos[].queda` is the list of half-spaces kept (union, `clipIntersection`).
  - `{ruta: N, queda: "antes"|"despues"}` cuts perpendicular to the route; two half-spaces remove a middle stretch.
- **flujo.**
  - Particles (`InstancedMesh`) run along the lumen, with a speed per zone.
  - Liquid crosses the narrowing.
  - A solid larger than the minimum lumen piles up before the narrowing and only small pieces get through; in the normal mode it passes, shrinking.
  - In a "queda" mode with `post_ruta`, the flow follows the reconstruction.
  - During the flow the numbered points hide and the camera goes to `flujo.vista`.

## Tabs, glossary and video

- `pestanas.html` is a series of `<section class="panel" id="panel-x" data-titulo="Label">`; file order is tab order. `id="panel-explorar"` creates no tab: its content goes under the 3D.
- `data-ver="mode"` (best on an `<a href="#panel-explorar">`) switches the 3D to that mode; `data-flujo="liquido|solido"` also starts the flow.
- Placeholders (HTML comments with double underscores): `LEYENDA_COLORES`, `PUNTOS` and `VIDEO` (position of the video tab). The legend and the numbered points are generated from the config and show without JS.
- `data-privado` on any element removes it from the share copy.
- The glossary file holds only the rows `<div data-terms="alias|alias"><dt>…</dt><dd>…</dd></div>`. The video file holds the tab's content; the MP4s travel next to the HTML and are sent separately.
- Available components (template CSS): `blk`, `lead`, `note`, `quote`, `mono`, `pasos/paso`, `fork/path`, `vs`, `cifras/cifra`, `tri`, `dib` (SVG on a dark background), `fila` + `btn`, `vids/vid`, `ok-t/warn-t/crit-t`, `dot`.

## Share copy (`--variante compartir`)

- It uses `banner_compartir` (if missing, a neutral banner: the private one never travels) and the other `<field>_compartir`.
- It appends `-compartir` to the `localStorage` prefix.
- It removes `pestanas_privadas` and every `data-privado` element.
- Regenerate it with every version.

## Tests (`probar_visor.py`)

- **Run it from the PowerShell tool** (or a normal terminal). From the Bash tool, headless Edge exits with code 0 and writes no screenshots.
- **How it works.**
  - It makes a test copy with an error catcher (`onerror`, promises, `console.error`, scripts that fail to load) and an automatic action set by URL (`?modo=&flujo=&avanzar=&tema=&tab=&vista=`).
  - The action waits for the model, advances with `__avanzar`, freezes time and leaves `VISOR_LISTO {state}` in the console.
  - Edge runs with `--headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --virtual-time-budget=15000`, a fresh profile every run, and `--enable-logging=stderr` (where errors and state come from).
- **Narrow width.** The headless window won't go below ~500 px (asking for 375 gives 492). A wrapper with a 375 px iframe gives a real 375 px viewport, and the screenshot is cropped.
- **No JS.** `--blink-settings=scriptEnabled=false` prevents capturing, so it uses a profile whose `Preferences` block JavaScript. Also:
  - screenshots of a `#anchor` come out blank;
  - windows taller than ~8000 px repeat content.
  So the page is captured in 6000 px windows (a shifted iframe) cut into slices, and the anchors are validated in the HTML (each tab has its section; no `oculto`).
- Don't stop drawing before the screenshot: a canvas resize clears it.
- MP4s missing next to the copy are reported as warnings, not errors. It exits with code 1 on JS errors, missing screenshots or a failed no-JS check.
- Look at the screenshots: model framed, colours not washed out, numbered points in place, captions, tabs, both themes and 375 px.

## Lessons learned

- **Washed-out colours:** missing `convertSRGBToLinear()` with `outputEncoding = sRGBEncoding`.
- **Camera flying away in headless:** the tween uses `performance.now()` clamped at 1, never the rAF timestamp.
- **Hotspot texts per mode:** "the white is the lumen" doesn't read the same with and without the lesion (`por_modo`).
- **Misaligned normal lumen** (longer or shifted): generate it with the same indices and the same route samples as the diseased stretch.
- **Leftovers after surgery:** "queda" hides what no longer exists (`saca` + `ocultar_queda`), including the air or lumen of the removed stretch.
- **Unreadable stages:** 6.5 s per stage, «Etapa X de N» and a pause button.
- **Weight:** the GLB grows ×1.33 as base64. The builder warns above 12 MB and refuses above 16 MB (the artifact limit); decimate in Blender.
- **Node names:** `GLTFLoader` sanitises names (spaces, dots, colons). Keys are ASCII `[A-Za-z0-9_-]`.
- **Blender coordinates pasted into the config** (Z up): the builder warns when a point falls far from the model.
- **Placeholders inside comments:** writing a placeholder comment inside another comment closes it early. The docs name placeholders without the syntax.

## Limits

- three.js downloads from jsdelivr on open: without internet the first time, there is no 3D (the rest of the page works).
- Resection cuts are planes. A reconstruction is a tube through given points: a sketch, not the surgical technique.
- The flow simulation illustrates; it doesn't measure pressures or calibres. If it rests on a physiological fact, cite it in the caption.
- No volume rendering and no PET layer: meshes only.
