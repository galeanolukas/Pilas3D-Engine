# Guía: cómo ordenar `modelos/`

`modelos/` está en `.gitignore`: es **tu biblioteca local** — los
assets no se publican (licencias y peso). Aun así, ordenarla rinde:
el editor descubre `.glb` recursivamente, y encontrar qué se puede
usar de un vistazo ahorra tiempo.

## Regla de oro

**Separar lo que el motor CARGA de lo que EDITA.**

El motor lee `.glb`/`.gltf` (riggeados) y `.obj` (estáticos). Todo lo
demás — `.blend`, `.fbx`, `.c4d`, `.ma`, `.max`, `.lxo`, `.ztl` — es
formato de autoría: no se carga, solo sirve para re-exportar.

## Estructura propuesta

```
modelos/
├── personajes/            # riggeados (.glb con skin)
│   ├── wolf/
│   │   ├── Wolf.glb
│   │   └── texturas/      # imágenes sueltas que usa el .gltf
│   ├── fox/Fox.glb
│   ├── cesium_man/CesiumMan.glb
│   ├── brainstem/BrainStem.glb
│   ├── mousylon/039_Mousylon_Art.glb
│   └── polypug/060_Polypug_Art.glb
├── props/                 # estáticos (.glb/.obj, sin skin)
│   ├── avatar_logo/TheAvatarShow_Logo_Background.glb
│   ├── streetlight/
│   │   ├── Streetlight_LowRes.obj + .mtl
│   │   └── texturas/
│   ├── low_poly_tree/Lowpoly_tree_sample.obj
│   └── moon/Moon 2K.obj + .mtl + Diffuse_2K.png
├── fuentes/               # archivos de autoría, por si hay que
│   │                      # re-exportar: .blend .fbx .obj .c4d...
│   ├── moon/
│   ├── low_poly_tree/
│   └── streetlight/
└── docs/                  # readmes, licencias, pdfs, renders
```

## Reglas concretas

1. **Una carpeta por modelo**, con nombre claro y sin espacios
   (`cesium_man`, no `Supporting Files`). Los espacios funcionan,
   pero complican scripts y consolas.
2. **Preferí `.glb`**: un solo archivo autocontenido (malla +
   texturas + skin + animaciones). Guardá el `.gltf`+`.bin` suelto
   solo si necesitás inspeccionar el JSON.
3. **Formatos por uso**:
   | Qué querés | Formato |
   |---|---|
   | Personaje animado | `.glb` con skin + clips |
   | Prop estático | `.glb` u `.obj`+`.mtl` |
   | Re-exportar/editar en Blender | `.blend`/`.fbx` → carpeta `fuentes/` |
   | Referencia visual | renders/jpgs → `docs/` |
4. **Texturas sueltas** van en `texturas/` dentro de la carpeta del
   modelo (el `.gltf` las referencia por ruta relativa).
5. **Deduplicar**: el wolf trae 6 texturas con nombres tipo
   `Material__wolf_col_tga_diffuse.jpeg` y `..._jpeg.jpg` duplicadas —
   quedate las que el `.gltf` referencia y mové el resto a `fuentes/`.
6. **Documentá la fuente**: un `docs/FUENTES.md` con origen y
   licencia de cada pack (Khronos CC0, Mixamo, Quaternius CC0...).
   Si mañana publicás algo, evitás sustos.

## Bonus: cómo lo ve el editor

`editor_personaje.py` hace `glob('modelos/**/*.glb')` — **solo los
`.glb` aparecen** en la tecla N. Entonces: `.glb` en `personajes/` y
`props/` se cargan solos; los `.obj` estáticos quedan disponibles por
ruta para los ejemplos (`actores.Modelo('modelos/props/moon/Moon 2K.obj')`).

## Migración rápida del estado actual

```
33-gltf-wolf/gltf/          → personajes/wolf/
khronos/*.glb               → personajes/{fox,cesium_man,brainstem}/
Supporting Files/*.glb      → personajes/ (mousylon, polypug, robot)
                              + props/avatar_logo/
                              + docs/README.pdf
SpiderAnimate/              → props/spider/ (obj+mtl+texturas)
Streetlight/{Obj,Fbx,Render}→ props/streetlight/ (obj) + fuentes/ (fbx)
                              + docs/ (renders)
low_poly_tree/*.obj         → props/low_poly_tree/ ; resto → fuentes/
Moon 2K.* (raíz, sueltos)   → props/moon/ (obj+mtl+textures)
                              ; blend/c4d/fbx/ma/max → fuentes/moon/
Textures/*.png              → props/moon/texturas/
```

