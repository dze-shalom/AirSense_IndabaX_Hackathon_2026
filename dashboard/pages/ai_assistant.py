"""pages/ai_assistant.py — Rule-based bilingual air quality chatbot (no API key needed)."""
import math
import streamlit as st
from datetime import datetime

from config import CITIES, CITY_STATS, WHO_24H, T
from utils.helpers import LNG, aqi, health_impact, live_source_attribution
from components.ui import sec, info_box, _cbg, _cborder, _ctxt, _ctxt2, _accent
from components.charts import PLO

TEAL  = "#64ffda"
RED   = "#ff6b6b"
AMBER = "#f59e0b"
GREEN = "#22c55e"

NORTHERN = {"Far North", "North", "Adamawa"}

# ── Intent keyword map ────────────────────────────────────────────────────────
_INTENTS = {
    "greeting":    ["hi","hello","hey","good morning","good afternoon","good evening",
                    "bonjour","salut","bonsoir","bonne journée","bonne nuit"],
    "safety":      ["safe","safety","dangerous","quality","how is the air","how is air",
                    "current","right now","today","aujourd","maintenant","sûr","dangereux",
                    "qualité","comment est","air quality"],
    "forecast":    ["tomorrow","week","forecast","next days","next week","prediction","coming days",
                    "prévision","demain","semaine","prochains","prévoir","cette semaine"],
    "source":      ["cause","why","because","source","where does","what causes","responsible",
                    "origin","coming from","pourquoi","vient","causé","d'où","à cause","responsable"],
    "health":      ["health","sick","breathe","breathing","respiratory","lungs","symptom",
                    "effect","impact","affect","disease","santé","malade","respirer","poumons",
                    "symptôme","effet","maladie","toux","cough","asthma","asthme"],
    "protection":  ["protect","what to do","avoid","reduce","action","advice","tip",
                    "que faire","protéger","éviter","réduire","conseil","quoi faire"],
    "mask":        ["mask","respirator","n95","ffp2","kn95","filter","wear",
                    "masque","respiratoire","filtre","porter"],
    "school":      ["school","children","kids","child","student","classroom","outdoor","pe ",
                    "école","enfants","enfant","élève","classe","extérieur","sport"],
    "agriculture": ["farm","crop","livestock","agriculture","farming","cattle","plant","harvest",
                    "ferme","élevage","culture","bétail","plante","récolte","agricole"],
    "harmattan":   ["harmattan","dust","saharan","dust storm","sand","northeast","desert",
                    "poussière","saharien","tempête","sable","nord-est","désert"],
    "who":         ["who ","standard","guideline","limit","threshold","norm","benchmark","guideline",
                    "oms","norme","seuil","limite","directive","référence"],
    "trend":       ["trend","getting better","getting worse","improving","worsening","next days",
                    "tendance","améliore","aggrave","évolution","prochains jours"],
    "help":        ["help","what can","commands","what do you","how to use","options","menu",
                    "aide","que peux","comment utiliser","quoi demander","options"],
}


def _detect_intent(msg: str) -> str:
    msg_l = msg.lower()
    for intent, keywords in _INTENTS.items():
        if any(kw in msg_l for kw in keywords):
            return intent
    return "fallback"


def _aqi_info(pm25: float):
    if pm25 < 5:   return "good",      "#22c55e", "Good",      "Bon"
    if pm25 < 15:  return "moderate",  "#f59e0b", "Moderate",  "Modéré"
    if pm25 < 30:  return "poor",      "#f97316", "Poor",      "Mauvais"
    if pm25 < 60:  return "very_poor", "#ef4444", "Very Poor", "Très Mauvais"
    return         "hazardous",        "#8b5cf6", "Hazardous", "Dangereux"


