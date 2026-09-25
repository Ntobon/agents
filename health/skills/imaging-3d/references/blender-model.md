# The Blender model: meshes, stills, video and GLB

Three scripts in `scripts/blender/`, always with Blender in **background mode** (`-b`). Nothing extra needs installing: Blender ships Python, numpy and openvdb. All of them use `scripts/coords.py`.

```
masks (mascaras.npz + json) ──mallas.py──▶ modelo.blend ──render.py──▶ 01 Frente.png … · giro.mp4
                                                         └──glb.py────▶ modelo.glb + centros.json (viewer)
```

## How to run them

Quote paths that contain spaces; the script's own arguments go after `--`. `blender` is the executable (on Windows: `"C:\Program Files\Blender Foundation\Blender <version>\blender.exe"`).

```
blender -b -P scripts/blender/mallas.py -- --trabajo "<work>" --estilo estilo.json --salida "<deliverable>/modelo.blend"
blender -b "<deliverable>/modelo.blend" -P scripts/blender/render.py -- --camaras camaras.json --salida "<deliverable>"
blender -b "<deliverable>/modelo.blend" -P scripts/blender/render.py -- --camaras camaras.json --salida "<deliverable>" --sin-fotos --video giro_completo.mp4 --camara frente
blender -b "<deliverable>/modelo.blend" -P scripts/blender/render.py -- --camaras camaras.json --salida "<deliverable>" --sin-fotos --video giro_detalle.mp4 --camara detalle
blender -b "<deliverable>/modelo.blend" -P scripts/blender/glb.py -- --salida "<work>/modelo.glb" --centros "<work>/centros.json"
```

| Script | In | Out | Useful options |
| --- | --- | --- | --- |
| `mallas.py` | `--trabajo` with `mascaras.npz`, `mascaras.json`, `volumen.json`, `mapeo.json`; `--estilo` | `.blend` + `<model>_mallas.json` (voxels, triangles, vertices, mask and mesh volume in mL, clean-up) | `--solo key1,key2` to iterate on one structure |
| `render.py` | `.blend`, `--camaras` | one PNG per camera; MP4 with `--video` | `--resolucion W H`, `--muestras N`, `--solo frente,detalle`, `--sin-fotos`, `--guardar escena.blend` (cameras, lights and labels, to open in Blender) |
| `glb.py` | `.blend` | `.glb` + `centros.json` | `--decimar 0.35`, `--decimar-por key=0.2`, `--min-caras 2000`, `--excluir key`, `--presupuesto-mb 8` |

**Observed timings** (abdomen, reduced grid of ~300×256×256, 11-13 structures, desktop GPU):

- `mallas.py`: 15-25 s, of which the skin takes ~10 s.
- One still at 1600×1200 and 64 samples: 1-2.5 s.
- Video: ~0.2 s per frame plus ~4 s of shader compilation; 240 frames at 1080×1080 take about 1 min.
- `glb.py`: 3-6 s.

Rendering can run in the background while you keep working on the dashboard.

## Space

- **1 unit = 1 cm.** `B = (P_LPS − centro_mm) / 10`, with `centro_mm` from `mapeo.json`: the same origin for Blender and the viewer. The scene is saved with `scale_length = 0.01` so the UI shows cm. Never scale objects by hand.
- Vertices go from the reduced-grid index → full-volume index (`reducido_a_voxel`) → LPS → Blender. Objects keep an identity transform.
- **Front** = camera at −y looking toward +y: the patient's left on the screen's right and the head up, as in every radiological image. Check it on the first still of every case.
- glTF (+Y up): `G = (Bx, Bz, −By)`. `centros.json` is already in that space.

## Style (`estilo.json`)

See `scripts/blender/estilo-ejemplo.json`. Each structure has:

- `clave`, `nombre`;
- `color` (hex sRGB), `alpha`;
- `grupo` (one collection per group);
- `suavizado {blur, taubin}`;
- `decimar` (the fraction of **triangles** kept);
- `min_componente_vox`.

