import pytest

from security import ModerationError, decrypt_text, encrypt_text, encryption_enabled, moderate


def test_moderate_blocks_forbidden_term():
    with pytest.raises(ModerationError):
        moderate("Genera una imagen de un arma de fuego apuntando a la cámara")


def test_moderate_allows_clean_text():
    moderate("Un logo minimalista para una cafetería de especialidad")


def test_encrypt_roundtrip_when_key_present():
    if not encryption_enabled():
        pytest.skip("APP_ENCRYPTION_KEY no está configurada en este entorno")
    original = "contenido de prueba con datos de marca"
    assert decrypt_text(encrypt_text(original)) == original


def test_encrypt_is_noop_without_key(monkeypatch):
    import security

    monkeypatch.setattr(security, "APP_ENCRYPTION_KEY", "")
    assert encryption_enabled() is False
    assert encrypt_text("texto plano") == "texto plano"
