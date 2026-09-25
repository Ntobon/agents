"""Fotos (PNG) por cámara y video de giro (MP4) del modelo que dejó mallas.py.

Uso (siempre en segundo plano; las rutas con espacios van entre comillas):
  blender -b modelo.blend -P render.py -- --camaras camaras.json --salida "<carpeta>"
          [--video giro.mp4 --segundos 10 --fps 24 --camara frente] [--resolucion W H]
          [--muestras N] [--solo frente,detalle] [--sin-fotos] [--guardar escena.blend]

camaras.json (ver camaras-ejemplo.json):
  {"fondo": "#131416", "resolucion": [1600, 1200], "resolucion_video": [1080, 1080],
   "camaras": [{"nombre": "frente", "tipo": "frente", "archivo": "01 Frente.png",
                "azimut": 0, "elevacion": 0, "encuadre": [claves], "ocultar": [claves],
                "solo": [claves], "alpha": {clave: 0.2}, "ocupacion": [0.5, 0.9],
                "etiquetas": [{"texto": "Título: detalle", "clave": "lesion", "lado": "izquierda"}]}]}

Tipos de cámara (azimut positivo = hacia la izquierda del paciente; elevación positiva = desde arriba):
  frente 0°/0° (cámara en -y: la izquierda del paciente a la derecha de la pantalla, cabeza arriba) ·
  oblicua 35°/0° · lateral 90°/0° (desde la izquierda del paciente: anterior a la izquierda, como un sagital) ·
  lateral_derecha -90° · atras 180° · arriba 0°/90° (anterior abajo) · abajo 0°/-90° (como un axial:
  anterior arriba, izquierda del paciente a la derecha) · detalle (encuadre ajustado a las claves de
  "encuadre") · orbita (azimut y elevación libres).

El giro usa un Empty pivote en el centro del encuadre con la cámara (y las luces) como hijos, rotación
lineal 0-360° y H.264. Antes de animar se borran los marcadores de la línea de tiempo: un marcador
atado a una cámara congela el giro en esa cámara.
"""
import argparse
import json
import math
import os
import shutil
import sys
import textwrap
import time

import numpy as np
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode = True   # no dejar __pycache__ de Blender dentro de la skill (Drive)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import coords  # noqa: E402  (scripts/coords.py)

T0 = time.time()
MARCA = "render_py"          # propiedad de los objetos que crea este script (se borran al repetir)
TIPOS = {"frente": (0, 0), "oblicua": (35, 0), "lateral": (90, 0), "lateral_derecha": (-90, 0),
         "atras": (180, 0), "arriba": (0, 90), "abajo": (0, -90), "detalle": (0, 0), "orbita": (0, 0)}
R_REF = 27.6                 # semidiagonal (cm) del modelo con el que se calibraron las luces
LUCES = [  # nombre, posición relativa (cm, con R_REF), energía (W), tamaño (cm), sombra
    ("Luz principal", (-70, -110, 85), 260000, 90, True),
    ("Luz de relleno", (115, -70, 10), 120000, 110, False),
    ("Luz de contorno", (40, 130, 70), 110000, 90, False),
]
COL_ETIQ = {"titulo": "#ffffff", "texto": "#c9ced6", "fondo": "#202328", "linea": "#e6e8eb",
            "nota": "#8a9099", "contorno": "#0e1012"}


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def aviso(*a):
    print(f"[{time.time() - T0:7.1f}s] AVISO:", *a, flush=True)


def argumentos():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="render.py", description="Fotos y video de giro del modelo 3D.")
    ap.add_argument("--camaras", required=True, help="camaras.json")
    ap.add_argument("--salida", required=True, help="carpeta de salida de las fotos (y del video si su ruta es relativa)")
    ap.add_argument("--video", help="nombre o ruta del MP4 del giro (sin esto no se hace video)")
    ap.add_argument("--segundos", type=float, default=10.0, help="duración del giro (defecto 10)")
    ap.add_argument("--fps", type=int, default=24, help="cuadros por segundo (defecto 24)")
    ap.add_argument("--camara", help="cámara de camaras.json (o tipo) que define el giro (defecto: la primera)")
    ap.add_argument("--resolucion", type=int, nargs=2, metavar=("W", "H"),
                    help="resolución de fotos y video (defecto 1600x1200 fotos, 1080x1080 video)")
    ap.add_argument("--muestras", type=int, help="muestras EEVEE (defecto 64 fotos, 16 video)")
    ap.add_argument("--solo", help="renderizar solo estas cámaras (nombres separados por coma)")
    ap.add_argument("--sin-fotos", action="store_true", help="no renderizar fotos (solo el video)")
    ap.add_argument("--guardar", help="guardar además un .blend con cámaras, luces y etiquetas")
    return ap.parse_args(argv)


