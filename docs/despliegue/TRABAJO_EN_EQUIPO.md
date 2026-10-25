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

El panel muestra comentarios paginados y evaluaciones con sus diez respuestas.
«Descargar todo (CSV)» incluye los dos tipos completos. El código de participante
permite agrupar entregas sin exportar nombres ni correos de las cuentas. El texto
libre puede contener datos personales aportados por usuarios: mantener el archivo
entre investigadores autorizados. Las respuestas «No probado / No aplica» son
vacías/null y deben excluirse del cálculo de valores medios, no contarse como cero.
El instrumento es una adaptación propia, no una puntuación validada de Nielsen.

Para autorizar otra cuenta, actualizar la lista privada y redesplegar el backend.
El frontend comprueba el permiso autenticado; ocultar el menú no sustituye el
control de acceso del API. La ruta anterior `/teacher/feedback` redirige al panel.
