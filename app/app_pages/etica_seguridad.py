import streamlit as st

from config import DEMO_MODE
from prompts import BLOCKED_TERMS, SYSTEM_PROMPT_TEMPLATE
from security import encryption_enabled

st.title("Ética y seguridad", icon=":material/security:")
st.caption("Salvaguardas activas en esta instancia — detalle completo en docs/3.6-etica-y-seguridad.md")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Moderación de contenido", icon=":material/filter_alt:")
    st.write(
        "Filtro de palabras clave sobre la entrada y la salida (imágenes y texto). "
        "En producción se recomienda **Amazon Bedrock Guardrails**."
    )
    st.code("\n".join(f"- {t}" for t in BLOCKED_TERMS), language="text")

    st.subheader("Prompt injection", icon=":material/shield_lock:")
    st.write(
        "El texto del usuario viaja siempre delimitado en etiquetas `<texto_usuario>`. "
        "El system prompt indica explícitamente que ese contenido es dato a editar, nunca instrucciones."
    )
    with st.expander("Ver system prompt completo de Claude", icon=":material/code:"):
        st.code(SYSTEM_PROMPT_TEMPLATE.format(tono="{tono}"), language="text")

with col2:
    st.subheader("Sesgo", icon=":material/balance:")
    st.write(
        "El rol **Aprobador** revisa todo contenido antes de marcarlo como aprobado. "
        "El system prompt prohíbe explícitamente estereotipos y contenido discriminatorio."
    )

    st.subheader("Privacidad y copyright", icon=":material/lock:")
    if encryption_enabled():
        st.badge("Cifrado en reposo activado", icon=":material/check:", color="green")
    else:
        st.badge("Cifrado en reposo desactivado", icon=":material/warning:", color="red")
        st.caption("Configura APP_ENCRYPTION_KEY en .env para cifrar imágenes y contenido guardado.")
    st.write(
        "No se envían a Bedrock datos personales de clientes ni empleados. "
        "Evita solicitar el estilo de un artista o marca protegida concreto al generar imágenes; "
        "valida con legal antes de publicar contenido generado por IA."
    )

if DEMO_MODE:
    st.warning("DEMO_MODE está activo: ninguna llamada real a Bedrock se está realizando en este momento.")
