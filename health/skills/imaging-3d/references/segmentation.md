# Segmentation: from the series to masks, lumen and measurements

A practical guide to `dicom_series.py`, `cortes_qa.py`, `segmentar.py` and `trazar_luz.py`. Everything runs locally with numpy and Pillow; scipy is used only if installed.

Coordinates follow `coords.py`: a full-volume voxel is `[k, j, i]` = [slice, row, column], with k ascending along the normal (in an axial series, feet to head).

## 1. Choosing the series

```
python scripts/dicom_series.py listar "<zip or folder>" --salida "<work>"
python scripts/dicom_series.py cargar "<zip or folder>" --serie 3 --salida "<work>"
```

**CT.**

- **What to pick:**
  - axial, `ORIGINAL/PRIMARY`;
  - step ≤ 1.25 mm (ideally 0.6-1 mm);
  - soft kernel (STANDARD, B30, SOFT);
  - full coverage of the region.
- **Avoid** bone or lung kernels (B60-B70, LUNG, BONE): their noise breaks the thresholds.
- **The phase follows the question:**

| Question | Phase |
| --- | --- |
| Solid organs, visceral walls, veins | Portal (~70 s) |
| Arteries, hypervascular lesions | Arterial (~25-35 s) |
| Urinary tract | Excretory (5-10 min) |
| Calcium, acute bleeding, baseline | Non-contrast |

- `listar` gives hints: description, contrast agent and acquisition order.
- Confirm the phase by measuring with `cortes_qa.py muestrear`:
  - **arterial:** aorta > 250 HU and portal vein lower;
  - **portal:** portal vein ≥ aorta, both around 150-220 HU;
  - **delayed:** all vessels similar.

**Thickness ≠ step.** `SliceThickness` is the nominal thickness; what matters is the distance between positions (`espaciado_mm[0]`). Some exports carry a wrong `SpacingBetweenSlices`, and `cargar` warns about it.

**`cargar` warnings that matter:**

- *Irregular spacing.* Coordinates in mm are wrong past a gap: use `--uniformizar` (interpolates to a uniform step) or pick another series.
- *Tilted gantry.* Coordinates drift toward the ends; for measuring, prefer another series.
- *Mixed stacks.* Echoes, times or phases in one series: it uses the largest stack and says so.

`--recorte k0:k1` keeps only those slices and saves memory when the series covers chest, abdomen and pelvis.

**MRI.** Pick the sequence by what you are looking for: T2 for fluid and walls, contrast T1 for what enhances, diffusion to locate cellular tissue.

- 3D works with volumetric acquisitions with slices ≤ 3 mm: gadolinium T1 3D (VIBE/LAVA/THRIVE-type) or T2 3D (SPACE/CUBE-type).
- A 2D axial with 5-6 mm slices gives a stair-stepped model.
- Two series from the same session with the same geometry (same `origen_mm`, `cosenos` and `espaciado_mm`) let you segment on one and show the other.

## 2. Windows

| Name | W / L | For |
| --- | --- | --- |
| `abdomen` | 400 / 50 | soft tissue, viscera |
| `higado` | 150 / 80 | fine differences inside an organ |
| `mediastino` | 350 / 40 | soft chest |
| `pulmon` | 1500 / -600 | air, gas-filled lumen, lung |
| `hueso` | 2000 / 500 | bone, calcium, dense contrast |
| `auto` | p1-p99 | MRI (percentiles from `volumen.json`) |

`--ventana` also accepts `W/L` (400/50) or `lo:hi`.

## 3. Look before segmenting (the workflow)

1. **Montage with a grid.**
   ```
   cortes_qa.py montaje --volumen T --cada 20 --salida m.png
   cortes_qa.py montaje --volumen T --cortes 300,310,320 --recuadro 180:280,200:340 --escala 2 --salida z.png
   ```
   The grid labels full-volume `(j, i)` every 32 px and each tile carries its `k`, so seeds and boxes can be read off the image.
2. **Reformat** to see the head-to-feet extent, with the correct dz/dx ratio.
   ```
   cortes_qa.py reformat --volumen T --j 200,240 --salida cor.png
   ```
   - `--grosor N --modo minip` follows gas.
   - `--modo mip` follows contrast.
3. **Sample** every seed and every tissue.
   ```
   cortes_qa.py muestrear --volumen T --puntos "300 256 240; 350 230 150"
   ```
   - It gives the value, mean ± SD, min and max, and a suggested range.
   - With masks already made, it says which one the point falls in.
