# INSOFT

**Sistema web de apoyo al aprendizaje de Oftalmología.**

INSOFT es una plataforma educativa con contenido académico oficial de Oftalmología,
dos roles de usuario (estudiante y profesor), cursos con acceso mediante código y
seguimiento del progreso del estudiante.

## Arquitectura

```text
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│ React + Vite      │ ───> │ FastAPI (REST)    │ ───> │ PostgreSQL        │
│ Frontend :3000    │      │ Backend :8000     │      │ Base de datos     │
└───────────────────┘      └───────────────────┘      └───────────────────┘
```

- **Frontend:** React, Vite, React Router, Tailwind CSS, `@react-oauth/google`.
- **Backend:** Python, FastAPI, SQLAlchemy, JWT, verificación de Google OAuth en servidor.
- **Base de datos:** PostgreSQL.
- **Contenedores:** Docker Compose.

## Estructura del proyecto

```text
├── frontend/                 # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/       # Componentes reutilizables
│   │   ├── hooks/            # AuthContext (useAuth)
│   │   ├── pages/            # Landing, dashboards, curso, subtema…
│   │   ├── services/         # Cliente HTTP de la API
│   │   └── App.jsx           # Rutas
│   └── Dockerfile
│
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── api/routes/       # auth, users, courses, content, progress
│   │   ├── auth/             # Google OAuth, JWT, dependencias de autorización
│   │   ├── core/             # Configuración (variables de entorno)
│   │   ├── database/         # Engine y sesión SQLAlchemy
│   │   ├── models/           # users, courses, memberships, topics, subtopics…
│   │   ├── repositories/     # Acceso a datos
│   │   ├── schemas/          # Esquemas Pydantic
│   │   ├── seed/             # Contenido oficial de Oftalmología
│   │   ├── services/         # Lógica de negocio
│   │   └── main.py
│   ├── tests/                # Tests de humo (TestClient + SQLite)
│   └── Dockerfile
│
├── docker-compose.yml
└── .env.example
```

> **¿Quieres probar la aplicación paso a paso?** Consulta la [Guía de pruebas](GUIA_DE_PRUEBAS.md).
> **¿Vas a tocar la interfaz?** Lee antes el [sistema de diseño](DESIGN.md).
> **¿Quieres activar el login con Google?** Consulta la [Guía de Google OAuth](GUIA_GOOGLE_OAUTH.md).

## Puesta en marcha con Docker (recomendado)

1. Copia las variables de entorno y edítalas:

   ```bash
   cp .env.example .env
   ```

2. Configura `GOOGLE_CLIENT_ID` (Google Cloud Console → Credenciales → ID de cliente OAuth,
   tipo "Aplicación web", con `http://localhost:3000` como origen autorizado).

3. Levanta los tres contenedores:

   ```bash
   docker compose up --build
   ```

4. Abre la plataforma:

   - Frontend: http://localhost:3000
   - API (docs Swagger): http://localhost:8000/docs

Al arrancar, el backend crea las tablas, carga el **contenido oficial de Oftalmología**
(8 unidades, 22 subtemas y 66 preguntas de repaso) y el **Curso General de Oftalmología**
automáticamente.

### Rol de profesor

Por defecto todo usuario nuevo es **estudiante**. Para que un correo obtenga el rol de
profesor automáticamente al registrarse, añádelo en `.env`:

```text
TEACHER_EMAILS=profesor@universidad.edu,otro@universidad.edu
```

### Login de desarrollo (sin Google)

Si `DEV_AUTH_ENABLED=true`, la página de inicio muestra un formulario de acceso de
desarrollo (elige correo y rol) para probar la plataforma sin credenciales de Google.
**Desactívalo en producción.**

