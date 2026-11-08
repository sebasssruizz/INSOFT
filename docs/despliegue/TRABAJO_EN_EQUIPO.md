# Publicación desde main y acceso a opiniones

## Para desarrollar desde otro PC

El repositorio es `sebasssruizz/INSOFT`, rama de producción `main`.
Eddy ya dispone de permiso de escritura como colaborador. Antes de editar,
actualizar la copia local sin descartar cambios propios:

```sh
git switch main
git pull --ff-only origin main
```

Si hay cambios locales o divergencia, resolverlos antes; no usar force push ni
reset para quitar los cambios de otra persona. Tras revisar y probar el cambio,
crear el commit con los archivos concretos y ejecutar `git push origin main`.
Los archivos GLB usan Git LFS: instalar Git LFS y ejecutar `git lfs pull` al clonar.
No subir `.env`, claves de Google, conexiones de Neon ni respaldos de la base.

Vercel usa dos proyectos del mismo repositorio:

| Proyecto | Raíz | Rama | Dirección |
|---|---|---|---|
| insoft-web | frontend | main | https://insoft-web.vercel.app |
| insoft-api | backend | main | https://insoft-api.vercel.app |

La integración GitHub de Vercel debe estar autorizada para este repositorio.
Conexión Git no equivale a actualizar inmediatamente: cada push inicia un build,
y solo una publicación READY cambia la versión que ven los usuarios.
Los fallos se revisan en Deployments de Vercel y Actions de GitHub. No publicar
un bundle de CI: la URL de API de los tests es ficticia. Vercel recibe las
variables reales desde la configuración privada de cada proyecto.

Configurar Git LFS en el proyecto web, FastAPI/requirements-onnx para backend y
conservar variables reales solo en Production. No dar a previews de ramas
arbitrarias acceso a la base o secretos de producción. La instalación de la app
GitHub puede requerir confirmación directa del titular. No activar planes de pago
para resolver permisos sin autorización explícita.

## Opiniones y PQRS

Ruta privada `/feedback/review`, opción «Opiniones y PQRS» en el menú.
Permiso independiente del rol de estudiante/profesor, determinado en el backend
por `FEEDBACK_REVIEWER_EMAILS`. Esta lista vive en Vercel, nunca en Git.
No es necesario crear superusuario ni conceder acceso a cursos de otra persona.

El panel muestra comentarios paginados y evaluaciones con sus diez respuestas,
junto con el nombre y correo de la cuenta que realizó cada envío.
«Descargar todo (CSV)» incluye los dos tipos completos y las columnas `nombre`
y `correo`. El código de participante se conserva en el CSV para agrupar entregas.
Los datos del autor se consultan desde su cuenta actual, también para envíos
anteriores; si la cuenta no está disponible, el panel lo indica y el CSV deja
esos campos vacíos. Mantener el archivo entre investigadores autorizados.
Las respuestas «No probado / No aplica» son
vacías/null y deben excluirse del cálculo de valores medios, no contarse como cero.
El instrumento es una adaptación propia, no una puntuación validada de Nielsen.

Para autorizar otra cuenta, actualizar la lista privada y redesplegar el backend.
El frontend comprueba el permiso autenticado; ocultar el menú no sustituye el
control de acceso del API. La ruta anterior `/teacher/feedback` redirige al panel.

### Publicar la información del autor de PQRS

1. Publicar juntos los cambios del backend y frontend en `main`. No se necesita
   una migración de base de datos: los envíos ya están vinculados a sus autores.
2. En Vercel, comprobar que los despliegues de `insoft-api` e `insoft-web`
   correspondientes al commit terminen en `READY`. El frontend debe conservar
   su `VITE_API_URL` de producción apuntando al backend publicado.
3. En `insoft-api`, conservar `FEEDBACK_REVIEWER_EMAILS` en el entorno Production.
   Para añadir una cuenta, agregar su correo a la lista existente, separado por
   comas, y redesplegar el backend. El `.env` local y Docker Compose no configuran
   las variables de Vercel.
4. Iniciar sesión con una cuenta autorizada y abrir `/feedback/review`. Revisar
   nombre y correo tanto en PQRS como en evaluaciones, incluidos envíos anteriores,
   y comprobar las columnas `nombre` y `correo` en la descarga CSV.

El acceso a este panel es independiente del rol docente. `TEACHER_EMAILS`
asigna el rol al crear cuentas; para promover una cuenta existente, ejecutar
`app/scripts/promote_teacher.py --email <correo> --apply` desde `backend` en un
entorno configurado para la base de datos correspondiente. Cambiar el rol en la
base local no cambia la cuenta de producción.