def _build_context(city: str) -> dict:
    """Gather live data for the selected city."""
    from utils.live_data import get_live_stats
    live  = get_live_stats()
    stats = live.get(city) or CITY_STATS.get(city, {})
    pm25  = stats.get("mean_pm25", 15.0)
    region = stats.get("region", "Centre")
    forecasts = stats.get("forecasts", [])

    # 3-day trend
    if len(forecasts) >= 3:
        delta = forecasts[2]["pm25"] - forecasts[0]["pm25"]
        trend = "improving" if delta < -1 else "worsening" if delta > 1 else "stable"
    else:
        trend = "stable"

    lvl, col, lbl_en, lbl_fr = _aqi_info(pm25)
    prob    = 1 / (1 + math.exp(-(0.2221 * pm25 - 3.0372)))
    exceeded = pm25 > WHO_24H

    month   = datetime.now().month
    north   = region in NORTHERN
    harm_active = month in [11, 12, 1, 2] and north

    # Source attribution
    ws  = 10.0 if harm_active else 4.0
    wd  = 35.0 if harm_active else 180.0
    prc = 0.0  if month in [11, 12, 1, 2] else 5.0
    hum = 30.0 if harm_active else 65.0
    src = live_source_attribution(ws, wd, month, region, prc, hum, pm25)
    dom_src = max(src, key=src.get)

    # School level
    o3 = max(0, 30 + (28 - 25) * 2.8)
    if   pm25 <= 15 and o3 <= 60: school_lv = 1
    elif pm25 <= 35 and o3 <= 80: school_lv = 2
    elif pm25 <= 55:               school_lv = 3
    else:                          school_lv = 4

    er, hr, ld = health_impact(pm25)

    return dict(
        city=city, region=region, pm25=pm25,
        lvl=lvl, lbl_en=lbl_en, lbl_fr=lbl_fr,
        prob=prob, exceeded=exceeded,
        forecasts=forecasts, trend=trend,
        north=north, month=month, harm_active=harm_active,
        src=src, dom_src=dom_src,
        school_lv=school_lv, er=er, hr=hr, ld=ld,
    )


