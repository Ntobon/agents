"""Segmentación por umbrales guiada por una receta JSON (motor genérico, solo numpy).

  python segmentar.py --volumen DIR --receta receta.json --salida DIR

Lee volumen.npy/volumen.json (dicom_series.py cargar) y escribe en --salida:
  mascaras.npz   una máscara booleana por estructura, en la rejilla reducida
  mascaras.json  reducción, recorte, forma, espaciado y, por estructura, vóxeles, mL, fuente y parámetros
  mapeo.json     centro_mm (centro de la caja de la estructura «centro»), origen común de Blender y del visor

Preproceso (sobre el recorte de la receta):
  V  = media de cada bloque fz x fy x fx          (la intensidad «normal» reducida)
  VM = máximo de cada bloque                        (capta hueso cortical y calcio finos)
  Vs = V suavizado con una caja 3x3x3 (suma / 27)   (para órganos: sin esto la erosión borra
                                                     máscaras ruidosas)
Por estructura, en el orden de la receta:
  candidato = lo < fuente < hi, menos 'excluir', dentro de 'limitar_a'
  -> filtro_vecinos -> erosión -> crecer desde semillas (o mayor componente) -> se devuelve la
  erosión dilatando dentro del candidato -> mayor_componente -> rellenar_por_corte -> dilatar_despues.
'excluir' solo puede nombrar estructuras anteriores: el orden de la receta importa.
Esquema completo y umbrales de partida: references/segmentation.md y recetas/*.json.
"""
import argparse
import json
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coords  # noqa: E402
import morfologia as mf  # noqa: E402

NOTA = "Segmentación aproximada por umbrales; no es una lectura radiológica."
CAMPOS = {"clave", "fuente", "rango", "excluir", "semillas_voxel", "erosion", "crecer", "filtro_vecinos",
          "rellenar_por_corte", "mayor_componente", "dilatar_despues", "limitar_a", "auxiliar", "max_iter"}


def _consola():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace", **({} if s.isatty() else {"encoding": "utf-8"}))
        except Exception:
            pass


def _factores(red):
    return [int(red)] * 3 if isinstance(red, (int, float)) else [int(x) for x in red]


def modos_bordes(nombre):
    """(modo del suavizado, modo del conteo de vecinos). 'envolver' reproduce np.roll."""
    if nombre in (None, "replicar"):
        return "replicar", "constante"
    if nombre == "envolver":
        return "envolver", "envolver"
    raise SystemExit(f"bordes debe ser 'replicar' o 'envolver', no {nombre!r}")


# ------------------------------------------------------------------ recorte y preproceso
def recorte_auto(vol, info, margen=4):
    """Caja del cuerpo: mayor componente sobre una versión submuestreada x4."""
    s = np.asarray(vol[::4, ::4, ::4], np.float32)
    if info.get("modalidad") == "CT":
        m = s > -500
    else:
        p = info["percentiles"]
        m = s > p["p1"] + 0.10 * (p["p99"] - p["p1"])
    m = mf.mayor_componente(mf.erosionar(m, 1))
    if not m.any():
        raise SystemExit("recorte 'auto': no se encontró el cuerpo; indique el recorte a mano.")
    idx = np.argwhere(m)
    lo = np.maximum(idx.min(0) * 4 - margen, 0)
    hi = np.minimum((idx.max(0) + 1) * 4 + margen, vol.shape)
    return dict(k0=int(lo[0]), k1=int(hi[0]), j0=int(lo[1]), j1=int(hi[1]), i0=int(lo[2]), i1=int(hi[2]))


