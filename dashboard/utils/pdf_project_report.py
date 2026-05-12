"""utils/pdf_project_report.py — AirSense Cameroon stakeholder project report."""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)

from config import (
    CITY_STATS, REGIONS_DATA, MODEL_COMPARISON, MODEL_MAE, MODEL_R2,
    MODEL_RL_F1, WHO_24H, REGION_SHAP_FALLBACK,
)

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#0a192f")
NAVY2  = colors.HexColor("#112240")
TEAL   = colors.HexColor("#64ffda")
TEAL2  = colors.HexColor("#0891b2")
TEXT1  = colors.HexColor("#e6f1ff")
TEXT2  = colors.HexColor("#8892b0")
BORDER = colors.HexColor("#233554")
GREEN  = colors.HexColor("#22c55e")
AMBER  = colors.HexColor("#eab308")
ORANGE = colors.HexColor("#f97316")
RED    = colors.HexColor("#ef4444")
GREY   = colors.HexColor("#6b7280")
LIGHT  = colors.HexColor("#e5e7eb")
WHITE  = colors.white
BLACK  = colors.black

W, H = A4  # 210 × 297 mm


# ── Style helpers ─────────────────────────────────────────────────────────────
def _sty(name, **kw):
    base = ParagraphStyle(name)
    for k, v in kw.items():
        setattr(base, k, v)
    return base


COVER_TITLE = _sty("CoverTitle", fontSize=28, textColor=TEAL,
                   fontName="Helvetica-Bold", alignment=TA_CENTER, leading=36)
COVER_SUB   = _sty("CoverSub",   fontSize=13, textColor=TEXT1,
                   fontName="Helvetica", alignment=TA_CENTER, leading=18)
COVER_META  = _sty("CoverMeta",  fontSize=9,  textColor=TEXT2,
                   fontName="Helvetica", alignment=TA_CENTER, leading=13)
SEC_HDR     = _sty("SecHdr",     fontSize=14, textColor=TEAL,
                   fontName="Helvetica-Bold", alignment=TA_LEFT, leading=20,
                   spaceBefore=4*mm)
BODY        = _sty("Body",       fontSize=9,  textColor=BLACK,
                   fontName="Helvetica", alignment=TA_LEFT, leading=14)
BODY_SM     = _sty("BodySm",     fontSize=8,  textColor=GREY,
                   fontName="Helvetica", alignment=TA_LEFT, leading=12)
BULLET      = _sty("Bullet",     fontSize=9,  textColor=BLACK,
                   fontName="Helvetica", alignment=TA_LEFT, leading=14,
                   leftIndent=10)
TH          = _sty("TH",         fontSize=8,  textColor=WHITE,
                   fontName="Helvetica-Bold", alignment=TA_CENTER, leading=11)
TD          = _sty("TD",         fontSize=8,  textColor=BLACK,
                   fontName="Helvetica", alignment=TA_CENTER, leading=11)
TD_L        = _sty("TDL",        fontSize=8,  textColor=BLACK,
                   fontName="Helvetica", alignment=TA_LEFT, leading=11)
FOOTER_S    = _sty("Footer",     fontSize=7,  textColor=GREY,
                   fontName="Helvetica", alignment=TA_CENTER, leading=10)
KPI_NUM     = _sty("KpiNum",     fontSize=18, textColor=TEAL,
                   fontName="Helvetica-Bold", alignment=TA_CENTER, leading=22)
KPI_LBL     = _sty("KpiLbl",     fontSize=7,  textColor=GREY,
                   fontName="Helvetica", alignment=TA_CENTER, leading=10)


# ── Table style helpers ───────────────────────────────────────────────────────
def _tbl_base(header_rows=1):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), NAVY2),
        ("TEXTCOLOR",  (0, 0), (-1, header_rows - 1), WHITE),
        ("FONTNAME",   (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [WHITE, colors.HexColor("#f9fafb")]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ])


