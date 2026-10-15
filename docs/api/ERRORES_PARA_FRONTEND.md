# Errores de la API para el frontend

Estado: **verificado** contra el backend de la rama `docs/api-frontend` (10–11 oct 2026).
Los ejemplos reales están en [`ejemplos/`](ejemplos/INDICE.json), generados con
`backend/scripts/generar_ejemplos_api.py` sobre Postgres pgvector **desechable** y con el
proveedor de IA mockeado. No se usó ningún dato personal.

Todo lo que aquí figura como "hoy" existe en el código. Lo marcado como **propuesta**
no existe todavía.

---

## 1. Formato de error

| Origen | Cuerpo | Ejemplo real |
|---|---|---|
| Errores de negocio (`ServiceError`: 403, 404, 409, 400) y `HTTPException` | `{"detail": "texto"}` | `403`: `{"detail": "Solo el autor puede modificar esta pregunta."}` |
| Validación de FastAPI (solo 422) | `{"detail": [{"type","loc","msg","input"}]}` | `422`: `{"detail": [{"type":"missing","loc":["query","course_id"],"msg":"Field required"}]}` |
| Autenticación | `{"detail": "No autenticado o token inválido."}` | `401` (ejemplo `error_sin_token`) |
| Límite de tasa (slowapi) | `{"error": "Rate limit exceeded: 1 per 1 hour"}` | `429` (medido, ver §4) |
| Error no controlado | `{"detail": "[error-interno] Contacta al equipo con el X-Request-ID."}` | `500` |

**Regla práctica para el frontend:** leer `detail` (string o lista) y, si no existe, `error`.
Hoy el front no puede distinguir un error por código estable: debe usar el **código HTTP**
y, en algunos casos, el texto.

Todas las respuestas incluyen la cabecera **`X-Request-ID`** (se propaga si llega en la
petición). Sirve para reportar errores al equipo.

## 2. Códigos HTTP que devuelve la API

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 / 201 | Éxito (201 al crear curso o pregunta) | objeto o lista |
| 400 | Petición inválida en lógica de negocio | `detail` |
| 401 | Sin token, token inválido o caducado | `detail` |
| 403 | Rol insuficiente, o no es dueño / no tiene acceso al curso o subtema | `detail` |
| 404 | Recurso inexistente (curso, subtema, pregunta) | `detail` |
| 409 | Conflicto (enunciado duplicado, ya inscrito, etc.) | `detail` |
| 422 | Validación de campos (p. ej. pregunta que no tiene exactamente 4 opciones) | lista de FastAPI |
| 429 | Límite de tasa, tope diario de IA o saturación | `detail` o `error` (ver §4) |
| 500 | Error interno no controlado | `detail` con `[error-interno]` |
| 502 | Generación de preguntas con IA sin resultado válido | `detail` |
| 503 | Asistente no disponible / saturado (ver §5) | `detail` con prefijo |

Los `status` de los 29 ejemplos están en [`ejemplos/INDICE.json`](ejemplos/INDICE.json).

## 3. Códigos estables entre corchetes (existen hoy)

Solo hay **tres** códigos de error estables en la API. Todos llevan el código al inicio del `detail`:

| Código | HTTP | Significado | Estado real |
|---|---|---|---|
| `[error-interno]` | 500 | Fallo no controlado. El detalle está solo en el log. | Código presente en `app/main.py`; no se provocó en esta verificación. |
| `[asistente-no-disponible]` | 503 | El proveedor de IA falló al responder. | Medido: con fallo del proveedor `/api/ai/ask` responde 200 en modo respaldo (§5), así que este 503 no aparece. |
| `[asistente-saturado]` | 503 | Concurrencia del asistente al límite. Cabecera `Retry-After: 10`. | Medido con saturación del proveedor: `/api/ai/ask` responde 200 en modo respaldo; este 503 no aparece en el flujo probado. |

Los prefijos `[batch]`, `[import]`, `[export]`, `[index]` y `[validate]` que aparecen en el código
son **mensajes de consola de los scripts**, no códigos de la API. No deben usarse en el frontend.

## 4. Límites de tasa y topes

| Caso | HTTP | Cabecera `Retry-After` | Cuerpo real |
|---|---|---|---|
| Límite de tasa por endpoint (slowapi), p. ej. `AI_ASK_RATE_LIMIT` | 429 | **no se envía** (medido) | `{"error": "Rate limit exceeded: 1 per 1 hour"}` |
| Tope diario de consultas al asistente (`AI_DAILY_LIMIT_PER_USER`) | 429 | `3600` | `{"detail": "Alcanzaste el límite de consultas del día para el asistente."}` |
| Proveedor de IA saturado (límite global) | 429 en el router; **hoy `/ask` responde 200** (§5) | `60` en el router | — |

> **Inconsistencia medida:** el límite de tasa usa la clave `error` y no envía `Retry-After`.
> El frontend debe tratar `429` como "espera y reintenta" aunque no haya cabecera.

