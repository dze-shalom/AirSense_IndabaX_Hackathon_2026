"""utils/pdf_report.py — PDF air quality report generator using ReportLab."""
import io
import math
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#0a192f")
TEAL   = colors.HexColor("#38b2ac")
AMBER  = colors.HexColor("#f59e0b")
RED    = colors.HexColor("#ef4444")
GREEN  = colors.HexColor("#22c55e")
ORANGE = colors.HexColor("#f97316")
PURPLE = colors.HexColor("#8b5cf6")
DARK   = colors.HexColor("#1a0e04")
GREY   = colors.HexColor("#6b7280")
LIGHT  = colors.HexColor("#f3f4f6")
WHITE  = colors.white


def _aqi_color(pm25: float):
    if pm25 < 5:   return GREEN
    if pm25 < 15:  return AMBER
    if pm25 < 30:  return ORANGE
    if pm25 < 60:  return RED
    return PURPLE


def _aqi_label(pm25: float, lang: str) -> str:
    if pm25 < 5:   return "Good"       if lang == "en" else "Bon"
    if pm25 < 15:  return "Moderate"   if lang == "en" else "Modere"
    if pm25 < 30:  return "Poor"       if lang == "en" else "Mauvais"
    if pm25 < 60:  return "Very Poor"  if lang == "en" else "Tres Mauvais"
    return         "Hazardous"         if lang == "en" else "Dangereux"


def _alert_prob(pm25: float) -> float:
    return 1 / (1 + math.exp(-(0.2221 * pm25 - 3.0372)))


