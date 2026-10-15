# Timeouts de base de datos (cierre de §13)

**Fecha**: 2026-10-14 · **Rama**: `fix/timeouts-bd` · **PR**: pequeño, apilado sobre #53

## Problema

Con la base suspendida (Neon calcula el cómputo en frío) o saturada, las peticiones
quedaban colgadas hasta que el cliente se rindiera: no había límite de espera en
la app. Hallazgo del ensayo local 2.8 (PR #54).

## Decisión por defecto (configurable por variables)

| Parámetro | Variable | Defecto | Efecto |
|---|---|---|---|
| connect_timeout | `DB_CONNECT_TIMEOUT` | `10` s | existe ya: TCP falla rápido |
| pool_timeout | `DB_POOL_TIMEOUT` | `10` s | esperar como máximo 10 s por una conexión del pool |
| statement_timeout | `DB_STATEMENT_TIMEOUT_S` | `15` s | corte por transacción para consultas normales |

- `DB_STATEMENT_TIMEOUT_S=0` desactiva el statement_timeout.
- Las **migraciones/DDL** usan el engine directo sin este límite (una migración
  legítima puede superar 15 s; un DDL cortado a mitad es lo peor que puede pasar).

## Cómo se fija el statement_timeout con el pooler de Neon

Neon usan pgbouncer en `pool_mode=transaction` (documentación "Connection
pooling", neon.com/docs/connect/connection-pooling): en conexiones pooladas NO
se admite estado de sesión (`SET`, `LISTEN/NOTIFY`) y el parámetro de arranque
`options` NO está soportado (`unsupported startup parameter: options`,
neondatabase/neon#6291, reproducción en pgbouncer#875). La alternativa viable
y la que aplica el código es **`SET LOCAL statement_timeout` al iniciar cada
transacción** (`SET LOCAL` expira con la transacción, es válido en modo
transacción; recomendación en pgbouncer#1334). La alternativa por rol
(`ALTER ROLE ... SET statement_timeout=…`) queda documentada como opción
coexistente para el pgbouncer propio del ensayo, no se aplica por defecto.

Implementación: listener `after_begin` de `SessionLocal`
(`backend/app/database/session.py`) ejecuta `SET LOCAL statement_timeout = <ms>`
en cada transacción de la app.

## Comportamiento cuando la BD no responde (nunca cuelgue)

- Pool agotado o conexión imposible (TCP, DNS, suspensión) →
  **503** con `{"error": "db_unavailable", "detail": "…"}` y
  cabecera **`Retry-After: 5`** (código estable nuevo, ver
  `docs/api/ERRORES_PARA_FRONTEND.md` §códigos).
- `OperationalError` y `TimeoutError` de SQLAlchemy tienen sendos manejadores
  en `backend/app/main.py`; el handler genérico de 500 se mantiene para el resto.

## Verificación

- Unit tests: `backend/tests/test_db_timeouts.py` (4 pruebas, sin red) —
  503 + Retry-After ante pool agotado y BD caída, defectos de settings y
  queue pool real que lanza `TimeoutError` en vez de colgarse.
- Postgres real (contenedor `insoft-db`): `BEGIN; SET LOCAL statement_timeout=500;
  SELECT pg_sleep(2);` → `ERROR: canceling statement due to statement timeout`;
  con 15000 ms → `SELECT 42` OK y `ROLLBACK` limpio.
