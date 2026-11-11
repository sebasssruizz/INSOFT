#!/usr/bin/env bash
# Smoke test de PRODUCCIÓN (read-only): corre contra el dominio real.
#   bash scripts/smoke_prod.sh https://insoft.edu.co
# Salida: [OK]/[FAIL] por ítem y exit 1 si alguno falla. No usa credenciales.
set -uo pipefail

BASE="${1:-}"
if [ -z "$BASE" ]; then
  echo "Uso: $0 https://dominio-del-backend-o-site (sin / al final)"
  exit 2
fi
BASE="${BASE%/}"
FAIL=0

check() { # $1 nombre, $2 condición (0 = ok; usa valor por defecto 1 si falta)
  local status="${2:-1}"
  if [ "$status" -eq 0 ]; then
    echo "[OK]  $1"
  else
    echo "[FAIL] $1"
    FAIL=1
  fi
}

# 1) salud viva y lista
curl -fsS "$BASE/health" >/dev/null 2>&1
check "/health responde 200" $?

curl -fsS "$BASE/ready" >/dev/null 2>&1
check "/ready responde 200 (DB + pgvector OK)" $?

# 2) login dev BLOQUEADO en producción
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/auth/dev" \
  -H 'Content-Type: application/json' -d '{"email":"smoke@test.com","name":"x","role":"TEACHER"}')
[ "$CODE" = "403" ] || [ "$CODE" = "404" ] || [ "$CODE" = "400" ]
if [ "$CODE" = "403" ]; then
  check "/api/auth/dev responde $CODE (dev OFF)" 0
else
  check "/api/auth/dev responde esperado 403, real $CODE" 1
fi

# 3) cabeceras básicas de seguridad en el frontend (si el dominio sirve el SPA)
BODY=$(curl -fsSL "$BASE/" 2>/dev/null || true)
if [ -n "$BODY" ]; then
  echo "$BODY" | grep -qi "insoft"
  check "el sitio responde HTML del frontend" $?
else
  echo "[SKIP] el dominio no sirve el frontend (¿es solo backend?)"
fi

ASSET=$(echo "$BODY" | grep -oE '/assets/index-[^"]+\.js' | head -1 || true)
if [ -n "$ASSET" ]; then
  JS=$(curl -fsSL "$BASE$ASSET" 2>/dev/null || true)
  if echo "$JS" | grep -q "Acceso de desarrollo"; then
    check "bundle SIN tarjeta de acceso dev" 1
  else
    check "bundle SIN tarjeta de acceso dev" 0
  fi
  echo "$JS" | grep -q "Agregar preguntas"
  check "bundle contiene 'Agregar preguntas'" $?
  if echo "$JS" | grep -q "formatDurationShort"; then
    check "bundle SIN mostrar tiempos" 1
  else
    check "bundle SIN mostrar tiempos" 0
  fi
fi

# 4) 401 sin token en rutas protegidas (una muestra)
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/users/me")
[ "$CODE" = "401" ]
check "/api/users/me sin token -> 401" $?

echo
if [ "$FAIL" -eq 0 ]; then
  echo "SMOKE PROD: OK"
else
  echo "SMOKE PROD: CON FALLAS"
fi
exit $FAIL