def resolver_recorte(receta_recorte, vol, info, factores):
    nk, nj, ni = vol.shape
    completo = dict(k0=0, k1=nk, j0=0, j1=nj, i0=0, i1=ni)
    if receta_recorte in (None, "completo"):
        rc = completo
    elif receta_recorte == "auto":
        rc = recorte_auto(vol, info)
    elif isinstance(receta_recorte, dict):
        base = recorte_auto(vol, info) if receta_recorte.get("auto") else completo
        rc = {c: int(receta_recorte[c]) if isinstance(receta_recorte.get(c), (int, float)) else base[c] for c in completo}
    else:
        raise SystemExit("recorte debe ser 'auto', 'completo' o {k0, k1, j0, j1, i0, i1}")
    fz, fy, fx = factores
    for (a, b, f, n) in (("k0", "k1", fz, nk), ("j0", "j1", fy, nj), ("i0", "i1", fx, ni)):
        rc[a], rc[b] = max(rc[a], 0), min(rc[b], n)
        rc[b] = rc[a] + ((rc[b] - rc[a]) // f) * f      # múltiplo exacto del factor
        if rc[b] <= rc[a]:
            raise SystemExit(f"recorte vacío en {a}:{b}")
    return rc


def preprocesar(vol, rc, factores, bordes="replicar"):
    """Devuelve V (media por bloque), VM (máximo por bloque) y Vs (V suavizado 3x3x3), float32."""
    fz, fy, fx = factores
    nk, nj, ni = (rc["k1"] - rc["k0"]) // fz, (rc["j1"] - rc["j0"]) // fy, (rc["i1"] - rc["i0"]) // fx
    V = np.empty((nk, nj, ni), np.float32)
    VM = np.empty_like(V)
    for kr in range(nk):
        k = rc["k0"] + kr * fz
        b = np.asarray(vol[k:k + fz, rc["j0"]:rc["j1"], rc["i0"]:rc["i1"]], np.float32)
        b = b.reshape(fz, nj, fy, ni, fx)
        V[kr] = b.mean(axis=(0, 2, 4))
        VM[kr] = b.max(axis=(0, 2, 4))
    Vs = mf.media_caja(V, modos_bordes(bordes)[0])
    return V, VM, Vs


# ------------------------------------------------------------------ piezas de la receta
def parse_excluir(txt):
    m = re.match(r"^\s*([a-z0-9_]+)\s*(?:\+\s*dil\s*:\s*(\d+))?\s*$", str(txt))
    if not m:
        raise SystemExit(f"excluir: formato no válido {txt!r} (use 'clave' o 'clave+dil:N')")
    return m.group(1), int(m.group(2) or 0)


def semillas_reducidas(minfo, semillas, clave):
    if isinstance(semillas, str) or not semillas:
        raise SystemExit(f"[{clave}] faltan semillas: {semillas!r}. Ubíquelas con cortes_qa.py montaje (rejilla) y "
                         "verifíquelas con cortes_qa.py muestrear; van en coordenadas del volumen completo [k, j, i].")
    out = []
    forma = minfo["forma"]
    for s in semillas:
        r = tuple(int(np.rint(float(x))) for x in coords.voxel_a_reducido(minfo, *s))
        if not all(0 <= v < n for v, n in zip(r, forma)):
            raise SystemExit(f"[{clave}] la semilla {s} queda fuera del recorte (reducida {list(r)}, forma {forma}).")
        out.append(r)
    return out


def region(minfo, lim, forma):
    """Máscara de 'limitar_a': {'caja_voxel': [[k0,k1],[j0,j1],[i0,i1]]} y/o
    {'esfera_voxel': [k,j,i], 'radio_mm': r}, en coordenadas del volumen completo."""
    m = np.ones(forma, bool)
    esp = np.asarray(minfo["espaciado_mm"], float)
    if "caja_voxel" in lim:
        (a0, a1), (b0, b1), (c0, c1) = lim["caja_voxel"]
        lo = np.floor(coords.voxel_a_reducido(minfo, a0, b0, c0)).astype(int)
        hi = np.ceil(coords.voxel_a_reducido(minfo, a1, b1, c1)).astype(int)
        caja = np.zeros(forma, bool)
        caja[max(lo[0], 0):max(hi[0], 0), max(lo[1], 0):max(hi[1], 0), max(lo[2], 0):max(hi[2], 0)] = True
        m &= caja
    if "esfera_voxel" in lim:
        c = np.asarray(coords.voxel_a_reducido(minfo, *lim["esfera_voxel"]), float)
        r = float(lim["radio_mm"])
        ext = np.ceil(r / esp).astype(int) + 1
        lo = np.maximum(np.floor(c).astype(int) - ext, 0)
        hi = np.minimum(np.ceil(c).astype(int) + ext + 1, forma)
        kk, jj, ii = np.meshgrid(*[np.arange(a, b) for a, b in zip(lo, hi)], indexing="ij")
        d2 = ((kk - c[0]) * esp[0]) ** 2 + ((jj - c[1]) * esp[1]) ** 2 + ((ii - c[2]) * esp[2]) ** 2
        esf = np.zeros(forma, bool)
        esf[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]] = d2 <= r * r
        m &= esf
    return m


