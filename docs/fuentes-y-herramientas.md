[← Índice](00-indice.md)

## Fuentes y herramientas

### Enunciado y guía del curso
- *Caso Práctico Unidad 3 — Generative AI* y *Guía del Trabajo Práctico* (Instituto Europeo de Posgrado). Definen el problema, las cuatro funcionalidades exigidas y la rúbrica de evaluación que guiaron todo el diseño (ver `docs/00-indice.md` en adelante).

### Servicios y modelos (Amazon Bedrock)
- **Amazon Bedrock** — capa de API gestionada usada vía `boto3` (`bedrock-runtime`, `invoke_model`) y `bedrock` (`list_foundation_models`, `list_inference_profiles`, `get_use_case_for_model_access`) para descubrir en tiempo real qué modelos e *inference profiles* estaban realmente disponibles y activos en la cuenta usada — en vez de asumir nombres de modelo de memoria, se consultaron directamente contra la API antes de fijarlos en el código (esto fue clave para detectar, por ejemplo, que Stable Diffusion XL ya no está disponible y que los modelos Claude recientes requieren *inference profile*). También se inspeccionó `response["ResponseMetadata"]` (`RequestId`) y el campo `usage` (tokens de entrada/salida) que devuelve la Messages API de Claude, para construir el log de auditoría de `app/bedrock_client.py`.
- **Stability AI — Stable Image Core** (texto → imagen) y **Anthropic Claude** (edición de texto) — documentación oficial de Amazon Bedrock para el formato de petición/respuesta de cada familia de modelos (`InvokeModel`, Messages API).
- **Amazon Titan Text Embeddings** — usado para los embeddings del RAG opcional sobre la guía de marca.

### Librerías y frameworks
- **Streamlit** (`st.chat_message`, `st.chat_input`, `st.navigation`/`st.Page`, `st.segmented_control`, theming vía `.streamlit/config.toml`) — documentación y guías de referencia oficiales del propio paquete instalado, consultadas para construir la interfaz de chat.
- **boto3 / botocore** — SDK oficial de AWS para Python; también se inspeccionó su código fuente instalado para confirmar el nombre exacto de la variable de entorno de autenticación por *Bedrock API key* (`AWS_BEARER_TOKEN_BEDROCK`) y el esquema de permisos de `PutUseCaseForModelAccess`.
- **cryptography (Fernet)** — cifrado simétrico en reposo para imágenes y contenido guardado localmente.
- **python-dotenv** — carga de variables de entorno desde `.env`.
- **pytest** — pruebas automatizadas (`tests/`) que verifican en CI/local los controles de la sección 3.6: bloqueo de contenido por `moderate()`, cifrado en reposo y permisos por rol.

### Metodología
Buena parte de las decisiones técnicas de este proyecto (IDs de modelo correctos, formato de payload de Stable Image, por qué `temperature` y `top_p` no pueden enviarse juntos, el requisito del formulario de "use case" de Anthropic) no se tomaron de memoria: se verificaron empíricamente contra la cuenta real de AWS Bedrock usada para el proyecto, iterando sobre los errores que la propia API devolvía hasta confirmar la configuración que funciona — documentado en `docs/3.3-modelos-y-parametros-de-inferencia.md`.

---
[← 3.7 Resumen de decisiones clave](3.7-resumen-de-decisiones-clave.md) · [Índice](00-indice.md)
