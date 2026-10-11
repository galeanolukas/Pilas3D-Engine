# Guía: estructura de un proyecto de juego

Cómo ordenar los archivos para un juego con pilas3d — qué formato
acepta cada subsistema y **dónde tiene que estar** para que el motor
lo encuentre solo.

Todo el árbol de abajo lo crea el scaffolding:

```bash
pilas3d-init mi_juego       # crea mi_juego/ con juego.py + README
```

## El árbol completo

```
mi_juego/
├── juego.py                    # punto de entrada (el main)
├── mapas/                      # mapas del editor (pilas3d-mapas)
│   ├── nivel1.mapa.json        # voxels + actores (tecla G/L/O)
│   └── mundo.terreno.json      # terreno heightmap + material
├── modelos/                    # tus .glb / .gltf / .obj
│   ├── personajes/             # riggeados: skin + clips
│   │   └── heroe/Heroe.glb
│   ├── props/                  # estáticos: árboles, casas, armas
│   │   └── arbol/Arbol.obj + Arbol.mtl + texturas/
│   ├── fuentes/                # .blend/.fbx de autoría (no se cargan)
│   └── docs/                   # readmes, licencias
├── texturas/                   # packs de materiales PBR
│   ├── Pasto_2K/               # archivos sueltos (ambientCG)
│   └── floor_tiles_08_2k.gltf/ # pack .gltf de Poly Haven
│       └── textures/*.jpg
├── sonidos/                    # .wav (efectos, música)
├── fonts/                      # .ttf/.otf extra del proyecto
├── data/
│   ├── hdr/                    # fondos .hdr equirectangulares
│   └── imagenes/               # sprites, pantallas de título
└── juegos/                     # salida del asistente de IA
```

Todo lo de `modelos/`, `texturas/`, `data/hdr/` y `data/fonts/*/` está
en `.gitignore`: son assets locales pesados — no viajan al repo.

## Formatos por subsistema

| Asset | Formato | Dónde lo busca el motor | API |
|---|---|---|---|
| Personaje animado | **`.glb`** con skin + clips | `modelos/` o ruta | `pilas.actores.ModeloGLTF(ruta)` |
| Prop estático | `.glb`, `.gltf`+`.bin`, `.obj`+`.mtl` | idem | `ModeloGLTF` / `pilas.actores.Modelo` |
| Material PBR | JPG/PNG con nombres estándar | `texturas/<pack>/` | `pilas.materiales['pack']` |
| Fondo HDR | **`.hdr`** Radiance equirect (Poly Haven) | `data/hdr/` por nombre | `pilas.actores.Cielo('x.hdr')` |
| Imagen/sprite | `.png`, `.jpg`, `.bmp` | cwd, `data/`, `data/hdr/` | `actor.imagen` / `pilas.imagenes` |
| Fuente | `.ttf`, `.otf`, `.ttc` | `fonts/`, `data/fonts/` | `Texto(fuente='X.ttf')` |
| Sonido | `.wav` (recomendado) | cwd, `data/` | `pilas.sonidos.cargar` |
| Mapa | `.mapa.json` / `.terreno.json` | `mapas/` | `pilas.mapas.cargar` |
| Gamepad USB | cualquiera XInput/DirectInput | automático | `pilas.mandos` |

## Personajes y animaciones

### ¿Sprite 2D o modelo 3D?

| Actor | Cuándo |
|---|---|
| `Cartel` | imagen estática que mira a la cámara (árbol, item) |
| `Animacion` | hoja de cuadros genérica (fuego, explosión, prop) |
| `PersonajeSprite` | **personaje 2D**: fila por dirección, quieto/caminar automático, espejo y estados |
| `PersonajeCapas` | igual + capas apiladas (ropa/cabello) sincronizadas |
| `ModeloGLTF` | personaje 3D riggeado con clips |

`PersonajeSprite` usa la convención LPC: la hoja tiene una fila por
dirección (abajo/izquierda/derecha/arriba) y N cuadros de ciclo:

```python
pj = pilas.actores.PersonajeSprite('heroe.png', columnas=9, filas=4)
pj.aprender(pilas.habilidades.MoverseConElTeclado)

# hojas con un solo lateral: la otra dirección sale espejada
pj2 = pilas.actores.PersonajeSprite('chica.png', columnas=3, filas=3,
    direcciones={'abajo':0, 'izquierda':1, 'arriba':2},
    espejar={'derecha':'izquierda'})

# filas extra de la hoja = estados (ataque, muerte, salto)
pj.agregar_estado('atacar', fila=4, ciclica=False)
pj.agregar_estado('morir', fila=5, quedarse=True)
pj.reproducir_estado('atacar')
```

