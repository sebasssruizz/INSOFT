# Paso a paso: pruebas en internet (Vercel + Neon + backend en el PC con túnel)

Ruta vigente para el MVP (oct 2026): **frontend en Vercel**, **base en Neon**, **backend en un PC
del equipo** con un **túnel HTTPS de URL estable**. La VM y el dominio propio quedan en stand by
hasta noviembre.

Cada paso termina con una comprobación. No avances si la comprobación falla.

---

## 0. Topología

```
Navegador ─► Vercel (frontend, estático) ─► https://<túnel-backend>  ─► PC: backend :8000 ─► Neon (Postgres + pgvector)
```

- Vercel sirve el frontend. Llama al backend con `VITE_API_URL`, que se **fija al compilar**.
- El backend corre en Docker en el PC (`docker compose`), publicado solo en `127.0.0.1`.
- El túnel lleva HTTPS desde internet hasta `127.0.0.1` del PC.
- Neon guarda los datos. El backend usa la **cadena directa** para DDL y la agrupada para consultas, según el ajuste de la base.
- Neon es la única base de datos de pruebas. La base local del compose (`insoft_postgres_data`) **no se toca**.

---

## 1. Preparar el PC

1. **Docker al arrancar**: Docker Desktop o el servicio `docker` activado (`systemctl enable docker`).
2. **Sin suspensión**: el PC no debe dormir ni hibernar mientras haya pruebas. Ajustes de energía: "nunca suspender" con la tapa cerrada si el equipo sigue en uso.
3. **Reinicio controlado**: si se reinicia, el stack vuelve solo porque el compose usa `restart: unless-stopped`. El túnel debe arrancar también (ver §4).
4. **Espacio y RAM**: el backend con embeddings ocupa ~1 GB. Cierra aplicaciones pesadas durante las pruebas.

Comprobación: `docker info` responde y `systemctl is-enabled docker` devuelve `enabled`.

---

## 2. Configurar y arrancar el stack

En la carpeta del repositorio, crea `.env` a partir de `.env.example`. **No lo copies tal cual**:

```bash
cp .env.example .env
```

Variables obligatorias (generadas por ti, nunca en el repositorio):

| Variable | Cómo generarla |
|---|---|
| `POSTGRES_PASSWORD` | `openssl rand -hex 16` |
| `SECRET_KEY` | `openssl rand -hex 32` (sin ella el backend se niega a arrancar con `DEV_AUTH_ENABLED=false`) |
| `BACKEND_CORS_ORIGINS` | Origen **exacto** del frontend, p. ej. `https://insoft-staging.vercel.app` |
| `GOOGLE_CLIENT_ID` | Credencial web de Google (§6) |
| `DEV_AUTH_ENABLED` | `false` |
| `DOCS_ENABLED` | `false` |
| `SEED_MODE` | Vacío (queda `if_empty` fuera de desarrollo) |

Arranque:

```bash
docker compose up -d --build
docker compose ps
```

Comprobación local (desde el propio PC):

```bash
curl -s http://127.0.0.1:8000/health      # {"status":"ok"} o similar
curl -s http://127.0.0.1:8000/ready       # base de datos y pgvector OK
```

Si `/ready` falla, mira `docker compose logs backend --tail=100`. El backend reintenta 30 veces
mientras la base termina de arrancar.

---

## 3. Base en Neon

1. Crea un **proyecto** en Neon. Anota la región.
2. Activa la extensión `vector` en la rama de pruebas:

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

   El backend la crea solo al arrancar (`ensure_pgvector_extension`), pero hacerlo a mano confirma que la cuenta puede usarla.
3. Copia **dos** cadenas desde el panel de conexión:
   - **Directa** (sin `-pooler` en el host): para DDL, migraciones y el bootstrap.
   - **Agrupada** (`-pooler`): para la aplicación en régimen, si el plan la usa.
   Ninguna va en el repositorio ni en capturas. Guárdalas en tu gestor de secretos.
4. Un Neon que se duerme tarda en despertar: la primera conexión puede fallar. Reintenta.

Comprobación (con la cadena directa, en una terminal):

```bash
cd backend
DATABASE_URL='postgresql+psycopg2://…directa…?sslmode=require' \
  PYTHONPATH=. .venv/bin/python -m app.scripts.bootstrap_remote   # dry-run: no escribe nada
```

