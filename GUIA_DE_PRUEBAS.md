# Guía de pruebas — INSOFT

Pasos para probar la aplicación de principio a fin (estudiante y profesor).

---

## 0. Requisitos

- **Docker + Docker Compose** (recomendado), o
- Python 3.12+ y Node 20+ para ejecución local sin Docker.

---

## 1. Configuración inicial

```bash
cp .env.example .env
```

El `.env.example` ya viene listo para probar **sin credenciales de Google**
(`DEV_AUTH_ENABLED=true`). En la pantalla de login aparecerá un formulario de
"Acceso de desarrollo" donde eliges correo y rol.

Si quieres probar el login real con Google:
crea un *ID de cliente OAuth* (tipo aplicación web) en
[Google Cloud Console](https://console.cloud.google.com/apis/credentials) con
`http://localhost:3000` como origen autorizado y ponlo en `.env` como
`GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com`.

---

## 2. Arrancar la aplicación

```bash
docker compose up --build
```

Cuando termine:

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |

> El PostgreSQL de Docker se expone en el puerto **5433** de tu máquina para no
> entrar en conflicto con un PostgreSQL local que use el 5432 (puedes cambiarlo
> con `POSTGRES_PORT` en `.env`). Esto no afecta a la aplicación: los
> contenedores se comunican internamente por la red de Docker.

---

## 3. Prueba como ESTUDIANTE

1. Abre http://localhost:3000.
2. Inicia sesión:
   - **Con Google:** botón *Continuar con Google*.
   - **Sin Google (dev):** correo `ana@estudiante.com`, nombre `Ana`, rol **Estudiante**.
3. En el dashboard verás automáticamente el **Curso General de Oftalmología**
   con progreso 0% — no hay que hacer nada para obtenerlo.
4. Pulsa **Continuar estudiando** → verás los 4 temas oficiales
   (Anatomía ocular, Glaucoma, Catarata, Patologías de la retina).
5. Abre un subtema, por ejemplo **Globo ocular**, y lee el contenido.
6. Pulsa **Marcar como completado**.
7. Vuelve al curso o al dashboard: el progreso se habrá actualizado
   (1 de 14 subtemas ≈ 7%).

---

## 4. Prueba como PROFESOR

1. Cierra sesión (o abre una ventana de incógnito en http://localhost:3000).
2. Inicia sesión con otra cuenta:
   - **Dev:** correo `prof@oftallearn.com`, nombre `Dr. Pérez`, rol **Profesor**.
   - **Con Google:** añade antes tu correo a `TEACHER_EMAILS` en `.env` y
     reinicia el backend.
3. En el dashboard del profesor pulsa **Crear curso**:
   - Nombre: `Oftalmología - Grupo A`
   - Descripción: `Curso de Oftalmología para estudiantes del grupo A`
4. El curso aparece con un **código único** tipo `OFT-A72K`. Pulsa **Copiar**.

---

## 5. Unión del estudiante por código

1. Vuelve a la sesión del **estudiante**.
2. En el dashboard, en **Unirse a un curso**, pega el código y pulsa **Unirse**.
3. El curso `Oftalmología - Grupo A` aparece junto al Curso General.
4. Comprueba los casos de error:
   - Unirse **dos veces** al mismo código → mensaje "Ya perteneces a este curso".
   - Código inexistente (`OFT-ZZZZ`) → "No existe ningún curso con ese código".

---

## 6. El profesor ve a sus estudiantes

1. En la sesión del **profesor**, pulsa **Ver curso** en `Oftalmología - Grupo A`.
2. Verás el código del curso y la tabla de **estudiantes inscritos**
   (Ana García — ana@estudiante.com).
3. Desde **Ver contenido del curso** puedes consultar los temas oficiales,
   pero **no editarlos** (no existe esa funcionalidad para profesores).

---

## 7. Probar la API directamente (opcional)

Abre http://localhost:8000/docs (Swagger UI) o usa curl:

```bash
# Login de desarrollo (devuelve un JWT)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/dev \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@estudiante.com","name":"Ana","role":"STUDENT"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Mis cursos
curl -s http://localhost:8000/api/courses -H "Authorization: Bearer $TOKEN"

# Temas del curso 1
curl -s http://localhost:8000/api/courses/1/topics -H "Authorization: Bearer $TOKEN"

# Marcar subtema 1 como completado
curl -s -X POST http://localhost:8000/api/progress \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"course_id":1,"subtopic_id":1,"completed":true}'
```

Comprobaciones de seguridad rápidas:

- Sin token → `401`.
- Estudiante haciendo `POST /api/courses` → `403`.
- Profesor haciendo `POST /api/courses/join` → `403`.
- Profesor consultando `/api/courses/{id}/students` de un curso ajeno → `403`.

---

## 8. Tests automatizados del backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest httpx
python -m pytest tests/ -v
```

Cubre: registro, acceso automático al Curso General, contenido, progreso,
creación de curso con código único, unión por código, listado de estudiantes
y reglas de autorización.

---

## 9. Solución de problemas

| Problema | Solución |
|---|---|
| `port 5432 already in use` | Ya está resuelto: el `db` usa el puerto 5433 del host por defecto (`POSTGRES_PORT` en `.env`) |
| `could not translate host name "db"` | El contenedor de la base de datos no arrancó. Limpia y reconstruye: `docker compose down -v && docker compose up --build` |
| El frontend no muestra el botón de Google | Falta `GOOGLE_CLIENT_ID` en `.env`; reconstruye con `docker compose up --build` |
| Login de desarrollo no aparece | Asegúrate de `DEV_AUTH_ENABLED=true` y reconstruye el frontend |
| Quiero empezar con la base de datos limpia | `docker compose down -v && docker compose up --build` |

## 10. Probar "Agregar preguntas" como docente (local)

1. En `.env` (raíz) define quién es docente y activa el login de desarrollo:
   `TEACHER_EMAILS=profesora@correo.com` (la app compara minúsculas) y `DEV_AUTH_ENABLED=true`.
   Luego `docker compose up --build` (recomendado `docker compose down -v` si cambiaste TEACHER_EMAILS
   y el usuario ya existía: el rol solo se adjudica al crear la cuenta).
2. Frontend local: `cd frontend && npm run dev` (puerto 5173; la API de desarrollo apunta a `http://localhost:8000`).
3. En `/login`, accede con la tarjeta "Modo de desarrollo": correo DESDE el paso 1
   (`profesora@correo.com`) y rol "teacher".
   
   Nota: si ya existía el usuario con otro rol, ábrelo en `/perfil` y cambia el rol a "teacher"
   (autogestión), o borra la fila en la base local.
4. Verifica el rol: en `/dashboard` debe verse el panel con "Mis cursos · Añadir curso" y
   `GET http://localhost:8000/api/auth/me` debe devolver `"role": "TEACHER"`.
5. Entra a la tarjeta del curso en `Mis cursos` (ruta `/teacher/courses/{id}`): arriba verás el
   botón **Agregar preguntas**; abre el asistente:
   - Elige **Unidad** y luego **Subtema** (el select de subtema se desbloquea).
   - Escribe el enunciado, las 4 opciones **A–D** y marca la correcta (clic en la letra).
   - Explicación opcional.
   - **Guardar y agregar otra** conserva unidad y subtema, limpia el resto, muestra
     "Pregunta guardada…" y devuelve el foco al enunciado.
   - **Guardar y salir** guarda y cierra; las preguntas nuevas aparecen en el banco abajo.
   - El botón es visible SOLO con rol `TEACHER` (la página exige el rol; un estudiante
     ve su `/dashboard` de estudiante, no esta ruta).
