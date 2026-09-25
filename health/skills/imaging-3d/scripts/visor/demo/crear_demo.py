"""Anatomía sintética para el ejemplo del visor (caso ficticio, sin datos de nadie).

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P crear_demo.py -- [--salida <carpeta>]

Crea, en glTF (+Y arriba, 1 unidad = 1 cm, +X = izquierda del paciente, +Z hacia adelante):
- organo_hueco   tubo curvo con una estrechez (la pared vista por fuera)
- lesion         manga que engruesa la pared alrededor de la estrechez
- luz            la luz dentro de la lesión (lo blanco: por donde pasa el contenido)
- organo_vecino  órgano sólido al lado
- nodulo         masa pequeña (para las etapas de tipo escala)
- envoltura      contorno translúcido (hace de piel)
y exporta demo.glb (sin materiales), demo-centros.json (caja por nodo) y demo-ruta.json (puntos de la
luz en glTF + radios en mm + la estrechez), con los nombres que usa config-ejemplo.json.

La curva es la misma Catmull-Rom centrípeta de three.js (misma fórmula y mismos extremos), así que los
tubos que el visor dibuja sobre la ruta (luz normal, etapas) caen exactamente sobre estas mallas.
"""
import json
import math
import os
import sys

import bpy
import bmesh
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(AQUI, "..", "..")))   # scripts/ (coords.py)
from coords import gltf_a_blender  # noqa: E402

K = 12   # muestras por tramo, como el visor

# Ruta de la luz (glTF, cm) y radio de la luz en mm por punto. Estrechez entre los puntos 6 y 10.
PUNTOS = [
    (-7.0, 8.0, 0.0), (-5.0, 8.6, 0.4), (-2.5, 8.2, 0.8), (-0.3, 6.9, 1.2), (1.2, 5.0, 1.5),
    (1.9, 3.0, 1.7), (2.05, 1.2, 1.8), (2.1, 0.0, 1.8), (2.1, -1.2, 1.8), (2.05, -2.4, 1.8),
    (1.9, -3.6, 1.7), (1.4, -5.3, 1.5), (0.2, -6.9, 1.2), (-1.8, -7.9, 0.9), (-4.2, -8.4, 0.6),
    (-6.6, -8.1, 0.3),
]
RADIOS_MM = [12, 13, 14, 15, 15, 12, 6, 3.5, 2.2, 3.5, 6, 9, 10, 10, 10, 10]
ESTRECHEZ = {"desde": 6, "hasta": 10}
PARED_EXT = [1.5, 1.6, 1.7, 1.8, 1.8, 1.5, 1.3, 1.3, 1.3, 1.3, 1.3, 1.25, 1.3, 1.3, 1.3, 1.3]   # cm, contorno del órgano
FIN_ORGANO = 11   # del 11 en adelante el visor lo dibuja como «tubo» (estructura dibujada)


def catmull_centripeta(P, K):
    """Igual que THREE.CatmullRomCurve3(P, false, 'centripetal').getPoint(k / M), k = 0..M."""
    P = [np.asarray(p, float) for p in P]
    n = len(P)
    M = (n - 1) * K
    out = []
    for k in range(M + 1):
        t = k / M
        p = (n - 1) * t
        ip = int(math.floor(p))
        w = p - ip
        if w == 0 and ip == n - 1:
            ip, w = n - 2, 1.0
        p0 = P[ip - 1] if ip > 0 else P[0] + (P[0] - P[1])
        p1, p2 = P[ip], P[ip + 1]
        p3 = P[ip + 2] if ip + 2 < n else P[n - 1] + (P[n - 1] - P[n - 2])
        dt0 = np.sum((p0 - p1) ** 2) ** 0.25
        dt1 = np.sum((p1 - p2) ** 2) ** 0.25
        dt2 = np.sum((p2 - p3) ** 2) ** 0.25
        if dt1 < 1e-4:
            dt1 = 1.0
        if dt0 < 1e-4:
            dt0 = dt1
        if dt2 < 1e-4:
            dt2 = dt1
        t1 = ((p1 - p0) / dt0 - (p2 - p0) / (dt0 + dt1) + (p2 - p1) / dt1) * dt1
        t2 = ((p2 - p1) / dt1 - (p3 - p1) / (dt1 + dt2) + (p3 - p2) / dt2) * dt1
        c0, c1 = p1, t1
        c2 = -3 * p1 + 3 * p2 - 2 * t1 - t2
        c3 = 2 * p1 - 2 * p2 + t1 + t2
        out.append(c0 + c1 * w + c2 * w * w + c3 * w * w * w)
    return np.array(out)


