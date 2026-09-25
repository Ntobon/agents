"""Series de un estudio DICOM: listarlas y convertir una en volumen numpy.

  python dicom_series.py listar <carpeta|zip> [--salida DIR] [--uids]
  python dicom_series.py cargar <carpeta|zip> --serie <N|#índice|UID> --salida DIR
                                [--recorte k0:k1] [--uniformizar]

Entrada: una carpeta (se recorre completa, con o sin DICOMDIR) o el .zip que exporta el portal.
`listar` lee solo encabezados y escribe series.json; `cargar` escribe volumen.npy [k, j, i]
(int16 en HU para TAC, float32 para lo demás) y volumen.json (ver coords.py).

Privacidad: ningún archivo de salida guarda nombre, documento, fecha de nacimiento, número de
acceso, fechas, UIDs ni institución. La hora de adquisición sí (sirve para ordenar las fases).
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import zipfile
from collections import Counter

import numpy as np
import pydicom
from pydicom.errors import InvalidDicomError

EXT_NO_DICOM = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".pdf", ".txt", ".htm", ".html", ".xml",
                ".js", ".css", ".exe", ".dll", ".inf", ".ini", ".ico", ".json", ".md", ".csv",
                ".zip", ".cab", ".msi", ".bat", ".cmd", ".sys", ".db", ".lnk", ".url", ".plist"}
TOL_POS = 1e-3          # mm: dos cortes a menos de esto ocupan la misma posición


# ------------------------------------------------------------------ utilidades
def _consola():
    """Salida en UTF-8 cuando va a un tubo (Git Bash, PowerShell); la consola real ya es Unicode."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace", **({} if s.isatty() else {"encoding": "utf-8"}))
        except Exception:
            pass


def _txt(v):
    return "" if v is None else str(v).strip()


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ent(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _lista(v):
    try:
        return [float(x) for x in v]
    except (TypeError, ValueError):
        return None


def _hora(t):
    """'082727.5343' -> ('08:27:27', segundos)."""
    m = re.match(r"^(\d{2})(\d{2})?(\d{2})?", t or "")
    if not m:
        return "", None
    h, mi, s = int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)
    return f"{h:02d}:{mi:02d}:{s:02d}", h * 3600 + mi * 60 + s


def _plano(texto):
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return t.lower()


def _buscar(ds, clave):
    """Atributo del nivel superior o, en multiframe, del primer ítem de los grupos funcionales."""
    if clave in ds:
        return ds.get(clave)
    for grupo in ("SharedFunctionalGroupsSequence", "PerFrameFunctionalGroupsSequence"):
        seq = ds.get(grupo)
        if not seq:
            continue
        for elem in seq[0]:
            if elem.VR == "SQ" and elem.value and clave in elem.value[0]:
                return elem.value[0].get(clave)
    return None


def _en_item(item, macro, clave):
    """Valor de `clave` dentro de la macro `macro` de un ítem de grupo funcional."""
    seq = item.get(macro) if item is not None else None
    if seq and clave in seq[0]:
        return seq[0].get(clave)
    return None


# ------------------------------------------------------------------ entrada (carpeta o zip)
class Entrada:
    def __init__(self, ruta):
        self.ruta = ruta
        self.zip = None
        if os.path.isdir(ruta):
            self.nombres = []
            for raiz, _, archivos in os.walk(ruta):
                for a in sorted(archivos):
                    if os.path.splitext(a)[1].lower() in EXT_NO_DICOM or a.upper() == "DICOMDIR":
                        continue
                    self.nombres.append(os.path.join(raiz, a))
        elif zipfile.is_zipfile(ruta):
            self.zip = zipfile.ZipFile(ruta)
            self.nombres = [n for n in self.zip.namelist()
                            if not n.endswith("/")
                            and os.path.splitext(n)[1].lower() not in EXT_NO_DICOM
                            and os.path.basename(n).upper() != "DICOMDIR"]
        elif os.path.isfile(ruta):
            self.nombres = [ruta]
        else:
            raise SystemExit(f"No existe la entrada: {ruta}")

    def leer(self, nombre, pixeles=False):
        f = self.zip.open(nombre) if self.zip else open(nombre, "rb")
        with f:
            try:
                return pydicom.dcmread(f, stop_before_pixels=not pixeles)
            except InvalidDicomError:
                try:
                    f.seek(0)
                    ds = pydicom.dcmread(f, stop_before_pixels=not pixeles, force=True)
                except Exception:
                    return None
                return ds if ("SOPClassUID" in ds or "Rows" in ds) else None
            except Exception:
                return None


