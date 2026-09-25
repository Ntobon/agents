"""Exporta el modelo de mallas.py a GLB para el visor web, más centros.json. No toca el .blend.

Uso (siempre en segundo plano; las rutas con espacios van entre comillas):
  blender -b modelo.blend -P glb.py -- --salida modelo.glb --centros centros.json
          [--decimar 0.35] [--decimar-por clave=0.2,clave2=0.6] [--min-caras 2000]
          [--excluir clave,...] [--presupuesto-mb 8]

- Diezma COPIAS de las mallas (el .blend guardado no cambia: este script nunca guarda).
- Nodos con nombre ASCII = clave de la estructura; vértices ya en coordenadas del mundo (transformación
  identidad); sin materiales (el visor colorea desde su configuración), sin cámaras ni luces.
- glTF con +Y arriba: G = (Bx, Bz, -By).
- centros.json: {clave: {"centro": [X,Y,Z], "min": [...], "max": [...], "caras": n}} en coordenadas glTF.
- El visor incrusta el GLB en base64 (x1.33) dentro de un HTML que debe pesar < 16 MB: por encima de
  --presupuesto-mb (8) avisa y sugiere cuánto diezmar.
"""
import argparse
import json
import os
import re
import struct
import sys
import time
import unicodedata

import numpy as np
import bpy

sys.dont_write_bytecode = True   # no dejar __pycache__ de Blender dentro de la skill (Drive)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import coords  # noqa: E402  (scripts/coords.py)

T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def aviso(*a):
    print(f"[{time.time() - T0:7.1f}s] AVISO:", *a, flush=True)


def argumentos():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="glb.py", description="Modelo de Blender -> GLB liviano + centros.json.")
    ap.add_argument("--salida", required=True, help="ruta del .glb")
    ap.add_argument("--centros", required=True, help="ruta de centros.json")
    ap.add_argument("--decimar", type=float, default=0.35, help="fracción de triángulos que se conserva (defecto 0.35)")
    ap.add_argument("--decimar-por", default="", help="fracción por estructura: clave=0.2,clave2=0.6")
    ap.add_argument("--min-caras", type=int, default=2000, help="no diezmar por debajo de estos triángulos (defecto 2000)")
    ap.add_argument("--excluir", default="", help="claves que no van al GLB, separadas por coma")
    ap.add_argument("--presupuesto-mb", type=float, default=8.0, help="tamaño a partir del cual se avisa (defecto 8)")
    return ap.parse_args(argv)


def ascii_seguro(clave):
    if re.fullmatch(r"[A-Za-z0-9_]+", clave):
        return clave
    s = unicodedata.normalize("NFKD", clave).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s).strip("_") or "estructura"
    aviso(f"la clave '{clave}' no es ASCII simple; en el GLB queda como '{s}'")
    return s


