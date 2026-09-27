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
`%ia make_game <idea>` genera un juego en juegos/ con IA.
`%ia run <archivo>` / `%ia edit <archivo> <cambio>` / `%ia list`.
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

    # Sin esto la ventana de pyglet solo procesa eventos cuando se
    # ejecuta una celda (paso()); con el inputhook la ventana queda
    # viva mientras la consola espera input: se redimensiona, se
    # repinta y responde al mouse como si corriera un script.
    try:
        shell.enable_gui('pyglet')
    except Exception:
        pass

    ultimo_error = {'texto': None}

    def guardar_error(result):
        if getattr(result, 'error_in_exec', None):
            ultimo_error['texto'] = ''.join(
                result.error_in_exec.__class__.__name__
                + ': ' + str(result.error_in_exec))
        else:
            ultimo_error['texto'] = None

    def _correr_en_ventana(ruta):
        """Ejecuta un .py dentro de la ventana ya abierta: parchea
        pilas3d.iniciar (devuelve la pilas viva) y Pilas.ejecutar
        (no-op; el auto-refresco con paso() la anima)."""
        import pathlib
        ruta = pathlib.Path(ruta)
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

    def _ia(line):
        """Asistente con subcomandos: make_game, run, edit, list."""
        import pathlib
        from pilas3d.ia.make_game import (JUEGOS_DIR, generar_juego,
                                          editar_juego)

        partes = line.strip().split(maxsplit=2)
        cmd = partes[0].lower() if partes else ''

        try:
            if cmd == 'make_game':
                if len(partes) < 2:
                    print("Uso: %ia make_game <descripción del juego>")
                    return
                descripcion = ' '.join(partes[1:])
                print("Generando juego: %s" % descripcion)
                exito, ruta, msg = generar_juego(descripcion)
                print("%s %s" % ('✔' if exito else '⚠', msg))
                print("  guardado en %s" % ruta)
                print("  corré con: %%ia run %s" % ruta)
                return

            if cmd == 'run':
                if len(partes) < 2:
                    print("Uso: %ia run <archivo.py>")
                    return
                ruta = pathlib.Path(partes[1])
                if not ruta.exists():
                    print("No existe: %s" % ruta)
                    return
                _correr_en_ventana(ruta)
                print("%s cargado en la escena actual" % ruta.name)
                return

            if cmd == 'edit':
                if len(partes) < 3:
                    print("Uso: %ia edit <archivo.py> <cambio>")
                    return
                ruta, cambio = pathlib.Path(partes[1]), partes[2]
                if not ruta.exists():
                    print("No existe: %s" % ruta)
                    return
                exito, msg = editar_juego(ruta, cambio)
                print("%s %s — %s"
                      % ('✔' if exito else '⚠', ruta.name, msg))
                return

            if cmd == 'list':
                JUEGOS_DIR.mkdir(exist_ok=True)
                juegos = sorted(JUEGOS_DIR.glob('*.py'))
                if not juegos:
                    print("No hay juegos guardados. "
                          "Creá uno con %ia make_game <descripción>")
                for f in juegos:
                    print('  ', f)
                return

            # sin subcomando: charla normal con el asistente
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
        _correr_en_ventana(ruta)

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
