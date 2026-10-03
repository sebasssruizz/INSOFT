#!/usr/bin/env bash
# Respaldo de la base de datos de INSOFT (pg_dump -Fc).
#
# Uso:  ./backup.sh                     # usa el compose del directorio actual
#       COMPOSE_FILE=... ./backup.sh    # o el que se indique
#
# Variables (ver .env.prod.example):
#   POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB   (docker-compose.prod.yml)
#   BACKUP_DIR                destino local (default /opt/insoft/backups)
#   BACKUP_RETENTION_DAILY    diarios a conservar (default 7)
#   BACKUP_RETENTION_WEEKLY   semanales a conservar (default 4)
#   RCLONE_REMOTE             remoto rclone (p. ej. spaces:insoft-backups);
#                             vacío = solo local (queda avisado en el log)
#
# Retención: conserva los N diarios más recientes y los M semanales (los
# domingos). Salida: <BACKUP_DIR>/insoft_<fecha>_[semanal.]dump + .sha256.
# Códigos: 0 = OK; 1 = falla del respaldo local; 2 = falla de la copia remota.
set -eu

COMPOSE_CMD="${COMPOSE_CMD:-docker compose -f docker-compose.prod.yml --env-file .env.prod}"
BACKUP_DIR="${BACKUP_DIR:-/opt/insoft/backups}"
RETENTION_DAILY="${BACKUP_RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${BACKUP_RETENTION_WEEKLY:-4}"
DOW=$(date +%u)  # 1..7 (7 = domingo)

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
NAME="insoft_${STAMP}"
if [ "$DOW" = "7" ]; then NAME="${NAME}_semanal"; fi
FILE="$BACKUP_DIR/${NAME}.dump"

echo "[backup] $(date '+%F %T') iniciando respaldo local: $FILE"

$COMPOSE_CMD exec -T db pg_dump -U "${POSTGRES_USER:-oftallearn}" -d "${POSTGRES_DB:-oftallearn}" -Fc > "$FILE"

if [ ! -s "$FILE" ]; then
  echo "[backup] ERROR: el archivo quedó vacío; no se conservará."
  rm -f "$FILE"
  exit 1
fi

HASH=$(sha256sum "$FILE" | cut -d' ' -f1)
echo "$HASH  $(basename "$FILE")" > "$FILE.sha256"
SIZE=$(du -h "$FILE" | cut -f1)
echo "[backup] OK local: $FILE ($SIZE) sha256=$HASH"

# ── Retención local ──────────────────────────────────────────────────────
# Diarios: todos menos los RETENTION_DAILY más recientes (los "_semanal" se
# protegen aparte). Semanales: todos menos los RETENTION_WEEKLY más recientes.
ls -1t "$BACKUP_DIR"/insoft_[0-9]*.dump 2>/dev/null | tail -n +$((RETENTION_DAILY + 1)) | while read -r old; do
  case "$old" in *_semanal.dump) continue ;; esac
  echo "[backup] retención: elimino $(basename "$old")"
  rm -f "$old" "$old.sha256"
done
ls -1t "$BACKUP_DIR"/insoft_*_semanal.dump 2>/dev/null | tail -n +$((RETENTION_WEEKLY + 1)) | while read -r old; do
  echo "[backup] retención semanal: elimino $(basename "$old")"
  rm -f "$old" "$old.sha256"
done

# ── Copia fuera del servidor (opcional) ──────────────────────────────────
if [ -n "${RCLONE_REMOTE:-}" ]; then
  echo "[backup] copiando a $RCLONE_REMOTE …"
  if command -v rclone >/dev/null 2>&1; then
    if rclone copy "$FILE" "$RCLONE_REMOTE/$(date +%Y/%m)" --config "${RCLONE_CONFIG_PATH:-}" && \
       rclone copy "$FILE.sha256" "$RCLONE_REMOTE/$(date +%Y/%m)" --config "${RCLONE_CONFIG_PATH:-}"; then
      echo "[backup] OK remoto: $RCLONE_REMOTE/$(date +%Y/%m)/$(basename "$FILE")"
    else
      echo "[backup] ERROR: la copia remota falló (el respaldo local sí está)."
      exit 2
    fi
  else
    echo "[backup] ERROR: RCLONE_REMOTE está definido pero rclone no está instalado."
    exit 2
  fi
else
  echo "[backup] AVISO: RCLONE_REMOTE no está configurado; el respaldo queda SOLO en este servidor ($BACKUP_DIR). Configure rclone hacia Spaces/B2 para tener una copia fuera."
fi

echo "[backup] $(date '+%F %T') respaldo completo."
