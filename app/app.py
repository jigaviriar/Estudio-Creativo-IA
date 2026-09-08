"""Punto de entrada de la app. Ejecutar con: streamlit run app/app.py"""
import streamlit as st

import chat_style

st.set_page_config(page_title="Estudio Creativo IA", page_icon=":material/auto_awesome:", layout="centered")
chat_style.inject_global()

page = st.navigation(
    [
        st.Page("app_pages/chat.py", title="Estudio", icon=":material/chat:"),
        st.Page("app_pages/etica_seguridad.py", title="Ética y seguridad", icon=":material/security:"),
        st.Page("app_pages/auditoria.py", title="Auditoría", icon=":material/fact_check:"),
    ],
    position="top",
)
page.run()
