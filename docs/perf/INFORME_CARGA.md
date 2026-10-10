# INFORME_CARGA — prueba ligera T8 (30 y 60 usuarios)

7-oct-2026. Stack DESECHABLE: backend (imagen ONNX, staging HEAD) +
Postgres 16 con pgvector, `AI_MOCK=true` (bloqueado con ENVIRONMENT=production),
`DEV_AUTH_ENABLED=true`. Destruido tras las corridas (docker compose down).

Comando: `python scripts/loadtest.py --base http://localhost:8010 --users N --wave W`
(fases por usuario: login dev → temario → subtema → repaso → quiz answer → progreso;
100 % también consideran llamadas IA mock).

## Resultado (host: 8 GB laptop, Docker)

| Fase | n (30u) | p50 / p95 (30u) | n (60u) | p50 / p95 (60u) |
|---|---|---|---|---|
| login dev | 30 | 74 / 214 ms | 60 | ~150 / ~350 ms |
| topics | 60 | 394 / 513 ms | 120 | 551 / 817 ms |
| subtema | 30 | 184 / 286 ms | 60 | 307 / 494 ms |
| repaso | 30 | 213 / 295 ms | 60 | 346 / 453 ms |
| IA (mock) | 3 | 88 / 93 ms | 8 | 125 / 202 ms |
| quiz answer | 30 | 204 / 267 ms | 60 | 319 / 455 ms |
| progreso | 30 | 96 / 188 ms | 60 | 190 / 332 ms |
| **TOTAL** | 183 | **213 / 467 ms** | 361 | **342 / 750 ms** |

Duración total: 4,8 s (30u) · 11,1 s (60u) con oleadas de 10/15. **Errores: 0**.

RAM/CPU del contenedor backend durante la corrida: **124 MB / ~0.2 % CPU**
(imagen ONNX, sin modelo cargado pues AI_MOCK evita embeddings… al emparchar la
IA la primera carga subió a ~0.67 GB ver INFORME_MEMORIA).

## conclusiones

1. Con 60 usuarios concurrentS el backend ONNX responde p95 < 1 s con
   PostgreSQL local — holgura para el piloto de 30–60 estudiantes de la docente.
2. El punto caliente es el índice `topics` (2 consultas por usuario: cursos +
   gráfico de contenidos): seguir caché de respuesta para el instructor si el
   piloto crece.
3. Tamaño de VM recomendado: **1–2 GB RAM / 1 vCPU** para 60 estudiantes
   concurrentes incluso con embeddings ONNX locales (0.67 GB peak) — margen ok.
   Para el free tier de Render (512 MB) NO cabe carga de 60 con embeddings.

## Limitaciones

- Runs con la IA mock: no mide latencia real de OpenRouter (varía mucho).
- Solo backend; sin el frontend nginx en el loop (utilizó los endpoints del
  mismo modo que los hace la UI).