# ------------------------------------------------------------------ utilidades
def srgb_a_lineal(hx):
    h = str(hx).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def arbol(idblock):
    if idblock.node_tree is None:
        idblock.use_nodes = True
    return idblock.node_tree


def coleccion(nombre, padre=None):
    c = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    p = padre or bpy.context.scene.collection
    if c.name not in [x.name for x in p.children]:
        p.children.link(c)
    return c


def vertices_mundo(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


def direccion(az, el):
    """Vector unitario del objetivo hacia la cámara (azimut 0 = cámara en -y, delante del paciente)."""
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def arriba_de(az, el):
    """'Arriba' de la pantalla: +z proyectado; en las vistas cenitales, continuo con la de frente."""
    a, e = math.radians(az), math.radians(el)
    return Vector((-math.sin(e) * math.sin(a), math.sin(e) * math.cos(a), math.cos(e)))


def orientar(ob, adelante, arriba):
    f = adelante.normalized()
    r = f.cross(arriba).normalized()
    u = r.cross(f).normalized()
    ob.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()


def base(cam):
    mw = cam.matrix_world
    R = mw.to_3x3().normalized()
    return (np.array(mw.translation), np.array(R @ Vector((1, 0, 0))), np.array(R @ Vector((0, 1, 0))),
            np.array(-(R @ Vector((0, 0, 1)))))


def proyeccion(cam, P):
    """Coordenadas tangentes (x/z, y/z) y profundidad z de los puntos P vistos desde la cámara."""
    pos, r, u, f = base(cam)
    d = P - pos
    z = d @ f
    return (d @ r) / z, (d @ u) / z, z


def emisivo(nombre, hx):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre)
    nt = arbol(m)
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*srgb_a_lineal(hx), 1)
    em.inputs[1].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    m.diffuse_color = (*srgb_a_lineal(hx), 1)
    m[MARCA] = True
    return m


def bsdf(ob):
    m = ob.active_material
    if m is None or m.node_tree is None:
        return None
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


# ------------------------------------------------------------------ escena
def limpiar_previos():
    for ob in list(bpy.data.objects):
        if ob.get(MARCA):
            bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.get(MARCA) and not c.objects and not c.children:
            bpy.data.collections.remove(c)


def preparar_escena(fondo, muestras):
    sc = bpy.context.scene
    sc.timeline_markers.clear()
    mundo = bpy.data.worlds.get("Fondo") or bpy.data.worlds.new("Fondo")
    sc.world = mundo
    nt = arbol(mundo)
    nt.nodes.clear()
    lp = nt.nodes.new("ShaderNodeLightPath")
    fondo_cam = nt.nodes.new("ShaderNodeBackground")      # lo que ve la cámara: el color de fondo
    fondo_cam.inputs[0].default_value = (*srgb_a_lineal(fondo), 1)
    fondo_luz = nt.nodes.new("ShaderNodeBackground")      # lo que ilumina: un gris neutro
    fondo_luz.inputs[0].default_value = (0.30, 0.30, 0.31, 1)
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    salida = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(lp.outputs["Is Camera Ray"], mezcla.inputs[0])
    nt.links.new(fondo_luz.outputs[0], mezcla.inputs[1])
    nt.links.new(fondo_cam.outputs[0], mezcla.inputs[2])
    nt.links.new(mezcla.outputs[0], salida.inputs[0])
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = muestras
    sc.render.film_transparent = False
    sc.render.resolution_percentage = 100
    # 'Standard': el color del render es el hex del estilo (AgX/Filmic lo desaturan)
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0


def luces(centro, R, coll):
    s = max(R, 1e-3) / R_REF
    obs = []
    for nombre, p, energia, tam, sombra in LUCES:
        ld = bpy.data.lights.new(nombre, "AREA")
        ld.energy = energia * s * s
        ld.shape = "DISK"
        ld.size = tam * s
        ld.use_shadow = sombra
        ob = bpy.data.objects.new(nombre, ld)
        ob[MARCA] = True
        coll.objects.link(ob)
        ob.location = Vector(centro) + Vector(p) * s
        orientar(ob, Vector(centro) - ob.location, Vector((0, 0, 1)))
        obs.append(ob)
    return obs


