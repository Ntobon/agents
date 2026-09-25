"""Luz de un órgano hueco o de un vaso: trayecto, manga de pared o lesión alrededor, y medidas.

  python trazar_luz.py ruta  --trabajo DIR --caja k0:k1,j0:j1,i0:i1 [--eje k|j|i]
                             [--luz aire|contraste | --rango lo:hi] [--puntos "k j i; ..."]
                             [--suavizar 5] [--area-min 4] [--salto-max 12] [--zona nombre:s0:s1]
  python trazar_luz.py ruta  --trabajo DIR --manual "k j i; k j i; ..." [--paso 1] [--luz ...]
  python trazar_luz.py manga --trabajo DIR --radio 12 --clave lesion [--rango -20:200] [--fuente Vs]
                             [--menos higado,arterias+dil:1] [--desde s0 --hasta s1] [--mayor-componente]
  python trazar_luz.py medir --trabajo DIR --clave lesion [--paso 2] [--umbral 5] [--desde s0 --hasta s1]

ruta: en cada corte de la caja (a lo largo de --eje) toma la luz (aire < -400 UH, contraste > 150 UH
  o un rango de intensidad en RM), su componente mayor y, desde el segundo corte, la que continúa la
  anterior; el trayecto es la línea de sus centroides, suavizada. Los cortes sin luz (un segmento
  colapsado o estrecho) se interpolan y quedan en «huecos»; --puntos obliga el paso por puntos dados.
  --manual arma el trayecto con puntos de paso (se subdivide cada tramo sin mover los vértices).
  Radio equivalente por punto = sqrt(área · cos θ / π), con θ el ángulo entre el trayecto y la normal
  del corte (corrige la sección alargada de una luz oblicua). Escribe ruta.json y ruta_qa.png.
manga: vóxeles de la rejilla reducida a <= R mm del tramo [s0, s1] del trayecto, dentro del rango de
  la fuente (V/VM/Vs) y fuera de las máscaras de --menos; agrega la clave a mascaras.npz/json.
medir: por estación a lo largo del trayecto: radio de la luz, área de la manga, radio externo
  equivalente y grosor (externo - luz); largo total con grosor > umbral, tramo continuo más largo,
  grosor máximo y luz mínima. Escribe medidas.json. Son aproximaciones por umbrales, no una medición
  radiológica: no van a documentos para médicos como si fueran un informe.
Coordenadas: vóxel del volumen completo [k, j, i] (coords.py). s = distancia a lo largo del trayecto (mm).
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coords  # noqa: E402
import cortes_qa as qa  # noqa: E402
import morfologia as mf  # noqa: E402
import segmentar as sg  # noqa: E402

LUZ = {"aire": (None, -400.0), "contraste": (150.0, None)}
EJES = {"k": 0, "j": 1, "i": 2}
NOTA_MEDIDAS = ("Medidas aproximadas por umbrales sobre una sola serie (volumen parcial, rejilla reducida, "
                "manga de radio fijo): sirven para entender, no son una medición radiológica ni un informe.")


# ------------------------------------------------------------------ utilidades
def _json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _par(txt):
    a, b = txt.split(":")
    return (float(a) if a.strip() else None), (float(b) if b.strip() else None)


def criterio(args, info):
    if args.rango:
        return _par(args.rango)
    luz = args.luz or "aire"
    if luz not in LUZ:
        raise SystemExit("--luz debe ser aire o contraste (o use --rango lo:hi)")
    if info.get("modalidad") != "CT":
        raise SystemExit("En RM no hay unidades absolutas: use --rango lo:hi (mídalo con cortes_qa.py muestrear).")
    return LUZ[luz]


def en_rango(a, lo, hi):
    m = np.ones(a.shape, bool)
    if lo is not None:
        m &= a > lo
    if hi is not None:
        m &= a < hi
    return m


def suavizar_plano(a):
    """Media 3x3 dentro de cada corte (eje 0) de un arreglo 3D."""
    p = np.pad(a, ((0, 0), (1, 1), (1, 1)), mode="edge")
    s = np.zeros(a.shape, np.float32)
    for dy in range(3):
        for dx in range(3):
            s += p[:, dy:dy + a.shape[1], dx:dx + a.shape[2]]
    return s / 9.0


def longitud_arco(P_mm):
    d = np.linalg.norm(np.diff(P_mm, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(d)])


def media_movil(x, w):
    if w <= 1 or len(x) < 3:
        return x.copy()
    h = w // 2
    out = np.empty_like(x)
    for n in range(len(x)):
        a, b = max(0, n - h), min(len(x), n + h + 1)
        out[n] = x[a:b].mean(0)
    return out


def tangentes(P_mm):
    if len(P_mm) < 2:
        return np.tile([0.0, 0.0, 1.0], (len(P_mm), 1))
    t = np.gradient(P_mm, axis=0)
    n = np.linalg.norm(t, axis=1, keepdims=True)
    return t / np.maximum(n, 1e-9)


def tramos(bandera):
    """Índices [ini, fin] (inclusivos) de las corridas True."""
    out, ini = [], None
    for n, b in enumerate(list(bandera) + [False]):
        if b and ini is None:
            ini = n
        elif not b and ini is not None:
            out.append([ini, n - 1])
            ini = None
    return out


def largo_tramo(s, a, b):
    """Largo (mm) de los puntos a..b: cada punto aporta media distancia a cada vecino."""
    ini = (s[a] + s[max(a - 1, 0)]) / 2
    fin = (s[b] + s[min(b + 1, len(s) - 1)]) / 2
    return float(fin - ini)


def cargar_ruta(trabajo, nombre):
    r = _json(os.path.join(trabajo, nombre))
    return r, np.asarray(r["puntos_voxel"], float)


def subtrayecto(P, s, s0, s1):
    """Polilínea entre las distancias s0 y s1 (interpola los extremos)."""
    s0 = s[0] if s0 is None else max(s0, s[0])
    s1 = s[-1] if s1 is None else min(s1, s[-1])
    if s1 <= s0:
        raise SystemExit(f"Tramo vacío: la ruta mide {s[-1]:.1f} mm.")
    dentro = (s > s0) & (s < s1)
    ini = np.array([np.interp(s0, s, P[:, c]) for c in range(3)])
    fin = np.array([np.interp(s1, s, P[:, c]) for c in range(3)])
    return np.vstack([ini, P[dentro], fin]), np.concatenate([[s0], s[dentro], [s1]])


def proyectar(Q, P, s):
    """Distancia mínima de cada punto Q (mm) a la polilínea P (mm), distancia s del punto más cercano
    y si ese punto cae en una punta (proyección recortada en el primer o último vértice)."""
    dist = np.full(len(Q), np.inf)
    sc = np.zeros(len(Q))
    punta = np.zeros(len(Q), bool)
    nseg = len(P) - 1
    for n in range(max(nseg, 1)):
        a = P[n]
        b = P[n + 1] if nseg else P[n]
        ab = b - a
        L2 = float(ab @ ab)
        t_raw = ((Q - a) @ ab) / L2 if L2 > 0 else np.zeros(len(Q))
        t = np.clip(t_raw, 0.0, 1.0)
        d = np.linalg.norm(Q - (a + t[:, None] * ab), axis=1)
        mejor = d < dist
        dist[mejor] = d[mejor]
        sc[mejor] = s[n] + t[mejor] * math.sqrt(L2)
        p = np.zeros(len(Q), bool)
        if n == 0:
            p |= t_raw < 0
        if n == max(nseg, 1) - 1:
            p |= t_raw > 1
        punta[mejor] = p[mejor]
    return dist, sc, punta


# ------------------------------------------------------------------ ruta
def _componentes(lab):
    """Área, centroide y corte de cada etiqueta (componentes por corte)."""
    s, a, b = np.nonzero(lab)
    L = lab[s, a, b]
    n = int(lab.max())
    area = np.bincount(L, minlength=n + 1).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        ca = np.bincount(L, weights=a, minlength=n + 1) / area
        cb = np.bincount(L, weights=b, minlength=n + 1) / area
        cs = np.bincount(L, weights=s, minlength=n + 1) / area
    return area, ca, cb, np.rint(np.nan_to_num(cs)).astype(int)


def ruta_automatica(args, info, vol, lo, hi):
    nk, nj, ni = vol.shape
    try:
        pk, pj, pi = args.caja.split(",")
    except ValueError:
        raise SystemExit("--caja debe ser k0:k1,j0:j1,i0:i1 (volumen completo)")
    k0, k1 = qa.rango(pk, nk)
    j0, j1 = qa.rango(pj, nj)
    i0, i1 = qa.rango(pi, ni)
    off = np.array([k0, j0, i0], float)
    e = EJES[args.eje]
    otros = [x for x in range(3) if x != e]
    esp = np.asarray(info["espaciado_mm"], float)
    sub = np.asarray(vol[k0:k1, j0:j1, i0:i1], np.float32)
    sub = np.moveaxis(sub, e, 0)                                   # (corte, a, b)
    luz = en_rango(suavizar_plano(sub), lo, hi)
    lab, n = mf.etiquetar(luz, plano=True)
    if n == 0:
        raise SystemExit("No hay luz con ese criterio dentro de la caja (revise la caja y --luz/--rango).")
    area, ca, cb, cs = _componentes(lab)
    ea, eb = esp[otros[0]], esp[otros[1]]
    grandes = area >= args.area_min
    grandes[0] = False
    por_corte = {}
    for L in np.nonzero(grandes)[0]:
        por_corte.setdefault(int(cs[L]), []).append(int(L))
    wps = {}
    for p in qa.puntos(args.puntos):
        loc = np.asarray(p, float) - off
        sidx = int(round(loc[e]))
        if 0 <= sidx < sub.shape[0]:
            wps[sidx] = (loc[otros[0]], loc[otros[1]])
    elegido, previa, cprev = {}, None, None
    for sidx in range(sub.shape[0]):
        cands = por_corte.get(sidx, [])
        ref = wps.get(sidx, cprev)
        sel = None
        if cands and previa is not None and sidx not in wps:
            sol = lab[sidx][previa]
            sol = sol[np.isin(sol, cands)]
            if sol.size:
                sel = int(np.bincount(sol).argmax())
        if sel is None and cands and ref is not None:
            d = [math.hypot((ca[L] - ref[0]) * ea, (cb[L] - ref[1]) * eb) for L in cands]
            if min(d) <= args.salto_max:
                sel = cands[int(np.argmin(d))]
        if sel is None and cands and ref is None:
            sel = max(cands, key=lambda L: area[L])
        if sel is not None:
            elegido[sidx] = sel
            previa = lab[sidx] == sel
            cprev = (ca[sel], cb[sel])
        else:
            previa = None
            if sidx in wps:                 # el trayecto pasa por el punto aunque no haya luz
                cprev = wps[sidx]
    conocidos = sorted(set(elegido) | set(wps))
    if not conocidos:
        raise SystemExit("No se encontró luz en la caja.")
    filas = []
    for sidx in range(conocidos[0], conocidos[-1] + 1):
        # un punto de paso elige qué luz seguir; solo se vuelve punto del trayecto donde no hay luz
        if sidx in wps and sidx not in elegido:
            a_, b_ = wps[sidx]
            filas.append((sidx, a_, b_, 0.0, True, True))
        elif sidx in elegido:
            L = elegido[sidx]
            filas.append((sidx, ca[L], cb[L], area[L], False, False))
        else:
            filas.append((sidx, np.nan, np.nan, 0.0, True, False))
    F = np.array([[f[0], f[1], f[2]] for f in filas], float)
    for c in (1, 2):                                               # interpola los huecos
        ok = ~np.isnan(F[:, c])
        F[~ok, c] = np.interp(F[~ok, 0], F[ok, 0], F[ok, c])
    hueco = np.array([f[4] for f in filas])
    forzado = np.array([f[5] for f in filas])
    area_px = np.array([f[3] for f in filas])
    suave = media_movil(F[:, 1:], args.suavizar)
    suave[forzado] = F[forzado, 1:]
    F[:, 1:] = suave
    P = np.zeros((len(F), 3))
    P[:, e] = F[:, 0]
    P[:, otros[0]] = F[:, 1]
    P[:, otros[1]] = F[:, 2]
    P += off
    cos = np.abs(tangentes(P * esp)[:, e])
    radios = np.sqrt(area_px * ea * eb * cos / math.pi)
    radios[hueco] = 0.0
    return P, radios, hueco, dict(caja=[[k0, k1], [j0, j1], [i0, i1]], eje=args.eje,
                                  puntos_de_paso=[list(map(float, p)) for p in qa.puntos(args.puntos)])


def radio_local(vol, info, P, e, lo, hi, tangente, ventana_mm=25.0, busca_mm=3.0):
    """Radio equivalente de la luz alrededor de un punto, en el corte perpendicular a --eje."""
    esp = np.asarray(info["espaciado_mm"], float)
    otros = [x for x in range(3) if x != e]
    c = [int(round(x)) for x in P]
    if not all(0 <= c[x] < vol.shape[x] for x in range(3)):
        return 0.0
    sl = [slice(None)] * 3
    sl[e] = c[e]
    lim = []
    for x in otros:
        h = int(ventana_mm / esp[x])
        lim.append((max(c[x] - h, 0), min(c[x] + h + 1, vol.shape[x])))
        sl[x] = slice(*lim[-1])
    img = np.asarray(vol[tuple(sl)], np.float32)[None]
    m = en_rango(suavizar_plano(img), lo, hi)[0]
    lab, n = mf.etiquetar(m)
    if n == 0:
        return 0.0
    pa, pb = c[otros[0]] - lim[0][0], c[otros[1]] - lim[1][0]
    L = lab[pa, pb] if (0 <= pa < m.shape[0] and 0 <= pb < m.shape[1]) else 0
    if not L:
        yy, xx = np.nonzero(lab)
        d = np.hypot((yy - pa) * esp[otros[0]], (xx - pb) * esp[otros[1]])
        if d.min() > busca_mm:
            return 0.0
        L = lab[yy[d.argmin()], xx[d.argmin()]]
    area = float((lab == L).sum()) * esp[otros[0]] * esp[otros[1]]
    return math.sqrt(area * abs(tangente[e]) / math.pi)


def ruta_manual(args, info, vol, crit):
    W = np.asarray(qa.puntos(args.manual), float)
    if len(W) < 2:
        raise SystemExit("--manual necesita al menos 2 puntos 'k j i; k j i'")
    esp = np.asarray(info["espaciado_mm"], float)
    pts = []
    for a, b in zip(W[:-1], W[1:]):
        L = float(np.linalg.norm((b - a) * esp))
        m = max(1, int(math.ceil(L / args.paso)))
        pts += [a + (b - a) * t for t in np.arange(m) / m]
    pts.append(W[-1])
    P = np.array(pts)
    e = EJES[args.eje]
    if crit is None:
        radios = np.zeros(len(P))
    else:
        T = tangentes(P * esp)
        radios = np.array([radio_local(vol, info, p, e, crit[0], crit[1], t) for p, t in zip(P, T)])
    hueco = radios <= 0
    return P, radios, hueco, dict(manual=[list(map(float, w)) for w in W], eje=args.eje)


def qa_ruta(ruta_png, info, vol, P, hueco, caja, modo, ventana_txt):
    """Proyección coronal (sobre las filas j de la caja) y sagital (sobre las columnas i), con el
    trayecto: amarillo donde hay luz, rojo donde se interpoló."""
    nk, nj, ni = vol.shape
    dz, dy, dx = info["espaciado_mm"]
    (k0, k1), (j0, j1), (i0, i1) = caja
    mg = 20
    ka, kb = max(k0 - mg, 0), min(k1 + mg, nk)
    ja, jb = max(j0 - mg, 0), min(j1 + mg, nj)
    ia, ib = max(i0 - mg, 0), min(i1 + mg, ni)
    reg = np.asarray(vol[ka:kb, ja:jb, ia:ib], np.float32)
    f = {"minip": np.min, "mip": np.max}.get(modo, np.mean)
    cor = f(reg[:, j0 - ja:j1 - ja, :], axis=1)
    sag = f(reg[:, :, i0 - ia:i1 - ia], axis=2)
    lo, hi = qa.ventana(info, ventana_txt)
    fnt = qa.fuente(12)
    es = min(4.0, 420.0 / max(ib - ia, jb - ja, 1))
    tiles = []
    for img, eje_h, h0, h1, col_h, dh in ((cor, "i", ia, ib, 2, dx), (sag, "j", ja, jb, 1, dy)):
        g = qa.gris(img[::-1], lo, hi)
        lineas = []
        for a, b in tramos(~hueco) + tramos(hueco):
            a0, b0 = max(a - 1, 0), min(b + 1, len(P) - 1)
            color = (255, 60, 60) if hueco[a] else (255, 220, 0)
            lineas.append(([(P[n, 0], P[n, col_h]) for n in range(a0, b0 + 1)], color, 2))
        box = [(k0, (i0 if eje_h == "i" else j0)), (k0, (i1 if eje_h == "i" else j1)),
               (k1, (i1 if eje_h == "i" else j1)), (k1, (i0 if eje_h == "i" else j0)),
               (k0, (i0 if eje_h == "i" else j0))]
        lineas.insert(0, (box, (90, 200, 255), 1))
        nombre = "coronal (proyección en j de la caja)" if eje_h == "i" else "sagital (proyección en i de la caja)"
        tiles.append(qa.mosaico(np.stack([g] * 3, -1), nombre, (("k", ka, kb, True), (eje_h, h0, h1)), 32, fnt,
                                es, es * dz / dh, (), lineas))
    img = qa.componer(tiles, 2, [("luz medida", (255, 220, 0)), ("interpolado (sin luz)", (255, 60, 60)),
                                 ("caja", (90, 200, 255))], fnt)
    qa.guardar(img, ruta_png)


def cmd_ruta(args):
    info, vol = qa.cargar_volumen(args.trabajo)
    manual = bool(args.manual)
    crit = criterio(args, info) if (not manual or args.luz or args.rango) else None
    if manual:
        P, radios, hueco, extra = ruta_manual(args, info, vol, crit)
    else:
        if not args.caja:
            raise SystemExit("Indique --caja (modo automático) o --manual.")
        P, radios, hueco, extra = ruta_automatica(args, info, vol, *crit)
    s = longitud_arco(coords.voxel_a_lps(info, P[:, 0], P[:, 1], P[:, 2]))
    ruta_mapeo = os.path.join(args.trabajo, "mapeo.json")
    if os.path.exists(ruta_mapeo):
        G = coords.voxel_a_gltf(info, _json(ruta_mapeo), P[:, 0], P[:, 1], P[:, 2]).tolist()
    else:
        G = []
        print("Aviso: no hay mapeo.json (se crea con segmentar.py); puntos_gltf queda vacío.")
    zonas = []
    for z in args.zona or []:
        nombre, a, b = z.rsplit(":", 2)
        a, b = float(a), float(b)
        idx = np.nonzero((s >= a) & (s <= b))[0]
        if len(idx):
            zonas.append(dict(nombre=nombre, desde=int(idx[0]), hasta=int(idx[-1]), s0_mm=a, s1_mm=b))
    huecos = tramos(hueco)
    out = dict(puntos_voxel=np.round(P, 3).tolist(), puntos_gltf=np.round(G, 4).tolist() if G else [],
               radios_mm=np.round(radios, 2).tolist(), zonas=zonas, huecos=huecos,
               s_mm=np.round(s, 2).tolist(), longitud_mm=round(float(s[-1]), 1),
               criterio=dict(lo=crit[0], hi=crit[1]) if crit else None, **extra,
               nota="Trayecto aproximado de la luz (umbral + centroides); radio 0 = sin luz visible.")
    ruta_json = os.path.join(args.trabajo, args.salida)
    sg.guardar_json(ruta_json, out)
    modo = {"aire": "minip", "contraste": "mip"}.get(args.luz or ("" if args.rango else "aire"), "media")
    caja = extra.get("caja") or [[int(P[:, 0].min()) - 5, int(P[:, 0].max()) + 6],
                                 [int(P[:, 1].min()) - 15, int(P[:, 1].max()) + 16],
                                 [int(P[:, 2].min()) - 15, int(P[:, 2].max()) + 16]]
    caja = [[max(a, 0), min(b, n)] for (a, b), n in zip(caja, vol.shape)]
    qa_ruta(os.path.splitext(ruta_json)[0] + "_qa.png", info, vol, P, hueco, caja, modo, args.ventana)
    medidos = radios[~hueco]
    print(f"Ruta: {len(P)} puntos, {s[-1]:.1f} mm; {len(huecos)} huecos "
          f"({sum(largo_tramo(s, a, b) for a, b in huecos):.1f} mm sin luz visible)"
          + (f"; radio equivalente {medidos.min():.1f}-{medidos.max():.1f} mm (mediana {np.median(medidos):.1f})"
             if medidos.size else ""))
    print(f"Escrito {ruta_json}")


# ------------------------------------------------------------------ manga
def _mascaras(trabajo):
    minfo = _json(os.path.join(trabajo, "mascaras.json"))
    npz = np.load(os.path.join(trabajo, "mascaras.npz"))
    return minfo, {k: npz[k].astype(bool) for k in npz.files}


def _vox_mm(info):
    return np.asarray(info["espaciado_mm"], float)


def cmd_manga(args):
    info, vol = qa.cargar_volumen(args.trabajo)
    minfo, M = _mascaras(args.trabajo)
    if not re.match(r"^[a-z0-9_]+$", args.clave):
        raise SystemExit("--clave: minúsculas ASCII, números y _")
    ruta, P = cargar_ruta(args.trabajo, args.ruta)
    esp = _vox_mm(info)
    Pmm = P * esp                                           # marco del volumen completo en mm
    s = longitud_arco(Pmm)
    Psub, ssub = subtrayecto(Pmm, s, args.desde, args.hasta)
    forma = tuple(minfo["forma"])
    # caja de candidatos en la rejilla reducida
    Pred = np.array(coords.voxel_a_reducido(minfo, *(Psub / esp).T)).T
    ext = np.ceil(args.radio / np.asarray(minfo["espaciado_mm"], float)).astype(int) + 1
    lo = np.maximum(np.floor(Pred.min(0)).astype(int) - ext, 0)
    hi = np.minimum(np.ceil(Pred.max(0)).astype(int) + ext + 1, forma)
    kk, jj, ii = np.meshgrid(*[np.arange(a, b) for a, b in zip(lo, hi)], indexing="ij")
    idx = np.stack([kk.ravel(), jj.ravel(), ii.ravel()], 1)
    Q = np.array(coords.reducido_a_voxel(minfo, *idx.T)).T * esp
    dist, _, _ = proyectar(Q, Psub, ssub)
    m = np.zeros(forma, bool)
    dentro = dist <= args.radio
    m[tuple(idx[dentro].T)] = True
    fuente = None
    if args.rango:
        a, b = _par(args.rango)
        fuente = args.fuente
        V, VM, Vs = sg.preprocesar(vol, minfo["recorte"], sg._factores(minfo["reduccion"]),
                                   minfo.get("bordes", "replicar"))
        m &= en_rango({"V": V, "VM": VM, "Vs": Vs}[fuente], a, b)
    menos = []
    for x in (args.menos.split(",") if args.menos else []):
        c, n = sg.parse_excluir(x)
        if c not in M:
            raise SystemExit(f"--menos: no existe la máscara '{c}' (claves: {sorted(M)})")
        m &= ~(mf.dilatar(M[c], n=n) if n else M[c])
        menos.append(x)
    if args.mayor_componente:
        m = mf.mayor_componente(m)
    M[args.clave] = m
    n = int(m.sum())
    ml = n * float(np.prod(minfo["espaciado_mm"])) / 1000.0
    minfo.setdefault("estructuras", {})[args.clave] = dict(
        voxeles=n, volumen_ml=round(ml, 1), fuente=f"manga({fuente})" if fuente else "manga",
        parametros=dict(ruta=args.ruta, radio_mm=args.radio, desde_mm=round(float(ssub[0]), 2),
                        hasta_mm=round(float(ssub[-1]), 2), rango=list(_par(args.rango)) if args.rango else None,
                        menos=menos, mayor_componente=bool(args.mayor_componente)))
    sg.guardar_npz(os.path.join(args.trabajo, "mascaras.npz"), M)
    sg.guardar_json(os.path.join(args.trabajo, "mascaras.json"), minfo)
    print(f"Manga '{args.clave}': {n} vóxeles, {ml:.1f} mL (radio {args.radio} mm, tramo {ssub[0]:.1f}-{ssub[-1]:.1f} mm "
          f"de {s[-1]:.1f}). Revise con cortes_qa.py superponer --claves {args.clave}")


# ------------------------------------------------------------------ medir
def cmd_medir(args):
    info, _ = qa.cargar_volumen(args.trabajo)
    minfo, M = _mascaras(args.trabajo)
    if args.clave not in M:
        raise SystemExit(f"No existe la máscara '{args.clave}' (claves: {sorted(M)})")
    ruta, P = cargar_ruta(args.trabajo, args.ruta)
    radios = np.asarray(ruta["radios_mm"], float)
    esp = _vox_mm(info)
    Pmm = P * esp
    s = longitud_arco(Pmm)
    hueco = np.zeros(len(P), bool)
    for a, b in ruta.get("huecos", []):
        hueco[a:b + 1] = True
    idx = np.argwhere(M[args.clave])
    if len(idx) == 0:
        raise SystemExit("La máscara está vacía.")
    Q = np.array(coords.reducido_a_voxel(minfo, *idx.T)).T * esp
    s0 = s[0] if args.desde is None else max(args.desde, s[0])
    s1 = s[-1] if args.hasta is None else min(args.hasta, s[-1])
    nb = max(1, int(math.floor((s1 - s0) / args.paso)))
    bordes = s0 + args.paso * np.arange(nb + 1)
    vox_mm3 = float(np.prod(minfo["espaciado_mm"]))
    centros = (bordes[:-1] + bordes[1:]) / 2
    radio_manga = minfo.get("estructuras", {}).get(args.clave, {}).get("parametros", {}).get("radio_mm")
    r_max = (radio_manga or args.radio_max) + float(np.linalg.norm(minfo["espaciado_mm"])) / 2

    def punto(x):
        return np.array([np.interp(x, s, Pmm[:, c]) for c in range(3)])
    # sección local en cada estación: losa de ancho `paso` perpendicular a la tangente (sin
    # acumulaciones en las curvas, a diferencia de proyectar por distancia a lo largo)
    h = max(args.paso, 1.0)
    cuenta = np.zeros(nb)
    for n, c in enumerate(centros):
        C = punto(c)
        T = punto(min(c + h, s[-1])) - punto(max(c - h, s[0]))
        T /= max(np.linalg.norm(T), 1e-9)
        v = Q - C
        a = v @ T
        rad = np.linalg.norm(v - a[:, None] * T, axis=1)
        cuenta[n] = int(((np.abs(a) <= args.paso / 2) & (rad <= r_max)).sum())
    r_luz = np.interp(centros, s, radios)
    h_st = np.interp(centros, s, hueco.astype(float)) >= 0.5
    area = cuenta * vox_mm3 / args.paso
    r_ext = np.sqrt(area / math.pi + r_luz ** 2)
    grosor = r_ext - r_luz
    sobre = grosor > args.umbral
    corridas = tramos(sobre)
    largo = [(centros[b] - centros[a] + args.paso, a, b) for a, b in corridas]
    mejor = max(largo) if largo else None
    fuera = ~h_st
    i_min = int(np.argmin(np.where(fuera, r_luz, np.inf))) if fuera.any() else None
    estaciones = [dict(s_mm=round(float(c), 1), r_luz_mm=round(float(r), 2), area_pared_mm2=round(float(a), 1),
                       r_externo_mm=round(float(x), 2), grosor_mm=round(float(g), 2), sin_luz=bool(h))
                  for c, r, a, x, g, h in zip(centros, r_luz, area, r_ext, grosor, h_st)]
    resumen = dict(
        tramo_medido_mm=[round(float(s0), 1), round(float(bordes[-1]), 1)],
        largo_con_grosor_sobre_umbral_mm=round(float(sobre.sum() * args.paso), 1),
        tramo_continuo_mas_largo=(dict(desde_mm=round(float(centros[mejor[1]] - args.paso / 2), 1),
                                       hasta_mm=round(float(centros[mejor[2]] + args.paso / 2), 1),
                                       largo_mm=round(float(mejor[0]), 1)) if mejor else None),
        grosor_max_mm=round(float(grosor.max()), 1), s_grosor_max_mm=round(float(centros[int(grosor.argmax())]), 1),
        grosor_mediano_en_tramo_mm=(round(float(np.median(grosor[sobre])), 1) if sobre.any() else None),
        luz_minima_diametro_mm=(round(float(2 * r_luz[i_min]), 1) if i_min is not None else None),
        s_luz_minima_mm=(round(float(centros[i_min]), 1) if i_min is not None else None),
        largo_sin_luz_visible_mm=round(float(h_st.sum() * args.paso), 1),
    )
    avisos = []
    if radio_manga and (r_ext >= 0.9 * radio_manga).any():
        avisos.append(f"En {int((r_ext >= 0.9 * radio_manga).sum())} estaciones el radio externo llega al radio de la "
                      f"manga ({radio_manga} mm): la pared podría ser más gruesa (repita manga con más radio).")
    avisos.append("La manga cuenta todo el tejido del rango dentro del radio: órganos vecinos pegados a la pared "
                  "inflan el grosor; excluya sus máscaras con --menos y revise con superponer.")
    out = dict(nota=NOTA_MEDIDAS, clave=args.clave, ruta=args.ruta, paso_mm=args.paso, umbral_grosor_mm=args.umbral,
               radio_manga_mm=radio_manga, resumen=resumen, estaciones=estaciones, avisos=avisos)
    sg.guardar_json(os.path.join(args.trabajo, args.salida), out)
    print(f"{'s (mm)':>7} {'r luz':>6} {'área pared':>11} {'r ext':>6} {'grosor':>7}")
    for x in estaciones:
        marca = " *" if x["grosor_mm"] > args.umbral else ""
        print(f"{x['s_mm']:>7.1f} {x['r_luz_mm']:>6.1f} {x['area_pared_mm2']:>9.0f} mm2 {x['r_externo_mm']:>6.1f} "
              f"{x['grosor_mm']:>6.1f}{marca}{'  (sin luz)' if x['sin_luz'] else ''}")
    r = resumen
    print(f"\nAPROXIMADO (umbrales, no es una medición radiológica). Grosor > {args.umbral} mm en "
          f"{r['largo_con_grosor_sobre_umbral_mm']} mm del trayecto"
          + (f"; tramo continuo más largo {r['tramo_continuo_mas_largo']['largo_mm']} mm "
             f"(s {r['tramo_continuo_mas_largo']['desde_mm']}-{r['tramo_continuo_mas_largo']['hasta_mm']})"
             if r["tramo_continuo_mas_largo"] else "")
          + f"; grosor máximo {r['grosor_max_mm']} mm (s {r['s_grosor_max_mm']}).")
    if r["luz_minima_diametro_mm"] is not None:
        print(f"Luz mínima medida: diámetro equivalente {r['luz_minima_diametro_mm']} mm (s {r['s_luz_minima_mm']}); "
              f"sin luz visible en {r['largo_sin_luz_visible_mm']} mm.")
    for a in avisos:
        print("Aviso: " + a)
    print(f"Escrito {os.path.join(args.trabajo, args.salida)}")


# ------------------------------------------------------------------ CLI
def main():
    qa._consola()
    ap = argparse.ArgumentParser(description="Trayecto de una luz (ruta), manga de pared o lesión (manga) y medidas "
                                             "aproximadas de largo x grosor (medir).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def base(p):
        p.add_argument("--trabajo", "--volumen", dest="trabajo", default=".",
                       help="carpeta de trabajo (volumen, máscaras, mapeo y rutas)")
        p.add_argument("--ruta", default="ruta.json", help="archivo de la ruta dentro de la carpeta de trabajo")

    p = sub.add_parser("ruta", help="trayecto de la luz -> ruta.json + ruta_qa.png")
    base(p)
    p.add_argument("--caja", help="k0:k1,j0:j1,i0:i1 (volumen completo) donde buscar la luz")
    p.add_argument("--eje", choices=["k", "j", "i"], default="k",
                   help="eje de barrido: el que la luz recorre de punta a punta (k = axiales)")
    p.add_argument("--luz", choices=["aire", "contraste"], help="criterio de TAC: aire (< -400) o contraste (> 150)")
    p.add_argument("--rango", help="criterio propio lo:hi (obligatorio en RM)")
    p.add_argument("--puntos", help="puntos de paso obligados 'k j i; ...' (p. ej. por un tramo colapsado)")
    p.add_argument("--manual", help="trayecto completo por puntos de paso 'k j i; k j i; ...'")
    p.add_argument("--paso", type=float, default=1.0, help="subdivisión del trayecto manual (mm)")
    p.add_argument("--suavizar", type=int, default=5, help="ventana de la media móvil de los centroides (puntos)")
    p.add_argument("--area-min", dest="area_min", type=float, default=4, help="área mínima de la luz (píxeles)")
    p.add_argument("--salto-max", dest="salto_max", type=float, default=12.0,
                   help="distancia máxima (mm) para retomar la luz después de un hueco")
    p.add_argument("--zona", action="append", help="tramo con nombre 'nombre:s0:s1' (mm); se puede repetir")
    p.add_argument("--ventana", help="ventana del PNG de control")
    p.add_argument("--salida", default="ruta.json")
    p.set_defaults(fn=cmd_ruta)

    p = sub.add_parser("manga", help="pared o lesión alrededor de un tramo de la ruta -> nueva máscara")
    base(p)
    p.add_argument("--clave", required=True, help="nombre de la máscara nueva (p. ej. lesion, pared)")
    p.add_argument("--radio", type=float, required=True, help="radio de la manga en mm")
    p.add_argument("--rango", help="lo:hi del tejido (p. ej. -20:200); sin rango, un tubo sólido")
    p.add_argument("--fuente", choices=["V", "VM", "Vs"], default="Vs")
    p.add_argument("--menos", help="máscaras a restar, 'higado,arterias+dil:1'")
    p.add_argument("--desde", type=float, help="s inicial (mm)")
    p.add_argument("--hasta", type=float, help="s final (mm)")
    p.add_argument("--mayor-componente", dest="mayor_componente", action="store_true",
                   help="conservar solo el componente conexo mayor (quita motas)")
    p.set_defaults(fn=cmd_manga)

    p = sub.add_parser("medir", help="largo x grosor aproximados a lo largo de la ruta -> medidas.json")
    base(p)
    p.add_argument("--clave", required=True, help="máscara de pared o lesión (la de manga)")
    p.add_argument("--paso", type=float, default=2.0, help="largo de cada estación (mm)")
    p.add_argument("--umbral", type=float, default=5.0, help="grosor que cuenta como engrosado (mm)")
    p.add_argument("--desde", type=float)
    p.add_argument("--hasta", type=float)
    p.add_argument("--radio-max", dest="radio_max", type=float, default=25.0,
                   help="radio de la sección si la máscara no vino de manga (mm)")
    p.add_argument("--salida", default="medidas.json")
    p.set_defaults(fn=cmd_medir)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
