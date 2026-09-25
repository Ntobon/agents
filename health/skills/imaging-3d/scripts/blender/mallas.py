"""Máscaras segmentadas -> mallas de Blender (.blend) con materiales y una colección por grupo.

Uso (siempre en segundo plano; las rutas con espacios van entre comillas):
  blender -b -P mallas.py -- --trabajo "<carpeta>" --estilo estilo.json --salida modelo.blend
          [--estadisticas mallas.json] [--solo clave1,clave2]

Entradas en --trabajo (contrato de la etapa de segmentación):
  mascaras.npz   arreglos booleanos [k, j, i] en la rejilla reducida, uno por clave de estructura
  mascaras.json  reduccion, recorte {k0, j0, i0, ...}, forma, espaciado_mm, volumen (nombre del volumen.json)
  volumen.json   forma, espaciado_mm [dz, dy, dx], origen_mm, cosenos, normal
  mapeo.json     centro_mm: origen común de Blender y del visor

Por cada estructura del estilo (en su orden): limpieza opcional (dentro_de, componentes pequeñas,
solo la mayor) -> desenfoque [1 2 1] -> rejilla openvdb -> polígonos en el isovalor (0.5 por defecto)
-> vértices: índice reducido -> índice completo -> LPS (mm) -> Blender (cm) con coords.py -> suavizado
de Taubin -> diezmado -> sombreado suave -> material Principled -> colección del grupo.

Blender: 1 unidad = 1 cm, B = (P_LPS - centro_mm) / 10. Las claves que no están en el npz se omiten con
un aviso. Al final guarda el .blend y un JSON de estadísticas (vértices, caras, volumen encerrado en mL).
"""
import argparse
import colorsys
import json
import os
import sys
import time

import numpy as np
import bpy
import openvdb as vdb   # incluido en Blender (no hace falta instalar nada)

sys.dont_write_bytecode = True   # no dejar __pycache__ de Blender dentro de la skill (Drive)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import coords  # noqa: E402  (scripts/coords.py, compartido por toda la skill)

T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def aviso(*a):
    print(f"[{time.time() - T0:7.1f}s] AVISO:", *a, flush=True)


# ------------------------------------------------------------------ argumentos
def argumentos():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="mallas.py", description="Máscaras -> mallas de Blender (.blend).")
    ap.add_argument("--trabajo", required=True, help="carpeta con mascaras.npz, mascaras.json, volumen.json y mapeo.json")
    ap.add_argument("--estilo", required=True, help="estilo.json (estructuras, colores, suavizado, grupos, fondo)")
    ap.add_argument("--salida", required=True, help="ruta del .blend que se va a escribir")
    ap.add_argument("--estadisticas", help="JSON de estadísticas (por defecto <salida>_mallas.json)")
    ap.add_argument("--solo", help="procesar solo estas claves, separadas por coma")
    return ap.parse_args(argv)


# ------------------------------------------------------------------ estilo
DEFECTOS = {
    "color": "#cccccc", "alpha": 1.0, "grupo": "Estructuras", "decimar": 1.0,
    "min_componente_vox": 0, "iso": 0.5, "rugosidad": 0.45, "emision": 0.0,
}
BANDA_LESION = (265.0, 345.0)   # tonos (grados) reservados a la lesión: violetas, lilas, fucsias, rosados


def hex_a_rgb(hx):
    h = str(hx).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"color hex inválido: {hx!r}")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb_a_lineal(hx):
    """Blender trabaja en lineal: los hex de diseño (sRGB) se convierten o salen lavados/oscuros."""
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in hex_a_rgb(hx))


def normalizar_estilo(estilo):
    salida, vistas = [], set()
    for e in estilo.get("estructuras", []):
        if "clave" not in e:
            aviso("entrada del estilo sin 'clave', se omite:", e)
            continue
        if e["clave"] in vistas:
            aviso("clave repetida en el estilo, se usa la primera:", e["clave"])
            continue
        vistas.add(e["clave"])
        d = dict(DEFECTOS)
        d.update(e)
        d.setdefault("nombre", e["clave"])
        s = dict(e.get("suavizado") or {})
        d["blur"] = int(s.get("blur", 1))
        d["taubin"] = int(s.get("taubin", 10))
        d["alpha"] = float(d["alpha"])
        salida.append(d)
    return salida