4. **Segment** with a recipe copied from `scripts/recetas/`.
5. **Overlay.** This is the gate.
   ```
   cortes_qa.py superponer --volumen T --salida qa
   ```
   - Review every structure on axial and coronal images.
   - Fix range, erosion, seeds, `excluir` or `limitar_a`, and repeat.
6. Only once the masks are right: `trazar_luz.py` if there is a hollow organ, then Blender.

`--marcas "k j i; k j i"` draws points (seeds, waypoints) on montages and reformats.

## 4. Recipes

```
python scripts/segmentar.py --volumen "<work>" --receta receta.json [--salida "<work>"]
```

**Preprocessing** runs on the crop, on the reduced grid `[fz, fy, fx]`. With 2×2×2 on a 0.7 mm CT, voxels end up ~1.4 mm.

- **V** = block mean: the normal intensity.
- **VM** = block max: catches thin cortex and calcium.
- **Vs** = V smoothed 3×3×3 (sum / 27): for organs. Without smoothing, erosion wipes out noisy masks.

**Top-level fields**

| Field | Meaning |
| --- | --- |
| `recorte` | `"auto"` (body box), `"completo"`, or `{k0, k1, j0, j1, i0, i1}` in the full volume. `{"auto": true, "k0": .., "k1": ..}` limits the slices and takes j, i from the body. |
| `reduccion` | `[fz, fy, fx]` or an integer. For thick-slice MRI, `[1, 2, 2]`. |
| `bordes` | `"replicar"` (default). `"envolver"` reproduces the `np.roll` of old scripts; only useful to validate equivalence. |
| `centro` | The structure whose box centre defines `mapeo.json` (default `cuerpo`). |

**Per-structure fields**, in order of application. List order matters: `excluir` can only name earlier structures.

| Field | What it does |
| --- | --- |
| `clave` | The name in `mascaras.npz`, lowercase ASCII. Use the Blender palette's keys: `lesion`, `luz`, `contenido`, `contraste`, `higado`, `bazo`, `rinones`, `pulmones`, `arterias`, `venas`, `hueso`, `cuerpo`. |
| `fuente` | `V`, `VM` or `Vs`. |
| `rango` | `[lo, hi]`, strict (lo < value < hi); `null` = no limit. |
| `excluir` | Structures to subtract: `"key"` or `"key+dil:N"` (subtracted after dilating it N voxels). |
| `limitar_a` | Allowed region: `{"caja_voxel": [[k0,k1],[j0,j1],[i0,i1]]}` and/or `{"esfera_voxel": [k,j,i], "radio_mm": r}`. |
| `filtro_vecinos` | Keeps voxels with ≥ N marked voxels in their 3×3×3 box (removes specks). |
| `erosion` | Erosions before growing; afterwards they are given back by dilating inside the candidate. Cuts thin bridges to neighbouring organs. |
| `crecer` + `semillas_voxel` | The 6-connected component that contains the seeds `[[k, j, i], ...]` (full-volume). A seed outside the eroded mask moves to the nearest valid voxel, with a warning. If none falls inside, the error gives the source value at each seed. |
| `max_iter` | Optional: grow at most N steps instead of taking the whole component (stops distant leaks). |
| `mayor_componente` | Without seeds: the largest component (with erosion, taken before giving it back). |
| `rellenar_por_corte` | Fills the holes in each slice (body). |
| `dilatar_despues` | A final free dilation. |
| `auxiliar` | Used in `excluir` but not saved. |
| `_nota` | Free comment. |

**Outputs**

- `mascaras.npz`: booleans on the reduced grid.
- `mascaras.json`: reduction, effective crop, shape, spacing, and voxels, mL, source and parameters per structure.
- `mapeo.json`: `centro_mm` and the Blender/glTF convention.

Re-running `segmentar.py` rewrites `mascaras.npz`: the sleeves from `trazar_luz.py` are lost and must be redone (it warns).

## 5. Starting CT ranges (HU)

These are only a starting point. They shift with kVp (at 80-100 kVp iodine reads higher), bolus timing, cardiac output, noise and disease. **Always measure them with `muestrear`.**