def triangulos(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def vertices_mundo(me):
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def filtrar(op, kw):
    validos = set(op.get_rna_type().properties.keys())
    fuera = [k for k in kw if k not in validos]
    if fuera:
        log("opciones del exportador que esta versión no tiene (se omiten):", ", ".join(fuera))
    return {k: v for k, v in kw.items() if k in validos}


def leer_glb(ruta):
    """Lee el bloque JSON del GLB: nombres de nodos con malla y min/max de POSITION."""
    with open(ruta, "rb") as f:
        magia, _, _ = struct.unpack("<4sII", f.read(12))
        if magia != b"glTF":
            raise ValueError("no es un GLB")
        largo, tipo = struct.unpack("<I4s", f.read(8))
        g = json.loads(f.read(largo).decode("utf-8"))
    nodos = {}
    for n in g.get("nodes", []):
        if "mesh" not in n:
            continue
        prims = g["meshes"][n["mesh"]]["primitives"]
        acc = [g["accessors"][p["attributes"]["POSITION"]] for p in prims]
        nodos[n.get("name")] = dict(min=np.min([a["min"] for a in acc], 0), max=np.max([a["max"] for a in acc], 0),
                                    trs=any(k in n for k in ("translation", "rotation", "scale", "matrix")),
                                    material=any("material" in p for p in prims))
    return nodos


def main():
    a = argumentos()
    blend = bpy.data.filepath
    mtime = os.path.getmtime(blend) if blend and os.path.exists(blend) else None
    salida, centros_ruta = os.path.abspath(a.salida), os.path.abspath(a.centros)
    excluir = {x.strip() for x in a.excluir.split(",") if x.strip()}
    por = {}
    for par in filter(None, (x.strip() for x in a.decimar_por.split(","))):
        k, _, v = par.partition("=")
        por[k.strip()] = float(v)
    sc = bpy.context.scene
    OB = {ob["clave"]: ob for ob in sc.objects if ob.type == "MESH" and "clave" in ob.keys()}
    if not OB:
        aviso("el .blend no tiene objetos con la propiedad 'clave'; se usan todas las mallas por nombre")
        OB = {ob.name: ob for ob in sc.objects if ob.type == "MESH"}
    for k in sorted(excluir - set(OB)):
        aviso(f"--excluir: '{k}' no está en el modelo")
    for k in sorted(set(por) - set(OB)):
        aviso(f"--decimar-por: '{k}' no está en el modelo")
    claves = [k for k in OB if k not in excluir]
    if not claves:
        raise SystemExit("no queda ninguna estructura para exportar")
    for ob in OB.values():                      # liberar los nombres para las copias (solo en memoria)
        ob.name = "_original_" + ob.name
        ob.data.name = "_original_" + ob.data.name
    coll = bpy.data.collections.new("_glb")
    sc.collection.children.link(coll)
    copias, info = [], {}
    for k in claves:
        ob = OB[k]
        nombre = ascii_seguro(k)
        t0 = triangulos(ob.data)
        ratio = min(1.0, max(por.get(k, a.decimar), a.min_caras / max(1, t0)))
        mod = None
        if ratio < 1.0:
            mod = ob.modifiers.new("_glb_diezmar", "DECIMATE")
            mod.decimate_type = "COLLAPSE"
            mod.ratio = ratio
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        if mod is not None:
            ob.modifiers.remove(mod)
        me.transform(ob.matrix_world)          # vértices en el mundo, nodo con transformación identidad
        me.materials.clear()
        me.validate(clean_customdata=False)
        me.shade_smooth()
        me.name = nombre
        cp = bpy.data.objects.new(nombre, me)
        coll.objects.link(cp)
        copias.append(cp)
        G = coords.blender_a_gltf(vertices_mundo(me))
        mn, mx = G.min(0), G.max(0)
        t1 = triangulos(me)
        info[nombre] = {"centro": [round(float(x), 3) for x in (mn + mx) / 2],
                        "min": [round(float(x), 3) for x in mn], "max": [round(float(x), 3) for x in mx],
                        "caras": t1}
        log(f"{nombre:22s} triángulos {t0:7d} -> {t1:7d} (fracción {ratio:.2f})")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for cp in copias:
        cp.select_set(True)
    bpy.context.view_layer.objects.active = copias[0]
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    op = bpy.ops.export_scene.gltf
    kw = filtrar(op, dict(filepath=salida, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=True, export_materials="NONE", export_texcoords=False, export_normals=True,
                          export_tangents=False, export_cameras=False, export_lights=False, export_animations=False,
                          export_extras=False, export_draco_mesh_compression_enable=False,
                          export_meshopt_compression_enable=False, export_attributes=False))
    op(**kw)
    tmp = centros_ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(info, fh, ensure_ascii=True, indent=1)
    os.replace(tmp, centros_ruta)

    # verificación: nombres de nodos = claves, sin transformaciones ni materiales, cajas = centros.json
    nodos = leer_glb(salida)
    faltan = sorted(set(info) - set(nodos))
    sobran = sorted(set(nodos) - set(info))
    err = max((float(np.abs(nodos[k]["min"] - info[k]["min"]).max()) for k in info if k in nodos), default=0.0)
    con_trs = [k for k, n in nodos.items() if n["trs"]]
    con_mat = [k for k, n in nodos.items() if n["material"]]
    if faltan or sobran or con_trs or con_mat or err > 0.01:
        aviso(f"verificación del GLB: faltan {faltan}, sobran {sobran}, con transformación {con_trs}, "
              f"con material {con_mat}, error de caja {err:.4f}")
    else:
        log(f"verificación del GLB: {len(nodos)} nodos = claves, identidad, sin materiales, cajas iguales a centros.json")
    mb = os.path.getsize(salida) / 1e6
    total = sum(v["caras"] for v in info.values())
    log(f"GLB: {salida} · {mb:.2f} MB ({mb * 4 / 3:.2f} MB en base64) · {len(info)} estructuras · {total} triángulos")
    log(f"centros: {centros_ruta}")
    if mb > a.presupuesto_mb:
        s = a.presupuesto_mb / mb * 0.95
        gruesas = sorted(info.items(), key=lambda kv: -kv[1]["caras"])[:4]
        sug = ",".join("%s=%.2f" % (k, max(0.02, min(1.0, por.get(k, a.decimar)) * s)) for k, _ in gruesas)
        pesadas = ", ".join("%s (%d)" % (k, v["caras"]) for k, v in gruesas)
        aviso(f"el GLB pesa {mb:.1f} MB (> {a.presupuesto_mb:.0f} MB). El visor lo incrusta en base64 dentro de un "
              f"HTML que debe quedar < 16 MB. Las más pesadas (triángulos): {pesadas}. "
              f"Probar --decimar {a.decimar * s:.2f} o --decimar-por {sug}, o --excluir lo que el visor no use.")
    if mtime is not None:
        log("el .blend no se modificó" if os.path.getmtime(blend) == mtime else "AVISO: el .blend cambió de fecha")


if __name__ == "__main__":
    main()
