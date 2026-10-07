# ENLACES_FINALES — checklist de enlaces para la entrega

> Todo lo marcado **POR COMPLETAR** lo completa Sebastián (o quien administre)
> justo antes del 30-oct: no es información técnica nueva, son URLs.

## Índice de enlaces

| Ítem | URL | Estado |
|---|---|---|
| Repositorio GitHub | **POR COMPLETAR** (repo actual: `https://github.com/sebasssruizz/INSOFT`) — confirmar URL definitiva / público-privado para la entrega | [x] base, pendiente confirmar visibilidad |
| Frontend (producción) | **POR COMPLETAR** — Vercel o la URL de la VM según despliegue final | [ ] |
| Backend (API prod) | **POR COMPLETAR** — `https://…/docs` (Swagger) | [ ] |
| Frontend staging/dev | **POR COMPLETAR** | [ ] |
| Base de datos (panel) | **POR COMPLETAR** — panel Neon o VM (no compartir credenciales) | [ ] |
| Tablero (Planner/Proyectos) | **POR COMPLETAR** — URL del tablero del equipo | [ ] |
| Documento de aula (PDF) | **POR COMPLETAR** — Prueba Samuel entrega | [ ] |
| Video demo / partida | **POR COMPLETAR** (Samuel) | [ ] |
| Guías internas | `GUIA_DE_PRUEBAS.md`, `GUIA_GOOGLE_OAUTH.md`, `DEPLOY.md`, `docs/despliegue/*`, `docs/piloto/*`, `docs/plan/ESTADO_VS_PLAN.md` | [x] están en el repo |
| Reporte final de la noche | `docs/reporte-noche-2026-10-07.md` | [x] |

## Tablero del proyecto (GitHub Projects V2)

El token que usamos esta noche tiene `repo, workflow, read:org` pero **NO
`read:project`**: no puedo listar el tablero ni proponer movimientos concretos
por nombre. Propuesta (cuando se habilite):

1. Habilitar `read:project` (o abrir el tablero a mano) y ejecutar:
   `gh api graphql -f query='{viewer{projectsV2(first:10){nodes{id title items(first:50){nodes{id content{id} fieldValues(first:20){nodes{... on ProjectV2ItemFieldSingleSelectValue{name text}}}}}}}}}'`.
2. Escribir `docs/tablero-propuesta.md` con: tarjetas "HECHO" (PRs mergeados de esta noche: #9–#28), "en curso" y "bloqueado"
   con sus referencias.

## Cómo verificar cada entregable (para el día de la entrega)

1. `bash scripts/smoke_prod.sh https://<dominio>` → todas `[OK]`.
2. En la plataforma: estudiante de prueba responde repaso, pregunta al
   asistente, termina unidad con progreso 100 %.
3. Docente: "Agregar preguntas" (4 opciones), genera IA (pendiente), la aprueba
   y aparece en el repaso.
4. Backup: `deploy/backup.sh` corre + `restore.sh` probado una vez (evidencia).
5. 30+ estudiantes del piloto registrados por CSV y encuesta SUS ≥ 68.
