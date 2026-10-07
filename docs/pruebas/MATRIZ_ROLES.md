# MATRIZ_ROLES — hallazgos de la matriz de autorización (T2)

Fecha 7-oct-2026. Ejecutable: `backend/tests/test_role_matrix.py` (24 asserts).
Sujetos: `anon` (401), `student_in` (inscrito), `student_out` ("no inscrito" en
el curso X, pero auto-inscrito al Curso General), `owner` (docente dueño) y
`other` (docente de otro curso), más un docente desechable para el PATCH de rol.

## Conclusión en una línea
La autorización está **sólida**: los casos ordenados de la matriz concuerdan con el
diseño; se corrigieron **2 huecos reales** (uno de alcance de datos y uno de
dupe lógico) y se detectó **ningún aprendizaje de rol** (escaladas: 0).

## Huecos corregidos (commit aparte `fix`)

1. **/api/rag/search global exponía contenido sin verificar pertenencia a
   cursos** (`routes/rag.py`). Antes: sin `course_id`/`subtopic_id` se buscaba
   sobre TODO el índice para cualquier usuario autenticado.
   **Ahora**: la búsqueda global se acota a chunks de topics habilitados en los
   cursos del usuario (estudiante: sus membresías; docente: sus cursos).
   *Impacto práctico bajo*: todo estudiante queda inscrito al Curso General
   (que habilita todo el temario), así que en la práctica no se exponía
   contenido nuevo — pero el fix evita fugas si en el futuro se deshabilitan
   unidades o se quita el auto-enrol en General. Test nuevo:
   `test_rag_global_scope.py`.
2. **Chunks duplicados en la búsqueda** (`subtopic_chunk_repository`): al unir
   por cursos, un chunk habilitado en N cursos del usuario repetía N veces el
   mismo resultado. Ahora `distinct()`; un documento aparece una sola vez.

## Hallazgos por revisión (sin cambio de código)

- **Quiz/práctica son "por subtema"**, no por curso: cualquier estudiante
  (aunque no esté inscrito en "Curso X") puede responder/practicar el contenido
  oficial del subtema a través de su membresía del Curso General. Refleja el
  diseño de contenido compartido; no es fuga — el banco ese subtema comparte
  también aporta las preguntas del curso "X".
- **PATCH /api/users/me/role permite autodescuentar/dar rol** (200 si es el
  propio usuario). Riesgo conocidamente ACEPTADO para esta fase: en
  producción/despliegue final conviene deshabilitarlo (issue de cambio: solo
  con DEV_AUTH o remove del endpoint en producción). Recomendación: protegerlo
  con env ADMIN_ROLE_CHANGES.
- `/health` público por diseño (T5 agrega `/ready` para apoyo inverso sin
  secretos).

## Endpoints sin protección explícita (checklist del máximo riesgo)

| Endpoint | Situación |
|---|---|
| `GET /health` | público esperado (ok) |
| routers (courses/content/quiz/ai/rag/practice/progress/users) | 401 sin token ✓ |

Ningún endpoint quedó sin autenticación o con dependencias de rol ausentes.