def revisar_paleta(estructuras):
    """Reglas de color aprendidas: la lesión es el único tono violeta-rosado saturado; un color, un significado."""
    hsv = {e["clave"]: colorsys.rgb_to_hsv(*hex_a_rgb(e["color"])) for e in estructuras}
    lesiones = [e["clave"] for e in estructuras if e.get("lesion")]
    if not lesiones:
        aviso("ninguna estructura tiene \"lesion\": true; no se revisa la banda de color de la lesión")
    for e in estructuras:
        if e["clave"] in lesiones:
            continue
        h, s, v = hsv[e["clave"]]
        tono = h * 360.0
        if lesiones and s >= 0.25 and v >= 0.25 and BANDA_LESION[0] <= tono <= BANDA_LESION[1]:
            aviso(f"'{e['clave']}' ({e['color']}, tono {tono:.0f}°) cae en la banda reservada a la lesión "
                  f"({BANDA_LESION[0]:.0f}-{BANDA_LESION[1]:.0f}°): se puede confundir con ella. Usar otro tono "
                  "(p. ej. gris azulado #7f93ad).")
    claves = [e["clave"] for e in estructuras]
    for a in range(len(claves)):
        for b in range(a + 1, len(claves)):
            ca = np.array(hex_a_rgb(estructuras[a]["color"])) * 255
            cb = np.array(hex_a_rgb(estructuras[b]["color"])) * 255
            if np.linalg.norm(ca - cb) < 40:
                aviso(f"'{claves[a]}' y '{claves[b]}' tienen colores casi iguales: un color, un significado.")


# ------------------------------------------------------------------ máscaras
def componentes(m):
    """Componentes 6-conexas de una máscara booleana, solo con numpy (sin scipy).
    Unión por enganche de raíces + compresión de punteros. Devuelve (activos, etiqueta, tamaños)."""
    act = np.nonzero(m)
    n = len(act[0])
    pos = np.full(m.shape, -1, np.int32)
    pos[act] = np.arange(n, dtype=np.int32)
    a_l, b_l = [], []
    for ax in range(3):
        s0 = [slice(None)] * 3
        s1 = [slice(None)] * 3
        s0[ax] = slice(0, -1)
        s1[ax] = slice(1, None)
        p0, p1 = pos[tuple(s0)], pos[tuple(s1)]
        ok = (p0 >= 0) & (p1 >= 0)
        a_l.append(p0[ok])
        b_l.append(p1[ok])
    del pos
    a, b = np.concatenate(a_l), np.concatenate(b_l)
    padre = np.arange(n, dtype=np.int32)
    while len(a):
        pa, pb = padre[a], padre[b]
        dif = pa != pb
        if not dif.any():
            break
        a, b, pa, pb = a[dif], b[dif], pa[dif], pb[dif]
        padre[np.maximum(pa, pb)] = np.minimum(pa, pb)   # enganchar la raíz mayor a la menor
        while True:                                       # comprimir: cada nodo apunta a su raíz
            pp = padre[padre]
            if np.array_equal(pp, padre):
                break
            padre = pp
    _, etiqueta, tam = np.unique(padre, return_inverse=True, return_counts=True)
    return act, etiqueta, tam


def limpiar(m, e, M):
    """Limpieza opcional de una máscara según el estilo. Devuelve (máscara, nota)."""
    notas = []
    n0 = int(m.sum())
    dentro = e.get("dentro_de")
    if dentro:
        if dentro in M:
            m = m & M[dentro]
            notas.append(f"dentro de '{dentro}'")
        else:
            aviso(f"'{e['clave']}': dentro_de '{dentro}' no está en el npz; se ignora")
    minimo = int(e.get("min_componente_vox") or 0)
    if (minimo > 0 or e.get("solo_mayor")) and m.any():
        nz = np.nonzero(m)
        caja = tuple(slice(int(x.min()), int(x.max()) + 1) for x in nz)
        del nz
        sub = m[caja]
        act, etq, tam = componentes(sub)
        if e.get("solo_mayor"):
            quedan = etq == int(np.argmax(tam))
            notas.append(f"solo la componente mayor (de {len(tam)})")
        else:
            quedan = tam[etq] >= minimo
            notas.append(f"{int((tam < minimo).sum())} de {len(tam)} componentes < {minimo} vóxeles retiradas")
        nuevo = np.zeros_like(sub)
        nuevo[tuple(x[quedan] for x in act)] = True
        m = np.zeros_like(m)
        m[caja] = nuevo
    if notas:
        notas.insert(0, f"{n0} -> {int(m.sum())} vóxeles")
    return m, "; ".join(notas)


