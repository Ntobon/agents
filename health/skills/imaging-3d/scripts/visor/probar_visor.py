"""Prueba headless de un visor 3D ya armado: capturas de cada modo (escritorio y angosto), los dos temas,
las pestañas, los flujos y la vista SIN JavaScript, con los errores de JS de cada corrida.

    python probar_visor.py --visor "Visor 3D.html" --salida <carpeta de capturas> [--rapido] [--modos a,b]

IMPORTANTE (Windows): lanzarlo desde la herramienta PowerShell o desde una terminal normal. Desde el Bash
tool de Claude Code, Edge headless termina con código 0 sin escribir ninguna captura.

Cómo funciona:
- Hace una copia de prueba (__prueba.html) con dos fragmentos: un capturador de errores (window.onerror,
  promesas, console.error y recursos que no cargan) que los escribe en el título, en una franja roja y en la
  consola, y una acción automática que lee la URL (?modo=&flujo=&avanzar=&tema=&tab=&vista=), espera a que
  cargue el modelo, avanza las simulaciones de forma síncrona (window.__avanzar), congela el tiempo y deja
  una línea VISOR_LISTO {estado} en la consola.
- Lanza Edge headless (--headless=new, WebGL por SwiftShader, --virtual-time-budget) con un perfil nuevo en
  cada corrida y --enable-logging=stderr, que es de donde salen los errores y el estado.
- Ancho angosto: la ventana headless no baja de ~500 px (pedir 375 da un viewport de 492). Se usa una página
  envoltorio con un iframe de 375 px, que sí da un viewport real de 375; la captura se recorta a 375.
- Sin JS: --blink-settings=scriptEnabled=false impide la captura, así que se usa un perfil cuyas
  Preferences bloquean JavaScript (lo mismo que apagarlo en la configuración). Se captura la página
  completa en una ventana muy alta y se corta en tajadas (una captura con #ancla sale en blanco en
  headless), y se revisa el HTML: sin clase «oculto», cada pestaña es un ancla con su sección.
- Sale con código 1 si hubo errores de JS, capturas que no se escribieron o fallas del chequeo sin JS.
"""
import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

EDGES = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
         r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]

CAPTURADOR = r"""<script>/* probar_visor: capturador de errores */
(function(){window.__errores=[];
function reg(m){m=String(m);window.__errores.push(m);try{console.log('VISOR_ERR '+m);}catch(e){}
document.title='ERRORES('+window.__errores.length+') '+m;
var d=document.getElementById('__errores');
if(!d){d=document.createElement('div');d.id='__errores';d.style.cssText='position:fixed;left:0;right:0;bottom:0;z-index:99999;background:#b3261e;color:#fff;font:13px/1.35 monospace;padding:8px;white-space:pre-wrap';(document.body||document.documentElement).appendChild(d);}
d.textContent=window.__errores.join('\n');}
window.addEventListener('error',function(e){var t=e.target;
if(t&&t!==window&&(t.src||t.href)){var u=String(t.src||t.href);
if(/^https?:/.test(u)||t.tagName==='SCRIPT')reg('no cargó: '+u);else console.log('VISOR_RECURSO '+u);return;}
reg((e.message||'error')+' @'+String(e.filename||'').split('/').pop()+':'+(e.lineno||''));},true);
window.addEventListener('unhandledrejection',function(e){reg('promesa: '+(e.reason&&e.reason.message||e.reason));});
var ce=console.error;console.error=function(){reg('console.error: '+[].map.call(arguments,function(x){return x&&x.stack||x;}).join(' '));return ce.apply(console,arguments);};
})();</script>
"""

