"""Stamp "Pág. X de Y" on the footer of every page of a PDF (the merged medical package).

Usage:
    python paginate.py "00 Paquete médico - ... .pdf"          # overwrites the same file
    python paginate.py input.pdf -o output.pdf                  # writes to another file
    python paginate.py input.pdf --label "Patient · paquete médico 2026-09-01"

Why: the clinical summary cites "(anexo N, pág. M)" and the doctor looks for that page on paper;
without a printed number the reference is useless. Stamp AFTER merging and normalizing to portrait
letter, as the very last step, so the numbering matches what the summary cites.

Requires PyMuPDF (pymupdf). Grayscale, Helvetica, bottom-right; optional short label (patient and
date) bottom-left so every loose sheet identifies itself. The stamp text is Spanish on purpose:
the package circulates among Spanish-speaking doctors — change `TEXT` for another locale.
"""
import argparse
import os
import sys

import pymupdf

TEXT = "Pág. {i} de {n}"


def paginate(src: str, dst: str | None = None, label: str | None = None) -> int:
    doc = pymupdf.open(src)
    total = len(doc)
    for i, page in enumerate(doc, start=1):
        rect = page.rect
        y = rect.height - 18  # 18 pt from the bottom edge
        text = TEXT.format(i=i, n=total)
        width = pymupdf.get_text_length(text, fontname="helv", fontsize=8.5)
        x = rect.width - 40 - width
        # White box behind the stamp: scans (CamScanner, letterheads) often carry marks in that corner
        page.draw_rect(pymupdf.Rect(x - 4, y - 9, x + width + 4, y + 4), color=None, fill=(1, 1, 1), overlay=True)
        page.insert_text((x, y), text, fontname="helv", fontsize=8.5, color=(0.25, 0.25, 0.25))
        if label:
            lw = pymupdf.get_text_length(label, fontname="helv", fontsize=8.5)
            page.draw_rect(pymupdf.Rect(36, y - 9, 44 + lw, y + 4), color=None, fill=(1, 1, 1), overlay=True)
            page.insert_text((40, y), label, fontname="helv", fontsize=8.5, color=(0.45, 0.45, 0.45))
    target = dst or src
    if target == src:
        tmp = src + ".tmp"
        doc.save(tmp, garbage=3, deflate=True)
        doc.close()
        os.replace(tmp, src)
    else:
        doc.save(target, garbage=3, deflate=True)
        doc.close()
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description="Number the pages of a PDF (Pág. X de Y).")
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--label", default=None, help="Short text for the bottom-left footer (patient · date)")
    args = ap.parse_args()
    if not os.path.exists(args.input):
        sys.exit(f"Not found: {args.input}")
    n = paginate(args.input, args.output, args.label)
    print(f"Numbered {n} pages -> {args.output or args.input}")


if __name__ == "__main__":
    main()
