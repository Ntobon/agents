"""Identifica en qué perfiles del navegador está instalada la extensión del agente y, si se pide,
abre el navegador con un perfil concreto para que la extensión se conecte.

Por qué existe: la herramienta de navegador solo ve "Browser 1", "Browser 2"... — nombres que no
dicen de quién es cada perfil. Este script responde desde el disco: qué perfiles hay, qué cuenta
tiene cada uno y cuáles tienen la extensión.

Privacidad: lee ÚNICAMENTE el nombre y la cuenta de cada perfil (archivo "Local State") y la
presencia de la carpeta de la extensión. No abre historial, contraseñas, cookies ni autocompletado.

Uso:
    python perfiles_navegador.py                          # lista los perfiles que tienen la extensión
    python perfiles_navegador.py --todos                  # lista todos los perfiles
    python perfiles_navegador.py --cuenta alguien@correo  # solo el perfil de esa cuenta (sale con 1 si no existe o no tiene la extensión)
    python perfiles_navegador.py --abrir "Profile 7" [--url https://...]   # abre el navegador con ese perfil

Solo Windows (rutas de %LOCALAPPDATA%). --navegador chrome|edge (por defecto chrome).
"""
import argparse
import json
import os
import subprocess
import sys

EXTENSION_POR_DEFECTO = "fcoeoabgfenejglbffodgkkbkcdhcgfn"  # Claude in Chrome

NAVEGADORES = {
    "chrome": (
        os.path.join("Google", "Chrome", "User Data"),
        [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
         r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    ),
    "edge": (
        os.path.join("Microsoft", "Edge", "User Data"),
        [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
         r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"],
    ),
}


def perfiles(base, extension):
    with open(os.path.join(base, "Local State"), encoding="utf-8") as f:
        cache = json.load(f)["profile"]["info_cache"]
    for carpeta, info in sorted(cache.items()):
        yield {
            "carpeta": carpeta,
            "nombre": info.get("name") or "",
            "cuenta": info.get("user_name") or "",
            "extension": os.path.isdir(os.path.join(base, carpeta, "Extensions", extension)),
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--navegador", choices=sorted(NAVEGADORES), default="chrome")
    ap.add_argument("--extension", default=EXTENSION_POR_DEFECTO)
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--cuenta")
    ap.add_argument("--abrir", metavar="CARPETA_DE_PERFIL")
    ap.add_argument("--url", default="about:blank")
    a = ap.parse_args()

    relativa, ejecutables = NAVEGADORES[a.navegador]
    base = os.path.join(os.environ["LOCALAPPDATA"], relativa)

    if a.abrir:
        if not os.path.isdir(os.path.join(base, a.abrir)):
            sys.exit("No existe el perfil " + a.abrir)
        exe = next((e for e in ejecutables if os.path.exists(e)), None)
        if not exe:
            sys.exit("No se encontró el ejecutable de " + a.navegador)
        subprocess.Popen([exe, "--profile-directory=" + a.abrir, a.url])
        print("Abierto", a.navegador, "con el perfil", a.abrir)
        return

    lista = list(perfiles(base, a.extension))
    if a.cuenta:
        lista = [p for p in lista if p["cuenta"].lower() == a.cuenta.lower()]
    elif not a.todos:
        lista = [p for p in lista if p["extension"]]
    for p in lista:
        print("%-12s | %-24s | %-36s | extensión: %s" % (
            p["carpeta"], p["nombre"], p["cuenta"] or "(sin cuenta)", "SÍ" if p["extension"] else "no"))
    if a.cuenta and not any(p["extension"] for p in lista):
        sys.exit(1)


if __name__ == "__main__":
    main()
