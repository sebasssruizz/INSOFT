# Respaldos de la base de datos

Scripts: `backend/scripts/backup_db.sh` (respaldo) y `backend/scripts/verificar_respaldo.sh`
(comprueba que se restaura). Ambos usan contenedores; el host no necesita herramientas de PostgreSQL.

## Respaldo

Dos modos de conexión:

| Modo | Cuándo | Cómo |
|---|---|---|
| `container` (por defecto) | PC con el compose | `pg_dump` dentro de `insoft-db`. No hay contraseña en la línea de órdenes. |
| `direct` | Base con cadena directa (p. ej. Neon) | `BACKUP_MODE=direct` y `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE`, `PGPASSWORD`, `PGSSLMODE`. Usa la URL **directa** (sin `-pooler`). La contraseña va en variable de entorno, no en argumentos. |

```bash
# PC (compose)
BACKUP_DIR=$HOME/insoft-respaldos bash backend/scripts/backup_db.sh

# Base con cadena directa (variables exportadas desde tu gestor de secretos, no en el repo)
BACKUP_MODE=direct PGHOST=… PGPORT=5432 PGUSER=… PGDATABASE=… PGPASSWORD=… PGSSLMODE=require \
  bash backend/scripts/backup_db.sh
```

Cada ejecución crea dos archivos:

- `insoft_<UTC>.dump`: volcado en formato custom (comprimido, restaurable con `pg_restore`).
- `insoft_<UTC>.meta`: recuento de filas de las tablas clave, para verificar la restauración.

Garantías del script:

- **Solo lectura** sobre la base. No bloquea ni borra datos.
- Si `pg_dump` falla, **no queda ningún archivo** (ni vacío ni parcial): se borra en la salida.
- Comprueba el índice del volcado (`pg_restore --list`) antes de darlo por bueno.
- Carpeta con permisos `700`.

## Retención

- `BACKUP_RETENTION` (por defecto **14 días**): los respaldos más viejos se borran.
- `BACKUP_KEEP_MIN` (por defecto **3**): nunca se borran los 3 más recientes, aunque sean viejos.

Verificado: con 5 respaldos de 30 días y uno nuevo, se borran los 5 viejos y se conservan 3.

## Verificar que se puede restaurar

```bash
bash backend/scripts/verificar_respaldo.sh ~/insoft-respaldos/insoft_<fecha>.dump
```

Arranca un contenedor `pgvector` **sin puertos publicados y sin volumen**, restaura el `.dump` en
una base temporal (`tmp_restauracion_desech`), compara los recuentos con el `.meta` y destruye el
contenedor. Sale con código 1 si algún recuento no coincide.

Comprobado: el respaldo de prueba **PASA**; un recuento alterado a propósito **FALLA** (exit 1).

**Nunca** restaures sobre la base real con este script. Para restaurar de verdad hay que hacerlo
a mano, con una base nueva y tras parar la aplicación:

```bash
docker exec -i insoft-db pg_restore -U oftallearn -d <base_nueva> --no-owner --no-privileges < insoft_<fecha>.dump
```

## Programación (NO instalada)

Ejemplo de **cron** (PC, cada día a las 03:00):

```cron
0 3 * * * BACKUP_DIR=$HOME/insoft-respaldos /ruta/al/repo/backend/scripts/backup_db.sh >> $HOME/insoft-respaldos/backup.log 2>&1
```

Ejemplo de **systemd** de usuario (no instalado). Archivos
`~/.config/systemd/user/insoft-respaldo.service` y `insoft-respaldo.timer`:

```ini
# insoft-respaldo.service
[Unit]
Description=Respaldo diario de la base de INSOFT

[Service]
Type=oneshot
Environment=BACKUP_DIR=%h/insoft-respaldos
ExecStart=/ruta/al/repo/backend/scripts/backup_db.sh
```

```ini
# insoft-respaldo.timer
[Unit]
Description=Respaldo diario de INSOFT

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Activación (cuando se decida): `systemctl --user enable --now insoft-respaldo.timer`.

## Límites

- El respaldo no sustituye a la copia del proveedor (Neon ofrece sus propios mecanismos según el plan; verificar en su documentación antes de confiar solo en ellos).
- Un respaldo del PC se pierde si se pierde el PC: copiar `BACKUP_DIR` a un disco externo o a otro equipo.
- El `.dump` contiene datos personales de estudiantes: tratarlo como dato sensible (permisos, cifrado si sale del PC).