## Ejecución local sin Docker

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://oftallearn:oftallearn@localhost:5432/oftallearn"
export SECRET_KEY="dev-secret"
export GOOGLE_CLIENT_ID="tu-client-id.apps.googleusercontent.com"
export DEV_AUTH_ENABLED=true
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
echo "VITE_ENABLE_DEV_LOGIN=true" >> .env.local
npm run dev
```

## Tests del backend

Los tests cubren el flujo completo (registro, curso general, progreso, creación de
curso con código, unión por código, listado de estudiantes y reglas de autorización)
usando SQLite y el login de desarrollo:

```bash
cd backend
pip install pytest httpx
python -m pytest tests/ -v
```

## API REST principal

| Método | Endpoint | Descripción | Rol |
|---|---|---|---|
| POST | `/api/auth/google` | Login con Google (ID token) | público |
| POST | `/api/auth/dev` | Login de desarrollo | público* |
| GET | `/api/users/me` | Usuario autenticado | cualquiera |
| GET | `/api/courses` | Mis cursos (con progreso o nº de estudiantes) | cualquiera |
| POST | `/api/courses` | Crear curso (genera código único) | profesor |
| GET | `/api/courses/{id}` | Detalle de un curso | miembro/profesor |
| POST | `/api/courses/join` | Unirse a un curso con código | estudiante |
| GET | `/api/courses/{id}/students` | Estudiantes inscritos | profesor dueño |
| GET | `/api/courses/{id}/topics` | Temas y subtemas del curso | miembro/profesor |
| GET | `/api/topics/{id}/questions?course_id=` | Preguntas de repaso de una unidad | miembro/profesor |
| GET | `/api/subtopics/{id}?course_id=` | Contenido de un subtema | miembro/profesor |
| POST | `/api/progress` | Marcar subtema completado | estudiante |
| GET | `/api/progress` | Progreso en todos mis cursos | estudiante |
| GET | `/api/progress/course?course_id=` | Progreso en un curso | estudiante |
| POST | `/api/ai/ask` | Pregunta al asistente IA (RAG) | miembro/profesor |
| POST | `/api/ai/questions/generate` | Generar preguntas IA (nacen pendientes) | profesor |
| POST | `/api/content/subtopics/{id}/questions` | Crear pregunta manual | profesor |
| GET | `/api/content/subtopics/{id}/questions/bank` | Banco de preguntas del subtema | profesor |
| GET | `/api/content/topics/{id}/questions/summary` | Conteos por subtema | profesor |
| PATCH | `/api/content/questions/{id}` | Editar pregunta propia | profesor autor |
| DELETE | `/api/content/questions/{id}` | Borrar pregunta propia | profesor autor |
| POST | `/api/content/questions/{id}/review` | Aprobar/rechazar pregunta IA | profesor autor |

\* solo si `DEV_AUTH_ENABLED=true`.

## Modelo de datos

```text
users ──────────────┐
                    ├──< course_memberships >── courses ──< course_topics >── topics ──< subtopics ──< questions
users ──< progress (user_id, course_id, subtopic_id, completed)
```

- El **contenido oficial** (`topics`/`subtopics`/`questions`) existe una sola vez y es
  compartido por todos los cursos mediante `course_topics` (sin duplicación). El temario
  vive en `app/seed/seed_content.py` y el banco de preguntas en `app/seed/seed_questions.py`.
- El **Curso General de Oftalmología** tiene `type=GENERAL` y `teacher_id=NULL`;
  todo estudiante nuevo se inscribe automáticamente.
- Los cursos de profesor tienen `type=TEACHER` y un código único `OFT-XXXX`.

## Banco de preguntas y preguntas con IA

Los profesores gestionan las preguntas de evaluación desde el panel de su curso
(sección "Banco de preguntas"), con tres orígenes:

- **Oficial**: importada del compendio vía `POST /api/content/import`. Es de solo
  lectura para todos; solo el importador la actualiza.
- **Docente**: creada a mano por el profesor (enunciado + 4 opciones A-D + correcta +
  explicación opcional). Es `approved` y los estudiantes la ven de inmediato.
- **IA**: generada con `POST /api/ai/questions/generate` a partir del contenido oficial
  indexado (RAG). Nace `pending` y **no se muestra a estudiantes** hasta que el profesor
  la aprueba o la descarta desde la cola de revisión.

Cada pregunta tiene `source` (official/ai/teacher) y `status` (approved/pending/rejected);
los quizzes de estudiantes solo incluyen `approved`, con un tope de
`QUIZ_MAX_QUESTIONS` (muestreo aleatorio si hay más).

Variables de entorno nuevas:

| Variable | Default | Descripción |
|---|---|---|
| `AI_QUESTION_RATE_LIMIT` | `5/hour` | Límite de generaciones IA por profesor y hora |
| `AI_QUESTION_MAX_ATTEMPTS` | `2` | Intentos del LLM por solicitud |
| `QUIZ_MAX_QUESTIONS` | `10` | Tope de preguntas por quiz |

## Seguridad

- El ID token de Google se verifica criptográficamente en el backend.
- Las sesiones usan JWT firmados con `SECRET_KEY`.
- Toda la autorización (roles, membresías, propiedad de cursos) se valida en el backend.
- El contenido oficial es de solo lectura para los profesores; las preguntas propias del
  banco docente sí pueden crearse, editarse y borrarse por su autor.

## Alcance de esta versión

Incluye el asistente conversacional basado en RAG (`/api/ai/ask`, con OpenRouter o
Gemini como proveedor, embeddings locales multilingües e indexación por chunks), el
banco de preguntas del profesor y la generación de preguntas IA con revisión. La
vista 3D y el contenido multimedia se encuentran en desarrollo.
