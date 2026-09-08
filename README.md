# Estudio Creativo IA — Generación de imágenes y edición de contenido con Amazon Bedrock

Caso práctico de Generative AI — **Vía A: aplicación funcional**.

App Streamlit con **una interfaz única estilo chat** (tema oscuro moderno) que integra **Amazon Bedrock** para:
- generar imágenes con **Stability AI** (con selector de estilo: anime, óleo, realismo),
- editar y mejorar texto con **Claude** (resumir, expandir, corregir, generar variaciones),
- aplicar opcionalmente **RAG** sobre una guía de marca usando embeddings de **Amazon Titan**,
- colaborar por roles (diseñador, redactor, aprobador) con comentarios, aprobación e historial de versiones —
  todo en un solo feed conversacional compartido por el equipo,
- auditar cada llamada real a Bedrock (usuario, modelo, request, response) en una pestaña separada.

El documento de diseño completo (historias de usuario, arquitectura, modelos y parámetros, system prompt,
RAG/memoria, ética y seguridad) se entrega por separado, no en este repositorio.

## Estructura del proyecto

```
app/
  app.py                        # punto de entrada: st.navigation (tema oscuro en .streamlit/config.toml)
  config.py                     # configuración (región, IDs de modelo, flags)
  prompts.py                    # system prompt de Claude, plantillas de tarea, estilos de imagen
  security.py                   # moderación básica + cifrado en reposo (Fernet)
  storage.py                    # persistencia local (galería, historial de contenido, comentarios)
  bedrock_client.py             # wrapper: única capa que llama a bedrock-runtime
  rag.py                        # troceo, embeddings Titan e índice en memoria para la guía de marca
  auth.py                       # roles y permisos (selección de usuario demo)
  gemini_style.py               # CSS del tema Gemini (burbujas, saludo, input tipo píldora)
  .streamlit/config.toml        # tema oscuro moderno (chat-like)
  app_pages/
    chat.py                     # interfaz única: imágenes + edición de texto + colaboración, en un feed de chat
    etica_seguridad.py          # resumen de las salvaguardas activas
    auditoria.py                # registro de cada llamada real a Bedrock: usuario, modelo, request, response
  data/                         # se crea en tiempo de ejecución (gitignored)
tests/                           # pruebas pytest (moderación, cifrado, permisos por rol)
logs/                            # logs de ejecución y bedrock_calls.jsonl (se crea al arrancar, gitignored)
requirements.txt
requirements-dev.txt             # + pytest, para correr tests/
.env.example
```

## Requisitos previos

- Python 3.10+ (probado con 3.14).
- Una cuenta de AWS con acceso a Amazon Bedrock (ver nota sobre modelos de Anthropic más abajo):
  - Un modelo de texto-a-imagen de **Stability AI** (p. ej. `stability.stable-image-core-v1:1` — en algunas
    cuentas solo está disponible en `us-west-2`, aunque el resto lo uses en otra región).
  - Un modelo de **Anthropic Claude** vía *inference profile* (p. ej. `us.anthropic.claude-sonnet-4-5-20250929-v1:0`).
  - **Amazon Titan Text Embeddings** (`amazon.titan-embed-text-v2:0`).
  - El acceso puede tardar unos minutos en aprobarse tras solicitarlo.
- Credenciales de AWS configuradas localmente, por **una** de estas dos vías:
  - **Bedrock API key** (más simple): Consola AWS → **Amazon Bedrock** → **API keys** → *Generate*, y copia
    el token generado en `AWS_BEARER_TOKEN_BEDROCK` dentro de `.env`.
  - **Perfil de AWS CLI/SSO**:
    ```bash
    aws configure --profile mi-perfil
    # o, si tu organización usa SSO:
    aws configure sso --profile mi-perfil
    ```
    y pon el nombre del perfil en `AWS_PROFILE` dentro de `.env`.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # Windows: copy .env.example .env
```

Edita `.env`:
- `AWS_BEARER_TOKEN_BEDROCK` **o** `AWS_PROFILE` (nunca los dos secretos en la misma variable — `AWS_PROFILE`
  solo acepta un *nombre* de perfil, no un token).
- `AWS_REGION`: región donde tienes habilitado el acceso a los modelos (Bedrock no está en todas las regiones).
- `APP_ENCRYPTION_KEY`: genera una clave propia con:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- Deja `DEMO_MODE=false` si ya tienes acceso real a los modelos.

## Ejecutar

```bash
streamlit run app/app.py
```

Abre el enlace que muestra la terminal (por defecto http://localhost:8501).

Si prefieres correrla en segundo plano y guardar la salida en archivo (útil para dejarla corriendo mientras trabajas en otra cosa):
```bash
mkdir -p logs
streamlit run app/app.py --server.headless true > logs/streamlit.log 2>&1 &
```

## Pruebas automatizadas

Verifican los controles de la sección 3.6 (ética y seguridad): moderación de contenido, cifrado en reposo
y permisos por rol.

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## ¿Sin acceso a AWS todavía?

Pon `DEMO_MODE=true` en `.env`. La interfaz funciona igual, pero `bedrock_client.py` devuelve respuestas
simuladas en vez de llamar a `invoke_model`. El código de la llamada real queda igual de visible y
comentado en ese archivo — es la integración que se ejecutaría en cuanto actives el acceso.

## Flujo de prueba sugerido (para la demo/video)

1. Cambia el "Usuario activo (demo)" en la barra lateral entre los tres roles y observa cómo cambia lo que
   puedes hacer (el feed del chat es el mismo para todos; los controles cambian según el rol).
2. Como **Diseñador**: escribe una descripción en el chat, ajusta el estilo en :material/tune: *Opciones de
   imagen* y genera la imagen. Descárgala desde el propio mensaje.
3. Como **Redactor**: escribe un texto en el chat para crear un contenido, elige la acción (Corregir,
   Variaciones...) en :material/tune: *Opciones de edición* y pulsa **Aplicar**. Cada versión queda como un
   turno nuevo en el feed (así se ve el historial).
4. (Opcional) Sube una guía de marca desde el expander de la barra lateral y activa "Aplicar guía de marca"
   antes de pulsar Aplicar.
5. Como **Aprobador**: en el mismo feed, comenta una imagen o un texto y cambia su estado a "Aprobado" o
   "Rechazado".
6. Ve a la pestaña **Ética y seguridad** (arriba) para ver las salvaguardas activas (moderación, cifrado,
   system prompt).
7. Ve a la pestaña **Auditoría** para ver el detalle real de cada llamada a Bedrock que acabas de generar:
   usuario, modelo, request enviado, tokens/semilla y el `RequestId` de AWS como evidencia de que la llamada
   ocurrió de verdad (no aplica en `DEMO_MODE`, donde se marca como simulada).
8. (Opcional, antes de grabar de nuevo) En la barra lateral de **Estudio**, usa "Borrar todo y empezar de
   nuevo" para limpiar los datos de prueba — pide confirmación explícita antes de borrar.

## Notas de seguridad

- Nunca subas `.env` al repositorio (ya está en `.gitignore`).
- Las claves de AWS y la clave de cifrado son solo ejemplos con marcador de posición (`MY_SECRET_HERE`) en
  `.env.example`; complétalas localmente con tus propios valores.
- Este es un MVP académico: el "login" por roles es una simplificación sin autenticación real (en producción
  se recomendaría Amazon Cognito o el SSO corporativo existente).
