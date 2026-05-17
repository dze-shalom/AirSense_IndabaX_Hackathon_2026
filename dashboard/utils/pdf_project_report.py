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
        author="AirSense Team",
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
        ("Prédiction IA de la qualité de l'air au Cameroun" if fr
         else "AI-Powered Air Quality Prediction for Cameroon"),
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

    elems.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 6 — NOTEBOOKS & REPRODUCIBILITY
    # ══════════════════════════════════════════════════════════════════════════
    elems.append(Paragraph(
        "5. Notebooks et reproductibilité" if fr else "5. Notebooks & Reproducibility",
        SEC_HDR,
    ))
    hr()

    elems.append(Paragraph(
        ("L'ensemble du pipeline — collecte des données, analyse exploratoire, "
         "entraînement des modèles et génération des graphiques — est documenté "
         "dans quatre notebooks Jupyter ordonnés. Chaque notebook est autonome, "
         "annoté scientifiquement et produit des artefacts explicitement nommés "
         "consommés par le suivant. L'exécution dans l'ordre garantit une "
         "reproduction complète des résultats."
         if fr else
         "The entire pipeline — data collection, exploratory analysis, model "
         "training, and chart generation — is documented in four ordered Jupyter "
         "notebooks. Each notebook is self-contained, scientifically annotated, "
         "and produces explicitly named artefacts consumed by the next. "
         "Running them in order fully reproduces all results."),
        BODY,
    ))
    elems.append(Spacer(1, 4*mm))

    # ── Notebook pipeline table ───────────────────────────────────────────────
    elems.append(Paragraph(
        "Pipeline des notebooks :" if fr else "Notebook Pipeline:",
        _sty("BoldNb1", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    nb_hdr = [
        Paragraph("#", TH),
        Paragraph("Fichier" if fr else "File", TH),
        Paragraph("Objectif" if fr else "Purpose", TH),
        Paragraph(("Sorties clés" if fr else "Key Outputs"), TH),
    ]
    nb_rows = [
        [
            "00",
            "00_Data_Cleaning.ipynb",
            ("Nettoyage, ingénierie des variables, récupération CAMS + ERA5, "
             "construction des proxys et validation"
             if fr else
             "Data cleaning, feature engineering, CAMS + ERA5 fetching, "
             "proxy target construction and validation"),
            ("airsense_clean.parquet\n(87 240 lignes, 40 variables)"
             if fr else
             "airsense_clean.parquet\n(87,240 rows, 40 features)"),
        ],
        [
            "01",
            "01_EDA.ipynb",
            ("Analyse exploratoire : distribution de la cible, corrélations "
             "météo, saisonnalité Harmattan, classements de villes, "
             "tendances inter-annuelles"
             if fr else
             "Exploratory analysis: target distribution, weather correlations, "
             "Harmattan seasonality, city rankings, "
             "year-over-year worsening trend"),
            ("Décisions de modélisation documentées,\ngraphiques EDA"
             if fr else
             "Documented modelling decisions,\nEDA charts"),
        ],
        [
            "02",
            "02_Modelling.ipynb",
            ("Entraînement : baselines → XGBoost + Optuna → "
             "Two-Stage Harmattan → Ensemble → GNN → Transformer → "
             "Calibration Platt → SHAP → Généralisation spatiale → "
             "Projections CMIP6 → Sauvegarde artefacts"
             if fr else
             "Training: baselines → XGBoost + Optuna → "
             "Two-Stage Harmattan → Ensemble → GNN → Transformer → "
             "Platt calibration → SHAP → Spatial generalisation → "
             "CMIP6 projections → Artefact save"),
            ("xgb_pm25.json, models/*.pkl,\n"
             "conformal_intervals.json,\n"
             "platt_alert_calibration.json,\n"
             "region_shap.pkl, climate_projections.json"
             ),
        ],
        [
            "03",
            "03_Pitch_Charts.ipynb",
            ("Génération des graphiques prêts à publier : excédances PM2.5, "
             "régimes de pollution, tendance temporelle, performance du modèle, "
             "SHAP, calibration des alertes, généralisation spatiale, "
             "projections 2050"
             if fr else
             "Publication-ready chart generation: PM2.5 exceedances, "
             "pollution regimes, trend, model performance, SHAP, "
             "alert calibration, spatial generalisation, 2050 projections"),
            "outputs/*.png",
        ],
    ]

    nb_data = [nb_hdr]
    for row in nb_rows:
        nb_data.append([
            Paragraph(row[0], TD),
            Paragraph(row[1], _sty(f"Mono{row[0]}", fontSize=7,
                                   fontName="Helvetica-Bold",
                                   textColor=TEAL2, leading=10)),
            Paragraph(row[2], TD_L),
            Paragraph(row[3], _sty(f"MonoOut{row[0]}", fontSize=7,
                                   fontName="Helvetica",
                                   textColor=GREY, leading=10,
                                   alignment=TA_LEFT)),
        ])
    nb_tbl = Table(nb_data, colWidths=[8*mm, 42*mm, 72*mm, 52*mm + 6*mm])
    nb_tbl.setStyle(_tbl_base())
    elems.append(nb_tbl)
    elems.append(Spacer(1, 5*mm))

    # ── Model artefacts ───────────────────────────────────────────────────────
    elems.append(Paragraph(
        "Artefacts du modèle (models/) :" if fr else "Model Artefacts (models/):",
        _sty("BoldNb2", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    art_hdr = [
        Paragraph("Fichier" if fr else "File", TH),
        Paragraph("Contenu" if fr else "Contents", TH),
        Paragraph(("Notebook source" if fr else "Source Notebook"), TH),
    ]
    art_rows = [
        ("xgb_pm25.json",
         "Modèle XGBoost principal (PM2.5)" if fr else "Primary XGBoost model (PM2.5)",
         "02 — Step 5b"),
        ("models_multi.pkl",
         "8 modèles composés (PM10, NO₂, O₃…)" if fr else "8 compound models (PM10, NO₂, O₃…)",
         "02 — Step 6"),
        ("model_harmattan.pkl / model_non_harmattan.pkl",
         "Two-Stage Harmattan model" if fr else "Two-stage Harmattan model",
         "02 — Step 6b"),
        ("platt_alert_calibration.json",
         "Paramètres de calibration Platt (σ, b)" if fr else "Platt calibration params (σ, b)",
         "02 — Step 7"),
        ("conformal_intervals.json",
         "Intervalles de confiance 90% par ville" if fr else "90% conformal intervals per city",
         "02 — Step 5b"),
        ("region_shap.pkl",
         "Top-7 SHAP par région" if fr else "Top-7 SHAP features per region",
         "02 — Step 8b"),
        ("climate_projections.json",
         "Projections CMIP6 SSP1–SSP5, 2025–2100" if fr else "CMIP6 SSP1–SSP5 projections 2025–2100",
         "02 — Step 10"),
        ("label_encoders.pkl",
         "Encodeurs ville + région" if fr else "City + region label encoders",
         "02 — Step 2"),
        ("city_confidence_tiers.json",
         "Niveaux de confiance par ville (High/Med/Low)" if fr else "City confidence tiers (High/Med/Low)",
         "02 — Step 9c"),
    ]
    art_data = [art_hdr]
    for f, c, s in art_rows:
        art_data.append([
            Paragraph(f, _sty(f"AF{f}", fontSize=7, fontName="Helvetica-Bold",
                               textColor=TEAL2, leading=10)),
            Paragraph(c, TD_L),
            Paragraph(s, TD),
        ])
    art_tbl = Table(art_data, colWidths=[56*mm, 84*mm, 40*mm])
    art_tbl.setStyle(_tbl_base())
    elems.append(art_tbl)
    elems.append(Spacer(1, 5*mm))

    # ── Reproduction steps ────────────────────────────────────────────────────
    elems.append(Paragraph(
        "Étapes de reproduction :" if fr else "Reproduction Steps:",
        _sty("BoldNb3", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    steps = (
        [
            ("1 — Cloner", "git clone https://github.com/dze-shalom/airsense_indabax_hackathon_2026"),
            ("2 — Installer", "pip install -r requirements.txt   # Python 3.10+"),
            ("3 — Données", "Placer Dataset_complet_Meteo.csv dans data/"),
            ("4 — Nettoyage", "Exécuter notebooks/00_Data_Cleaning.ipynb   → produit airsense_clean.parquet"),
            ("5 — EDA", "Exécuter notebooks/01_EDA.ipynb   → décisions de modélisation"),
            ("6 — Entraînement", "Exécuter notebooks/02_Modelling.ipynb   → produit tous les artefacts dans models/"),
            ("7 — Graphiques", "Exécuter notebooks/03_Pitch_Charts.ipynb   → produit outputs/*.png"),
            ("8 — Dashboard", "cd dashboard && streamlit run app.py   → http://localhost:8501"),
            ("9 — API (optionnel)", "uvicorn api.main:app --reload --port 8000   → http://localhost:8000/docs"),
        ]
        if fr else
        [
            ("1 — Clone", "git clone https://github.com/dze-shalom/airsense_indabax_hackathon_2026"),
            ("2 — Install", "pip install -r requirements.txt   # Python 3.10+"),
            ("3 — Data", "Place Dataset_complet_Meteo.csv in data/"),
            ("4 — Clean", "Run notebooks/00_Data_Cleaning.ipynb   → produces airsense_clean.parquet"),
            ("5 — EDA", "Run notebooks/01_EDA.ipynb   → modelling decisions"),
            ("6 — Train", "Run notebooks/02_Modelling.ipynb   → produces all artefacts in models/"),
            ("7 — Charts", "Run notebooks/03_Pitch_Charts.ipynb   → produces outputs/*.png"),
            ("8 — Dashboard", "cd dashboard && streamlit run app.py   → http://localhost:8501"),
            ("9 — API (optional)", "uvicorn api.main:app --reload --port 8000   → http://localhost:8000/docs"),
        ]
    )

    step_hdr = [
        Paragraph("Étape" if fr else "Step", TH),
        Paragraph("Commande / Action" if fr else "Command / Action", TH),
    ]
    step_data = [step_hdr]
    for lbl, cmd in steps:
        step_data.append([
            Paragraph(lbl, _sty(f"SL{lbl}", fontSize=8, fontName="Helvetica-Bold",
                                 textColor=BLACK, leading=11)),
            Paragraph(cmd, _sty(f"SC{lbl}", fontSize=7.5, fontName="Helvetica",
                                 textColor=GREY, leading=11, alignment=TA_LEFT)),
        ])
    step_tbl = Table(step_data, colWidths=[38*mm, 142*mm])
    step_tbl.setStyle(_tbl_base())
    elems.append(step_tbl)
    elems.append(Spacer(1, 4*mm))

    # ── Dependencies ──────────────────────────────────────────────────────────
    elems.append(Paragraph(
        "Dépendances principales :" if fr else "Key Dependencies:",
        _sty("BoldNb4", fontSize=9, fontName="Helvetica-Bold",
             textColor=BLACK, leading=14),
    ))
    elems.append(Spacer(1, 1*mm))

    dep_pairs = [
        ("xgboost ≥ 2.0", "Modèle PM2.5 principal" if fr else "Primary PM2.5 model"),
        ("lightgbm ≥ 4.0", "Membre de l'ensemble" if fr else "Ensemble member"),
        ("optuna ≥ 3.4", "Optimisation hyperparamètres" if fr else "Hyperparameter optimisation"),
        ("shap ≥ 0.44", "Explicabilité des facteurs" if fr else "Feature explainability"),
        ("scikit-learn ≥ 1.3", "Calibration Platt, encodeurs, métriques" if fr
         else "Platt calibration, encoders, metrics"),
        ("streamlit ≥ 1.32", "Dashboard web" if fr else "Web dashboard"),
        ("fastapi ≥ 0.110", "API REST" if fr else "REST API"),
        ("reportlab ≥ 4.0", "Génération PDF" if fr else "PDF generation"),
        ("pandas ≥ 2.0 / numpy ≥ 1.24", "Traitement des données" if fr else "Data processing"),
        ("plotly ≥ 5.18", "Visualisations interactives" if fr else "Interactive visualisations"),
    ]
    # Two columns
    mid = (len(dep_pairs) + 1) // 2
    col_a = dep_pairs[:mid]
    col_b = dep_pairs[mid:]
    dep_rows = []
    for i in range(max(len(col_a), len(col_b))):
        la = col_a[i] if i < len(col_a) else ("", "")
        lb = col_b[i] if i < len(col_b) else ("", "")
        dep_rows.append([
            Paragraph(la[0], _sty(f"DK{i}a", fontSize=7.5, fontName="Helvetica-Bold",
                                   textColor=TEAL2, leading=11)),
            Paragraph(la[1], _sty(f"DV{i}a", fontSize=7.5, fontName="Helvetica",
                                   textColor=BLACK, leading=11, alignment=TA_LEFT)),
            Paragraph(lb[0], _sty(f"DK{i}b", fontSize=7.5, fontName="Helvetica-Bold",
                                   textColor=TEAL2, leading=11)),
            Paragraph(lb[1], _sty(f"DV{i}b", fontSize=7.5, fontName="Helvetica",
                                   textColor=BLACK, leading=11, alignment=TA_LEFT)),
        ])
    dep_tbl = Table(dep_rows, colWidths=[38*mm, 52*mm, 38*mm, 52*mm])
    dep_style = TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, colors.HexColor("#f9fafb")]),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ])
    dep_tbl.setStyle(dep_style)
    elems.append(dep_tbl)
    elems.append(Spacer(1, 4*mm))

    # ── Reproducibility note ──────────────────────────────────────────────────
    note = (
        "Note de reproductibilité : les modèles .json/.pkl versionnés dans Git "
        "permettent de faire fonctionner le dashboard sans ré-entraînement. "
        "Si les fichiers .pkl sont absents (LFS non disponible), "
        "python scripts/setup_models.py génère des modèles de substitution "
        "fonctionnels en ~5 secondes. La clé API Groq est optionnelle — "
        "l'assistant IA utilise un fallback basé sur des règles sans elle."
        if fr else
        "Reproducibility note: the .json/.pkl model artefacts versioned in Git "
        "allow the dashboard to run without re-training. "
        "If .pkl files are absent (Git LFS unavailable), "
        "python scripts/setup_models.py generates functional stub models in ~5 s. "
        "The Groq API key is optional — the AI assistant falls back to "
        "rule-based responses without it."
    )
    elems.append(Paragraph(
        note,
        _sty("ReproNote", fontSize=7.5, textColor=GREY,
             fontName="Helvetica-Oblique", leading=11),
    ))

    # ── Footer on final page ──────────────────────────────────────────────────
    elems.append(Spacer(1, 8*mm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    elems.append(Spacer(1, 2*mm))
    footer = (
        f"AirSense Cameroon | "
        f"{'Données' if fr else 'Data'}: CAMS + ERA5 + Open-Meteo | "
        f"{'Modèle' if fr else 'Model'}: XGBoost + Optuna "
        f"(MAE {MODEL_MAE} µg/m³, R² {MODEL_R2}) | "
        f"{'Généré le' if fr else 'Generated'}: {now}"
    )
    elems.append(Paragraph(footer, FOOTER_S))

    doc.build(elems)
    return buf.getvalue()