# ------------------------------------------------------------------ encabezados
def _registro(ds, nombre):
    tipo = [str(x) for x in (ds.get("ImageType") or [])]
    r = dict(
        archivo=nombre,
        uid=_txt(ds.get("SeriesInstanceUID")) or f"sin-uid-{_txt(ds.get('SeriesNumber'))}-{_txt(ds.get('Modality'))}",
        sop_inst=_txt(ds.get("SOPInstanceUID")) or nombre,
        numero=_ent(ds.get("SeriesNumber")),
        modalidad=_txt(ds.get("Modality")),
        descripcion=_txt(ds.get("SeriesDescription")),
        protocolo=_txt(ds.get("ProtocolName")),
        tipo=tipo,
        filas=_ent(ds.get("Rows")), columnas=_ent(ds.get("Columns")),
        muestras=_ent(ds.get("SamplesPerPixel")) or 1,
        pixel=_lista(_buscar(ds, "PixelSpacing")),
        espesor=_num(_buscar(ds, "SliceThickness")),
        paso_encabezado=_num(_buscar(ds, "SpacingBetweenSlices")),
        iop=_lista(_buscar(ds, "ImageOrientationPatient")),
        ipp=_lista(ds.get("ImagePositionPatient")),
        instancia=_ent(ds.get("InstanceNumber")) or 0,
        hora=_txt(ds.get("AcquisitionTime") or ds.get("ContentTime") or ds.get("SeriesTime")),
        agente=_txt(ds.get("ContrastBolusAgent")), via=_txt(ds.get("ContrastBolusRoute")),
        kvp=_num(ds.get("KVP")), kernel=_txt(ds.get("ConvolutionKernel")),
        inclinacion=_num(ds.get("GantryDetectorTilt")),
        adquisicion=_ent(ds.get("AcquisitionNumber")), eco=_ent(ds.get("EchoNumbers")),
        tiempo=_ent(ds.get("TemporalPositionIdentifier")),
        parte=_txt(ds.get("BodyPartExamined")), posicion=_txt(ds.get("PatientPosition")),
        frames=_ent(ds.get("NumberOfFrames")) or 1,
        pendiente=_num(_buscar(ds, "RescaleSlope")) or 1.0,
        intercepto=_num(_buscar(ds, "RescaleIntercept")) or 0.0,
        # resonancia
        secuencia=_txt(_buscar(ds, "ScanningSequence") or _buscar(ds, "EchoPulseSequence")),
        variante=_txt(_buscar(ds, "SequenceVariant")),
        nombre_sec=_txt(_buscar(ds, "SequenceName") or _buscar(ds, "PulseSequenceName")),
        TE=_num(_buscar(ds, "EchoTime") or _buscar(ds, "EffectiveEchoTime")),
        TR=_num(_buscar(ds, "RepetitionTime")),
        TI=_num(_buscar(ds, "InversionTime") or (_lista(_buscar(ds, "InversionTimes")) or [None])[0]),
        campo=_num(_buscar(ds, "MagneticFieldStrength")),
        angulo=_num(_buscar(ds, "FlipAngle")),
        b=_num(_buscar(ds, "DiffusionBValue")),
    )
    pf = ds.get("PerFrameFunctionalGroupsSequence")
    if r["frames"] > 1 and pf:
        sh = ds.get("SharedFunctionalGroupsSequence")
        sh = sh[0] if sh else None
        pos, ori, pen, inter = [], [], [], []
        for it in pf:
            pos.append(_lista(_en_item(it, "PlanePositionSequence", "ImagePositionPatient")))
            ori.append(_lista(_en_item(it, "PlaneOrientationSequence", "ImageOrientationPatient")
                              or _en_item(sh, "PlaneOrientationSequence", "ImageOrientationPatient")))
            pen.append(_num(_en_item(it, "PixelValueTransformationSequence", "RescaleSlope")
                            or _en_item(sh, "PixelValueTransformationSequence", "RescaleSlope")) or 1.0)
            inter.append(_num(_en_item(it, "PixelValueTransformationSequence", "RescaleIntercept")
                              or _en_item(sh, "PixelValueTransformationSequence", "RescaleIntercept")) or 0.0)
        r.update(ipp_frames=pos, iop_frames=ori, pend_frames=pen, inter_frames=inter)
    return r


def leer_encabezados(ent):
    regs, vistos, fallidos = [], set(), 0
    for n, nombre in enumerate(ent.nombres, 1):
        ds = ent.leer(nombre)
        if ds is None:
            fallidos += 1
            continue
        if _txt(ds.get("SOPClassUID")) == "1.2.840.10008.1.3.10":      # DICOMDIR
            continue
        r = _registro(ds, nombre)
        if r["sop_inst"] in vistos:
            continue
        vistos.add(r["sop_inst"])
        regs.append(r)
        if n % 1000 == 0:
            print(f"  ... {n} archivos leídos", file=sys.stderr)
    return regs, fallidos


