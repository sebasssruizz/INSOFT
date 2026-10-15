#!/usr/bin/env bash
# Detiene y elimina el ensayo: contenedores tmp-ensayo-*, red y secretos generados.
# NO usa -v ni toca volúmenes de otros proyectos (el ensayo no tiene volúmenes con nombre).
set -uo pipefail
RUN=${ENSAYO_RUN:-$HOME/Documentos/INSOFT-evidencias/ensayo-run}
DIR=$(cd "$(dirname "$0")" && pwd)
if [ -f "$RUN/compose.env" ]; then
  docker compose --env-file "$RUN/compose.env" -f "$DIR/docker-compose.ensayo.yml" -p tmp-ensayo down --remove-orphans >/dev/null 2>&1
fi
for c in $(docker ps -a --format '{{.Names}}' | grep '^tmp-ensayo-'); do docker rm -f "$c" >/dev/null 2>&1; done
docker network rm tmp-ensayo-net >/dev/null 2>&1
if [ -d "$RUN" ]; then rm -rf "$RUN"; echo "[ensayo] secretos y certificados eliminados"; fi
echo "[ensayo] contenedores tmp-ensayo-* restantes: $(docker ps -a --format '{{.Names}}' | grep -c '^tmp-ensayo-')"