def _respond(intent: str, ctx: dict, lang: str) -> str:
    city   = ctx["city"]
    region = ctx["region"]
    pm25   = ctx["pm25"]
    lbl    = ctx["lbl_fr"] if lang == "fr" else ctx["lbl_en"]
    lvl    = ctx["lvl"]
    prob   = ctx["prob"]
    exc    = ctx["exceeded"]
    trend  = ctx["trend"]
    fc     = ctx["forecasts"]
    src    = ctx["src"]
    dom    = ctx["dom_src"]
    ha     = ctx["harm_active"]
    sl     = ctx["school_lv"]
    er     = ctx["er"]
    hr_    = ctx["hr"]

    tr_en = {"improving":"improving ↓","worsening":"worsening ↑","stable":"stable →"}[trend]
    tr_fr = {"improving":"en amélioration ↓","worsening":"en dégradation ↑","stable":"stable →"}[trend]

    who_en = "⚠️ Exceeds WHO 24h limit (15 µg/m³)." if exc else "✅ Within WHO 24h limit (15 µg/m³)."
    who_fr = "⚠️ Dépasse la limite OMS 24h (15 µg/m³)." if exc else "✅ Dans la limite OMS 24h (15 µg/m³)."

    _health_en = {
        "good":"No health concerns for any group.",
        "moderate":"Sensitive individuals may experience minor symptoms.",
        "poor":"Limit prolonged outdoor activity. Sensitive groups should stay indoors.",
        "very_poor":"Avoid outdoor activities. Everyone may be affected.",
        "hazardous":"Stay indoors immediately. Health emergency.",
    }[lvl]
    _health_fr = {
        "good":"Aucun problème de santé pour tous les groupes.",
        "moderate":"Les personnes sensibles peuvent ressentir des symptômes mineurs.",
        "poor":"Limitez les activités extérieures prolongées. Groupes sensibles: restez à l'intérieur.",
        "very_poor":"Évitez les activités extérieures. Tout le monde peut être affecté.",
        "hazardous":"Restez à l'intérieur immédiatement. Urgence sanitaire.",
    }[lvl]

    if intent == "greeting":
        if lang == "fr":
            return (f"Bonjour ! Je suis l'assistant AirSense pour **{city}**.\n\n"
                    f"La qualité de l'air est actuellement **{lbl}** (PM2.5 = {pm25:.1f} µg/m³). "
                    f"{who_fr}\n\nTapez **aide** pour voir ce que je peux faire.")
        return (f"Hello! I'm the AirSense assistant for **{city}**.\n\n"
                f"Air quality is currently **{lbl}** (PM2.5 = {pm25:.1f} µg/m³). "
                f"{who_en}\n\nType **help** to see what I can do.")

    elif intent == "safety":
        if lang == "fr":
            return (f"**Qualité de l'air à {city}** : **{lbl}**\n\n"
                    f"📊 PM2.5 = **{pm25:.1f} µg/m³** · {who_fr}\n"
                    f"🎯 Probabilité d'alerte : **{prob*100:.0f}%**\n"
                    f"📈 Tendance 3 jours : {tr_fr}\n\n"
                    f"💡 {_health_fr}")
        return (f"**Air quality in {city}**: **{lbl}**\n\n"
                f"📊 PM2.5 = **{pm25:.1f} µg/m³** · {who_en}\n"
                f"🎯 Alert probability: **{prob*100:.0f}%**\n"
                f"📈 3-day trend: {tr_en}\n\n"
                f"💡 {_health_en}")

    elif intent == "forecast":
        if not fc:
            return ("No forecast data available — try refreshing." if lang == "en"
                    else "Données de prévision non disponibles — actualisez.")
        lines = []
        for p in fc[:7]:
            _, _, le, lf = _aqi_info(p["pm25"])
            lb = lf if lang == "fr" else le
            lines.append(f"• {p['date']}: **{p['pm25']:.1f} µg/m³** — {lb}")
        body = "\n".join(lines)
        if lang == "fr":
            return f"**Prévisions 7 jours pour {city}** :\n\n{body}\n\n📈 Tendance : {tr_fr}"
        return f"**7-day forecast for {city}**:\n\n{body}\n\n📈 Trend: {tr_en}"

    elif intent == "source":
        src_fr = {
            "Dust":"Poussière saharienne","Biomass Burning":"Feux de biomasse",
            "Traffic":"Trafic routier","Industry":"Industrie",
            "Secondary Aerosol":"Aérosol secondaire","Secondary":"Aérosol secondaire",
            "Other":"Autres",
        }
        if lang == "fr":
            lines = "\n".join(f"• {src_fr.get(k,k)}: **{v*100:.0f}%**"
                              for k,v in sorted(src.items(), key=lambda x:-x[1]))
            dom_fr = src_fr.get(dom, dom)
            return (f"**Sources de pollution à {city}** ({region}) :\n\n{lines}\n\n"
                    f"🏆 Source dominante : **{dom_fr}**\n"
                    + ("🌬 La saison Harmattan amplifie le transport de poussières sahariennes." if ha else ""))
        lines = "\n".join(f"• {k}: **{v*100:.0f}%**"
                          for k,v in sorted(src.items(), key=lambda x:-x[1]))
        return (f"**Pollution sources in {city}** ({region}):\n\n{lines}\n\n"
                f"🏆 Dominant source: **{dom}**\n"
                + ("🌬 Harmattan season is amplifying Saharan dust transport." if ha else ""))

    elif intent == "health":
        if lang == "fr":
            return (f"**Impact sanitaire à {city}** (PM2.5 = {pm25:.1f} µg/m³) :\n\n"
                    f"• 🏥 Cas respiratoires excédentaires : **{er:.1f}** / 10 000 personnes / an\n"
                    f"• 🚑 Risque d'hospitalisation : **{hr_:.1f}%**\n"
                    f"• 😷 Groupes à risque : enfants <12 ans, personnes âgées, asthmatiques, femmes enceintes\n\n"
                    f"{'⚠️ Le niveau actuel dépasse la directive OMS.' if exc else '✅ Le niveau actuel respecte la directive OMS.'}")
        return (f"**Health impact in {city}** (PM2.5 = {pm25:.1f} µg/m³):\n\n"
                f"• 🏥 Excess respiratory cases: **{er:.1f}** / 10,000 people / year\n"
                f"• 🚑 Hospital admission risk: **{hr_:.1f}%**\n"
                f"• 😷 At-risk groups: children <12, elderly, asthmatics, pregnant women\n\n"
                f"{'⚠️ Current level exceeds WHO guideline.' if exc else '✅ Current level within WHO guideline.'}")

    elif intent in ("protection", "mask"):
        _mask_en = {
            "good":      "No mask needed. All outdoor activities are safe.",
            "moderate":  "No mask needed for most people. Sensitive groups may use a surgical mask.",
            "poor":      "Wear a surgical mask outdoors. Reduce prolonged exertion.",
            "very_poor": "Wear an N95/FFP2 mask outdoors. Limit outdoor time to essentials.",
            "hazardous": "N95/FFP2 mandatory outdoors. Stay indoors as much as possible.",
        }[lvl]
        _mask_fr = {
            "good":      "Pas de masque nécessaire. Activités extérieures sûres.",
            "moderate":  "Pas de masque pour la plupart. Les personnes sensibles peuvent porter un masque chirurgical.",
            "poor":      "Portez un masque chirurgical dehors. Réduisez l'effort prolongé.",
            "very_poor": "Portez un masque N95/FFP2 dehors. Limitez le temps extérieur à l'essentiel.",
            "hazardous": "N95/FFP2 obligatoire dehors. Restez à l'intérieur autant que possible.",
        }[lvl]
        if lang == "fr":
            return (f"**Protection recommandée pour {city}** (PM2.5 = {pm25:.1f} µg/m³) :\n\n"
                    f"😷 {_mask_fr}\n\n"
                    f"**Conseils généraux :**\n"
                    f"• Restez à l'intérieur aux heures de pointe\n"
                    f"• Fermez les fenêtres lors des pics de pollution\n"
                    f"• Hydratez-vous bien\n"
                    f"• Consultez un médecin si vous ressentez des symptômes")
        return (f"**Protection advice for {city}** (PM2.5 = {pm25:.1f} µg/m³):\n\n"
                f"😷 {_mask_en}\n\n"
                f"**General tips:**\n"
                f"• Stay indoors during peak pollution hours\n"
                f"• Close windows during high pollution events\n"
                f"• Stay well hydrated\n"
                f"• See a doctor if you experience symptoms")

    elif intent == "school":
        _sl_en = {1:"✅ SAFE — All outdoor activities permitted including PE.",
                  2:"⚠️ CAUTION — Limit vigorous outdoor activity. Shorten PE sessions.",
                  3:"🔶 RESTRICTED — No PE outdoors. Short breaks only (10 min max).",
                  4:"🔴 CLOSE — All outdoor activities cancelled. Stay indoors."}
        _sl_fr = {1:"✅ SÛR — Toutes les activités extérieures autorisées y compris l'EPS.",
                  2:"⚠️ PRÉCAUTION — Limitez les activités vigoureuses. Raccourcissez l'EPS.",
                  3:"🔶 RESTREINT — Pas d'EPS dehors. Pauses courtes uniquement (10 min max).",
                  4:"🔴 FERMER — Toutes les activités extérieures annulées. Restez à l'intérieur."}
        exc_note_en = "Exceeds" if exc else "Within"
        exc_note_fr = "Dépasse" if exc else "Dans"
        if lang == "fr":
            return (f"**Avis scolaire pour {city}** — Niveau d'action **{sl}/4**\n\n"
                    f"{_sl_fr[sl]}\n\n"
                    f"PM2.5 actuel : {pm25:.1f} µg/m³ · {exc_note_fr} la limite OMS")
        return (f"**School advisory for {city}** — Action level **{sl}/4**\n\n"
                f"{_sl_en[sl]}\n\n"
                f"Current PM2.5: {pm25:.1f} µg/m³ · {exc_note_en} WHO limit")

    elif intent == "agriculture":
        north = ctx["north"]
        if lang == "fr":
            if not north:
                return f"Pas d'alerte agricole spécifique pour {city} ({region}). Conditions normales."
            if pm25 > 50:
                return (f"⚠️ **Alerte agricole pour {city}** :\n\n"
                        f"• Mettez le bétail à l'abri immédiatement\n"
                        f"• Couvrez les points d'eau\n"
                        f"• Retardez les traitements phytosanitaires\n"
                        f"• Protégez les jeunes plants")
            return (f"**Avis agricole pour {city}** ({region}) :\n\n"
                    f"• Conditions modérées — surveillance recommandée\n"
                    f"• Couvrez les réserves d'eau\n"
                    f"• Limitez le pâturage aux heures matinales\n"
                    f"• Surveillez les signes de stress respiratoire chez le bétail")
        if not north:
            return f"No specific agricultural alert for {city} ({region}). Normal conditions."
        if pm25 > 50:
            return (f"⚠️ **Agricultural alert for {city}**:\n\n"
                    f"• Shelter livestock immediately\n"
                    f"• Cover water sources\n"
                    f"• Delay crop spraying\n"
                    f"• Protect young plants")
        return (f"**Agricultural advisory for {city}** ({region}):\n\n"
                f"• Moderate conditions — monitoring recommended\n"
                f"• Cover water reserves\n"
                f"• Limit grazing to morning hours\n"
                f"• Watch for respiratory stress in livestock")

    elif intent == "harmattan":
        if lang == "fr":
            if ha:
                return (f"🌬 **Harmattan actif à {city}** !\n\n"
                        f"Le vent de nord-est transporte de la poussière saharienne depuis le désert du Sahara. "
                        f"C'est la principale cause du PM2.5 élevé ({pm25:.1f} µg/m³) en ce moment.\n\n"
                        f"**Précautions :**\n"
                        f"• Portez un masque N95/FFP2 dehors\n"
                        f"• Fermez les fenêtres et portes\n"
                        f"• Hydratez-vous davantage\n"
                        f"• Surveillez les enfants et personnes âgées")
            return (f"Pas d'Harmattan actif à {city} en ce moment. "
                    f"La saison Harmattan dure typiquement de novembre à février dans les régions nord. "
                    f"PM2.5 actuel : {pm25:.1f} µg/m³.")
        if ha:
            return (f"🌬 **Harmattan is active in {city}**!\n\n"
                    f"NE winds are transporting Saharan dust from the Sahara Desert. "
                    f"This is the primary driver of elevated PM2.5 ({pm25:.1f} µg/m³) right now.\n\n"
                    f"**Precautions:**\n"
                    f"• Wear N95/FFP2 mask outdoors\n"
                    f"• Close windows and doors\n"
                    f"• Increase fluid intake\n"
                    f"• Monitor children and elderly")
        return (f"No active Harmattan in {city} right now. "
                f"Harmattan season typically runs November–February in northern Cameroon. "
                f"Current PM2.5: {pm25:.1f} µg/m³.")

    elif intent == "who":
        if lang == "fr":
            return (f"**Normes de qualité de l'air :**\n\n"
                    f"• OMS 2021 (24h) : **15 µg/m³** PM2.5\n"
                    f"• OMS 2021 (annuel) : **5 µg/m³** PM2.5\n"
                    f"• UE 2024 (24h) : 25 µg/m³\n"
                    f"• EPA US (24h) : 35 µg/m³\n\n"
                    f"**{city}** ({region}) — PM2.5 actuel : **{pm25:.1f} µg/m³** · "
                    f"{'⚠️ Dépasse' if exc else '✅ Dans'} la limite OMS 2021.")
        return (f"**Air Quality Standards:**\n\n"
                f"• WHO 2021 (24h): **15 µg/m³** PM2.5\n"
                f"• WHO 2021 (annual): **5 µg/m³** PM2.5\n"
                f"• EU 2024 (24h): 25 µg/m³\n"
                f"• US EPA (24h): 35 µg/m³\n\n"
                f"**{city}** ({region}) — current PM2.5: **{pm25:.1f} µg/m³** · "
                f"{'⚠️ Exceeds' if exc else '✅ Within'} WHO 2021 limit.")

    elif intent == "trend":
        if not fc:
            return "No forecast data available." if lang == "en" else "Pas de données disponibles."
        if lang == "fr":
            msgs = {"worsening":"📈 La pollution devrait augmenter. Restez vigilant.",
                    "improving":"📉 La pollution devrait diminuer. Bonne nouvelle !",
                    "stable":"📊 La pollution devrait rester stable."}
            return (f"**Tendance à {city}** :\n\n"
                    f"Aujourd'hui : **{pm25:.1f} µg/m³**\n"
                    f"Tendance 3 jours : {tr_fr}\n\n{msgs[trend]}")
        msgs = {"worsening":"📈 Pollution expected to rise. Stay vigilant.",
                "improving":"📉 Pollution expected to fall. Good news!",
                "stable":"📊 Pollution expected to remain stable."}
        return (f"**Trend for {city}**:\n\n"
                f"Today: **{pm25:.1f} µg/m³**\n"
                f"3-day trend: {tr_en}\n\n{msgs[trend]}")

    elif intent == "help":
        if lang == "fr":
            return ("**Je peux vous aider avec :**\n\n"
                    "• *L'air est-il sûr aujourd'hui ?*\n"
                    "• *Quelles sont les prévisions cette semaine ?*\n"
                    "• *Quelle est la source de pollution ?*\n"
                    "• *Quel masque porter ?*\n"
                    "• *Les enfants peuvent-ils aller à l'école ?*\n"
                    "• *Y a-t-il une alerte agricole ?*\n"
                    "• *L'Harmattan est-il actif ?*\n"
                    "• *Quelles sont les normes OMS ?*\n"
                    "• *Quel est l'impact sur la santé ?*\n"
                    "• *La pollution s'améliore-t-elle ?*")
        return ("**I can help you with:**\n\n"
                "• *Is the air safe today?*\n"
                "• *What is the forecast this week?*\n"
                "• *What is causing the pollution?*\n"
                "• *What mask should I wear?*\n"
                "• *Can children go to school?*\n"
                "• *Is there an agricultural alert?*\n"
                "• *Is the Harmattan active?*\n"
                "• *What are the WHO standards?*\n"
                "• *What are the health impacts?*\n"
                "• *Is pollution improving?*")

    # fallback
    if lang == "fr":
        return (f"Je n'ai pas compris votre question. Essayez : "
                f"*qualité de l'air*, *prévisions*, *masque*, *école*, *santé* — "
                f"ou tapez **aide** pour voir toutes les options.")
    return (f"I didn't quite understand that. Try asking about: "
            f"*air quality*, *forecast*, *mask*, *school*, *health* — "
            f"or type **help** to see all options.")


