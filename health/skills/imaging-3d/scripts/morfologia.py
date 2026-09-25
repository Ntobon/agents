"""Primitivas morfológicas para segmentar.py y trazar_luz.py (solo numpy).

Todas usan vecindad de 6 (caras) en 3D y de 4 en 2D. Si scipy está instalado, las
componentes conexas lo usan (mismo resultado, más rápido); si no, hay una implementación
propia por tramos (run-length + unión de conjuntos vectorizada).

Convenciones heredadas del caso de origen (no cambiarlas sin revisar las recetas):
- La erosión no erosiona desde el borde del arreglo (fuera del arreglo cuenta como «dentro»):
  una estructura que toca el borde del recorte sigue más allá de él.
- crecer() = componentes de la máscara erosionada que contienen las semillas, y luego se
  devuelve lo erosionado dilatando dentro de la máscara original.
"""
import numpy as np

try:  # opcional
    from scipy import ndimage as _ndi
except Exception:  # pragma: no cover
    _ndi = None


# ------------------------------------------------------------------ dilatar / erosionar
def _vecinos(a, out, op):
    for ax in range(a.ndim):
        s1 = [slice(None)] * a.ndim
        s0 = [slice(None)] * a.ndim
        s1[ax], s0[ax] = slice(1, None), slice(None, -1)
        s1, s0 = tuple(s1), tuple(s0)
        if op == "or":
            out[s1] |= a[s0]
            out[s0] |= a[s1]
        else:
            out[s1] &= a[s0]
            out[s0] &= a[s1]


def dilatar(a, limite=None, n=1):
    """Dilatación de vecindad 6 (4 en 2D) repetida n veces; con límite, se recorta en cada paso."""
    a = np.asarray(a, bool)
    for _ in range(int(n)):
        c = a.copy()
        _vecinos(a, c, "or")
        if limite is not None:
            c &= limite
        a = c
    return a


def erosionar(a, n=1):
    """Erosión de vecindad 6 repetida n veces (el borde del arreglo no erosiona)."""
    a = np.asarray(a, bool)
    for _ in range(int(n)):
        c = a.copy()
        _vecinos(a, c, "and")
        a = c
    return a


# ------------------------------------------------------------------ sumas de caja 3x3x3
def suma_caja(a, modo="constante", dtype=np.float32):
    """Suma en una caja de 3 por eje (separable). modo: 'constante' (0 fuera), 'replicar'
    (borde repetido) o 'envolver' (como np.roll, se conserva para reproducir recetas viejas)."""
    pad = {"constante": "constant", "replicar": "edge", "envolver": "wrap"}[modo]
    s = np.pad(np.asarray(a, dtype), 1, mode=pad)
    for ax in range(s.ndim):
        n = s.shape[ax]
        t = [slice(None)] * s.ndim
        t0, t1, t2 = list(t), list(t), list(t)
        t0[ax], t1[ax], t2[ax] = slice(0, n - 2), slice(1, n - 1), slice(2, n)
        s = s[tuple(t0)] + s[tuple(t1)] + s[tuple(t2)]
    return s


def media_caja(V, modo="replicar"):
    """Suavizado 3x3x3 (media de 27 vóxeles). Divide por 27: la suma de la caja entre su conteo."""
    s = suma_caja(V, modo, np.float32)
    s /= np.float32(3 ** np.ndim(V))
    return s


def filtro_vecinos(m, minimo, modo="constante"):
    """Quita motas: conserva los vóxeles con al menos `minimo` vóxeles marcados en su caja 3x3x3
    (el propio vóxel cuenta)."""
    cnt = suma_caja(m, modo, np.uint8)
    return np.asarray(m, bool) & (cnt >= minimo)


# ------------------------------------------------------------------ componentes conexas
def etiquetar(m, plano=False):
    """Etiqueta componentes de vecindad 6 (3D) o 4 (2D). plano=True en 3D: solo dentro de cada
    corte (eje 0), sin unir cortes vecinos. Devuelve (etiquetas int32, n)."""
    m = np.asarray(m, bool)
    if _ndi is not None:
        st = _ndi.generate_binary_structure(m.ndim, 1)
        if plano and m.ndim == 3:
            st[0] = False
            st[2] = False
        lab, n = _ndi.label(m, structure=st)
        return lab.astype(np.int32), int(n)
    return _etiquetar_np(m, plano)


