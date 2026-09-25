"""Mirar antes de segmentar: montajes con rejilla, reformateos, muestreo de valores y
superposición de máscaras. Solo numpy + Pillow.

  python cortes_qa.py montaje    --volumen DIR [--cada N | --cortes k1,k2,..] [--rango k0:k1]
                                 [--ventana abdomen] [--recuadro j0:j1,i0:i1] [--marcas "k j i; k j i"]
                                 --salida montaje.png
  python cortes_qa.py reformat   --volumen DIR (--j J[,J..] | --i I[,I..]) [--rango k0:k1]
                                 [--grosor N --modo media|mip|minip] --salida coronal.png
  python cortes_qa.py muestrear  --volumen DIR K J I [--radio 3] [--radio-k 1] [--puntos "k j i; ..."]
  python cortes_qa.py superponer --volumen DIR [--mascaras DIR] [--claves a,b] [--cortes ..] [--coronal J,..]
                                 --salida qa        (escribe qa_axial.png y qa_coronal.png)

Todas las coordenadas son del volumen completo: k = corte (orden ascendente sobre la normal),
j = fila, i = columna, como en coords.py. La rejilla rotula (j, i) cada 32 píxeles y cada mosaico
lleva su k: así se leen semillas y cajas directamente de la imagen.
Ventanas de TAC: abdomen (W400/L50), pulmon (1500/-600), hueso (2000/500), mediastino (350/40),
higado (150/80); RM: auto (p1-p99). También 'W/L' (p. ej. 400/50) o 'lo:hi'.
"""
import argparse
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coords  # noqa: E402
import morfologia as mf  # noqa: E402

VENTANAS = {"abdomen": (400, 50), "pulmon": (1500, -600), "hueso": (2000, 500),
            "mediastino": (350, 40), "higado": (150, 80)}
# Mismos colores que la paleta de ejemplo de Blender (un color, un significado en todo el flujo).
# La banda de violetas/fucsias queda reservada para la lesión: ningún color de respaldo cae en ella.
COLORES = {
    "lesion": (255, 45, 149), "luz": (255, 255, 255), "contenido": (244, 211, 94),
    "contraste": (60, 255, 78), "higado": (142, 51, 36), "bazo": (127, 147, 173),
    "rinones": (240, 138, 36), "pulmones": (142, 201, 242), "arterias": (209, 31, 42),
    "venas": (47, 95, 208), "vasos": (209, 31, 42), "hueso": (238, 228, 198), "cuerpo": (227, 180, 154),
}
PALETA = [(255, 215, 0), (0, 200, 160), (255, 99, 71), (154, 205, 50), (0, 191, 255),
          (244, 164, 96), (128, 128, 0), (0, 128, 128), (210, 180, 140), (173, 255, 47)]
FONDO = (18, 18, 22)
REJ = (70, 80, 170)


# ------------------------------------------------------------------ carga y utilidades
def _consola():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace", **({} if s.isatty() else {"encoding": "utf-8"}))
        except Exception:
            pass


def cargar_volumen(d):
    with open(os.path.join(d, "volumen.json"), encoding="utf-8") as f:
        info = json.load(f)
    return info, np.load(os.path.join(d, "volumen.npy"), mmap_mode="r")


def cargar_mascaras(ruta):
    """ruta: carpeta o mascaras.json. Devuelve (info, {clave: bool[...]})."""
    if os.path.isdir(ruta):
        ruta = os.path.join(ruta, "mascaras.json")
    with open(ruta, encoding="utf-8") as f:
        info = json.load(f)
    npz = np.load(os.path.join(os.path.dirname(ruta), "mascaras.npz"))
    return info, {k: npz[k].astype(bool) for k in npz.files}