| Tissue | Non-contrast | Arterial | Portal | Delayed / excretory | Notes |
| --- | --- | --- | --- | --- | --- |
| Air | -1000 | | | | Gas lumen: threshold < -400 to -450 (wall partial volume). |
| Lung | -900 to -700 | | | | Threshold < -500 takes the aerated parenchyma. |
| Fat | -120 to -60 | | | | |
| Simple fluid (bile, urine, cysts, ascites) | 0-20 | = | = | Urine > 300 when excreted | Thick fluid or exudate 20-35. |
| Retained contents in a hollow viscus | 0-60 | = | = | | Variable: water 0-20, food 20-60. |
| Muscle | 40-60 | 50-70 | 55-75 | | |
| Blood / vessels | 35-55 | Aorta 250-400+, portal vein 100-150 | Aorta and portal vein 150-220 | 100-150, even | Acute haematoma 50-80. |
| Liver | 50-65 | 65-90 | 100-130 | 90-110 | Steatosis: < 40 non-contrast or 10+ HU below the spleen; on portal phase it may sit at 60-100. |
| Spleen | 40-55 | Mottled | 110-130 | ~100 | Can't be segmented with one range on arterial phase. |
| Kidney | 30-45 | Cortex 150-200, medulla lower | 150-200, homogeneous | Urinary tract > 300 | |
| Bone | Cancellous 150-400, cortical 700-2000+ | = | = | = | Osteoporosis lowers cancellous bone (< 150). Use VM. |
| Calcium | > 130 | = | = | = | |
| Positive oral contrast | 150-600 (dense > 1000) | = | = | = | Negative contrast (water) is 0-20. |
| Metal | > 2000 | | | | Streak artefact: exclude the area. |

**Overlaps that force an order:**

- spleen and kidney;
- enhanced liver and renal cortex;
- portal-phase vessels and renal cortex;
- oral contrast, arterial vessels and cancellous bone.

They are solved with seeds, erosion and `excluir` (section 7), not with a magic threshold.

## 6. MRI

- **No absolute units.** Intensity depends on the coil, the sequence and the scanner, and varies inside one volume (inhomogeneity).
  - `volumen.json` stores the series' p1, p50 and p99 percentiles, and windows use `auto`.
  - Ranges come from `muestrear` in the organ itself (mean ± 2 SD, sometimes 1.5), never from a table.
- **Relative brightness** (a rough guide):

| Tissue | T1 | T2 | Gadolinium T1 | Diffusion (high b) |
| --- | --- | --- | --- | --- |
| Fat | Bright | Bright (dark with fat suppression) | Depends on suppression | Dark |
| Fluid (bile, urine, cysts, CSF) | Dark | Very bright | Dark, no enhancement | Dark (except pus or thick fluid) |
| Liver | Intermediate, brighter than spleen | Dark, darker than spleen | Enhances | Intermediate |
| Spleen | Intermediate | Bright | Enhances | Bright |
| Muscle | Intermediate | Dark | Enhances little | Dark |
| Vessels | Dark on spin echo; bright on gradient echo/3D | Dark (flow void) | Very bright | Variable |
| Air and cortical bone | No signal | No signal | No signal | No signal |
| Tumours (many) | Intermediate-low | Intermediate-high | Enhance | Bright (restricted) |

- **How to segment.**
  - Seeds plus a local range.
  - `limitar_a` with a box per region: inhomogeneity means one range won't fit the whole volume.
  - Somewhat more erosion, and reduction `[1, 2, 2]` for thick slices.
- **Lumen on MRI.**
  - Gas gives no signal, but neither do cortical bone and flow voids, so use a tight box.
  - A fluid-filled lumen is bright on T2: `trazar_luz.py ruta --rango lo:hi`.
- **More manual review.** Run `superponer` on more slices. Whatever the sequence can't separate is drawn and labelled "drawn".

## 7. Lessons learned (order, subtraction and leaks)

1. **Smooth before thresholding** (source `Vs`) for organs. Without it, erosion wipes out the mask and the seed falls outside.
2. **Segment first the organ that sticks to another, and subtract it dilated.** Example: spleen before kidneys, with `"excluir": ["bazo+dil:2"]` on the kidney. Same with vessels: they are subtracted from everything after them.
3. **Leaks into a neighbour** (e.g. the liver into a viscus or a thickened wall): narrower range and `erosion` 4. If that isn't enough, `limitar_a` with a box, or `max_iter`.
4. **Bone with VM** and `filtro_vecinos: 6`, subtracting vessels and contrast dilated by 1.
   - Dense contrast the vessels didn't take (heart chambers, veins with pure contrast, catheters) ends up as bone: limit k or seed it in the vessels.
   - `superponer` shows this at once.
