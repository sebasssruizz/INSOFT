# ESTADO_VS_PLAN — proyección del plan comprimido al estado real del repo

Generado: 7-oct-2026 (noche). Fuente del plan: `docs/PLAN_REV_2_SEMANAS.txt` (plan
comprimido, feature freeze 6-oct · MVP prod 15-oct · piloto 16–31-oct · entrega
30-oct, límite 4-nov). Documento de proyecto: `docs/PROYECTO_2_INSOFT_rev_4956.pdf`
(se deba la traducción al PDF final: Samuel).

## A. Auditoría de ramas y PRs

| Rama | Estado | Detalle |
|---|---|---|
| `feat/preguntas-ia-banco-profesor` | ✔ integrada en staging | 0 commits únicos vs staging |
| `feat/estadisticas-intentos-quiz` | ✔ integrada en staging | 0 commits únicos |
| `feat/practica-y-agregar-pregunta` | ✔ integrada | solo queda copia local; rama remota ya no existe |
| `feat/contenido-unidades-restantes` | ✔ integrada en staging | 0 commits únicos (y también llegó a main por hotfixes de contenido) |
| `feat/deploy-prod` (worktree `../INSOFT-deploy`) | ⚠ **NO integrada** | 8 commits no en staging: `feat(despliegue): backups, restauración probada y operación`, `docs(despliegue): runbook de DigitalOcean`, `docs(despliegue): reporte`, `test(despliegue): verificación local y smoke test`, etc. (Caddy+Nginx, compose prod). **Plan de integración en T6 (docs/despliegue), no se mergea ahora.** |
| PRs abiertos | ninguno | #9–#17 ya mergeados/cerrados a staging |
| `stash@{0}` | ⚠ pendiente de decisión | "WIP on main" (75fe27e, 15-sep): trabajo de estadísticas IA en `ai_query_repository`, `routes/ai.py`, `TeacherDashboard` (+744 líneas). La feature ya integrada por `feat/estadisticas-intentos-quiz` probablemente lo hace obsoleto — **no aplicar sin comparar por pedazos**; riesgo medio.

## B. Estado por ítem del plan

| Ítem del plan | Responsable | Estado | Evidencia | Riesgo |
|---|---|---|---|---|
| Vistas 3D mínimas (GLB, sala, paneles) | Eddy | Hecho | `frontend/src/components/three/`, `pages/InteractiveViewPage.jsx`, modelos `frontend/public/models/*.glb` | Bajo: falta e2e propio (plan de hoy: T8 carga/rendimiento) |
| Videos por subtema + transcripción | Samuel | Parcial | video pterigión transcrita en repo (`docs/importacion/*.mp4`, `Transcripcion_…txt`); no hay player por subtema en el módulo | Medio: decisión de alcance antes del piloto |
| Generador de preguntas desde interacción | Sebastián | Hecho (base) | `routes/ai.py`, `services/ai_service.py`, tests `test_question_generator.py`; robustez pendiente hoy (T4) | Bajo |
| Robustez asistente RAG (límites, fallback) | Sebastián | Parcial | límites/rate limit existen en `core/config.py` y `routes/ai.py`; hoy se completa hoy (T3) (timeouts, degradado, breaker, inyección) | Medio: costo si falla días libres |
| Responsive crítico | Samuel | Parcial | clases Tailwind responsive en páginas curso; sin verificación sistemática de móvil/tablet | Medio |
| Contenido validado (9 unidades) | Claudia + equipo | Hecho | BD `topics/subtopics/questions` (85 approved); `docs/importacion/units_v2/*.md`; unidad 9 con preguntas verbatim | Bajo: pendiente finalize (T9) |
| Asistente RAG (pgvector + MiniLM) | Sebastián | Hecho | `services/embeddings_service.py`, `repositories/subtopic_chunk_repository.py`, `routes/rag.py` | Alto por memoria en plan gratis (T1) |
| Pruebas backend/roles | Sebastián | Parcial | 150 tests; matriz de roles es la tarea T2 de hoy | Bajo |
| Despliegue dockerizado VM + HTTPS | Sebastián | Parcial | `feat/deploy-prod` no integrado (compose prod, backups, runbook DO); gratis documentado en `DEPLOY.md`/`render.yaml` | Alto: consolidación hoy (T6) |
| Backups y recuperación | Sebastián | Parcial | trabajo en `feat/deploy-prod` (backups + restauración probada) sin integrar | Alto |
| Pruebas y encuestas con estudiantes | equipo | Pendiente | borradores en T10 de esta noche | Bajo |
| Tablero/planificación | Todos | Parcial | planner externo; no hay snapshot en repo (T11) | Bajo |

## C. Cronograma día a día

Semana 2 (8–15 oct) — tareas de Sebastián:

- **Mié 8**: T3 robustez IA (merge del PR de robustez), T4 generador robusto; correos de PRs revisados.
- **Jue 9**: T6 consolidación despliegue: integrar decisión feat/deploy-prod vs ruta gratis; smoke_prod.sh verde.
- **Vie 10**: dominio + HTTPS (Caddy o túnel según decisión), `SECRET_KEY`, CORS, backups con días de retención.
- **Sáb 11**: T7 carga accountable del piloto (plantilla CSV + guía por cuenta); T8 informe de carga y tamaño de VM.
- **Dom 12**: T9 cierre de contenido unidad 9 + banco pterigión (solo múltiple A-D); pendientes listados.
- **Lun 13**: T5 observabilidad final (logs rotación, /ready); smoke de producción con datos reales.
- **Mar 14**: estabilización: pogrújar p95 de carga, correcciones menores, probas por rol (T2 en staging).
- **Mié 15**: **MVP en producción** — smoke_prod verde + tag/release v1.0 + tablero del repo.

Semana 3–4 (16–31 oct) — Sebastián:

- 16–22: soporte del piloto, blobs de observación por Samuel, correcciones calientes vía ramas `fix/*`.
- 23–29: Indiana de ajustes priorizados (equipo), documentación de arquitectura; Samuel produce el PDF.
- 30 oct: **entrega** (límite 4-nov); primera semana de nov: sorpresa sustentación.

*Nota: la rama `stash@{0}` se revisa con Sebastián comparendiendo delante de los
PRs ya integrados antes de elegir drop.
