# CORS: reglas y patrones por defecto

**Fecha**: 2026-10-14 · **Rama**: `fix/cors-defecto` · **PR**: pequeño, apilado sobre `fix/timeouts-bd`

## Qué cambió

- La regex CORS **por defecto en el código queda vacía** (`BACKEND_CORS_ORIGIN_REGEX=""`):
  solo se aceptan los orígenes exactos de `BACKEND_CORS_ORIGINS` (alias
  ALLOWED_ORIGINS de `.env`). Antes el default incluía rangos privados
  (192.168.x, 100.x de Tailscale, etc.) y `https://*.vercel.app`.
- Cualquier ampliación es ahora **explícita en `.env`** (solo si se pide):
  si no se escribió, no existe.

## Patrones exactos (solo si se piden, pegar en .env)

### 1. Probar el frontend desde el móvil/otro PC de la LAN o por Tailscale

```
BACKEND_CORS_ORIGIN_REGEX=^http://(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3})(:\d+)?$
```

Cubre localhost/127.0.0.1/0.0.0.0 y los rangos privados 10.x, 192.168.x,
172.16-31.x y CGNAT/Tailscale 100.64-127.x, en cualquier puerto. Es el patrón
exacto que venía en el default hasta hoy, restringido a redes privadas.

### 2. Solo los previews de Vercel del proyecto

Cuando los previews de Vercel tengan que llamar a tu backend (PC con túnel u otra URL pública),
añade esta regex en `.env` (cambia `insoft` y `<team>` por los valores reales de tu Vercel):

```
BACKEND_CORS_ORIGIN_REGEX=^https://insoft-([a-z0-9]+)-[a-z0-9]+\.vercel\.app$|^https://insoft-git-[a-z0-9-]+-[a-z0-9]+\.vercel\.app$
```

El prefijo es el patrón EXACTO del proyecto: los previews de Vercel usan
`https://<proyecto>-<hash>-<team>.vercel.app` y las ramas
`https://<proyecto>-git-<rama>-<team>.vercel.app`. Se evita el comodín
`https://.*\.vercel\.app` (cualquier tercero podría montar su propio deploy en
Vercel y que el navegador aceptara su origen con credenciales).

## Tests

`backend/tests/test_cors_defecto.py` (4 pruebas, en memoria, sin red):
1. con settings por defecto el regex es vacío y **abierto un origen de
   Vercel NO permitido** → 400 “disallowed origin”;
2. un origen declarado en BACKEND_CORS_ORIGINS sí responde con
   `access-control-allow-origin`;
3. al fijar la regex en .env manualmente, un preview Vercel SIN
   escapar el prefijo de proyecto se rechaza;
4. con el patrón del proyecto sí se puede.
