"""RAG opcional sobre la guía de marca (sección 3.5 del documento de diseño).

Trocea un documento de texto, genera embeddings con Amazon Titan y guarda un
índice en memoria de proceso (st.session_state). Suficiente para un MVP; en
producción se sustituiría por un vector store gestionado (p. ej. OpenSearch
Serverless) para persistir el índice entre sesiones y escalar el volumen.
"""
from __future__ import annotations

import math

from bedrock_client import embed_text

CHUNK_SIZE = 800  # caracteres por fragmento, aproximación simple para el MVP


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 1 > chunk_size and current:
            chunks.append(current)
            current = p
        else:
            current = f"{current}\n{p}" if current else p
    if current:
        chunks.append(current)
    return chunks


def build_index(text: str, user: str = "") -> list[dict]:
    """Devuelve una lista de {text, embedding} lista para guardar en session_state."""
    return [{"text": chunk, "embedding": embed_text(chunk, user=user)} for chunk in chunk_text(text)]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve(index: list[dict], query: str, top_k: int = 2, user: str = "") -> str:
    """Recupera los fragmentos más relevantes de la guía de marca para el texto dado."""
    if not index:
        return ""
    query_vec = embed_text(query, user=user)
    scored = sorted(index, key=lambda item: _cosine(item["embedding"], query_vec), reverse=True)
    top = scored[:top_k]
    return "\n---\n".join(item["text"] for item in top)
