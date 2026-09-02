#!/usr/bin/env python3
"""Generates the synthetic PDFs of the demo family (100% fictional data).

Run from anywhere:  python build_demo_pdfs.py
Output: the PDFs under  ./family/  (already archived per the pattern) and
        ./inbox/  (raw, to be archived live during a demo).

Every page carries a "DOCUMENTO FICTICIO" notice. No real person, lab,
doctor, institution or ID is represented.  Requires: reportlab.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = Path(__file__).resolve().parent
PATIENT = "Jorge Restrepo Vélez"
PATIENT_ID = "CC 00.000.001 (ficticia)"
BIRTH = "12-mar-1955"
NOTICE = ("DOCUMENTO FICTICIO PARA DEMOSTRACIÓN. Paciente, laboratorio, médicos y valores "
          "son inventados. No corresponde a ninguna persona real.")

H = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=15, spaceAfter=4)
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9, textColor=colors.grey, spaceAfter=10)
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14)
SMALL = ParagraphStyle("small", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.grey)
SEC = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=11, spaceBefore=10, spaceAfter=4)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Oblique", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(18 * mm, 12 * mm, NOTICE[:110])
    canvas.drawString(18 * mm, 8.5 * mm, NOTICE[110:])
    canvas.restoreState()


def header_block(institution: str, doc_type: str, date: str, order_no: str):
    return [
        Paragraph(f"{institution}", H),
        Paragraph(f"{doc_type} · Fecha: {date} · N.º {order_no}", SUB),
        Paragraph(f"<b>Paciente:</b> {PATIENT} · <b>Documento:</b> {PATIENT_ID} · "
                  f"<b>Nacimiento:</b> {BIRTH} · <b>Sexo:</b> M", BODY),
        Spacer(1, 8),
    ]


def lab_table(rows):
    data = [["Examen", "Resultado", "Unidad", "Referencia"]] + rows
    t = Table(data, colWidths=[62 * mm, 30 * mm, 28 * mm, 50 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build(path: Path, story):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=22 * mm, title=path.stem)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("ok", path.relative_to(HERE))


def labs(date, order_no, values):
    rows = [
        ["Glucosa en ayunas", values["glu"], "mg/dL", "70 - 100"],
        ["Hemoglobina glicosilada (HbA1c)", values["a1c"], "%", "< 5.7 (control DM: < 7.0)"],
        ["Creatinina", values["crea"], "mg/dL", "0.7 - 1.3"],
        ["Colesterol total", values["col"], "mg/dL", "< 200"],
        ["Colesterol LDL", values["ldl"], "mg/dL", "< 100"],
        ["Colesterol HDL", values["hdl"], "mg/dL", "> 40"],
        ["Triglicéridos", values["tg"], "mg/dL", "< 150"],
        ["Hemoglobina", values["hb"], "g/dL", "13.0 - 17.0"],
        ["Leucocitos", values["wbc"], "x10³/µL", "4.0 - 10.0"],
        ["Plaquetas", values["plt"], "x10³/µL", "150 - 450"],
        ["TSH", values["tsh"], "µUI/mL", "0.4 - 4.0"],
    ]
    story = header_block("Laboratorio Clínico Demo · Sede Centro", "Resultados de laboratorio", date, order_no)
    story += [Paragraph("Muestra: sangre venosa, ayuno de 10 h. Validado por: bacterióloga (ficticia).", SMALL),
              Spacer(1, 6), lab_table(rows), Spacer(1, 10),
              Paragraph("Método: química seca / HPLC para HbA1c. Los valores de referencia son orientativos "
                        "y deben interpretarse por el médico tratante.", SMALL)]
    return story


def main():
    fam = HERE / "family" / "Papá"
    inbox = HERE / "inbox"

    # 1. Labs Nov-2025 (baseline, DM2 uncontrolled)
    build(fam / "06 - Originales" / "2025" / "Resultados_lab_141125.pdf",
          labs("14-nov-2025", "LC-25-08811", dict(glu="132", a1c="7.4", crea="1.1", col="212", ldl="128",
                                                 hdl="41", tg="178", hb="14.2", wbc="6.8", plt="231", tsh="2.1")))

    # 2. Labs May-2026 (improving)
    build(fam / "06 - Originales" / "2026" / "Resultados_lab_200526.pdf",
          labs("20-may-2026", "LC-26-03107", dict(glu="118", a1c="6.9", crea="1.2", col="188", ldl="104",
                                                 hdl="44", tg="151", hb="14.0", wbc="7.1", plt="240", tsh="2.4")))

    # 3. Consult note May-2026
    story = header_block("IPS Demo Salud · Medicina interna", "Nota de consulta externa", "28-may-2026", "HC-26-4410")
    story += [
        Paragraph("Motivo de consulta", SEC),
        Paragraph("Control de diabetes mellitus tipo 2 e hipertensión arterial. Trae laboratorios del 20-may-2026.", BODY),
        Paragraph("Análisis", SEC),
        Paragraph("HbA1c 6.9 % (previa 7.4 % en nov-2025): mejoría con la dosis actual de metformina y cambios en la "
                  "alimentación. LDL 104 mg/dL, aún por encima de la meta de 100 para su riesgo cardiovascular. "
                  "Creatinina 1.2 mg/dL (1.1 previa): leve ascenso, TFG estimada 62 mL/min/1.73 m²; se solicita "
                  "ecografía renal y de vías urinarias para descartar causa estructural. Presión arterial en consulta "
                  "134/82 mmHg.", BODY),
        Paragraph("Diagnósticos", SEC),
        Paragraph("E11.9 Diabetes mellitus tipo 2 sin complicaciones · I10 Hipertensión esencial · E78.5 Hiperlipidemia.", BODY),
        Paragraph("Plan", SEC),
        Paragraph("1. Continuar metformina 850 mg cada 12 h. 2. Continuar losartán 50 mg/día. 3. Aumentar "
                  "atorvastatina a 40 mg/noche. 4. Ecografía renal y de vías urinarias (orden adjunta). "
                  "5. Laboratorios de control en 3 meses: HbA1c, creatinina, perfil lipídico. 6. Control en 3 meses "
                  "con resultados.", BODY),
        Spacer(1, 18),
        Paragraph("________________________<br/>Dra. Ejemplo Pérez · Medicina interna · Registro ficticio 00000", BODY),
    ]
    build(fam / "06 - Originales" / "2026" / "Nota_consulta_280526.pdf", story)

    # 4. Order May-2026 (signed document; in a real case it would circulate as a scan)
    story = header_block("IPS Demo Salud · Medicina interna", "Orden médica", "28-may-2026", "OM-26-9021")
    story += [
        Paragraph("Se ordena", SEC),
        Paragraph("<b>Ecografía renal y de vías urinarias</b> (CUPS ficticio 881302). Prioridad: ordinaria.", BODY),
        Paragraph("Justificación", SEC),
        Paragraph("Ascenso leve de creatinina (1.1 → 1.2 mg/dL) en paciente con DM2 e HTA. Descartar uropatía "
                  "obstructiva o lesión estructural.", BODY),
        Spacer(1, 30),
        Paragraph("________________________<br/>Dra. Ejemplo Pérez · Medicina interna · Registro ficticio 00000", BODY),
    ]
    build(fam / "06 - Originales" / "2026" / "Orden_ecografia_280526.pdf", story)

    # 5. INBOX: labs Aug-2026 (to be archived live)
    build(inbox / "Resultados_lab_200826.pdf",
          labs("20-ago-2026", "LC-26-05590", dict(glu="109", a1c="6.6", crea="1.1", col="171", ldl="92",
                                                 hdl="46", tg="139", hb="14.3", wbc="6.5", plt="228", tsh="2.2")))

    # 6. INBOX: renal ultrasound report Aug-2026 (to be archived live)
    story = header_block("Centro de Imágenes Demo", "Informe de ecografía renal y de vías urinarias", "21-ago-2026", "IMG-26-1170")
    story += [
        Paragraph("Técnica", SEC),
        Paragraph("Exploración en modo B y Doppler color con transductor convexo de 3.5 MHz.", BODY),
        Paragraph("Hallazgos", SEC),
        Paragraph("Riñón derecho de 10.8 cm, contornos regulares, relación corticomedular conservada, sin dilatación "
                  "pielocalicial. Riñón izquierdo de 11.1 cm; en polo superior se observa imagen anecoica de paredes "
                  "finas, sin septos ni calcificaciones, de 1.6 cm, compatible con quiste simple (Bosniak I). "
                  "Vejiga de paredes lisas, sin litiasis. Sin líquido libre.", BODY),
        Paragraph("Conclusión", SEC),
        Paragraph("Quiste simple renal izquierdo de 1.6 cm (Bosniak I), sin significado patológico. Resto del estudio "
                  "dentro de límites normales. No se identifica causa obstructiva.", BODY),
        Spacer(1, 18),
        Paragraph("________________________<br/>Dr. Ejemplo Gómez · Radiología · Registro ficticio 00001", BODY),
    ]
    build(inbox / "Informe_ecografia_renal_210826.pdf", story)


if __name__ == "__main__":
    main()
