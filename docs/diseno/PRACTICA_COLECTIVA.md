# PRACTICA_COLECTIVA — diseño (T12, NO implementado)

¿Cubre el modo práctica "preguntar sobre lo que consultaron otros estudiantes de
la misma unidad"? **No**: hoy el pool IA se pondera por (a) popularidad
AGREGADA de subtemas por consultas global, (b) 3× las consultas PROPIAS del
usuario y (c) su % de acierto propio (ver README §modo práctica y
`practice_service.py`). No existe composición por "lo que preguntó otra gente
de la unidad para este subtema/campo".

## Propuesta (pending implementación, detrás de flag apagado)

Flag: `PRACTICE_COLLECTIVE_ENABLED=false` (server-side; cuando true activa la
función descrita abajo como FUENTE EXTRA, no como sustituto del banco).

### Datos

- `ai_queries` ya registra user_id, subtopic_id, question_normalizada y session.
- **Agregado por unidad/subtema**: clusters simples de preguntas normalizadas
  (similaridad de embeddings ya disponible) y frecuencias por tema.
- Nada de identificadores: el dataset para seleccionar preguntas solo expone
  (subtopic_id, número de consultas distintas, etiqueta por tema).
- Descarte: filas con **datos personales** (heurística: contiene @, teléfono,
  nombres propios del patrón "mi caso"). El red scan del dataset es una etiqueta
  `collective_text=none` (solo se usa la META, nunca el texto de la consulta).
- Mínimo para activarse: `PRACTICE_COLLECTIVE_MIN_QUERIES=5` consultas
  distintas en la unidad; de lo contrario se usa pr ly el pool actual.

### Selección

1. Para el subtema elegido, se buscan administered clustres por unidad con
   đủ hits (>= mínimo).
2. Se reutiliza el generador para crear preguntas `practice` (status=practice,
   created_by=NULL) con el CONTEXTO oficial + el rango de temas colectivos
   (solo temas, nunca texto de estudiantes). Todo entra por la misma cola de
   revisión docente; nada automático aprobado.
3. En la sesión práctica el pool prioriza esas preguntas SOLO si hay staff.

### Segmentación y privacidad

- Guardas: sin IDs, sin textos de terceros, mínimo de k=3 estudiantes
  distintas para cada cluster (silencio interactivo).
- Log del pipeline agrega: unit/cluster/tag, sin user_id por fila nueva.
- Aviso de datos ya cubre el uso agregado y anónimo (AVISO_DATOS §2).

## Por qué NO se implementó esta noche

- Feature freeze 6-oct superado; no es bloqueante del piloto.
- Requiere migración (nueva tabla `practice_collective_clusters`) + flujo de
  revisión docente + pruebas: ~1 día de trabajo con QA.
- Se deja como backlog del 23-29 oct con el flag apagado por defecto.
