"""Moderación básica de contenido y cifrado en reposo (sección 3.6).

La moderación aquí es un filtro de palabras clave de MVP: sirve para
demostrar el flujo (bloquear antes de llamar a Bedrock y antes de mostrar
la salida). En producción se sustituiría por Amazon Bedrock Guardrails,
que se conecta pasando `guardrailIdentifier`/`guardrailVersion` en la
llamada a `invoke_model` sin cambiar el resto de la arquitectura.
"""
from __future__ import annotations

from cryptography.fernet import Fernet

from config import APP_ENCRYPTION_KEY
from prompts import BLOCKED_TERMS


class ModerationError(Exception):
    """Se lanza cuando la entrada o la salida viola la política de contenido."""


def moderate(text: str) -> None:
    lowered = text.lower()
    for term in BLOCKED_TERMS:
        if term in lowered:
            raise ModerationError(
                f"Contenido bloqueado por política de uso (se detectó: '{term}'). "
                "Ajusta la descripción y vuelve a intentarlo."
            )


def _fernet() -> Fernet | None:
    if not APP_ENCRYPTION_KEY:
        return None
    return Fernet(APP_ENCRYPTION_KEY.encode())


def encrypt_bytes(data: bytes) -> bytes:
    f = _fernet()
    return f.encrypt(data) if f else data


def decrypt_bytes(data: bytes) -> bytes:
    f = _fernet()
    return f.decrypt(data) if f else data


def encrypt_text(text: str) -> str:
    f = _fernet()
    return f.encrypt(text.encode()).decode() if f else text


def decrypt_text(text: str) -> str:
    f = _fernet()
    return f.decrypt(text.encode()).decode() if f else text


def encryption_enabled() -> bool:
    return _fernet() is not None
