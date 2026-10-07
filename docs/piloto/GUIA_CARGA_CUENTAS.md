# GUIA — Carga de cuentas del piloto (T7)

Objetivo: que los estudiantes de la docente entren SOLO con su Google y ya
tengan el curso del piloto, sin crear cuentas a mano ni enviar correos.

## 1. Crear el curso del piloto y su código

1. Entra como docente (la de Claudia) al panel: `/dashboard` → "Mis cursos".
2. Botón **"Añadir curso"** → nombre de la clase (p. ejemplo
   "Oftalmología — Piloto 2026-B"). El sistema genera un **código OFT-XXXX**.
3. Verifica el código en la tarjeta del curso (o `GET /api/courses`).

## 2. Armar el CSV

- Formato (UTF-8, separado por comas):
  ```csv
  email,nombre
  estudiante1@correo.edu,Nombre Apellido
  ```
- Incluye SOLO correos dados por la docente. El script rechaza líneas con
  email inválido y lo reporta (no las aplica).

## 3. Ejecutar (2 pasos: dry-run SIEMPRE primero)

```bash
docker compose exec backend python app/scripts/import_pilot_users.py \
  docs/piloto/plantilla_estudiantes.csv --code OFT-XXXX

# si el reporte del dry-run es el esperado:
docker compose exec backend python app/scripts/import_pilot_users.py \
  docs/piloto/plantilla_estudiantes.csv --code OFT-XXXX --apply
```

- **Idempotente**: si lo corres de nuevo, los usuarios existentes solo
  garantizan membresía (no hay duplicados).
- Al correr dentro del contenedor de backend, la base usada es la del stack
  (`DATABASE_URL` del compose).

## 4. Cómo queda el login de esos estudiantes

- El script crea el usuario con `role=STUDENT` y un `google_id` temporal
  (`pilot-<email>`).
- El **primer login con Google** de ese correo busca el usuario **por EMAIL** y
  le asocia el `google_id` real (servicio `authenticate_with_google`: primero
  busca por google_id; si no existe, busca por email y actualiza el campo).
  Así la pre-carga queda enlazada sin duplicar cuentas y sin inventar
  contraseñas.
- Si el correo NO está en `TEACHER_EMAILS`, el rol queda STUDENT (correcto).

## 5. Qué NO hace (deliberado)

- No envía correos ni invitaciones.
- No borra/actualiza datos de usuarios existentes (solo garantiza membresía).
- No toca roles de usuarios existentes.

## 6. Verificación de punta a punta (checklist docente)

- [ ] Estudiante entra con Google a la URL de producción.
- [ ] Ve el curso del piloto en "Mis cursos" con su progreso en 0.
- [ ] Puede responder el repaso y el asistente le responde.
- [ ] Si hay incidencia de rol/correo mal escrito: corregir el CSV (o crearlo
      a mano vía `/perfil`) y correr de nuevo el script (idempotencia).