Optional: `iso`, `solo_mayor`, `dentro_de`, `max_caras`, `rugosidad`, `emision`, `sombra`, `transparencia`, `lesion`. Keys missing from the npz are skipped with a warning.

**Colour rules** (they come from a real case, and `mallas.py` warns when they are broken):

1. **The lesion has the only saturated colour of its family** (magenta `#ff2d95`). Violets, lilacs, fuchsias and pinks (hue 265°-345°) are reserved for it. A violet spleen was once mistaken for the tumour; the fix was grey-blue `#7f93ad`.
2. **One colour, one meaning.** Two colours closer than 40/255 get confused. Example: an orange kidney next to amber gastric content, fixed with yellow `#f4d35e`.
3. **Conventions:** the lumen or air of the organ under study is white and emissive, so it shows through the lesion. The body envelope is almost transparent (alpha 0.05-0.1). Bone is ivory. Arteries red, veins blue.
4. **Hex in sRGB, render in linear.** `mallas.py` converts, and `render.py` uses the "Standard" view transform. AgX and Filmic desaturate the palette.

**Meshing:**

- **[1 2 1] blur** per axis before the isovalue. Each pass rounds shapes and erases ~1 voxel of detail.
  - 1 pass for thin structures;
  - 2 for smooth organs;
  - 3 for the skin.
- **Isovalue 0.5** on the blurred mask: the surface sits on the mask's edge and keeps its volume (mesh and mask agree within ±1-5 %).
  - For thin structures (a narrow lumen, small vessels) use 0.35-0.45: at 0.5 they break up or disappear.
  - At 0.4, bone swells by ~7 %.
- **Taubin smoothing** (λ 0.5, μ −0.53) removes stair-stepping without shrinking: 6-12 iterations, 60 for the skin.
- **Clean-up:**
  - `dentro_de: "cuerpo"` removes the scanner table from the bone and the outside air from the lungs.
  - `min_componente_vox` removes specks.
  - `solo_mayor` keeps a single island (lesion, single organs).
  - Components are computed with numpy, because Blender doesn't ship scipy.
- **Decimation** inside the `.blend`: skin ~0.15, lungs ~0.2, bone ~0.33, organs 0.4-0.6, small things not decimated. Then call `validate()`: the collapse leaves invalid geometry, and the glTF exporter warns "Mesh … is not valid".

**Transparency in EEVEE (Blender 4.2+ / 5.x):**

- **Envelopes** (alpha ≤ 0.25: skin, lungs): `BLENDED` with `use_transparency_overlap = True`. With `False`, each object does a depth pre-pass: if the skin is drawn first it hides the lungs, and in one case the lungs disappeared from the render.
- **Everything else:** `DITHERED`. It doesn't depend on draw order and converges with samples; at 16 samples it leaves fine grain.
- `use_backface_culling` when alpha < 1: a single layer, so the alpha reads literally.
- Envelopes cast no shadows (`sombra: false`).

## Cameras (`camaras.json`)

See `scripts/blender/camaras-ejemplo.json`.

| Type | Azimuth / elevation | What it shows |
| --- | --- | --- |
| `frente` | 0° / 0° | Camera at −y. The patient's left on the screen's right. |
| `oblicua` | 35° / 0° | Turned toward the patient's left (positive azimuth = toward +x). |
| `lateral` | 90° / 0° | From the patient's left: anterior on the screen's left, like a sagittal image. |
| `lateral_derecha`, `atras` | −90°, 180° | — |
| `arriba` | 0° / 90° | From the head; anterior at the bottom. Continues the front view: the patient's left stays on the right. |
| `abajo` | 0° / −90° | From the feet, like an axial slice: anterior at the top. |
| `detalle` | free | Framed on the keys listed in `encuadre`. |
| `orbita` | free | — |

- **Auto-framing.**
  - The camera is placed at 3× the diagonal of what it frames (≥ 1.5× the diagonal of what is visible).
  - It re-centres on the projection and sets the lens so the subject fills `ocupacion` of the frame: 0.88×0.9 without labels, 0.5×0.9 with labels on the sides.
