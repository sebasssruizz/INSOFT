# PLAN_PILOTO — Oftalmología (Claudia Romero) · 16–31 oct

Equipo: Sebastián (ops/IA/despliegue) · Eddy (3D/e2e/soporte) · Samuel
(videos/responsive/informe/documentación).

## Objetivos

1. Validar con estudiantes reales el flujo: enunciado → contenido → repaso →
   práctica → asistente IA.
2. Medir uso y percepción con datos, no con opiniones sueltas.
3. Detectar bloqueantes y bajarlos a producción antes del 24-oct.
4. Dejar evidencia de la iteración para el documento de aula (Samuel).

## Participantes

- Alumnos inscritos del grupo de la docente: objetivo **30** (mín 20).
- Carga de cuentas: ver `docs/piloto/GUIA_CARGA_CUENTAS.md` (CSV + importador
  idempotente; sin correos automáticos).
- Docente: acceso al panel docente (banco, quotas IA, stats).

## Qué se mide y de dónde salen los números

| Métrica | Fuente (endpoints/tablas) | Reporte |
|---|---|---|
| Estudiantes activos por día | `users`/`course_memberships` + actividad diaria | export de `quiz/stats` |
| Subtemas completados | `progress`, endpoint `/api/progress/course` | CSV quiz export |
| Intentos de repaso y aciertos | `quiz/stats/*` + `question_answers` | export CSV docente |
| Consultas al asistente | `ai_queries` (+ status ok/degraded/error, `GET /api/ai/stats/*`) | stats overview |
| Tiempo de respuesta IA | `ai_queries.response_time_ms` | stats subtopics |
| Generaciones IA del docente | `questions` source=ai por estado | banco | 
| Satisfacción | encuesta SUS (ver abajo; `scripts/score_sus.py`) | CSV encuesta |

**Extra**: export CSV ya existente (`/api/quiz/stats/export.csv`) como reporte
docente; los atajos de dashboards muestran tendencia por subtema.

## Duties día a día

| Qué | Responsable | Ritmo |
|---|---|---|
| Salud diaria (`/health`, `/ready`, logs, backups) | Sebastián | diario AM |
| Soporte horas pico (club 17:00-21:00) | Eddy | en ventana |
| Observación / hallazgos de usabilidad | Samuel | 3 checkpoints/día |
| Correcciones hot (<24h) con rama `fix/*` + PR | Sebastian+Eddy | por impacto |
| Encuesta al final (1er y 3er día) | Samuel + docente | 16 y 24 oct |

## Ventana

- 16-oct: check-in de acceso (los estudiantes ya cargados), primer uso.
- 17–24-oct: uso normal; reporte de hallazgos continuo.
- 25–31-oct: medidas de cierre, encuesta SUS, informe de hallazgos.

## Riesgos y plan B

| Riesgo | Señal | Plan B |
|---|---|---|
| IA caída/cuota | opciones `degraded` crecientes en `ai_queries.status` | El modo degradado entrega fragmentos oficiales; se avisa a estudiantes |
| Volumen de consultas | 429 frecuentes a media mañana | subir `AI_DAILY_LIMIT_PER_USER` o rotar proveedor (gemini) |
| Contenido disputado | reportes de la docente | corrección con rama `fix/contenido-*` y PR |
| Caída de host | `/ready` 503 | reinicio compose; si nada: URL alternativa (túnel) 30 min |
| Escalada de bugs | seguimiento del canal reportado | triaje diario a las 9PM, cortes de parches |

## Reglas de operación

- Sin experimentos de código EN PRODUCCIÓN durante el piloto (todo va por PR).
- Los cambios de contenido solo lo aprueba la docente.
- Backup diario antes de 1AM y captura de la restauración semanal (evidencia).
