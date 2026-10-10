#!/bin/bash
# Respaldo de la base del compose (PC) via pg_dump + retención configurable.
#
# Solo LECTURA de la base real: pg_dump no bloquea ni borra datos.
#
# Uso:
#   bash backend/scripts/backup_db.sh                       # normal (retención 7)
#   BACKUP_RETENTION=14 bash backend/scripts/backup_db.sh   # retención 14 días
#   BACKUP_DIR=/ruta/a/disco-externo bash backend/scripts/backup_db.sh
#
# Variables (todas opcionales):
#   BACKUP_DIR       (default ./backups)
#   BACKUP_CONTAINER (default insoft-db)
#   POSTGRES_DB      (default oftallearn)
#   POSTGRES_USER    (default oftallearn)
#   BACKUP_RETENTION (default 7 días; los .dump más viejos se eliminan)
#
# Programación (cron del PC): cosa nocturna a las 03:00
#   crontab -e
#   0 3 * * * /ruta/al/repo/backend/scripts/backup_db.sh >> /ruta/al/repo/backups/backup.log 2>&1
#
# Restauración (documentada en PASO_A_PASO_STAGING.md):
#   cat dump.file | docker exec -i insoft-db pg_restore -U oftallearn -d oftallearn --clean --if-exists
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-./backups}
CONTAINER=${BACKUP_CONTAINER:-insoft-db}
DB=${POSTGRES_DB:-oftallearn}
USER=${POSTGRES_USER:-oftallearn}
RETENTION=${BACKUP_RETENTION:-7}

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
OUT="$BACKUP_DIR/insoft_${STAMP}.dump"

echo "[backup] dumping $DB desde contenedor $CONTAINER → $OUT"
docker exec "$CONTAINER" pg_dump -U "$USER" -d "$DB" -Fc --no-owner --no-privileges > "$OUT"

SIZE=$(du -h "$OUT" | cut -f1)
echo "[backup] OK: $OUT ($SIZE)"

# Retención: elimina respaldos más viejos que BACKUP_RETENTION días
echo "[backup] limpieza: dumps > ${RETENTION} días"
find "$BACKUP_DIR" -name 'insoft_*.dump' -type f -mtime "+${RETENTION}" -print -delete \
  | sed 's/^/[backup] borrado /'

# Verificación rápida de integridad: pg_restore --list lee el TOC
docker exec -i "$CONTAINER" pg_restore --list < "$OUT" >/dev/null \
  && echo "[backup] integridad OK (TOC legible)" || { echo "[backup] FALLA integridad: $OUT inválido"; exit 1; }
