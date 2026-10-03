# RUNBOOK — Despliegue de INSOFT en DigitalOcean (Ubuntu 24.04)

Guía paso a paso para un primer despliegue en producción. Todos los comandos
están listos para copiar (ajusta `tudominio.com` y las rutas si difieren).
Stack resultante: `Caddy (80/443, HTTPS) → Nginx estático + backend FastAPI →
PostgreSQL`, todo en una VM con Docker Compose.

## 1. Crear el droplet

1. Panel de DigitalOcean → **Create → Droplets**.
   - Región: **Nueva York (NYC1/NYC3)** o **Atlanta** (más cerca de Colombia).
   - Imagen: **Ubuntu 24.04 LTS**.
   - Plan: **Basic / Regular CPU 4 vCPU / 8 GB RAM** (el piloto funciona, ver
     métricas en `docs/despliegue/REPORTE.md`; con 4 GB también es viable).
   - Autenticación: **SSH Key** (crea una con `ssh-keygen -t ed25519` si no tienes).
   - Opciones: activa **Backups** (opcional, ~20 % del costo) y IPv6.
   - Cantidad: 1. Nombre: `insoft-prod`.
2. **Alerta de facturación:** Billing → *Spending Alerts* → umbral p. ej. USD 25.

## 2. Endurecer el servidor

Conecta y crea el usuario de servicio (los comandos van como root la primera vez):

```bash
ssh root@IP_DEL_DROPLET

adduser insoft
usermod -aG sudo insoft
rsync --archive --chown=insoft:insoft /root/.ssh /home/insoft
```

SSH solo con llave y UFW:

```bash
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable
```

Actualizaciones automáticas y protección de SSH:

```bash
apt update && apt -y upgrade
apt -y install unattended-upgrades fail2ban
dpkg-reconfigure -plow unattended-upgrades   # deja el default (sí)
systemctl enable --now fail2ban
```

## 3. Instalar Docker (repositorio oficial)

```bash
apt -y install ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt update
apt -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker insoft     # docker sin sudo (cierra sesión y vuelve a entrar)
docker run --rm hello-world   # prueba
```

## 4. Traer el código y crear `.env.prod`

Opción A (deploy key de solo lectura en GitHub/GitLab):

```bash
sudo -iu insoft
ssh-keygen -t ed25519 -f ~/.ssh/id_deploy -N ""
cat ~/.ssh/id_deploy.pub   # pégala en el repo como Deploy Key (solo lectura)
git clone git@github.com:ORG/INSOFT.git /opt/insoft/app    # ajusta la URL
cd /opt/insoft/app
```

Opción B: sube el repo como tarball con `scp` y descomprime en `/opt/insoft/app`.

Configura el entorno de producción:

```bash
cp .env.prod.example .env.prod
nano .env.prod    # edita: DOMAIN, POSTGRES_PASSWORD, SECRET_KEY,
                  # GOOGLE_CLIENT_ID, BACKEND_CORS_ORIGINS, TEACHER_EMAILS
chmod 600 .env.prod
```

Genera los secretos (valores para `.env.prod`):

```bash
openssl rand -hex 16   # → POSTGRES_PASSWORD
openssl rand -hex 32   # → SECRET_KEY
```

## 5. DNS

En tu gestor de dominio crea un registro **A**: `tudominio.com` → IP del droplet
(la de `ssh root@…`). Verifica propagación:

```bash
dig +short tudominio.com   # debe devolver la IP del droplet
```

**Sin dominio todavía:** solo para pruebas puedes usar `DOMAIN=localhost` y
entrar por `https://IP:443` con `curl -k` (certificado interno, el navegador lo
marcará como no confiable). **Para el piloto se necesita dominio real:** el
HTTPS de Let's Encrypt y el login de Google lo requieren.

## 6. Google OAuth

1. Google Cloud Console → **APIs y servicios → Credenciales** → crea/edita el
   **ID de cliente OAuth (tipo Aplicación web)**.
2. **Orígenes JavaScript autorizados:** `https://tudominio.com`
   (la app usa Google Identity Services; no hay redirect de servidor).
3. **URIs de redirección autorizados:** `https://tudominio.com`
   (por documentación de Google para GIS; sin port 8000).
4. Copia el **Client ID** a `.env.prod` en `GOOGLE_CLIENT_ID`
   (el frontend lo recibe como build-arg `VITE_GOOGLE_CLIENT_ID`).
5. Tras desplegar, comprueba el login: entra a `https://tudominio.com`,
   pulsa "Continuar con Google" y verifica que entras como estudiante.

## 7. Primer despliegue

```bash
cd /opt/insoft/app
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

(comptea 5–10 min la primera vez: compila imágenes y descarga el modelo de embeddings)

Comprobar salud:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl -sk https://localhost/health          # {"status":"ok",...} (o sin -k con dominio real)
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f backend
```

