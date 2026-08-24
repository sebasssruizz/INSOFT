# Guía — Configurar el inicio de sesión con Google en INSOFT

Esta guía explica cómo activar el botón **Continuar con Google** paso a paso.
No necesitas tarjeta de crédito ni pagar nada: es una configuración gratuita de
Google Cloud.

> **Nota técnica:** INSOFT usa el flujo de *ID token* de Google Identity
> Services. Solo necesitas un **Client ID** — el *Client Secret* **no se usa**
> en este flujo (el backend verifica el token criptográficamente contra Google).

---

## Paso 1 · Crear un proyecto en Google Cloud

1. Entra en [Google Cloud Console](https://console.cloud.google.com/).
2. Inicia sesión con tu cuenta de Google.
3. Arriba a la izquierda, junto al logo, abre el selector de proyectos y pulsa
   **Proyecto nuevo** (*New Project*).
4. Nombre: `INSOFT` (o el que prefieras) → **Crear**.
5. Espera unos segundos y selecciona el proyecto recién creado.

## Paso 2 · Configurar la pantalla de consentimiento

Es la pantalla que verán los usuarios al iniciar sesión ("INSOFT quiere
acceder a tu cuenta…").

1. En el menú lateral: **APIs y servicios** → **Pantalla de consentimiento de OAuth**
   (*APIs & Services → OAuth consent screen*).
2. Tipo de usuario: **Externo** (*External*) → **Crear**.
3. Rellena solo lo obligatorio:
   - **Nombre de la aplicación:** `INSOFT`
   - **Correo de asistencia del usuario:** tu correo
   - **Correo de contacto del desarrollador** (abajo del todo): tu correo
4. Pulsa **Guardar y continuar** en las secciones de *Permisos/Scopes* y
   *Usuarios de prueba* (no hace falta tocar nada más).
5. Finaliza con **Volver al panel**.

> Mientras la app esté en estado **"En pruebas"**, cualquier usuario puede
> iniciar sesión, pero Google puede mostrar un aviso. Para uso real puedes
> pulsar **Publicar aplicación** en esa misma pantalla.

## Paso 3 · Crear el ID de cliente de OAuth

1. Menú lateral: **APIs y servicios** → **Credenciales** (*Credentials*).
2. Arriba: **+ Crear credenciales** → **ID de cliente de OAuth**.
3. **Tipo de aplicación:** `Aplicación web` (*Web application*).
4. **Nombre:** `INSOFT Web`.
5. En **Orígenes de JavaScript autorizados** (*Authorized JavaScript origins*)
   añade:

   ```text
   http://localhost:3000
   ```

   Si accedes también por `0.0.0.0` o por la IP de tu equipo, añádelos igualmente:

   ```text
   http://0.0.0.0:3000
   http://192.168.X.X:3000
   ```

   > No hace falta rellenar "URI de redirección" para este flujo.

6. Pulsa **Crear** y **copia el ID de cliente**, que tiene esta forma:

   ```text
   123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
   ```

## Paso 4 · Configurar INSOFT

Edita el archivo `.env` en la raíz del proyecto y pega el mismo Client ID en
las **dos** variables:

```bash
GOOGLE_CLIENT_ID=123456789012-abc...apps.googleusercontent.com
VITE_GOOGLE_CLIENT_ID=123456789012-abc...apps.googleusercontent.com
```

- `GOOGLE_CLIENT_ID` → la usa el **backend** para verificar los tokens.
- `VITE_GOOGLE_CLIENT_ID` → la usa el **frontend** para mostrar el botón.

### Opcional pero recomendado

```bash
# Correos que serán PROFESORES automáticamente al entrar con Google
TEACHER_EMAILS=tu-correo@gmail.com,otro-profesor@gmail.com

# Cuando Google funcione, desactiva el acceso de desarrollo
DEV_AUTH_ENABLED=false
```

> ⚠️ Todo correo que **no** esté en `TEACHER_EMAILS` entrará como **estudiante**.
> Si alguien se registra con el rol equivocado, puede cambiarlo desde su panel
> de perfil (click en el avatar → "Cambiar a Profesor").

## Paso 5 · Reconstruir y arrancar

Las variables del frontend se incrustan durante el build, así que hay que
reconstruir:

```bash
docker compose down
docker compose up --build
```

## Paso 6 · Probar

1. Abre **http://localhost:3000**.
2. Ahora aparece el botón **Continuar con Google**.
3. Inicia sesión con tu cuenta:
   - Si tu correo está en `TEACHER_EMAILS` → entras como **profesor**.
   - Si no → entras como **estudiante** con el Curso General de Oftalmología.
4. Haz click en tu avatar (arriba a la derecha): el panel lateral mostrará tu
   **foto de Google, nombre y correo** reales, con proveedor "Google".

---

## Producción (cuando despliegues en un dominio real)

1. En Google Cloud Console → Credenciales → tu ID de cliente, añade el origen
   real, p. ej. `https://insoft.tudominio.com`.
2. En el `.env` del servidor:
   ```bash
   BACKEND_CORS_ORIGINS=https://insoft.tudominio.com
   VITE_API_URL=https://api.tudominio.com
   DEV_AUTH_ENABLED=false
   SECRET_KEY=<genera-una-segura: openssl rand -hex 32>
   ```
3. Usa HTTPS (Google exige orígenes seguros en producción, salvo localhost).
4. Considera **Publicar aplicación** en la pantalla de consentimiento.

---

## Solución de problemas

| Error | Causa y solución |
|---|---|
| El botón de Google no aparece | Falta `VITE_GOOGLE_CLIENT_ID` en `.env` o no reconstruiste. Ejecuta `docker compose up --build` |
| `The given origin is not allowed for the given client ID` | El origen desde el que navegas no está en los *orígenes autorizados* del Client ID. Añádelo en Google Cloud Console (Paso 3) |
| `Token de Google inválido` al entrar | El Client ID del frontend y del backend **no coinciden**. Deben ser exactamente el mismo en `GOOGLE_CLIENT_ID` y `VITE_GOOGLE_CLIENT_ID` |
| La ventana de Google no se abre | El navegador bloqueó el popup. Permite ventanas emergentes para `localhost` |
| `access_blocked` / `Error 403` | La pantalla de consentimiento está en pruebas y el correo no está autorizado: añade tu correo como *usuario de prueba* o publica la aplicación |
| Entré como estudiante siendo profesor | Tu correo no está en `TEACHER_EMAILS`. Añádelo y vuelve a entrar, o cámbialo desde el panel de perfil (avatar → *Cambiar a Profesor*) |
