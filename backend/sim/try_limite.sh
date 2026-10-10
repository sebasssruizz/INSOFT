#!/bin/bash
# Mediciones F2: simula el plan gratis de Render (0.1 CPU / 512 MB; también
# 0.5 CPU para comparar) contra un Postgres desechable (sim-pg, red sim-perf).
#
# Uso: bash try_limite.sh <mem>   (ej. 512m, 640m, 768m)
# Requiere: imagen insoft-backend-sim (EMBEDDINGS_BACKEND=onnx), sim-pg arriba
# y un JWT de estudiante en backend/sim/.token (salida del bootstrap).
set -u
MEM=${1:?uso: try_limite.sh <mem>; ej. 512m}
docker rm -f sim-backend >/dev/null 2>&1
docker run -d --name sim-backend --network sim-perf \
  --memory=$MEM --memory-swap=$MEM --cpus=0.1 \
  -e DATABASE_URL=postgresql+psycopg2://sim:sim@sim-pg:5432/sim \
  -e SECRET_KEY=sim-only-disposable-key-dev-auth-false \
  -e DEV_AUTH_ENABLED=false -e AI_PROVIDER=openrouter \
  -e EMBEDDINGS_BACKEND=onnx \
  -e OMP_NUM_THREADS=1 -e MALLOC_ARENA_MAX=2 \
  -p 5598:8000 insoft-backend-sim >/dev/null

T0=$(date +%s.%N)
for i in $(seq 1 400); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 http://localhost:5598/health 2>/dev/null)
  [ "$CODE" = "200" ] && break
  sleep 0.25
done
T1=$(date +%s.%N)
echo "cold->health: $(echo "$T1-$T0" | bc) s"

T0=$(date +%s.%N)
R=$(curl -s -o /dev/null -w '%{http_code}:%{time_total}' --max-time 240 -X POST \
    http://localhost:5598/api/ai/ask \
    -H "Authorization: Bearer $(cat "$(dirname "$0")/.token" 2>/dev/null)" \
    -H 'Content-Type: application/json' \
    -d '{"question":"prueba de limites de memoria"}')
T1=$(date +%s.%N)
echo "primer /ai/ask: $R (wall $(echo "$T1-$T0" | bc) s)"
echo "estado: $(docker inspect sim-backend --format 'oom={{.State.OOMKilled}} exit={{.State.ExitCode}} status={{.State.Status}}' 2>/dev/null) RAM=$(docker stats --no-stream --format '{{.MemUsage}}' sim-backend 2>/dev/null)"
