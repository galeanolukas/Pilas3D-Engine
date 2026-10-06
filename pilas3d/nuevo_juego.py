# -*- encoding: utf-8 -*-
"""``pilas3d-init`` — scaffolding de un proyecto de juego.

    pilas3d-init mi_juego

Crea ``mi_juego/`` con la estructura de ``docs/estructura-juego.md``
(directorios de modelos, texturas, sonidos, fuentes, hdr y mapas) y
un ``juego.py`` que ya corre: cielo, piso, jugador con teclado y HUD.

Las carpetas quedan con ``.gitkeep`` — se van llenando con los
assets (``texturas/<pack>/``, ``modelos/personajes/<n>/``…) y las
herramientas del motor las encuentran solas.
"""

import os
import re
import sys

# el árbol de docs/estructura-juego.md
_DIRS = (
    'mapas',
    'modelos/personajes',
    'modelos/props',
    'modelos/fuentes',
    'modelos/docs',
    'texturas',
    'sonidos',
    'fonts',
    'data/hdr',
    'data/imagenes',
)

_JUEGO = '''\
# -*- encoding: utf-8 -*-
"""{titulo} — creado con pilas3d-init.

Estructura del proyecto: docs/estructura-juego.md
  modelos/    .glb animados, .obj props
  texturas/   packs de materiales (pilas.materiales['alias'])
  data/hdr/   fondos HDR -> Cielo('archivo.hdr')
  sonidos/    .wav -> pilas.sonidos.cargar('x.wav')
  mapas/      niveles del editor pilas3d-mapas (tecla G)

Herramientas del motor:
  pilas3d-mapas       editor de niveles (voxels + terreno)
  pilas3d-editor      editor de personajes .glb (poses/animaciones)
  pilas3d-bloques     IDE de bloques -> exporta .py y .html
  pilas3d-empaquetar  empaqueta el juego en un ejecutable
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="{titulo}")

# -- fondo: cielo generado; con un .hdr en data/hdr/ queda mejor:
#    cielo = pilas.actores.Cielo('kloofendal_48d_partly_cloudy_puresky_2k.hdr')
#    cielo.iluminar_escena()     # la luz sale del propio mapa HDR
pilas.actores.Cielo('dia')
pilas.actores.Piso(tamano=30, divisiones=30)

# -- jugador
jugador = pilas.actores.Robot()
jugador.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=5)

# -- HUD
pilas.actores.Texto("{titulo}", x=10, y=10, tamano=18)
pilas.actores.Texto("flechas: caminar", x=10, y=35, tamano=12)


pilas.ejecutar()
'''

_AYUDA = '''\
# {titulo}

Creado con `pilas3d-init`. Reglas rápidas — la guía completa está en
`docs/estructura-juego.md` del motor.

## Correr

```
python juego.py
```

## Dónde va cada cosa

| Carpeta | Qué poner | Cómo se usa |
|---|---|---|
| `modelos/personajes/` | `.glb` riggeados | `pilas.actores.ModeloGLTF('modelos/personajes/x/X.glb')` |
| `modelos/props/` | `.glb`/`.obj`+`.mtl` | `pilas.actores.Modelo(...)` |
| `modelos/fuentes/` | `.blend`/`.fbx` | no se cargan — re-exportar a .glb |
| `texturas/` | packs de mapas PBR | `pilas.materiales['alias']` |
| `data/hdr/` | `.hdr` equirectangulares | `pilas.actores.Cielo('x.hdr')` |
| `sonidos/` | `.wav` | `pilas.sonidos.cargar('x.wav')` |
| `fonts/` | `.ttf`/`.otf` | `Texto('...', fuente='x.ttf')` |
| `mapas/` | niveles | `pilas3d-mapas` los crea (G guarda) |

## Herramientas

```
pilas3d-mapas       # editor de niveles (voxels y terreno)
pilas3d-editor      # poses/animaciones de personajes .glb
pilas3d-bloques     # programación por bloques -> .py / .html
pilas3d-empaquetar  # ejecutable distribuible
pilas3d             # REPL interactivo
```
'''


def _nombre_directorio(titulo):
    """'Mi Juego!' -> 'mi_juego' — nombre de carpeta seguro."""
    nombre = re.sub(r'[^a-zA-Z0-9]+', '_', titulo.strip().lower())
    return nombre.strip('_') or 'mi_juego'


def crear(titulo, directorio=None):
    """Crea la estructura del proyecto. Devuelve la ruta creada."""
    base = directorio or _nombre_directorio(titulo)
    if os.path.exists(base) and os.listdir(base):
        raise IOError("'%s' ya existe y no está vacío" % base)
    for d in _DIRS:
        ruta = os.path.join(base, d)
        os.makedirs(ruta, exist_ok=True)
        open(os.path.join(ruta, '.gitkeep'), 'a').close()
    with open(os.path.join(base, 'juego.py'), 'w') as f:
        f.write(_JUEGO.format(titulo=titulo))
    with open(os.path.join(base, 'README.md'), 'w') as f:
        f.write(_AYUDA.format(titulo=titulo))
    return base


def cli(argv=None):
    """Punto de entrada del comando ``pilas3d-init``."""
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 1
    titulo = ' '.join(argv)
    try:
        base = crear(titulo)
    except IOError as e:
        print('error: %s' % e)
        return 1
    print('Proyecto "%s" creado en ./%s/' % (titulo, base))
    print()
    print('  cd %s' % base)
    print('  python juego.py          # ya corre: cielo + jugador')
    print()
    print('Cuando sumes assets el motor los encuentra solo:')
    print('  modelos/personajes/*.glb  -> pilas.actores.ModeloGLTF')
    print('  texturas/<pack>/          -> pilas.materiales["<pack>"]')
    print('  data/hdr/*.hdr            -> pilas.actores.Cielo("x.hdr")')
    print()
    print('Herramientas: pilas3d-mapas (niveles), pilas3d-editor '
          '(personajes),')
    print('              pilas3d-bloques (bloques), '
          'pilas3d-empaquetar (exe)')
    return 0


if __name__ == '__main__':
    sys.exit(cli())