def segmentar_estructura(e, F, M, minfo, modo_conteo):
    clave = e["clave"]
    fuente = e.get("fuente", "Vs")
    if fuente not in F:
        raise SystemExit(f"[{clave}] fuente debe ser V, VM o Vs")
    lo, hi = (list(e.get("rango", [None, None])) + [None, None])[:2]
    A = F[fuente]
    cand = np.ones(A.shape, bool)
    if lo is not None:
        cand &= A > lo
    if hi is not None:
        cand &= A < hi
    for x in e.get("excluir", []) or []:
        c, n = parse_excluir(x)
        if c not in M:
            raise SystemExit(f"[{clave}] excluir nombra '{c}', que no existe antes en la receta (el orden importa).")
        cand &= ~(mf.dilatar(M[c], n=n) if n else M[c])
    if e.get("limitar_a"):
        cand &= region(minfo, e["limitar_a"], A.shape)
    if e.get("filtro_vecinos"):
        cand = mf.filtro_vecinos(cand, int(e["filtro_vecinos"]), modo_conteo)
    r = int(e.get("erosion", 0) or 0)
    notas, sem = [], None
    if e.get("crecer", False):
        sem = semillas_reducidas(minfo, e.get("semillas_voxel"), clave)
        try:
            reg, notas = mf.crecer(cand, sem, erosion=r, max_iter=e.get("max_iter"))
        except RuntimeError as err:
            valores = ", ".join(f"{float(A[s]):.0f}" for s in sem)
            raise SystemExit(f"[{clave}] {err}.\n  {fuente} en las semillas: {valores}; rango ({lo}, {hi}), erosión {r}"
                             f"{', excluir ' + str(e.get('excluir')) if e.get('excluir') else ''}. Ajuste el rango a lo "
                             "medido con cortes_qa.py muestrear, baje la erosión o mueva la semilla.")
        if e.get("mayor_componente"):
            reg = mf.mayor_componente(reg)
    else:
        er = mf.erosionar(cand, r) if r else cand
        if e.get("mayor_componente"):
            er = mf.mayor_componente(er)
        reg = mf.dilatar(er, cand, r) if r else er
    if e.get("rellenar_por_corte"):
        reg = mf.rellenar_por_corte(reg)
    if e.get("dilatar_despues"):
        reg = mf.dilatar(reg, n=int(e["dilatar_despues"]))
    return reg, notas, sem


def guardar_npz(ruta, M):
    tmp = ruta + ".tmp"
    with open(tmp, "wb") as f:
        np.savez_compressed(f, **{k: np.asarray(v, bool) for k, v in M.items()})
    os.replace(tmp, ruta)


def guardar_json(ruta, datos):
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ruta)