ACCION = r"""<script>/* probar_visor: acción automática según la URL */
(function(){var q=new URLSearchParams(location.search),n=0;
function informar(extra){var st={};try{st=window.__visor3d?window.__visor3d.estado():{};}catch(e){st={error:String(e)};}
var t=document.querySelector('.tab.activo');st.pestana=t?t.dataset.tab:null;st.errores=(window.__errores||[]).length;
st.falla=window.__falla3d||null;st.ancho=window.innerWidth;st.extra=extra||null;console.log('VISOR_LISTO '+JSON.stringify(st));}
function acciones(){try{
var tema=q.get('tema');if(tema&&document.documentElement.dataset.theme!==tema){var b=document.getElementById('btn-tema');if(b)b.click();}
if(q.get('modo')&&window.__modo3d)window.__modo3d(q.get('modo'));
if(q.get('vista')&&window.__visor3d)window.__visor3d.vista(q.get('vista'));
if(q.get('flujo')&&window.__visor3d)window.__visor3d.flujo(q.get('flujo'));
if(window.__avanzar)window.__avanzar(parseFloat(q.get('avanzar')||'0.05'));
if(window.__visor3d)window.__visor3d.congelar(true);
var tab=q.get('tab');if(tab){var a=document.querySelector('.tab[data-tab="'+tab+'"]');if(a)a.click();window.scrollTo(0,0);}
else{var st=document.getElementById('stage');if(st){var r=st.getBoundingClientRect();if(r.bottom>window.innerHeight)window.scrollBy(0,r.bottom-window.innerHeight+8);}}
setTimeout(function(){informar();},500);
}catch(e){console.error('probar_visor: '+(e&&e.stack||e));informar('excepcion');}}
(function esperar(){if(window.__listo3d||window.__falla3d||n++>250)acciones();else setTimeout(esperar,100);})();
})();</script>
"""

RE_CONSOLA = re.compile(r'CONSOLE[^\]]*\] "(.*)", source: (\S+)')


def buscar_edge(ruta):
    for e in ([ruta] if ruta else []) + EDGES:
        if e and os.path.exists(e):
            return e
    sys.exit("No encontré msedge.exe; páselo con --edge")