def _frames(regs):
    """Una entrada por corte (expande los multiframe)."""
    out = []
    for r in regs:
        if r.get("ipp_frames"):
            for f in range(r["frames"]):
                out.append(dict(archivo=r["archivo"], frame=f, ipp=r["ipp_frames"][f],
                                iop=r["iop_frames"][f] or r["iop"], pendiente=r["pend_frames"][f],
                                intercepto=r["inter_frames"][f], instancia=r["instancia"] * 100000 + f,
                                eco=r["eco"], tiempo=r["tiempo"], adquisicion=r["adquisicion"],
                                tipo="/".join(r["tipo"])))
        else:
            for f in range(r["frames"]):
                out.append(dict(archivo=r["archivo"], frame=(f if r["frames"] > 1 else None), ipp=r["ipp"],
                                iop=r["iop"], pendiente=r["pendiente"], intercepto=r["intercepto"],
                                instancia=r["instancia"], eco=r["eco"], tiempo=r["tiempo"],
                                adquisicion=r["adquisicion"], tipo="/".join(r["tipo"])))
    return out


# ------------------------------------------------------------------ geometría
def _normal(iop):
    fila, col = np.asarray(iop[:3], float), np.asarray(iop[3:], float)
    n = np.cross(fila, col)
    return n / (np.linalg.norm(n) or 1.0)


def orientacion(iop):
    if not iop:
        return "-"
    n = _normal(iop)
    ax = int(np.argmax(np.abs(n)))
    nombre = ("sagital", "coronal", "axial")[ax]
    return nombre if abs(n[ax]) >= 0.97 else f"oblicuo(~{nombre})"


def _geometria(frames):
    """Orientación dominante, posiciones sobre la normal y resumen del espaciado."""
    con = [f for f in frames if f["ipp"] and f["iop"]]
    if not con:
        return None
    cuenta = Counter(tuple(round(x, 3) for x in f["iop"]) for f in con)
    iop_c = cuenta.most_common(1)[0][0]
    grupo = [f for f in con if tuple(round(x, 3) for x in f["iop"]) == iop_c]
    iop = grupo[0]["iop"]
    n = _normal(iop)
    pos = np.array([np.dot(f["ipp"], n) for f in grupo])
    ps = np.sort(pos)
    difs = np.diff(ps)
    reales = difs[difs > TOL_POS]
    paso = float(np.median(reales)) if len(reales) else None
    dup = int((difs <= TOL_POS).sum())
    huecos = int((reales > 1.5 * paso).sum()) if paso else 0
    irregular = bool(paso and len(reales) and np.abs(reales - paso).max() > max(0.01 * paso, 0.02))
    if len(ps) < 2:
        unif = "-"
    elif dup:
        unif = f"{dup} posiciones repetidas"
    elif huecos:
        unif = f"irregular ({huecos} huecos)"
    elif irregular:
        unif = "irregular"
    else:
        unif = "uniforme"
    return dict(iop=iop, normal=n, grupo=grupo, pos=pos, paso=paso, cobertura=float(ps[-1] - ps[0]),
                uniformidad=unif, orientaciones=len(cuenta), duplicados=dup, huecos=huecos)


# ------------------------------------------------------------------ pistas de fase / secuencia
_PISTAS = [
    (r"arter", "arterial"),
    (r"portal|venos|venous|\bpv\b", "portal/venosa"),
    (r"tard|delay|late|equilib|excret|urogr|nefrogr", "tardía/excretora"),
    (r"simple|sin contr|sin c\b|s/c|non.?con|sin medio|\bnc\b|plain|nativ|basal|\bpre\b", "sin contraste"),
    (r"contrast|\bc\+|con c\b|\biv\b|\bpost\b|gado|\bgd\b", "con contraste"),
]


def pistas_fase(texto):
    t = _plano(texto)
    return [et for pat, et in _PISTAS if re.search(pat, t)]


def ponderacion(s):
    """Pista (no diagnóstico) de la ponderación de una serie de RM."""
    t = _plano(s["descripcion"] + " " + s["protocolo"] + " " + s["nombre_sec"])
    tipo = "/".join(s["tipo"]).upper()
    if "DIFF" in tipo or "ADC" in tipo or re.search(r"dwi|diff|\badc\b|trace", t) or s["b"]:
        return "difusión"
    for pat, et in ((r"flair", "FLAIR"), (r"stir", "STIR"), (r"mrcp|colangio", "T2 intensa (colangio)"),
                    (r"vibe|lava|thrive|\bt1\b|t1w|t1_", "T1"), (r"haste|ssfse|\bt2\b|t2w|t2_", "T2")):
        if re.search(pat, t):
            return et
    TE, TR, TI = s["TE"], s["TR"], s["TI"]
    if TI and TI > 1500:
        return "FLAIR"
    if TI and 100 <= TI <= 250:
        return "STIR"
    if TR and TE:
        if TR < 1000 and TE < 30:
            return "T1"
        if TR >= 1500 and TE >= 60:
            return "T2"
        if TR >= 1500 and TE < 40:
            return "densidad protónica"
    return "?"