## 5. Asistente de IA: modo respaldo (no es un error)

`POST /api/ai/ask` **no devuelve 503** cuando el proveedor falla o está saturado. Responde
**200** con `degraded: true` y fragmentos del contenido oficial. Ejemplo real
(`chat_ia_degradado`):

```json
{
  "respuesta": "[MODO RESPALDO] El asistente con IA no está disponible ahora mismo.\n\nEstos son los fragmentos relacionados del contenido oficial:\n\n1. El glaucoma de ángulo cerrado aumenta la presión intraocular…",
  "degraded": true,
  "subtopic_id": 1,
  "chunks_usados": 1
}
```

Para el frontend: **mostrar el aviso de modo respaldo cuando `degraded === true`**, no tratarlo
como error. El `200` con `degraded: false` es la respuesta normal.

## 6. Cabeceras relevantes

| Cabecera | Dónde | Valor |
|---|---|---|
| `Retry-After` | 429 del tope diario | `3600` |
| `Retry-After` | 503 del router (asistente) | `60` o `10` (no alcanzable desde `/ask`) |
| `X-Request-ID` | Todas las respuestas | 16 caracteres hex |
| `WWW-Authenticate` | Algunas respuestas 401 (código del backend) | valor definido en el código; no verificado en los ejemplos |
| `Content-Disposition` | Exportes CSV (`/api/quiz/stats/export.csv`, `/api/ai/stats/export.csv`) | `attachment; filename=…` |

## 7. Campos de progreso (barra del panel)

La barra se calcula **solo con subtemas completados** (nunca con tiempo).

| Endpoint | Campo porcentaje | Campos de conteo | Notas |
|---|---|---|---|
| `GET /api/courses` (ítem de curso) | `progress_percentage` | `completed_subtopics`, `total_subtopics` | Lo usa la tarjeta de curso. |
| `GET /api/progress/course?course_id=…` | **`percentage`** | `completed_subtopics`, `total_subtopics` | Mismo cálculo, **nombre distinto** (§8). |
| `GET /api/courses/{id}/topics` (unidad) | — (no hay porcentaje) | `completed_subtopics`, `total_subtopics` | El front calcula la unidad con estos dos. |
| `GET /api/courses/{id}/topics` (subtema) | — | `completed` (bool) | Un subtema completado = `true`. |

Fórmula del backend: `percentage = round(completed / total * 100, 1)` (0 si `total = 0`).

## 8. Inconsistencias encontradas y unificación mínima propuesta

| # | Inconsistencia | Impacto en el front | Propuesta mínima (no implementada) |
|---|---|---|---|
| 1 | El 429 de límite de tasa usa `error`; el resto usa `detail`. | Hay que leer dos claves. | Devolver `detail` también en el handler de slowapi (cambio no rompedor si se mantiene `error`). |
| 2 | El 429 de límite de tasa no envía `Retry-After`. | Reintento sin tiempo. | Añadir `Retry-After` con la ventana del límite. |
| 3 | `detail` puede ser string o lista (422). | Hay que comprobar el tipo. | Mantener; el front ya debe tratar la lista. |
| 4 | Solo 3 códigos entre corchetes; 2 de ellos no aparecen en el flujo del chat probado. | Códigos documentados sin efecto real. | Eliminar los no alcanzables o documentarlos como "reservados". |
| 5 | Porcentaje: `progress_percentage` en cursos y `percentage` en progreso. | Mapeo distinto por endpoint. | Alias en el esquema de progreso (`percentage` y `progress_percentage`) durante una versión. |
| 6 | El chat degrada con `200` mientras los códigos 503/429 existen en el router. | Lógica de error duplicada. | Decidir: degradar siempre (lo que hace hoy) y borrar las ramas 503/429 del router. |
| 7 | La API expone `estimated_minutes` en cursos, unidades y subtemas (medido en `unidades_del_curso` y `lista_cursos_estudiante`). | La UI no debe mostrarlos (regla de producto: cero tiempos). | Retirarlos de los esquemas de lectura en una versión posterior. Hoy solo se ocultan en la UI. |

Propuesta de **código de error estable** (no existe hoy, para una versión futura y compatible):
añadir `"code"` al cuerpo, p. ej. `{"detail": "…", "code": "pregunta_sin_4_opciones"}`. Los clientes actuales
no se rompen porque `detail` se mantiene.

## 9. Recomendación al frontend

1. Decidir por **código HTTP** (401, 403, 404, 409, 422, 429, 5xx) y mostrar `detail` como texto.
2. Tratar `401` en un único lugar (`apiFetch`, ya implementado): limpiar sesión y volver al login.
3. Tratar `429` como "espera": leer `Retry-After` si existe; si no, mostrar un mensaje genérico.
4. Leer `degraded` en la respuesta del chat; no mostrarla como error.
5. Para el progreso, usar `progress_percentage` (cursos) o `percentage` (endpoint de progreso) según el endpoint.
6. No mostrar tiempos aunque la respuesta los traiga.