def marcos(pos):
    """Tangentes y marcos por transporte paralelo (como el visor)."""
    M = len(pos) - 1
    tan = np.array([pos[min(M, k + 1)] - pos[max(0, k - 1)] for k in range(M + 1)])
    tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    ref = np.array([0, 1, 0.0]) if abs(tan[0][1]) < 0.9 else np.array([1, 0, 0.0])
    nor = [np.cross(tan[0], ref) / np.linalg.norm(np.cross(tan[0], ref))]
    for k in range(1, M + 1):
        nk = nor[-1].copy()
        ax = np.cross(tan[k - 1], tan[k])
        sn = np.linalg.norm(ax)
        if sn > 1e-9:
            ax /= sn
            ang = math.atan2(sn, float(np.dot(tan[k - 1], tan[k])))
            nk = nk * math.cos(ang) + np.cross(ax, nk) * math.sin(ang) + ax * np.dot(ax, nk) * (1 - math.cos(ang))
        nk -= tan[k] * np.dot(nk, tan[k])
        nor.append(nk / np.linalg.norm(nk))
    nor = np.array(nor)
    return tan, nor, np.cross(tan, nor)


def valor(v, k, i0=0.0):
    x = k / K - i0
    i = int(math.floor(x))
    if i < 0:
        return v[0]
    if i >= len(v) - 1:
        return v[-1]
    f = x - i
    return v[i] + (v[i + 1] - v[i]) * f


def anillos(pos, nor, bi, k0, k1, radio_fn, n):
    """Vértices de anillos entre las muestras k0..k1 (radio_fn(k, u) con u = 0..1 a lo largo)."""
    ver = []
    for k in range(k0, k1 + 1):
        u = (k - k0) / max(1, k1 - k0)
        r = radio_fn(k, u)
        for j in range(n):
            a = 2 * math.pi * j / n
            ver.append(pos[k] + r * (-math.cos(a) * nor[k] + math.sin(a) * bi[k]))
    return ver


def caras_tubo(filas, n, base=0):
    caras = []
    for r in range(filas - 1):
        for j in range(n):
            a, b = base + r * n + j, base + r * n + (j + 1) % n
            caras.append((a, b, b + n, a + n))
    return caras


def tubo_cerrado(pos, nor, bi, k0, k1, radio_fn, n):
    ver = anillos(pos, nor, bi, k0, k1, radio_fn, n)
    filas = k1 - k0 + 1
    caras = caras_tubo(filas, n)
    ver.append(pos[k0])
    ver.append(pos[k1])
    c0, c1 = len(ver) - 2, len(ver) - 1
    ult = (filas - 1) * n
    for j in range(n):
        caras.append((c0, (j + 1) % n, j))
        caras.append((c1, ult + j, ult + (j + 1) % n))
    return ver, caras


def manga(pos, nor, bi, k0, k1, r_ext, r_int, n):
    """Pared anular cerrada (lesión de la pared): cara externa, interna y los dos anillos de los extremos."""
    ext = anillos(pos, nor, bi, k0, k1, r_ext, n)
    inn = anillos(pos, nor, bi, k0, k1, r_int, n)
    filas = k1 - k0 + 1
    ver = ext + inn
    caras = caras_tubo(filas, n) + caras_tubo(filas, n, base=len(ext))
    ult = (filas - 1) * n
    for j in range(n):
        jn = (j + 1) % n
        caras.append((j, len(ext) + j, len(ext) + jn, jn))
        caras.append((ult + j, ult + jn, len(ext) + ult + jn, len(ext) + ult + j))
    return ver, caras