def generate_pdf_report(
    city: str,
    region: str,
    pm25: float,
    forecasts: list,
    sources: dict,
    lang: str = "en",
) -> bytes:
    """
    Generate a PDF air quality report and return it as bytes.

    Parameters
    ----------
    city      : city name
    region    : region name
    pm25      : current mean PM2.5 (µg/m³)
    forecasts : list of dicts with keys date, pm25
    sources   : dict of source -> fraction (sums to 1)
    lang      : "en" or "fr"
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    W = A4[0] - 36*mm  # usable width

    # ── Custom styles ─────────────────────────────────────────────────────────
    def sty(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=styles[parent], **kw)

    h_white  = sty("HWhite",  fontSize=18, textColor=WHITE, fontName="Helvetica-Bold", leading=22)
    h_sub    = sty("HSub",    fontSize=10, textColor=colors.HexColor("#ccd6f6"), fontName="Helvetica")
    h1       = sty("H1",      fontSize=13, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=4)
    body     = sty("Body",    fontSize=9,  textColor=DARK, leading=14)
    small    = sty("Small",   fontSize=8,  textColor=GREY)
    badge_g  = sty("BadgeG",  fontSize=11, textColor=WHITE, fontName="Helvetica-Bold", alignment=TA_CENTER)
    footer_s = sty("Footer",  fontSize=7,  textColor=GREY, alignment=TA_CENTER)

    fr = lang == "fr"
    date_str = datetime.now().strftime("%d %B %Y" if fr else "%B %d, %Y")
    prob     = _alert_prob(pm25)
    aqi_col  = _aqi_color(pm25)
    aqi_lbl  = _aqi_label(pm25, lang)
    exceeded = pm25 > 15.0

    elems = []

    # ── Header banner ─────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("AirSense Cameroon", h_white),
        Paragraph(
            f"{'Rapport Qualite de l Air' if fr else 'Air Quality Report'} &mdash; {city}",
            sty("HS2", fontSize=10, textColor=colors.HexColor("#ccd6f6"),
                fontName="Helvetica-Bold", alignment=TA_RIGHT)
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[W * 0.55, W * 0.45])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), NAVY),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    elems.append(header_tbl)

    sub_data = [[
        Paragraph(f"{'Region' if fr else 'Region'}: <b>{region}</b>", sty("Meta", fontSize=8, textColor=GREY)),
        Paragraph(f"{'Genere le' if fr else 'Generated'}: <b>{date_str}</b>",
                  sty("MetaR", fontSize=8, textColor=GREY, alignment=TA_RIGHT)),
    ]]
    sub_tbl = Table(sub_data, colWidths=[W * 0.5, W * 0.5])
    sub_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elems.append(sub_tbl)
    elems.append(HRFlowable(width=W, thickness=1, color=LIGHT))
    elems.append(Spacer(1, 4*mm))

    # ── Current status cards ──────────────────────────────────────────────────
    elems.append(Paragraph("Etat Actuel" if fr else "Current Status", h1))

    who_note = (
        ("Depasse la limite OMS 24h (15 ug/m3)" if exceeded else "Respecte la limite OMS 24h (15 ug/m3)")
        if fr else
        ("Exceeds WHO 24h limit (15 ug/m3)" if exceeded else "Within WHO 24h limit (15 ug/m3)")
    )
    who_col = RED if exceeded else GREEN

    status_data = [
        [
            Paragraph(f"<b>{pm25:.1f}</b><br/><font size=7>ug/m3 PM2.5</font>",
                      sty("PM", fontSize=20, textColor=WHITE, fontName="Helvetica-Bold",
                          alignment=TA_CENTER, leading=24)),
            Paragraph(f"<b>{aqi_lbl}</b><br/><font size=7>{'Niveau IQA' if fr else 'AQI Level'}</font>",
                      sty("AQI", fontSize=16, textColor=WHITE, fontName="Helvetica-Bold",
                          alignment=TA_CENTER, leading=20)),
            Paragraph(f"<b>{prob*100:.0f}%</b><br/><font size=7>{'Prob. alerte' if fr else 'Alert prob.'}</font>",
                      sty("Prob", fontSize=16, textColor=WHITE, fontName="Helvetica-Bold",
                          alignment=TA_CENTER, leading=20)),
        ]
    ]
    status_tbl = Table(status_data, colWidths=[W/3, W/3, W/3])
    status_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), aqi_col),
        ("BACKGROUND",    (1, 0), (1, 0), aqi_col),
        ("BACKGROUND",    (2, 0), (2, 0), RED if prob > 0.7 else AMBER if prob > 0.4 else GREEN),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("GRID",          (0, 0), (-1, -1), 2, WHITE),
    ]))
    elems.append(status_tbl)
    elems.append(Spacer(1, 2*mm))
    elems.append(Paragraph(
        f"{'⚠' if exceeded else '✓'} {who_note}",
        sty("WhoNote", fontSize=8, textColor=who_col, fontName="Helvetica-Bold")
    ))
    elems.append(Spacer(1, 5*mm))

    # ── 7-day forecast ────────────────────────────────────────────────────────
    if forecasts:
        elems.append(HRFlowable(width=W, thickness=0.5, color=LIGHT))
        elems.append(Spacer(1, 3*mm))
        elems.append(Paragraph("Previsions 7 Jours" if fr else "7-Day Forecast", h1))

        fc_header = [
            "Date",
            "PM2.5 (ug/m3)",
            "AQI" if lang == "en" else "IQA",
            "WHO" if lang == "en" else "OMS",
        ]
        fc_rows = [fc_header]
        for p in forecasts[:7]:
            plv = p.get("pm25", 0)
            lbl = _aqi_label(plv, lang)
            who = ("Above" if plv > 15 else "OK") if lang == "en" else ("Depasse" if plv > 15 else "OK")
            fc_rows.append([p.get("date", ""), f"{plv:.1f}", lbl, who])

        fc_tbl = Table(fc_rows, colWidths=[W*0.28, W*0.24, W*0.28, W*0.20])
        fc_style = [
            ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ]
        for i, row in enumerate(fc_rows[1:], 1):
            plv = forecasts[i-1].get("pm25", 0)
            fc_style.append(("TEXTCOLOR", (1, i), (2, i), _aqi_color(plv)))
            fc_style.append(("FONTNAME",  (1, i), (2, i), "Helvetica-Bold"))
            if plv > 15:
                fc_style.append(("TEXTCOLOR", (3, i), (3, i), RED))
                fc_style.append(("FONTNAME",  (3, i), (3, i), "Helvetica-Bold"))

        fc_tbl.setStyle(TableStyle(fc_style))
        elems.append(fc_tbl)
        elems.append(Spacer(1, 5*mm))

    # ── Pollution sources ─────────────────────────────────────────────────────
    if sources:
        elems.append(HRFlowable(width=W, thickness=0.5, color=LIGHT))
        elems.append(Spacer(1, 3*mm))
        elems.append(Paragraph(
            "Sources de Pollution" if fr else "Pollution Sources", h1
        ))

        src_fr = {
            "Dust": "Poussiere saharienne", "Biomass Burning": "Feux de biomasse",
            "Traffic": "Trafic routier", "Industry": "Industrie",
            "Secondary Aerosol": "Aerosol secondaire", "Secondary": "Aerosol secondaire",
            "Other": "Autres",
        }
        src_header = [
            "Source" if lang == "en" else "Source",
            "Part (%)",
            "",  # bar
        ]
        src_rows = [src_header]
        for k, v in sorted(sources.items(), key=lambda x: -x[1]):
            label = src_fr.get(k, k) if fr else k
            bar_pct = f"{'|' * int(v * 40)}"
            src_rows.append([label, f"{v*100:.0f}%", bar_pct])

        src_tbl = Table(src_rows, colWidths=[W*0.42, W*0.16, W*0.42])
        src_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ALIGN",         (1, 0), (1, -1), "CENTER"),
            ("FONTNAME",      (1, 1), (1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR",     (1, 1), (1, -1), TEAL),
            ("FONTNAME",      (2, 1), (2, -1), "Courier"),
            ("TEXTCOLOR",     (2, 1), (2, -1), TEAL),
            ("FONTSIZE",      (2, 1), (2, -1), 7),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ]))
        elems.append(src_tbl)
        elems.append(Spacer(1, 5*mm))

    # ── Health impact ─────────────────────────────────────────────────────────
    elems.append(HRFlowable(width=W, thickness=0.5, color=LIGHT))
    elems.append(Spacer(1, 3*mm))
    elems.append(Paragraph("Impact sur la Sante" if fr else "Health Impact", h1))

    er  = max(0, (pm25 - 10) * 1.04) if pm25 > 10 else 0
    hr  = max(0, (pm25 - 10) * 0.28) if pm25 > 10 else 0
    ld  = max(0, (pm25 - 10) * 0.55) if pm25 > 10 else 0

    if fr:
        health_text = (
            f"Au niveau actuel de PM2.5 ({pm25:.1f} ug/m3) a {city}, on estime :"
            f" <b>{er:.1f} cas respiratoires excedentaires</b> par 10 000 personnes par an,"
            f" un risque d'hospitalisation de <b>{hr:.1f}%</b>,"
            f" et <b>{ld:.1f} journees de travail perdues</b> pour 1 000 personnes."
            f" Les groupes vulnerables (enfants &lt;12 ans, personnes agees, asthmatiques,"
            f" femmes enceintes) sont particulierement exposes."
        )
    else:
        health_text = (
            f"At the current PM2.5 level ({pm25:.1f} ug/m3) in {city}, estimates indicate:"
            f" <b>{er:.1f} excess respiratory cases</b> per 10,000 people per year,"
            f" a hospital admission risk of <b>{hr:.1f}%</b>,"
            f" and <b>{ld:.1f} lost workdays</b> per 1,000 people."
            f" Vulnerable groups (children &lt;12, elderly, asthmatics, pregnant women)"
            f" face elevated exposure risk."
        )
    elems.append(Paragraph(health_text, body))
    elems.append(Spacer(1, 5*mm))

    # ── Recommendations ───────────────────────────────────────────────────────
    elems.append(HRFlowable(width=W, thickness=0.5, color=LIGHT))
    elems.append(Spacer(1, 3*mm))
    elems.append(Paragraph("Recommandations" if fr else "Recommendations", h1))

    level = ("good" if pm25 < 5 else "moderate" if pm25 < 15
             else "poor" if pm25 < 30 else "very_poor" if pm25 < 60 else "hazardous")
    recs_en = {
        "good":      ["No action needed. Air is safe for all groups.",
                      "Good day for outdoor exercise and activities.",
                      "Keep windows open to ventilate indoor spaces."],
        "moderate":  ["Sensitive groups (asthmatics, elderly) should limit strenuous outdoors.",
                      "No mask required for healthy adults.",
                      "Monitor children with respiratory conditions."],
        "poor":      ["Wear a surgical mask for extended outdoor activities.",
                      "Reduce prolonged outdoor exercise.",
                      "Keep windows closed during peak pollution hours (morning rush, evening)."],
        "very_poor": ["Wear an N95/FFP2 mask outdoors at all times.",
                      "Limit outdoor exposure to essential trips only.",
                      "Run air purifiers indoors if available.",
                      "Seek medical attention if experiencing respiratory symptoms."],
        "hazardous": ["Stay indoors — health emergency conditions.",
                      "N95/FFP2 mask mandatory if you must go outside.",
                      "Close all windows and doors.",
                      "Contact health services if symptoms develop."],
    }
    recs_fr = {
        "good":      ["Aucune action requise. L'air est sur pour tous.",
                      "Bonne journee pour les activites physiques exterieures.",
                      "Ouvrez les fenetres pour ventiler les espaces interieurs."],
        "moderate":  ["Les groupes sensibles (asthmatiques, personnes agees) doivent limiter les efforts exterieurs.",
                      "Pas de masque necessaire pour les adultes en bonne sante.",
                      "Surveillez les enfants presentant des problemes respiratoires."],
        "poor":      ["Portez un masque chirurgical pour les activites exterieures prolongees.",
                      "Reduisez l'exercice physique intense a l'exterieur.",
                      "Fermez les fenetres aux heures de pointe (matin et soir)."],
        "very_poor": ["Portez un masque N95/FFP2 en tout temps a l'exterieur.",
                      "Limitez les sorties a l'essentiel uniquement.",
                      "Utilisez un purificateur d'air en interieur si disponible.",
                      "Consultez un medecin si vous presentez des symptomes respiratoires."],
        "hazardous": ["Restez a l'interieur - conditions d'urgence sanitaire.",
                      "Masque N95/FFP2 obligatoire si vous devez sortir.",
                      "Fermez toutes les fenetres et portes.",
                      "Contactez les services de sante si des symptomes apparaissent."],
    }
    recs = recs_fr[level] if fr else recs_en[level]
    for rec in recs:
        elems.append(Paragraph(f"• {rec}", sty("Rec", fontSize=9, textColor=DARK, leftIndent=10, leading=14)))
    elems.append(Spacer(1, 6*mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    elems.append(HRFlowable(width=W, thickness=0.5, color=LIGHT))
    elems.append(Spacer(1, 2*mm))
    footer_txt = (
        f"AirSense Cameroon | IndabaX 2026 | "
        f"{'Donnees' if fr else 'Data'}: CAMS Reanalysis + Open-Meteo | "
        f"{'Modele' if fr else 'Model'}: XGBoost (MAE 6.27 µg/m³, R² 0.603) | "
        f"WHO 2021: 15 µg/m³ (24h)"
    )
    elems.append(Paragraph(footer_txt, footer_s))

    doc.build(elems)
    return buf.getvalue()
