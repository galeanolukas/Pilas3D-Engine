# Guía: editor de mapas (`pilas3d-mapas`)

Editor de mapas de bloques (voxels) con la misma interfaz del editor
de personajes: vista 3D + paleta lateral + barra inferior. Los mapas
se guardan en `mapas/<nombre>.mapa.json` y los juegos los cargan con
`pilas.mapas.cargar()`.

```bash
.venv/bin/pilas3d-mapas
```

## Controles

| Entrada | Acción |
|---|---|
| click izquierdo | poner bloque en la celda marcada |
| click medio o `X` | sacar el bloque golpeado |
| `ESPACIO` + mover mouse | orbitar la cámara (rueda: zoom; click derecho + drag también funciona) |
| `←` / `→` | cambiar tipo de bloque / prop en la paleta |
| `M` | alternar paleta: bloques ↔ props (`modelos/props/*.glb/.gltf/.obj`) |
| `R` | girar el prop bajo el cursor 45° (paleta props) |
| `D` | agarrar el prop bajo el cursor — sigue al mouse como fantasma; `D` o click suelta |
| `F` / `V` | subir / bajar el prop en Y (0.5 por pulsación) |
| `Z` / `C` | achicar / agrandar el prop |
| `Q` / `E` | subir / bajar la columna bajo el cursor (esculpir terreno) |
| `S` | marcar/quitar el spawn (punto de inicio) |
| `T` | terreno procedural de base (pasto/tierra/piedra) |
| `N` | mapa nuevo (vacío) |
| `G` | guardar — al path actual si ya existe; si no pide nombre → `mapas/<nombre>.mapa.json` |
| `O` | "guardar como..." — siempre pide nombre nuevo |
| `L` | explorador de archivos → carga cualquier `.mapa.json` (navegá dirs con `[dir]` y `..`) |

La esfera roja marca la celda donde caería el bloque (adyacente al
bloque golpeado por el rayo del mouse, o el piso si no hay bloques).
En la paleta de **props** el marcador salta al prop bajo el cursor:
ese es el objetivo de `D`, `R`, `F`/`V`, `Z`/`C` y `X`.
La grilla es 24×24 con altura hasta 10.

## Tipos de bloque

`cesped`, `tierra`, `piedra`, `ladrillo`, `arena` — las baldosas del
atlas básico del `Mundo` (muro = `ladrillo` apilado, piso = `tierra`).

## Usar el mapa en un juego

```python
mundo = pilas.mapas.cargar('mapas/nivel.mapa.json')
jugador.posicion = mundo.spawn      # punto de inicio (o None)
for prop in mundo.props:            # modelos estáticos del mapa
    prop.actualizar()               # (los .glb/.obj se cargan solos)
```

## El formato `.mapa.json`

```json
{
  "version": 1, "nombre": "nivel",
  "spawn": [0.5, 1.0, 0.5],
  "bloques": [[i, j, k, "tipo"], ...],
  "props": [{"ruta": "modelos/props/arbol.glb",
             "x": 0, "y": 1, "z": 0, "escala": 1.0}]
}
```

- `bloques`: celdas enteras `[i,j,k)` del voxel — las mismas
  coordenadas de `Mundo.poner_bloque`
- `props`: modelos `.glb`/`.gltf`/`.obj` posicionados encima del
  terreno (árboles, farolas...). El editor los coloca desde la paleta
  de props (`M`) con click, los saca con `X` y los gira con `R`.
  Se guardan con `ruta`, `x/y/z`, `escala` y `rotacion_y`; el
  prop "objetivo" es el agarrado (`D`) o el más cercano al cursor.
  Las rutas relativas se resuelven junto al `.mapa.json` si no están
  en el cwd — el mapa es portable si copiás los modelos al lado.
- `spawn`: punto de inicio del jugador (esfera celeste, tecla `S`)

## Límites honestos

- El editor es por mouse sobre la superficie visible — para hacer
  cuevas hay que picar como en Minecraft.
- Los props van en `modelos/props/` (para que el editor los liste)
  o se referencian por ruta en el JSON a mano.
- Un solo atlas de bloques (`TIPOS_POR_DEFECTO`); más tipos =
  ampliar `TIPOS` en `pilas3d/mapa_editor.py` y el atlas del `Mundo`.

## Modo terreno (heightmap)

Con `Y` el editor cambia de voxels a **terreno continuo**: rejilla
deformable con click (colinas), pozos, lagos con agua y baldosa por
celda. Guarda `*.terreno.json` — `pilas.mapas.cargar()` detecta el
formato solo. Guía completa: [docs/terreno.md](terreno.md).