---

## 4. Bootstrap de contenido (primera vez o base nueva)

El bootstrap crea esquema, contenido oficial, curso general e indexa el RAG. Es idempotente.

```bash
cd backend
DATABASE_URL='postgresql+psycopg2://…directa…?sslmode=require' PYTHONPATH=. \
  .venv/bin/python -m app.scripts.bootstrap_remote \
  --apply --confirm-host <host-completo-de-la-cadena> \
  [--teacher-email correo@institucion] [--skip-index]
```

- `--confirm-host` debe ser el **host completo** de la cadena (no la versión enmascarada). Si no coincide, el script se niega.
- `--teacher-email` promueve a docente un correo que **ya haya entrado con Google**. Si el usuario no existe, el paso se salta.
- Relanzarlo no daña nada.

Comprobación: la salida muestra `[1/4] esquema OK`, unidades y subtemas, y `Bootstrap completado`.

---

## 5. Túnel HTTPS con URL estable

Antes de elegir, lee los límites vigentes de cada opción. Las cifras de la tabla se verificaron
en la documentación pública indicada; compruébalas de nuevo si pasan meses.

| Opción | URL estable | Requisitos | Límites vigentes (documentación) | Veredicto |
|---|---|---|---|---|
| **Tailscale Funnel** | Sí: `https://<equipo>.<tailnet>.ts.net`, mientras no cambie el nombre del equipo | Cuenta Tailscale, MagicDNS, HTTPS del tailnet, atributo `funnel` en la política | Solo puertos **443, 8443 y 10000**. Ancho de banda no configurable. Está en **beta**. Documentación revisada el 20-ene-2026. | **Recomendada para la ruta actual**: sin dominio propio, URL fija y sin cuenta de pago. |
| **ngrok con dominio** | Sí, con dominio de desarrollo o dominio de ngrok | Cuenta ngrok, authtoken | **Free**: hasta 3 endpoints online, 1 GB de transferencia, 20 000 peticiones HTTP/S, **página intermedia (interstitial)** en endpoints HTTP/S. **Hobbyist** ($10/mes): sin interstitial, 5 GB, 100 000 peticiones. Dominio propio solo desde Pay-as-you-go. (Precios consultados el 12-oct-2026.) | Válida si el interstitial no molesta. Con Free, el navegador verá una página de advertencia antes de la app. |
| **Cloudflare Tunnel con nombre** | Sí | **Cuenta Cloudflare y un dominio gestionado en Cloudflare** (requisito para publicar aplicaciones) | Documentación actualizada el 30-sep-2026. | **Hoy no es viable**: no hay dominio (stand by hasta noviembre). Reevaluar entonces. |
| **Cloudflare Quick Tunnel** (`trycloudflare.com`) | **No**: cambia en cada ejecución | Ninguna | Sin garantía de disponibilidad; 200 peticiones simultáneas máximo; solo para pruebas. | **Descartada**: Vercel fija la URL del backend al compilar y se rompería en cada reinicio. |

### 5.1 Tailscale Funnel (ruta recomendada)

```bash
tailscale up                                  # inicia sesión en tu tailnet (una vez)
tailscale funnel --bg 3000                    # frontend local → https://<equipo>.<tailnet>.ts.net
tailscale funnel --bg --https=8443 8000       # backend       → https://<equipo>.<tailnet>.ts.net:8443
tailscale funnel status
```

Notas (según la referencia de la CLI, revisada el 26-ene-2026):

- La sintaxis es `tailscale funnel [--bg] --https=<puerto> <destino>`. Sin `--https` se usa 443.
- La primera vez, `tailscale funnel` pide aprobar el atributo `funnel` en la consola de administración.
- Los puertos públicos son los únicos permitidos (443, 8443, 10000). El backend usa 8443 porque el 443 ya lo usa el frontend.
- **Con `--bg` el funnel se reanuda solo** tras reiniciar el equipo o ejecutar `tailscale up`. Sin `--bg`, hay que relanzarlo a mano.
- Para quitar un funnel: repite el comando con `off` al final (p. ej. `tailscale funnel --https=8443 8000 off`).
- `tailscale funnel reset` borra **toda** la configuración de funnels. No lo ejecutes sin querer: corta el acceso.

