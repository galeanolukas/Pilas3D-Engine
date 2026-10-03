# Materiales: texturas compuestas (normal, AO, rugosidad)

El shader del motor es Lambert educativo, pero soporta los mapas
que más cambian una escena de un pack de texturas (Poliigon,
ambientCG, Quixel, PolyHaven):

```python
mat = pilas.materiales.desde_carpeta(
    'modelos/Poliigon_GrassPatchyGround_4585/2K')
terreno.material = mat        # detecta base+normal+ao+rugosidad solo
```

O a mano:

```python
mat = pilas.materiales.cargar(
    base='suelo.png', normal='suelo_n.png',
    ao='suelo_ao.png', rugosidad='suelo_r.png')
cubo.material = mat
```

## Qué hace cada mapa

| Slot | Mapa | Efecto | Estado |
|---|---|---|---|
| `base` | BaseColor / Albedo / Diffuse | la textura de color (igual que `actor.imagen`) | ✅ |
| `normal` | Normal | relieve por normal map — por derivadas de pantalla, sin tangentes: sirve para `.obj`, `Terreno` y mallas procedurales | ✅ |
| `ao` | AmbientOcclusion | atenúa la luz ambiente y parte de las puntuales | ✅ |
| `rugosidad` | Roughness | brillo especular (Blinn-Phong) de la luz direccional: liso = brillo fino e intenso, rugoso = casi nada | ✅ |
| `metalico` | Metallic | detectado pero **no se usa** — sin env map el metal no se ve | ⚠️ honesto |
| `heightmap` | Displacement / Height | no va al shader — alimenta `Terreno.desde_heightmap` | ⚠️ offline |

Las prioridades están pensadas así: **normal + AO es el 80% del
salto visual**; roughness agrega brillo; metallic sin environment
map apenas cambia; displacement real necesita tessellation (otro
proyecto).

## Autodetección por nombre (`desde_carpeta`)

Reconoce los nombres típicos de los packs sin parsear el `.mtlx`:

| Slot | Patrones (minúsculas, subcadena) |
|---|---|
| `base` | `basecolor`, `albedo`, `diffuse`, `colormap` |
| `normal` | `normal`, `_nrm` |
| `ao` | `ambientocclusion`, `occlusion`, `_ao` |
| `rugosidad` | `roughness`, `rugosidad`, `rough` |
| `metalico` | `metallic`, `metalness`, `metal` |
| `heightmap` | `displacement`, `heightmap`, `disp`, `bump` |

Solo `.png/.jpg/.jpeg/.bmp` — los `.tiff` (típicos del Displacement
de Poliigon) no los lee pyglet: convertirlos a PNG o usarlos solo
para `desde_heightmap` tras convertir.

## Terreno desde un heightmap

```python
t = pilas.actores.Terreno(celdas=40)
t.material = mat
t.desde_heightmap('montanas.png', altura=6)   # blanco = más alto
```

La luminancia de la imagen se muestrea a la rejilla (`celdas+1`
vértices por lado). Ideal con mapas `Displacement`/`Height`
convertidos a PNG, o con un degradado pintado a mano.

## Límites honestos

- Los mapas extra aplican a los actores con `Actor.dibujar`
  (`Terreno`, `Cubo`, `Plano`, `Modelo`, `Piso`…). `ModeloGLTF`
  dibuja por material propio y **no** usa estos slots todavía.
- El especular es solo de la luz direccional (las puntuales no
  emiten brillo especular — costo por pixel).
- El AO modula la luz, no es SSAO de verdad — es un factor de la
  textura, que es como lo usan los packs de todas formas.
- `normal` necesita UVs correctas — el `Terreno` y el `Plano`
  repiten la textura por celda (`GL_REPEAT`), así que el normal map
  tilea igual que la base: justo lo que se quiere con texturas
  seamless de Poliigon.

## Checklist de assets (resumen)

**Props estáticos** (`.glb` recomendado sobre `.obj` para textura):

- Origen en la base del objeto, +Y arriba, escala en metros
- Un objeto por archivo, triangulado, ≤ 3-5k triángulos
- Una `baseColorTexture` ≤ 1024 PNG
- `modelos/props/<tipo>/` — la carpeta es la categoría del editor

**Texturas seamless para suelos/terreno**: el pack completo en una
carpeta y `desde_carpeta` hace el resto. 1K-2K alcanza para el
motor; 4K es desperdicio de VRAM.

**Modelos animados** (`.glb`): ver `docs/modelos-rendimiento.md` —
una skin, LINEAR/STEP, ≤3k vértices el héroe, `frente` si camina de
espaldas.