# ------------------------------------------------------------------ principal
def main():
    _consola()
    ap = argparse.ArgumentParser(description="Segmenta estructuras por umbrales según una receta JSON y escribe "
                                             "mascaras.npz, mascaras.json y mapeo.json.")
    ap.add_argument("--volumen", "--trabajo", dest="volumen", required=True,
                    help="carpeta con volumen.npy y volumen.json")
    ap.add_argument("--receta", required=True, help="receta JSON (ver recetas/)")
    ap.add_argument("--salida", help="carpeta de salida (por defecto, la del volumen)")
    args = ap.parse_args()
    salida = args.salida or args.volumen
    os.makedirs(salida, exist_ok=True)
    t0 = time.time()
    with open(os.path.join(args.volumen, "volumen.json"), encoding="utf-8") as f:
        vinfo = json.load(f)
    vol = np.load(os.path.join(args.volumen, "volumen.npy"), mmap_mode="r")
    with open(args.receta, encoding="utf-8") as f:
        receta = json.load(f)
    factores = _factores(receta.get("reduccion", 2))
    bordes = receta.get("bordes", "replicar")
    modo_conteo = modos_bordes(bordes)[1]
    rc = resolver_recorte(receta.get("recorte", "auto"), vol, vinfo, factores)
    V, VM, Vs = preprocesar(vol, rc, factores, bordes)
    esp = [float(a) * b for a, b in zip(vinfo["espaciado_mm"], factores)]
    minfo = dict(reduccion=factores, recorte=rc, forma=list(V.shape), espaciado_mm=esp,
                 volumen=os.path.relpath(os.path.join(args.volumen, "volumen.json"), salida).replace(os.sep, "/"),
                 estructuras={}, nota=NOTA, bordes=bordes,
                 receta=os.path.basename(args.receta))
    ml_vox = float(np.prod(esp)) / 1000.0
    print(f"recorte {rc}, reducción {factores}, rejilla {list(V.shape)}, vóxel {esp[0]:.3f} x {esp[1]:.3f} x "
          f"{esp[2]:.3f} mm ({time.time() - t0:.1f} s)")
    F = {"V": V, "VM": VM, "Vs": Vs}
    M, guardar, aux = {}, {}, []
    for e in receta["estructuras"]:
        clave = e.get("clave", "")
        if not re.match(r"^[a-z0-9_]+$", clave):
            raise SystemExit(f"clave no válida {clave!r}: minúsculas ASCII, números y _")
        extra = [c for c in e if c not in CAMPOS and not c.startswith("_")]
        if extra:
            print(f"  [{clave}] aviso: campos desconocidos ignorados: {extra}")
        t1 = time.time()
        reg, notas, sem = segmentar_estructura(e, F, M, minfo, modo_conteo)
        M[clave] = reg
        n = int(reg.sum())
        for x in notas:
            print(f"  [{clave}] {x}")
        if e.get("auxiliar"):
            aux.append(clave)
            print(f"{clave:<22} (auxiliar) {n:>9} vóxeles  {time.time() - t1:5.1f} s")
            continue
        guardar[clave] = reg
        par = {c: v for c, v in e.items() if c not in ("clave", "fuente") and not c.startswith("_")}
        if sem:
            par["semillas_reducidas"] = [list(s) for s in sem]
        if notas:
            par["notas"] = notas
        minfo["estructuras"][clave] = dict(voxeles=n, volumen_ml=round(n * ml_vox, 1),
                                           fuente=e.get("fuente", "Vs"), parametros=par)
        print(f"{clave:<22} {n:>9} vóxeles {n * ml_vox:9.1f} mL  {time.time() - t1:5.1f} s")
    if aux:
        minfo["auxiliares"] = aux
    ruta_npz = os.path.join(salida, "mascaras.npz")
    if os.path.exists(ruta_npz):
        try:
            viejas = set(np.load(ruta_npz).files) - set(guardar)
        except Exception:
            viejas = set()
        if viejas:
            print(f"Aviso: se reemplaza mascaras.npz; estas claves de una corrida anterior no están en la receta y "
                  f"se pierden (vuelva a correr trazar_luz.py manga si eran mangas): {sorted(viejas)}")
    guardar_npz(ruta_npz, guardar)
    guardar_json(os.path.join(salida, "mascaras.json"), minfo)
    centro = receta.get("centro", "cuerpo")
    if centro in M and M[centro].any():
        c = coords.centro_de_mascara(vinfo, minfo, M[centro])
    else:
        print(f"Aviso: no hay estructura '{centro}' para el centro; se usa el centro del recorte.")
        centro = "recorte"
        f = np.array(minfo["forma"], float)
        c = coords.voxel_a_lps(vinfo, *coords.reducido_a_voxel(minfo, *((f - 1) / 2.0)))
    guardar_json(os.path.join(salida, "mapeo.json"),
                 dict(centro_mm=[float(x) for x in c], escala=0.1, convencion="B=(P-C)/10 cm; glTF=(Bx,Bz,-By)",
                      estructura_centro=centro))
    print(f"Escritos mascaras.npz, mascaras.json y mapeo.json en {salida} ({time.time() - t0:.1f} s). "
          "Revise con: cortes_qa.py superponer")


if __name__ == "__main__":
    main()