# ------------------------------------------------------------------ series
def agrupar(regs):
    por_uid = {}
    for r in regs:
        por_uid.setdefault(r["uid"], []).append(r)
    series = []
    for uid, rs in por_uid.items():
        rs.sort(key=lambda r: r["instancia"])
        r0 = rs[0]
        fr = _frames(rs)
        g = _geometria(fr)
        horas = sorted(h for h in (_hora(r["hora"])[1] for r in rs) if h is not None)
        tipo = r0["tipo"]
        s = dict(uid=uid, regs=rs, numero=r0["numero"], modalidad=r0["modalidad"],
                 descripcion=r0["descripcion"], protocolo=r0["protocolo"], tipo=tipo,
                 n=len(fr), filas=r0["filas"], columnas=r0["columnas"], muestras=r0["muestras"],
                 pixel=r0["pixel"], espesor=r0["espesor"], paso_encabezado=r0["paso_encabezado"],
                 orientacion=orientacion(g["iop"]) if g else "-",
                 paso=g["paso"] if g else None, cobertura=g["cobertura"] if g else None,
                 uniformidad=g["uniformidad"] if g else "-",
                 hora_s=horas[0] if horas else None,
                 hora=_hora(min((r["hora"] for r in rs if r["hora"]), default=""))[0],
                 agente=r0["agente"], via=r0["via"], kvp=r0["kvp"], kernel=r0["kernel"],
                 inclinacion=r0["inclinacion"], parte=r0["parte"], posicion=r0["posicion"],
                 multiframe=r0["frames"] > 1,
                 secuencia=r0["secuencia"], variante=r0["variante"], nombre_sec=r0["nombre_sec"],
                 TE=r0["TE"], TR=r0["TR"], TI=r0["TI"], campo=r0["campo"], angulo=r0["angulo"], b=r0["b"])
        s["localizador"] = ("LOCALIZER" in [x.upper() for x in tipo]) or s["n"] < 3
        s["pistas"] = pistas_fase(s["descripcion"])
        s["pistas_protocolo"] = pistas_fase(s["protocolo"])
        series.append(s)
    series.sort(key=lambda s: (s["numero"] if s["numero"] is not None else 10 ** 9, s["hora_s"] or 0, s["uid"]))
    imagen = [s for s in series if s["hora_s"] is not None and not s["localizador"]]
    rango = {id(s): r for r, s in enumerate(sorted(imagen, key=lambda s: s["hora_s"]), 1)}
    for i, s in enumerate(series, 1):
        s["indice"] = i
        s["orden_adq"] = (rango[id(s)], len(rango)) if id(s) in rango else None
    return series


def _contraste(s):
    if s["agente"]:
        return f"agente: {s['agente']}" + (f" ({s['via']})" if s["via"] else "")
    if s["pistas"]:
        return "descripción: " + ", ".join(s["pistas"])
    if s["pistas_protocolo"]:
        return "protocolo: " + ", ".join(s["pistas_protocolo"])
    return "no consta"


def _es_contraste(s):
    return bool(s["agente"]) or any(p != "sin contraste" for p in s["pistas"])


def sugerir(series):
    cand = [s for s in series if s["orientacion"] == "axial" and s["n"] >= 20 and not s["localizador"]
            and s["paso"] and s["muestras"] == 1]
    if not cand:
        return []

    def clave(s):
        original = "ORIGINAL" in [x.upper() for x in s["tipo"]]
        contraste = _es_contraste(s) if s["modalidad"] == "CT" else True
        return (not original, not contraste, round(s["paso"] / 0.25), -(s["cobertura"] or 0))
    return sorted(cand, key=clave)


