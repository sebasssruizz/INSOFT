# Sofía: memoria conversacional, contexto y retroalimentación

## Funcionamiento

El chat envía `course_id`, `topic_id` (cuando se está en una unidad),
`subtopic_id`, `session_id` y, opcionalmente, `selected_text` a
`POST /api/ai/ask`. El servidor valida el acceso y resuelve los nombres de
curso, unidad y subtema desde la base de datos. Los títulos no se aceptan
como fuentes suministradas por el navegador.

Cada respuesta utiliza:

1. La ubicación académica actual, para preguntas como «explícame esto».
2. Hasta seis intercambios previos exitosos del mismo usuario, sesión y curso.
   Cada pregunta se limita a 500 caracteres y cada respuesta previa a 1800.
   Se vuelve a comprobar el acceso al material mencionado. El historial
   interpreta referencias; no sustituye las fuentes académicas. Una respuesta
   valorada negativamente no se reutiliza como explicación en la memoria.
3. Una consulta de recuperación enriquecida con los títulos, la selección y,
   para continuaciones como «¿y sus cuidados?», las últimas preguntas.
4. Hasta tres fragmentos para preguntas puntuales o seis distribuidos por el
   material para resúmenes. El contenido de cada fragmento enviado al modelo
   se limita a 500 palabras. La recuperación sin curso explícito también se
   restringe al contenido autorizado del usuario.

Si el ámbito consultado aún no tiene fragmentos indexados, se utiliza el texto
académico autorizado del subtema, unidad o cursos, dividido localmente en
fragmentos y ordenado por coincidencia de términos. Esta alternativa no crea
embeddings ni modifica el índice. Las preguntas sobre el alcance del curso
reciben además su descripción y temario desde la base de datos, sin depender
del índice vectorial. Desde el inicio se incluyen solo temarios de cursos
accesibles; el modelo identifica el curso único o solicita aclaración si hay varios.
El proveedor recibe fuentes numeradas,
separadas del historial y de la ubicación. Se le pide aclarar referencias
ambiguas, reconocer información insuficiente y adaptar la extensión de la
respuesta al tipo de consulta.

Gemini conserva una sola llamada de generación. OpenRouter mantiene la
normalización y la generación, además de sus mecanismos de respaldo.

## Uso del chat

- El encabezado muestra **Contexto actual**.
- El hilo se conserva al navegar entre subtemas del mismo curso.
- Una continuación explícita puede recuperar el subtema anterior; «esto»,
  «aquí» o «lo que estoy viendo» se interpretan según la página actual.
- **Nueva conversación** cambia el identificador y reinicia el hilo visible.
  Los registros anteriores permanecen en el historial.
- El identificador activo se conserva en `sessionStorage`, separado por usuario
  y curso. Al recargar la pestaña se recuperan hasta 50 intercambios guardados.
  El modelo utiliza solo los seis últimos intercambios exitosos.
- Las respuestas pendientes de un contexto anterior no se insertan en otro hilo.
- En una lección, seleccionar texto permite pulsar **Preguntar a Sofía sobre
  el fragmento seleccionado**. El backend comprueba que pertenezca al contenido
  actual, normalizando encabezados, listas y negritas.
- **Fuentes consultadas** muestra títulos, extractos y enlaces al subtema.

## Retroalimentación

`PUT /api/ai/answers/{query_id}/feedback` admite:

```json
{
  "helpful": false,
  "reason": "context",
  "comment": "La respuesta se refiere a otra cirugía."
}
```

Los motivos son `context`, `incomplete`, `incorrect` y `other`. El comentario
es opcional y tiene un máximo de 1000 caracteres. Solo el autor de la consulta
puede valorar o actualizar su respuesta; no se crean votos duplicados.

En **Estadísticas → Uso de IA**, el docente puede leer las valoraciones y
filtrar por respuestas que no sirvieron o por motivo. El historial nuevo queda
acotado a los cursos propios y a sus estudiantes. Las consultas antiguas sin
curso conservan el filtrado histórico por estudiantes.

El endpoint de historial propio admite `session_id`, `course_id` y
`global_only=true`; el historial docente admite `feedback_only=true` y
`feedback_reason`. La respuesta del chat añade `query_id`, `session_id` y
`sources` sin retirar los campos anteriores.

## Actualización de la base de datos

La migración **7: memoria_y_feedback_ia** añade a `ai_queries` las columnas
`course_id`, `topic_id`, `sources`, `feedback_helpful`, `feedback_reason` y
`feedback_comment`, junto con un índice de conversación. Es aditiva e
idempotente y se ejecuta mediante el mecanismo habitual al arrancar el backend.
No necesita nuevas claves ni variables de entorno.

La migración **8: session_id_uuid** convierte el `session_id` de texto de bases
PostgreSQL antiguas al tipo UUID del modelo. Conserva las consultas y sus sesiones;
si encuentra identificadores inválidos, cancela la migración sin eliminarlos.
También normaliza sesiones antiguas de SQLite al formato utilizado por SQLAlchemy.

Desplegar el backend actualizado y ejecutar sus migraciones antes de publicar
el frontend que consume los campos nuevos. En Docker, reconstruir y reiniciar
ambos servicios con el procedimiento del proyecto.

## Comprobación manual

1. Abrir un subtema y preguntar «Resúmeme lo que estoy viendo».
2. Preguntar por un instrumento y después «¿y qué cuidados debo tener?».
3. Cambiar de subtema y preguntar «Explícame esto»; comprobar las fuentes.
4. Seleccionar un párrafo y abrir la consulta sobre ese fragmento.
5. Recargar la pestaña y comprobar que vuelve el hilo.
6. Iniciar una conversación nueva y comprobar que empieza sin mensajes previos.
7. Valorar una respuesta, recargar y cambiar la valoración.
8. Revisar el reporte desde el panel docente y aplicar los filtros.

## Alcance y limitaciones

- La memoria está acotada: no recuerda ilimitadamente todas las conversaciones.
- Las referencias se interpretan combinando contexto y heurísticas; pueden
  requerir aclaraciones. No hay un planificador autónomo ni reentrenamiento.
- La retroalimentación permite revisión y mejora supervisada; un voto no
  modifica automáticamente el contenido oficial ni los pesos del modelo.
- El chat recibe texto y ubicación, no imágenes, fotogramas del video ni el
  instrumento seleccionado en el visor 3D.
- Las citas identifican material recuperado; no son una verificación automática
  de cada afirmación del modelo. La calidad depende de las fuentes y del proveedor.
- La recuperación semántica se mantiene por similitud coseno; no se añade un
  umbral arbitrario sin una evaluación de relevancia con preguntas reales.

## Pruebas

`backend/tests/test_ai_conversation.py` cubre memoria con ambos proveedores,
aislamiento, navegación, selección validada, unidad, material sin indexar,
permisos revocados, valoraciones y modo respaldo, con proveedor y embeddings
simulados. Las pruebas de migración comprueban actualización sin pérdida de datos.

`frontend/src/components/AiChatWidget.test.jsx` verifica sesiones, restauración,
fuentes, valoraciones, selección y respuestas pendientes al cambiar de curso.
`frontend/src/pages/TeacherAiStats.test.jsx` comprueba la revisión docente.

Estas pruebas verifican el flujo de la aplicación. La precisión semántica y la
calidad pedagógica deben evaluarse además con el proveedor y contenido reales.