def crear_camara(nombre, objetivo, az, el, dist, P, wfrac, hfrac, aspecto, coll, centrar=True):
    cd = bpy.data.cameras.new(nombre)
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0
    cam = bpy.data.objects.new(nombre, cd)
    cam[MARCA] = True
    coll.objects.link(cam)
    d = direccion(az, el)
    cam.location = Vector(objetivo) + d * dist
    orientar(cam, -d, arriba_de(az, el))
    bpy.context.view_layer.update()
    rx, ry, z = proyeccion(cam, P)
    if centrar:  # recentrar la cámara en el centro de la proyección
        _, r, u, _ = base(cam)
        cx, cy = (rx.max() + rx.min()) / 2, (ry.max() + ry.min()) / 2
        cam.location = cam.location + Vector(r) * (cx * dist) + Vector(u) * (cy * dist)
        bpy.context.view_layer.update()
        rx, ry, z = proyeccion(cam, P)
    ajustar_lente(cd, rx, ry, wfrac, hfrac, aspecto)
    cd.clip_start = max(0.1, float(z.min()) * 0.05)
    cd.clip_end = float(z.max()) * 4 + 100
    return cam


def ajustar_lente(cd, rx, ry, wfrac, hfrac, aspecto):
    ax = max(float(np.abs(rx).max()), 1e-6)
    ay = max(float(np.abs(ry).max()), 1e-6)
    k = min((wfrac / 2) / ax, (hfrac / 2) / (aspecto * ay))
    cd.lens = k * cd.sensor_width


# ------------------------------------------------------------------ etiquetas
def envolver(texto, ancho=30):
    if "\n" in texto:
        return texto
    return "\n".join(textwrap.wrap(texto, ancho)) or texto


def largo_titulo(e, texto):
    t = e.get("titulo")
    if isinstance(t, str) and texto.replace("\n", " ").startswith(t):
        return len(t)
    plano = texto
    if ":" in plano:
        return plano.index(":") + 1
    return 0


BVH = {}


def bvh_de(ob):
    if ob.name not in BVH:
        me = ob.data
        me.calc_loop_triangles()
        tri = np.empty(len(me.loop_triangles) * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", tri)
        V = vertices_mundo(ob)
        BVH[ob.name] = (BVHTree.FromPolygons(V.tolist(), tri.reshape(-1, 3).tolist()), V)
    return BVH[ob.name]


def alfa_actual(ob):
    b = bsdf(ob)
    return float(b.inputs["Alpha"].default_value) if b else 1.0


def ancla(pos, ob, objetivo, oclusores, right, up, fwd):
    """Punto de `ob` donde termina la línea guía: el primero que ve la cámara en dirección al objetivo;
    si otra estructura casi opaca lo tapa, el punto visible de `ob` más cercano en pantalla al objetivo."""
    bvh, V = bvh_de(ob)
    d = objetivo - pos
    hit = bvh.ray_cast(pos, d.normalized(), d.length * 2)
    A0 = hit[0]
    if A0 is None:
        cerca = bvh.find_nearest(objetivo)
        A0 = cerca[0] if cerca[0] is not None else objetivo

    def tapado(p):
        dv = p - pos
        L = dv.length
        return any(b.ray_cast(pos, dv / L, L - 0.05)[0] is not None for b in oclusores)
    if not oclusores or not tapado(A0):
        return A0
    P = V if len(V) <= 6000 else V[np.linspace(0, len(V) - 1, 6000).astype(int)]
    p0, r, u, f = np.array(pos), np.array(right), np.array(up), np.array(fwd)
    dd, t = P - p0, np.array(objetivo) - p0
    z, zt = dd @ f, t @ f
    dist2 = ((dd @ r) / z - (t @ r) / zt) ** 2 + ((dd @ u) / z - (t @ u) / zt) ** 2
    for idx in np.argsort(dist2)[:400]:
        p = Vector(P[idx].tolist())
        dv = p - pos
        h = bvh.ray_cast(pos, dv.normalized(), dv.length + 0.1)
        if h[0] is None or (h[0] - p).length > 0.3:   # vértice en la cara de atrás de la propia estructura
            continue
        if not tapado(h[0]):
            return h[0]
    return A0     # todo tapado (p. ej. una luz dentro de la lesión): se ve a través de la translucidez


def objeto_malla(nombre, verts, caras, mat, coll):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v) for v in verts], [], caras)
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    ob[MARCA] = True
    coll.objects.link(ob)
    ob.visible_shadow = False
    return ob