def resumen_json(s):
    """Lo que va a series.json: sin UIDs, fechas ni datos del paciente."""
    d = dict(indice=s["indice"], numero=s["numero"], modalidad=s["modalidad"], descripcion=s["descripcion"],
             protocolo=s["protocolo"], tipo_imagen="/".join(s["tipo"]), imagenes=s["n"],
             matriz=[s["filas"], s["columnas"]], pixel_mm=s["pixel"], espesor_mm=s["espesor"],
             paso_mm=s["paso"], cobertura_mm=s["cobertura"], uniformidad=s["uniformidad"],
             orientacion=s["orientacion"], localizador=s["localizador"], multiframe=s["multiframe"],
             color=s["muestras"] > 1, hora_adquisicion=s["hora"],
             orden_adquisicion=list(s["orden_adq"]) if s["orden_adq"] else None,
             contraste=_contraste(s), pistas_fase=s["pistas"], kvp=s["kvp"], kernel=s["kernel"],
             parte_cuerpo=s["parte"], posicion_paciente=s["posicion"])
    if s["modalidad"] == "MR":
        d["mr"] = dict(secuencia=s["secuencia"], variante=s["variante"], nombre_secuencia=s["nombre_sec"],
                       TE=s["TE"], TR=s["TR"], TI=s["TI"], campo_T=s["campo"], angulo=s["angulo"],
                       b=s["b"], ponderacion_probable=ponderacion(s))
    return d


def _f(v, fmt="{:.2f}", nada="-"):
    return nada if v is None else fmt.format(v)


def listar(args):
    ent = Entrada(args.entrada)
    regs, fallidos = leer_encabezados(ent)
    if not regs:
        raise SystemExit("No se encontraron archivos DICOM en la entrada.")
    series = agrupar(regs)
    print(f"{len(ent.nombres)} archivos, {len(regs)} imágenes DICOM, {len(series)} series"
          + (f" ({fallidos} archivos no DICOM ignorados)" if fallidos else ""))
    cab = (f"{'#':>3} {'Serie':>5} {'Mod':<4}{'Descripción':<28}{'Tipo':<11}{'Imgs':>6} {'Matriz':<9}"
           f"{'Píxel mm':<10}{'Esp.mm':>7}{'Paso mm':>8}{'Cobert.':>9}  {'Orient.':<16}{'Uniformidad'}")
    print(cab)
    print("-" * len(cab))
    for s in series:
        tipo = "/".join(x[:4] for x in s["tipo"][:2]) or "-"
        if s["localizador"]:
            tipo = "LOCALIZ"
        px = f"{s['pixel'][0]:.2f}x{s['pixel'][1]:.2f}" if s["pixel"] else "-"
        print(f"{s['indice']:>3} {_f(s['numero'], '{}'):>5} {s['modalidad']:<4}{s['descripcion'][:27]:<28}"
              f"{tipo[:10]:<11}{s['n']:>6} {str(s['filas']) + 'x' + str(s['columnas']):<9}{px:<10}"
              f"{_f(s['espesor']):>7}{_f(s['paso'], '{:.3f}'):>8}{_f(s['cobertura'], '{:.0f} mm'):>9}  "
              f"{s['orientacion']:<16}{s['uniformidad']}")
        det = [f"contraste/fase: {_contraste(s)}"]
        if s["orden_adq"]:
            det.append(f"adquisición {s['orden_adq'][0]} de {s['orden_adq'][1]} ({s['hora']})")
        if s["modalidad"] == "CT":
            det += [f"kVp {_f(s['kvp'], '{:.0f}')}", f"kernel {s['kernel'] or '-'}"]
            if s["inclinacion"]:
                det.append(f"gantry inclinado {s['inclinacion']:.1f}°")
        if s["muestras"] > 1:
            det.append("imagen en color (captura, no volumen)")
        if s["multiframe"]:
            det.append("multiframe (enhanced)")
        print("      " + "; ".join(det))
        if s["modalidad"] == "MR":
            print(f"      RM: secuencia {s['secuencia'] or '-'} {s['variante'] or ''} ({s['nombre_sec'] or '-'}), "
                  f"TE {_f(s['TE'], '{:.0f}')} ms, TR {_f(s['TR'], '{:.0f}')} ms, TI {_f(s['TI'], '{:.0f}')} ms, "
                  f"{_f(s['campo'], '{:.1f}')} T -> ponderación probable: {ponderacion(s)}")
        if args.uids:
            print(f"      UID: {s['uid']}")
    cand = sugerir(series)
    print()
    if cand:
        c = cand[0]
        print(f"Sugerencia: serie {c['numero']} (#{c['indice']}): axial, paso {c['paso']:.3f} mm, cobertura "
              f"{c['cobertura']:.0f} mm, {c['n']} cortes, contraste: {_contraste(c)}.")
        if len(cand) > 1:
            print("  Alternativas: " + "; ".join(f"serie {s['numero']} (#{s['indice']}, paso {s['paso']:.3f} mm, "
                                                 f"{s['cobertura']:.0f} mm)" for s in cand[1:3]))
        print("  Regla: la axial más delgada y de mayor cobertura, con contraste. La fase se confirma mirando "
              "(aorta y porta con cortes_qa.py muestrear).")
    else:
        print("Sugerencia: no hay una serie axial apta para 3D (>= 20 cortes, con posiciones).")
    os.makedirs(args.salida, exist_ok=True)
    ruta = os.path.join(args.salida, "series.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(dict(series=[resumen_json(s) for s in series],
                       sugerida=cand[0]["indice"] if cand else None), f, ensure_ascii=False, indent=1)
    print(f"Escrito {ruta}")