def _kpi_table(items):
    """Horizontal KPI strip: list of (value_str, label_str)."""
    col_w = (W - 40*mm) / max(len(items), 1)
    header = [Paragraph(v, KPI_NUM) for v, _ in items]
    labels = [Paragraph(l, KPI_LBL) for _, l in items]
    t = Table([header, labels], colWidths=[col_w] * len(items))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#d1fae5")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ── Derived data ──────────────────────────────────────────────────────────────
def _region_stats():
    """Return list of (region, mean_pm25, who_exc_pct, n_cities) sorted by pm25 desc."""
    from collections import defaultdict
    acc = defaultdict(list)
    exc = defaultdict(list)
    for city, s in CITY_STATS.items():
        r = s["region"]
        acc[r].append(s["mean_pm25"])
        exc[r].append(s["who_exc"])
    rows = []
    for r in REGIONS_DATA:
        pm = round(sum(acc[r]) / len(acc[r]), 1) if acc[r] else 0
        ex = round(sum(exc[r]) / len(exc[r]), 1) if exc[r] else 0
        rows.append((r, pm, ex, len(acc[r])))
    return sorted(rows, key=lambda x: -x[1])


def _top_cities(n=5, worst=True):
    cities = sorted(CITY_STATS.items(), key=lambda x: x[1]["mean_pm25"], reverse=worst)
    return cities[:n]


def _health_impact(pm25, n_pop_k=100):
    """
    WHO concentration-response: each 10 µg/m³ above 15 → ~6% excess resp. risk.
    Returns (excess_cases_per_10k, hospital_risk_pct, lost_workdays_per_10k).
    """
    excess = max(0.0, (pm25 - WHO_24H) / 10.0) * 6.0
    excess_cases = round(excess * 10, 0)
    hospital_risk = round(min(excess * 0.4, 15), 1)
    lost_days = round(min(excess * 3.5, 80), 0)
    return int(excess_cases), hospital_risk, int(lost_days)