5. **Vessels with erosion 1.** This separates thin branches that touch bone or kidney. Subtract cortical bone (`hueso_duro+dil:1`, an auxiliary with VM > 650).
   - If arteries and veins touch in the mask, the arteries block takes both: more erosion, or a single `vasos` block.
6. **Body** without a seed: `mayor_componente` + `rellenar_por_corte`.
7. **Moved seed** (a `segmentar.py` warning). If it moved more than 1-2 voxels, the range doesn't represent that tissue: measure again.
8. **Validating against an old script.** With `"bordes": "envolver"` the engine reproduces an `np.roll`-based script voxel for voxel. With the default, only the slices at the ends of the crop change.

## 8. Lumen, wall and measurements (`trazar_luz.py`)

**`ruta`** traces the lumen of a hollow organ or a vessel.

```
trazar_luz.py ruta --trabajo T --caja 280:330,170:230,200:270 --luz aire [--puntos "k j i; ..."]
```

- **How it finds the lumen.** In each slice of the box (along `--eje`) it thresholds the lumen: `aire` < -400, `contraste` > 150, or `--rango lo:hi` on MRI.
  - It takes the largest component and, from the second slice on, the one that continues the previous one (overlapping or within `--salto-max` mm).
  - The line of centroids is smoothed.
- **Gaps.** Where there is no lumen (a collapsed segment, or one narrower than the resolution) it interpolates and records the stretch in `huecos`, with radius 0.
- **Waypoints (`--puntos`).**
  - Where there is lumen, they choose which one to follow.
  - Where there isn't, the path goes through them.
  - Place them by looking at the montage.
- **Lumen parallel to the slices.** If the lumen runs almost parallel to the slice plane, the centroid jumps. Fixes:
  - `--eje j` or `--eje i`, if it runs along that axis end to end;
  - waypoints;
  - `--manual "k j i; ..."`, which subdivides each stretch without moving the vertices and measures the radius at each point when `--luz` or `--rango` is given.
- **Equivalent radius per point:** `sqrt(area · cos θ / π)`. θ is the angle between the path and the slice normal; this corrects the elongated cross-section of an oblique lumen.
- **Outputs:**
  - `ruta.json`: `puntos_voxel`, `puntos_gltf` (with `mapeo.json`), `radios_mm`, `huecos`, `zonas` (`--zona name:s0:s1`), `s_mm`;
  - `ruta_qa.png`: coronal and sagittal projection of the box with the path. Yellow = measured lumen, red = interpolated.

**`manga`** extracts the wall or lesion around a stretch `[s0, s1]` of the route.

```
trazar_luz.py manga --trabajo T --radio 12 --rango=-20:200 --menos higado,arterias --clave lesion
```

- Radius larger than the thickest wall expected, plus a margin (10-15 mm).
- A soft-tissue range that leaves out fat and gas. With positive contrast in the lumen, set `hi` below the contrast.
- `--menos` subtracts neighbouring organs already segmented.
- `--mayor-componente` removes specks.
- Check it with `superponer --claves lesion`.

**`medir`** gives length × thickness and the minimum lumen.

```
trazar_luz.py medir --trabajo T --clave lesion --paso 2 --umbral 5
```

- **How it measures.** At each station (every `paso` mm) it counts the sleeve's voxels in a slab perpendicular to the tangent. That is the wall area.
  - Outer radius = `sqrt(area/π + r_lumen²)`; thickness = outer − lumen.
- **Results:**
  - total length with thickness > threshold;
  - longest continuous stretch;
  - maximum thickness;
  - minimum lumen diameter;
  - length with no visible lumen.
- **Outputs:** `medidas.json` and a table on screen.

**Limits of the measurements**

- Thickness can't exceed the sleeve radius; it warns when it gets close.
- Any in-range tissue within the radius counts as wall, so a neighbouring organ stuck to it inflates the thickness.
- Partial volume adds or removes about one reduced voxel (~1.4 mm).
- A collapsed segment gives lumen 0, and "wall" = the whole cylinder.

## 9. Honest limits

- Threshold + seed ≠ radiology. A lesion with the same density as the wall or the organ can't be separated by threshold, and a single phase doesn't characterise lesions.
- The masks live on a ~1.4 mm grid, and the measurements are approximate by construction. `mascaras.json` and `medidas.json` say so in their note.
- These masks and measurements are for understanding and for asking better questions.
  - They **never** go into the medical record, a medical package or any document for doctors as if they were a report or a finding.
  - If a measurement changes a decision, it goes to a radiologist as a concrete question: series, slice and what is seen.
