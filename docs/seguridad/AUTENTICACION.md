# Autenticación (Google y JWT)

Código: `backend/app/auth/google.py`, `backend/app/auth/jwt.py`, `backend/app/auth/dependencies.py`.
Pruebas: `backend/tests/test_auth_endurecido.py` (25 pruebas, tokens simulados, sin red).

## Google (ID token)

Dos capas:

1. **Criptográfica** (`google-auth`): firma contra las claves públicas de Google y expiración.
2. **Reglas propias** (`validar_claims_google`):
   - `iss` ∈ {`accounts.google.com`, `https://accounts.google.com`};
   - `aud` = `GOOGLE_CLIENT_ID` de este backend;
   - `exp` en el futuro y presente;
   - `sub` y `email` presentes;
   - `email_verified` = verdadero. Sin esto no se vincula una cuenta existente por correo.

El correo se normaliza a minúsculas. Cualquier fallo devuelve **401** con un mensaje claro.

## JWT de sesión

- Algoritmo fijo (`ALGORITHM`, por defecto HS256). Un token con `alg=none` se rechaza.
- Son obligatorios `exp` y `sub`. Un token sin expiración no es válido.
- Caducado, mal firmado o de un usuario que ya no existe → **401** con `detail: "No autenticado o token inválido."` y `WWW-Authenticate: Bearer`.
- El rol se lee **de la base de datos** en cada petición, no del token.
- `ACCESS_TOKEN_EXPIRE_MINUTES` (por defecto 7 días): el arranque se niega si está fuera de 5 min – 30 días.

## Comportamiento en el frontend

Un 401 limpia la sesión y vuelve a la pantalla de entrada (`apiFetch` en `frontend/src/services/api.js`).
El 403 no cierra sesión (es un permiso, no una sesión vencida).

## Pendiente (fuera de esta tarea)

- Rotación de `SECRET_KEY` sin cerrar sesiones: hoy cambiarla invalida todos los tokens.
- Revocación de tokens antes de su caducidad (no existe lista de revocación).
