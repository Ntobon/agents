"""Coordenadas compartidas por todo el flujo: DICOM -> máscaras -> Blender -> visor web.

Convenciones (todas las piezas de la skill las usan; no inventar otras):

- Volumen en memoria: arreglo [k, j, i] = [corte, fila, columna]. Los cortes se ordenan de
  forma ascendente a lo largo de la normal del corte (en un axial estándar: de pies a cabeza).
- Paciente, en mm, convención DICOM LPS: +x hacia la izquierda del paciente, +y hacia atrás
  (posterior), +z hacia la cabeza.
- Blender (1 unidad = 1 cm, z arriba): B = (P - C) / 10, con C = centro_mm de mapeo.json.
  Vista de frente = cámara en -y mirando hacia +y: la izquierda del paciente queda a la
  derecha de la pantalla, como en cualquier imagen radiológica.
- glTF / three.js (y arriba): G = (Bx, Bz, -By), que es lo que hace el exportador glTF de
  Blender con «+Y arriba». En el visor, +Z apunta hacia quien mira desde el frente.

Archivos que describen el espacio:
- volumen.json  (dicom_series.py): forma, espaciado_mm [dz, dy, dx], origen_mm, cosenos, normal.
- mascaras.json (segmentar.py): reduccion [fz, fy, fx] y recorte {k0, j0, i0, ...} de la
  rejilla reducida en la que viven las máscaras.
- mapeo.json    (segmentar.py): centro_mm, el origen común de Blender y del visor.

Uso en línea de comandos (para ubicar un punto visto en un corte dentro del modelo):
  python coords.py --vol volumen.json --mapeo mapeo.json --voxel 412 260 301
  python coords.py --vol volumen.json --masc mascaras.json --mapeo mapeo.json --reducido 120 130 150
  python coords.py --vol volumen.json --mapeo mapeo.json --gltf 3.2 -1.5 4.0
"""
import argparse
import json

import numpy as np


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def ruta_volumen_json(carpeta, masc):
    """Ubica el volumen.json que corresponde a unas máscaras.

    Busca primero en la misma carpeta de las máscaras (lo normal si se copió el trabajo) y
    después en la ruta que dejó segmentar.py en mascaras.json («volumen», relativa a esa carpeta).
    """
    import os
    candidatas = [os.path.join(carpeta, "volumen.json")]
    registrada = masc.get("volumen")
    if registrada:
        candidatas.append(registrada if os.path.isabs(registrada) else os.path.join(carpeta, registrada))
    for c in candidatas:
        if os.path.isfile(c):
            return os.path.normpath(c)
    raise FileNotFoundError("No encuentro volumen.json; probé: " + " | ".join(candidatas)
                            + ". Copie volumen.json junto a mascaras.json.")


def _ejes(vol):
    c = np.asarray(vol["cosenos"], float)
    fila, col = c[:3], c[3:]
    normal = np.asarray(vol.get("normal") or np.cross(fila, col), float)
    return fila, col, normal


def _factores(masc):
    f = masc["reduccion"]
    return (f, f, f) if isinstance(f, (int, float)) else tuple(f)


def voxel_a_lps(vol, k, j, i):
    """Índices del volumen completo (enteros, fraccionarios o arreglos) -> mm LPS."""
    fila, col, normal = _ejes(vol)
    dz, dy, dx = vol["espaciado_mm"]
    k, j, i = (np.asarray(a, float) for a in (k, j, i))
    return (np.asarray(vol["origen_mm"], float)
            + np.multiply.outer(i * dx, fila)
            + np.multiply.outer(j * dy, col)
            + np.multiply.outer(k * dz, normal))


def lps_a_voxel(vol, P):
    """Inverso de voxel_a_lps (cosenos ortonormales). Devuelve (k, j, i) continuos."""
    fila, col, normal = _ejes(vol)
    dz, dy, dx = vol["espaciado_mm"]
    d = np.asarray(P, float) - np.asarray(vol["origen_mm"], float)
    return d @ normal / dz, d @ col / dy, d @ fila / dx


