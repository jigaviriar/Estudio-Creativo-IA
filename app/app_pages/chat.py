"""Estudio Creativo IA — interfaz única estilo chat.

Todas las funcionalidades (generación de imágenes, edición de texto, guía de
marca/RAG, colaboración con comentarios y aprobación) viven en un solo feed
conversacional compartido por el equipo, con permisos según el rol activo.
"""
import streamlit as st
from botocore.exceptions import ClientError

import chat_style
from auth import can, current_user, render_user_switcher
from bedrock_client import edit_text, generate_image
from prompts import STYLE_SUFFIXES, TASK_LABELS
from rag import build_index, retrieve
from security import ModerationError
from storage import (
    add_comment,
    add_image,
    add_version,
    clear_all,
    create_content,
    get_content,
    load_content,
    load_gallery,
    read_image_bytes,
    set_status,
)

# La evidencia de cada llamada a Bedrock (modelo, request, respuesta) vive en
# la página "Auditoría" (app_pages/auditoria.py), no en este feed.

ASSISTANT_AVATAR = ":material/auto_awesome:"
ROLE_AVATARS = {
    "Diseñador": ":material/design_services:",
    "Redactor": ":material/edit_note:",
    "Aprobador": ":material/fact_check:",
}
STATUS_BADGE = {
    "pendiente": ("Pendiente de revisión", ":material/schedule:", "orange"),
    "aprobado": ("Aprobado", ":material/check:", "green"),
    "rechazado": ("Rechazado", ":material/close:", "red"),
}
IMAGE_SUGGESTIONS = {
    "Logo de cafetería": (":material/local_cafe:", "Un logo minimalista para una cafetería de especialidad, con una taza de café humeante"),
    "Frasco de perfume": (":material/spa:", "Un frasco de perfume elegante sobre mármol negro, con luz dorada de estudio"),
}
FRIENDLY_AWS_ERRORS = {
    "AccessDeniedException": "Tu cuenta de AWS no tiene acceso a este modelo todavía. Solicítalo en la consola: Amazon Bedrock → Model access.",
    "ThrottlingException": "Bedrock está limitando las solicitudes en este momento. Espera unos segundos y vuelve a intentar.",
    "ResourceNotFoundException": "El modelo configurado no existe o no está disponible en esta región. Revisa BEDROCK_*_MODEL_ID en .env.",
}


def describe_error(e: Exception) -> str:
    """Traduce errores comunes de Bedrock a un mensaje accionable para el usuario."""
    if isinstance(e, ClientError):
        error = e.response.get("Error", {})
        return FRIENDLY_AWS_ERRORS.get(error.get("Code", ""), error.get("Message", str(e)))
    return str(e)


TEXT_SUGGESTIONS = {
    "Copy de lanzamiento": (":material/campaign:", "Lanzamiento — Línea Primavera",
        "Nuestra nueva línea de primavera combina esencias naturales con tecnología de "
        "vanguardia para ofrecer una fragancia que dura todo el día. Cada frasco es "
        "diseñado a mano por artesanos locales."),
    "Email a clientes": (":material/mail:", "Email — Reactivación de clientes",
        "Hola, hace tiempo no sabemos de ti. Queremos invitarte a probar nuestras "
        "novedades con un descuento especial solo por esta semana."),
}