- **Per camera:** `ocultar`, `solo` and `alpha` affect only that still. For example, the detail view hides skin, lungs and bone and drops the liver to 0.15.
- **Lights.** Three area lights (key, fill and rim) scaled to the model's bounding box; energy grows with the square of the size. The background shows the `fondo` colour, and ambient light is a neutral grey (Light Path node).
- **Labels.** Text with a title before the ":", a dark panel, a bar in the structure's colour and a leader line.
  - They sit on a plane in front of everything visible, in columns beside the silhouette, without overlapping.
  - The line ends on the **visible** part of the structure: if another nearly opaque one (alpha ≥ 0.5) covers it, it finds the nearest visible point.
  - A label without `clave` is a note.
  - The label texts come from the case reading. Labels don't appear in the video.

## Turntable video

- An Empty pivot sits at the centre of the framing. The camera and the lights are its children, so the lighting stays constant on screen.
- Linear rotation from 0° to 360°: frame N+1 equals frame 1, so the loop closes without a jump.
- 5° elevation unless the camera says otherwise. The lens is computed so the subject fits during the whole turn (checked every 10°).
- **`scene.timeline_markers.clear()` before animating.** A marker bound to a camera (the "one camera per frame" trick for stills) freezes the turntable on that camera: every frame comes out identical.
- **Output:** FFMPEG, MPEG4 container, H.264, CRF "HIGH", preset "GOOD", no audio. In Blender 5.x set `image_settings.media_type = "VIDEO"` first.
  - H.264 needs even width and height; the script forces them.
  - Blender writes `name0001-0240.mp4`, so the script renders into a temp folder and renames the file to the requested name.
- 10 s at 1080×1080 weigh ~13 MB and work for WhatsApp. If the channel needs less, use 720×720 or fewer seconds.
- **Verify:** the first frame and the middle one must differ (e.g. with OpenCV, mean difference > 1). If they are equal, the turn froze.

## GLB for the viewer

- **Copies.** Decimated copies are exported and the `.blend` is left alone: the script never saves, and checks the file's timestamp at the end.
- **Decimation:** `--decimar` (0.35) globally, `--decimar-por` per structure. Never below `--min-caras` (2000 triangles): small things deform.
- **Contents:**
  - Nodes with ASCII names = keys. Vertices are already in world space (identity).
  - No materials: the viewer colours them from its config.
  - No cameras, lights, animations, UVs or Draco/meshopt compression (the viewer loads no decoders).
- **Automatic check:** it re-reads the GLB and checks that names equal keys, transforms are identity, there are no materials, and the bounding boxes match `centros.json`.
- **Budget.** The viewer embeds the GLB in base64 (×1.33) inside an HTML that must stay under 16 MB.
  - Reference: ~186,000 triangles ≈ 3.4 MB, about 18 bytes per triangle.
  - Above `--presupuesto-mb` (8) the script warns, names the heaviest structures and suggests `--decimar` or `--decimar-por`.
  - Skin and bone are almost always the heaviest.

## Known pitfalls

- Always run Blender with `-b`. `mallas.py` starts with `read_factory_settings(use_empty=True)`, so the startup file's cube, camera and light don't sneak in.
- Use absolute paths inside the scripts: in Blender, `//` is relative to the `.blend`. The scripts set `sys.dont_write_bytecode`, so no `__pycache__` is left in Drive.
- openvdb takes the array as (x, y, z) = (i, j, k), so the [k, j, i] array is transposed. The bounding box gets a margin of ≥ blur + 3 voxels so the surface closes.
- Meshes end up with outward normals (signed volume). The mesh volume is a check: if it differs much from the mask's, revisit the isovalue.
- If a structure touches the edge of the crop, the mesh closes with a flat cap: normal for skin and bone at the ends.
- Very anisotropic volumes (MRI with thick slices): the blur works per index, so it rounds differently in z. Resample during segmentation if it shows.
