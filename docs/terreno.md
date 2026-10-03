# Terreno: heightmap deformable con baldosa por celda

`Terreno` es una rejilla continua donde **cada vértice tiene altura**
y **cada celda una baldosa del atlas** — colinas, pozos y lagos suaves,
a diferencia del `Mundo` voxel (bloques cúbicos).

```python
t = pilas.actores.Terreno(celdas=20)          # 20x20 celdas de 1 m
t.montana(5, 5, radio=4, altura=3)            # colina suave
t.pozo(14, 12, radio=3, profundidad=2)        # hoyo
t.pintar_zona(14, 12, 3, 'agua')              # baldosas del fondo
t.agua = 0.4                                  # plano de agua → lago

# un personaje que sigue las lomas
h = t.altura_suelo(robot.x, robot.z)
if h is not None:
    robot.y = h
```

## Deformación

| Método | Qué hace |
|---|---|
| `t.subir(i, k, n)` / `t.bajar(i, k, n)` | mueve un vértice puntual (0 a `celdas`) |
| `t.montana(i, k, radio, altura)` | colina redonda con decaimiento suave |
| `t.pozo(i, k, radio, profundidad)` | hoyo redondo — lago si queda bajo el agua |
| `t.nivelar(h)` | deja todo plano a esa altura |

## Texturas por celda

Cada celda elige una baldosa del atlas. Por defecto hay `pasto`,
`piedra` y `agua`:

```python
t.pintar(i, k, 'piedra')              # una celda (0 a celdas-1)
t.pintar_zona(i, k, radio, 'agua')    # un círculo de celdas

# tus propias texturas (pilas3d/data/ o cwd)
t = pilas.actores.Terreno(celdas=20,
    tipos={'arena': 'arena.png', 'nieve': 'nieve.png'})

# una sola imagen repetida en todo el terreno
t = pilas.actores.Terreno(celdas=20, imagen='suelo.png')
```

## Agua

`t.agua = altura` crea un plano celeste semitransparente a esa altura:
todo pozo que quede por debajo se ve lleno — lago gratis.
`t.agua = None` lo saca.

## Guardar y cargar

```python
t.spawn = (0, 1, 0)
t.guardar('mapas/nivel.terreno.json')
t2 = pilas.mapas.cargar('mapas/nivel.terreno.json')   # auto-detecta
```

El `.terreno.json` guarda alturas, baldosas por celda, nivel de agua,
spawn y props — mismo contrato que los `.mapa.json` de voxels.

## En el editor (`pilas3d-mapas`)

`Y` alterna voxels ↔ terreno (conviven en la misma escena):

| Entrada | Acción |
|---|---|
| `ENTER` o `B` | colina bajo el cursor (`CTRL+click` también) |
| `X` | pozo — con agua queda lleno |
| `Q` / `E` | subir / bajar un vértice |
| `P` | pintar la zona del brush con la baldosa elegida |
| `1`-`3` o `←`/`→` | elegir baldosa |
| `Z` / `C` | tamaño del brush |
| `W` | agua on/off · `T` lomas aleatorias · `S` spawn |

`G` guarda `mapas/<nombre>.terreno.json`, `L` lo carga.

## En bloques

Categoría **Actores**: `crear terreno`, `forma` (montaña/pozo/subir/
bajar), `pintar zona` y `agua`. En el `.html` exportado el terreno
se dibuja con color por vértice (las texturas no viajan a web).

## ¿Qué suelo usar?

| Actor | Para |
|---|---|
| `Piso` | guía de referencia (líneas, sin superficie) |
| `Plano` | un quad plano con textura |
| `Terreno` | paisajes suaves: colinas, pozos, lagos, senderos |
| `Mundo` | voxels: cavar, construir, cuevas (tipo Minecraft) |

Ejemplo jugable: `python3 ejemplos/terreno.py`.
