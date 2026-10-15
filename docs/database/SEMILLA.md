# Contenido oficial al arrancar (`SEED_MODE`)

Al arrancar, el backend aplica el contenido oficial (8 unidades, subtemas y preguntas
oficiales) y asegura el Curso General. Código: `backend/app/seed/seed_content.py`
(`seed_official_content`). Variable: `SEED_MODE`.

## Modos

| Modo | Qué hace | Cuándo |
|---|---|---|
| `always` | Reescribe las unidades oficiales y **borra subtemas que no estén en la semilla** (con su progreso). | Solo desarrollo. Es el valor **automático** cuando `DEV_AUTH_ENABLED=true`. |
| `if_empty` | Crea **únicamente** las unidades oficiales cuyo nombre no existe. No actualiza ni borra nada existente. | **Valor por defecto fuera de desarrollo** (`DEV_AUTH_ENABLED=false`). |
| `off` | No toca el contenido al arrancar. | Cuando el contenido se gestiona solo por importación. |

Un valor distinto de estos tres impide arrancar (`SEED_MODE` inválido).

## Por qué

En la versión anterior el arranque **siempre** sincronizaba la semilla, y eso podía:

- sobrescribir el texto de un subtema editado o importado;
- borrar subtemas que no estuvieran en la semilla, junto con su progreso.

Con `if_empty`, un reinicio ya no toca nada existente. Caso cubierto: una unidad importada
por la docente que ocupa el número de una oficial no se sobrescribe, porque la comparación
es **por nombre**, no por posición (`match_by_order=False`).

## Qué no hace `if_empty` (límites conocidos)

- No añade **subtemas nuevos** a una unidad oficial que ya existe. Eso sigue siendo tarea de
  la importación de documentos (`POST /api/content/import`, que nunca borra).
- No corrige texto oficial ya modificado. Si la docente quiere volver a la versión oficial,
  debe hacerlo a mano o con una importación explícita.

## Verificación

`backend/tests/test_semilla_segura.py` (9 pruebas, SQLite desechable):

- primer arranque siembra las 8 unidades;
- un reinicio no pisa contenido editado ni unidades importadas;
- una unidad importada con el mismo número de orden no se sobrescribe;
- si falta una unidad oficial, `if_empty` la agrega;
- `always` restaura la semilla y borra sobrantes (comportamiento de desarrollo);
- `off` no toca nada;
- el valor por defecto depende de `DEV_AUTH_ENABLED`; un valor inválido se rechaza.

## Operación

- Producción / Neon / PC de pruebas (`DEV_AUTH_ENABLED=false`): no definir `SEED_MODE`
  (queda `if_empty`) o fijarlo explícitamente en `if_empty`.
- Desarrollo local: `DEV_AUTH_ENABLED=true` → `always`, como antes.