def render_sidebar() -> None:
    render_user_switcher()
    with st.sidebar:
        with st.expander("Guía de marca (RAG)", icon=":material/menu_book:"):
            st.caption(
                "Súbela una vez: las ediciones de texto podrán apoyarse en tu manual "
                "de estilo (tono, términos prohibidos, claims permitidos)."
            )
            uploaded = st.file_uploader("Archivo .txt", type=["txt"], label_visibility="collapsed")
            pasted = st.text_area("O pega el texto aquí", height=100, label_visibility="collapsed")
            source_text = uploaded.read().decode("utf-8", errors="ignore") if uploaded else pasted
            if st.button("Indexar guía", disabled=not source_text, icon=":material/upload:"):
                user, _ = current_user()
                with st.spinner("Generando embeddings con Titan..."):
                    st.session_state["brand_index"] = build_index(source_text, user=user)
                st.toast(f"Guía indexada: {len(st.session_state['brand_index'])} fragmentos.", icon=":material/check:")
            if st.session_state.get("brand_index"):
                st.badge(f"{len(st.session_state['brand_index'])} fragmentos activos", icon=":material/check:", color="green")

        with st.popover(":material/delete_sweep: Borrar todo y empezar de nuevo"):
            st.caption(
                "Elimina permanentemente todas las imágenes, textos, versiones y comentarios "
                "del feed compartido. No se puede deshacer."
            )
            confirm = st.checkbox("Confirmo que quiero borrar todo")
            if st.button("Borrar todo permanentemente", icon=":material/delete_forever:",
                         type="primary", disabled=not confirm):
                clear_all()
                st.session_state.pop("brand_index", None)
                st.toast("Feed borrado.", icon=":material/check:")
                st.rerun()


def build_feed() -> list[dict]:
    turns = []
    for item in load_gallery():
        turns.append({"ts": item["timestamp"], "kind": "image", "item": item})
    for item in load_content():
        for version in item["versions"]:
            turns.append({
                "ts": version["timestamp"],
                "kind": "content_version",
                "item": item,
                "version": version,
                "is_latest": version["n"] == item["versions"][-1]["n"],
            })
    return sorted(turns, key=lambda t: t["ts"])


def render_item_footer(store: str, item: dict) -> None:
    status = item["status"]
    label, icon, color = STATUS_BADGE[status]
    st.badge(label, icon=icon, color=color)

    for c in item["comments"]:
        st.caption(f"**{c['author']}** ({c['role']}) · {c['timestamp'][:16].replace('T', ' ')}")
        st.write(c["text"])

    cols = st.columns([3, 1]) if can("comentar") else [None]
    if can("comentar"):
        with cols[0]:
            comment_text = st.text_input(
                "Comentario", key=f"comment_{store}_{item['id']}",
                placeholder="Escribe un comentario...", label_visibility="collapsed",
            )
        with cols[1]:
            if st.button("Comentar", key=f"btn_comment_{store}_{item['id']}", disabled=not comment_text, icon=":material/send:"):
                user, role = current_user()
                add_comment(store, item["id"], author=user, role=role, text=comment_text)
                st.rerun()

    if can("aprobar"):
        new_status = st.segmented_control(
            "Estado", options=["pendiente", "aprobado", "rechazado"],
            format_func=lambda s: STATUS_BADGE[s][0], default=status,
            key=f"status_{store}_{item['id']}",
        )
        if new_status and new_status != status:
            set_status(store, item["id"], new_status)
            st.rerun()


def render_feed(turns: list[dict]) -> None:
    for turn in turns:
        if turn["kind"] == "image":
            item = turn["item"]
            chat_style.user_marker()
            with st.chat_message("user", avatar=ROLE_AVATARS.get(item["role"], ":material/person:")):
                st.markdown(f":material/palette: **Generar imagen** · estilo _{item['style']}_")
                st.write(item["prompt_plain"])
                st.caption(f"{item['author']} · {item['timestamp'][:16].replace('T', ' ')}")
            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                st.image(read_image_bytes(item), width=380)
                st.caption(f"Semilla: {item['seed']}")
                st.download_button(
                    "Descargar", data=read_image_bytes(item), file_name=f"{item['id']}.png",
                    mime="image/png", key=f"dl_{item['id']}", icon=":material/download:",
                )
                render_item_footer("gallery", item)

        elif turn["kind"] == "content_version":
            item, version = turn["item"], turn["version"]
            if version["action"] == "original":
                chat_style.user_marker()
                with st.chat_message("user", avatar=ROLE_AVATARS.get(version["role"], ":material/person:")):
                    st.markdown(f":material/description: **{item['title']}**")
                    st.write(version["text_plain"])
                    st.caption(f"{version['author']} · {version['timestamp'][:16].replace('T', ' ')}")
            else:
                chat_style.user_marker()
                with st.chat_message("user", avatar=ROLE_AVATARS.get(version["role"], ":material/person:")):
                    st.markdown(f":material/bolt: **{TASK_LABELS.get(version['action'], version['action'])}** · _{item['title']}_")
                    st.caption(f"{version['author']} · {version['timestamp'][:16].replace('T', ' ')}")
                with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                    st.write(version["text_plain"])
                    if turn["is_latest"]:
                        render_item_footer("content", item)


