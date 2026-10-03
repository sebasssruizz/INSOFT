#!/usr/bin/env bash
# Smoke test de INSOFT en producción (sin LLM).
#
# Uso:   ./smoke.sh https://mi-dominio.com
#        ./smoke.sh https://localhost        (pruebas locales, usa -k)
#
# Comprueba: /health, /docs y /openapi.json cerrados, login de desarrollo
# deshabilitado, cabeceras de seguridad, carga del frontend y fallback SPA,
# y que la API exige autenticación. Sale 0 si todo pasa, 1 si algo falla.
set -u
BASE="${1:-https://localhost}"
failures=0
ok()   { echo "  OK    $1"; }
fail() { echo "  FALLA $1"; failures=$((failures + 1)); }

CURL="curl -sk --max-time 15"

echo "== Smoke test INSOFT contra $BASE =="

# 1) Salud
code=$($CURL -o /tmp/smoke_health.$$ -w "%{http_code}" "$BASE/health")
body=$(cat /tmp/smoke_health.$$ 2>/dev/null); rm -f /tmp/smoke_health.$$
if [ "$code" = "200" ] && echo "$body" | grep -q '"ok"'; then ok "/health 200"; else fail "/health (code=$code)"; fi

# 2) /docs y /openapi.json cerrados (el backend no debe exponerlos)
code=$($CURL -o /dev/null -w "%{http_code}" "$BASE/api/openapi.json")
if [ "$code" = "404" ]; then ok "/api/openapi.json cerrado (404)"; else fail "/api/openapi.json (code=$code)"; fi

swagger=$($CURL "$BASE/docs" | grep -c "Swagger UI" || true)
if [ "$swagger" = "0" ]; then ok "/docs sin Swagger UI"; else fail "/docs expone Swagger UI"; fi

# 3) Login de desarrollo deshabilitado
code=$($CURL -o /dev/null -w "%{http_code}" -X POST "$BASE/api/auth/dev" \
  -H "Content-Type: application/json" -d '{"email":"smoke@test.local","name":"smoke","role":"student"}')
if [ "$code" = "400" ]; then ok "login de desarrollo deshabilitado (400)"; else fail "/api/auth/dev (code=$code, esperado 400)"; fi

# 4) Cabeceras de seguridad
hsts=$($CURL -D - -o /dev/null "$BASE/health" | grep -ci "strict-transport-security")
if [ "$hsts" -ge 1 ]; then ok "HSTS presente"; else fail "falta Strict-Transport-Security"; fi

nosniff=$($CURL -D - -o /dev/null "$BASE/" | grep -ci "x-content-type-options")
if [ "$nosniff" -ge 1 ]; then ok "X-Content-Type-Options presente"; else fail "falta X-Content-Type-Options"; fi

# 5) Frontend: portada y fallback SPA
root=$($CURL "$BASE/" | grep -c '<div id="root">')
if [ "$root" -ge 1 ]; then ok "index.html carga la app"; else fail "el index no contiene #root"; fi

spa=$($CURL "$BASE/unidad/6/subtema/1" | grep -c '<div id="root">')
if [ "$spa" -ge 1 ]; then ok "fallback SPA funciona"; else fail "fallback SPA no sirve index.html"; fi

# 6) La API exige autenticación (no debe filtrar contenido sin token)
code=$($CURL -o /dev/null -w "%{http_code}" "$BASE/api/courses/1/topics")
if [ "$code" = "401" ] || [ "$code" = "403" ]; then ok "API protegida ($code)"; else fail "/api/courses/1/topics sin token (code=$code, esperado 401/403)"; fi

echo "== Resultado: $failures fallos =="
[ "$failures" = "0" ]
