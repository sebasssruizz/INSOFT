#!/usr/bin/env bash
# Prepara el ensayo local tipo Neon: genera contraseñas y certificados de PRUEBA
# en una carpeta FUERA del repositorio (por defecto ~/Documentos/INSOFT-evidencias/ensayo-run),
# con permisos 700/600. Nada de lo generado se versiona.
#
#   bash deploy/ensayo/preparar.sh          # crea la carpeta de ejecución
#   bash deploy/ensayo/limpiar.sh           # detiene y borra contenedores y secretos
set -euo pipefail

RUN=${ENSAYO_RUN:-$HOME/Documentos/INSOFT-evidencias/ensayo-run}
umask 077
mkdir -p "$RUN/certs" "$RUN/pgbouncer"
chmod 700 "$RUN" "$RUN/certs" "$RUN/pgbouncer"

PW=$(openssl rand -hex 16)
SK=$(openssl rand -hex 32)

# ── variables de compose (interpolación) ───────────────────────────────────────
cat > "$RUN/compose.env" <<EOF
ENSAYO_RUN=$RUN
ENSAYO_PG_PASSWORD=$PW
EOF

# ── variables del backend (equivalentes a producción: SSL, sin dev auth) ──────
cat > "$RUN/backend.env" <<EOF
DATABASE_URL=postgresql+psycopg2://ensayo:$PW@tmp-ensayo-pgbouncer:6432/ensayo?sslmode=require
DATABASE_URL_DDL=postgresql+psycopg2://ensayo:$PW@tmp-ensayo-pg:5432/ensayo?sslmode=require
DATABASE_SSL=true
SECRET_KEY=$SK
DEV_AUTH_ENABLED=false
DOCS_ENABLED=false
TEACHER_EMAILS=
BACKEND_CORS_ORIGINS=http://127.0.0.1:4173
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-ensayo-falsa-no-es-real
EMBEDDINGS_BACKEND=onnx
EMBEDDINGS_LOCAL_ONLY=true
FASTEMBED_CACHE_PATH=/app/model-cache
HF_HOME=/app/model-cache/hf
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
PYTHONDONTWRITEBYTECODE=1
EOF

# ── pgbouncer: usuario en texto plano (solo ensayo; la conexión va cifrada) ───
printf '"ensayo" "%s"\n' "$PW" > "$RUN/pgbouncer/userlist.txt"
chmod 600 "$RUN/pgbouncer/userlist.txt"

# ── certificados: una CA de prueba y dos hojas (Postgres/pgbouncer y openrouter.ai)
cd "$RUN/certs"
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.pem -days 3 \
  -subj "/CN=INSOFT ensayo CA (no es real)" >/dev/null 2>&1

hoja() {  # hoja <nombre> <CN> <SAN>
  printf 'subjectAltName=%s\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n' "$3" > "$1.ext"
  openssl req -newkey rsa:2048 -nodes -keyout "$1.key" -out "$1.csr" -subj "/CN=$2" >/dev/null 2>&1
  openssl x509 -req -in "$1.csr" -CA ca.pem -CAkey ca.key -CAcreateserial -out "$1.crt" \
    -days 3 -extfile "$1.ext" >/dev/null 2>&1
  rm -f "$1.csr" "$1.ext"
}
hoja server tmp-ensayo-pg "DNS:tmp-ensayo-pg,DNS:tmp-ensayo-pgbouncer"
hoja openrouter openrouter.ai "DNS:openrouter.ai"
rm -f ca.srl
chmod 600 ./*.key
chmod 644 ./*.crt ca.pem

echo "[ensayo] preparado en $RUN (secretos y certificados de prueba, sin repositorio)"
