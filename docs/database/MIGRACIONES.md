# Migraciones de base de datos

Código: `backend/app/database/migrations.py`. Pruebas: `backend/tests/test_migraciones.py`
(SQLite) y `backend/tests/test_migraciones_pg.py` (PostgreSQL desechable).

## Cómo funciona al arrancar

En `app/main.py`, el arranque ejecuta en este orden, con reintentos mientras la base no responde:

1. `ensure_pgvector_extension()`: `CREATE EXTENSION IF NOT EXISTS vector` (solo PostgreSQL). Debe ir antes de `create_all` porque las columnas `vector` lo necesitan.
2. `Base.metadata.create_all()`: crea las tablas que no existan. **No** altera tablas existentes.
3. `run_migrations()`: aplica las migraciones pendientes.

`run_migrations()`:

- crea la tabla `schema_migrations (version, name, applied_at)` si no existe;
- en PostgreSQL toma `pg_advisory_lock(7142001)`, así dos procesos que arrancan a la vez no migran en paralelo;
- ejecuta en orden las migraciones que no aparecen en `schema_migrations`;
- registra cada una **solo si terminó sin error**. Si falla, el arranque falla y el siguiente intento la reintenta.

## Adopción de bases existentes

Una base creada antes de este sistema no tiene `schema_migrations`. Al primer arranque:

- la migración 1 (`linea_base`) se ejecuta. Es idempotente: sobre un esquema al día no cambia nada, y sobre uno viejo añade lo que falte;
- queda registrada como `linea_base`;
- no se borra ni se modifica ningún dato.

## Migraciones actuales

| Versión | Nombre | Qué hace |
|---|---|---|
| 1 | `linea_base` | Todo el esquema previo: extensión pgvector, `question_answers`, columnas `users.country/age`, `questions.source/status/created_by/created_at`, columnas de `ai_queries`, índices de quiz y banco. |
| 2 | `indice_ai_queries_usuario_fecha` | Índice `(user_id, created_at)` en `ai_queries` para el tope diario del asistente. |
| 3 | `pregunta_normalizada_ai` | Añade `question_normalizada TEXT` anulable a bases antiguas; conserva consultas y respuestas existentes. |
| 4 | `crear_feedback` | Tabla aditiva de PQRS vinculadas a la cuenta. |
| 5 | `crear_evaluaciones_usabilidad` | Tabla aditiva de evaluaciones versionadas, respuestas JSON y UUID único de entrega. |

## Cómo añadir una migración

1. Añade una entrada **al final** de `MIGRATIONS` con el siguiente número:

   ```python
   def _mi_cambio(conn: Connection) -> None:
       # idempotente: comprueba antes de crear/añadir
       if "mi_tabla" in set(inspect(conn).get_table_names()):
           return
       conn.execute(text("CREATE TABLE mi_tabla (...)"))

   MIGRATIONS.append(Migration(3, "mi_cambio", _mi_cambio))
   ```

2. Reglas:
   - **Nunca** renumerar ni editar una migración ya publicada: crea una nueva.
   - Solo cambios **aditivos** (columnas nuevas, tablas nuevas, índices). Nada de `DROP` ni de borrar datos.
   - En SQLite no se puede añadir `NOT NULL` con `DEFAULT` no constante: añade la columna anulable y rellénala (ver `_linea_base`).
   - Cada migración debe funcionar sobre una base **vacía** y sobre una base con datos.
3. Añade una prueba en `test_migraciones.py` que cubra el paso nuevo, y repite la verificación en PostgreSQL.

## Verificación

```bash
cd backend
PYTHONPATH=. .venv/bin/python -m pytest tests/test_migraciones.py -q            # SQLite
MIGRACIONES_PG_URL='postgresql+psycopg2://usuario:clave@127.0.0.1:5433/tmp_migraciones_desech' \
  PYTHONPATH=. .venv/bin/python -m pytest tests/test_migraciones_pg.py -q       # PostgreSQL desechable
```

La prueba de PostgreSQL **borra el esquema público** de la base indicada. Por eso exige que el
nombre de la base contenga `desech` o `tmp`, y **nunca** debe apuntar a la base real
(`insoft_postgres_data`).

## Resultados de la verificación (oct 2026)

- SQLite: 5/5 (base nueva, esquema viejo con datos, adopción, migración fallida y reintento, orden de versiones).
- PostgreSQL pgvector desechable: 2/2 (esquema viejo con datos → actual sin perder filas, segundo arranque sin cambios).
- Hallazgo: en SQLite, `ALTER TABLE ... ADD COLUMN ... NOT NULL DEFAULT CURRENT_TIMESTAMP` falla. El código anterior tenía el mismo límite; ahora se resuelve en dos pasos. En producción (PostgreSQL) no aplica.
