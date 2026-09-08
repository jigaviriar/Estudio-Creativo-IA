"""Auditoría de llamadas a Amazon Bedrock.

Lee `logs/bedrock_calls.jsonl` (generado por bedrock_client.py en cada
invocación, real o simulada) y muestra quién disparó cada llamada, qué modelo
se invocó, con qué parámetros (request) y qué respondió la API (response).
Es la evidencia técnica de que la app consume los modelos de verdad —
separada del feed de "Estudio" para no ensuciarlo con detalle técnico.
"""
import json

import streamlit as st

from config import LOGS_DIR

LOG_FILE = LOGS_DIR / "bedrock_calls.jsonl"

TASK_ICONS = {
    "generar_imagen": ":material/palette:",
    "editar_texto": ":material/edit_note:",
    "embeddings": ":material/dataset:",
}
TASK_LABELS = {
    "generar_imagen": "Generar imagen",
    "editar_texto": "Editar texto",
    "embeddings": "Embeddings (RAG)",
}


def load_entries() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    entries = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return list(reversed(entries))  # más reciente primero


def render_field(label: str, value, key: str) -> None:
    if value in (None, ""):
        return
    if isinstance(value, str) and len(value) > 160:
        st.caption(label)
        st.text_area(label, value, height=100, disabled=True, label_visibility="collapsed", key=key)
    else:
        st.markdown(f"**{label}:** {value}")


st.title("Auditoría", icon=":material/fact_check:")
st.caption(
    "Registro real de cada llamada a Amazon Bedrock: quién la disparó, qué modelo se invocó, "
    "con qué parámetros (request) y qué respondió la API (response). Evidencia técnica de que la "
    "app consume los modelos de verdad — no solo datos fijos (ver docs/3.2 y 3.3)."
)

entries = load_entries()

if not entries:
    st.info(
        "Todavía no hay llamadas registradas. Genera una imagen o edita un texto en **Estudio** "
        "para ver el registro aquí.",
        icon=":material/info:",
    )
else:
    real_calls = [e for e in entries if not e.get("demo_mode")]
    col1, col2, col3 = st.columns(3)
    col1.metric("Llamadas totales", len(entries))
    col2.metric("Llamadas reales a AWS", len(real_calls))
    if real_calls:
        avg_latency = sum(e["response"].get("latency_ms", 0) for e in real_calls) / len(real_calls)
        col3.metric("Latencia promedio", f"{avg_latency:.0f} ms")
    else:
        col3.metric("Latencia promedio", "—")

    tasks = sorted({e["task"] for e in entries})
    selected_tasks = st.multiselect(
        "Filtrar por tarea", tasks, default=tasks, format_func=lambda t: TASK_LABELS.get(t, t),
    )

    for i, entry in enumerate(entries):
        if entry["task"] not in selected_tasks:
            continue
        label = (
            f"{TASK_LABELS.get(entry['task'], entry['task'])} · {entry['model_id']} · "
            f"{entry['user']} · {entry['timestamp'][:16].replace('T', ' ')}"
        )
        with st.expander(label, icon=TASK_ICONS.get(entry["task"], ":material/bolt:")):
            if entry.get("demo_mode"):
                st.badge("Simulado (DEMO_MODE) — no llamó a AWS", icon=":material/science:", color="orange")
            if entry.get("region") and entry["region"] != "-":
                st.caption(f":material/location_on: Región: {entry['region']}")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Solicitud enviada**")
                for k, v in entry.get("request", {}).items():
                    render_field(k.replace("_", " ").capitalize(), v, key=f"req_{i}_{k}")
            with c2:
                st.markdown("**Respuesta recibida**")
                for k, v in entry.get("response", {}).items():
                    render_field(k.replace("_", " ").capitalize(), v, key=f"res_{i}_{k}")
