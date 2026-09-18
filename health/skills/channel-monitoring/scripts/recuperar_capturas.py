"""Recupera como archivos las capturas de pantalla que quedaron en el transcript de una sesión.

Las capturas que toma el agente en el navegador no se guardan en disco: quedan como
bloques de imagen en base64 dentro del .jsonl de la sesión. Este script las extrae.

Uso:
    python recuperar_capturas.py --proyecto "<carpeta de transcripts del proyecto>" --salida "<carpeta>"
        [--sesion <archivo.jsonl>]      # por defecto: el .jsonl modificado más recientemente
        [--desde 2026-01-31T14:00:00]   # solo capturas posteriores (hora UTC del transcript)
        [--ancho-min 1000]              # descarta miniaturas y capturas a escala reducida
        [--solo-usuario]                # solo imágenes pegadas por el usuario (no resultados de herramienta)

Escribe cap_01.jpg, cap_02.png... en orden cronológico e imprime fecha, tamaño y dimensiones
de cada una para poder identificarlas. No sobrescribe: si la carpeta de salida ya tiene
archivos cap_*, continúa la numeración.
"""
import argparse
import base64
import glob
import hashlib
import io
import json
import os
import sys

try:
    from PIL import Image
except ImportError:  # sin Pillow no se pueden medir; se extrae todo
    Image = None


def ultima_sesion(proyecto):
    archivos = glob.glob(os.path.join(proyecto, "*.jsonl"))
    if not archivos:
        sys.exit("No hay transcripts .jsonl en " + proyecto)
    return max(archivos, key=os.path.getmtime)


def es_resultado_de_herramienta(rec):
    msg = rec.get("message")
    contenido = msg.get("content") if isinstance(msg, dict) else None
    return isinstance(contenido, list) and any(
        isinstance(c, dict) and c.get("type") == "tool_result" for c in contenido
    )


def imagenes(obj):
    if isinstance(obj, dict):
        fuente = obj.get("source")
        if obj.get("type") == "image" and isinstance(fuente, dict) and fuente.get("type") == "base64":
            yield fuente.get("media_type", "image/png"), fuente["data"]
            return
        for v in obj.values():
            yield from imagenes(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from imagenes(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proyecto", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--sesion")
    ap.add_argument("--desde", default="")
    ap.add_argument("--ancho-min", type=int, default=0)
    ap.add_argument("--solo-usuario", action="store_true")
    a = ap.parse_args()

    sesion = a.sesion or ultima_sesion(a.proyecto)
    os.makedirs(a.salida, exist_ok=True)
    n = len(glob.glob(os.path.join(a.salida, "cap_*")))
    vistos = set()

    with open(sesion, encoding="utf-8") as f:
        for linea in f:
            try:
                rec = json.loads(linea)
            except ValueError:
                continue
            ts = rec.get("timestamp") or ""
            if a.desde and ts < a.desde:
                continue
            if a.solo_usuario and (rec.get("type") == "assistant" or es_resultado_de_herramienta(rec)):
                continue
            for tipo, b64 in imagenes(rec):
                datos = base64.b64decode(b64)
                huella = hashlib.md5(datos).hexdigest()
                if huella in vistos:
                    continue
                vistos.add(huella)
                dims = ""
                if Image is not None:
                    try:
                        ancho, alto = Image.open(io.BytesIO(datos)).size
                    except Exception:
                        continue
                    if ancho < a.ancho_min:
                        continue
                    dims = "%dx%d" % (ancho, alto)
                n += 1
                ext = tipo.split("/")[-1].replace("jpeg", "jpg")
                destino = os.path.join(a.salida, "cap_%02d.%s" % (n, ext))
                with open(destino, "xb") as out:
                    out.write(datos)
                print(n, ts, dims, len(datos), "bytes ->", os.path.basename(destino))
    print("sesion:", os.path.basename(sesion), "| total:", n)


if __name__ == "__main__":
    main()