# ------------------------------------------------------------------ cargar
def elegir(series, sel):
    sel = str(sel).strip()
    if sel.startswith("#"):
        i = int(sel[1:])
        m = [s for s in series if s["indice"] == i]
    elif "." in sel and len(sel) > 10:
        m = [s for s in series if s["uid"] == sel]
    else:
        m = [s for s in series if s["numero"] is not None and str(s["numero"]) == sel]
        if not m and sel.isdigit():
            m = [s for s in series if s["indice"] == int(sel)]
            if m:
                print(f"Aviso: no hay serie número {sel}; se usa el índice #{sel}.")
    if not m:
        raise SystemExit(f"No se encontró la serie '{sel}'. Use el número de serie, '#índice' o el UID "
                         "(listar --uids).")
    if len(m) > 1:
        raise SystemExit(f"Hay {len(m)} series con número {sel} (índices "
                         + ", ".join("#" + str(s["indice"]) for s in m) + "): use '#índice'.")
    return m[0]


def _separar_pilas(frames, pos, adv):
    """Si hay posiciones repetidas, separa por eco / tiempo / adquisición / tipo y usa el grupo mayor."""
    def repetidas(idx):
        p = np.sort(pos[idx])
        return bool((np.diff(p) <= TOL_POS).any())
    todos = np.arange(len(frames))
    if not repetidas(todos):
        return todos
    for claves in (("eco",), ("tiempo",), ("adquisicion",), ("eco", "tiempo"), ("tipo",)):
        grupos = {}
        for i, f in enumerate(frames):
            grupos.setdefault(tuple(f[c] for c in claves), []).append(i)
        if len(grupos) > 1 and not any(repetidas(np.array(g)) for g in grupos.values()):
            clave, idx = max(grupos.items(), key=lambda kv: len(kv[1]))
            adv.append(f"La serie mezcla {len(grupos)} pilas por {'+'.join(claves)} (tamaños "
                       f"{sorted(len(g) for g in grupos.values())}); se usó {'+'.join(claves)}={clave} "
                       f"({len(idx)} cortes).")
            return np.array(idx)
    orden = sorted(todos, key=lambda i: frames[i]["instancia"])
    vistos, idx = [], []
    for i in orden:
        if not any(abs(pos[i] - p) <= TOL_POS for p in vistos):
            vistos.append(pos[i])
            idx.append(i)
    adv.append(f"Posiciones repetidas sin criterio para separarlas: se conservó el primer corte (por número "
               f"de instancia) de cada posición ({len(idx)} de {len(frames)}).")
    return np.array(idx)


class LectorCortes:
    """Devuelve cada corte ya reescalado; decodifica cada archivo una sola vez (multiframe)."""

    def __init__(self, ent):
        self.ent, self.nombre, self.arr = ent, None, None

    def corte(self, f):
        if f["archivo"] != self.nombre:
            ds = self.ent.leer(f["archivo"], pixeles=True)
            if ds is None:
                raise SystemExit(f"No se pudo leer {f['archivo']}")
            try:
                self.arr = ds.pixel_array
            except Exception as e:
                raise SystemExit(f"No se pudieron decodificar los píxeles ({e}). Si la sintaxis es JPEG/JPEG2000, "
                                 "instale un decodificador local: pip install pylibjpeg pylibjpeg-libjpeg "
                                 "pylibjpeg-openjpeg (o python-gdcm).")
            self.nombre = f["archivo"]
        a = self.arr[f["frame"]] if f["frame"] is not None else self.arr
        if a.ndim != 2:
            raise SystemExit("La serie tiene imágenes en color o de más de 2 dimensiones: no es un volumen.")
        return a.astype(np.float64) * f["pendiente"] + f["intercepto"]