def disco(centro, der, arr, r, n=24):
    return [centro + (der * math.cos(2 * math.pi * i / n) + arr * math.sin(2 * math.pi * i / n)) * r
            for i in range(n)], [tuple(range(n))]


def curva(nombre, puntos, grosor, mat, coll):
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = grosor
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(puntos) - 1)
    for i, p in enumerate(puntos):
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
    cu.materials.append(mat)
    ob = bpy.data.objects.new(nombre, cu)
    ob[MARCA] = True
    coll.objects.link(ob)
    ob.visible_shadow = False
    return ob


def construir_etiquetas(cam, nombre_cam, etiquetas, OB, P_vis, P_enc, W, H, coll, centro_mm):
    aspecto = W / H
    pos_np, r_np, u_np, f_np = base(cam)
    pos, right, up, fwd = Vector(pos_np), Vector(r_np), Vector(u_np), Vector(f_np)
    k_ = cam.data.lens / cam.data.sensor_width
    _, _, z_vis = proyeccion(cam, P_vis)
    rx_e, _, _ = proyeccion(cam, P_enc)
    D = float(z_vis.min()) - max(1.0, 0.02 * float(z_vis.min()))   # plano de etiquetas: delante de todo lo visible
    Wd = D / k_
    Hd = Wd / aspecto
    px = Wd / 1600.0          # "píxel de referencia" (el diseño se calibró a 1600 px de ancho)
    centro = pos + fwd * D

    def plano(a, b, dz=0.0):
        return centro + right * a + up * b + fwd * dz
    em, pad, barra, hueco = 27 * px, 11 * px, 7 * px, 10 * px
    m_tit, m_txt = emisivo("Etiqueta · título", COL_ETIQ["titulo"]), emisivo("Etiqueta · texto", COL_ETIQ["texto"])
    m_fondo, m_linea = emisivo("Etiqueta · fondo", COL_ETIQ["fondo"]), emisivo("Etiqueta · línea", COL_ETIQ["linea"])
    m_cont = emisivo("Etiqueta · contorno", COL_ETIQ["contorno"])
    items = []
    for n, e in enumerate(etiquetas, 1):
        texto = envolver(str(e.get("texto", "")), int(e.get("ancho", 30)))
        ob = OB.get(e.get("clave")) if e.get("clave") else None
        if e.get("clave") and (ob is None or ob.hide_render):
            aviso(f"etiqueta {n} de '{nombre_cam}': '{e.get('clave')}' no existe o está oculta; va como nota sin línea")
            ob = None
        objetivo = None
        if e.get("punto"):
            objetivo = Vector(e["punto"])
        elif e.get("punto_lps") and centro_mm is not None:
            objetivo = Vector(coords.lps_a_blender({"centro_mm": centro_mm}, e["punto_lps"]).tolist())
        elif ob is not None:
            objetivo = Vector(vertices_mundo(ob).mean(0).tolist())
        A = None
        if objetivo is not None:
            if ob is not None:
                ocl = [bvh_de(o)[0] for o in OB.values()
                       if o is not ob and not o.hide_render and alfa_actual(o) >= 0.5]
                A = ancla(pos, ob, objetivo, ocl, right, up, fwd)
            else:
                A = objetivo
            d = A - pos
            z = d.dot(fwd)
            u_a, v_a = 0.5 + k_ * d.dot(right) / z, 0.5 + k_ * aspecto * d.dot(up) / z
        lado = e.get("lado")
        if lado not in ("izquierda", "derecha"):
            lado = "derecha" if A is None or u_a >= 0.5 else "izquierda"
        nombre = f"Etiqueta {n} · {nombre_cam}"
        cu = bpy.data.curves.new(nombre, "FONT")
        cu.body = texto
        cu.size = em
        cu.align_x = "RIGHT" if lado == "izquierda" else "LEFT"
        cu.align_y = "CENTER"
        cu.space_line = 1.08
        cu.resolution_u = 5
        cu.materials.append(m_tit)
        cu.materials.append(m_txt)
        nt = largo_titulo(e, texto)
        for ci, ch in enumerate(cu.body_format):
            ch.material_index = 0 if ci < nt else 1
        to = bpy.data.objects.new(nombre, cu)
        to[MARCA] = True
        coll.objects.link(to)
        to.visible_shadow = False
        to.rotation_euler = cam.rotation_euler.copy()
        sw = ob.get("color") if ob is not None else None
        items.append(dict(n=n, lado=lado, txt=to, A=A, depth=(A - pos).dot(fwd) if A is not None else None,
                          want_b=((v_a - 0.5) * Hd) if A is not None else -Hd * 0.5,
                          swatch=emisivo("Etiqueta · color " + str(sw), sw) if sw else emisivo("Etiqueta · nota", COL_ETIQ["nota"])))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for it in items:
        bb = [Vector(c) for c in it["txt"].evaluated_get(dg).bound_box]
        it["xmin"], it["xmax"] = min(c.x for c in bb), max(c.x for c in bb)
        it["ymin"], it["ymax"] = min(c.y for c in bb), max(c.y for c in bb)
        it["h"] = (it["ymax"] - it["ymin"]) + 2 * pad
        it["w"] = (it["xmax"] - it["xmin"]) + 2 * pad + barra + hueco
    # columnas junto a la silueta de lo encuadrado; sin solaparse (pasada de arriba abajo y de abajo arriba)
    umin, umax = 0.5 + k_ * float(rx_e.min()), 0.5 + k_ * float(rx_e.max())
    margen = 0.012 * Wd
    for lado in ("izquierda", "derecha"):
        col = sorted([it for it in items if it["lado"] == lado], key=lambda t: -t["want_b"])
        if not col:
            continue
        tope, piso, g = Hd / 2 - 0.035 * Hd, -Hd / 2 + 0.035 * Hd, 0.022 * Hd
        prev = None
        for it in col:
            lim = tope - it["h"] / 2 if prev is None else prev["b"] - prev["h"] / 2 - g - it["h"] / 2
            it["b"] = min(it["want_b"], lim)
            prev = it
        sig = None
        for it in reversed(col):
            lim = piso + it["h"] / 2 if sig is None else sig["b"] + sig["h"] / 2 + g + it["h"] / 2
            it["b"] = max(it["b"], lim)
            sig = it
        for it in col:
            if lado == "izquierda":
                interior = max((umin - 0.5) * Wd - 0.015 * Wd, -Wd / 2 + margen + it["w"])
                it["interior"], it["exterior"] = interior, interior - it["w"]
            else:
                interior = min((umax - 0.5) * Wd + 0.015 * Wd, Wd / 2 - margen - it["w"])
                it["interior"], it["exterior"] = interior, interior + it["w"]
    for it in items:
        n, to = it["n"], it["txt"]
        sgn = 1 if it["lado"] == "izquierda" else -1
        borde_txt = it["interior"] - sgn * (barra + hueco + pad)
        ax_ = borde_txt - (it["xmax"] if it["lado"] == "izquierda" else it["xmin"])
        to.location = plano(ax_, it["b"] - (it["ymin"] + it["ymax"]) / 2)
        a0, a1 = sorted((it["exterior"], it["interior"]))
        b0, b1 = it["b"] - it["h"] / 2, it["b"] + it["h"] / 2
        objeto_malla(f"Etiqueta {n} · fondo · {nombre_cam}",
                     [plano(a0, b0, 0.15), plano(a1, b0, 0.15), plano(a1, b1, 0.15), plano(a0, b1, 0.15)],
                     [(0, 1, 2, 3)], m_fondo, coll)
        s0, s1 = sorted((it["interior"] - sgn * barra, it["interior"]))
        objeto_malla(f"Etiqueta {n} · color · {nombre_cam}",
                     [plano(s0, b0, 0.08), plano(s1, b0, 0.08), plano(s1, b1, 0.08), plano(s0, b1, 0.08)],
                     [(0, 1, 2, 3)], it["swatch"], coll)
        if it["A"] is not None:
            A = it["A"]
            F = pos + (A - pos) * (D / it["depth"])      # mismo píxel que A, sobre el plano de etiquetas
            ini = plano(it["interior"], it["b"])
            curva(f"Etiqueta {n} · guía · {nombre_cam}", [ini, F, A], 1.25 * px, m_linea, coll)
            curva(f"Etiqueta {n} · guía contorno · {nombre_cam}", [ini + fwd * 0.12, F + fwd * 0.12], 2.6 * px, m_cont, coll)
            v, c = disco(F - fwd * 0.05, right, up, 4.5 * px)
            objeto_malla(f"Etiqueta {n} · punto · {nombre_cam}", v, c, m_linea, coll)
            v, c = disco(F + fwd * 0.02, right, up, 7.0 * px)
            objeto_malla(f"Etiqueta {n} · punto contorno · {nombre_cam}", v, c, m_cont, coll)
    return len(items)


