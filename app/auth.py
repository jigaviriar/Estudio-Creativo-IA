"""Control de acceso por rol (sección 3 · Colaboración y flujo de trabajo).

Simplificación deliberada de MVP: el "login" es una selección de usuario
demo en la barra lateral, sin contraseña. Sustituye a un sistema de
identidad real. En producción se recomienda Amazon Cognito (o el SSO
corporativo existente) para autenticación real y roles gestionados de forma
centralizada — ver docs/3.7-resumen-de-decisiones-clave.md.
"""
from __future__ import annotations

import streamlit as st

from config import DEMO_USERS

PERMISSIONS = {
    "Diseñador": {"generar_imagen", "ver_galeria", "comentar"},
    "Redactor": {"editar_contenido", "ver_historial", "comentar"},
    "Aprobador": {"ver_galeria", "ver_historial", "comentar", "aprobar"},
}


def current_user() -> tuple[str, str]:
    """Devuelve (nombre_usuario, rol) según la selección activa en la sesión."""
    if "demo_user" not in st.session_state:
        st.session_state.demo_user = list(DEMO_USERS)[0]
    user = st.session_state.demo_user
    return user, DEMO_USERS[user]


def render_user_switcher() -> None:
    with st.sidebar:
        st.selectbox(
            "Usuario activo (demo)",
            options=list(DEMO_USERS),
            key="demo_user",
            format_func=lambda u: f"{u} — {DEMO_USERS[u]}",
        )
        user, role = current_user()
        st.caption(f"Sesión: **{user}** · Rol: **{role}**")


def can(permission: str) -> bool:
    _, role = current_user()
    return permission in PERMISSIONS.get(role, set())


def require(permission: str) -> bool:
    """Muestra un aviso y devuelve False si el rol activo no tiene el permiso."""
    if not can(permission):
        _, role = current_user()
        st.warning(f"Tu rol actual ({role}) no tiene permiso para esta acción.")
        return False
    return True
