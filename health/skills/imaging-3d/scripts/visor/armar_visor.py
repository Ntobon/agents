"""Arma el visor 3D de un solo archivo a partir de la plantilla genérica.

    python armar_visor.py --glb modelo.glb --config visor.json --salida "Visor 3D.html"
        [--pestanas pestanas.html] [--glosario glosario.html] [--video video.html]
        [--poster render.jpg] [--variante privada|compartir]
    python armar_visor.py --glb modelo.glb --listar      (nodos del GLB con su caja, para escribir la configuración)
    python armar_visor.py --glb modelo.glb --esqueleto visor.json [--estilo estilo.json]
        (configuración inicial con todos los nodos; con --estilo hereda la paleta de Blender)

Qué hace:
1. Lee y valida la configuración (JSON). Las claves que empiezan con «_» son documentación y no viajan.
2. Lee el bloque JSON del GLB: cada estructuras[].k debe existir como nodo con geometría; los nodos
   sin configurar se avisan. Los puntos [x,y,z] muy lejos del modelo se avisan (casi siempre es un error
   de convención: el visor usa glTF, +Y arriba, 1 unidad = 1 cm; ver scripts/coords.py).
3. Resuelve ruta.archivo (el ruta.json del trazado de la luz: puntos glTF + radios en mm), aplica el
   suavizado pedido y deja los radios en cm.
4. Arma las pestañas: Explorar (plantilla) + las <section class="panel" id="panel-x" data-titulo="…">
   del archivo de pestañas + Video + Glosario. Una sección id="panel-explorar" se suma debajo del 3D.
   Marcadores dentro de las pestañas: <!--__LEYENDA_COLORES__--> <!--__PUNTOS__--> <!--__VIDEO__-->.
5. --variante compartir (copia para un médico o un tercero): usa banner_compartir y los demás
   <campo>_compartir, cambia el prefijo de localStorage (+ "-compartir") y quita las pestañas de
   pestanas_privadas y todo elemento con el atributo data-privado.
6. Escribe UTF-8 con <meta charset> y viewport en las dos primeras líneas, de forma atómica. Avisa
   por encima de 12 MB y no escribe por encima de 16 MB.
"""
import argparse
import base64
import html
import json
import math
import os
import re
import struct
import sys
from html.parser import HTMLParser

AQUI = os.path.dirname(os.path.abspath(__file__))
MB = 1024 * 1024
RE_CLAVE = re.compile(r"[A-Za-z0-9_-]+")
RE_HEX = re.compile(r"#[0-9a-fA-F]{6}")
RE_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
MARCADORES = ["__TITULO_PAGINA__", "<!--__CABECERA__-->", "<!--__NAV__-->", "<!--__POSTER__-->",
              "<!--__EXPLORAR_EXTRA__-->", "<!--__SIN_JS__-->", "<!--__PANELES__-->", "<!--__PIE__-->",
              "/*__CONFIG_JSON__*/", "__GLB_B64__"]
PIE = "Informativo; no reemplaza a los médicos tratantes ni al informe del radiólogo."
BANNER_COMPARTIR = "Reconstrucción aproximada hecha a partir del estudio de imágenes; no es una lectura de radiólogo."
SUBTITULO = "Gire con un dedo, acerque con dos y toque los números."


class ErrorArmado(Exception):
    pass


def esc(t):
    return html.escape(str(t if t is not None else ""), quote=True)


