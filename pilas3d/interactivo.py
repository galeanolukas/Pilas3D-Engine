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