def fuente(tam=12):
    for nombre in ("arial.ttf", "DejaVuSans.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(nombre, tam)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:
        return ImageFont.load_default()


def ventana(info, nombre):
    if not nombre:
        nombre = "abdomen" if info.get("modalidad") == "CT" else "auto"
    if nombre in VENTANAS:
        W, L = VENTANAS[nombre]
        return L - W / 2.0, L + W / 2.0
    if nombre == "auto":
        p = info["percentiles"]
        return p["p1"], p["p99"]
    m = re.match(r"^\s*(-?[\d.]+)\s*/\s*(-?[\d.]+)\s*$", nombre)
    if m:
        W, L = float(m.group(1)), float(m.group(2))
        return L - W / 2.0, L + W / 2.0
    m = re.match(r"^\s*(-?[\d.]+)\s*:\s*(-?[\d.]+)\s*$", nombre)
    if m:
        return float(m.group(1)), float(m.group(2))
    raise SystemExit(f"Ventana no reconocida: {nombre}")


def gris(a, lo, hi):
    return (np.clip((np.asarray(a, np.float32) - lo) / max(hi - lo, 1e-6), 0, 1) * 255).astype(np.uint8)


def rango(txt, n):
    if not txt:
        return 0, n
    a, b = txt.split(":")
    a = int(a) if a else 0
    b = int(b) if b else n
    return max(a, 0), min(b, n)


def recuadro(txt, nj, ni):
    if not txt:
        return 0, nj, 0, ni
    pj, pi = txt.split(",")
    j0, j1 = rango(pj, nj)
    i0, i1 = rango(pi, ni)
    return j0, j1, i0, i1


def puntos(txt):
    if not txt:
        return []
    out = []
    for p in txt.split(";"):
        v = [float(x) for x in p.replace(",", " ").split()]
        if len(v) == 3:
            out.append(v)
    return out


def color_de(clave, n):
    return COLORES.get(clave, PALETA[n % len(PALETA)])


def a_rejilla(v, paso):
    """Múltiplos de `paso` dentro de [v0, v1)."""
    v0, v1 = v
    return list(range(((v0 + paso - 1) // paso) * paso, v1, paso))


# ------------------------------------------------------------------ mosaicos
def mosaico(rgb, titulo, ejes, rejilla, fnt, escala_x, escala_y, marcas=(), lineas=()):
    """rgb: imagen ya en color (filas = eje vertical). ejes = ((nombre_v, v0, v1, invertido),
    (nombre_h, h0, h1)) en coordenadas del volumen completo. Dibuja rejilla, rótulos, marcas
    [(v, h, rótulo)] y líneas [([(v, h), ...], color, ancho)]."""
    (nv, v0, v1, inv), (nh, h0, h1) = ejes
    img = Image.fromarray(rgb)
    W, H = int(round((h1 - h0) * escala_x)), int(round((v1 - v0) * escala_y))
    img = img.resize((max(W, 1), max(H, 1)), Image.BILINEAR)
    mi, ms = 34, 30
    lienzo = Image.new("RGB", (W + mi + 4, H + ms + 4), FONDO)
    lienzo.paste(img, (mi, ms))
    d = ImageDraw.Draw(lienzo)

    def yv(v):
        return ms + ((v1 - 1 - v + 0.5) if inv else (v - v0 + 0.5)) * escala_y

    def xh(h):
        return mi + (h - h0 + 0.5) * escala_x
    for v in a_rejilla((v0, v1), rejilla):
        y = yv(v)
        d.line([(mi, y), (mi + W - 1, y)], fill=REJ, width=1)
        d.text((2, y - 6), str(v), fill=(200, 200, 230), font=fnt)
    for h in a_rejilla((h0, h1), rejilla):
        x = xh(h)
        d.line([(x, ms), (x, ms + H - 1)], fill=REJ, width=1)
        d.text((x - 8, ms - 13), str(h), fill=(200, 200, 230), font=fnt)
    d.text((mi, 1), titulo, fill=(255, 255, 255), font=fnt)
    d.text((2, ms - 13), f"{nv}\\{nh}", fill=(150, 150, 170), font=fnt)
    for pts, col, ancho in lineas:
        if len(pts) > 1:
            d.line([(xh(h), yv(v)) for v, h in pts], fill=col, width=ancho)
    for v, h, rot in marcas:
        x, y = xh(h), yv(v)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=(255, 40, 40), width=2)
        d.text((x + 8, y - 8), str(rot), fill=(255, 80, 80), font=fnt)
    return lienzo


def componer(mosaicos, columnas, pie=None, fnt=None):
    if not mosaicos:
        raise SystemExit("No hay cortes que mostrar.")
    columnas = max(1, min(columnas, len(mosaicos)))
    filas = (len(mosaicos) + columnas - 1) // columnas
    w = max(m.width for m in mosaicos)
    h = max(m.height for m in mosaicos)
    alto_pie = 0
    if pie:
        alto_pie = 22 * ((len(pie) + 3) // 4) + 8
    out = Image.new("RGB", (columnas * (w + 6) + 6, filas * (h + 6) + 6 + alto_pie), FONDO)
    for n, m in enumerate(mosaicos):
        out.paste(m, (6 + (n % columnas) * (w + 6), 6 + (n // columnas) * (h + 6)))
    if pie:
        d = ImageDraw.Draw(out)
        y0 = filas * (h + 6) + 10
        ancho = max(1, (out.width - 12) // 4)
        for n, (texto, col) in enumerate(pie):
            x, y = 8 + (n % 4) * ancho, y0 + (n // 4) * 22
            d.rectangle([x, y + 2, x + 14, y + 16], fill=col)
            d.text((x + 20, y + 2), texto, fill=(230, 230, 230), font=fnt)
    return out


def guardar(img, ruta):
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    img.save(ruta)
    print(f"Escrito {ruta} ({img.width}x{img.height})")


def _escala_def(ancho, escala):
    return escala if escala else min(1.0, 420.0 / max(ancho, 1))


def _lista_cortes(args, k0, k1, n_def=8):
    if args.cortes:
        return [int(x) for x in re.split(r"[,\s]+", args.cortes.strip()) if x]
    paso = args.cada or max(1, (k1 - k0) // n_def)
    return list(range(k0 + paso // 2, k1, paso))


def _z(info, k, nj, ni):
    return float(coords.voxel_a_lps(info, k, nj / 2.0, ni / 2.0)[2])


# ------------------------------------------------------------------ montaje axial
def cmd_montaje(args):
    info, vol = cargar_volumen(args.volumen)
    nk, nj, ni = vol.shape
    lo, hi = ventana(info, args.ventana)
    k0, k1 = rango(args.rango, nk)
    j0, j1, i0, i1 = recuadro(args.recuadro, nj, ni)
    es = _escala_def(i1 - i0, args.escala)
    fnt = fuente(12)
    marcas = puntos(args.marcas)
    tiles = []
    for k in _lista_cortes(args, k0, k1):
        if not 0 <= k < nk:
            continue
        g = gris(vol[k, j0:j1, i0:i1], lo, hi)
        rgb = np.stack([g] * 3, -1)
        mk = [(m[1], m[2], n) for n, m in enumerate(marcas, 1) if abs(m[0] - k) <= args.tol_marcas]
        tiles.append(mosaico(rgb, f"k {k}   z {_z(info, k, nj, ni):.1f} mm", (("j", j0, j1, False), ("i", i0, i1)),
                             args.rejilla, fnt, es, es, mk))
    guardar(componer(tiles, args.columnas), args.salida)


# ------------------------------------------------------------------ reformateo
def _losa(vol, eje, c, g, k0, k1, modo):
    if eje == "j":
        a = np.asarray(vol[k0:k1, max(c - g, 0):c + g + 1, :], np.float32)
        ax = 1
    else:
        a = np.asarray(vol[k0:k1, :, max(c - g, 0):c + g + 1], np.float32)
        ax = 2
    if modo == "mip":
        return a.max(ax)
    if modo == "minip":
        return a.min(ax)
    return a.mean(ax)


def cmd_reformat(args):
    info, vol = cargar_volumen(args.volumen)
    nk, nj, ni = vol.shape
    dz, dy, dx = info["espaciado_mm"]
    lo, hi = ventana(info, args.ventana)
    k0, k1 = rango(args.rango, nk)
    if bool(args.j) == bool(args.i):
        raise SystemExit("Indique --j (coronal) o --i (sagital).")
    eje, valores = ("j", args.j) if args.j else ("i", args.i)
    dh = dx if eje == "j" else dy
    horiz = ("i", 0, ni) if eje == "j" else ("j", 0, nj)
    es = _escala_def(horiz[2], args.escala)
    fnt = fuente(12)
    marcas = puntos(args.marcas)
    tiles = []
    for c in [int(x) for x in valores.split(",")]:
        img = _losa(vol, eje, c, args.grosor, k0, k1, args.modo)[::-1]
        g = gris(img, lo, hi)
        mk = [(m[0], m[2] if eje == "j" else m[1], n) for n, m in enumerate(marcas, 1)
              if abs((m[1] if eje == "j" else m[2]) - c) <= args.tol_marcas]
        nombre = "coronal" if eje == "j" else "sagital"
        titulo = f"{nombre} {eje}={c}" + (f" ±{args.grosor} {args.modo}" if args.grosor else "")
        tiles.append(mosaico(np.stack([g] * 3, -1), titulo, (("k", k0, k1, True), horiz), args.rejilla, fnt,
                             es, es * dz / dh, mk))
    guardar(componer(tiles, args.columnas), args.salida)


# ------------------------------------------------------------------ muestreo
def cmd_muestrear(args):
    info, vol = cargar_volumen(args.volumen)
    nk, nj, ni = vol.shape
    lista = puntos(args.puntos) if args.puntos else [[args.k, args.j, args.i]]
    if not lista or None in lista[0]:
        raise SystemExit("Indique K J I o --puntos.")
    minfo = M = None
    ruta_m = args.mascaras or args.volumen
    if os.path.exists(os.path.join(ruta_m, "mascaras.json")) if os.path.isdir(ruta_m) else os.path.exists(ruta_m):
        minfo, M = cargar_mascaras(ruta_m)
    u = info["unidades"]
    for k, j, i in lista:
        k, j, i = int(round(k)), int(round(j)), int(round(i))
        if not (0 <= k < nk and 0 <= j < nj and 0 <= i < ni):
            print(f"({k}, {j}, {i}) fuera del volumen {list(vol.shape)}")
            continue
        r, rk = args.radio, args.radio_k
        a = np.asarray(vol[max(k - rk, 0):k + rk + 1, max(j - r, 0):j + r + 1, max(i - r, 0):i + r + 1], np.float64)
        jj, ii = np.ogrid[max(j - r, 0) - j:min(j + r + 1, nj) - j, max(i - r, 0) - i:min(i + r + 1, ni) - i]
        disco = (jj ** 2 + ii ** 2) <= r * r
        v = a[:, disco].ravel()
        P = coords.voxel_a_lps(info, k, j, i)
        print(f"k {k} j {j} i {i}  (LPS {P[0]:.1f}, {P[1]:.1f}, {P[2]:.1f} mm)  valor {float(vol[k, j, i]):.1f} {u}")
        print(f"  vecindario (disco r={r} px x {2 * rk + 1} cortes, n={v.size}): media {v.mean():.1f}  "
              f"DE {v.std():.1f}  min {v.min():.1f}  max {v.max():.1f}  p5 {np.percentile(v, 5):.1f}  "
              f"p95 {np.percentile(v, 95):.1f}")
        print(f"  rango orientativo (media ± 2 DE): [{v.mean() - 2 * v.std():.0f}, {v.mean() + 2 * v.std():.0f}] "
              f"— en la receta el umbral actúa sobre V/Vs (promediados): su DE es menor")
        if M is not None:
            kr, jr, ir = (int(round(float(x))) for x in coords.voxel_a_reducido(minfo, k, j, i))
            forma = minfo["forma"]
            if 0 <= kr < forma[0] and 0 <= jr < forma[1] and 0 <= ir < forma[2]:
                dentro = [c for c, m in M.items() if m[kr, jr, ir]]
                print(f"  rejilla reducida ({kr}, {jr}, {ir}): dentro de {', '.join(dentro) if dentro else 'ninguna máscara'}")
            else:
                print("  fuera del recorte de las máscaras")


# ------------------------------------------------------------------ superposición
def _pintar(rgb, capas, alfa):
    """capas: lista de (máscara 2D, color, solo_contorno)."""
    out = rgb.astype(np.float32)
    for m, col, contorno in capas:
        if not m.any():
            continue
        borde = m & ~mf.erosionar(m, 1)
        if not contorno:
            out[m] = (1 - alfa) * out[m] + alfa * np.array(col, np.float32)
        out[borde] = col
    return out.astype(np.uint8)


def cmd_superponer(args):
    info, vol = cargar_volumen(args.volumen)
    minfo, M = cargar_mascaras(args.mascaras or args.volumen)
    nk, nj, ni = vol.shape
    dz, dy, dx = info["espaciado_mm"]
    fz, fy, fx = coords._factores(minfo)
    rc = minfo["recorte"]
    nkr, njr, nir = minfo["forma"]
    orden = list(minfo.get("estructuras", {}).keys()) + [c for c in M if c not in minfo.get("estructuras", {})]
    claves = [c for c in (args.claves.split(",") if args.claves else orden) if c in M]
    contorno = set(args.solo_contorno.split(",")) if args.solo_contorno else set()
    colores = {c: color_de(c, n) for n, c in enumerate(claves)}
    lo, hi = ventana(info, args.ventana)
    fnt = fuente(12)
    union = np.zeros(minfo["forma"], bool)
    for c in claves:
        if c not in contorno:
            union |= M[c]
    if not union.any():
        union = np.ones(minfo["forma"], bool)
    kk, jj, ii = np.nonzero(union.any(axis=(1, 2)))[0], np.nonzero(union.any(axis=(0, 2)))[0], np.nonzero(union.any(axis=(0, 1)))[0]
    K0, K1 = rc["k0"] + kk.min() * fz, rc["k0"] + (kk.max() + 1) * fz
    J0, J1 = rc["j0"] + jj.min() * fy, rc["j0"] + (jj.max() + 1) * fy
    I0, I1 = rc["i0"] + ii.min() * fx, rc["i0"] + (ii.max() + 1) * fx
    if args.recuadro:
        j0, j1, i0, i1 = recuadro(args.recuadro, nj, ni)
    else:
        mg = 12
        j0, j1, i0, i1 = max(J0 - mg, 0), min(J1 + mg, nj), max(I0 - mg, 0), min(I1 + mg, ni)
    pie = [(f"{c} ({minfo['estructuras'][c]['volumen_ml']:.0f} mL)" if c in minfo.get("estructuras", {}) else c,
            colores[c]) for c in claves]

    def plano_completo(m2, f_v, f_h, v0, h0, forma):
        full = np.zeros(forma, bool)
        up = np.repeat(np.repeat(m2, f_v, 0), f_h, 1)
        full[v0:v0 + up.shape[0], h0:h0 + up.shape[1]] = up
        return full

    # axiales
    es = _escala_def(i1 - i0, args.escala)
    tiles = []
    for k in _lista_cortes(args, K0, K1):
        if not 0 <= k < nk:
            continue
        g = gris(vol[k, j0:j1, i0:i1], lo, hi)
        kr = (k - rc["k0"]) // fz
        capas = []
        if 0 <= kr < nkr:
            for c in claves:
                full = plano_completo(M[c][kr], fy, fx, rc["j0"], rc["i0"], (nj, ni))
                capas.append((full[j0:j1, i0:i1], colores[c], c in contorno))
        rgb = _pintar(np.stack([g] * 3, -1), capas, args.alfa)
        tiles.append(mosaico(rgb, f"k {k}", (("j", j0, j1, False), ("i", i0, i1)), args.rejilla, fnt, es, es))
    base = args.salida[:-4] if args.salida.lower().endswith(".png") else args.salida
    guardar(componer(tiles, args.columnas, pie, fnt), base + "_axial.png")

    # coronales
    if args.coronal:
        js = [int(x) for x in args.coronal.split(",")]
    else:
        js = [int(J0 + (J1 - J0) * f) for f in (0.3, 0.5, 0.7)]
    ka, kb = max(K0 - 8, 0), min(K1 + 8, nk)
    tiles = []
    for j in js:
        g = gris(np.asarray(vol[ka:kb, j, i0:i1]), lo, hi)
        jr = (j - rc["j0"]) // fy
        capas = []
        if 0 <= jr < njr:
            for c in claves:
                full = plano_completo(M[c][:, jr, :], fz, fx, rc["k0"], rc["i0"], (nk, ni))
                capas.append((full[ka:kb, i0:i1], colores[c], c in contorno))
        rgb = _pintar(np.stack([g] * 3, -1), capas, args.alfa)[::-1]
        tiles.append(mosaico(rgb, f"coronal j={j}", (("k", ka, kb, True), ("i", i0, i1)), args.rejilla, fnt,
                             es, es * dz / dx))
    guardar(componer(tiles, min(args.columnas, len(tiles)), pie, fnt), base + "_coronal.png")


# ------------------------------------------------------------------ CLI
def main():
    _consola()
    ap = argparse.ArgumentParser(description="Revisión visual del volumen y de las máscaras (montajes con rejilla, "
                                             "reformateos, muestreo y superposición).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def comunes(p, salida=True):
        p.add_argument("--volumen", "--trabajo", dest="volumen", default=".",
                       help="carpeta con volumen.npy y volumen.json (la de trabajo)")
        p.add_argument("--ventana", help="abdomen, pulmon, hueso, mediastino, higado, auto, 'W/L' o 'lo:hi'")
        p.add_argument("--rejilla", type=int, default=32, help="paso de la rejilla en píxeles del volumen completo")
        p.add_argument("--escala", type=float, help="escala de cada mosaico (por defecto, ~420 px de ancho)")
        p.add_argument("--columnas", type=int, default=4)
        p.add_argument("--marcas", help="puntos a señalar, 'k j i; k j i' (volumen completo)")
        p.add_argument("--tol-marcas", dest="tol_marcas", type=float, default=2,
                       help="distancia máxima (en cortes) para dibujar una marca en un mosaico")
        if salida:
            p.add_argument("--salida", required=True, help="archivo PNG de salida")

    p = sub.add_parser("montaje", help="cortes axiales con rejilla de coordenadas")
    comunes(p)
    p.add_argument("--cada", type=int, help="un corte cada N")
    p.add_argument("--cortes", help="lista de cortes k (coma o espacio)")
    p.add_argument("--rango", help="k0:k1 (por defecto, todo)")
    p.add_argument("--recuadro", help="j0:j1,i0:i1 para ampliar una región")
    p.set_defaults(fn=cmd_montaje)

    p = sub.add_parser("reformat", help="coronal (--j) o sagital (--i) con la proporción correcta")
    comunes(p)
    p.add_argument("--j", help="fila(s) j para coronales, separadas por coma")
    p.add_argument("--i", help="columna(s) i para sagitales, separadas por coma")
    p.add_argument("--rango", help="k0:k1")
    p.add_argument("--grosor", type=int, default=0, help="media losa: usa las filas c-N..c+N")
    p.add_argument("--modo", choices=["media", "mip", "minip"], default="media",
                   help="cómo combinar la losa (mip para contraste, minip para aire)")
    p.set_defaults(fn=cmd_reformat)

    p = sub.add_parser("muestrear", help="media/DE/mín/máx alrededor de un punto (verificar semillas y rangos)")
    p.add_argument("--volumen", "--trabajo", dest="volumen", default=".")
    p.add_argument("k", type=float, nargs="?")
    p.add_argument("j", type=float, nargs="?")
    p.add_argument("i", type=float, nargs="?")
    p.add_argument("--puntos", help="varios puntos 'k j i; k j i'")
    p.add_argument("--radio", type=int, default=3, help="radio del disco en el plano (píxeles)")
    p.add_argument("--radio-k", dest="radio_k", type=int, default=1, help="cortes a cada lado")
    p.add_argument("--mascaras", help="carpeta o mascaras.json para decir en qué estructura cae el punto")
    p.set_defaults(fn=cmd_muestrear)

    p = sub.add_parser("superponer", help="máscaras en color sobre axiales y coronales (la revisión clave)")
    comunes(p)
    p.add_argument("--mascaras", help="carpeta o mascaras.json (por defecto, la de --volumen)")
    p.add_argument("--claves", help="solo estas estructuras (coma)")
    p.add_argument("--solo-contorno", dest="solo_contorno", default="cuerpo",
                   help="estructuras que se dibujan solo con su borde (coma)")
    p.add_argument("--alfa", type=float, default=0.40, help="opacidad del relleno")
    p.add_argument("--cada", type=int)
    p.add_argument("--cortes", help="cortes k de los axiales")
    p.add_argument("--coronal", help="filas j de los coronales (coma)")
    p.add_argument("--recuadro", help="j0:j1,i0:i1")
    p.set_defaults(fn=cmd_superponer)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