def leer_texto(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return f.read().replace("\r\n", "\n")


def leer_json(ruta):
    try:
        return json.loads(leer_texto(ruta))
    except json.JSONDecodeError as e:
        raise ErrorArmado(f"JSON no válido en {ruta}: {e.msg} (línea {e.lineno}, columna {e.colno})")


def sin_doc(x):
    """Quita las claves de documentación («_doc», «_nota»…) en todos los niveles."""
    if isinstance(x, dict):
        return {k: sin_doc(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, list):
        return [sin_doc(v) for v in x]
    return x


# ---------------------------------------------------------------------------------------------
# GLB: nodos y cajas (desde el bloque JSON; los POSITION del glTF traen min/max obligatorios)
# ---------------------------------------------------------------------------------------------
def leer_glb(ruta):
    with open(ruta, "rb") as f:
        datos = f.read()
    if len(datos) < 20 or datos[:4] != b"glTF":
        raise ErrorArmado(f"{ruta} no es un GLB (falta la firma «glTF»)")
    version, largo = struct.unpack_from("<II", datos, 4)
    if version != 2:
        raise ErrorArmado(f"{ruta}: GLB versión {version}; el visor necesita glTF 2")
    clen, ctipo = struct.unpack_from("<II", datos, 12)
    if ctipo != 0x4E4F534A:
        raise ErrorArmado(f"{ruta}: el primer bloque del GLB no es JSON")
    return json.loads(datos[20:20 + clen].decode("utf-8")), datos


def _mat_nodo(n):
    if "matrix" in n:
        m = n["matrix"]   # column-major
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    tx, ty, tz = n.get("translation", [0, 0, 0])
    qx, qy, qz, qw = n.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = n.get("scale", [1, 1, 1])
    r = [[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
         [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
         [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]]
    return [[r[0][0] * sx, r[0][1] * sy, r[0][2] * sz, tx],
            [r[1][0] * sx, r[1][1] * sy, r[1][2] * sz, ty],
            [r[2][0] * sx, r[2][1] * sy, r[2][2] * sz, tz],
            [0, 0, 0, 1]]


def _mult(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def nodos_glb(g):
    """{nombre: {"malla": bool, "min": [..], "max": [..]}} en coordenadas del mundo glTF."""
    acc, mallas, nodos = g.get("accessors", []), g.get("meshes", []), g.get("nodes", [])
    info = {}

    def caja_malla(mi):
        mn, mx = [math.inf] * 3, [-math.inf] * 3
        for p in mallas[mi].get("primitives", []):
            a = p.get("attributes", {}).get("POSITION")
            if a is None or "min" not in acc[a]:
                continue
            for i in range(3):
                mn[i] = min(mn[i], acc[a]["min"][i])
                mx[i] = max(mx[i], acc[a]["max"][i])
        return (mn, mx) if mn[0] < math.inf else None

    def visitar(i, padre, ancestros):
        n = nodos[i]
        m = _mult(padre, _mat_nodo(n))
        nombre = n.get("name") or f"nodo_{i}"
        d = info.setdefault(nombre, {"malla": False, "min": [math.inf] * 3, "max": [-math.inf] * 3})
        if "mesh" in n:
            cm = caja_malla(n["mesh"])
            if cm:
                for x in (cm[0][0], cm[1][0]):
                    for y in (cm[0][1], cm[1][1]):
                        for z in (cm[0][2], cm[1][2]):
                            w = [m[r][0] * x + m[r][1] * y + m[r][2] * z + m[r][3] for r in range(3)]
                            for dd in [d] + [info[a] for a in ancestros]:
                                dd["malla"] = True
                                for k in range(3):
                                    dd["min"][k] = min(dd["min"][k], w[k])
                                    dd["max"][k] = max(dd["max"][k], w[k])
        for c in n.get("children", []):
            visitar(c, m, ancestros + [nombre])

    ident = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    escenas = g.get("scenes") or [{"nodes": list(range(len(nodos)))}]
    for r in escenas[g.get("scene", 0)].get("nodes", []):
        visitar(r, ident, [])
    return info


def caja_total(info):
    mn, mx = [math.inf] * 3, [-math.inf] * 3
    for d in info.values():
        if d["malla"]:
            for k in range(3):
                mn[k] = min(mn[k], d["min"][k])
                mx[k] = max(mx[k], d["max"][k])
    return (mn, mx) if mn[0] < math.inf else None


# ---------------------------------------------------------------------------------------------
# Ruta de la luz
# ---------------------------------------------------------------------------------------------
def _puntos_de_archivo(datos):
    pts = datos.get("puntos", datos.get("puntos_gltf"))
    rad = None
    if isinstance(pts, list) and pts and isinstance(pts[0], dict):
        filas = pts
        pts = [f.get("p") or f.get("gltf") or f.get("xyz") for f in filas]
        rmm = [f.get("r_mm", f.get("radio_mm")) for f in filas]
        if all(isinstance(x, (int, float)) for x in rmm):
            rad = [x / 10.0 for x in rmm]
    if rad is None and isinstance(datos.get("radios_mm"), list):
        rad = [x / 10.0 for x in datos["radios_mm"]]
    if rad is None and isinstance(datos.get("radios"), list):
        rad = list(datos["radios"])
    return pts, rad


def preparar_ruta(cfg, base):
    r = cfg.get("ruta")
    if not isinstance(r, dict):
        return
    if r.get("archivo"):
        ruta_arch = os.path.join(base, r["archivo"])
        if not os.path.exists(ruta_arch):
            raise ErrorArmado(f"ruta.archivo: no existe {ruta_arch}")
        datos = leer_json(ruta_arch)
        pts, rad = _puntos_de_archivo(datos)
        if "puntos" not in r:
            r["puntos"] = pts
        if "radios" not in r and "radios_mm" not in r and rad is not None:
            r["radios"] = rad
        for k, v in datos.items():   # p. ej. «estrechez» detectada por el trazado
            if k not in r and not k.startswith("_") and k not in ("puntos", "puntos_gltf", "radios", "radios_mm"):
                r[k] = v
        del r["archivo"]
    if isinstance(r.get("radios_mm"), list):
        r["radios"] = [x / 10.0 for x in r.pop("radios_mm")]
    pasadas = int(r.pop("suavizado", 0) or 0)
    for _ in range(max(0, pasadas)):
        for clave, dim in (("puntos", 3), ("radios", 1)):
            v = r.get(clave)
            if not isinstance(v, list) or len(v) < 3:
                continue
            if dim == 1:
                r[clave] = [v[0]] + [(v[i - 1] + 2 * v[i] + v[i + 1]) / 4 for i in range(1, len(v) - 1)] + [v[-1]]
            else:
                r[clave] = [v[0]] + [[(v[i - 1][j] + 2 * v[i][j] + v[i + 1][j]) / 4 for j in range(3)] for i in range(1, len(v) - 1)] + [v[-1]]
    if isinstance(r.get("puntos"), list):
        r["puntos"] = [[round(float(c), 4) for c in p] for p in r["puntos"] if isinstance(p, list) and len(p) == 3]
    if isinstance(r.get("radios"), list):
        r["radios"] = [round(float(x), 4) for x in r["radios"]]


# ---------------------------------------------------------------------------------------------
# Validación de la configuración
# ---------------------------------------------------------------------------------------------
class Revisor:
    def __init__(self, cfg, nodos):
        self.cfg, self.nodos = cfg, nodos
        self.errores, self.avisos = [], []
        self.claves = {}
        self.caja = caja_total(nodos)
        r = cfg.get("ruta") if isinstance(cfg.get("ruta"), dict) else {}
        self.n_ruta = len(r.get("puntos") or [])

    def err(self, t):
        self.errores.append(t)

    def aviso(self, t):
        self.avisos.append(t)

    def numero(self, v, donde, minimo=None, maximo=None):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            self.err(f"{donde}: debe ser un número (vino {v!r})")
            return False
        if (minimo is not None and v < minimo) or (maximo is not None and v > maximo):
            self.err(f"{donde}: {v} fuera de rango [{minimo}, {maximo}]")
            return False
        return True

    def color(self, v, donde):
        if v is not None and not (isinstance(v, str) and RE_HEX.fullmatch(v)):
            self.err(f"{donde}: color no válido {v!r} (use #rrggbb)")

    def clave(self, k, donde):
        if k not in self.claves:
            self.err(f"{donde}: la estructura «{k}» no está en «estructuras»")

    def lista_claves(self, v, donde):
        if v is None:
            return
        if not isinstance(v, list):
            self.err(f"{donde}: debe ser una lista de claves")
            return
        for k in v:
            self.clave(k, donde)

    def indice(self, v, donde):
        if self.n_ruta < 2:
            self.err(f"{donde}: usa índices de la ruta, pero no hay ruta con puntos")
            return False
        return self.numero(v, donde, 0, self.n_ruta - 1)

    def punto(self, p, donde, rango=False):
        if isinstance(p, list) and len(p) == 3 and all(isinstance(x, (int, float)) for x in p):
            if self.caja:
                mn, mx = self.caja
                marg = [max(2.0, 0.3 * (mx[i] - mn[i])) for i in range(3)]
                if any(p[i] < mn[i] - marg[i] or p[i] > mx[i] + marg[i] for i in range(3)):
                    self.aviso(f"{donde}: {p} queda lejos del modelo (caja {[round(x, 1) for x in mn]} a "
                               f"{[round(x, 1) for x in mx]}); ¿coordenadas de Blender (Z arriba) en vez de glTF (Y arriba)?")
            return
        if isinstance(p, str):
            m = re.fullmatch(r"ruta:(-?\d+(?:\.\d+)?)", p)
            if m:
                self.indice(float(m.group(1)), f"{donde} («{p}»)")
                return
            m = re.fullmatch(r"ruta:(\d+)-(\d+)", p)
            if m and rango:
                self.indice(int(m.group(1)), f"{donde} («{p}»)")
                self.indice(int(m.group(2)), f"{donde} («{p}»)")
                return
            if p in self.claves:
                return
        extra = ', "ruta:A-B"' if rango else ""
        self.err(f"{donde}: punto no válido {p!r} (use [x,y,z], una clave de estructura, \"ruta:N\"{extra})")

    def valor_tramo(self, v, desde, hasta, donde):
        if isinstance(v, list):
            if not all(isinstance(x, (int, float)) for x in v):
                self.err(f"{donde}: la lista debe tener solo números")
            elif isinstance(desde, (int, float)) and isinstance(hasta, (int, float)) and float(desde).is_integer() and float(hasta).is_integer():
                esperado = int(hasta) - int(desde) + 1
                if len(v) != esperado:
                    self.err(f"{donde}: {len(v)} valores; el tramo {desde}-{hasta} tiene {esperado} puntos")
        else:
            self.numero(v, donde, 0)

    def revisar(self):
        c = self.cfg
        est = c.get("estructuras")
        if not isinstance(est, list) or not est:
            self.err("«estructuras» debe ser una lista con al menos una estructura")
            return
        for i, e in enumerate(est):
            d = f"estructuras[{i}]"
            if not isinstance(e, dict):
                self.err(f"{d}: debe ser un objeto")
                continue
            k = e.get("k")
            if not isinstance(k, str) or not RE_CLAVE.fullmatch(k):
                self.err(f"{d}: «k» debe ser una clave ASCII (letras, números, _ o -); vino {k!r}")
                continue
            if k in self.claves:
                self.err(f"{d}: clave repetida «{k}»")
            self.claves[k] = e
        for i, e in enumerate(est):
            if not isinstance(e, dict) or not isinstance(e.get("k"), str):
                continue
            d, k = f"estructuras[{i}] «{e.get('k')}»", e["k"]
            if not isinstance(e.get("n"), str) or not e["n"].strip():
                self.err(f"{d}: falta «n» (nombre visible)")
            self.color(e.get("c"), d + ".c")
            self.color(e.get("emis"), d + ".emis")
            if "a" in e:
                self.numero(e["a"], d + ".a", 0, 1)
            if e.get("con") is not None and e["con"] not in self.claves:
                self.err(f"{d}: «con» apunta a «{e['con']}», que no existe")
            tubo = e.get("tubo")
            if tubo is not None:
                if not isinstance(tubo, dict):
                    self.err(f"{d}.tubo: debe ser un objeto")
                elif "puntos" in tubo:
                    pts = tubo["puntos"]
                    if not isinstance(pts, list) or len(pts) < 2:
                        self.err(f"{d}.tubo.puntos: necesita al menos 2 puntos")
                    else:
                        for j, p in enumerate(pts):
                            self.punto(p, f"{d}.tubo.puntos[{j}]", rango=True)
                else:
                    self.indice(tubo.get("desde", 0), d + ".tubo.desde")
                    self.indice(tubo.get("hasta", max(0, self.n_ruta - 1)), d + ".tubo.hasta")
                if isinstance(tubo, dict) and "radio" in tubo:
                    self.valor_tramo(tubo["radio"], tubo.get("desde"), tubo.get("hasta"), d + ".tubo.radio")
                if k in self.nodos and self.nodos[k]["malla"]:
                    self.aviso(f"{d}: tiene «tubo» pero también existe en el GLB; se usa la malla del GLB")
            elif k not in self.nodos:
                disp = ", ".join(sorted(n for n, v in self.nodos.items() if v["malla"]))
                self.err(f"{d}: la clave no existe como nodo en el GLB (nodos con geometría: {disp})")
            elif not self.nodos[k]["malla"]:
                self.err(f"{d}: el nodo «{k}» del GLB no tiene geometría")
        configurados = set(self.claves)
        for n, v in self.nodos.items():
            if v["malla"] and n not in configurados:
                self.aviso(f"nodo del GLB sin configurar: «{n}» (se verá gris, en el grupo «Sin configurar»)")
        # grupos
        ids = []
        for i, g in enumerate(c.get("grupos") or []):
            if not isinstance(g, dict) or not isinstance(g.get("id"), str):
                self.err(f"grupos[{i}]: debe ser {{\"id\": …, \"n\": …}}")
            else:
                ids.append(g["id"])
        if ids:
            for e in est:
                if isinstance(e, dict) and e.get("g") and e["g"] not in ids:
                    self.aviso(f"estructura «{e.get('k')}»: el grupo «{e['g']}» no está en «grupos» (se agrega al final)")
        self.lista_claves(c.get("foco_ocultar"), "foco_ocultar")
        self.revisar_ruta()
        self.revisar_vistas()
        modos = self.revisar_modos()
        self.revisar_puntos(modos)
        self.revisar_flujo()
        self.revisar_secuencias()
        self.revisar_reseccion()
        if "seg_etapa" in c:
            self.numero(c["seg_etapa"], "seg_etapa", 1, 60)
        pp = c.get("pestanas_privadas")
        if pp is not None and not (isinstance(pp, list) and all(isinstance(x, str) for x in pp)):
            self.err("pestanas_privadas: debe ser una lista de ids de pestaña")

    def revisar_ruta(self):
        r = self.cfg.get("ruta")
        if r is None:
            return
        if not isinstance(r, dict):
            self.err("ruta: debe ser un objeto")
            return
        pts, rad = r.get("puntos"), r.get("radios")
        if not isinstance(pts, list) or len(pts) < 2:
            self.err("ruta.puntos: necesita al menos 2 puntos [x,y,z] (o «archivo»)")
            return
        for i in range(1, len(pts)):
            if math.dist(pts[i], pts[i - 1]) < 1e-6:
                self.err(f"ruta.puntos[{i}]: repite el punto anterior")
        for i, p in enumerate(pts[:: max(1, len(pts) // 12)]):
            self.punto(p, f"ruta.puntos (muestra {i})")
        if rad is not None and (not isinstance(rad, list) or len(rad) != len(pts)):
            self.err(f"ruta.radios: debe tener un radio (cm) por punto ({len(pts)})")
        if "vel" in r:
            self.numero(r["vel"], "ruta.vel", 0.01)
        for i, z in enumerate(r.get("zonas") or []):
            self.indice(z.get("desde", 0), f"ruta.zonas[{i}].desde")
            self.indice(z.get("hasta", len(pts) - 1), f"ruta.zonas[{i}].hasta")
            if "vel" in z:
                self.numero(z["vel"], f"ruta.zonas[{i}].vel", 0.01)
        e = r.get("estrechez")
        if e is not None:
            if not isinstance(e, dict) or "desde" not in e or "hasta" not in e:
                self.err("ruta.estrechez: necesita «desde» y «hasta» (índices de la ruta)")
                return
            if self.indice(e["desde"], "ruta.estrechez.desde") and self.indice(e["hasta"], "ruta.estrechez.hasta") and e["desde"] >= e["hasta"]:
                self.err("ruta.estrechez: «desde» debe ser menor que «hasta»")
            for campo in ("luz_normal", "pared_normal"):
                if campo in e:
                    self.valor_tramo(e[campo], e["desde"], e["hasta"], f"ruta.estrechez.{campo}")
            self.color(e.get("color_normal"), "ruta.estrechez.color_normal")
            if e.get("clave") is not None:
                self.clave(e["clave"], "ruta.estrechez.clave")

    def revisar_vistas(self):
        v = self.cfg.get("vistas")
        if v is None:
            return
        if not isinstance(v, dict):
            self.err("vistas: debe ser un objeto {id: {n, dir, objetivo, radio}}")
            return
        for vid, x in v.items():
            d = f"vistas.{vid}"
            if not isinstance(x, dict):
                self.err(f"{d}: debe ser un objeto")
                continue
            dr = x.get("dir", [0, 0.08, 1])
            if not (isinstance(dr, list) and len(dr) == 3 and all(isinstance(t, (int, float)) for t in dr)) or not any(dr):
                self.err(f"{d}.dir: debe ser [x,y,z] distinto de cero")
            if "objetivo" in x:
                self.punto(x["objetivo"], d + ".objetivo")
            if "radio" in x:
                self.numero(x["radio"], d + ".radio", 0.01)
        vi = self.cfg.get("vista_inicial")
        if vi is not None and vi not in v:
            self.err(f"vista_inicial: «{vi}» no está en vistas")

    def revisar_modos(self):
        modos = {}
        cr = self.cfg.get("reseccion") if isinstance(self.cfg.get("reseccion"), dict) else {}
        ops = cr.get("opciones") if isinstance(cr.get("opciones"), dict) else {}
        secs = self.cfg.get("secuencias") if isinstance(self.cfg.get("secuencias"), dict) else {}
        vistas = self.cfg.get("vistas") if isinstance(self.cfg.get("vistas"), dict) else {"frente": 1, "oblicua": 1, "lateral": 1}
        est = (self.cfg.get("ruta") or {}).get("estrechez") if isinstance(self.cfg.get("ruta"), dict) else None
        for i, m in enumerate(self.cfg.get("modos") or []):
            d = f"modos[{i}]"
            if not isinstance(m, dict) or not isinstance(m.get("id"), str) or not RE_ID.fullmatch(m["id"]):
                self.err(f"{d}: «id» debe ser minúsculas, números y guiones")
                continue
            d = f"modos «{m['id']}»"
            if m["id"] in modos:
                self.err(f"{d}: id repetido")
            modos[m["id"]] = m
            if not isinstance(m.get("n"), str):
                self.err(f"{d}: falta «n» (texto del botón)")
            for campo in ("mostrar", "ocultar"):
                self.lista_claves(m.get(campo), f"{d}.{campo}")
            for k, a in (m.get("opacidad") or {}).items():
                self.clave(k, f"{d}.opacidad")
                self.numero(a, f"{d}.opacidad.{k}", 0, 1)
            if m.get("vista") is not None and m["vista"] not in vistas:
                self.err(f"{d}.vista: «{m['vista']}» no está en vistas")
            mod = m.get("modulo")
            if mod not in (None, "normal", "etapas", "reseccion"):
                self.err(f"{d}.modulo: «{mod}» no existe (normal, etapas, reseccion)")
            if mod == "normal" and not (isinstance(est, dict) and "luz_normal" in est and "pared_normal" in est):
                self.err(f"{d}: el módulo «normal» necesita ruta.estrechez con luz_normal y pared_normal")
            if mod == "etapas" and m.get("secuencia") not in secs:
                self.err(f"{d}: «secuencia» debe ser una de {sorted(secs)}")
            if mod == "reseccion":
                if m.get("opcion") not in ops:
                    self.err(f"{d}: «opcion» debe ser una de {sorted(ops)}")
                if m.get("fase", "saca") not in ("saca", "queda"):
                    self.err(f"{d}: «fase» debe ser «saca» o «queda»")
        mi = self.cfg.get("modo_inicial")
        if mi is not None and mi not in modos:
            self.err(f"modo_inicial: «{mi}» no está en modos")
        self.modos = modos
        return modos

    def revisar_puntos(self, modos):
        vistos = set()
        for i, h in enumerate(self.cfg.get("hotspots") or []):
            d = f"hotspots[{i}]"
            if not isinstance(h, dict):
                self.err(f"{d}: debe ser un objeto")
                continue
            if not isinstance(h.get("n"), int):
                self.err(f"{d}: «n» (número visible) debe ser entero")
            elif h["n"] in vistos:
                self.err(f"{d}: número repetido {h['n']}")
            vistos.add(h.get("n"))
            if not isinstance(h.get("t"), str):
                self.err(f"{d}: falta «t» (título)")
            self.punto(h.get("p"), d + ".p")
            if h.get("k") is not None:
                self.clave(h["k"], d + ".k")
            self.color(h.get("color"), d + ".color")
            for mid, v in (h.get("por_modo") or {}).items():
                if mid not in modos:
                    self.err(f"{d}.por_modo: el modo «{mid}» no existe")
                if v not in (False, None) and not isinstance(v, dict):
                    self.err(f"{d}.por_modo.{mid}: debe ser {{t, d}} o false")

    def revisar_flujo(self):
        f = self.cfg.get("flujo")
        if f is None:
            return
        if self.n_ruta < 2:
            self.err("flujo: necesita una ruta con puntos")
            return
        so = f.get("solido") or {}
        if "tam" in so and not (isinstance(so["tam"], list) and len(so["tam"]) == 2):
            self.err("flujo.solido.tam: debe ser [mínimo, máximo] en cm (radio de cada trozo)")
        for k, a in (f.get("opacidad") or {}).items():
            self.clave(k, "flujo.opacidad")
        vistas = self.cfg.get("vistas") if isinstance(self.cfg.get("vistas"), dict) else {}
        if f.get("vista") is not None and f["vista"] not in vistas:
            self.err(f"flujo.vista: «{f['vista']}» no está en vistas")
        if not (self.cfg.get("ruta") or {}).get("estrechez"):
            self.aviso("flujo sin ruta.estrechez: el contenido pasará sin frenarse ni acumularse")

    def revisar_secuencias(self):
        s = self.cfg.get("secuencias")
        if s is None:
            return
        if not isinstance(s, dict):
            self.err("secuencias: debe ser un objeto {id: [etapas]}")
            return
        est = (self.cfg.get("ruta") or {}).get("estrechez") or {}
        for sid, etapas in s.items():
            if not isinstance(etapas, list) or not etapas:
                self.err(f"secuencias.{sid}: debe ser una lista de etapas")
                continue
            for i, et in enumerate(etapas):
                d = f"secuencias.{sid}[{i}]"
                if not isinstance(et, dict):
                    self.err(f"{d}: debe ser un objeto")
                    continue
                if not isinstance(et.get("t"), str):
                    self.err(f"{d}: falta «t» (leyenda de la etapa)")
                if et.get("tipo") == "escala":
                    self.clave(et.get("clave"), d + ".clave")
                    self.numero(et.get("factor"), d + ".factor", 0.01)
                    continue
                for k, fct in (et.get("escala") or {}).items():
                    self.clave(k, d + ".escala")
                    self.numero(fct, f"{d}.escala.{k}", 0.01)
                if ("luz" in et) != ("pared" in et):
                    self.err(f"{d}: «luz» y «pared» van juntas")
                if "luz" in et:
                    desde, hasta = et.get("desde", est.get("desde")), et.get("hasta", est.get("hasta"))
                    if desde is None or hasta is None:
                        self.err(f"{d}: sin tramo: ponga «desde»/«hasta» o defina ruta.estrechez")
                        continue
                    self.indice(desde, d + ".desde")
                    self.indice(hasta, d + ".hasta")
                    self.valor_tramo(et["luz"], desde, hasta, d + ".luz")
                    self.valor_tramo(et["pared"], desde, hasta, d + ".pared")
                    self.color(et.get("color"), d + ".color")
                elif not et.get("escala"):
                    self.err(f"{d}: una etapa lleva «luz» y «pared», «escala» o es {{\"tipo\": \"escala\"}}")

    def revisar_reseccion(self):
        r = self.cfg.get("reseccion")
        if r is None:
            return
        if not isinstance(r, dict) or not isinstance(r.get("opciones"), dict) or not r["opciones"]:
            self.err("reseccion: necesita «opciones»: {id: {…}}")
            return
        self.color(r.get("color_saca"), "reseccion.color_saca")
        self.color(r.get("color_ganglios"), "reseccion.color_ganglios")
        for j, p in enumerate(r.get("ganglios") or []):
            self.punto(p, f"reseccion.ganglios[{j}]")
        for oid, op in r["opciones"].items():
            d = f"reseccion.opciones.{oid}"
            if not isinstance(op, dict):
                self.err(f"{d}: debe ser un objeto")
                continue
            self.lista_claves(op.get("saca"), d + ".saca")
            self.lista_claves(op.get("ocultar_queda"), d + ".ocultar_queda")
            for i, pl in enumerate(op.get("planos") or []):
                dp = f"{d}.planos[{i}]"
                self.lista_claves(pl.get("claves"), dp + ".claves")
                q = pl.get("queda")
                if not isinstance(q, list) or not q:
                    self.err(f"{dp}.queda: lista de semiespacios que se conservan")
                    continue
                for j, s in enumerate(q):
                    if isinstance(s, dict) and "ruta" in s:
                        self.indice(s["ruta"], f"{dp}.queda[{j}].ruta")
                        if s.get("queda", "antes") not in ("antes", "despues"):
                            self.err(f"{dp}.queda[{j}].queda: «antes» o «despues»")
                    elif isinstance(s, dict) and "punto" in s and "normal" in s:
                        self.punto(s["punto"], f"{dp}.queda[{j}].punto")
                    else:
                        self.err(f"{dp}.queda[{j}]: use {{\"ruta\": N, \"queda\": \"antes\"}} o {{\"punto\": …, \"normal\": […]}}")
            for j, p in enumerate(op.get("ganglios") or []):
                self.punto(p, f"{d}.ganglios[{j}]")
            for j, rc in enumerate(op.get("reconstruccion") or []):
                pts = rc.get("puntos") if isinstance(rc, dict) else None
                if not isinstance(pts, list) or len(pts) < 2:
                    self.err(f"{d}.reconstruccion[{j}]: necesita «puntos» (al menos 2)")
                    continue
                for i, p in enumerate(pts):
                    self.punto(p, f"{d}.reconstruccion[{j}].puntos[{i}]", rango=True)
                self.color(rc.get("color"), f"{d}.reconstruccion[{j}].color")
            for j, p in enumerate(op.get("uniones") or []):
                self.punto(p, f"{d}.uniones[{j}]")
            pr = op.get("post_ruta")
            if pr is not None:
                pts = pr.get("puntos") if isinstance(pr, dict) else None
                if not isinstance(pts, list) or len(pts) < 2:
                    self.err(f"{d}.post_ruta: necesita «puntos» (al menos 2)")
                else:
                    for i, p in enumerate(pts):
                        self.punto(p, f"{d}.post_ruta.puntos[{i}]", rango=True)


# ---------------------------------------------------------------------------------------------
# HTML: secciones y elementos privados (con el parser de la biblioteca estándar)
# ---------------------------------------------------------------------------------------------
VACIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class _Rangos(HTMLParser):
    """Ubica elementos (inicio, fin, atributos, inicio y fin del contenido) que cumplen pred(tag, attrs)."""

    def __init__(self, texto, pred):
        super().__init__(convert_charrefs=True)
        self.texto, self.pred = texto, pred
        self.lineas = [0] + [m.end() for m in re.finditer("\n", texto)]
        self.pila, self.rangos = [], []

    def _pos(self):
        linea, col = self.getpos()
        return self.lineas[linea - 1] + col

    def handle_starttag(self, tag, attrs):
        ini = self._pos()
        fin = ini + len(self.get_starttag_text() or "")
        a = dict(attrs)
        if tag in VACIOS:
            if self.pred(tag, a):
                self.rangos.append((ini, fin, a, fin, fin))
            return
        self.pila.append((tag, ini, a, fin))

    def handle_startendtag(self, tag, attrs):
        ini = self._pos()
        fin = ini + len(self.get_starttag_text() or "")
        a = dict(attrs)
        if self.pred(tag, a):
            self.rangos.append((ini, fin, a, fin, fin))

    def handle_endtag(self, tag):
        ini_cierre = self._pos()
        fin = self.texto.find(">", ini_cierre) + 1
        for j in range(len(self.pila) - 1, -1, -1):
            if self.pila[j][0] == tag:
                _, ini, a, fin_tag = self.pila[j]
                del self.pila[j:]
                if self.pred(tag, a):
                    self.rangos.append((ini, fin, a, fin_tag, ini_cierre))
                return


def rangos(texto, pred):
    p = _Rangos(texto, pred)
    p.feed(texto)
    p.close()
    fuera, ultimo = [], -1
    for r in sorted(p.rangos):
        if r[0] >= ultimo:   # solo los de más afuera
            fuera.append(r)
            ultimo = r[1]
    return fuera


def quitar_privados(texto):
    for ini, fin, *_ in reversed(rangos(texto, lambda t, a: "data-privado" in a)):
        texto = texto[:ini] + texto[fin:]
    return texto


def extraer_secciones(texto, nombre):
    """[(id, titulo, html, inicio)] de las <section class="panel" id="panel-…" data-titulo="…">."""
    out = []
    for ini, fin, a, _, _ in rangos(texto, lambda t, a: t == "section" and (a.get("id") or "").startswith("panel-")):
        sid = a["id"][len("panel-"):]
        clases = (a.get("class") or "").split()
        if not RE_ID.fullmatch(sid):
            raise ErrorArmado(f"{nombre}: id de pestaña no válido «{a['id']}» (use panel-minusculas-y-guiones)")
        if "panel" not in clases:
            raise ErrorArmado(f"{nombre}: la sección «{a['id']}» necesita class=\"panel\"")
        if "oculto" in clases:
            raise ErrorArmado(f"{nombre}: la sección «{a['id']}» trae la clase «oculto»; la pone el script (sin JS debe verse)")
        if sid != "explorar" and not (a.get("data-titulo") or "").strip():
            raise ErrorArmado(f"{nombre}: la sección «{a['id']}» necesita data-titulo (rótulo de la pestaña)")
        out.append((sid, (a.get("data-titulo") or "").strip(), texto[ini:fin], ini))
    return out


# ---------------------------------------------------------------------------------------------
# Piezas estáticas (se ven sin JS)
# ---------------------------------------------------------------------------------------------
def texto_cfg(cfg, campo, variante, defecto=""):
    if variante == "compartir" and cfg.get(campo + "_compartir"):
        return cfg[campo + "_compartir"]
    return cfg.get(campo) or defecto


def cabecera(cfg, variante):
    banner = texto_cfg(cfg, "banner", variante)
    if variante == "compartir" and not cfg.get("banner_compartir"):
        banner = BANNER_COMPARTIR   # el banner privado nunca viaja en la copia
    partes = []
    if banner:
        partes.append(f'  <div class="private">{esc(banner)}</div>')
    partes.append("  <header>")
    ey = texto_cfg(cfg, "eyebrow", variante)
    if ey:
        partes.append(f'    <div class="mono">{esc(ey)}</div>')
    partes.append(f'    <h1>{esc(texto_cfg(cfg, "titulo", variante, "Modelo 3D"))}</h1>')
    partes.append(f'    <p class="upd">{esc(texto_cfg(cfg, "subtitulo", variante, SUBTITULO))}</p>')
    partes.append("  </header>")
    return "\n".join(partes)


def navegacion(cfg, pestanas):
    filas = ['  <nav class="tabs" role="tablist" aria-label="Secciones">',
             f'    <a class="tab activo" data-tab="explorar" href="#panel-explorar" role="tab">{esc(cfg.get("explorar_titulo") or "Explorar")}</a>']
    for sid, titulo, _ in pestanas:
        filas.append(f'    <a class="tab" data-tab="{sid}" href="#panel-{sid}" role="tab">{esc(titulo)}</a>')
    filas.append('    <button class="tema" id="btn-tema" type="button" aria-label="Cambiar entre tema claro y oscuro">☾</button>')
    filas.append("  </nav>")
    return "\n".join(filas)


def _grupos(cfg):
    orden = [(g["id"], g.get("n") or g["id"]) for g in cfg.get("grupos") or [] if isinstance(g, dict) and g.get("id")]
    ids = [g for g, _ in orden]
    for e in cfg["estructuras"]:
        g = e.get("g") or "estructuras"
        if g not in ids:
            ids.append(g)
            orden.append((g, "Estructuras" if g == "estructuras" else g))
    return orden


def _leg(color, nombre, desc):
    return (f'      <div class="leg"><span class="dot" style="background:{color}"></span>'
            f'<div><b>{esc(nombre)}</b><span class="s">{esc(desc)}</span></div></div>')


def leyenda_colores(cfg):
    filas = ['<div class="leyenda-colores">']
    for gid, gn in _grupos(cfg):
        es = [e for e in cfg["estructuras"] if (e.get("g") or "estructuras") == gid and e.get("leyenda", True) is not False]
        if not es:
            continue
        filas.append(f'    <div class="ley-grupo"><span class="mono">{esc(gn)}</span>')
        filas += [_leg(e.get("c") or "#9aa5a1", e["n"], e.get("d") or "") for e in es]
        filas.append("    </div>")
    extra = []
    ruta = cfg.get("ruta") or {}
    est = ruta.get("estrechez") or {}
    if "luz_normal" in est:
        extra.append(_leg(est.get("color_normal") or "#e8b9a0", "Sin la lesión (ilustración)", "Pared y luz normales dibujadas sobre el mismo tramo."))
    secs = cfg.get("secuencias") or {}
    if any("luz" in et for s in secs.values() for et in s if isinstance(et, dict)):
        c_les = next((e.get("c") for e in cfg["estructuras"] if e.get("k") == est.get("clave")), "#e0237d")
        extra.append(_leg(c_les, "Etapas (ilustración)", "La pared y la luz de cada etapa; no son mediciones."))
    rs = cfg.get("reseccion") or {}
    ops = (rs.get("opciones") or {}).values()
    if ops:
        extra.append(_leg(rs.get("color_saca") or "#e53935", "Lo que se saca (esquema)", "En rojo, en los modos «qué se saca»."))
        if rs.get("ganglios") or any(o.get("ganglios") for o in ops):
            extra.append(_leg(rs.get("color_ganglios") or "#ffd166", "Ganglios (esquema)", "Ubicación ilustrativa; no salen del estudio."))
        rec = [r for o in ops for r in o.get("reconstruccion") or []]
        if rec:
            extra.append(_leg(rec[0].get("color") or "#e8b9a0", "Reconstrucción (esquema)", "Cómo se vuelve a unir lo que queda."))
        if any(o.get("uniones") for o in ops):
            extra.append(_leg("#ffffff", "Uniones (esquema)", "Los puntos donde se cose."))
    fl = cfg.get("flujo") or {}
    if fl:
        extra.append(_leg((fl.get("liquido") or {}).get("color") or "#4fc3f7", "Líquido (simulación)", "Ilustra el paso; no mide nada."))
        extra.append(_leg((fl.get("solido") or {}).get("color") or "#8d5a2b", "Sólido (simulación)", "Trozos de distinto tamaño."))
    if extra:
        filas.append('    <div class="ley-grupo"><span class="mono">Lo que dibuja el visor</span>')
        filas += extra
        filas.append("    </div>")
    filas.append("  </div>")
    return "\n".join(filas)


def _claro(hexa):
    c = int(hexa[1:], 16)
    return 0.299 * (c >> 16 & 255) + 0.587 * (c >> 8 & 255) + 0.114 * (c & 255) > 165


def lista_puntos(cfg):
    hs = sorted([h for h in cfg.get("hotspots") or [] if isinstance(h, dict)], key=lambda h: h.get("n", 0))
    if not hs:
        return ""
    colores = {e["k"]: e.get("c") for e in cfg["estructuras"]}
    filas = ['<ol class="puntos-lista">']
    for h in hs:
        c = h.get("color") or colores.get(h.get("k")) or "#4fb3ac"
        tinta = "#0e1513" if _claro(c) else "#ffffff"
        filas.append(f'    <li><span class="n" style="background:{c};color:{tinta}">{int(h["n"])}</span>'
                     f'<div><b>{esc(h.get("t"))}</b><span class="s">{esc(h.get("d"))}</span></div></li>')
    filas.append("  </ol>")
    return "\n".join(filas)


def bloque_sin_js(cfg):
    partes = []
    lp = lista_puntos(cfg)
    if lp:
        partes.append(f'    <div class="blk"><h2>Los números del modelo</h2>\n  {lp}\n    </div>')
    partes.append(f'    <div class="blk"><h2>Qué es cada color</h2>\n  {leyenda_colores(cfg)}\n    </div>')
    return "\n".join(partes)


# ---------------------------------------------------------------------------------------------
# Armado
# ---------------------------------------------------------------------------------------------
def armar(a):
    avisos = []
    cfg_bruta = leer_json(a.config)
    cfg = sin_doc(cfg_bruta)
    preparar_ruta(cfg, os.path.dirname(os.path.abspath(a.config)))
    gltf, datos_glb = leer_glb(a.glb)
    if gltf.get("materials"):
        avisos.append("el GLB trae materiales: el visor los ignora y colorea desde la configuración")
    nodos = nodos_glb(gltf)
    rev = Revisor(cfg, nodos)
    rev.revisar()
    avisos += rev.avisos
    if rev.errores:
        raise ErrorArmado("la configuración tiene errores:\n  - " + "\n  - ".join(rev.errores))

    variante = a.variante
    if variante == "compartir":
        cfg["prefijo_storage"] = (cfg.get("prefijo_storage") or "visor3d") + "-compartir"

    # Pestañas de contenido
    extra_explorar, pestanas = "", []
    if a.pestanas:
        txt = leer_texto(a.pestanas)
        secciones = extraer_secciones(txt, os.path.basename(a.pestanas))
        pos_video = txt.find("<!--__VIDEO__-->")
        for sid, titulo, cuerpo, ini in secciones:
            if sid in ("glosario", "video") and ((sid == "glosario" and a.glosario) or (sid == "video" and a.video)):
                raise ErrorArmado(f"pestañas: la sección «{sid}» choca con --{sid}")
            if sid == "explorar":
                extra_explorar = cuerpo[cuerpo.find(">") + 1:cuerpo.rfind("</section>")].strip("\n")
                continue
            if pos_video >= 0 and ini > pos_video and a.video and not any(p[0] == "video" for p in pestanas):
                pestanas.append(("video", "Video", None))
            pestanas.append((sid, titulo, cuerpo))
    if a.video and not any(p[0] == "video" for p in pestanas):
        pestanas.append(("video", "Video", None))
    if a.glosario:
        pestanas.append(("glosario", "Glosario", None))
    vistos = set()
    for sid, _, _ in pestanas:
        if sid in vistos:
            raise ErrorArmado(f"pestaña repetida: «{sid}»")
        vistos.add(sid)
    for pid in cfg.get("pestanas_privadas") or []:
        if pid not in vistos:
            avisos.append(f"pestanas_privadas: «{pid}» no es una pestaña de este visor")

    def cuerpo_de(sid, cuerpo):
        if sid == "video":
            return (f'  <section class="panel" id="panel-video" data-titulo="Video">\n'
                    f'{leer_texto(a.video).strip()}\n  </section>')
        if sid == "glosario":
            filas = leer_texto(a.glosario).strip()
            if "<dl" in filas:
                raise ErrorArmado("--glosario: el archivo lleva solo las filas <div data-terms=…><dt>…</dt><dd>…</dd></div>, sin <dl>")
            return ('  <section class="panel" id="panel-glosario" data-titulo="Glosario">\n    <div class="blk">\n'
                    '      <h2>Glosario</h2>\n      <p class="lead">Toque cualquier palabra subrayada con puntos y aparece su definición.</p>\n'
                    f'      <dl class="dicc" id="dicc">\n{filas}\n      </dl>\n    </div>\n  </section>')
        return "  " + cuerpo

    if variante == "compartir":
        privadas = set(cfg.get("pestanas_privadas") or [])
        pestanas = [p for p in pestanas if p[0] not in privadas]
    paneles = "\n\n".join(cuerpo_de(sid, cuerpo) for sid, _, cuerpo in pestanas)
    if variante == "compartir":
        paneles = quitar_privados(paneles)
        extra_explorar = quitar_privados(extra_explorar)
    leyenda, puntos = leyenda_colores(cfg), lista_puntos(cfg)
    paneles = paneles.replace("<!--__LEYENDA_COLORES__-->", leyenda).replace("<!--__PUNTOS__-->", puntos).replace("<!--__VIDEO__-->", "")
    extra_explorar = extra_explorar.replace("<!--__LEYENDA_COLORES__-->", leyenda).replace("<!--__PUNTOS__-->", puntos)
    for m in re.finditer(r'data-ver="([^"]*)"', paneles + extra_explorar):
        if m.group(1) not in rev.modos:
            avisos.append(f'data-ver="{m.group(1)}": ese modo no existe en la configuración')

    # Plantilla
    plantilla = leer_texto(a.plantilla)
    for mk in MARCADORES:
        if plantilla.count(mk) != 1:
            raise ErrorArmado(f"plantilla: el marcador {mk} debe aparecer una vez (aparece {plantilla.count(mk)})")
    poster = ""
    if a.poster:
        ext = os.path.splitext(a.poster)[1].lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext)
        if not mime:
            raise ErrorArmado("--poster: use .jpg, .png o .webp")
        with open(a.poster, "rb") as f:
            poster = (f'      <img class="poster" id="poster" alt="Vista fija del modelo 3D" '
                      f'src="data:{mime};base64,{base64.b64encode(f.read()).decode()}">')
    cfg_json = json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    glb_b64 = base64.b64encode(datos_glb).decode("ascii")
    reemplazos = {
        "__TITULO_PAGINA__": esc(texto_cfg(cfg, "titulo", variante, "Modelo 3D")),
        "<!--__CABECERA__-->": cabecera(cfg, variante),
        "<!--__NAV__-->": navegacion(cfg, pestanas),
        "<!--__POSTER__-->": poster,
        "<!--__EXPLORAR_EXTRA__-->": extra_explorar,
        "<!--__SIN_JS__-->": bloque_sin_js(cfg),
        "<!--__PANELES__-->": paneles,
        "<!--__PIE__-->": f'  <p class="foot">{esc(texto_cfg(cfg, "pie", variante, PIE))}</p>',
        "/*__CONFIG_JSON__*/": cfg_json,
        "__GLB_B64__": glb_b64,
    }
    # Una sola pasada sobre la plantilla: el contenido insertado nunca se vuelve a buscar
    salida = re.sub("|".join(re.escape(m) for m in MARCADORES), lambda m: reemplazos[m.group(0)], plantilla)
    if not salida.startswith('<meta charset="utf-8">\n<meta name="viewport"'):
        raise ErrorArmado("la salida debe empezar con <meta charset> y viewport")
    if re.search(r'class="[^"]*\boculto\b', salida):
        raise ErrorArmado("el HTML armado trae la clase «oculto»: sin JS se perdería contenido")
    n_completar = salida.count("[COMPLETAR")
    if n_completar:
        avisos.append(f"quedan {n_completar} marcadores [COMPLETAR: …] por llenar")
    datos = salida.encode("utf-8")
    malos = [b for b in datos[:400000] if b < 9 or (13 < b < 32)]
    if malos:
        raise ErrorArmado("la salida tiene bytes de control (¿una ruta de Windows con escapes?)")
    tam = len(datos)
    if tam > 16 * MB:
        raise ErrorArmado(f"el visor pesa {tam / MB:.1f} MB (> 16 MB, límite de los artefactos): reduzca el GLB (decimar) o quite el póster")
    if tam > 12 * MB:
        avisos.append(f"el visor pesa {tam / MB:.1f} MB (> 12 MB): conviene decimar el GLB")
    destino = os.path.abspath(a.salida)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tmp = destino + ".tmp"
    with open(tmp, "wb") as f:
        f.write(datos)
    os.replace(tmp, destino)
    return destino, tam, len(datos_glb), cfg, pestanas, avisos


def listar(ruta_glb):
    gltf, _ = leer_glb(ruta_glb)
    info = nodos_glb(gltf)
    print(f"{'nodo':28s} {'centro (glTF, cm)':>28s}   tamaño")
    for n, d in sorted(info.items()):
        if not d["malla"]:
            continue
        c = [(d["min"][i] + d["max"][i]) / 2 for i in range(3)]
        t = [d["max"][i] - d["min"][i] for i in range(3)]
        print(f"{n:28s} {'[' + ', '.join(f'{x:7.2f}' for x in c) + ']':>28s}   " + " × ".join(f"{x:.1f}" for x in t))
    ct = caja_total(info)
    if ct:
        print("caja total:", [round(x, 2) for x in ct[0]], "a", [round(x, 2) for x in ct[1]])
    if gltf.get("materials"):
        print("aviso: el GLB trae materiales; el visor los ignora")


PALETA = ["#e8b9a0", "#7f93ad", "#c9a86a", "#6aa6e8", "#eadfc4", "#f4d35e", "#8fbf9f", "#90a4ae",
          "#bcaaa4", "#80cbc4", "#c5b358", "#a1887f"]   # neutra: sin violetas ni rojos (lesión y arterias)
# Claves conocidas (las de la paleta de Blender) cuando no se pasa --estilo.
CONOCIDAS = {"lesion": ("Lesión", "#ff2d95", 0.85), "luz": ("Luz (aire o contraste)", "#ffffff", 1.0),
             "hueso": ("Hueso", "#eee4c6", 0.55), "arterias": ("Arterias", "#d11f2a", 1.0),
             "venas": ("Venas", "#2f5fd0", 1.0), "cuerpo": ("Cuerpo (piel)", "#e3b49a", 0.07),
             "pulmones": ("Pulmones", "#8ec9f2", 0.2), "higado": ("Hígado", "#8e3324", 0.5),
             "bazo": ("Bazo", "#7f93ad", 0.55), "rinones": ("Riñones", "#f08a24", 0.7),
             "contenido": ("Contenido retenido", "#f4d35e", 0.55), "contraste": ("Contraste oral", "#3cff4e", 1.0)}


def _slug(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_") or "grupo"


def _escalar_hex(hexa, f):
    h = hexa.lstrip("#")
    return "#" + "".join("%02x" % max(0, min(255, round(int(h[i:i + 2], 16) * f))) for i in (0, 2, 4))


def esqueleto(ruta_glb, destino, ruta_estilo=None):
    """Configuración inicial con todos los nodos del GLB. Con --estilo toma nombres, colores, alfa y
    grupos del estilo.json de Blender (una sola paleta para fotos, video y visor); sin él usa las claves
    conocidas y una paleta neutra. La envoltura (la caja más grande que contiene los centros de casi
    todo lo demás) y las capas casi transparentes quedan en foco_ocultar."""
    gltf, _ = leer_glb(ruta_glb)
    info = {n: d for n, d in nodos_glb(gltf).items() if d["malla"]}
    if not info:
        raise ErrorArmado("el GLB no tiene nodos con geometría")
    vol = {n: math.prod(max(1e-6, d["max"][i] - d["min"][i]) for i in range(3)) for n, d in info.items()}
    centros = {n: [(d["min"][i] + d["max"][i]) / 2 for i in range(3)] for n, d in info.items()}
    envolturas = []
    for n in sorted(info, key=lambda x: -vol[x]):
        d = info[n]
        dentro = sum(all(d["min"][i] <= centros[o][i] <= d["max"][i] for i in range(3)) for o in info if o != n)
        if len(info) > 2 and dentro >= 0.8 * (len(info) - 1):
            envolturas.append(n)
        break
    estilo = {}
    orden_estilo = []
    if ruta_estilo:
        for e in leer_json(ruta_estilo).get("estructuras", []):
            if isinstance(e, dict) and e.get("clave"):
                estilo[e["clave"]] = e
                orden_estilo.append(e["clave"])
    grupos, est, foco = [], [], list(envolturas)
    libres = iter(PALETA * 4)
    claves = [k for k in orden_estilo if k in info] + sorted(k for k in info if k not in estilo)
    for n in claves:
        env = n in envolturas
        e = estilo.get(n)
        if e:
            g_nombre = re.sub(r"^\s*\d+\s*", "", str(e.get("grupo") or "Estructuras")) or "Estructuras"
            fila = {"k": n, "n": e.get("nombre") or n, "c": e.get("color") or next(libres),
                    "a": float(e.get("alpha", 1.0)), "g": _slug(g_nombre)}
            if e.get("emision"):
                fila["emis"] = _escalar_hex(fila["c"], min(1.0, float(e["emision"])) * 0.5)
        else:
            nom, col, alfa = CONOCIDAS.get(n, (n.replace("_", " ").strip().capitalize(), None, 0.55))
            g_nombre = "Referencia" if env else "Estructuras"
            fila = {"k": n, "n": nom, "c": "#e3b49a" if env else (col or next(libres)),
                    "a": 0.08 if env else alfa, "g": _slug(g_nombre)}
            if n == "luz":
                fila["emis"] = "#666666"
        fila["d"] = "[COMPLETAR: una línea]"
        if (fila["a"] <= 0.25 or n == "hueso") and n not in foco:
            foco.append(n)   # en los modos de foco estorban: envolturas, capas casi transparentes y el hueso
        if fila["g"] not in [x["id"] for x in grupos]:
            grupos.append({"id": fila["g"], "n": g_nombre})
        est.append(fila)
    cfg = {"_doc": "Esqueleto generado por armar_visor.py --esqueleto: completar nombres, colores (la lesión con el único color saturado), grupos, vistas, hotspots y modos. Ver references/viewer.md.",
           "titulo": "Modelo 3D", "prefijo_storage": "visor3d", "estructuras": est,
           "grupos": grupos, "foco_ocultar": foco}
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return len(est), envolturas


def main():
    ap = argparse.ArgumentParser(description="Arma el visor 3D de un solo archivo HTML.")
    ap.add_argument("--glb", required=True, help="modelo.glb (nodos con la clave de cada estructura, sin materiales)")
    ap.add_argument("--config", help="visor.json")
    ap.add_argument("--pestanas", help="HTML con las <section class=\"panel\"> de contenido")
    ap.add_argument("--glosario", help="HTML con las filas del glosario (<div data-terms=…><dt>…</dt><dd>…</dd></div>)")
    ap.add_argument("--video", help="HTML con el contenido de la pestaña Video")
    ap.add_argument("--poster", help="imagen fija que se ve mientras carga o sin JS (render de Blender)")
    ap.add_argument("--salida", help="archivo .html de salida")
    ap.add_argument("--variante", choices=["privada", "compartir"], default="privada")
    ap.add_argument("--plantilla", default=os.path.join(AQUI, "plantilla.html"))
    ap.add_argument("--listar", action="store_true", help="solo lista los nodos del GLB con su centro y tamaño")
    ap.add_argument("--esqueleto", metavar="JSON", help="escribe una configuración inicial con todos los nodos del GLB y termina")
    ap.add_argument("--estilo", help="con --esqueleto: estilo.json de Blender, para heredar nombres, colores, alfa y grupos")
    a = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")   # consolas cp1252: nunca fallar por un carácter
        except Exception:
            pass
    try:
        if a.listar:
            listar(a.glb)
            return 0
        if a.esqueleto:
            n, env = esqueleto(a.glb, a.esqueleto, a.estilo)
            print(f"ok  {a.esqueleto}: {n} estructuras; envoltura: {', '.join(env) or 'ninguna'}")
            return 0
        if not a.config or not a.salida:
            ap.error("--config y --salida son obligatorios (salvo con --listar)")
        destino, tam, tam_glb, cfg, pestanas, avisos = armar(a)
    except ErrorArmado as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    mods = [m for m, ok in (("flujo", cfg.get("flujo")), ("etapas", cfg.get("secuencias")), ("reseccion", cfg.get("reseccion")),
                            ("normal", ((cfg.get("ruta") or {}).get("estrechez") or {}).get("luz_normal") is not None)) if ok]
    print(f"ok  {destino}")
    print(f"    {tam / MB:.2f} MB (GLB {tam_glb / MB:.2f} MB) · variante {a.variante} · "
          f"{len(cfg['estructuras'])} estructuras · {len(cfg.get('modos') or [])} modos · {len(cfg.get('hotspots') or [])} hotspots")
    print(f"    pestañas: explorar, {', '.join(p[0] for p in pestanas) or '—'} · módulos: {', '.join(mods) or 'ninguno'}")
    for t in avisos:
        print("    aviso:", t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
