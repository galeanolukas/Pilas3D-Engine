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
| click derecho + drag | orbitar la cámara (rueda: zoom) |
| `←` / `→` | cambiar tipo de bloque en la paleta |
| `S` | marcar/quitar el spawn (punto de inicio) |
| `T` | terreno procedural de base (pasto/tierra/piedra) |
| `N` | mapa nuevo (vacío) |
| `G` | guardar — pide nombre → `mapas/<nombre>.mapa.json` |
| `L` | listar mapas guardados y cargar |

La esfera roja marca la celda donde caería el bloque (adyacente al
bloque golpeado por el rayo del mouse, o el piso si no hay bloques).
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
- `props`: modelos `.glb`/`.obj` posicionados encima del terreno
  (árboles, farolas, etc. — el editor todavía no los coloca, pero el
  formato y el cargador ya los soportan)
- `spawn`: punto de inicio del jugador (esfera celeste, tecla `S`)

## Límites honestos

- El editor es por mouse sobre la superficie visible — para hacer
  cuevas hay que picar como en Minecraft.
- Los props se definen en el JSON a mano por ahora.
- Un solo atlas de bloques (`TIPOS_POR_DEFECTO`); más tipos =
  ampliar `TIPOS` en `pilas3d/mapa_editor.py` y el atlas del `Mundo`.