def _etiquetar_np(m, plano):
    forma = m.shape
    m3 = m.reshape((1,) * (3 - m.ndim) + forma)
    nk, nj, ni = m3.shape
    nfil = nk * nj
    pad = np.zeros((nfil, ni + 2), np.int8)
    pad[:, 1:-1] = m3.reshape(nfil, ni)
    d = np.diff(pad, axis=1)
    del pad
    fila, ini = np.nonzero(d == 1)
    _, fin = np.nonzero(d == -1)
    del d
    R = len(ini)
    if R == 0:
        return np.zeros(forma, np.int32), 0
    fila = fila.astype(np.int64)
    W = ni + 1
    c_ini = fila * W + ini
    c_fin = fila * W + fin
    pa, pb = [], []

    def enlazar(desp, valido):
        a = np.nonzero(valido)[0]
        if len(a) == 0:
            return
        t = fila[a] + desp
        lo = np.searchsorted(c_fin, t * W + ini[a], side="right")
        hi = np.searchsorted(c_ini, t * W + fin[a], side="left")
        cnt = hi - lo
        s = cnt > 0
        a, lo, cnt = a[s], lo[s], cnt[s]
        tot = int(cnt.sum())
        if tot == 0:
            return
        pa.append(np.repeat(a, cnt))
        pb.append(np.repeat(lo - (np.cumsum(cnt) - cnt), cnt) + np.arange(tot))

    enlazar(1, (fila % nj) < nj - 1)            # fila siguiente del mismo corte
    if not plano:
        enlazar(nj, (fila // nj) < nk - 1)      # misma fila del corte siguiente
    lab = np.arange(R, dtype=np.int64)
    if pa:
        A, B = np.concatenate(pa), np.concatenate(pb)
        while True:
            la, lb = lab[A], lab[B]
            dif = la != lb
            if not dif.any():
                break
            A, B, la, lb = A[dif], B[dif], la[dif], lb[dif]
            np.minimum.at(lab, np.maximum(la, lb), np.minimum(la, lb))
            while True:                              # compresión de caminos
                nl = lab[lab]
                if np.array_equal(nl, lab):
                    break
                lab = nl
    _, inv = np.unique(lab, return_inverse=True)
    etq = (inv + 1).astype(np.int32)
    n = int(etq.max())
    plano_ = np.zeros(nfil * ni + 1, np.int32)
    plano_[fila * ni + ini] += etq
    plano_[fila * ni + fin] -= etq
    out = np.cumsum(plano_[:-1], dtype=np.int32)
    return out.reshape(forma), n


def mayor_componente(m):
    lab, n = etiquetar(m)
    if n == 0:
        return np.zeros_like(m, bool)
    tam = np.bincount(lab.ravel())
    tam[0] = 0
    return lab == int(tam.argmax())


def rellenar_por_corte(m):
    """Rellena los huecos de cada corte (eje 0): lo que no toca el borde del corte pasa a ser
    parte de la máscara. En 2D rellena la imagen."""
    m = np.asarray(m, bool)
    m3 = m if m.ndim == 3 else m[None]
    lab, n = etiquetar(~m3, plano=True)
    if n == 0:
        return m.copy()
    borde = np.concatenate([lab[:, 0, :].ravel(), lab[:, -1, :].ravel(),
                            lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])
    fondo = np.zeros(n + 1, bool)
    fondo[np.unique(borde)] = True
    fondo[0] = False
    out = ~fondo[lab]
    return out if m.ndim == 3 else out[0]


# ------------------------------------------------------------------ crecer desde semillas
def ajustar_semilla(e, s, caja=(4, 6, 6)):
    """Si la semilla no cae en la máscara, busca el vóxel válido más cercano dentro de una caja
    (en índices). Devuelve (semilla, distancia en índices) o (None, None)."""
    s = tuple(int(round(v)) for v in s)
    if all(0 <= v < n for v, n in zip(s, e.shape)) and e[s]:
        return s, 0.0
    lo = [max(v - c, 0) for v, c in zip(s, caja)]
    hi = [min(max(v + c + 1, 0), n) for v, c, n in zip(s, caja, e.shape)]
    sub = e[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    idx = np.argwhere(sub)
    if len(idx) == 0:
        return None, None
    rel = np.array(s) - np.array(lo)
    d2 = ((idx - rel) ** 2).sum(1)
    c = idx[int(np.argmin(d2))]
    return tuple(int(a + b) for a, b in zip(c, lo)), float(np.sqrt(d2.min()))


def crecer(mascara, semillas, erosion=0, max_iter=None, caja=(4, 6, 6)):
    """Región conexa (vecindad 6) de `mascara` que contiene las semillas.

    1. Erosiona la máscara `erosion` veces (corta puentes finos hacia órganos vecinos).
    2. Toma las componentes de la máscara erosionada que contienen alguna semilla; una semilla
       que no cae en ella se mueve al vóxel válido más cercano (caja de búsqueda `caja`).
       Con max_iter, en vez de la componente completa crece como máximo max_iter pasos.
    3. Devuelve lo erosionado dilatando `erosion` veces dentro de la máscara original.
    Devuelve (región, notas)."""
    mascara = np.asarray(mascara, bool)
    e = erosionar(mascara, erosion)
    notas, validas = [], []
    for n_s, s in enumerate(semillas, 1):
        v, dist = ajustar_semilla(e, s, caja)
        if v is None:
            notas.append(f"semilla {n_s} {list(map(int, s))} sin vóxel válido cerca: se ignora")
        else:
            if dist:
                notas.append(f"semilla {n_s} {list(map(int, s))} fuera de la máscara: se usó {list(v)} "
                             f"(a {dist:.1f} vóxeles reducidos)")
            validas.append(v)
    if not validas:
        raise RuntimeError("ninguna semilla cae en la máscara (revise semillas y rango con "
                           "cortes_qa muestrear); " + "; ".join(notas))
    if max_iter is None:
        lab, _ = etiquetar(e)
        ids = np.unique([lab[v] for v in validas])
        sel = np.zeros(int(lab.max()) + 1, bool)
        sel[ids] = True
        sel[0] = False
        reg = sel[lab]
    else:
        reg = np.zeros_like(e)
        for v in validas:
            reg[v] = True
        n0 = -1
        for _ in range(int(max_iter)):
            reg = dilatar(reg, e)
            n = int(reg.sum())
            if n == n0:
                break
            n0 = n
    reg = dilatar(reg, mascara, erosion)
    return reg, notas
