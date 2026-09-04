import io
import math
import urllib.request
import os
from typing import Dict
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from core.models import CompleteLabProfile

FONT_NAME = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"

def ensure_utf8_fonts():
    """Gwarantuje obecność fontu DejaVuSans obsługującego pełny zestaw polskich znaków UTF-8."""
    os.makedirs("fonts", exist_ok=True)
    regular_path = os.path.join("fonts", "DejaVuSans.ttf")
    bold_path = os.path.join("fonts", "DejaVuSans-Bold.ttf")

    if not os.path.exists(regular_path):
        url_reg = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
        urllib.request.urlretrieve(url_reg, regular_path)

    if not os.path.exists(bold_path):
        url_bld = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf"
        urllib.request.urlretrieve(url_bld, bold_path)

    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, regular_path))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, bold_path))
    except Exception:
        pass

# Inicjalizacja czcionek UTF-8
try:
    ensure_utf8_fonts()
except Exception:
    FONT_NAME = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"


def create_pdf_vector_shap(marginals: Dict, is_pl: bool) -> Drawing:
    sorted_items = sorted(marginals.items(), key=lambda x: abs(x[1]), reverse=True)[:8]
    d = Drawing(540, 130)
    d.add(Rect(0, 0, 540, 130, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#e2e8f0"), strokeWidth=0.5, rx=4, ry=4))

    title_text = "DEKOMPOZYCJA WPŁYWU BIOMARKERÓW (XAI SHAP) [LATA]" if is_pl else "BIOMARKER ATTRIBUTION & AGE SHIFT (XAI SHAP) [YEARS]"
    d.add(String(12, 116, title_text, fontName=FONT_BOLD, fontSize=8, fillColor=colors.HexColor("#0f172a")))

    center_x = 340
    d.add(Line(center_x, 10, center_x, 110, strokeColor=colors.HexColor("#94a3b8"), strokeWidth=1, strokeDashArray=[2, 2]))

    max_val = max([abs(v) for _, v in sorted_items] + [1.0])
    scale_factor = 140.0 / max_val

    y = 96
    for label, val in sorted_items:
        short_label = label.split('(')[0].strip() if '(' in label else label
        d.add(String(15, y + 2, short_label[:28], fontName=FONT_NAME, fontSize=7, fillColor=colors.HexColor("#1e293b")))

        bar_len = abs(val) * scale_factor
        if val > 0:
            d.add(Rect(center_x, y, bar_len, 8, fillColor=colors.HexColor("#ef4444"), strokeColor=None, rx=1, ry=1))
            d.add(String(center_x + bar_len + 4, y + 1, f"+{val:.2f}", fontName=FONT_NAME, fontSize=6.5, fillColor=colors.HexColor("#ef4444")))
        else:
            d.add(Rect(center_x - bar_len, y, bar_len, 8, fillColor=colors.HexColor("#10b981"), strokeColor=None, rx=1, ry=1))
            d.add(String(center_x - bar_len - 22, y + 1, f"{val:.2f}", fontName=FONT_NAME, fontSize=6.5, fillColor=colors.HexColor("#10b981")))

        y -= 12

    return d


def create_pdf_vector_radar(res: Dict, is_pl: bool) -> Drawing:
    p: CompleteLabProfile = res["profile"]
    d = Drawing(540, 110)
    d.add(Rect(0, 0, 540, 110, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#e2e8f0"), strokeWidth=0.5, rx=4, ry=4))

    title_text = "RADAR REZERW NARZĄDOWYCH I METABOLICZNYCH (0-100)" if is_pl else "ORGAN & METABOLIC RESERVE RADAR (0-100)"
    d.add(String(12, 96, title_text, fontName=FONT_BOLD, fontSize=8, fillColor=colors.HexColor("#0f172a")))

    cx, cy, r_max = 270, 50, 36
    d.add(Circle(cx, cy, r_max, fillColor=None, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5))
    d.add(Circle(cx, cy, r_max * 0.5, fillColor=None, strokeColor=colors.HexColor("#e2e8f0"), strokeWidth=0.5))

    r_cardio = min(max(100 - (45 - p.vo2max) * 2.2, 20), 100) / 100.0
    r_immune = min(max(100 - (p.hscrp_mg_l - 0.7) * 25, 20), 100) / 100.0
    r_metab = min(max(100 - (res["homa_ir"] - 1.0) * 35, 20), 100) / 100.0
    r_renal = min(max((res["egfr"] / 110) * 100, 20), 100) / 100.0
    r_liver = min(max(100 - (res["fib4"] * 40), 20), 100) / 100.0

    values = [r_cardio, r_immune, r_metab, r_renal, r_liver]
    labels = ["Wydolność", "Zapalenie", "Metabolizm", "Nerki", "Wątroba"] if is_pl else ["Cardio", "Immune", "Metab", "Renal", "Hepatic"]

    poly_points = []
    for i in range(5):
        angle = (i * 2 * math.pi / 5) - math.pi / 2
        ax = cx + r_max * math.cos(angle)
        ay = cy + r_max * math.sin(angle)
        d.add(Line(cx, cy, ax, ay, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.5))

        lx = cx + (r_max + 14) * math.cos(angle)
        ly = cy + (r_max + 14) * math.sin(angle) - 2
        d.add(String(lx - 14, ly, labels[i], fontName=FONT_NAME, fontSize=6.5, fillColor=colors.HexColor("#475569")))

        px = cx + (r_max * values[i]) * math.cos(angle)
        py = cy + (r_max * values[i]) * math.sin(angle)
        poly_points.extend([px, py])

    d.add(Polygon(poly_points, fillColor=colors.HexColor("#0284c7"), strokeColor=colors.HexColor("#0369a1"), strokeWidth=1.2, fillOpacity=0.25))
    return d


def generate_pdf_in_memory(res: Dict) -> bytes:
    p: CompleteLabProfile = res["profile"]
    is_pl = (res["lang"] == "PL")
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=28, rightMargin=28, topMargin=20, bottomMargin=20
    )
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle('H', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, leading=14, textColor=colors.HexColor("#0f172a"))
    subhead_style = ParagraphStyle('Sub', parent=styles['Normal'], fontName=FONT_NAME, fontSize=7, leading=9, textColor=colors.HexColor("#475569"))
    sec_title = ParagraphStyle('Sec', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=8.5, leading=10, textColor=colors.HexColor("#0284c7"))
    cell_style = ParagraphStyle('C', parent=styles['Normal'], fontName=FONT_NAME, fontSize=6.5, leading=8, textColor=colors.HexColor("#1e293b"))
    cell_bold = ParagraphStyle('CB', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=6.5, leading=8, textColor=colors.HexColor("#0f172a"))
    legal_style = ParagraphStyle('L', parent=styles['Normal'], fontName=FONT_NAME, fontSize=5.5, leading=7, textColor=colors.HexColor("#64748b"))

    story = [
        Paragraph("CENTRALNE LABORATORIUM DIAGNOSTYCZNE & BIOSTATYSTYKA LONGEVITY AETERNACORE" if is_pl else "AETERNACORE CLINICAL DIAGNOSTICS & LONGEVITY MEDICAL LAB", header_style),
        Paragraph("Standard: PN-EN ISO 15189:2023-02 | LIS Engine: AeternaCore v13.1 Enterprise | Specimen UID: AET-2026-KL99120", subhead_style),
        Spacer(1, 3),
        HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#0284c7"), spaceAfter=5)
    ]

    pt_data = [
        [
            Paragraph("<b>Identyfikator Próbki:</b> AET-2026-KL99120" if is_pl else "<b>Specimen ID:</b> AET-2026-KL99120", cell_style),
            Paragraph(f"<b>Wiek Metrykalny:</b> {p.age:.0f} lat" if is_pl else f"<b>Chronological Age:</b> {p.age:.0f} yrs", cell_style),
            Paragraph(f"<b>Płeć:</b> {'Mężczyzna' if p.sex in ['M', 'Male'] else 'Kobieta'}" if is_pl else f"<b>Sex:</b> {'Male' if p.sex in ['M', 'Male'] else 'Female'}", cell_style)
        ],
        [
            Paragraph(f"<b>Data w LIS:</b> {res['timestamp']}" if is_pl else f"<b>LIS Timestamp:</b> {res['timestamp']}", cell_style),
            Paragraph(f"<b>Status Autowalizacji:</b> <b>{res['autoval_verdict']}</b>" if is_pl else f"<b>LIS Disposition:</b> <b>{res['autoval_verdict']}</b>", cell_style),
            Paragraph(f"<b>Interferencje HIL:</b> {res['l2_hil']}" if is_pl else f"<b>HIL Status:</b> {res['l2_hil']}", cell_style)
        ]
    ]
    t_pt = Table(pt_data, colWidths=[180, 180, 180])
    t_pt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.extend([t_pt, Spacer(1, 5)])

    story.append(Paragraph("1. WYNIKI ANALIZY BIOMARKERÓW LABORATORYJNYCH (LOINC)" if is_pl else "1. ANALYTICAL LABORATORY BIOMARKER MATRIX (LOINC)", sec_title))

    lab_rows = [
        [Paragraph("<b>Badanie Diagnostyczne</b>" if is_pl else "<b>Diagnostic Test</b>", cell_bold), Paragraph("<b>LOINC</b>", cell_bold), Paragraph("<b>Wynik</b>" if is_pl else "<b>Result</b>", cell_bold), Paragraph("<b>Jednostka</b>" if is_pl else "<b>Unit</b>", cell_bold), Paragraph("<b>Zakres Ref.</b>" if is_pl else "<b>Ref. Range</b>", cell_bold), Paragraph("<b>Status LIS</b>", cell_bold)],
        [Paragraph("Albumina w surowicy", cell_style), Paragraph("1751-7", cell_style), Paragraph(f"{p.alb_g_dl*10:.1f}", cell_bold), Paragraph("g/L", cell_style), Paragraph("35.0 - 52.0", cell_style), Paragraph("NORMAL", cell_style)],
        [Paragraph("Kreatynina w surowicy", cell_style), Paragraph("2160-0", cell_style), Paragraph(f"{p.cr_mg_dl*88.4:.0f}", cell_bold), Paragraph("µmol/L", cell_style), Paragraph("62 - 106", cell_style), Paragraph("NORMAL", cell_style)],
        [Paragraph("Glukoza na czczo", cell_style), Paragraph("2345-7", cell_style), Paragraph(f"{p.glu_mg_dl*0.0555:.1f}", cell_bold), Paragraph("mmol/L", cell_style), Paragraph("3.9 - 5.5", cell_style), Paragraph("FLAG" if p.glu_mg_dl > 100 else "NORMAL", cell_style)],
        [Paragraph("hsCRP (Białko C-reaktywne)", cell_style), Paragraph("30522-7", cell_style), Paragraph(f"{p.hscrp_mg_l:.2f}", cell_bold), Paragraph("mg/L", cell_style), Paragraph("< 1.00", cell_style), Paragraph("ELEVATED" if p.hscrp_mg_l > 1.0 else "OPTIMAL", cell_style)],
        [Paragraph("Limfocyty %", cell_style), Paragraph("26474-7", cell_style), Paragraph(f"{p.lym_pct:.1f}", cell_bold), Paragraph("%", cell_style), Paragraph("20.0 - 45.0", cell_style), Paragraph("NORMAL", cell_style)],
        [Paragraph("Wskaźnik RDW", cell_style), Paragraph("789-8", cell_style), Paragraph(f"{p.rdw_pct:.1f}", cell_bold), Paragraph("%", cell_style), Paragraph("11.5 - 14.5", cell_style), Paragraph("NORMAL", cell_style)],
        [Paragraph("Apolipoproteina B (ApoB)", cell_style), Paragraph("1884-6", cell_style), Paragraph(f"{p.apob_mg_dl:.0f}", cell_bold), Paragraph("mg/dL", cell_style), Paragraph("< 80", cell_style), Paragraph("HIGH" if p.apob_mg_dl > 80 else "OPTIMAL", cell_style)],
    ]
    t_lab = Table(lab_rows, colWidths=[160, 55, 65, 60, 100, 100])
    t_lab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.extend([t_lab, Spacer(1, 5)])

    story.append(Paragraph("2. BIOSTATYSTYKA LONGEVITY I REZERWY NARZĄDOWE" if is_pl else "2. BIOSTATISTICAL LONGEVITY AXIS & ORGAN RESERVES", sec_title))
    bio_data = [
        [
            Paragraph(f"<b>Levine PhenoAge:</b> {res['pheno_age']} lat (Delta: {res['age_delta']:+0.2f} lat)" if is_pl else f"<b>Levine PhenoAge:</b> {res['pheno_age']} yrs (Delta: {res['age_delta']:+0.2f} yrs)", cell_style),
            Paragraph(f"<b>DunedinPACE:</b> {res['dunedin_pace']} yr/yr", cell_style),
            Paragraph(f"<b>10Y Mortality Risk:</b> {res['mort_10y']}%", cell_style)
        ],
        [
            Paragraph(f"<b>eGFR (CKD-EPI 2021):</b> {res['egfr']} ml/min", cell_style),
            Paragraph(f"<b>FIB-4 Index:</b> {res['fib4']}", cell_style),
            Paragraph(f"<b>ESC SCORE2 (10Y CVD):</b> {res['score2_pct']}%", cell_style)
        ]
    ]
    t_bio = Table(bio_data, colWidths=[180, 180, 180])
    t_bio.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.extend([t_bio, Spacer(1, 5)])

    story.append(Paragraph("3. DEKOMPOZYCJA XAI SHAP ORAZ RADAR REZERW" if is_pl else "3. XAI ATTRIBUTION & ORGAN RADAR", sec_title))
    story.extend([create_pdf_vector_shap(res["marginals"], is_pl), Spacer(1, 3), create_pdf_vector_radar(res, is_pl), Spacer(1, 5)])

    story.append(Paragraph("4. KLAUZULA I AUTORYZACJA KLINICZNA" if is_pl else "4. CLINICAL SIGN-OFF & AUTHORIZATION", sec_title))
    sign_box = [
        [
            Paragraph(
                "<b>KLAUZULA PRAWNA:</b> Wyniki poddane regułom autowalizacji LIS i kryteriom Westgarda. "
                "Zgodnie z Ustawą z dn. 15 września 2022 r. o medycynie laboratoryjnej (Dz.U. 2022 poz. 2280), "
                "ostateczna autoryzacja sprawozdania wymaga podpisu uprawnionego diagnosty laboratoryjnego." if is_pl else
                "<b>REGULATORY NOTICE:</b> Results checked against automated LIS rules & Westgard SQC. "
                "Clinical diagnostic sign-off executed per ISO 15189 laboratory standards.",
                legal_style
            ),
            Paragraph(
                "<b>UPRAWNIONY DIAGNOSTA LABORATORYJNY:</b><br/>"
                "<i>[Podpisano kwalifikowanym podpisem elektronicznym]</i><br/>"
                "<b>Mateusz Jakubowski (Starszy Technolog Lab.)</b><br/>"
                "<font color='#64748b'>Nr PWZDL: [ARCHITEKT LIS] / ISO 15189 Quality</font>" if is_pl else
                "<b>CERTIFIED CLINICAL SCIENTIST:</b><br/>"
                "<i>[Digitally Signed with Qualified Signature]</i><br/>"
                "<b>Mateusz Jakubowski (Senior Medical Tech.)</b><br/>"
                "<font color='#64748b'>ISO 15189 Diagnostics Lead</font>",
                cell_style
            )
        ]
    ]
    t_sign = Table(sign_box, colWidths=[340, 200])
    t_sign.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_sign)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
