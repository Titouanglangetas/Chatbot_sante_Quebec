# streamlit_app/utils/auth.py

import streamlit as st
from pathlib import Path

# --------------------------------------------------
# ⚙️ Configuration des identifiants (à adapter !)
# --------------------------------------------------
USER_CREDENTIALS = {
    "admin": "1234",
    "user":  "azerty"
}

# --------------------------------------------------
# 💅 Chargement du CSS de la page de login
# --------------------------------------------------
def load_auth_css() -> None:
    css_path = Path(__file__).parents[1] / "assets" / "auth.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --------------------------------------------------
# 🔐 Fonction d’authentification
# --------------------------------------------------
def check_auth() -> bool:
    load_auth_css()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    # Si déjà authentifié, on ne réaffiche rien
    if st.session_state.authenticated:
        return True

    st.markdown("# 🔐 Connexion")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("👤 Nom d'utilisateur")
        password = st.text_input("🔑 Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.authenticated = True
                st.session_state.username      = username
                st.success("✅ Connexion réussie !")
                # ←── important : relancer tout l'app
                st.rerun()
            else:
                st.error("❌ Identifiants incorrects.")

    # Form non soumis ou authentifié == False
    return False

