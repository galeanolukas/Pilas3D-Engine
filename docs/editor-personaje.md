# Guía: editor de personajes

`ejemplos/editor_personaje.py` es una mini-herramienta para **posar
modelos articulados glTF y crear animaciones propias por keyframes**,
sin necesidad de Blender. Todo queda en JSON al lado del ejemplo.

```bash
.venv/bin/python ejemplos/editor_personaje.py
```

---

## 1. Vista general

```
┌────────────────────────┬──────────────────┐
│                        │  >> _rootJoint   │
│      vista 3D          │     Wolf_01      │
│   (botón der = órbita) │     Becken_05    │
│                        │      ...         │
├────────────────────────┴──────────────────┤
│ modelo | hueso | eje     ayuda de teclas  │
└───────────────────────────────────────────┘
```

La ventana se divide en dos áreas (`pilas.ventana.area_3d` +
`actores.Panel`): la vista 3D arriba-izquierda, el panel lateral con
la lista de huesos y el panel inferior con info y ayuda. Al estirar
la ventana los paneles se reacomodan solos.

## 2. Modelos

El editor busca automáticamente todos los `.glb` en `modelos/`
(recursivo) al arrancar. Ese directorio **está ignorado por git** a
propósito: los modelos son locales tuyos.

- **N**: pasa al siguiente modelo de la lista (cicla).
- Cada modelo se **auto-escala** a ~1.8 unidades de alto (el Fox de
  Khronos viene en centímetros, el wolf en metros).
- Si el modelo no tiene esqueleto (p. ej. un logo estático) se ve
  igual, pero el panel avisa "no tiene esqueleto".

### Cargar un .glb externo (tecla A)

Abre un **explorador de archivos** dentro de la ventana:

- `↑/↓` navegan, `ENTER` entra a carpetas `[dir]` o elige un `.glb`/`.gltf`,
  `..` sube un nivel, `ESC` cancela.
- Al elegir, un **input** te deja ponerle nombre al modelo (viene
  prellenado con el del archivo). `ENTER` confirma.
- El modelo queda agregado a la lista de `N`.

### De dónde sacar modelos compatibles

Funcionan `.glb`/`.gltf` **glTF 2.0** con una skin (`JOINTS_0` +
`WEIGHTS_0`). Del catálogo
[KhronosGroup/glTF-Sample-Assets](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models)
ya probados: **Fox** (texturas + Walk/Run/Survey, recomendado),
**CesiumMan**, **BrainStem**, **Wolf**. También sirven rigs de
Mixamo/Quaternius exportados a `.glb`.

## 3. Posar

| Tecla | Acción |
|---|---|
| `↑` / `↓` | elegir hueso (la esfera roja lo marca en el modelo) |
| `X` / `Y` / `Z` | elegir eje de rotación |
| `←` / `→` | rotar el hueso ±10° |
| `R` | reiniciar a la pose original |
| `G` / `C` | guardar / cargar `pose-<modelo>.json` |
| Botón derecho + drag | orbitar la cámara |

## 4. Animar por keyframes

La idea: **posás → capturás → posás otra cosa → capturás →
reproducís**. El motor interpola suave entre keyframes (nlerp de
quaternions, el mismo que usa para las animaciones del archivo).

| Tecla | Acción |
|---|---|
| `M` | capturar la pose actual como keyframe |
| `W` | borrar el último keyframe |
| `P` | compilar los keyframes en la animación `mi_anim` y reproducirla en loop |
| `J` | guardar la animación en `anim-<modelo>.json` |
| `L` | cargar `anim-<modelo>.json` y reproducirla |

Mínimo 2 keyframes. Cada keyframe son ~0.5 s de animación.

## 5. La API debajo del capó

Todo lo que hace el editor es API pública de `ModeloGLTF` — podés
usarla desde la consola o tus juegos:

```python
lobo = pilas.actores.ModeloGLTF('modelos/x.glb')

lobo.huesos()                       # [(indice, nombre), ...]
lobo.rotar_hueso('Becken_05', 'y', 15)
lobo.mover_hueso(i, dy=0.1)         # desplazar/estirar un hueso
lobo.posicion_hueso(i)              # posición mundo del hueso
lobo.refrescar_pose()               # re-aplicar la piel sin animar
lobo.reiniciar_pose()
lobo.guardar_pose('pose.json');  lobo.cargar_pose('pose.json')

lobo.crear_animacion('saludar', [pose_a, pose_b], duracion=0.8)
lobo.animar('saludar', ciclica=True)
lobo.guardar_animacion('a.json');  otro.cargar_animacion('a.json')
```

Los JSON de animación son portables entre instancias **del mismo
modelo** (los índices de hueso tienen que coincidir).

## 6. Límites honestos

- Una skin por modelo, triángulos, animación de nodos TRS. Morph
  targets y multi-material todavía no.
- Skinning por CPU: fluido con Fox/wolf; BrainStem (34k vértices)
  ya se nota pesado.
- No exporta `.glb`: lo que creás vive en JSON del motor. Para
  llevarlo a Blender habría que escribir un exportador (pendiente).
- Editás la pose, no la malla: no hay edición por vértice.
