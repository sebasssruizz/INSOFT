#!/usr/bin/env bash
# Verifica que un respaldo se puede RESTAURAR, en un contenedor PostgreSQL DESECHABLE.
#
# Uso: bash backend/scripts/verificar_respaldo.sh <archivo.dump>
#
# - Arranca un contenedor pgvector sin volumen y sin puertos publicados (solo
#   accesible desde dentro por el socket local).
# - Restaura el .dump en una base temporal cuyo nombre contiene "tmp".
# - Compara el recuento de filas de las tablas clave con el .meta del respaldo.
# - Destruye el contenedor pase lo que pase.
#
# NUNCA apunta a la base real: no se conecta a ningún host externo.
set -euo pipefail

DUMP=${1:?uso: verificar_respaldo.sh <archivo.dump>}
META="${DUMP%.dump}.meta"
IMAGE=${BACKUP_IMAGE:-pgvector/pgvector:pg16}
[ -f "$DUMP" ] || { echo "[verifica] no existe $DUMP"; exit 1; }
[ -f "$META" ] || { echo "[verifica] falta el recuento $META"; exit 1; }

NAME="tmp-verifica-$(date +%s)"
DB="tmp_restauracion_desech"
PASS=$(openssl rand -hex 16)   # solo para el contenedor efímero; no se imprime

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" -e POSTGRES_USER=verifica -e POSTGRES_PASSWORD="$PASS" \
  -e POSTGRES_DB="$DB" "$IMAGE" >/dev/null

for _ in $(seq 1 60); do
  docker exec "$NAME" pg_isready -U verifica >/dev/null 2>&1 && break
  sleep 2
done
docker exec "$NAME" pg_isready -U verifica >/dev/null

docker cp "$DUMP" "$NAME:/tmp/respaldo.dump"
docker exec "$NAME" sh -c "pg_restore --no-owner --no-privileges -U verifica -d $DB /tmp/respaldo.dump" \
  || echo "[verifica] pg_restore devolvió avisos (revisar si son ajenos a los datos)"

FALLOS=0
while IFS='=' read -r tabla esperado; do
  [ -z "$tabla" ] && continue
  if [ "$esperado" = "NA" ]; then
    echo "[verifica] $tabla: sin recuento de origen (omitida)"
    continue
  fi
  obtenido=$(docker exec "$NAME" psql -U verifica -d "$DB" -tAX -c "SELECT count(*) FROM ${tabla}" 2>/dev/null || echo "ERR")
  if [ "$obtenido" = "$esperado" ]; then
    echo "[verifica] $tabla: $obtenido filas (OK)"
  else
    echo "[verifica] $tabla: esperado $esperado, restaurado $obtenido (FALLO)"
    FALLOS=$((FALLOS + 1))
  fi
done < "$META"

if [ "$FALLOS" -eq 0 ]; then
  echo "[verifica] RESULTADO: PASA — el respaldo se restaura y los recuentos coinciden."
else
  echo "[verifica] RESULTADO: FALLA — $FALLOS tabla(s) no coinciden."
  exit 1
fi