# ------------------------------------------------------------------ mallado
def desenfocar(a, pasadas):
    """Filtro separable [1 2 1]/4 por eje, `pasadas` veces: suaviza el borde escalonado de la máscara."""
    a = a.astype(np.float32)
    for _ in range(pasadas):
        for ax in range(3):
            n = a.shape[ax]
            p = np.pad(a, [(1, 1) if i == ax else (0, 0) for i in range(3)])

            def s(b, e_, ax=ax):
                return tuple(slice(b, e_) if i == ax else slice(None) for i in range(3))
            a = 0.25 * p[s(0, n)] + 0.5 * p[s(1, n + 1)] + 0.25 * p[s(2, n + 2)]
    return a


def taubin(V, E, iters, lam=0.5, mu=-0.53):
    """Suavizado de Taubin (lambda/mu): quita el escalonado sin encoger la malla."""
    if iters <= 0 or len(E) == 0:
        return V
    nv = len(V)
    e0, e1 = E[:, 0], E[:, 1]
    grado = (np.bincount(e0, minlength=nv) + np.bincount(e1, minlength=nv)).astype(np.float64)
    grado[grado == 0] = 1
    V = V.astype(np.float64)

    def lap(V):
        S = np.empty_like(V)
        for c in range(3):
            S[:, c] = np.bincount(e0, weights=V[e1, c], minlength=nv) + np.bincount(e1, weights=V[e0, c], minlength=nv)
        return S / grado[:, None] - V
    for _ in range(iters):
        V = V + lam * lap(V)
        V = V + mu * lap(V)
    return V