def cargar(args):
    ent = Entrada(args.entrada)
    regs, _ = leer_encabezados(ent)
    series = agrupar(regs)
    s = elegir(series, args.serie)
    adv = []
    frames = _frames(s["regs"])
    g = _geometria(frames)
    if g is None:
        raise SystemExit("La serie no tiene posiciones ni orientación (ImagePositionPatient): no es un volumen.")
    if g["orientaciones"] > 1:
        adv.append(f"La serie mezcla {g['orientaciones']} orientaciones; se usó la más frecuente "
                   f"({len(g['grupo'])} de {len(frames)} cortes).")
    frames, iop, normal = g["grupo"], g["iop"], g["normal"]
    fila, col = np.asarray(iop[:3]), np.asarray(iop[3:])
    if abs(np.dot(fila, col)) > 1e-3 or abs(np.linalg.norm(fila) - 1) > 1e-3 or abs(np.linalg.norm(col) - 1) > 1e-3:
        adv.append("Los cosenos de orientación no son ortonormales: las coordenadas en mm son aproximadas.")
    pos = np.array([np.dot(f["ipp"], normal) for f in frames])
    idx = _separar_pilas(frames, pos, adv)
    frames = [frames[i] for i in idx]
    pos = pos[idx]
    orden = sorted(range(len(frames)), key=lambda i: (pos[i], frames[i]["instancia"]))
    frames = [frames[i] for i in orden]
    pos = pos[orden]
    n = len(frames)
    if n < 2:
        raise SystemExit("La serie tiene menos de 2 cortes: no es un volumen.")
    difs = np.diff(pos)
    dz = float(np.median(difs))
    if difs.max() > 1.5 * dz or np.abs(difs - dz).max() > max(0.01 * dz, 0.02):
        adv.append(f"Espaciado irregular: pasos entre {difs.min():.3f} y {difs.max():.3f} mm (mediana {dz:.3f}); "
                   f"{int((difs > 1.5 * dz).sum())} huecos > 1.5x la mediana."
                   + (" Se remuestreó a paso uniforme (--uniformizar)." if args.uniformizar else
                      " Las coordenadas en mm fallan más allá de un hueco: use --uniformizar o elija otra serie."))
    desplaz = np.asarray(frames[-1]["ipp"]) - np.asarray(frames[0]["ipp"])
    if np.linalg.norm(desplaz) > 0:
        ang = np.degrees(np.arccos(min(1.0, abs(np.dot(desplaz, normal)) / np.linalg.norm(desplaz))))
        if ang > 0.5:
            adv.append(f"Los cortes no se apilan sobre su normal (desvío {ang:.1f}°, gantry inclinado o cizalla): "
                       "las coordenadas en mm tienen un corrimiento que crece hacia los extremos.")
    if s["inclinacion"]:
        adv.append(f"GantryDetectorTilt = {s['inclinacion']:.1f}° en el encabezado.")
    if s["paso_encabezado"] and abs(s["paso_encabezado"] - dz) > 0.01:
        adv.append(f"SpacingBetweenSlices del encabezado ({s['paso_encabezado']:.3f}) no coincide con el paso real "
                   f"entre posiciones ({dz:.3f}); se usa el real.")
    if s["espesor"] and s["espesor"] > dz * 1.01:
        adv.append(f"Cortes solapados: espesor nominal {s['espesor']:.3f} mm > paso {dz:.3f} mm (normal en "
                   "reconstrucciones finas; el paso es lo que cuenta para la geometría).")

    # lista final de cortes: los originales o posiciones uniformes interpoladas
    if args.uniformizar:
        m = int(np.floor((pos[-1] - pos[0]) / dz + 1e-6)) + 1
        destino = pos[0] + dz * np.arange(m)
        a_idx = np.clip(np.searchsorted(pos, destino, side="right") - 1, 0, n - 1)
        b_idx = np.minimum(a_idx + 1, n - 1)
        w = np.where(b_idx > a_idx, (destino - pos[a_idx]) / np.maximum(pos[b_idx] - pos[a_idx], 1e-9), 0.0)
        plan = list(zip(a_idx, b_idx, np.clip(w, 0, 1)))
    else:
        destino = pos
        plan = [(i, i, 0.0) for i in range(n)]
    ntot = len(plan)
    k0, k1 = 0, ntot
    if args.recorte:
        a, b = args.recorte.split(":")
        k0 = int(a) if a else 0
        k1 = int(b) if b else ntot
        if not (0 <= k0 < k1 <= ntot):
            raise SystemExit(f"--recorte fuera de rango: la serie tiene {ntot} cortes (0:{ntot}).")
    plan = plan[k0:k1]
    if args.uniformizar:
        origen = np.asarray(frames[0]["ipp"], float) + (destino[k0] - pos[0]) * normal
    else:
        origen = np.asarray(frames[k0]["ipp"], float)      # IPP del primer corte guardado

    mod = s["modalidad"] or "OT"
    es_ct = mod == "CT"
    dtype = np.int16 if es_ct else np.float32
    filas, cols = s["filas"], s["columnas"]
    os.makedirs(args.salida, exist_ok=True)
    ruta_npy = os.path.join(args.salida, "volumen.npy")
    vol = np.lib.format.open_memmap(ruta_npy, mode="w+", dtype=dtype, shape=(len(plan), filas, cols))
    lector = LectorCortes(ent)
    cache = {}
    recortados = 0
    for kk, (a, b, w) in enumerate(plan):
        for i in (a, b):
            if i not in cache:
                cache[i] = lector.corte(frames[i])
        for i in [i for i in cache if i < a]:
            del cache[i]
        sl = cache[a] if w == 0 else (1 - w) * cache[a] + w * cache[b]
        if sl.shape != (filas, cols):
            raise SystemExit(f"Corte con matriz distinta ({sl.shape}) dentro de la serie.")
        if es_ct:
            sl = np.rint(sl)
            fuera = (sl < -32768) | (sl > 32767)
            recortados += int(fuera.sum())
            sl = np.clip(sl, -32768, 32767)
        vol[kk] = sl.astype(dtype)
        if (kk + 1) % 200 == 0:
            print(f"  ... {kk + 1}/{len(plan)} cortes", file=sys.stderr)
    vol.flush()
    del vol
    if recortados:
        adv.append(f"{recortados} vóxeles fuera del rango int16 se recortaron.")
    v = np.load(ruta_npy, mmap_mode="r")
    muestra = np.asarray(v[::4, ::4, ::4], np.float64)
    p1, p50, p99 = (float(x) for x in np.percentile(muestra, [1, 50, 99]))
    dy, dx = (float(x) for x in (s["pixel"] or [1.0, 1.0]))
    if not s["pixel"]:
        adv.append("Sin PixelSpacing: se asumió 1 mm; las medidas no son confiables.")
    info = dict(
        modalidad=mod, unidades="HU" if es_ct else "intensidad",
        forma=[int(x) for x in v.shape], espaciado_mm=[dz, dy, dx],
        origen_mm=[float(x) for x in origen], cosenos=[float(x) for x in iop],
        normal=[float(x) for x in normal],
        serie=dict(numero=s["numero"], descripcion=s["descripcion"], protocolo=s["protocolo"],
                   tipo_imagen="/".join(s["tipo"]), kernel=s["kernel"], hora_adquisicion=s["hora"],
                   contraste=_contraste(s), espesor_mm=s["espesor"], kvp=s["kvp"]),
        percentiles=dict(p1=p1, p50=p50, p99=p99),
        advertencias=adv,
    )
    if mod == "MR":
        info["mr"] = dict(secuencia=s["secuencia"], variante=s["variante"], nombre_secuencia=s["nombre_sec"],
                          TE=s["TE"], TR=s["TR"], TI=s["TI"], campo_T=s["campo"], angulo=s["angulo"], b=s["b"],
                          ponderacion_probable=ponderacion(s))
    if args.recorte:
        info["recorte_cortes"] = dict(k0=k0, k1=k1, n_serie=ntot)
    with open(os.path.join(args.salida, "volumen.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    print(f"Serie {s['numero']} (#{s['indice']}) -> {ruta_npy}")
    print(f"  forma {list(v.shape)} {v.dtype}, espaciado [dz, dy, dx] = [{dz:.4f}, {dy:.4f}, {dx:.4f}] mm, "
          f"orientación {orientacion(iop)}")
    print(f"  percentiles p1/p50/p99 = {p1:.1f} / {p50:.1f} / {p99:.1f} {info['unidades']}")
    for a in adv:
        print("  Aviso: " + a)


def main():
    _consola()
    ap = argparse.ArgumentParser(description="Lista las series DICOM de una carpeta o .zip y convierte una en "
                                             "volumen numpy (volumen.npy + volumen.json).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("listar", help="tabla de series (solo encabezados) + series.json")
    a.add_argument("entrada", help="carpeta (recursiva, con o sin DICOMDIR) o .zip")
    a.add_argument("--salida", default=".", help="carpeta donde escribir series.json (por defecto, la actual)")
    a.add_argument("--uids", action="store_true", help="mostrar en pantalla el SeriesInstanceUID (no se guarda)")
    c = sub.add_parser("cargar", help="convierte una serie en volumen.npy + volumen.json")
    c.add_argument("entrada", help="carpeta o .zip")
    c.add_argument("--serie", required=True, help="número de serie, '#índice' de listar, o UID")
    c.add_argument("--salida", required=True, help="carpeta de trabajo (fuera de Drive: pesa cientos de MB)")
    c.add_argument("--recorte", help="k0:k1 sobre los cortes ya ordenados (k1 excluido), para ahorrar memoria")
    c.add_argument("--uniformizar", action="store_true",
                   help="si el espaciado es irregular, interpola a paso uniforme (la mediana)")
    args = ap.parse_args()
    (listar if args.cmd == "listar" else cargar)(args)


if __name__ == "__main__":
    main()
