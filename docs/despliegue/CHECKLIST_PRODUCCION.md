# CHECKLIST DE PRODUCCIÓN — MVP 15-oct

Antes de declarar "MVP desplegado": todos los casilleros en ✅ sobre el entorno
REAL de producción (host, no localhost).

## 1. Secretos y acceso

- [ ] `SECRET_KEY` definida por env (NO placeholder): sin ella el backend no arranca.
- [ ] `DEV_AUTH_ENABLED=false` y `VITE_DEV_AUTH` ausente en el build del frontend.
- [ ] Ninguna clave en el repo ni en archivos del servidor con lectura pública.
- [ ] .env del host con `0600` y respaldado fuera de la máquina solo si el equipo lo aprueba.

## 2. HTTPS y CORS

- [ ] Certificado válido (Caddy auto-TLS en la VM; dominio real, no túnel temporal).
- [ ] `http://*` redirige a `https://*`.
- [ ] `BACKEND_CORS_ORIGINS` = SOLO los orígenes reales (frontend + staging UI).
- [ ] Login de Google: orígenes autorizados ya registrados en Google Cloud Console.

## 3. Base de datos

- [ ] Postgres con pgvector (Neon, VM o contenedor prod compose).
- [ ] `CREATE EXTENSION vector` aplicada (las migraciones lo hacen al arrancar).
- [ ] Migraciones ejecutadas contra la URL DIRECTA (no pooler) si es Neon.
- [ ] Seed idempotente ejecutado una vez y estado revisado (85 approved reales).
- [ ] **Backups**: `deploy/backup.sh` agendado (timer) y **restauración probada**
      con `deploy/restore.sh` al menos una vez hacia una DB de prueba.

## 4. IA y límites

- [ ] `AI_PROVIDER` y API keys correctas; probado /api/ai/ask con pregunta real.
- [ ] `AI_DAILY_LIMIT_PER_USER`, `AI_ASK_RATE_LIMIT` y `AI_MODEL_CHAIN` definidos.
- [ ] `OPENROUTER_GLOBAL_LIMIT_PER_MIN` acorde al tier contratado.
- [ ] Comprobada la respuesta degradada (apagar keys y verificar "MODO RESPALDO").

## 5. Observabilidad

- [ ] `/health` 200 y `/ready` 200 (503 solo si DB/extension falla).
- [ ] X-Request-ID presente en respuestas y logs correlacionados.
- [ ] Rotación de logs del compose activa (`max-size`/`max-file`).
- [ ] `LOG_FORMAT=json` y `LOG_LEVEL=INFO` (si hay colector) o `plain` en VM sin colector.

## 6. Smoke Gate (después del deploy)

- [ ] `bash scripts/smoke_prod.sh https://<dominio>` → todas las líneas `[OK]`.
- [ ] Repaso de unidad mostrando 4 opciones por pregunta y respaldo verde.
- [ ] "Agregar preguntas" visible como docente y NO visible como estudiante.
- [ ] Estudiante nuevo entra con código y ve el Curso General.
