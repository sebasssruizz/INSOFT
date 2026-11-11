#!/usr/bin/env bash
# Levanta el ensayo en el orden correcto y espera a que esté listo.
#   pg (SSL) → pgbouncer (certificados copiados con docker cp) → llm (mock) → backend
set -euo pipefail
RUN=${ENSAYO_RUN:-$HOME/Documentos/INSOFT-evidencias/ensayo-run}
DIR=$(cd "$(dirname "$0")" && pwd)
export ENSAYO_RUN=$RUN
COMPOSE=(docker compose --env-file "$RUN/compose.env" -f "$DIR/docker-compose.ensayo.yml" -p tmp-ensayo)

[ -f "$RUN/compose.env" ] || { echo "[ensayo] ejecuta antes deploy/ensayo/preparar.sh"; exit 1; }

"${COMPOSE[@]}" up -d pg llm
for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' tmp-ensayo-pg 2>/dev/null)" = healthy ] && break
  sleep 2
done
echo "[ensayo] postgres: $(docker inspect -f '{{.State.Health.Status}}' tmp-ensayo-pg)"

"${COMPOSE[@]}" up -d pgbouncer
for _ in $(seq 1 30); do
  docker exec tmp-ensayo-pgbouncer test -e /tmp >/dev/null 2>&1 && break
  sleep 1
done
docker cp "$RUN/certs/server.crt" tmp-ensayo-pgbouncer:/tmp/server.crt
docker cp "$RUN/certs/server.key" tmp-ensayo-pgbouncer:/tmp/server.key
docker cp "$RUN/pgbouncer/userlist.txt" tmp-ensayo-pgbouncer:/tmp/userlist.txt
docker exec -u 0 tmp-ensayo-pgbouncer sh -c \
  'chown 70:70 /tmp/server.crt /tmp/server.key /tmp/userlist.txt && chmod 644 /tmp/server.crt && chmod 600 /tmp/server.key /tmp/userlist.txt && install -o 70 -g 70 -m 600 /tmp/userlist.txt /etc/pgbouncer/userlist.txt'
echo "[ensayo] pgbouncer: certificados y userlist copiados"

"${COMPOSE[@]}" up -d backend
for _ in $(seq 1 90); do
  curl -fsS http://127.0.0.1:8010/ready >/dev/null 2>&1 && { echo "[ensayo] backend listo en http://127.0.0.1:8010"; exit 0; }
  sleep 2
done
echo "[ensayo] el backend no respondió a /ready; revisa: docker logs tmp-ensayo-backend" >&2
exit 1