Comprobación desde fuera del PC (p. ej. desde el móvil con datos, sin Wi-Fi):

```bash
curl -s https://<equipo>.<tailnet>.ts.net:8443/health
```

### 5.2 ngrok (alternativa)

```bash
ngrok config add-authtoken <authtoken>        # una vez, desde tu cuenta
ngrok http --domain=<dominio-de-desarrollo> 8000
```

Solo sirve al backend (el frontend va en Vercel). Con Free, la página intermedia de ngrok aparece en
navegador. Si eso es un problema para las pruebas, el plan Hobbyist la quita.

---

## 6. Google Cloud (inicio de sesión)

La aplicación usa el **ID token** de Google Identity Services. No hay redirección con código, así que
la credencial debe ser de tipo **aplicación web**.

1. Google Cloud Console → **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**.
2. Tipo: **Aplicación web** (no "Aplicación de escritorio": daría `redirect_uri_mismatch`).
3. **Orígenes de JavaScript autorizados** (exactos, sin barra final):
   - `https://<proyecto>.vercel.app` (y el dominio de previsualización si lo usas)
   - `https://<equipo>.<tailnet>.ts.net` si el frontend también se sirve por el túnel
4. **URI de redirección autorizados**: no se usan con el flujo del ID token. Deja vacío o añade la URL del frontend.
5. Copia el **ID de cliente** (`…apps.googleusercontent.com`) a `GOOGLE_CLIENT_ID` del backend y a `VITE_GOOGLE_CLIENT_ID` del frontend.
6. Si la pantalla de consentimiento está en "Pruebas", añade el correo de cada tester como usuario de prueba.

Comprobación: en el login de la app aparece el botón de Google y el inicio de sesión llega al backend
con un `200` en `/api/auth/google` (ver §7).

---

## 7. Vercel (frontend)

1. Importa el repositorio en Vercel. **Root Directory: `frontend`**. Framework: Vite.
2. **Production Branch: `staging`** (decisión del equipo: la línea de trabajo es staging).
3. Variables de entorno (Production y Preview):

   | Variable | Valor |
   |---|---|
   | `VITE_API_URL` | `https://<equipo>.<tailnet>.ts.net:8443` (el backend por el túnel, **sin barra final**) |
   | `VITE_GOOGLE_CLIENT_ID` | El ID de cliente de §6 |

   **`VITE_API_URL` es obligatoria en producción.** Si falta, el build **falla** a propósito
   (`vite.config.js`). No hay valor por defecto que adivinar.
4. Despliega. Comprueba que el build pasa y que el `check-dist` no reporta cadenas prohibidas.
5. El `vercel.json` del frontend ya reescribe las rutas de la SPA a `index.html`.

Comprobación: abre `https://<proyecto>.vercel.app/` y revisa que el navegador llama al backend de
§5 (pestaña Red, sin errores de CORS).

---

## 8. Backend: CORS, orígenes y sesión

`BACKEND_CORS_ORIGINS` debe contener **exactamente** el origen de cada frontend que va a llamar al
backend (esquema, host y puerto; sin barra final), separados por comas:

```
BACKEND_CORS_ORIGINS=https://<proyecto>.vercel.app,https://<equipo>.<tailnet>.ts.net
```

- Si el origen no coincide, el navegador bloquea la respuesta por CORS aunque el backend funcione.
- `BACKEND_CORS_ORIGIN_REGEX` debe quedar **vacío** en pruebas: no aceptes comodines.
- Tras cambiar `.env`, reinicia el backend: `docker compose up -d backend`.

---

## 9. Verificación capa por capa

Ejecuta estos comandos en orden. Cada uno tiene un resultado esperado.

