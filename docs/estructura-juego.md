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

## Personajes y animaciones

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