## Estándar de texturas en pilas3d

Lo que el motor soporta hoy (y cómo conviene armar los modelos):

### `.glb` — formato recomendado

- **Texturas embebidas**: PNG/JPEG dentro del `.glb` via
  `baseColorTexture`. Una por material — cada primitiva muestra **su**
  textura (el motor dibuja un grupo por material, no una textura
  global).
- **Texturas externas**: `.gltf` + `textures/*.png` al lado —
  el loader resuelve `uri` relativa al archivo (así está armado
  `modelos/props/hotdog (Copia 1)/`).
- **`baseColorFactor`**: se hornea como color de vértice y se
  multiplica con la textura (igual que la spec glTF). Un factor
  oscuro + textura = modelo oscuro; si se ve gris, revisá el factor
  al exportar (dejarlo en blanco `[1,1,1,1]` si solo querés la
  textura).
- **Canal de UV**: `TEXCOORD_0`. Si falta, la primitiva dibuja con el
  primer píxel de la textura (color plano del borde) — no da error,
  pero el resultado es "se ve de un solo color".

### Lo que no se lee (por ahora)

- `normalTexture`, `metallicRoughnessTexture`, `emissiveTexture`,
  `occlusionTexture` — se ignoran silenciosamente.
- `alphaMode` BLEND/MASK: se respeta solo el canal alfa de
  `baseColorFactor`/textura para descarte (`alpha < 0.1`), sin
  blending real.
- Múltiples UV sets (`TEXCOORD_1`+), vertex colors `COLOR_0`, KHR_*
  (draco, material variants).

### Reglas prácticas para que "se vean bien"

1. Exportá a `.glb` con **"Pack images"** (embebidas) — una sola
   textura baseColor por material evita el 90% de los problemas.
2. Aplicá transforms y normals en Blender antes de exportar
   (`Ctrl+A` + recalcular normals si se ven caras "huecas").
3. Si un modelo sale todo de un color, casi siempre es: sin UVs,
   textura externa mal referenciada, o `baseColorFactor` oscuro.
4. Para props estáticos con texturas sueltas, `.obj`+`.mtl`+png
   funciona, pero el estándar del motor es `.glb` embebido.

> **Por qué se veían mal antes**: `ModeloGLTF` tomaba la primera
> `baseColorTexture` y la aplicaba a todo el actor. Desde que cada
> material tiene su grupo de render, modelos multi-material como el
> hotdog (salchicha texturizada + outline plano) se ven correctos.

## Estáticos vs animados

| Tipo | Actor | Animación | Textura | Pintado |
|---|---|---|---|---|
| `.obj` | `pilas.actores.Modelo` | no | `imagen=` | `color=` tine |
| `.glb`/`.gltf` | `pilas.actores.ModeloGLTF` | skin por CPU | por material + `imagen=` override | `color=` tine |
| secuencia `.obj` | `pilas.actores.ModeloAnimado` | por cuadros | `imagen=` | `color=` tine |
| bloque Minecraft | `pilas.actores.ModeloJSON` | no | por elemento | `color=` tine |

`pilas.actores.Modelo('x.glb')` **delega automáticamente** a
`ModeloGLTF` — los `.glb` sin esqueleto funcionan como estáticos.

Para saber si un `.glb` es animado:

```python
m = pilas.actores.ModeloGLTF('fox.glb')
m.es_animado      # True si tiene skin (esqueleto)
m.es_estatico     # True si es de partes rígidas (horse, props)
m.animaciones()   # nombres de los clips
```

### Pintar (`color`) y texturizar (`imagen`) valen para todos

- `modelo.color = pilas.colores.rojo` **tiñe** el modelo:
  multiplica los colores de material/vértice (blanco = sin cambio).
- `modelo.imagen = 'x.png'` fuerza **una** textura para todo el
  actor — en `ModeloGLTF` reemplaza las texturas por material.
- `modelo.transparencia = 40` baja el alfa de todos los vértices.
