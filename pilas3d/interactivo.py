# -*- encoding: utf-8 -*-
"""Consola interactiva de pilas3d, con autocompletado.

Uso::

    pilas3d                    # comando (tras ``pip install -e .``)
    python3 -m pilas3d         # equivalente sin instalar el comando

Abre la ventana del juego y una consola IPython donde ``pilas`` ya
está iniciada. Cada línea que se ejecuta refresca la escena con
``pilas.paso()`` automáticamente, como en la consola de pilas-engine.

Si IPython no está instalado se usa la consola estándar de Python con
autocompletado por tabulador (sin refresco automático).
"""

import sys

import pilas3d

BANNER = """\
pilas3d interactivo
-------------------
`pilas` ya está iniciada y la ventana abierta. Cada línea que
ejecutes refresca la escena automáticamente (pilas.paso()).

    >>> cubo = pilas.actores.Cubo()
    >>> cubo.color = pilas.colores.rojo
    >>> for i in range(180):      # anima ~3 segundos
    ...     pilas.paso()

`pilas.ayuda()` muestra la guía completa de la API.
`%ejemplo <nombre>` corre un ejemplo en esta ventana (ej: %ejemplo hola_cubo).
`%ia <pregunta>` consulta al asistente local (opcional, IA).
`%explicar` pide a la IA que explique el último error.
"""


def main():
    pilas = pilas3d.iniciar(titulo="pilas3d - consola interactiva")
    ns = {'pilas': pilas, 'pilas3d': pilas3d}

    def refrescar(result=None):
        try:
            if pilas.ventana is not None:
                pilas.paso()
        except Exception:
            pass

    try:
        from IPython.terminal.interactiveshell import (
            TerminalInteractiveShell)
    except ImportError:
        _consola_basica(pilas, ns)
        return

    shell = TerminalInteractiveShell.instance(
        user_ns=ns, banner1=BANNER)

    ultimo_error = {'texto': None}

    def guardar_error(result):
        if getattr(result, 'error_in_exec', None):
            ultimo_error['texto'] = ''.join(
                result.error_in_exec.__class__.__name__
                + ': ' + str(result.error_in_exec))
        else:
            ultimo_error['texto'] = None

    def _ia(line):
        try:
            from pilas3d.ia.asistente import preguntar
            print(preguntar(line, contexto=pilas._contexto()))
        except RuntimeError as e:
            print("(asistente no disponible: %s)" % e)

    def _explicar(line):
        if not ultimo_error['texto']:
            print("No hay ningún error reciente que explicar.")
            return
        try:
            from pilas3d.ia.asistente import explicar_error
            print(explicar_error(ultimo_error['texto'],
                                 contexto=pilas._contexto()))
        except RuntimeError as e:
            print("(asistente no disponible: %s)" % e)

    def _ejemplo(line):
        """Corre un archivo de ejemplos/ dentro de esta misma ventana.

        Parchea pilas3d.iniciar (devuelve la pilas ya abierta) y
        Pilas.ejecutar (no-op: el auto-refresco con paso() la anima).
        """
        import pathlib
        nombre = line.strip().replace('ejemplos/', '')
        if nombre.endswith('.py'):
            nombre = nombre[:-3]
        ruta = pathlib.Path('ejemplos') / (nombre + '.py')
        if not ruta.exists():
            disponibles = sorted(p.stem
                                 for p in pathlib.Path('ejemplos')
                                 .glob('*.py'))
            print("No existe ese ejemplo. Disponibles:")
            for e in disponibles:
                print('  ', e)
            return
        codigo = compile(ruta.read_text(encoding='utf-8'),
                         str(ruta), 'exec')
        iniciar_orig, ejecutar_orig = (pilas3d.iniciar,
                                       pilas3d.Pilas.ejecutar)
        try:
            pilas3d.iniciar = lambda *a, **k: pilas
            pilas3d.Pilas.ejecutar = lambda self: None
            ns = shell.user_ns
            archivo_previo = ns.get('__file__')
            ns['__file__'] = str(ruta.resolve())
            exec(codigo, ns)
            ns['__file__'] = archivo_previo
        finally:
            pilas3d.iniciar = iniciar_orig
            pilas3d.Pilas.ejecutar = ejecutar_orig

    shell.register_magic_function(_ia, 'line', 'ia')
    shell.register_magic_function(_explicar, 'line', 'explicar')
    shell.register_magic_function(_ejemplo, 'line', 'ejemplo')
    shell.events.register('post_run_cell', guardar_error)
    shell.events.register('post_run_cell', refrescar)
    shell.interact()
    pilas.terminar()


def _consola_basica(pilas, ns):
    """Fallback sin IPython: consola estándar con tab-completion."""
    import code
    import readline
    import rlcompleter

    readline.set_completer(rlcompleter.Completer(ns).complete)
    readline.parse_and_bind('tab: complete')
    code.interact(banner=BANNER +
                  "(sin IPython: llamá a pilas.paso() para refrescar)",
                  local=ns)
    pilas.terminar()


if __name__ == '__main__':
    sys.exit(main())
