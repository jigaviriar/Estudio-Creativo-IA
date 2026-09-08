"""Wrapper de la aplicación sobre Amazon Bedrock (sección 3.2 del documento
de diseño). Centraliza: control de moderación, construcción de prompts,
parámetros de inferencia por tarea, e invocación real a bedrock-runtime.

Si DEMO_MODE=true (config.py), no se llama a AWS: se devuelven respuestas
simuladas para poder probar la interfaz sin credenciales. El código de la
llamada real queda igual de visible y comentado, tal como pide el enunciado
para quienes no tengan acceso a AWS.

Cada invocación (real o simulada) queda registrada en `logs/bedrock_calls.jsonl`
con quién la disparó, el modelo, el request y la respuesta — es la fuente de
datos de la página "Auditoría" (app_pages/auditoria.py), que demuestra que la
app efectivamente llama a los modelos y no solo muestra datos fijos.
"""
from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone

import boto3
from botocore.config import Config

import config
from prompts import STYLE_SUFFIXES, TASK_PARAMS, build_system_prompt, build_user_prompt
from security import moderate


def _record(*, user: str, task: str, model_id: str, region: str, demo_mode: bool,
            request: dict, response: dict) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user": user or "(desconocido)",
        "task": task,
        "model_id": model_id,
        "region": region,
        "demo_mode": demo_mode,
        "request": request,
        "response": response,
    }
    with open(config.LOGS_DIR / "bedrock_calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _bedrock_runtime(region: str | None = None):
    # Si hay un Bedrock API key (AWS_BEARER_TOKEN_BEDROCK en el entorno), boto3 lo
    # detecta solo al crear el cliente: no se debe forzar un perfil en ese caso.
    profile = None if config.USING_BEARER_TOKEN else config.AWS_PROFILE
    session = boto3.Session(profile_name=profile, region_name=region or config.AWS_REGION)
    return session.client("bedrock-runtime", config=Config(retries={"max_attempts": 3}))


def generate_image(prompt: str, style: str, negative_prompt: str = "", seed: int | None = None,
                    steps: int = 30, cfg_scale: float = 7.0, user: str = "") -> tuple[bytes, int]:
    """Genera una imagen con Stability AI (Stable Image) vía Bedrock. Devuelve (bytes_png, seed_usado).

    `steps` y `cfg_scale` se mantienen en la firma por compatibilidad con la UI, pero los
    modelos "Stable Image" (sucesores de Stable Diffusion XL en Bedrock) no los usan: solo
    aceptan `prompt`, `negative_prompt`, `seed` y `output_format`.
    """
    moderate(prompt)
    if negative_prompt:
        moderate(negative_prompt)

    styled_prompt = prompt
    if STYLE_SUFFIXES.get(style):
        styled_prompt = f"{prompt}, {STYLE_SUFFIXES[style]}"

    request_info = {"prompt": prompt, "style": style, "negative_prompt": negative_prompt or None,
                     "seed_requested": seed}
    start = time.perf_counter()

    if config.DEMO_MODE:
        # Respuesta simulada: un PNG de 1x1 para que la UI funcione sin AWS.
        pixel_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        latency_ms = (time.perf_counter() - start) * 1000
        _record(user=user, task="generar_imagen", model_id="(simulado)", region="-", demo_mode=True,
                request=request_info, response={"seed_used": seed or 0, "latency_ms": round(latency_ms, 1)})
        return pixel_png, seed or 0

    body = {"prompt": styled_prompt, "output_format": "png"}
    if negative_prompt:
        body["negative_prompt"] = negative_prompt
    if seed is not None:
        body["seed"] = seed

    response = _bedrock_runtime(config.IMAGE_REGION).invoke_model(
        modelId=config.IMAGE_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    latency_ms = (time.perf_counter() - start) * 1000
    payload = json.loads(response["body"].read())
    image_bytes = base64.b64decode(payload["images"][0])
    used_seed = payload.get("seeds", [seed or 0])[0]
    request_id = response["ResponseMetadata"].get("RequestId", "")
    _record(user=user, task="generar_imagen", model_id=config.IMAGE_MODEL_ID, region=config.IMAGE_REGION,
            demo_mode=False, request=request_info,
            response={"seed_used": used_seed, "latency_ms": round(latency_ms, 1), "request_id": request_id})
    return image_bytes, used_seed


def edit_text(task: str, text: str, tono: str = "profesional", extra_instructions: str = "",
              brand_context: str = "", user: str = "") -> str:
    """Edita texto con Claude vía Bedrock. task in {resumir, corregir, expandir, variaciones}."""
    moderate(text)

    temperature, max_tokens = TASK_PARAMS[task]
    system_prompt = build_system_prompt(tono)
    user_prompt = build_user_prompt(task, text, extra_instructions, brand_context)

    request_info = {
        "tarea": task, "tono": tono, "temperature": temperature, "max_tokens": max_tokens,
        "texto_original": text, "instrucciones_adicionales": extra_instructions or None,
        "guia_de_marca_aplicada": bool(brand_context),
    }
    start = time.perf_counter()

    if config.DEMO_MODE:
        latency_ms = (time.perf_counter() - start) * 1000
        _record(user=user, task="editar_texto", model_id="(simulado)", region="-", demo_mode=True,
                request=request_info, response={"latency_ms": round(latency_ms, 1)})
        return f"[DEMO_MODE] Resultado simulado de la tarea '{task}' sobre el texto proporcionado."

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": system_prompt,
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    response = _bedrock_runtime().invoke_model(
        modelId=config.TEXT_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    latency_ms = (time.perf_counter() - start) * 1000
    payload = json.loads(response["body"].read())
    result = payload["content"][0]["text"]
    usage = payload.get("usage", {})
    request_id = response["ResponseMetadata"].get("RequestId", "")

    moderate(result)
    _record(user=user, task="editar_texto", model_id=config.TEXT_MODEL_ID, region=config.AWS_REGION,
            demo_mode=False, request=request_info,
            response={
                "resultado": result, "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"), "latency_ms": round(latency_ms, 1),
                "request_id": request_id,
            })
    return result


def embed_text(text: str, user: str = "") -> list[float]:
    """Genera un embedding con Amazon Titan (usado por rag.py)."""
    request_info = {"texto": text}
    start = time.perf_counter()

    if config.DEMO_MODE:
        # Vector determinístico falso basado en el largo del texto, solo para
        # que la demo de similitud funcione sin llamar a AWS.
        latency_ms = (time.perf_counter() - start) * 1000
        _record(user=user, task="embeddings", model_id="(simulado)", region="-", demo_mode=True,
                request=request_info, response={"latency_ms": round(latency_ms, 1)})
        return [float((hash(text) >> i) % 100) / 100 for i in range(64)]

    response = _bedrock_runtime().invoke_model(
        modelId=config.EMBED_MODEL_ID,
        body=json.dumps({"inputText": text}),
        contentType="application/json",
        accept="application/json",
    )
    latency_ms = (time.perf_counter() - start) * 1000
    payload = json.loads(response["body"].read())
    request_id = response["ResponseMetadata"].get("RequestId", "")
    _record(user=user, task="embeddings", model_id=config.EMBED_MODEL_ID, region=config.AWS_REGION,
            demo_mode=False, request=request_info,
            response={"input_tokens": payload.get("inputTextTokenCount"), "latency_ms": round(latency_ms, 1),
                      "request_id": request_id})
    return payload["embedding"]
