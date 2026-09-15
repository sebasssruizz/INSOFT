# DESIGN.md — Sistema de diseño de INSOFT

Referencia para mantener coherente la interfaz. Si vas a añadir una pantalla,
léelo antes: casi todo lo que necesitas ya existe como componente o token.

## Registro

INSOFT es **producto**, no campaña: el estudiante viene a estudiar, no a mirar
la interfaz. La regla es familiaridad ganada. La única superficie con licencia
editorial es la portada pública (`LandingPage`).

Escena de uso que decide el tema: *un estudiante de instrumentación quirúrgica
leyendo contenido denso de cirugía oftalmológica en un portátil, entre rotaciones
clínicas, con luz ambiente alta.* De ahí que todas las superficies de trabajo
sean claras. Lo oscuro se reserva a dos momentos: la portada (donde manda el
vídeo) y la vista 3D a pantalla completa.

## Color

Estrategia **restrained**: papel cálido y blanco cargan casi toda la superficie,
los tintes pastel identifican secciones y un único azul profundo marca la acción.

| Escala | Uso |
|---|---|
| `ink-50` | Fondo de la aplicación: papel cálido, no gris de pantalla |
| `ink-100…300` | Bordes, separadores, pistas de progreso, campos en reposo |
| `ink-500…900` | Texto secundario, cuerpo y titulares |
| `blue-900` | **Acción.** Botón primario, navegación activa, progreso, cifras |
| `blue-800` | Enlaces y texto de acento sobre superficie clara |
| `blue-950` | Solo la llamada a la vista 3D y la propia vista 3D |
| `soft-*` | Tintes pastel de superficie: medallones, tarjetas, cabeceras |
| `deep-*` | Contrapartes legibles de los pastel: iconos, cifras, versalitas |
| `correct-*` | Solo acierto en preguntas |
| `wrong-*` | Solo fallo en preguntas y errores destructivos |

Reglas duras del par pastel:

- Los `soft-*` colorean, los `deep-*` escriben. Un medallón lleva
  `bg-soft-mint` con `text-deep-mint`; nunca al revés, y nunca texto largo
  sobre un `deep-*`.