# ------------------------------------------------------------------ cámaras
def aplicar(spec, OB):
    """Oculta y cambia alfas según la cámara. Devuelve la función que deshace los cambios."""
    previo_vis = {k: ob.hide_render for k, ob in OB.items()}
    previo_alpha = {}
    solo = set(spec.get("solo") or [])
    ocultar = set(spec.get("ocultar") or [])
    for k, ob in OB.items():
        if (solo and k not in solo) or k in ocultar:
            ob.hide_render = True
    for k, a in (spec.get("alpha") or {}).items():
        ob = OB.get(k)
        b = bsdf(ob) if ob else None
        if b is None:
            aviso(f"alpha: '{k}' no existe o no tiene Principled BSDF")
            continue
        previo_alpha[k] = (b.inputs["Alpha"].default_value, ob.active_material.use_backface_culling)
        b.inputs["Alpha"].default_value = float(a)
        ob.active_material.use_backface_culling = float(a) < 1.0
    faltan = [k for k in (spec.get("encuadre") or []) + list(ocultar) + list(solo) if k not in OB]
    if faltan:
        aviso(f"cámara '{spec.get('nombre')}': claves que no están en el modelo: {', '.join(sorted(set(faltan)))}")

    def deshacer():
        for k, v in previo_vis.items():
            OB[k].hide_render = v
        for k, (a, cull) in previo_alpha.items():
            bsdf(OB[k]).inputs["Alpha"].default_value = a
            OB[k].active_material.use_backface_culling = cull
    return deshacer