Ejemplo completo: `ejemplos/personaje_sprite.py`. Las hojas LPC de
OpenGameArt (9x4 o más) encajan en el mismo formato.

#### `.personaje.json` — manifiesto y editor visual

`pilas3d-personaje` es el editor de personajes-sprite: abre la hoja,
muestra el billboard caminando en una mini-escena 3D (WASD lo mueve,
la cámara lo sigue) y deja asignar filas a direcciones/estados con
teclas mientras se ve el resultado. **G** guarda un
`.personaje.json` que trae hoja, grilla, direcciones, espejos,
cuadro quieto, velocidad, tamaño y estados:

```bash
pilas3d-personaje vikingo.png -c 5 -f 2      # desde la hoja
pilas3d-personaje vikingo.personaje.json     # reabrir el manifiesto
```

Y en el juego el personaje se carga ya configurado — el código queda
en una línea:

```python
vik = pilas.actores.PersonajeSprite('vikingo.personaje.json')
```

La hoja se resuelve **relativa a la carpeta del JSON**, así el
personaje viaja como un par `.png` + `.personaje.json` portable.
Los kwargs explícitos (`ancho=`, `velocidad=`...) ganan al
manifiesto. `pj.guardar('nuevo.personaje.json')` escribe uno desde
código.

#### Variantes de color en la misma hoja

Si la hoja repite al personaje en bloques horizontales de N columnas
(por ejemplo 16 columnas = 4 poses × 4 tonos de piel), el manifiesto
declara `variantes` y el ciclo anima solo los `columnas/variantes`
cuadros del bloque activo:

```python
pj = pilas.actores.PersonajeSprite('heroes.personaje.json')
pj.definir_variante(2)            # o pj.variante = 2 — cambio en caliente
pj.variantes                      # 4
```

Ideal para un selector de personajes: mismo arte, mismo manifiesto,
varios colores. En el editor el slot `variante` cicla con ←/→.

#### `PersonajeCapas` — paper-doll (ropa, pelo encima del cuerpo)

`PersonajeCapas` apila varias hojas sincronizadas como un solo
personaje: todas comparten fila, cuadro, variante y espejo del base.
Las capas se resuelven relativas al manifiesto igual que la hoja:

```python
pj = pilas.actores.PersonajeCapas('data/personaje_base.png',
                                  columnas=4, filas=3)
pj.agregar_capa('data/personaje_ropa1.png')
pj.agregar_capa('data/personaje_cabello.png')
pj.quitar_capa()                  # o quitar_capa(0)

# y desde el manifiesto:
#   { "hoja": "base.png", "capas": ["ropa.png", "cabello.png"] }
```

Cada capa puede ser un string (usa la grilla del base) o un dict
`{"hoja": ..., "columnas": ..., "filas": ..., "variantes": ...}` — o
un `.personaje.json` propio, si la prenda tiene otra grilla. En el
editor: **C** agrega capa por el explorador, y **B** sobre un slot
`capa` la quita; **G** las guarda al manifiesto.

### El `.glb` es el formato ideal

Un `.glb` autocontenido trae malla + texturas + esqueleto + clips:

```python
heroe = pilas.actores.ModeloGLTF('modelos/personajes/heroe/Heroe.glb')
print(heroe.animaciones())            # clips que trae el archivo
heroe.animar('02_walk_Armature_0', ciclica=True)
```

- **Una carpeta por modelo** (`modelos/personajes/heroe/`): si es
  `.gltf` suelto, sus texturas van en `texturas/` al lado (el loader
  resuelve `uri` relativas al archivo).
- Los `.blend`/`.fbx` no se cargan — van a `fuentes/` para re-exportar.
- Poses y animaciones del editor: `<modelo>.pose.json` y
  `<modelo>.<nombre>.anim.json` se guardan **junto al `.glb`**
  (teclas G/J/L en `editor_personaje`).
- Ojo: el export a web (`pilas3d-bloques`) **sustituye los modelos
  por primitivas** — glTF es solo del runtime Python.

### Generar un personaje sin modelar

Si no tenés un `.glb` riggeado, el motor fabrica uno low-poly:

```python
from pilas3d.personaje import crear_personaje
crear_personaje('modelos/personajes/heroe.glb', alto=1.8,
                colores={'camisa': (200, 60, 60)})
```