**Seed e indexación RAG:** con `SEED_MODE=if_empty` el primer arranque carga
automáticamente las 9 unidades (26 subtemas, 85 preguntas oficiales) porque la
BD está vacía. La indexación RAG se corre una vez:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T backend python -m app.seed.index_content
# → "[index] LISTO: 26 subtopics, ~128 chunks indexados"
```

**Cuenta de la docente (rol profesor):** el mecanismo del proyecto es la
variable `TEACHER_EMAILS` — al registrarse por primera vez con Google, un
correo incluido ahí entra como **profesor** (si ya se registró antes como
estudiante, se le puede cambiar el rol en la BD o borrar su usuario para que
vuelva a registrarse). Deja en `.env.prod`:

```bash
TEACHER_EMAILS=correo.de.claudia@uninunez.edu.co
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d backend   # aplica el cambio
```

Luego ella entra con Google y verá las vistas de profesor (banco de preguntas,
importador, estadísticas). Desde ahí puede usar **"Agregar pregunta"** para
sumar sus preguntas oficiales (p. ej., banco de pterigión).

## 8. Verificación (smoke + manual)

```bash
./deploy/smoke.sh https://tudominio.com
# → 9 comprobaciones: /health, docs cerrado, dev-login deshabilitado,
#   HSTS, nosniff, index.html, fallback SPA, API protegida
```

Checklist en el navegador:
- [ ] Portada carga y el menú navega (rutas de unidad/subtema recargan sin 404).
- [ ] Login con Google funciona y el perfil queda guardado.
- [ ] Abrir un subtema (p. ej. UNIDAD 6) y hacer su quiz.
- [ ] Probar "Modo práctica" en un subtema.
- [ ] Consultar al asistente (widget) algo del contenido nuevo.
- [ ] (Profesor) abrir banco de preguntas y "Agregar pregunta".

## 9. Backups, restauración y monitoreo

**Timer diario (03:00):**

```bash
sudo cp deploy/insoft-backup.service deploy/insoft-backup.timer /etc/systemd/system/
sudo nano /etc/systemd/system/insoft-backup.service   # ajusta User= y WorkingDirectory=
sudo systemctl daemon-reload
sudo systemctl enable --now insoft-backup.timer
systemctl list-timers | grep insoft
```

(Alternativa cron en `deploy/crontab-ejemplo.txt`.)

**Copia fuera del servidor (Spaces/B2):** crea el bucket + access key, instala
`rclone` (`sudo apt -y install rclone`), configura el remoto
(`rclone config` → tipo s3) y pon `RCLONE_REMOTE=spaces:insoft-backups` en
`.env.prod`. Sin esa variable el respaldo queda solo local y el log lo avisa.

**Prueba de restauración en el servidor:**

```bash
./deploy/backup.sh
./deploy/restore.sh /opt/insoft/backups/insoft_XXXX.dump
# compara los conteos impresos con los de la BD actual
```

**Monitoreo gratuito:** UptimeRobot (u similar) → monitor HTTP(S) contra
`https://tudominio.com/health` cada 5 min. **Logs y consumo:**

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f --tail 100
docker stats
```

**Instantáneas:** además de los dumps, activa snapshots periódicos del droplet
en el panel de DigitalOcean (respaldo a nivel de VM).

## 10. Actualizar, revertir y restaurar

**Actualizar la aplicación:**

```bash
cd /opt/insoft/app
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
./deploy/smoke.sh https://tudominio.com
```

**Revertir a una versión anterior:**

```bash
git log --oneline -5          # elige el commit bueno
git checkout COMMIT_BUENO
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

**Restaurar un respaldo** (ver §9: `restore.sh`; la BD previa queda renombrada
como `oftallearn_pre_restore_*` por si hay que volver atrás).

## 11. Errores comunes

| Síntoma | Causa probable | Diagnóstico |
|---|---|---|
| Caddy no emite certificado | DNS no propagado o puerto 80 bloqueado | `dig +short tudominio.com`; `docker compose logs caddy` (busca "obtain"); revisa `ufw` |
| CORS en el navegador | `BACKEND_CORS_ORIGINS` sin `https://tudominio.com` | consola del navegador; corrige `.env.prod` y recrea backend |
| OAuth `redirect_uri_mismatch` | Orígenes/URIs sin el dominio de producción en Google Cloud Console | revisa la credencial OAuth; el Client ID debe coincidir con `GOOGLE_CLIENT_ID` |
| El backend no arranca: "se negó a arrancar" | Guardas de producción (secreto débil, dev-auth, CORS, OAuth) | el mensaje del log lista cada problema exacto |
| `redirect_ip` lentísimo o errores de memoria | RAM agotada | `docker stats`; sube el droplet o baja `WEB_CONCURRENCY` a 1 |
| El asistente responde sin contexto | Chunks sin indexar | corre `python -m app.seed.index_content`; verifica `SELECT count(*) FROM subtopic_chunks;` |
| Límite de peticiones por IP dispara de más | Proxy sin `--proxy-headers` / `FORWARDED_ALLOW_IPS` mal puesto | verifica el `CMD` de la imagen y `FORWARDED_ALLOW_IPS` en `.env.prod` |
| Un reinicio "revirtió" contenido | `SEED_MODE=always` activo | usa `SEED_MODE=if_empty` (producción) y reseed solo con `--force` |

## 12. Costos mensuales estimados (piloto)

| Ítem | Costo |
|---|---|
| Droplet 4 vCPU / 8 GB (~USD 0.071/h) | ~USD 48/mes |
| Instantáneas/backups del droplet (opcional) | ~USD 5/mes |
| Spaces o B2 para respaldos (250 GB / 30 GB) | USD 5 / ~USD 2/mes |
| Dominio | ~USD 10–15/año |
| Caddy/Let's Encrypt, UptimeRobot, embeddings locales | 0 |

Total piloto: **~USD 50–55/mes** (menos con droplet de 4 GB: ~USD 24/mes).