# ── Suggested prompts ─────────────────────────────────────────────────────────
_SUGGESTIONS_EN = [
    "Is the air safe today?",
    "What is the 7-day forecast?",
    "What is causing the pollution?",
    "What mask should I wear?",
    "Can children go to school?",
    "Is the Harmattan active?",
]
_SUGGESTIONS_FR = [
    "L'air est-il sûr aujourd'hui ?",
    "Quelles sont les prévisions 7 jours ?",
    "Quelle est la source de pollution ?",
    "Quel masque porter ?",
    "Les enfants peuvent-ils aller à l'école ?",
    "L'Harmattan est-il actif ?",
]


def page_ai():
    lang = LNG()
    t    = T[lang]
    st.markdown('<div class="as-content">', unsafe_allow_html=True)
    sec(t.get("ai_assistant_hdr", "AI Assistant"))

    # ── City selector ─────────────────────────────────────────────────────────
    all_cities = [c for clist in CITIES.values() for c, *_ in clist]
    col_r, col_c, col_clr = st.columns([1, 2, 1])
    with col_r:
        regions  = list(CITIES.keys())
        sel_reg  = st.selectbox(
            "Region" if lang == "en" else "Région",
            regions, key="ai_region",
        )
    with col_c:
        city_opts = [c for c, *_ in CITIES[sel_reg]]
        sel_city  = st.selectbox(
            "City" if lang == "en" else "Ville",
            city_opts, key="ai_city",
        )
    with col_clr:
        st.markdown("<div style='margin-top:1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("🗑 Clear" if lang == "en" else "🗑 Effacer",
                     key="ai_clear", use_container_width=True):
            st.session_state.ai_history = []
            st.rerun()

    # ── Status strip ──────────────────────────────────────────────────────────
    ctx = _build_context(sel_city)
    lvl_col = {"good":GREEN,"moderate":AMBER,"poor":"#f97316",
               "very_poor":RED,"hazardous":"#8b5cf6"}[ctx["lvl"]]
    lbl = ctx["lbl_fr"] if lang == "fr" else ctx["lbl_en"]
    exc_note = ("⚠️ above WHO limit" if ctx["exceeded"] else "✅ below WHO limit") if lang == "en" \
               else ("⚠️ au-dessus limite OMS" if ctx["exceeded"] else "✅ sous limite OMS")

    st.markdown(
        f'<div style="display:flex;gap:1.2rem;align-items:center;'
        f'background:{_cbg()};border:1px solid {_cborder()};'
        f'border-radius:10px;padding:.6rem 1rem;margin-bottom:.8rem;">'
        f'<span style="font-size:.7rem;color:{_ctxt2()};">'
        f'{"City" if lang=="en" else "Ville"}: <strong style="color:{_ctxt()};">{sel_city}</strong></span>'
        f'<span style="font-size:.7rem;color:{_ctxt2()};">'
        f'PM2.5: <strong style="color:{lvl_col};">{ctx["pm25"]:.1f} µg/m³</strong></span>'
        f'<span style="font-size:.7rem;color:{lvl_col};font-weight:700;">{lbl}</span>'
        f'<span style="font-size:.65rem;color:{_ctxt2()};">{exc_note}</span>'
        f'<span style="font-size:.65rem;color:{_ctxt2()};">'
        f'{"Alert prob" if lang=="en" else "Prob. alerte"}: '
        f'<strong>{ctx["prob"]*100:.0f}%</strong></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Chat history ──────────────────────────────────────────────────────────
    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []

    # Welcome message on first load
    if not st.session_state.ai_history:
        welcome = _respond("greeting", ctx, lang)
        st.session_state.ai_history.append({"role": "assistant", "content": welcome})

    for msg in st.session_state.ai_history:
        with st.chat_message(msg["role"],
                             avatar="🌬" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # ── Suggested prompts (shown until first user message) ────────────────────
    user_msgs = [m for m in st.session_state.ai_history if m["role"] == "user"]
    if not user_msgs:
        sugg = _SUGGESTIONS_FR if lang == "fr" else _SUGGESTIONS_EN
        st.markdown(
            f'<div style="font-size:.65rem;color:{_ctxt2()};margin:.4rem 0 .3rem;">'
            f'{"Suggestions" if lang=="en" else "Suggestions"} :</div>',
            unsafe_allow_html=True)
        cols = st.columns(3)
        for i, s in enumerate(sugg):
            with cols[i % 3]:
                if st.button(s, key=f"sugg_{i}", use_container_width=True):
                    st.session_state.ai_history.append({"role":"user","content":s})
                    intent   = _detect_intent(s)
                    response = _respond(intent, ctx, lang)
                    st.session_state.ai_history.append({"role":"assistant","content":response})
                    st.rerun()

    # ── Chat input ────────────────────────────────────────────────────────────
    placeholder = ("Ask about air quality, health, forecast…"
                   if lang == "en"
                   else "Posez une question sur la qualité de l'air, la santé, les prévisions…")
    user_input = st.chat_input(placeholder)
    if user_input:
        st.session_state.ai_history.append({"role": "user", "content": user_input})
        intent   = _detect_intent(user_input)
        response = _respond(intent, ctx, lang)
        st.session_state.ai_history.append({"role": "assistant", "content": response})
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