def handle_image_composer() -> None:
    user, role = current_user()
    if not load_gallery():
        cols = st.columns(2)
        for col, (label, (icon, prompt_text)) in zip(cols, IMAGE_SUGGESTIONS.items()):
            with col:
                if st.button(label, icon=icon, key=f"sugg_img_{label}", width="stretch"):
                    if _run_image_generation(prompt_text, "Realismo", "", None, user, role):
                        st.rerun()

    with st.popover(":material/tune: Opciones de imagen"):
        style = st.segmented_control("Estilo", options=list(STYLE_SUFFIXES.keys()), default="Realismo")
        negative_prompt = st.text_input("Prompt negativo (opcional)", placeholder="borroso, mal recortado, texto")
        use_seed = st.checkbox("Fijar semilla")
        seed = st.number_input("Semilla", min_value=0, max_value=2**31 - 1, value=42, disabled=not use_seed)

    st.caption(
        ":material/copyright: Evita pedir el estilo de un artista o marca protegida concretos. "
        "Valida con legal antes de publicar imágenes generadas por IA."
    )
    prompt = st.chat_input("Describe la imagen que quieres generar...", submit_mode="disable")
    if prompt:
        if _run_image_generation(prompt, style or "Realismo", negative_prompt, seed if use_seed else None, user, role):
            st.rerun()


def _run_image_generation(prompt, style, negative_prompt, seed, user, role) -> bool:
    """Devuelve True si la imagen se generó y guardó con éxito (para que el
    llamador solo haga st.rerun() en ese caso; si no, el error debe quedar
    visible en pantalla en vez de borrarse en el siguiente rerun)."""
    chat_style.user_marker()
    with st.chat_message("user", avatar=ROLE_AVATARS.get(role)):
        st.markdown(f":material/palette: **Generar imagen** · estilo _{style}_")
        st.write(prompt)
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        try:
            with st.status(":shimmer[Generando imagen]", type="compact") as status:
                image_bytes, used_seed = generate_image(prompt, style, negative_prompt, seed, user=user)
                status.update(label="Imagen lista", state="complete")
            st.image(image_bytes, width=380)
            add_image(image_bytes, prompt=prompt, style=style, seed=used_seed, author=user, role=role)
            return True
        except ModerationError as e:
            st.error(str(e), icon=":material/block:")
        except Exception as e:
            st.error(f"No se pudo generar la imagen: {describe_error(e)}", icon=":material/error:")
    return False


