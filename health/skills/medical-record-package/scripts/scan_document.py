# -*- coding: utf-8 -*-
"""
escanear.py — convierte la FOTO de un documento (orden, fórmula, consentimiento)
en una página con aspecto de escaneo, lista para integrar a un paquete médico.

Hace lo mismo que CamScanner: detecta el papel, corrige la perspectiva, aplana la
iluminación y blanquea el fondo, y entrega un PDF en carta VERTICAL (612x792 pt)
con el documento encajado y centrado (los apaisados NO se rotan: se encajan al
ancho, regla del 20-ago-2026). La firma y la papelería quedan intactas — por eso
esta herramienta existe: un documento firmado NUNCA se reemplaza por transcripción.

Uso:
    python escanear.py foto1.jpg [foto2.jpg ...] -o salida.pdf [opciones]

Opciones:
    -o SALIDA.pdf   PDF de salida (obligatorio). Varias fotos = varias páginas.
    --jpg CARPETA   además guarda cada imagen limpia como JPG en esa carpeta.
    --color         conserva el color (por defecto: escala de grises, imprime B/N).
    --sin-recorte   omite la detección de bordes (usa la foto completa).

Requiere: opencv-python-headless, numpy, Pillow (pip install si faltan).
"""
import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

LETTER_W_PT, LETTER_H_PT = 612, 792
DPI = 300
PAGE_W = int(LETTER_W_PT / 72 * DPI)   # 2550 px
PAGE_H = int(LETTER_H_PT / 72 * DPI)   # 3300 px
MARGIN = int(0.35 / 2.54 * DPI)        # ~3.5 mm de margen en página


def _order_corners(pts):
    """Ordena 4 puntos: arriba-izq, arriba-der, abajo-der, abajo-izq."""
    pts = pts.reshape(4, 2).astype(np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)],
                     pts[np.argmax(s)], pts[np.argmax(d)]], dtype=np.float32)


def detect_document(bgr):
    """Busca el contorno cuadrilátero del papel. Devuelve las 4 esquinas o None."""
    h, w = bgr.shape[:2]
    scale = 900.0 / max(h, w)
    small = cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    candidates = []
    # Dos detectores: Canny (bordes) y umbral de brillo (papel claro sobre fondo oscuro)
    edged = cv2.Canny(gray, 40, 120)
    edged = cv2.dilate(edged, np.ones((3, 3), np.uint8), iterations=2)
    candidates.append(edged)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    candidates.append(thresh)
    area_img = small.shape[0] * small.shape[1]
    best, best_area = None, 0
    for mask in candidates:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < 0.30 * area_img or area <= best_area:
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                best, best_area = approx, area
    if best is None:
        return None
    return _order_corners(best) / scale


def warp(bgr, corners):
    """Corrige la perspectiva al rectángulo definido por las esquinas."""
    tl, tr, br, bl = corners
    w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    m = cv2.getPerspectiveTransform(corners, dst)
    return cv2.warpPerspective(bgr, m, (w, h), flags=cv2.INTER_CUBIC)


def scan_effect(bgr, color=False):
    """Aplana la iluminación y blanquea el fondo (el 'efecto escaneado')."""
    def flatten(channel):
        bg = cv2.GaussianBlur(channel, (0, 0), sigmaX=max(channel.shape) / 30)
        norm = cv2.divide(channel, bg, scale=255)
        return norm

    if color:
        canales = [flatten(c) for c in cv2.split(bgr)]
        out = cv2.merge(canales)
    else:
        out = flatten(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
    # Estirar contraste con percentiles para no quemar la tinta
    flat = out.reshape(-1)
    lo, hi = np.percentile(flat, 2), np.percentile(flat, 90)
    hi = max(hi, lo + 1)
    out = np.clip((out.astype(np.float32) - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
    return out


def to_letter_page(img_arr):
    """Monta la imagen escaneada centrada en una página carta vertical (300 dpi)."""
    if img_arr.ndim == 2:
        pil = Image.fromarray(img_arr, mode="L").convert("RGB")
    else:
        pil = Image.fromarray(cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB))
    avail_w, avail_h = PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN
    s = min(avail_w / pil.width, avail_h / pil.height)
    pil = pil.resize((int(pil.width * s), int(pil.height * s)), Image.LANCZOS)
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    page.paste(pil, ((PAGE_W - pil.width) // 2, (PAGE_H - pil.height) // 2))
    return page


def process(path, color=False, crop=True):
    pil = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    if crop:
        corners = detect_document(bgr)
        if corners is not None:
            bgr = warp(bgr, corners)
            print(f"  {os.path.basename(path)}: papel detectado y enderezado")
        else:
            print(f"  {os.path.basename(path)}: sin cuadrilátero claro — se usa la foto completa")
    return scan_effect(bgr, color=color)


def main():
    ap = argparse.ArgumentParser(description="Foto de documento -> PDF con aspecto de escaneo (carta vertical)")
    ap.add_argument("fotos", nargs="+")
    ap.add_argument("-o", "--out", required=True, help="PDF de salida")
    ap.add_argument("--jpg", help="carpeta donde guardar también los JPG limpios")
    ap.add_argument("--color", action="store_true")
    ap.add_argument("--sin-recorte", action="store_true")
    args = ap.parse_args()

    pages = []
    for f in args.fotos:
        arr = process(f, color=args.color, crop=not args.sin_recorte)
        if args.jpg:
            os.makedirs(args.jpg, exist_ok=True)
            base = os.path.splitext(os.path.basename(f))[0]
            Image.fromarray(arr if arr.ndim == 2 else cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)).save(
                os.path.join(args.jpg, base + " (escaneado).jpg"), quality=92)
        pages.append(to_letter_page(arr))

    pages[0].save(args.out, save_all=True, append_images=pages[1:],
                  resolution=DPI, quality=92)
    print(f"OK -> {args.out} ({len(pages)} página(s), carta vertical {LETTER_W_PT}x{LETTER_H_PT} pt)")


if __name__ == "__main__":
    sys.exit(main())