- `blue-700` (#002aff) es azul eléctrico puro: vibra en superficies grandes y
  cansa. Existe en la escala, pero la acción usa `blue-900`.
- Cada unidad del temario tiene su tinte en `lib/curriculum.js`: el estudiante
  reconoce dónde está por el color antes de leer el título.

## Tipografía

Una sola familia auto-alojada (`@fontsource-variable/roboto`), ninguna petición
externa. **Roboto** responde a los dos tokens, `font-display` y `font-sans`: se
conservan porque los usa toda la aplicación, pero hoy apuntan a lo mismo.

La jerarquía no la da el contraste entre dos tipografías, sino el peso, el
tamaño y el interletrado:

- Titulares: 600 dentro de la aplicación, 700 en la portada, con `tracking`
  negativo (−0.02 a −0.025em) según crece el cuerpo.
- Texto corrido: 400.
- `.prose-lesson` es la superficie de lectura académica: 17px/1.75, máx. 68ch.
  Una sans pide un cuerpo algo menor y más interlineado que una serif para
  leerse igual de cómoda.

Dos convenciones:

- `.tabular` en toda cifra que se alinee o cambie (contadores, porcentajes,
  duraciones, códigos), para que no baile al actualizarse.
- `.eyebrow` para la etiqueta corta en versalitas sobre un título.

**Cuidado:** la capa base fija `text-ink-900` en `h1`–`h4`. Todo titular sobre
fondo oscuro (portada, vista 3D) debe declarar `text-white` explícitamente.

## Componentes

Vocabulario único; no crees variantes nuevas sin quitar la vieja.

- `ui/Button` — variantes `primary`, `secondary`, `inverse`, `outline`, `ghost`,
  `danger`; tamaños `sm`/`md`/`lg`. Cubre reposo, hover, foco, activo,
  deshabilitado y cargando. `as={Link}` para navegar conservando el aspecto.
- `ui/Progress` — `ProgressBar` y `ProgressRing`.
- `ui/Counter` — cifra que cuenta al entrar en pantalla, con red de seguridad.
- `ui/Meta` — `Meta` (dato con icono) y `Badge`.
- `course/ContentRail` — índice plegable del curso.
- `course/Quiz` — repaso con retroalimentación inmediata. Acepta `exit`: una
  salida visible durante todo el repaso, para que nadie quede atrapado dentro
  de las preguntas sin poder volver al temario.
- `.skeleton` para cargas; nunca un spinner en medio del contenido.

## Movimiento

- 150–250 ms en interacciones; 500–700 ms solo en barras de progreso.
- Salida exponencial (`ease-out`, `cubic-bezier(0.16, 1, 0.3, 1)`). Sin rebotes.
- **Nunca animes propiedades de layout.** El progreso se anima con `scaleX` y
  `stroke-dashoffset`, no con `width`.
- El contenido no puede depender de JavaScript para ser visible: las entradas
  usan CSS (`animate-rise-in`) y las revelaciones al hacer scroll usan
  `useReveal`, que arranca visible si no hay `IntersectionObserver`.
- `prefers-reduced-motion` está neutralizado globalmente en `index.css`.

## Prohibido

- Franjas de color como `border-left` en tarjetas o listas.
- Degradados sobre texto (`background-clip: text`).
- Glassmorphism decorativo.
- Rejillas de tarjetas idénticas icono + título + texto repetidas sin jerarquía.
- Tarjetas anidadas.
- Modales cuando cabe una solución en línea.
- Rayas em (—) en los textos de interfaz.

## Rendimiento

`three.js` pesa más que el resto de la aplicación junta: entra por `React.lazy`
(`three/LazyEyeScene`, `InteractiveViewPage`) y nunca en el paquete inicial.
Si añades una escena 3D, sigue el mismo patrón y detén el bucle de render
cuando el elemento salga de pantalla o se oculte la pestaña.

## Estilo de código

Comillas simples, sin punto y coma, ancho 100. Si formateas, usa:

```bash
npx prettier --write --single-quote --no-semi --print-width 100 "src/**/*.{js,jsx}"
```

## Adaptación a móvil

**Ninguna pantalla puede desplazarse en horizontal.** `index.css` fija
`overflow-x: hidden` en `html` y `body` y limita `img`, `video`, `svg` y
`canvas` a `max-width: 100%`, pero eso es la red de seguridad, no la solución:
cada pantalla debe caber por sí misma. Lo que sí puede desplazarse a lo ancho
es un bloque concreto dentro de su propio contenedor con `overflow-x-auto`
—la tabla de estudiantes, el ejemplo de Markdown—, nunca la página.

Cuatro reglas aprendidas:

- **`min-w-0` en toda celda de rejilla** que contenga algo que no se encoge
  (un `input[type=file]`, una tabla, código). Por omisión una celda se
  dimensiona al contenido y lo desborda todo.
- **Los paneles `fixed` que viven fuera de pantalla** (cajón de navegación,
  panel de perfil) van dentro de un contenedor con `overflow-hidden`: si no,
  empujan el ancho del documento aunque no se vean.
- **Los adornos que no caben, no se ponen.** El ojo 3D del panel del estudiante
  solo aparece a partir de `xl`; por debajo estorba en vez de decorar.
- **Botones de rótulo largo a ancho completo en móvil** (`w-full sm:w-auto`):
  dentro de un botón de altura fija, el texto plegado se corta.

## Portada

El vídeo del quirófano es el protagonista: se ve a plena opacidad, con un velo
lineal suave más un degradado radial concentrado detrás del texto. Así los
bordes del vídeo quedan limpios y el titular mantiene contraste. No lleva
elementos 3D: compiten con el vídeo.

El registro es **serio, no ilustrado**: sin trazos dibujados a mano, sin
tarjetas de tinte pastel y sin desplazamientos caprichosos de la rejilla. El
temario se presenta como un plan de estudios —celdas separadas por línea fina,
numeradas—, las imágenes van en una rejilla pareja y las secciones se anuncian
con una regla superior más su versalita. Radios contenidos (`rounded-lg`,
`rounded-xl`), nunca `rounded-3xl`.

Bajo el titular van tres cifras del temario que se pueden contar (unidades,
subtemas, preguntas) en una línea reglada. **Nada de porcentajes inventados**
tipo «98 % verificado»: si no sale de `seed_content.py`, no se enseña.
