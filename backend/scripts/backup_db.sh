#!/usr/bin/env bash
# Respaldo de la base de INSOFT con pg_dump (formato custom) + recuento + retención.
#
# SOLO LECTURA sobre la base: pg_dump no bloquea, no modifica ni borra datos.
# La restauración real NO se hace aquí: ver docs/operacion/RESPALDOS.md y
# backend/scripts/verificar_respaldo.sh (restaura en un contenedor desechable).
#
# Dos modos de conexión:
#   container (por defecto): pg_dump dentro del contenedor de la base del compose.
#                            No necesita contraseña en la línea de órdenes.
#   direct:   BACKUP_MODE=direct y variables PGHOST, PGPORT, PGUSER, PGDATABASE,
#             PGPASSWORD, PGSSLMODE (cadena DIRECTA, sin pooler). Corre pg_dump en
#             un contenedor efímero con red del host. La contraseña se pasa por
#             variable de entorno, nunca como argumento visible en `ps`.
#
# Variables:
#   BACKUP_DIR        carpeta de destino (default: $HOME/insoft-respaldos, permisos 700)
#   BACKUP_RETENTION  días que se conservan (default 14)
#   BACKUP_KEEP_MIN   mínimo de respaldos que nunca se borran (default 3)
#   BACKUP_CONTAINER  contenedor de la base en modo container (default insoft-db)
#   BACKUP_IMAGE      imagen con cliente PostgreSQL (default pgvector/pgvector:pg16)
#   POSTGRES_DB / POSTGRES_USER (modo container; defaults oftallearn)
#
# Cada respaldo genera dos archivos: insoft_<fecha>.dump (datos) y
# insoft_<fecha>.meta (recuento de filas de las tablas clave, para verificar la restauración).
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-$HOME/insoft-respaldos}
RETENTION=${BACKUP_RETENTION:-14}
KEEP_MIN=${BACKUP_KEEP_MIN:-3}
CONTAINER=${BACKUP_CONTAINER:-insoft-db}
IMAGE=${BACKUP_IMAGE:-pgvector/pgvector:pg16}
MODE=${BACKUP_MODE:-container}
TABLAS=(users courses topics subtopics questions question_answers ai_queries)

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%d_%H%M%S)
OUT="$BACKUP_DIR/insoft_${STAMP}.dump"
META="$BACKUP_DIR/insoft_${STAMP}.meta"

# ── ejecución de herramientas PostgreSQL según el modo ─────────────────────────
pgtool() {  # pgtool <binario> [args…]; stdin/stdout se pasan tal cual
  if [ "$MODE" = "direct" ]; then
    docker run --rm -i --network host \
      -e PGHOST -e PGPORT -e PGUSER -e PGDATABASE -e PGPASSWORD -e PGSSLMODE \
      "$IMAGE" "$@"
  else
    docker exec -i \
      -e PGUSER="$(printf '%s' "${POSTGRES_USER:-oftallearn}")" \
      -e PGDATABASE="${POSTGRES_DB:-oftallearn}" \
      "$CONTAINER" "$@"
  fi
}

if [ "$MODE" = "direct" ]; then
  : "${PGHOST:?define PGHOST (cadena directa)}" "${PGDATABASE:?define PGDATABASE}" "${PGUSER:?define PGUSER}"
  : "${PGPASSWORD:?define PGPASSWORD}"
  export PGPORT="${PGPORT:-5432}" PGSSLMODE="${PGSSLMODE:-require}"
  echo "[backup] modo directo → host ${PGHOST:0:2}***${PGHOST: -2} base ${PGDATABASE}"
else
  echo "[backup] modo contenedor → $CONTAINER base ${POSTGRES_DB:-oftallearn}"
fi

# Si algo falla a mitad (también dentro de pgtool), no debe quedar un respaldo
# incompleto con apariencia válida: la salida borra los archivos si COMPLETO no es 1.
COMPLETO=0
limpiar_incompleto() {
  if [ "$COMPLETO" -ne 1 ]; then
    rm -f "$OUT" "$META"
    echo "[backup] ERROR: respaldo incompleto eliminado" >&2
  fi
}
trap limpiar_incompleto EXIT

# 1) volcado (formato custom: restaurable con pg_restore, comprimido)
pgtool pg_dump -Fc --no-owner --no-privileges > "$OUT"

# 2) integridad: el índice (TOC) debe ser legible
pgtool pg_restore --list < "$OUT" >/dev/null || { echo "[backup] FALLA integridad: $OUT"; rm -f "$OUT"; exit 1; }

# 3) recuento de filas de tablas clave (para verificar la restauración)
{
  for t in "${TABLAS[@]}"; do
    n=$(pgtool psql -tAX -c "SELECT count(*) FROM ${t}" 2>/dev/null || echo "NA")
    echo "${t}=${n}"
  done
} > "$META"

COMPLETO=1
echo "[backup] OK: $OUT ($(du -h "$OUT" | cut -f1)) recuento: $META"

# 4) retención: borra los más viejos que RETENTION días, pero nunca los KEEP_MIN más recientes
mapfile -t TODOS < <(ls -1t "$BACKUP_DIR"/insoft_*.dump 2>/dev/null || true)
for ((i = KEEP_MIN; i < ${#TODOS[@]}; i++)); do
  f=${TODOS[$i]}
  if [ -n "$(find "$f" -mtime "+${RETENTION}" -print 2>/dev/null)" ]; then
    rm -f "$f" "${f%.dump}.meta"
    echo "[backup] retención: borrado $(basename "$f")"
  fi
done
echo "[backup] respaldos conservados: $(ls -1 "$BACKUP_DIR"/insoft_*.dump 2>/dev/null | wc -l)"
