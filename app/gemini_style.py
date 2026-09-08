"""CSS personalizado para acercar la interfaz al estilo visual de Gemini.

El theming nativo de Streamlit (.streamlit/config.toml) no permite quitar el
borde/fondo de los `st.chat_message`, dar forma de píldora al `st.chat_input`
o pintar el saludo con el gradiente de marca — para eso hace falta CSS. Se
apunta siempre a `data-testid` documentados/estables de Streamlit (o a marcadores
propios), nunca a nombres de clase internos generados al azar.
"""
import streamlit as st

GRADIENT = "linear-gradient(90deg, #4285f4, #9168c0, #ee4c77)"

# --- Chrome global: header, navegación superior, tipografía ---
GLOBAL_CSS = f"""
<style>
/* El header por defecto de Streamlit no existe en Gemini: lo hacemos transparente
   en vez de ocultarlo, para conservar el menú (deploy/about) accesible. */
[data-testid="stHeader"] {{
    background: transparent;
}}

/* Navegación superior (Estudio / Ética y seguridad) como pestañas tipo Gemini */
[data-testid="stTopNavSection"] {{
    gap: 0.25rem;
}}
[data-testid="stTopNavLinkContainer"] a {{
    border-radius: 999px !important;
    padding: 0.4rem 1rem !important;
}}
[data-testid="stTopNavLinkContainer"] a[aria-selected="true"] {{
    background: #e8f0fe !important;
    color: #1a73e8 !important;
}}
</style>
"""

# --- Página de chat: burbujas, input tipo píldora, saludo con gradiente ---
CHAT_CSS = f"""
<style>
/* Quita el borde/fondo por defecto de los mensajes: Gemini no usa burbujas. */
[data-testid="stChatMessage"] {{
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0.35rem 0;
}}

/* El mensaje del usuario sí lleva un fondo suave tipo píldora (marcador propio
   + selector de hermano adyacente, no depende de internals de Streamlit). */
.gem-user-marker + [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {{
    background: #f0f4f9;
    border-radius: 20px;
    padding: 0.6rem 1rem;
    display: inline-block;
}}

/* Avatar con el gradiente de marca (el "spark" de Gemini) */
[data-testid="stChatMessageAvatarCustom"] {{
    background: {GRADIENT} !important;
}}
.gem-user-marker + [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarCustom"] {{
    background: #e8eaed !important;
}}

/* Input tipo píldora, fijo abajo */
[data-testid="stChatInput"] {{
    border-radius: 28px !important;
    border: 1px solid #e3e6ea !important;
    background: #f0f4f9 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
}}
[data-testid="stChatInputSubmitButton"] {{
    background: #1a73e8 !important;
    border-radius: 50% !important;
}}

/* Saludo centrado con el gradiente de marca (estado vacío, estilo "Hola, ...") */
.gem-greeting {{
    text-align: center;
    font-size: 2.3rem;
    font-weight: 500;
    background: {GRADIENT};
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: 0.25rem;
}}
.gem-subgreeting {{
    text-align: center;
    color: #5f6368;
    margin-bottom: 1.5rem;
}}

/* Tarjetas de sugerencia (grid de botones, en vez de píldoras) */
div[data-testid="stButton"] button {{
    border-radius: 16px !important;
}}
</style>
"""


def inject_global() -> None:
    st.html(GLOBAL_CSS)


def inject_chat() -> None:
    st.html(CHAT_CSS)


def user_marker() -> None:
    """Emitir justo antes de un st.chat_message de rol usuario, para que el
    selector CSS de hermano adyacente le aplique el fondo tipo píldora."""
    st.html('<div class="gem-user-marker"></div>')


def greeting(title: str, subtitle: str) -> None:
    st.html(f'<div class="gem-greeting">{title}</div><div class="gem-subgreeting">{subtitle}</div>')
