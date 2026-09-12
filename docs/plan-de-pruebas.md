# Plan de pruebas de usuario

Checklist para validar la app antes de grabar la demo/video. Marca cada casilla a medida que
confirmes el resultado esperado.

## A. Generación de imágenes (rol Diseñador)

- [ ] **A1 — Caso feliz, Realismo.** Prompt: `Un frasco de perfume de lujo sobre mármol blanco, con pétalos de rosa y luz suave de estudio`.
  Verificar: imagen coherente, semilla visible, se puede descargar.
- [ ] **A2 — Caso feliz, Anime.** Prompt: `Una mascota de marca tipo zorro, estilo anime, colores vibrantes, sonriendo`.
  Verificar: el sufijo de estilo se aplicó (revisa en Auditoría el prompt real enviado).
- [ ] **A3 — Caso feliz, Óleo.** Prompt: `Un paisaje cafetero en Colombia al atardecer`, estilo "Pintura al óleo".
  Verificar: estilo aplicado correctamente.
- [ ] **A4 — Prompt negativo.** Prompt: `Un logo minimalista de una cafetería` · Negativo: `texto, letras, marcas de agua, borroso`.
  Verificar: la imagen no debería traer texto ni marcas de agua visibles.
- [ ] **A5 — Semilla reproducible.** Mismo prompt que A1, fija una semilla (ej. `42`) y genera dos veces.
  Verificar: ambas veces debe devolver semilla `42` (revisa `seed_used` en Auditoría).
- [ ] **A6 — Moderación, prompt principal.** Prompt: `Una escena de violencia gráfica extrema con sangre`.
  Verificar: debe bloquear con mensaje de error, sin llamar a Bedrock.
- [ ] **A7 — Moderación, prompt negativo.** Prompt limpio + Negativo: `contenido sexual explícito`.
  Verificar: también debe bloquear.

## B. Edición de texto (rol Redactor)

- [ ] **B1 — Resumir.** Texto: `Nuestra nueva línea de primavera combina esencias naturales con tecnología de vanguardia para ofrecer una fragancia que dura todo el día. Cada frasco es diseñado a mano por artesanos locales, usando vidrio reciclado y etiquetas biodegradables.`
  Verificar: resultado más corto, conserva las ideas clave.
- [ ] **B2 — Corregir.** Texto: `Nosotros a vamos ofrecer los mejores producto del mercado para todo nuestros clientes.`
  Verificar: corrige gramática sin inventar contenido nuevo.
- [ ] **B3 — Expandir.** Texto: `Nuestro nuevo perfume es elegante y duradero.`
  Verificar: desarrolla la idea sin inventar datos (fechas, precios, etc.).
- [ ] **B4 — Variaciones.** Cualquier texto corto de campaña.
  Verificar: debe devolver 3 propuestas numeradas.
- [ ] **B5 — Instrucciones adicionales.** Cualquier texto + "Instrucciones adicionales": `Máximo 2 frases, incluir llamado a la acción`.
  Verificar: el resultado respeta esa restricción.
- [ ] **B6 — Moderación de texto.** Pega un texto con contenido de odio/discriminatorio explícito.
  Verificar: debe bloquear antes de llamar a Claude.

## C. RAG (guía de marca)

- [ ] **C1 — Indexar guía.** Pega en el expander: `Tono cercano y cálido. Nunca usar la palabra "barato". Siempre mencionar que los ingredientes son 100% naturales.`
  Verificar: aparece el badge "N fragmentos activos".
- [ ] **C2 — Aplicar guía.** Edita (Corregir) el texto: `Este perfume barato es perfecto para el día a día.` con "Aplicar guía de marca" activado.
  Verificar: Claude debería evitar "barato" y/o mencionar ingredientes naturales.
- [ ] **C3 — Sin guía.** Repite B2/B3 sin activar la guía.
  Verificar: el resultado es distinto (para notar el efecto real del RAG).

## D. Colaboración y permisos

- [ ] **D1 — Comentar.** Como Aprobador, comenta una imagen y un texto.
  Verificar: comentario aparece con autor/rol/fecha.
- [ ] **D2 — Aprobar/Rechazar.** Cambia el estado de un ítem.
  Verificar: badge cambia de color e ícono.
- [ ] **D3 — Permiso Diseñador.** Cambia a Diseñador.
  Verificar: no debe poder editar texto ni aprobar.
- [ ] **D4 — Permiso Redactor.** Cambia a Redactor.
  Verificar: no debe poder generar imagen ni aprobar.

## E. Auditoría y reinicio

- [ ] **E1 — Evidencia real.** Después de A1 o B1, ve a Auditoría.
  Verificar: debe aparecer el registro con `RequestId` real de AWS (no vacío).
- [ ] **E2 — Filtro por tarea.** Usa el multiselect de Auditoría.
  Verificar: solo muestra las tareas seleccionadas.
- [ ] **E3 — Borrar auditoría.** Botón "Borrar" en Auditoría.
  Verificar: se vacía; el feed de Estudio no se ve afectado.
- [ ] **E4 — Borrar todo (Estudio).** Botón en la barra lateral de Estudio.
  Verificar: se vacía galería/contenido; Auditoría no se ve afectada.

## F. Manejo de errores (opcional)

- [ ] **F1 — Modelo inválido.** Cambia temporalmente `BEDROCK_TEXT_MODEL_ID` en `.env` a un valor inválido y genera un texto.
  Verificar: debe verse el mensaje amigable de `describe_error()` ("El modelo configurado no existe...") en vez de
  un traceback crudo de boto3. **Revierte el `.env` después de la prueba.**
