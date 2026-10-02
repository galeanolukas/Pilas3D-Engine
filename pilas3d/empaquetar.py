# -*- encoding: utf-8 -*-
"""pilas3d-empaquetar: convierte un juego en ejecutable con PyInstaller.

Uso::

    pilas3d-empaquetar mi_juego.py
    pilas3d-empaquetar mi_juego.py --nombre "Mi Juego" \
        --incluir modelos --incluir sonidos
    pilas3d-empaquetar mi_juego.py --workflow   # GitHub Actions multi-SO

PyInstaller empaqueta el intérprete + pilas3d + pyglet + los datos del
paquete (``pilas3d/data``) en un solo ejecutable. Para assets del juego
(modelos, texturas, sonidos propios) se usa ``--incluir`` — el juego los
busca como siempre, con ruta relativa.

OJO: PyInstaller NO cross-compila — el ejecutable que sale es del SO
donde corrés el comando. Para generar los tres (Windows/Linux/macOS)
de una vez, ``--workflow`` escribe un workflow de GitHub Actions que
los compila en la nube a cada push.
"""

import os
import shutil
import subprocess
import sys


def _hay_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def _separador():
    """Separador de --add-data: ';' en Windows, ':' en el resto."""
    return ';' if os.name == 'nt' else ':'


def _add_data(origen, destino, args):
    args += ['--add-data', origen + _separador() + destino]


def empaquetar(script, nombre=None, incluir=(), icono=None,
               consola=False, dist='dist'):
    """Corre PyInstaller sobre ``script`` y devuelve la ruta del
    ejecutable (o lanza SystemExit si falla)."""
    if not _hay_pyinstaller():
        print('falta pyinstaller — instalalo con:')
        print('    pip install pyinstaller')
        raise SystemExit(1)
    if not os.path.isfile(script):
        print('no existe el script:', script)
        raise SystemExit(1)

    args = ['-m', 'PyInstaller', '--noconfirm', '--clean',
            '--onefile', '--name', nombre or _nombre_de(script)]
    args.append('--console' if consola else '--windowed')

    # los datos del motor (texturas, sonidos, logo) viajan dentro
    data = os.path.join(os.path.dirname(__file__), 'data')
    _add_data(data, os.path.join('pilas3d', 'data'), args)

    # pyglet carga drivers por plataforma dinámicamente; pymunk trae
    # binarios de chipmunk. collect-* los arrastra aunque PyInstaller
    # no detecte el import estático.
    args += ['--collect-submodules', 'pyglet']
    try:
        import pymunk  # noqa: F401
        args += ['--collect-submodules', 'pymunk',
                 '--collect-binaries', 'pymunk',
                 # demos/tests de pymunk pesan y piden pygame
                 '--exclude-module', 'pymunk.examples',
                 '--exclude-module', 'pymunk.tests']
    except ImportError:
        pass

    for carpeta in incluir:
        if not os.path.exists(carpeta):
            print('aviso: no existe', carpeta, '— no se empaqueta')
            continue
        # va con el mismo nombre relativo para que el juego la
        # encuentre como siempre
        _add_data(os.path.abspath(carpeta),
                  os.path.basename(os.path.abspath(carpeta)), args)

    if icono:
        args += ['--icon', icono]

    args += ['--distpath', dist, script]

    print('empaquetando', script, '…')
    print('pyinstaller', ' '.join(args[3:]))
    resultado = subprocess.call([sys.executable] + args)
    if resultado != 0:
        print('PyInstaller falló — mirá el log de arriba')
        raise SystemExit(resultado)

    exe = os.path.join(dist, nombre or _nombre_de(script))
    if os.name == 'nt':
        exe += '.exe'
    print('listo →', os.path.abspath(exe))
    return exe


def _nombre_de(script):
    return os.path.splitext(os.path.basename(script))[0]


WORKFLOW = """# Generado por pilas3d-empaquetar — compila el juego en los tres SO.
# (PyInstaller no cross-compila: cada ejecutable sale de su runner.)
name: ejecutables
on: [push, workflow_dispatch]
jobs:
  compilar:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install -e . pyinstaller
      - run: pilas3d-empaquetar %(script)s %(incluir)s
      - uses: actions/upload-artifact@v4
        with:
          name: %(nombre)s-${{ matrix.os }}
          path: dist/%(nombre)s*
"""


def escribir_workflow(script, nombre=None, incluir=()):
    """Escribe .github/workflows/ejecutables.yml que compila el juego
    en Linux + Windows + macOS a cada push (PyInstaller no cross-
    compila: cada SO sale de su propio runner)."""
    nombre = nombre or _nombre_de(script)
    cmd_incluir = ' '.join('--incluir ' + c for c in incluir)
    ruta = os.path.join('.github', 'workflows', 'ejecutables.yml')
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w') as f:
        f.write(WORKFLOW % dict(incluir=cmd_incluir,
                                script=script, nombre=nombre))
    print('workflow escrito en', ruta)
    print('pushealo y GitHub Actions compila los 3 ejecutables en '
          '"Actions > ejecutables > Artifacts"')
    return ruta


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(
        prog='pilas3d-empaquetar',
        description='Convierte un juego pilas3d en ejecutable '
                    '(PyInstaller).')
    p.add_argument('script', help='el .py del juego (p. ej. '
                                  'ejemplos/lampara.py)')
    p.add_argument('--nombre', help='nombre del ejecutable')
    p.add_argument('--incluir', action='append', default=[],
                   help='carpeta de assets a empaquetar '
                        '(se puede repetir)')
    p.add_argument('--icono', help='icono .ico/.png del ejecutable')
    p.add_argument('--consola', action='store_true',
                   help='deja una consola visible (útil para depurar)')
    p.add_argument('--dist', default='dist',
                   help='carpeta de salida (default: dist)')
    p.add_argument('--workflow', action='store_true',
                   help='solo escribe el workflow de GitHub Actions '
                        '(compila Linux+Windows+macOS en la nube)')
    a = p.parse_args(argv)

    if a.workflow:
        escribir_workflow(a.script, a.nombre, a.incluir)
        return
    empaquetar(a.script, a.nombre, a.incluir, a.icono,
               a.consola, a.dist)


def cli():
    """Punto de entrada del comando ``pilas3d-empaquetar``."""
    main()

if __name__ == "__main__":
    main()