def elipsoide(centro, radios, nu=40, nv=20):
    ver, caras = [], []
    c = np.asarray(centro, float)
    for i in range(1, nv):
        th = math.pi * i / nv
        for j in range(nu):
            ph = 2 * math.pi * j / nu
            ver.append(c + np.array([radios[0] * math.sin(th) * math.cos(ph), radios[1] * math.cos(th), radios[2] * math.sin(th) * math.sin(ph)]))
    for i in range(nv - 2):
        for j in range(nu):
            a, b = i * nu + j, i * nu + (j + 1) % nu
            caras.append((a, b, b + nu, a + nu))
    ver.append(c + np.array([0, radios[1], 0]))
    ver.append(c + np.array([0, -radios[1], 0]))
    top, bot, ult = len(ver) - 2, len(ver) - 1, (nv - 2) * nu
    for j in range(nu):
        caras.append((top, (j + 1) % nu, j))
        caras.append((bot, ult + j, ult + (j + 1) % nu))
    return ver, caras


def crear(nombre, ver_gltf, caras):
    ver_b = gltf_a_blender(np.asarray(ver_gltf, float))
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(map(float, v)) for v in ver_b], [], caras)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    salida = AQUI
    if "--salida" in argv:
        salida = os.path.abspath(argv[argv.index("--salida") + 1])
    os.makedirs(salida, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    pos = catmull_centripeta(PUNTOS, K)
    tan, nor, bi = marcos(pos)
    luz_cm = [r / 10.0 for r in RADIOS_MM]
    geo = {}

    # Órgano hueco: contorno de la pared, puntos 0 a FIN_ORGANO
    geo["organo_hueco"] = tubo_cerrado(pos, nor, bi, 0, FIN_ORGANO * K, lambda k, u: valor(PARED_EXT, k), 32)
    # Lesión: manga entre 5.6 y 10.4, más gruesa en el centro; por dentro, la luz
    k0, k1 = round(5.6 * K), round(10.4 * K)
    geo["lesion"] = manga(pos, nor, bi, k0, k1,
                          lambda k, u: 1.35 + 0.22 * math.sin(math.pi * u),
                          lambda k, u: max(0.15, valor(luz_cm, k)), 32)
    # Luz dentro de la lesión (lo blanco)
    geo["luz"] = tubo_cerrado(pos, nor, bi, round(5.8 * K), round(10.2 * K), lambda k, u: 0.92 * max(0.15, valor(luz_cm, k)), 16)
    geo["organo_vecino"] = elipsoide((-3.6, 0.2, -0.6), (2.8, 3.4, 2.0), 40, 20)
    geo["nodulo"] = elipsoide((4.6, -1.4, 1.0), (0.85, 0.85, 0.85), 24, 12)
    geo["envoltura"] = elipsoide((-1.6, 0.2, 0.4), (10.0, 13.5, 6.0), 48, 24)

    centros = {}
    for nombre, (ver, caras) in geo.items():
        crear(nombre, ver, caras)
        v = np.asarray(ver, float)
        mn, mx = v.min(0), v.max(0)
        centros[nombre] = {"centro": [round(float(x), 3) for x in (mn + mx) / 2],
                           "min": [round(float(x), 3) for x in mn], "max": [round(float(x), 3) for x in mx],
                           "caras": len(caras)}

    ruta_glb = os.path.join(salida, "demo.glb")
    bpy.ops.export_scene.gltf(filepath=ruta_glb, export_format="GLB", export_yup=True, export_apply=True,
                              export_materials="NONE", export_texcoords=False, export_normals=True,
                              export_cameras=False, export_lights=False, use_selection=False)
    with open(os.path.join(salida, "demo-centros.json"), "w", encoding="utf-8") as f:
        json.dump(centros, f, ensure_ascii=False, indent=1)
    ruta = {"_doc": "Ruta de la luz del ejemplo ficticio: puntos en glTF (cm) y radio de la luz en mm por punto; "
                    "estrechez = índices del tramo estrecho. Mismo formato que el trazado de la luz de un caso real.",
            "puntos": [list(p) for p in PUNTOS], "radios_mm": RADIOS_MM, "estrechez": ESTRECHEZ}
    with open(os.path.join(salida, "demo-ruta.json"), "w", encoding="utf-8") as f:
        json.dump(ruta, f, ensure_ascii=False, indent=1)
    print("DEMO_OK", ruta_glb, os.path.getsize(ruta_glb), "bytes")


main()