```bash
# 1) Backend en el PC
curl -s http://127.0.0.1:8000/health                  # 200
curl -s http://127.0.0.1:8000/ready                   # 200, base y pgvector OK

# 2) Backend por el túnel (desde fuera del PC)
curl -s https://<equipo>.<tailnet>.ts.net:8443/health # 200

# 3) Documentación desactivada (DOCS_ENABLED=false)
curl -s -o /dev/null -w "%{http_code}\n" https://<equipo>.<tailnet>.ts.net:8443/docs   # 404

# 4) Sin sesión, la API responde 401 con mensaje estable
curl -s -i https://<equipo>.<tailnet>.ts.net:8443/api/users/me | head -n 1           # HTTP/2 401

# 5) CORS: el origen de Vercel es aceptado
curl -s -i -X OPTIONS https://<equipo>.<tailnet>.ts.net:8443/api/courses \
  -H "Origin: https://<proyecto>.vercel.app" \
  -H "Access-Control-Request-Method: GET" | grep -i "access-control-allow-origin"    # el origen de Vercel

# 6) Frontend en línea
curl -s -o /dev/null -w "%{http_code}\n" https://<proyecto>.vercel.app/              # 200

# 7) Acceso de desarrollo cerrado: POST /api/auth/dev debe dar 403
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://<equipo>.<tailnet>.ts.net:8443/api/auth/dev \
  -H "Content-Type: application/json" -d '{"email":"x@example.com","name":"x","role":"STUDENT"}'  # 403
```

Para el RAG real, necesitas un token: entra con Google en la app y usa la sesión. Sin IA configurada,
la respuesta es el modo respaldo (`degraded: true`), no un error.

---

## 10. Errores comunes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Consola: `CORS error` / `No 'Access-Control-Allow-Origin'` | El origen de Vercel no está en `BACKEND_CORS_ORIGINS`, o difiere en barra final o `http`/`https` | Corrige la variable y reinicia el backend (§8). |
| Build de Vercel falla con "Falta VITE_API_URL" | No se definió la variable en Vercel | Defínela en Production y Preview (§7). Es intencional. |
| Google: `redirect_uri_mismatch` | Credencial de tipo escritorio, o el origen no está en "Orígenes de JavaScript" | Crea una credencial **aplicación web** y añade el origen exacto (§6). |
| Google: `Token de Google inválido` | `GOOGLE_CLIENT_ID` del backend no coincide con el del frontend, o el correo no está verificado | Iguala los dos IDs. Un correo sin verificar se rechaza a propósito. |
| `/ready` falla al arrancar | Neon dormido o cadena incorrecta | Reintenta; revisa `DATABASE_URL` (directa vs agrupada). |
| Funnel responde pero la app no | Puerto del backend no es 8443, o el backend está caído | `tailscale funnel status`; `docker compose ps`. |
| Tras reiniciar el PC, no hay acceso | El funnel no se creó con `--bg`, o el PC se suspendió | Revisa §1 y `tailscale funnel status`; si falta, vuelve a crearlo con `--bg` (§5.1). |
| `401` tras un rato de uso | La sesión caducó (`ACCESS_TOKEN_EXPIRE_MINUTES`, 7 días por defecto) | Vuelve a entrar. El frontend ya limpia la sesión y redirige. |
| `503 [mantenimiento]` | `MAINTENANCE_MODE=true` | Desactívalo, o entra como docente (ver `docs/operacion/INTERRUPTORES.md`). |
| `503 [asistente-desactivado]` o `429 [asistente-tope-global]` | `AI_ENABLED=false` o tope diario agotado | Es el comportamiento configurado (ver interruptores). |

---

## 11. Rutas alternativas

- **Arranque automático de los túneles**: con `--bg` ya se reanudan tras un reinicio (§5.1). Solo si
  se usa Funnel sin `--bg` haría falta una unidad `systemd`; no se recomienda.
- **Respaldos**: ver `docs/operacion/RESPALDOS.md`. Programa el respaldo nocturno; no lo dejes sin programar.
- **Neon en otra región**: la latencia sube. Solo cambia la cadena; el resto no cambia.
- **VM de noviembre** (stand by): el mismo `docker compose` en una máquina con IP fija. Entonces sí
  conviene dominio propio y HTTPS con certificado del proveedor. No se documenta aquí.
- **Render de pago**: no se recomienda para el backend: 512 MB no bastan con embeddings (ver `docs/perf/SIMULACION_RENDER_FREE.md`).

---

## 12. Acceso de desarrollo

En el build de producción **no existe** el acceso de desarrollo (tarjeta de login ni `POST /api/auth/dev`).
Para probar en local con cuentas de demostración, usa `npm run dev` con `DEV_AUTH_ENABLED=true` en el
backend local. Nunca actives `DEV_AUTH_ENABLED=true` en el PC que sirve el túnel.