def handle_text_composer() -> None:
    user, role = current_user()
    content_items = load_content()

    options = {"Nuevo contenido": None} | {f"{it['title']}": it["id"] for it in content_items}
    # No se puede reasignar la key de un widget ya instanciado en el mismo run:
    # los botones/inputs de más abajo dejan la selección deseada aquí, y la
    # aplicamos justo antes de crear el selectbox (nunca después).
    if "_pending_active_label" in st.session_state:
        st.session_state["active_content_label"] = st.session_state.pop("_pending_active_label")
    if st.session_state.get("active_content_label") not in options:
        st.session_state["active_content_label"] = "Nuevo contenido"
    selected_label = st.selectbox(
        ":material/folder_open: Contenido activo", options=list(options.keys()), key="active_content_label",
    )
    st.session_state["active_content_id"] = options[selected_label]

    if st.session_state["active_content_id"] is None:
        if not content_items:
            cols = st.columns(2)
            for col, (label, (icon, title, text)) in zip(cols, TEXT_SUGGESTIONS.items()):
                with col:
                    if st.button(label, icon=icon, key=f"sugg_txt_{label}", width="stretch"):
                        item = create_content(title, text, author=user, role=role)
                        st.session_state["_pending_active_label"] = item["title"]
                        st.rerun()

        message = st.chat_input("Escribe o pega el texto que quieres mejorar...")
        if message:
            title = (message[:40] + "…") if len(message) > 40 else message
            chat_style.user_marker()
            with st.chat_message("user", avatar=ROLE_AVATARS.get(role)):
                st.markdown(f":material/description: **{title}**")
                st.write(message)
            item = create_content(title, message, author=user, role=role)
            st.session_state["_pending_active_label"] = item["title"]
            st.rerun()
        return

    content = get_content(st.session_state["active_content_id"])
    current_text = content["versions"][-1]["text_plain"]

    use_brand_guide = False
    with st.popover(":material/tune: Opciones de edición"):
        task = st.segmented_control("Acción", options=list(TASK_LABELS.keys()), format_func=lambda k: TASK_LABELS[k], default="corregir")
        tono = st.selectbox("Tono", options=["profesional", "cercano y conversacional", "formal y corporativo", "entusiasta"])
        if st.session_state.get("brand_index"):
            use_brand_guide = st.checkbox("Aplicar guía de marca", value=True)
        extra = st.text_input("Instrucciones adicionales (opcional)", placeholder="Máximo 2 frases, incluir llamado a la acción...")

    if st.button("Aplicar", type="primary", icon=":material/play_arrow:", disabled=not task):
        chat_style.user_marker()
        with st.chat_message("user", avatar=ROLE_AVATARS.get(role)):
            st.markdown(f":material/bolt: **{TASK_LABELS[task]}** · _{content['title']}_")
        success = False
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            try:
                brand_context = retrieve(st.session_state["brand_index"], current_text, user=user) if use_brand_guide else ""
                with st.status(":shimmer[Escribiendo]", type="compact") as status:
                    result = edit_text(task, current_text, tono=tono, extra_instructions=extra, brand_context=brand_context, user=user)
                    status.update(label="Listo", state="complete")
                st.write(result)
                add_version(content["id"], action=task, text=result, author=user, role=role)
                success = True
            except ModerationError as e:
                st.error(str(e), icon=":material/block:")
            except Exception as e:
                st.error(f"No se pudo editar el texto: {describe_error(e)}", icon=":material/error:")
        # Solo recargamos si funcionó: si hubo error, st.rerun() lo borraría
        # de la pantalla antes de que puedas leerlo.
        if success:
            st.rerun()

    message = st.chat_input("Escribe o pega un texto distinto para empezar otro contenido...")
    if message:
        title = (message[:40] + "…") if len(message) > 40 else message
        item = create_content(title, message, author=user, role=role)
        st.session_state["_pending_active_label"] = item["title"]
        st.rerun()


chat_style.inject_chat()

render_sidebar()

user, role = current_user()
can_image = can("generar_imagen")
can_text = can("editar_contenido")

feed = build_feed()

if not feed:
    chat_style.greeting(f"Hola, {user.split(' ')[0].capitalize()}", "¿Qué vamos a crear hoy?")
else:
    st.caption(":material/auto_awesome: Estudio Creativo IA")
render_feed(feed)

if can_image and can_text:
    mode = st.segmented_control("Modo", options=["imagen", "texto"], format_func=lambda m: "Generar imagen" if m == "imagen" else "Editar contenido", default="imagen", key="chat_mode")
elif can_image:
    mode = "imagen"
elif can_text:
    mode = "texto"
else:
    mode = None

if mode == "imagen":
    handle_image_composer()
elif mode == "texto":
    handle_text_composer()
else:
    st.caption(f"Tu rol ({role}) solo permite revisar, comentar y aprobar. Cambia de usuario en la barra lateral para generar contenido.")