def volumen_con_signo(V, tris):
    a, b, c = V[tris[:, 0]], V[tris[:, 1]], V[tris[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def aristas(quads, tris, nv):
    ed = []
    if len(quads):
        ed += [quads[:, [0, 1]], quads[:, [1, 2]], quads[:, [2, 3]], quads[:, [3, 0]]]
    if len(tris):
        ed += [tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]
    if not ed:
        return np.zeros((0, 2), np.int64)
    E = np.sort(np.concatenate(ed), axis=1)
    cod = np.unique(E[:, 0] * nv + E[:, 1])
    return np.stack([cod // nv, cod % nv], 1)


def crear_malla(nombre, V, quads, tris):
    """Malla desde arreglos numpy (rápido); si la API cambia, cae a from_pydata."""
    me = bpy.data.meshes.new(nombre)
    try:
        nq, nt = len(quads), len(tris)
        me.vertices.add(len(V))
        me.vertices.foreach_set("co", V.astype(np.float32).ravel())
        bucles = np.concatenate([quads.ravel(), tris.ravel()]).astype(np.int32)
        me.loops.add(len(bucles))
        me.loops.foreach_set("vertex_index", bucles)
        inicio = np.concatenate([np.arange(nq) * 4, nq * 4 + np.arange(nt) * 3]).astype(np.int32)
        me.polygons.add(nq + nt)
        me.polygons.foreach_set("loop_start", inicio)
        me.update(calc_edges=True)
        if len(me.polygons) != nq + nt or (nq and me.polygons[0].loop_total != 4):
            raise RuntimeError("conteo de caras inesperado")
    except Exception as ex:  # respaldo lento pero seguro
        aviso(f"{nombre}: creación rápida falló ({ex}); se usa from_pydata")
        bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new(nombre)
        me.from_pydata(V.tolist(), [], quads.tolist() + tris.tolist())
        me.update(calc_edges=True)
    if me.validate(clean_customdata=False):
        log(f"   {nombre}: validate() corrigió la malla")
    return me


def volumen_malla_ml(me):
    """(volumen encerrado en cm3 = mL, número de triángulos) de la malla final."""
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    if nt == 0:
        return 0.0, 0
    tri = np.empty(nt * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    return abs(volumen_con_signo(co.reshape(-1, 3), tri.reshape(-1, 3))), nt


def material(e):
    m = bpy.data.materials.new(e["nombre"])
    m["clave"] = e["clave"]
    nt = m.node_tree
    if nt is None:  # versiones anteriores a 5.x
        m.use_nodes = True
        nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bs is None:
        nt.nodes.clear()
        bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bs.outputs[0], out.inputs[0])
    col = srgb_a_lineal(e["color"])
    a = max(0.0, min(1.0, e["alpha"]))
    bs.inputs["Base Color"].default_value = (*col, 1.0)
    bs.inputs["Alpha"].default_value = a
    bs.inputs["Roughness"].default_value = float(e["rugosidad"])
    bs.inputs["Specular IOR Level"].default_value = 0.15 if a <= 0.25 else 0.35
    if float(e["emision"]) > 0:
        bs.inputs["Emission Color"].default_value = (*col, 1.0)
        bs.inputs["Emission Strength"].default_value = float(e["emision"])
    # EEVEE (5.x): las envolturas muy transparentes, mezcla ordenada (sin grano); el resto, tramado
    # (orden correcto entre órganos). Una sola capa por objeto: descarte de caras traseras.
    metodo = {"mezclada": "BLENDED", "tramada": "DITHERED"}.get(e.get("transparencia", ""), None)
    m.surface_render_method = metodo or ("BLENDED" if a <= 0.25 else "DITHERED")
    # Con BLENDED, use_transparency_overlap=False hace un prepaso de profundidad por objeto: si la
    # envoltura se dibuja primero, tapa a las otras mezcladas que tiene adentro (los pulmones desaparecen).
    m.use_transparency_overlap = m.surface_render_method == "BLENDED"
    try:
        m.use_transparent_shadow = True
    except Exception:
        pass
    m.use_backface_culling = a < 1.0
    m.diffuse_color = (*col, max(a, 0.15))   # color en la vista sólida
    m.roughness = float(e["rugosidad"])
    return m


def coleccion(nombre, escena):
    c = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    if c.name not in [x.name for x in escena.collection.children]:
        escena.collection.children.link(c)
    return c


# ------------------------------------------------------------------ principal
def main():
    a = argumentos()
    trabajo = os.path.abspath(a.trabajo)
    salida = os.path.abspath(a.salida)
    est_path = os.path.abspath(a.estadisticas) if a.estadisticas else os.path.splitext(salida)[0] + "_mallas.json"
    masc = coords.cargar(os.path.join(trabajo, "mascaras.json"))
    vol = coords.cargar(coords.ruta_volumen_json(trabajo, masc))
    mapeo = coords.cargar(os.path.join(trabajo, "mapeo.json"))
    estilo = coords.cargar(os.path.abspath(a.estilo))
    estructuras = normalizar_estilo(estilo)
    if a.solo:
        pedidas = {x.strip() for x in a.solo.split(",") if x.strip()}
        estructuras = [e for e in estructuras if e["clave"] in pedidas]
    revisar_paleta(estructuras)

    npz = np.load(os.path.join(trabajo, "mascaras.npz"))
    disponibles = set(npz.files)
    forma = tuple(masc.get("forma") or ())
    esp_red = masc.get("espaciado_mm")
    if not esp_red:
        f = masc["reduccion"]
        f = (f, f, f) if isinstance(f, (int, float)) else f
        esp_red = [s * r for s, r in zip(vol["espaciado_mm"], f)]
    ml_vox = float(np.prod(esp_red)) / 1000.0
    log("trabajo:", trabajo)
    log("claves en el npz:", sorted(disponibles))

    # escena vacía de fábrica: sin cubo, luz ni cámara del archivo de inicio del usuario
    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    us = escena.unit_settings
    us.system = "METRIC"
    us.scale_length = 0.01       # 1 unidad = 1 cm
    us.length_unit = "CENTIMETERS"
    escena["fondo"] = str(estilo.get("fondo", "#131416"))
    escena["centro_mm"] = [float(x) for x in mapeo["centro_mm"]]
    escena["imagenes_3d"] = "mallas.py"

    cache = {}

    def mascara(clave):
        if clave not in cache:
            cache[clave] = np.asarray(npz[clave]).astype(bool)
            if forma and cache[clave].shape != forma:
                aviso(f"'{clave}' tiene forma {cache[clave].shape} y mascaras.json dice {forma}")
        return cache[clave]

    class Perezoso(dict):  # dentro_de carga la máscara vecina solo si hace falta
        def __contains__(self, k):
            return k in disponibles

        def __getitem__(self, k):
            return mascara(k)

    stats, omitidas = {}, []
    for e in estructuras:
        clave = e["clave"]
        if clave not in disponibles:
            aviso(f"'{clave}' no está en mascaras.npz: se omite")
            omitidas.append(clave)
            continue
        t = time.time()
        m, nota = limpiar(mascara(clave), e, Perezoso())
        nvox = int(m.sum())
        if nvox == 0:
            aviso(f"'{clave}' quedó vacía: se omite")
            omitidas.append(clave)
            continue
        margen = max(4, e["blur"] + 3)
        nz_ = np.nonzero(m)
        lo = np.array([x.min() for x in nz_]) - margen
        hi = np.array([x.max() for x in nz_]) + margen + 1
        del nz_
        caja = np.zeros(tuple(hi - lo), np.float32)
        s_lo, s_hi = np.maximum(lo, 0), np.minimum(hi, m.shape)
        caja[tuple(slice(p - q, r - q) for p, q, r in zip(s_lo, lo, s_hi))] = m[tuple(slice(p, r) for p, r in zip(s_lo, s_hi))]
        f = desenfocar(caja, e["blur"])
        del caja
        g = vdb.FloatGrid()
        g.copyFromArray(np.ascontiguousarray(f.transpose(2, 1, 0)))   # openvdb: (x, y, z) = (i, j, k)
        del f
        pts, tris, quads = g.convertToPolygons(isovalue=float(e["iso"]), adaptivity=0.0)
        del g
        pts = np.asarray(pts, np.float64)
        tris = np.asarray(tris, np.int64).reshape(-1, 3)
        quads = np.asarray(quads, np.int64).reshape(-1, 4)
        if len(pts) == 0:
            aviso(f"'{clave}': el isovalor {e['iso']} no produjo superficie; se omite")
            omitidas.append(clave)
            continue
        # índice de la caja -> índice reducido -> índice completo -> LPS (mm) -> Blender (cm)
        k, j, i = coords.reducido_a_voxel(masc, pts[:, 2] + lo[0], pts[:, 1] + lo[1], pts[:, 0] + lo[2])
        V = coords.lps_a_blender(mapeo, coords.voxel_a_lps(vol, k, j, i))
        todas = np.concatenate([tris, quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]]) if len(quads) else tris
        if volumen_con_signo(V, todas) < 0:        # normales hacia afuera
            tris = tris[:, ::-1].copy()
            quads = quads[:, ::-1].copy()
        V = taubin(V, aristas(quads, tris, len(V)), e["taubin"])
        me = crear_malla(e["nombre"], V, quads, tris)
        ob = bpy.data.objects.new(e["nombre"], me)
        coleccion(str(e["grupo"]), escena).objects.link(ob)
        tri0 = 2 * len(quads) + len(tris)          # el diezmado cuenta triángulos
        ratio = float(e["decimar"])
        if e.get("max_caras"):
            ratio = min(ratio, float(e["max_caras"]) / max(1, tri0))
        if ratio < 1.0:
            mod = ob.modifiers.new("Diezmar", "DECIMATE")
            mod.decimate_type = "COLLAPSE"
            mod.ratio = max(0.01, ratio)
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()
            nueva = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            ob.modifiers.clear()
            vieja = ob.data
            ob.data = nueva
            bpy.data.meshes.remove(vieja)
            nueva.name = e["nombre"]
            if nueva.validate(clean_customdata=False):
                log(f"   {clave}: validate() corrigió la malla diezmada")
        ob.data.shade_smooth()
        ob.data.materials.clear()
        ob.data.materials.append(material(e))
        ob["clave"] = clave
        ob["grupo"] = str(e["grupo"])
        ob["color"] = str(e["color"])
        ob["alpha"] = float(e["alpha"])
        if "sombra" in e:
            ob.visible_shadow = bool(e["sombra"])
        elif e["alpha"] <= 0.25:
            ob.visible_shadow = False   # las envolturas no oscurecen lo de adentro
        vml, tri1 = volumen_malla_ml(ob.data)
        stats[clave] = dict(nombre=e["nombre"], grupo=str(e["grupo"]), voxeles=nvox,
                            vol_mascara_ml=round(nvox * ml_vox, 2), vol_malla_ml=round(vml, 2),
                            triangulos_iniciales=tri0, triangulos=tri1, vertices=len(ob.data.vertices),
                            tiempo_s=round(time.time() - t, 1), limpieza=nota or None)
        log(f"{clave:22s} vóx={nvox:9d} triángulos {tri0:7d} -> {tri1:7d} "
            f"vol máscara {nvox * ml_vox:9.1f} mL · malla {vml:9.1f} mL ({time.time() - t:.1f}s)"
            + (f" · {nota}" if nota else ""))
        cache.pop(clave, None)

    if not stats:
        raise SystemExit("ninguna estructura del estilo produjo malla; revisar claves y máscaras")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=salida, compress=True)
    info = dict(blender=bpy.app.version_string, salida=os.path.basename(salida),
                centro_mm=[float(x) for x in mapeo["centro_mm"]], voxel_reducido_mm=[float(x) for x in esp_red],
                estructuras=stats, omitidas=omitidas,
                totales=dict(triangulos=sum(s["triangulos"] for s in stats.values()),
                             vertices=sum(s["vertices"] for s in stats.values())),
                tiempo_total_s=round(time.time() - T0, 1))
    tmp = est_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(info, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, est_path)
    log(f"guardado {salida} ({os.path.getsize(salida) // 1024} KB) · {len(stats)} mallas, "
        f"{info['totales']['triangulos']} triángulos · estadísticas en {est_path}")
    if omitidas:
        aviso("omitidas:", ", ".join(omitidas))


if __name__ == "__main__":
    main()