def puntos(OB, claves=None):
    obs = [OB[k] for k in (claves or []) if k in OB] if claves else [ob for ob in OB.values() if not ob.hide_render]
    if not obs:
        obs = [ob for ob in OB.values() if not ob.hide_render]
    return np.concatenate([vertices_mundo(ob) for ob in obs])


def angulos(spec):
    tipo = spec.get("tipo") or (spec.get("nombre") if spec.get("nombre") in TIPOS else "frente")
    if tipo not in TIPOS:
        aviso(f"tipo de cámara desconocido '{tipo}'; se usa 'frente'")
        tipo = "frente"
    az, el = TIPOS[tipo]
    return tipo, float(spec.get("azimut", az)), float(spec.get("elevacion", el))


def diagonal(P):
    return float(np.linalg.norm(P.max(0) - P.min(0)))


def poner_salida_imagen(sc):
    try:
        sc.render.image_settings.media_type = "IMAGE"
    except Exception:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.compression = 15


# ------------------------------------------------------------------ video
def curvas_lineales(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    fcs = list(getattr(ad.action, "fcurves", []) or [])
    try:  # acciones por capas (Blender 4.4+)
        for capa in ad.action.layers:
            for tira in capa.strips:
                for cb in tira.channelbags:
                    fcs += list(cb.fcurves)
    except Exception:
        pass
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def video(a, spec, OB, coll, luces_obs, salida_dir, W, H, muestras):
    sc = bpy.context.scene
    sc.timeline_markers.clear()          # los marcadores atados a cámaras congelan el giro
    for c in bpy.data.collections:       # sin etiquetas en el video
        if c.get(MARCA) and c.name.startswith("Etiquetas"):
            c.hide_render = True
    deshacer = aplicar(spec, OB)
    tipo, az, el = angulos(spec)
    if "elevacion" not in spec and tipo not in ("arriba", "abajo"):
        el = 5.0                         # un poco desde arriba: da volumen al giro
    P = puntos(OB, spec.get("encuadre"))
    centro = (P.min(0) + P.max(0)) / 2
    dist = max(3.0 * diagonal(P), 1.5 * diagonal(puntos(OB)))
    piv = bpy.data.objects.new("Giro · pivote", None)
    piv[MARCA] = True
    coll.objects.link(piv)
    piv.location = Vector(centro)
    cd = bpy.data.cameras.new("Giro · cámara")
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0
    cam = bpy.data.objects.new("Giro · cámara", cd)
    cam[MARCA] = True
    coll.objects.link(cam)
    cam.parent = piv
    cam.location = direccion(az, el) * dist
    orientar(cam, -direccion(az, el), arriba_de(az, el))
    bpy.context.view_layer.update()
    for lz in luces_obs:                 # las luces giran con la cámara: iluminación constante en pantalla
        mw = lz.matrix_world.copy()
        lz.parent = piv
        lz.matrix_parent_inverse = piv.matrix_world.inverted()
        lz.matrix_world = mw
    # lente que encuadra el modelo en todo el giro (probando cada 10°)
    ocup = spec.get("ocupacion_video") or [0.9, 0.9]
    rxs, rys, zs = [], [], []
    for g in range(0, 360, 10):
        piv.rotation_euler = (0, 0, math.radians(g))
        bpy.context.view_layer.update()
        rx, ry, z = proyeccion(cam, P)
        rxs.append(np.abs(rx).max())
        rys.append(np.abs(ry).max())
        zs.append(z.min())
    ajustar_lente(cd, np.array(rxs), np.array(rys), ocup[0], ocup[1], W / H)
    cd.clip_start = max(0.1, float(min(zs)) * 0.05)
    cd.clip_end = dist * 4 + 100
    n = max(2, int(round(a.segundos * a.fps)))
    prefs = bpy.context.preferences.edit
    interp = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    piv.rotation_euler = (0, 0, 0)
    piv.keyframe_insert("rotation_euler", index=2, frame=1)
    piv.rotation_euler = (0, 0, 2 * math.pi)
    piv.keyframe_insert("rotation_euler", index=2, frame=n + 1)   # n+1 = n: el giro cierra sin salto
    prefs.keyframe_new_interpolation_type = interp
    curvas_lineales(piv)
    sc.camera = cam
    r = sc.render
    r.resolution_x, r.resolution_y = W - W % 2, H - H % 2          # H.264 exige dimensiones pares
    r.fps, r.fps_base = a.fps, 1.0
    sc.frame_start, sc.frame_end = 1, n
    sc.eevee.taa_render_samples = muestras
    try:
        r.image_settings.media_type = "VIDEO"                      # Blender 5.x
    except Exception:
        pass
    r.image_settings.file_format = "FFMPEG"
    r.image_settings.color_mode = "RGB"
    r.ffmpeg.format = "MPEG4"
    r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = "HIGH"
    r.ffmpeg.ffmpeg_preset = "GOOD"
    r.ffmpeg.audio_codec = "NONE"
    destino = a.video if os.path.isabs(a.video) else os.path.join(salida_dir, a.video)
    destino = os.path.abspath(destino)
    if not destino.lower().endswith(".mp4"):
        destino += ".mp4"
    tmp = os.path.join(os.path.dirname(destino), f".giro_tmp_{os.getpid()}")
    os.makedirs(tmp, exist_ok=True)
    r.filepath = os.path.join(tmp, "giro_")
    t = time.time()
    log(f"video: cámara '{spec.get('nombre', tipo)}' ({tipo}, azimut {az:.0f}°, elevación {el:.0f}°), "
        f"{n} cuadros a {a.fps} fps, {r.resolution_x}x{r.resolution_y}, {muestras} muestras, distancia {dist:.0f} cm")
    bpy.ops.render.render(animation=True)
    hechos = [f for f in os.listdir(tmp) if f.lower().endswith(".mp4")]
    if not hechos:
        raise SystemExit(f"el render de video no dejó ningún .mp4 en {tmp}")
    os.replace(os.path.join(tmp, hechos[0]), destino)
    shutil.rmtree(tmp, ignore_errors=True)
    log(f"video listo: {destino} ({os.path.getsize(destino) / 1e6:.1f} MB, {time.time() - t:.1f}s, "
        f"{(time.time() - t) / n:.2f} s/cuadro)")
    deshacer()


# ------------------------------------------------------------------ principal
def main():
    a = argumentos()
    with open(os.path.abspath(a.camaras), encoding="utf-8") as fh:
        conf = json.load(fh)
    salida_dir = os.path.abspath(a.salida)
    os.makedirs(salida_dir, exist_ok=True)
    sc = bpy.context.scene
    limpiar_previos()
    OB = {ob["clave"]: ob for ob in sc.objects if ob.type == "MESH" and "clave" in ob.keys()}
    if not OB:
        aviso("el .blend no tiene objetos con la propiedad 'clave' (¿no viene de mallas.py?); se usan todas las mallas por nombre")
        OB = {ob.name: ob for ob in sc.objects if ob.type == "MESH"}
    if not OB:
        raise SystemExit("no hay mallas en el .blend")
    fondo = conf.get("fondo") or sc.get("fondo") or "#131416"
    centro_mm = list(sc["centro_mm"]) if "centro_mm" in sc.keys() else None
    m_fotos = a.muestras or int(conf.get("muestras", 64))
    preparar_escena(fondo, m_fotos)
    coll = coleccion("Render")
    coll[MARCA] = True
    P_todo = puntos(OB, list(OB))
    centro = (P_todo.min(0) + P_todo.max(0)) / 2
    R = diagonal(P_todo) / 2
    luces_obs = luces(centro, R, coll)
    log(f"modelo: {len(OB)} estructuras, semidiagonal {R:.1f} cm; fondo {fondo}")
    camaras = conf.get("camaras") or [{"nombre": "frente", "tipo": "frente"}]
    for i, c in enumerate(camaras, 1):
        c.setdefault("nombre", f"camara{i}")
        c.setdefault("archivo", f"{i:02d} {c['nombre']}.png")
    W, H = a.resolucion or conf.get("resolucion") or (1600, 1200)
    hechas = []
    if not a.sin_fotos:
        poner_salida_imagen(sc)
        sc.render.resolution_x, sc.render.resolution_y = W, H
        pedidas = {x.strip() for x in a.solo.split(",")} if a.solo else None
        for c in camaras:
            if pedidas and c["nombre"] not in pedidas:
                continue
            t = time.time()
            deshacer = aplicar(c, OB)
            tipo, az, el = angulos(c)
            P_enc = puntos(OB, c.get("encuadre"))
            P_vis = puntos(OB)
            if tipo == "detalle" and not c.get("encuadre"):
                aviso(f"cámara '{c['nombre']}' es de detalle pero no tiene 'encuadre'; encuadra todo lo visible")
            etiquetas = c.get("etiquetas") or []
            ocup = c.get("ocupacion") or ([0.5, 0.9] if etiquetas else [0.88, 0.9])
            dist = max(3.0 * diagonal(P_enc), 1.5 * diagonal(P_vis))
            objetivo = (P_enc.min(0) + P_enc.max(0)) / 2
            cam = crear_camara(c["nombre"], objetivo, az, el, dist, P_enc, ocup[0], ocup[1], W / H, coll)
            ce = None
            if etiquetas:
                ce = coleccion("Etiquetas · " + c["nombre"], coll)
                ce[MARCA] = True
                construir_etiquetas(cam, c["nombre"], etiquetas, OB, P_vis, P_enc, W, H, ce, centro_mm)
            sc.camera = cam
            sc.render.filepath = os.path.join(salida_dir, c["archivo"])
            bpy.ops.render.render(write_still=True)
            if ce is not None:
                ce.hide_render = True
                ce.hide_viewport = True
            deshacer()
            hechas.append((c["nombre"], c["archivo"], cam))
            log(f"foto '{c['nombre']}' ({tipo}, az {az:.0f}°, el {el:.0f}°, {len(etiquetas)} etiquetas) -> "
                f"{c['archivo']} ({time.time() - t:.1f}s)")
    if a.guardar and hechas:
        primero = hechas[0]
        sc.camera = primero[2]
        ce = bpy.data.collections.get("Etiquetas · " + primero[0])
        if ce is not None:
            ce.hide_render = False
            ce.hide_viewport = False
        ruta = os.path.abspath(a.guardar)
        bpy.ops.wm.save_as_mainfile(filepath=ruta, compress=True, copy=True)
        log(f"escena guardada: {ruta} (cámara activa '{primero[0]}'; las etiquetas de las demás cámaras están ocultas)")
        if ce is not None:
            ce.hide_render = True
    if a.video:
        nombre = a.camara or camaras[0]["nombre"]
        spec = next((c for c in camaras if c["nombre"] == nombre), None)
        if spec is None:
            if nombre not in TIPOS:
                raise SystemExit(f"--camara '{nombre}' no está en camaras.json ni es un tipo conocido ({', '.join(TIPOS)})")
            spec = {"nombre": nombre, "tipo": nombre}
        if a.resolucion:
            Wv, Hv = a.resolucion
        else:
            Wv, Hv = conf.get("resolucion_video") or (1080, 1080)
        video(a, spec, OB, coll, luces_obs, salida_dir, Wv, Hv, a.muestras or int(conf.get("muestras_video", 16)))
    log("listo")


if __name__ == "__main__":
    main()
