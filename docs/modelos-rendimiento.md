# Modelos animados: requerimientos y rendimiento

`ModeloGLTF` anima por **skinning en CPU** (Python puro): cada frame
transforma cada vértice por sus huesos y reescribe el vertex list.
Es simple y educativo, pero pone un techo claro de rendimiento.
Esta es la guía para que los personajes carguen bien y sin lag.

## Requerimientos del archivo (.glb/.gltf)

| Regla | Detalle |
|---|---|
| Formato | `.glb` binario único (o `.gltf` + `.bin` junto). Sin Draco ni meshopt |
| Geometría | Solo primitivas **TRIANGLES** — líneas/puntos se descartan |
| Skin | **Una sola** por archivo (una armadura) |
| Animaciones | Canales `translation`/`rotation`/`scale`, interpolación **LINEAR o STEP**. `CUBICSPLINE` se interpreta mal — en Blender exportar con *Sampling* |
| Atributos | `POSITION`, `NORMAL`, `TEXCOORD_0`, `JOINTS_0`, `WEIGHTS_0` |
| Material | `baseColorFactor` + **una** `baseColorTexture` (PNG/JPEG, externa o embebida). Sin normal/metallic/emisiva |
| Morpher | Sin shape keys — los canales `weights` se ignoran |
| Ejes | +Y arriba, transforms aplicados |

## Límites de tamaño (medidos)

Con el vertex list **indexado** (los índices ya no se expanden):

| Vértices únicos | Skinning/frame | Veredicto |
|---|---|---|
| ~1.700 (Fox.glb) | ~5 ms | fluido |
| ~3.200 (Wolf) | ~9 ms | usable, 1-2 personajes |
| ~10.000 | ~17 ms | límite: solo el héroe |
| ~34.000 (BrainStem) | ~57 ms | slideshow, no usar |

Regla práctica:

- **Héroe animado**: ≤ ~3.000 vértices, ≤ ~50 huesos
- **NPCs secundarios**: personajes de mallas (`Robot`, `Mono`…) o
  `ModeloGLTF` sin animación activa
- **Textura**: una sola, ≤ 1024×1024
- Cada `ModeloGLTF` extra animado suma su skinning al frame — el
  presupuesto total es ~16 ms

## Qué se optimizó en el motor

- **Vertex list indexado**: antes los índices se expandían a
  vértices duplicados (BrainStem 34k → 185k → ~700 ms/frame). Ahora
  el skinning recorre vértices únicos: ~12× más rápido.
- **Pesos nulos precomputados**: el loop solo recorre los pares
  (hueso, peso) ≠ 0.
- **Caché de parseo**: `gltf.cargar` cachea por ruta — dos actores
  del mismo `.glb` no releen el archivo (reciben copia profunda).

## Siguientes pasos si hace falta más

1. Skip de skinning para actores fuera de cámara/lejos (frustum).
2. Detener el skinning cuando el clip terminó y `ciclica=False`
   (hoy ya se queda en la última pose, pero el costo queda si se
   fuerza `actualizar`).
3. Skinning en GPU por shader — el salto real para modelos de
   10k+ vértices o muchos personajes simultáneos.
