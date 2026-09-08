"""Almacenamiento local para galería de imágenes, historial de versiones de
contenido y comentarios. Usa JSON simple (suficiente para un MVP); los
campos de texto e imágenes se cifran en reposo si APP_ENCRYPTION_KEY está
configurada (ver security.py y sección 3.6 del documento de diseño).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR, IMAGES_DIR
from security import decrypt_bytes, decrypt_text, encrypt_bytes, encrypt_text

GALLERY_FILE = DATA_DIR / "gallery.json"
CONTENT_FILE = DATA_DIR / "content.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, items: list[dict]) -> None:
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- Galería de imágenes ----------

def add_image(image_bytes: bytes, prompt: str, style: str, seed, author: str, role: str) -> dict:
    item_id = uuid.uuid4().hex[:12]
    filename = f"{item_id}.bin"
    (IMAGES_DIR / filename).write_bytes(encrypt_bytes(image_bytes))
    item = {
        "id": item_id,
        "filename": filename,
        "prompt": encrypt_text(prompt),
        "style": style,
        "seed": seed,
        "author": author,
        "role": role,
        "timestamp": _now(),
        "status": "pendiente",
        "comments": [],
    }
    items = _load(GALLERY_FILE)
    items.append(item)
    _save(GALLERY_FILE, items)
    return item


def load_gallery() -> list[dict]:
    items = _load(GALLERY_FILE)
    for item in items:
        item["prompt_plain"] = decrypt_text(item["prompt"])
    return sorted(items, key=lambda x: x["timestamp"], reverse=True)


def read_image_bytes(item: dict) -> bytes:
    return decrypt_bytes((IMAGES_DIR / item["filename"]).read_bytes())


# ---------- Contenido de texto (con historial de versiones) ----------

def create_content(title: str, text: str, author: str, role: str) -> dict:
    item = {
        "id": uuid.uuid4().hex[:12],
        "title": title,
        "status": "pendiente",
        "comments": [],
        "versions": [
            {"n": 1, "action": "original", "text": encrypt_text(text), "author": author, "role": role, "timestamp": _now()}
        ],
    }
    items = _load(CONTENT_FILE)
    items.append(item)
    _save(CONTENT_FILE, items)
    return item


def add_version(content_id: str, action: str, text: str, author: str, role: str) -> None:
    items = _load(CONTENT_FILE)
    for item in items:
        if item["id"] == content_id:
            next_n = max(v["n"] for v in item["versions"]) + 1
            item["versions"].append(
                {"n": next_n, "action": action, "text": encrypt_text(text), "author": author, "role": role, "timestamp": _now()}
            )
            break
    _save(CONTENT_FILE, items)


def load_content() -> list[dict]:
    items = _load(CONTENT_FILE)
    for item in items:
        for v in item["versions"]:
            v["text_plain"] = decrypt_text(v["text"])
    return sorted(items, key=lambda x: x["versions"][-1]["timestamp"], reverse=True)


def get_content(content_id: str) -> dict | None:
    for item in load_content():
        if item["id"] == content_id:
            return item
    return None


# ---------- Comentarios y aprobación (compartido por imágenes y contenido) ----------

def add_comment(store: str, item_id: str, author: str, role: str, text: str) -> None:
    path = GALLERY_FILE if store == "gallery" else CONTENT_FILE
    items = _load(path)
    for item in items:
        if item["id"] == item_id:
            item["comments"].append({"author": author, "role": role, "text": text, "timestamp": _now()})
            break
    _save(path, items)


def set_status(store: str, item_id: str, status: str) -> None:
    path = GALLERY_FILE if store == "gallery" else CONTENT_FILE
    items = _load(path)
    for item in items:
        if item["id"] == item_id:
            item["status"] = status
            break
    _save(path, items)


# ---------- Reinicio del feed ----------

def clear_all() -> None:
    """Borra permanentemente toda la galería, el contenido y las imágenes guardadas.
    Irreversible: pensado para limpiar datos de prueba, no para uso normal del equipo."""
    for path in (GALLERY_FILE, CONTENT_FILE):
        if path.exists():
            path.unlink()
    for image_file in IMAGES_DIR.glob("*.bin"):
        image_file.unlink()