# ── Main generator ────────────────────────────────────────────────────────────
def generate_project_report(lang: str = "en") -> bytes:
    """Generate multi-page stakeholder PDF; returns bytes."""
    fr = (lang == "fr")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm,  bottomMargin=18*mm,
        title="AirSense Cameroon — Project Report",
        author="AirSense IndabaX 2026",
    )
    elems = []
    now   = datetime.now().strftime("%B %d, %Y")

    def hr():
        elems.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT,
                                spaceAfter=3*mm, spaceBefore=1*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    elems.append(Spacer(1, 22*mm))

    # Logo block (coloured rectangle + title)
    logo_data = [[Paragraph("AirSense Cameroon", COVER_TITLE)]]
    logo_tbl = Table(logo_data, colWidths=[W - 40*mm])
    logo_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY2),
        ("BOX",           (0, 0), (-1, -1), 1.5, TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    elems.append(logo_tbl)
    elems.append(Spacer(1, 6*mm))

    elems.append(Paragraph(
        ("Rapport de Projet — Qualité de l'Air au Cameroun" if fr
         else "Project Report — Air Quality Monitoring in Cameroon"),
        COVER_SUB,
    ))
    elems.append(Spacer(1, 3*mm))
    elems.append(Paragraph(
        ("Conférence IndabaX 2026 | Prédiction IA de la qualité de l'air" if fr
         else "IndabaX 2026 Conference | AI-Powered Air Quality Prediction"),
        COVER_META,
    ))
    elems.append(Spacer(1, 14*mm))

    # KPI strip
    all_pm = [s["mean_pm25"] for s in CITY_STATS.values()]
    n_cities = len(CITY_STATS)
    nat_mean  = round(sum(all_pm) / n_cities, 1)
    pct_above = round(sum(1 for v in all_pm if v > WHO_24H) / n_cities * 100, 1)

    kpi_items = [
        (str(n_cities),  ("Villes surveillées" if fr else "Cities Monitored")),
        (f"{nat_mean}",  ("PM2.5 moy. national\n(µg/m³)" if fr else "National Mean\nPM2.5 (µg/m³)")),
        (f"{pct_above}%", ("Villes > OMS" if fr else "Cities > WHO Limit")),
        (f"{MODEL_RL_F1}", ("Score F1\nClassificateur d'alertes" if fr else "F1 Score\nAlert Classifier")),
    ]
    elems.append(_kpi_table(kpi_items))
    elems.append(Spacer(1, 14*mm))

    elems.append(Paragraph(
        ("Généré le " if fr else "Generated: ") + now,
        COVER_META,
    ))
    elems.append(Spacer(1, 2*mm))
    elems.append(Paragraph(
        ("Données: CAMS Réanalyse + ERA5 + Open-Meteo | Modèle: XGBoost + Optuna" if fr
         else "Data: CAMS Reanalysis + ERA5 + Open-Meteo | Model: XGBoost + Optuna"),
        COVER_META,
    ))
    elems.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — PROJECT OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    elems.append(Paragraph(
        "1. Vue d'ensemble du projet" if fr else "1. Project Overview",
        SEC_HDR,
    ))
    hr()

    mission = (
        "AirSense Cameroun est un système de surveillance de la qualité de l'air "
        "basé sur l'intelligence artificielle, couvrant 10 régions et plus de 85 villes "
        "à travers le Cameroun. En combinant des données satellites (CAMS, ERA5), "
        "des facteurs climatiques et des modèles d'apprentissage automatique avancés, "
        "la plateforme fournit des prévisions PM2.5 sur 7 jours, des alertes sanitaires "
        "calibrées et des projections climatiques à horizon 2100 pour soutenir "
        "la prise de décision en matière de santé publique."
        if fr else
        "AirSense Cameroon is an AI-powered air quality monitoring system covering "
        "10 regions and 85+ cities across Cameroon. By combining satellite data "
        "(CAMS, ERA5), climate drivers, and advanced machine learning, the platform "
        "delivers 7-day PM2.5 forecasts, calibrated health alerts, and climate "
        "projections to 2100 — equipping public-health decision-makers with "
        "actionable, real-time intelligence."
    )
    elems.append(Paragraph(mission, BODY))
    elems.append(Spacer(1, 4*mm))

    elems.append(Paragraph(
        "Capacités principales :" if fr else "Core Capabilities:",
        _sty("BoldBody", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    capabilities = [
        ("Prévisions PM2.5 sur 7 jours" if fr else "7-day PM2.5 forecasts",
         "XGBoost + Optuna, intervalles de confiance conformaux 90%"),
        ("Système d'alertes calibré" if fr else "Calibrated alert system",
         "Classificateur Platt, F1=0.847, AUC=0.921"),
        ("Attribution des sources" if fr else "Source attribution",
         "Trafic, industrie, biomasse, poussière, fond"),
        ("Explicabilité SHAP" if fr else "SHAP explainability",
         "Facteurs climatiques par région — Harmattan, précipitations, saison sèche"),
        ("Projections climatiques 2050–2100" if fr else "2050–2100 climate projections",
         "Scénarios CMIP6 SSP1-1.9 → SSP5-8.5"),
        ("Calculateur d'impact sanitaire" if fr else "Health impact calculator",
         "Fonction dose-réponse OMS, cas respiratoires excédentaires"),
    ]
    for cap, desc in capabilities:
        elems.append(Paragraph(
            f"• <b>{cap}</b> — {desc}", BULLET,
        ))
    elems.append(Spacer(1, 4*mm))

    elems.append(Paragraph(
        "Sources de données :" if fr else "Data Sources:",
        _sty("BoldBody2", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    src_hdr = [
        Paragraph("Source", TH),
        Paragraph("Type", TH),
        Paragraph(("Variables clés" if fr else "Key Variables"), TH),
        Paragraph("Résolution" if fr else "Resolution", TH),
    ]
    src_rows = [
        ["CAMS Reanalysis", "Satellite", "PM2.5, PM10, NO₂, SO₂, O₃, AOD", "0.1° / 6h"],
        ["ERA5 (ECMWF)", "Reanalysis", "Temp, Humidity, Wind, Pressure", "0.25° / 1h"],
        ["Open-Meteo", "NWP / Archive", "7-day forecast, historical", "~10 km / 1h"],
        ["Proxy stations", "Validated", "Ground truth PM2.5 calibration", "City-level"],
    ]
    src_data = [src_hdr] + [
        [Paragraph(c, TD_L if i == 0 else TD) for i, c in enumerate(r)]
        for r in src_rows
    ]
    src_tbl = Table(src_data, colWidths=[45*mm, 32*mm, 72*mm, 30*mm])
    src_tbl.setStyle(_tbl_base())
    elems.append(src_tbl)
    elems.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — AIR QUALITY STATISTICS
    # ══════════════════════════════════════════════════════════════════════════
    elems.append(Paragraph(
        "2. Statistiques sur la qualité de l'air" if fr else "2. Air Quality Statistics",
        SEC_HDR,
    ))
    hr()

    elems.append(Paragraph(
        (f"L'analyse porte sur {n_cities} villes dans 10 régions. "
         f"{pct_above}% des villes dépassent régulièrement la limite OMS 2021 de "
         f"15 µg/m³ sur 24h. La région Extrême-Nord enregistre les concentrations "
         "les plus élevées, amplifiées par les épisodes de poussière Harmattan en "
         "saison sèche (novembre–février)."
         if fr else
         f"Analysis covers {n_cities} cities across 10 regions. "
         f"{pct_above}% of cities regularly exceed the WHO 2021 24-h PM2.5 guideline "
         f"of 15 µg/m³. The Far North region records the highest concentrations, "
         "amplified by Harmattan dust events during the dry season (November–February)."),
        BODY,
    ))
    elems.append(Spacer(1, 4*mm))

    elems.append(Paragraph(
        "Résumé régional PM2.5 :" if fr else "Regional PM2.5 Summary:",
        _sty("BoldBody3", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    reg_stats = _region_stats()
    reg_hdr = [
        Paragraph("Région" if fr else "Region", TH),
        Paragraph(("PM2.5 moy.\n(µg/m³)" if fr else "Mean PM2.5\n(µg/m³)"), TH),
        Paragraph(("Dépassement\nOMS (%)" if fr else "WHO Exceedance\n(%)"), TH),
        Paragraph("Villes" if fr else "Cities", TH),
        Paragraph("Statut" if fr else "Status", TH),
    ]
    reg_data = [reg_hdr]
    for r, pm, ex, nc in reg_stats:
        status_en = "Above WHO" if pm > WHO_24H else "Near WHO" if pm > 12 else "Below WHO"
        status_fr = "Au-dessus OMS" if pm > WHO_24H else "Proche OMS" if pm > 12 else "Sous OMS"
        status = status_fr if fr else status_en
        reg_data.append([
            Paragraph(r, TD_L),
            Paragraph(str(pm), TD),
            Paragraph(f"{ex}%", TD),
            Paragraph(str(nc), TD),
            Paragraph(status, TD),
        ])
    reg_tbl = Table(reg_data, colWidths=[42*mm, 30*mm, 35*mm, 22*mm, 35*mm + 16*mm])
    reg_style = _tbl_base()
    for i, (_, pm, _, _) in enumerate(reg_stats, start=1):
        clr = RED if pm > 25 else ORANGE if pm > 20 else AMBER if pm > WHO_24H else GREEN
        reg_style.add("TEXTCOLOR", (1, i), (1, i), clr)
        reg_style.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")
    reg_tbl.setStyle(reg_style)
    elems.append(reg_tbl)
    elems.append(Spacer(1, 5*mm))

    # Top 5 most polluted and cleanest side by side
    elems.append(Paragraph(
        "Villes les plus et les moins polluées :" if fr else "Most and Least Polluted Cities:",
        _sty("BoldBody4", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    worst5  = _top_cities(5, worst=True)
    best5   = _top_cities(5, worst=False)

    city_hdr_w = [
        Paragraph(("Ville (polluée)" if fr else "City (Most Polluted)"), TH),
        Paragraph("PM2.5", TH),
        Paragraph(("Exc. OMS" if fr else "WHO Exc."), TH),
    ]
    city_hdr_b = [
        Paragraph(("Ville (propre)" if fr else "City (Cleanest)"), TH),
        Paragraph("PM2.5", TH),
        Paragraph(("Exc. OMS" if fr else "WHO Exc."), TH),
    ]

    def city_rows(lst):
        rows = []
        for city, s in lst:
            rows.append([
                Paragraph(city, TD_L),
                Paragraph(str(s["mean_pm25"]), TD),
                Paragraph(f"{s['who_exc']}%", TD),
            ])
        return rows

    worst_data = [city_hdr_w] + city_rows(worst5)
    best_data  = [city_hdr_b] + city_rows(best5)

    worst_tbl = Table(worst_data, colWidths=[38*mm, 18*mm, 18*mm])
    worst_tbl.setStyle(_tbl_base())
    best_tbl  = Table(best_data,  colWidths=[38*mm, 18*mm, 18*mm])
    best_tbl.setStyle(_tbl_base())

    pair = Table([[worst_tbl, Spacer(6*mm, 1), best_tbl]],
                 colWidths=[(38+18+18)*mm, 6*mm, (38+18+18)*mm])
    pair.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elems.append(pair)
    elems.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 — ML MODEL PERFORMANCE
    # ══════════════════════════════════════════════════════════════════════════
    elems.append(Paragraph(
        "3. Performance du modèle ML" if fr else "3. ML Model Performance",
        SEC_HDR,
    ))
    hr()

    ml_kpis = [
        (f"{MODEL_MAE} µg/m³", ("MAE final\n(PM2.5)" if fr else "Final MAE\n(PM2.5)")),
        (f"{MODEL_R2}",        ("R² final\n(PM2.5)" if fr else "Final R²\n(PM2.5)")),
        (f"{MODEL_RL_F1}",     ("F1 Score\n(Alertes)" if fr else "F1 Score\n(Alerts)")),
        ("0.921",              ("AUC-ROC\n(Alertes)" if fr else "AUC-ROC\n(Alerts)")),
    ]
    elems.append(_kpi_table(ml_kpis))
    elems.append(Spacer(1, 4*mm))

    elems.append(Paragraph(
        "Comparaison des modèles :" if fr else "Model Comparison:",
        _sty("BoldBody5", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    mc_hdr = [
        Paragraph("Modèle" if fr else "Model", TH),
        Paragraph("MAE (µg/m³)", TH),
        Paragraph("R²", TH),
        Paragraph("Type", TH),
    ]
    _type_map = {
        "baseline": ("Référence" if fr else "Baseline"),
        "primary":  ("Principal" if fr else "Primary"),
        "ensemble": "Ensemble",
        "deep":     ("Profond" if fr else "Deep Learning"),
    }
    mc_data = [mc_hdr]
    for m in MODEL_COMPARISON:
        if m["mae"] is None:
            continue
        mc_data.append([
            Paragraph(m["model"], TD_L),
            Paragraph(f"{m['mae']:.3f}", TD),
            Paragraph(f"{m['r2']:.3f}", TD),
            Paragraph(_type_map.get(m["flag"], m["flag"]), TD),
        ])
    mc_tbl = Table(mc_data, colWidths=[80*mm, 30*mm, 20*mm, 40*mm + 10*mm])
    mc_style = _tbl_base()
    # Highlight best row (XGBoost + Optuna)
    for i, m in enumerate([x for x in MODEL_COMPARISON if x["mae"] is not None], start=1):
        if m["flag"] == "primary" and "Optuna" in m["model"]:
            mc_style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f0fdf4"))
            mc_style.add("FONTNAME",   (0, i), (-1, i), "Helvetica-Bold")
    mc_tbl.setStyle(mc_style)
    elems.append(mc_tbl)
    elems.append(Spacer(1, 4*mm))

    # Top SHAP features
    elems.append(Paragraph(
        "Principaux facteurs SHAP (moyenne nationale) :" if fr
        else "Top SHAP Features (national average):",
        _sty("BoldBody6", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    from collections import Counter
    feat_counts: Counter = Counter()
    for region_feats in REGION_SHAP_FALLBACK.values():
        for feat, val in region_feats:
            feat_counts[feat] += val
    top_feats = feat_counts.most_common(6)

    shap_desc = {
        "year":             ("Tendance multi-année 2020–2025" if fr else "Multi-year trend 2020–2025"),
        "precipitation":    ("Précipitations — lessivage des particules" if fr else "Rainfall — particle washout"),
        "daylight_duration": ("Durée d'ensoleillement — mélange convectif saisonnier" if fr
                              else "Daylight hours — seasonal convective mixing"),
        "is_dust_event":    ("Épisode de poussière — extrêmes Harmattan" if fr
                             else "Dust storm flag — Harmattan extremes"),
        "latitude":         ("Latitude — gradient N–S de pollution" if fr
                             else "Latitude — North–South pollution gradient"),
        "humidity":         ("Humidité — croissance hygroscopique / précurseur Harmattan" if fr
                             else "Humidity — hygroscopic growth / Harmattan precursor"),
        "region_enc":       ("Encodage région — activité de combustion" if fr
                             else "Region encoding — burning activity"),
        "surface_pressure": ("Pression atmosphérique — inversions de piégeage" if fr
                             else "Atmospheric pressure — particle trapping inversions"),
        "month_sin":        ("Encodage cyclique du mois — signal saisonnier" if fr
                             else "Cyclic month encoding — seasonal signal"),
        "day_of_year":      ("Jour de l'année — signal saisonnier continu" if fr
                             else "Day of year — continuous seasonal signal"),
    }

    shp_hdr = [
        Paragraph(("Facteur" if fr else "Feature"), TH),
        Paragraph("SHAP (sum)", TH),
        Paragraph("Description", TH),
    ]
    shp_data = [shp_hdr]
    for feat, val in top_feats:
        shp_data.append([
            Paragraph(feat, TD_L),
            Paragraph(f"{val:.2f}", TD),
            Paragraph(shap_desc.get(feat, feat), TD_L),
        ])
    shp_tbl = Table(shp_data, colWidths=[40*mm, 22*mm, 118*mm])
    shp_tbl.setStyle(_tbl_base())
    elems.append(shp_tbl)
    elems.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5 — HEALTH IMPACT ESTIMATES
    # ══════════════════════════════════════════════════════════════════════════
    elems.append(Paragraph(
        "4. Estimations de l'impact sanitaire" if fr else "4. Health Impact Estimates",
        SEC_HDR,
    ))
    hr()

    elems.append(Paragraph(
        ("Les estimations suivantes utilisent la fonction concentration-réponse de l'OMS. "
         "Chaque augmentation de 10 µg/m³ au-dessus de la limite OMS (15 µg/m³) est "
         "associée à une augmentation d'environ 6% des cas respiratoires excédentaires. "
         "Ces projections sont indicatives et supposent une population exposée de "
         "100 000 personnes par région."
         if fr else
         "The following estimates use the WHO concentration-response function. "
         "Each 10 µg/m³ increase above the WHO guideline (15 µg/m³) is associated "
         "with approximately 6% excess respiratory risk. Projections are indicative, "
         "assuming an exposed population of 100,000 per region."),
        BODY,
    ))
    elems.append(Spacer(1, 3*mm))

    hi_hdr = [
        Paragraph("Région" if fr else "Region", TH),
        Paragraph(("PM2.5 moy.\n(µg/m³)" if fr else "Mean PM2.5\n(µg/m³)"), TH),
        Paragraph(("Cas resp.\nexc. / 10k" if fr else "Excess Resp.\nCases / 10k"), TH),
        Paragraph(("Risque hospit.\n(%)" if fr else "Hospital\nRisk (%)"), TH),
        Paragraph(("Jours perdus\n/ 10k trav." if fr else "Lost Workdays\n/ 10k workers"), TH),
    ]
    hi_data = [hi_hdr]
    for r, pm, ex, _ in reg_stats:
        ec, hr_pct, ld = _health_impact(pm)
        hi_data.append([
            Paragraph(r, TD_L),
            Paragraph(str(pm), TD),
            Paragraph(str(ec), TD),
            Paragraph(f"{hr_pct}%", TD),
            Paragraph(str(ld), TD),
        ])
    hi_tbl = Table(hi_data, colWidths=[42*mm, 28*mm, 35*mm, 30*mm, 45*mm])
    hi_style = _tbl_base()
    for i, (_, pm, _, _) in enumerate(reg_stats, start=1):
        if pm > 25:
            hi_style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fef2f2"))
        elif pm > WHO_24H:
            hi_style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fffbeb"))
    hi_tbl.setStyle(hi_style)
    elems.append(hi_tbl)
    elems.append(Spacer(1, 4*mm))

    elems.append(Paragraph(
        "Groupes vulnérables :" if fr else "Vulnerable Groups:",
        _sty("BoldBody7", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    vuln = (
        [
            "Enfants (< 5 ans) — poumons en développement, risque de maladies respiratoires chroniques",
            "Personnes âgées (> 65 ans) — maladies cardio-vasculaires et pulmonaires préexistantes",
            "Femmes enceintes — effets sur le poids à la naissance et le développement fœtal",
            "Patients asthmatiques et BPCO — seuil de déclenchement abaissé",
            "Travailleurs en plein air — exposition prolongée et cumulée",
        ]
        if fr else
        [
            "Children (< 5 yrs) — developing lungs, risk of chronic respiratory disease",
            "Elderly (> 65 yrs) — pre-existing cardiovascular and pulmonary conditions",
            "Pregnant women — birth weight and foetal development impacts",
            "Asthma / COPD patients — lower trigger threshold",
            "Outdoor workers — prolonged cumulative exposure",
        ]
    )
    for v in vuln:
        elems.append(Paragraph(f"• {v}", BULLET))
    elems.append(Spacer(1, 4*mm))

    # Disclaimer
    elems.append(Paragraph(
        ("⚠ Avertissement : Ces estimations sont fournies à titre indicatif pour les "
         "décideurs de santé publique. Elles ne constituent pas un avis médical. "
         "Les concentrations réelles et les impacts sanitaires peuvent varier. "
         "Source : WHO Global Air Quality Guidelines 2021."
         if fr else
         "⚠ Disclaimer: These estimates are provided for public-health planning purposes "
         "only. They do not constitute medical advice. Actual concentrations and health "
         "impacts may vary by sub-population and exposure pattern. "
         "Source: WHO Global Air Quality Guidelines 2021."),
        _sty("Disc", fontSize=7.5, textColor=GREY, fontName="Helvetica-Oblique",
             leading=11, borderPad=3),
    ))

    # ── Footer on final page ──────────────────────────────────────────────────
    elems.append(Spacer(1, 10*mm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    elems.append(Spacer(1, 2*mm))
    footer = (
        f"AirSense Cameroon | IndabaX 2026 | "
        f"{'Données' if fr else 'Data'}: CAMS + ERA5 + Open-Meteo | "
        f"{'Modèle' if fr else 'Model'}: XGBoost + Optuna "
        f"(MAE {MODEL_MAE} µg/m³, R² {MODEL_R2}) | "
        f"{'Généré le' if fr else 'Generated'}: {now}"
    )
    elems.append(Paragraph(footer, FOOTER_S))

    doc.build(elems)
    return buf.getvalue()
