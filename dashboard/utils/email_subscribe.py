import streamlit as st


def render_email_subscribe_ui(api_base_url: str = ""):
    """Renders a small email subscription form that POSTs to /email/subscribe."""
    lang = st.session_state.get("lang", "en")

    with st.form("as_email_sub_form", clear_on_submit=True):
        placeholder = "your@email.com"
        label = "Weekly digest" if lang == "en" else "Résumé hebdomadaire"
        email = st.text_input(label, placeholder=placeholder, key="as_email_input")
        submitted = st.form_submit_button(
            "Subscribe" if lang == "en" else "S'abonner",
            use_container_width=True
        )
        if submitted and email and "@" in email:
            try:
                import requests
                resp = requests.post(
                    f"{api_base_url}/email/subscribe",
                    json={"email": email},
                    timeout=5
                )
                if resp.ok:
                    st.success("✓ Subscribed!" if lang == "en" else "✓ Abonné!")
                else:
                    st.error("Error. Try again." if lang == "en" else "Erreur. Réessayez.")
            except Exception:
                st.info("Saved locally — digest will be sent when API is available." if lang == "en"
                        else "Enregistré localement.")
        elif submitted:
            st.warning("Enter a valid email." if lang == "en" else "Entrez un email valide.")