Es un humanoide de cajas con esqueleto de 19 huesos (rigid
skinning) y nombres estándar — `mapear_huesos` lo reconoce, así que
`animacion_procedural` (caminar, correr, saludar...) y
`pilas3d-editor` funcionan directo. En el editor, la tecla **V**
crea uno sin salir. Parámetros: `alto`, `ancho`, `cabeza` (>1 =
chibi) y el dict `colores` (piel/camisa/pantalon/zapatos/ojos/pelo,
0-255).

### Animación por secuencia .obj

`ModeloAnimado` toma una lista de `.obj` como cuadros (técnica
MD2) — útil para morph targets simples exportados de Blender.

## Texturas / materiales

Los packs viven en `texturas/<alias>/`. El detector por nombre de
archivo entiende las tres convenciones grandes:

| Convención | Base | Normal | Rugosidad | AO | Heightmap |
|---|---|---|---|---|---|
| ambientCG | `*_Color` | `*_NormalGL` | `*_Roughness` | `*_AmbientOcclusion` | `*_Displacement` |
| Poliigon | `*_BaseColor` | `*_NormalDX/GL` | `*_Roughness` | `*_AmbientOcclusion` | `*_Displacement` |
| **Poly Haven** | `*_diff` | `*_nor_gl` | `*_rough` | `*_arm`/`*_ao` | `*_disp` |

```python
mat = pilas.materiales['floor_tiles_08_2k.gltf']  # detecta solo
actor.material = mat
actor.imagen = mat.base                            # color difuso
terreno.aplicar_material('floor_tiles_08_2k.gltf') # terreno texturado
terreno.desde_heightmap(mat.heightmap)             # relieve real (si hay disp)
```

El pack `.gltf` de Poly Haven **no hace falta abrirlo**: el motor
baja al subdirectorio `textures/` solo. Si el dir tiene un
subnivel (`Poliigon/.../2K/`), también lo encuentra.

## Fondos HDR

```python
cielo = pilas.actores.Cielo('kloofendal_48d_partly_cloudy_puresky_2k.hdr')
cielo.iluminar_escena()     # dirección del sol + ambiente del mapa
cielo.exposicion = 1.3      # brillo del fondo
```

- Los `.hdr` van en `data/hdr/` — se referencian **solo por nombre**
- Equirectangular 2:1, **2K es el sweet spot** (4K anda, 8K no rinde)
- La primera carga decodifica (~2s en 2K) y deja un `.cache` binario;
  las siguientes son instantáneas
- `iluminar_escena` saca el sol del píxel brillante y tiñe el
  ambiente — los objetos "pertenecen" al fondo, no quedan pegados

Sin `.hdr`, `Cielo('dia')` y `Cielo('estrellas')` son generados, y
`escena.fondo = pilas.colores.celeste` da un fondo plano.

## Escena mínima "gráficamente buena"

```python
import pilas3d
pilas = pilas3d.iniciar()

cielo = pilas.actores.Cielo('kloofendal_48d_partly_cloudy_puresky_2k.hdr')
cielo.iluminar_escena()

terreno = pilas.actores.Terreno(celdas=30, tamano_celda=1.5)
terreno.aplicar_material('Pasto_2K')

heroe = pilas.actores.ModeloGLTF('modelos/personajes/heroe/Heroe.glb')
heroe.animar('walk', ciclica=True)
heroe.aprender(pilas.habilidades.MoverseConElTeclado)

pilas.escena.niebla = (pilas.colores.celeste, 20, 80)   # profundidad
pilas.ejecutar()
```

~15 líneas: cielo HDR real + terreno texturado + personaje animado
+ niebla de profundidad. Ese es el "kit visual" completo del motor.

## Checklist de assets para un juego

- [ ] 1 `.glb` riggeado por personaje (clips idle/walk/run/attack)
- [ ] `.glb`/`.obj` por prop (árbol, piedra, casa, pickup)
- [ ] 1 pack de texturas por superficie (piso, pared, terreno)
- [ ] 1 `.hdr` por ambiente (día, atardecer, noche, interior)
- [ ] `.wav` por efecto + música de fondo
- [ ] 1 `.ttf` pixel/arcade para el HUD
- [ ] `.mapa.json` por nivel (los hace `pilas3d-mapas`)

Ver también: `docs/modelos.md` (detalle de `modelos/`),
`docs/materiales.md`, `docs/terreno.md`, `docs/editor-personaje.md`.