def leer_config(html):
    m = re.search(r'<script id="config-visor" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        sys.exit("El archivo no parece un visor armado (falta el script config-visor)")
    return json.loads(m.group(1))


def copia_de_prueba(html, destino):
    vp = re.search(r'<meta name="viewport"[^>]*>\n', html)
    if vp:
        html = html[:vp.end()] + CAPTURADOR + html[vp.end():]
    else:
        html = CAPTURADOR + html
    html = html.rstrip() + "\n" + ACCION
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


def envoltorio(carpeta, nombre, src, alto, ancho=375, desplazar=0):
    """Página con un iframe del ancho pedido. Con desplazar > 0 el iframe sube esos px: así se captura
    más abajo de la página sin anclas ni scroll (las capturas headless con #ancla salen en blanco y las
    ventanas de más de ~8000 px repiten contenido)."""
    ruta = os.path.join(carpeta, f"__angosto_{nombre}.html")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('<meta charset="utf-8"><style>html,body{margin:0;background:#777;overflow:hidden}'
                f'iframe{{border:0;width:{ancho}px;height:{alto}px;display:block;background:#fff;margin-top:-{desplazar}px}}</style>'
                f'<iframe src="{src}"></iframe>')
    return ruta


def correr(edge, url, png, ancho, alto, presupuesto, sin_js=False, recorte=None):
    perfil = tempfile.mkdtemp(prefix="visor3d_edge_")
    if sin_js:
        os.makedirs(os.path.join(perfil, "Default"), exist_ok=True)
        with open(os.path.join(perfil, "Default", "Preferences"), "w", encoding="utf-8") as f:
            json.dump({"profile": {"default_content_setting_values": {"javascript": 2}}}, f)
    if os.path.exists(png):
        os.remove(png)
    cmd = [edge, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
           f"--virtual-time-budget={presupuesto}", f"--screenshot={png}", f"--window-size={ancho},{alto}",
           f"--user-data-dir={perfil}", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
           "--disable-extensions", "--enable-logging=stderr", "--v=0", url]
    t0 = time.time()
    res = {"png": png, "errores": [], "recursos": [], "estado": None, "segundos": 0}
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        salida = r.stderr or ""
    except subprocess.TimeoutExpired:
        salida = ""
        res["errores"].append("Edge no terminó en 240 s")
    finally:
        shutil.rmtree(perfil, ignore_errors=True)
    res["segundos"] = round(time.time() - t0, 1)
    vistos = set()
    for linea in salida.splitlines():
        m = RE_CONSOLA.search(linea)
        if not m or not m.group(2).startswith("file:") or "__angosto_" in m.group(2):
            continue
        msg = m.group(1)
        if msg.startswith("VISOR_LISTO "):
            try:
                res["estado"] = json.loads(msg[len("VISOR_LISTO "):])
            except ValueError:
                res["errores"].append("estado ilegible: " + msg[:120])
        elif msg.startswith("VISOR_ERR "):
            vistos.add(msg[len("VISOR_ERR "):])
        elif msg.startswith("VISOR_RECURSO "):
            res["recursos"].append(msg[len("VISOR_RECURSO "):].rsplit("/", 1)[-1])
        elif "Uncaught" in msg:
            if not any(msg.split(":", 1)[-1].strip()[:40] in v for v in vistos):
                vistos.add(msg)
    res["errores"] += sorted(vistos)
    if not os.path.exists(png) or os.path.getsize(png) == 0:
        res["errores"].append("no se escribió la captura (¿Edge lanzado desde el Bash tool? use PowerShell)")
    elif recorte:
        try:
            from PIL import Image
            with Image.open(png) as im:
                im.crop((0, 0, min(recorte[0], im.width), min(recorte[1], im.height))).save(png)
        except Exception:
            pass   # sin Pillow queda la captura completa
    elif alto > 3000:
        res["tajadas"] = tajadas(png)
    return res


def tajadas(png, alto=1800):
    """Corta una captura muy alta en tajadas legibles y descarta el fondo vacío del final."""
    try:
        from PIL import Image
    except ImportError:
        return [png]
    out = []
    with Image.open(png) as im:
        im = im.convert("RGB")
        fondo = im.getpixel((im.width - 2, im.height - 2))
        for i, y in enumerate(range(0, im.height, alto)):
            t = im.crop((0, y, im.width, min(im.height, y + alto)))
            if t.getcolors(4) and len(t.getcolors(4)) == 1 and t.getpixel((0, 0)) == fondo:
                break   # solo fondo: se acabó la página
            ruta = png.replace(".png", f"_{i + 1}.png")
            t.save(ruta)
            out.append(ruta)
    os.remove(png)
    return out


def chequeo_sin_js(html):
    fallas = []
    if re.search(r'class="[^"]*\boculto\b', html):
        fallas.append("el HTML trae la clase «oculto» (sin JS se perdería contenido)")
    tabs = re.findall(r'<a class="tab[^"]*" data-tab="([^"]+)" href="#panel-([^"]+)"', html)
    if not tabs:
        fallas.append("no hay pestañas como anclas <a href=\"#panel-…\">")
    for a, b in tabs:
        if a != b or f'id="panel-{b}"' not in html:
            fallas.append(f"la pestaña «{a}» no tiene su sección id=panel-{b}")
    if "<noscript>" not in html:
        fallas.append("falta el bloque <noscript> de Explorar")
    if not html.startswith('<meta charset="utf-8">'):
        fallas.append("la primera línea no es <meta charset=\"utf-8\">")
    return fallas, [a for a, _ in tabs]


def main():
    ap = argparse.ArgumentParser(description="Capturas headless y errores de JS de un visor 3D armado.")
    ap.add_argument("--visor", required=True, help="el .html armado con armar_visor.py")
    ap.add_argument("--salida", required=True, help="carpeta para las capturas y el resumen")
    ap.add_argument("--edge", help="ruta de msedge.exe")
    ap.add_argument("--modos", help="lista de modos separados por coma (por defecto, todos)")
    ap.add_argument("--rapido", action="store_true", help="solo el modo inicial (claro y oscuro, escritorio y angosto) y sin JS")
    ap.add_argument("--sin-flujos", action="store_true")
    ap.add_argument("--sin-pestanas", action="store_true")
    ap.add_argument("--sin-nojs", action="store_true")
    ap.add_argument("--presupuesto", type=int, default=15000, help="virtual-time-budget en ms (15000)")
    ap.add_argument("--paralelo", type=int, default=3)
    a = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass

    edge = buscar_edge(a.edge)
    out = os.path.abspath(a.salida)
    os.makedirs(out, exist_ok=True)
    with open(a.visor, encoding="utf-8") as f:
        html = f.read()
    cfg = leer_config(html)
    prueba = os.path.join(out, "__prueba.html")
    copia_de_prueba(html, prueba)
    original = os.path.join(out, "__original.html")
    shutil.copyfile(a.visor, original)

    modos = [m for m in cfg.get("modos") or [] if isinstance(m, dict) and m.get("id")]
    inicial = cfg.get("modo_inicial") or next((m["id"] for m in modos if not m.get("modulo")), None)
    if a.modos:
        pedidos = [x.strip() for x in a.modos.split(",") if x.strip()]
        modos = [m for m in modos if m["id"] in pedidos]
    seg = float(cfg.get("seg_etapa") or 6.5)
    secs = cfg.get("secuencias") or {}
    casos = []   # (nombre, query, ancho, alto, sin_js, ancla)

    def caso(nombre, q, ancho="escritorio", alto=None, sin_js=False, ancla=""):
        casos.append((nombre, dict(q), ancho, alto, sin_js, ancla))

    for ancho in ("escritorio", "angosto"):
        caso("base_claro", {"tema": "light"}, ancho)
        caso("base_oscuro", {"tema": "dark"}, ancho)
    if not a.rapido:
        for m in modos:
            if m["id"] == inicial:
                continue
            q = {"modo": m["id"], "avanzar": "1"}
            if m.get("modulo") == "etapas":
                q["avanzar"] = "0.5"
            for ancho in ("escritorio", "angosto"):
                caso(f"modo_{m['id']}", q, ancho)
            if m.get("modulo") == "etapas":
                n = len(secs.get(m.get("secuencia"), []) or [])
                if n > 1:   # 3 s dentro de la última etapa: las escalas ya terminaron de animarse
                    caso(f"modo_{m['id']}_ultima", {"modo": m["id"], "avanzar": f"{seg * (n - 1) + 3:.2f}"})
        if cfg.get("flujo") and not a.sin_flujos:
            for tipo, t in (("liquido", "20"), ("solido", "30")):
                caso(f"flujo_{tipo}", {"flujo": tipo, "avanzar": t})
                for m in modos:
                    if m.get("modulo") == "normal":
                        caso(f"flujo_{tipo}_{m['id']}", {"modo": m["id"], "flujo": tipo, "avanzar": t})
            ops = (cfg.get("reseccion") or {}).get("opciones") or {}
            for m in modos:
                if m.get("modulo") == "reseccion" and m.get("fase") == "queda" and (ops.get(m.get("opcion")) or {}).get("post_ruta"):
                    caso(f"flujo_post_{m['id']}", {"modo": m["id"], "flujo": "liquido", "avanzar": "10"})
    fallas_nojs, pestanas = chequeo_sin_js(html)
    if not a.sin_pestanas and not a.rapido:
        for i, p in enumerate(pestanas):
            if p == "explorar":
                continue
            caso(f"pestana_{p}", {"tab": p, "tema": "dark" if i == 1 else "light"}, "angosto", 1900)
    if not a.sin_nojs:
        # Página completa sin JS, por ventanas de 6000 px (iframe desplazado), cortada en tajadas legibles.
        # Las anclas se validan en chequeo_sin_js.
        for k in range(4):
            caso(f"sinjs_p{k + 1}", {}, "pagina", 6000 * k, True)
        caso("sinjs_arriba", {}, "angosto", 1600, True)

    def ejecutar(i_caso):
        i, (nombre, q, ancho, alto, sin_js, ancla) = i_caso
        base = "__original.html" if sin_js else "__prueba.html"
        consulta = "" if sin_js else "?" + "&".join(f"{k}={v}" for k, v in q.items())
        png = os.path.join(out, f"{i:02d}_{nombre}_{ancho}.png")
        if ancho == "escritorio":
            url = pathlib.Path(os.path.join(out, base)).as_uri() + consulta + ancla
            r = correr(edge, url, png, 1280, alto or 960, a.presupuesto, sin_js)
        elif ancho == "pagina":   # tramo de la página completa: alto = desplazamiento
            env = envoltorio(out, f"{i:02d}", base + consulta, 6000 + alto, 1280, alto)
            r = correr(edge, pathlib.Path(env).as_uri(), png, 1280, 6000, a.presupuesto, sin_js)
        else:
            h = alto or 812
            env = envoltorio(out, f"{i:02d}", base + consulta + ancla, h)
            r = correr(edge, pathlib.Path(env).as_uri(), png, 520, h + 8, a.presupuesto, sin_js, recorte=(375, h))
        r["nombre"], r["ancho"], r["sin_js"] = nombre, ancho, sin_js
        return r

    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=max(1, a.paralelo)) as ex:
        resultados = list(ex.map(ejecutar, enumerate(casos, 1)))
    for f in os.listdir(out):
        if f.startswith("__angosto_"):
            os.remove(os.path.join(out, f))

    malos = 0
    recursos = sorted({x for r in resultados for x in r["recursos"]})
    print(f"{'captura':44s} {'err':>3s}  estado")
    for r in resultados:
        st = r["estado"] or {}
        if r["sin_js"]:
            desc = "sin JS"
        elif st:
            desc = (f"modo={st.get('modo')} etapa={st.get('etapa')} flujo={st.get('flujo')} puntos={st.get('puntos')} "
                    f"tema={st.get('tema')} ancho={st.get('ancho')} · {str(st.get('leyenda') or '')[:70]}")
            if st.get("falla"):
                r["errores"].append(f"el visor no cargó el 3D: {st.get('falla')}")
        else:
            desc = "SIN ESTADO (la acción automática no informó)"
            r["errores"].append("sin línea VISOR_LISTO")
        malos += len(r["errores"])
        if r.get("tajadas"):
            desc += f" · {len(r['tajadas'])} tajadas (_1 … _{len(r['tajadas'])})"
        print(f"{os.path.basename(r['png']):44s} {len(r['errores']):>3d}  {desc}")
        for e in r["errores"]:
            print(f"{'':49s}! {e[:220]}")
    print(f"\n{len(resultados)} capturas en {out} ({time.time() - t0:.0f} s)")
    if recursos:
        print("Aviso: archivos locales que no cargaron junto a la copia de prueba (normal para los MP4 que viajan aparte):",
              ", ".join(recursos))
    if fallas_nojs:
        print("Chequeo sin JS: FALLA")
        for f in fallas_nojs:
            print("  !", f)
    else:
        print(f"Chequeo sin JS: ok ({len(pestanas)} pestañas como anclas, cada una con su sección; sin «oculto» en el HTML)")
    with open(os.path.join(out, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump({"visor": os.path.abspath(a.visor), "resultados": resultados, "sin_js": fallas_nojs}, f, ensure_ascii=False, indent=1)
    total = malos + len(fallas_nojs)
    print("RESULTADO:", "sin errores" if total == 0 else f"{total} problema(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
