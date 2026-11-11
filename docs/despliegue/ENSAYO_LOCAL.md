# Ensayo local tipo Neon — reproducción del despliegue de pruebas en internet

El ensayo reproduce, en contenedores locales, la topología del despliegue de pruebas
(Vercel + Neon + backend en el PC): pgbouncer como conexión **agrupada**, PostgreSQL con
**SSL obligatorio** en ambos lados, conexión **directa** para DDL, arranque en frío de la
base y el frontend de producción servido desde **otro origen** para medir CORS.

Todo es desechable: contenedores sin volumen, sin puertos de base publicados, secretos y
certificados de prueba generados fuera del repositorio (se borran con `limpiar.sh`).

Código: `deploy/ensayo/`. Recorridos: `backend/scripts/recorridos_api.py`
(`backend/scripts/ensayo_tokens.py` crea los usuarios de prueba).

## Qué es y qué no es

| Aproximación a Neon | Diferencia declarada |
|---|---|
| pgbouncer transaction pooling con TLS en ambos lados | Es pgbouncer "nuestro", no el pooler de Neon; mismas reglas, distinta implementación. |
| Postgres SSL obligatorio (pg_hba con `hostnossl … reject`) | Certificado de prueba de 3 días (el cliente usa `sslmode=require`, no verifica identidad). |
| Conexión directa para DDL (engine `NullPool`) | El host difiere solo en el nombre (pg vs pgbouncer), como en Neon. |
| Arranque en frío: base pausada 20 s con `docker pause` | Neon suspende más suavemente (la reconecta al primer uso); la pausa es un caso más duro. |
| LLM: mock HTTPS en el contenedor con DNS `openrouter.ai` → mock | Nunca sale a internet. El certificado "openrouter.ai" es de la CA de prueba. |

## Uso

```bash
bash deploy/ensayo/preparar.sh        # secretos y certificados de prueba fuera del repo
bash deploy/ensayo/levantar.sh        # pg → pgbouncer (docker cp de cert/userlist) → mock → backend
VITE_API_URL=http://127.0.0.1:8010 npm run build --prefix frontend   # build de producción
python3 deploy/ensayo/servir_frontend.py frontend/dist 4173          # SPA como en Vercel

# contenido y datos de prueba (dentro del backend del ensayo)
docker exec -w /srv/src tmp-ensayo-backend \
  python -m app.scripts.bootstrap_remote --apply --confirm-host tmp-ensayo-pgbouncer
docker exec -w /srv/src tmp-ensayo-backend python scripts/ensayo_tokens.py \
  > ~/Documentos/INSOFT-evidencias/ensayo-run/tokens.json   # JSON con permisos 600

# recorridos de API (22 comprobaciones) y panel en el navegador
backend/.venv/bin/python backend/scripts/recorridos_api.py \
  --base http://127.0.0.1:8010 --tokens ~/Documentos/INSOFT-evidencias/ensayo-run/tokens.json \
  --out ~/Documentos/INSOFT-evidencias/ensayo-recorridos.json

bash deploy/ensayo/limpiar.sh         # detiene contenedores y borra secretos/certificados
```

## Resultados (11–12 oct 2026)

### Recorridos de API — 22/22

Estudiante (login y sesión, cursos, unidades, subtema con preguntas, respuesta calificada en
el servidor, progreso, práctica, consulta al asistente con IA simulada, 401/403) y docente
(crear curso, unirse con código, pregunta con 4 opciones, 422 con 3 opciones, generación IA,
aprobar pendiente, estadísticas y CSV), más el caso de proveedor caído. Reporte completo:
`INSOFT-evidencias/ensayo-recorridos.json`.

### Adopción y migraciones

- La base existió primero con el esquema de `staging` (create_all) y al arrancar el código nuevo
  aplicó las **3 migraciones** (línea base + índice + contador) **sin perder datos**: `schema_migrations`
  quedó con las 3 versiones.
- Bootstrap contra la agrupada con confirmación de host: 9 unidades, 26 subtemas, 85 preguntas,
  128 fragmentos. Relanzado: idempotente.

### CORS (frontend de producción en otro origen)

Configuración de producción (`BACKEND_CORS_ORIGIN_REGEX` **vacío**, orígenes exactos):

| Origen | Resultado |
|---|---|
| `http://127.0.0.1:4173` (en la lista) | permitido |
| `https://insoft-ensayo.vercel.app` (en la lista) | permitido |
| `http://localhost:4173` | 400 (no está en la lista) |
| `https://otro-proyecto.vercel.app` | 400 |
| `http://evil.example.test` | 400 |
| `http://192.168.1.50:4173` | 400 |

Con la **regex por defecto del código** (vacía solo si el compose la sobrescribe) sí pasaban
`localhost:<cualquier-puerto>` y cualquier `*.vercel.app`: hay que dejarla **vacía en producción**.

### SSL obligatorio

| Prueba | Resultado |
|---|---|
| pgbouncer con `sslmode=require` y contraseña correcta | conecta (TLS 1.3) |
| pgbouncer con `sslmode=disable` | rechazada |
| pgbouncer con contraseña incorrecta | rechazada |
| Postgres directo con `sslmode=disable` | **rechazada** (regla `hostnossl … reject`) |

### Arranque en frío

- Reinicio completo del backend: `/ready` responde en **7,3 s** (incluye migraciones).
- Base pausada 20 s: las peticiones se quedan **colgadas** hasta el timeout del cliente
  (`000` a los 30 s), sin error rápido; tras reanudar, respuestas 200 en 0,06–0,33 s.
  Causa principal: pgbouncer sin `query_wait_timeout` (espera indefinida) y el cliente de
  la app sin `statement_timeout`. **Recomendación**: fijar `query_wait_timeout=15` en el
  pooler y considerar `options=-c statement_timeout=15000` en la app.
- Nota: la pausa congeló también la conexión del pool de la app; tras reanudar se recuperó
  sola (`pool_pre_ping`), sin reiniciar el backend.

### Frontend real en el navegador (Chromium sin cabeza, 390 px)

Con el build de producción servido desde `127.0.0.1:4173` llamando al backend del ensayo:
sesión leída, perfil completado, panel del estudiante pintado con los datos del curso;
**cero peticiones de red fallidas y cero errores de consola o JS**.

### Hallazgo del modelo de embeddings (corregido)

Con el modelo ya en la imagen, fastembed 0.7.3 **consulta HuggingFace aunque el modelo esté en
caché** y fallaba la indexación con la red bloqueada. Añadido `EMBEDDINGS_LOCAL_ONLY=true`
(carga solo desde la caché; por defecto sigue `false`). Con la opción, el bootstrap indexa
sin zal de red: 26 subtemas, 128 fragmentos.

## Límites de esta prueba

- No se probó Google OAuth real ni Vercel real (no hay despliegue; la guía oficial de paso a paso
  sigue en `docs/despliegue/PASO_A_PASO_STAGING.md`).
- El LLM es un mock local: se valida el camino de la aplicación, no los modelos de verdad.
- `docker pause` es un caso de arranque en frío más duro que Neon suspendido.
- La imagen del backend es la de ensayo (`insoft-backend-sim`) con el código montado desde el repo
  (equivalente a production para este fin; no se reconstruyó la imagen completa).