def reducido_a_voxel(masc, k, j, i):
    """Índice de la rejilla reducida -> índice continuo del volumen completo (centro del bloque)."""
    fz, fy, fx = _factores(masc)
    r = masc["recorte"]
    return (r["k0"] + fz * np.asarray(k, float) + (fz - 1) / 2.0,
            r["j0"] + fy * np.asarray(j, float) + (fy - 1) / 2.0,
            r["i0"] + fx * np.asarray(i, float) + (fx - 1) / 2.0)


def voxel_a_reducido(masc, k, j, i):
    fz, fy, fx = _factores(masc)
    r = masc["recorte"]
    return ((np.asarray(k, float) - r["k0"] - (fz - 1) / 2.0) / fz,
            (np.asarray(j, float) - r["j0"] - (fy - 1) / 2.0) / fy,
            (np.asarray(i, float) - r["i0"] - (fx - 1) / 2.0) / fx)


def lps_a_blender(mapeo, P):
    return (np.asarray(P, float) - np.asarray(mapeo["centro_mm"], float)) / 10.0


def blender_a_gltf(B):
    B = np.asarray(B, float)
    return np.stack([B[..., 0], B[..., 2], -B[..., 1]], axis=-1)


def gltf_a_blender(G):
    G = np.asarray(G, float)
    return np.stack([G[..., 0], -G[..., 2], G[..., 1]], axis=-1)


def lps_a_gltf(mapeo, P):
    return blender_a_gltf(lps_a_blender(mapeo, P))


def gltf_a_lps(mapeo, G):
    return gltf_a_blender(G) * 10.0 + np.asarray(mapeo["centro_mm"], float)


def voxel_a_gltf(vol, mapeo, k, j, i):
    return lps_a_gltf(mapeo, voxel_a_lps(vol, k, j, i))


def reducido_a_gltf(vol, masc, mapeo, k, j, i):
    return voxel_a_gltf(vol, mapeo, *reducido_a_voxel(masc, k, j, i))


def centro_de_mascara(vol, masc, m):
    """Centro (mm LPS) de la caja que encierra una máscara reducida."""
    idx = np.argwhere(m)
    if len(idx) == 0:
        raise ValueError("máscara vacía")
    c = (idx.min(0) + idx.max(0)) / 2.0
    return voxel_a_lps(vol, *reducido_a_voxel(masc, *c))


def _fmt(v):
    return "[" + ", ".join(f"{x:.2f}" for x in np.ravel(v)) + "]"


def main():
    ap = argparse.ArgumentParser(description="Convierte un punto entre los espacios del flujo.")
    ap.add_argument("--vol", required=True, help="volumen.json")
    ap.add_argument("--masc", help="mascaras.json (para --reducido)")
    ap.add_argument("--mapeo", help="mapeo.json (para Blender/glTF)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--voxel", nargs=3, type=float, metavar=("K", "J", "I"))
    g.add_argument("--reducido", nargs=3, type=float, metavar=("K", "J", "I"))
    g.add_argument("--lps", nargs=3, type=float, metavar=("X", "Y", "Z"))
    g.add_argument("--gltf", nargs=3, type=float, metavar=("X", "Y", "Z"))
    a = ap.parse_args()
    vol = cargar(a.vol)
    masc = cargar(a.masc) if a.masc else None
    mapeo = cargar(a.mapeo) if a.mapeo else None
    if a.voxel:
        P = voxel_a_lps(vol, *a.voxel)
    elif a.reducido:
        if not masc:
            ap.error("--reducido necesita --masc")
        P = voxel_a_lps(vol, *reducido_a_voxel(masc, *a.reducido))
    elif a.lps:
        P = np.asarray(a.lps, float)
    else:
        if not mapeo:
            ap.error("--gltf necesita --mapeo")
        P = gltf_a_lps(mapeo, a.gltf)
    print("LPS mm      ", _fmt(P))
    print("vóxel k,j,i ", _fmt(lps_a_voxel(vol, P)))
    if masc:
        print("reducido    ", _fmt(voxel_a_reducido(masc, *lps_a_voxel(vol, P))))
    if mapeo:
        print("Blender cm  ", _fmt(lps_a_blender(mapeo, P)))
        print("glTF        ", _fmt(lps_a_gltf(mapeo, P)))


if __name__ == "__main__":
    main()
