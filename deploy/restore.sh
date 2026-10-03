#!/usr/bin/env bash
# Restauración de un respaldo de INSOFT (pg_dump -Fc) en la BD del stack.
#
# Uso:   ./restore.sh /ruta/a/insoft_20261003.dump
#
# Qué hace:
#   1. Verifica el hash si existe un .sha256 junto al archivo.
#   2. Renombra la BD actual (respaldo de emergencia) y crea una BD vacía.
#   3. Restaura el dump con pg_restore.
#   4. Imprime los conteos restaurados para comparar con backup.sh.
#
# La restauración NO borra la BD previa: queda como "<DB>_pre_restore_<fecha>"
# por si hay que volver atrás (ver runbook, sección "Restaurar un respaldo").
set -eu

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  echo "Uso: $0 /ruta/a/insoft_YYYYMMDD_HHMMSS.dump" >&2
  exit 1
fi

COMPOSE_CMD="${COMPOSE_CMD:-docker compose -f docker-compose.prod.yml --env-file .env.prod}"
PGUSER="${POSTGRES_USER:-oftallearn}"
PGDB="${POSTGRES_DB:-oftallearn}"

# 1) Verificación de integridad
if [ -f "$FILE.sha256" ]; then
  echo "[restore] verificando sha256 …"
  cd "$(dirname "$FILE")" && sha256sum -c "$(basename "$FILE").sha256"
  cd - >/dev/null
else
  echo "[restore] AVISO: no hay archivo .sha256 para verificar $FILE"
fi

echo "[restore] $(date '+%F %T') restaurando $(basename "$FILE") en la BD '$PGDB' …"

# 2) BD de emergencia con el estado actual + BD limpia destino
EMERGENCY="${PGDB}_pre_restore_$(date +%Y%m%d_%H%M%S)"
$COMPOSE_CMD exec -T db psql -U "$PGUSER" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$PGDB' AND pid <> pg_backend_pid();
ALTER DATABASE "$PGDB" RENAME TO "$EMERGENCY";
CREATE DATABASE "$PGDB" OWNER "$PGUSER";
SQL

# 3) Restauración (el dump se pasa por stdin: vive en el host, no en el contenedor)
set +e
$COMPOSE_CMD exec -T db pg_restore -U "$PGUSER" -d "$PGDB" --no-owner --role="$PGUSER" < "$FILE"
rc=$?
set -e
if [ "$rc" = "0" ]; then
  echo "[restore] pg_restore OK."
else
  echo "[restore] pg_restore terminó con código $rc (revisa las advertencias arriba)."
  exit 1
fi

# 4) Conteos para verificación
echo "[restore] conteos restaurados:"
$COMPOSE_CMD exec -T db psql -U "$PGUSER" -d "$PGDB" -t -A <<'SQL'
SELECT 'usuarios: ' || count(*) FROM users;
SELECT 'unidades: ' || count(*) FROM topics;
SELECT 'subtemas: ' || count(*) FROM subtopics;
SELECT 'preguntas oficiales aprobadas: ' || count(*) FROM questions WHERE source='official' AND status='approved';
SELECT 'respuestas de quiz: ' || count(*) FROM question_answers;
SQL

echo "[restore] $(date '+%F %T') restauración terminada. La BD previa quedó como '$EMERGENCY'."
