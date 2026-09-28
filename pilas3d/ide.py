# -*- encoding: utf-8 -*-
"""pilas3d-ide: consola Python integrada en la ventana del motor.

A diferencia de ``pilas3d`` (terminal + ventana flotante), acá el
REPL vive en una columna lateral dentro de la misma ventana — se ve
el resultado del código a la izquierda mientras se escribe.

    pilas3d-ide                  # comando (pip install -e .)

    >>> import pilas3d.ide
    >>> pilas3d.ide.main()       # desde Python

Controles de la consola:

- ENTER ejecuta la línea (los bloques ``def``/``for``/``si``
  multi-línea se detectan solos — ENTER en línea vacía cierra)
- ↑ / ↓ recorren el historial
- Ctrl+S guarda todo lo ejecutado en ``sesion_pilas3d.py``
- ESC limpia la línea actual (no cierra la ventana)
"""

import codeop
import contextlib
import io
import os
import traceback

import pilas3d


class Consola(object):
    """REPL embebido: columna lateral con log, input y ejecución."""

    PANEL = 400        # ancho de la columna de la consola (px)
    MAX_LOG = 60       # líneas visibles del historial de salida

    def __init__(self, pilas):
        self.pilas = pilas
        self.ns = {'pilas': pilas, 'pilas3d': pilas3d}
        self.buffer = []            # líneas del bloque en curso
        self.linea = ''             # línea que se está escribiendo
        self.historial = []         # bloques ejecutados (↑/↓)
        self.hist_sel = 0
        self.script = []            # código ejecutado (Ctrl+S)
        self.log = []
        self._comp = codeop.CommandCompiler()

        # UI: panel oscuro + log multilínea + línea de entrada
        self.panel = pilas.actores.Panel(color=pilas.colores.negro)
        self.salida = pilas.actores.Texto('', tamano=13,
                                          ancho=self.PANEL - 16)
        self.entrada = pilas.actores.Texto('', tamano=14)
        self.entrada.color = pilas.colores.verde

        self._linea('pilas3d ide — `pilas` ya está iniciada')
        self._linea('ENTER ejecuta - Ctrl+S guarda la sesión')
        self._pintar()

    # -- layout -------------------------------------------------------

    def organizar(self):
        """Columna derecha; la vista 3D queda en el resto."""
        if self.pilas.ventana is None:
            return
        w, h = self.pilas.ventana.width, self.pilas.ventana.height
        self.pilas.ventana.area_3d = (0, 0, w - self.PANEL, h)
        self.panel.x = w - self.PANEL
        self.panel.y = 0
        self.panel.ancho = self.PANEL
        self.panel.alto = h
        self.salida.x = w - self.PANEL + 8
        self.salida.y = h - 22
        self.entrada.x = w - self.PANEL + 8
        self.entrada.y = 14

    # -- pintado -------------------------------------------------------

    def _linea(self, texto):
        self.log.extend(texto.splitlines() or [''])

    def _prompt(self):
        return '... ' if self.buffer else '>>> '

    def _pintar(self):
        self.salida.texto = '\n'.join(self.log[-self.MAX_LOG:])
        self.entrada.texto = self._prompt() + self.linea + '_'

    # -- entrada de teclado (overlay sobre la ventana) ------------------

    def al_texto(self, texto):
        if texto >= ' ' and texto != '\r':
            self.linea += texto
            self._pintar()
        return True                 # consume todo: la consola es foco

    def al_pulsar(self, simbolo, modificadores):
        s = self.pilas.simbolos
        if modificadores & 2 and simbolo == s.s:   # Ctrl+S (MOD_CTRL)
            self.guardar()
        elif simbolo == s.ENTER:
            self._enter()
        elif simbolo == s.BACKSPACE:
            self.linea = self.linea[:-1]
        elif simbolo == s.ESCAPE:
            self.linea = ''
            self.buffer = []        # cancela también el multi-línea
        elif simbolo == s.ARRIBA:
            if self.historial and not self.buffer:
                self.hist_sel = max(0, self.hist_sel - 1)
                self.linea = self.historial[self.hist_sel]
        elif simbolo == s.ABAJO:
            if self.historial and not self.buffer:
                self.hist_sel = min(len(self.historial) - 1,
                                    self.hist_sel + 1)
                self.linea = self.historial[self.hist_sel]
        self._pintar()
        return True                 # consume (ESC no cierra ventana)

    # -- ejecución ------------------------------------------------------

    def _enter(self):
        entrada = self.linea
        self.linea = ''
        self._linea(self._prompt() + entrada)

        if not entrada.strip() and not self.buffer:
            self._pintar()
            return

        self.buffer.append(entrada)
        src = '\n'.join(self.buffer)
        codigo = self._comp(src, '<consola>', 'single')
        if codigo is None:
            self._pintar()          # bloque incompleto: prompt '...'
            return
        self.buffer = []
        self.historial.append(entrada)
        self.hist_sel = len(self.historial)
        self.script.append(src)
        self._ejecutar(src, codigo)
        self._pintar()

    def _ejecutar(self, src, codigo):
        salida = io.StringIO()
        try:
            with contextlib.redirect_stdout(salida), \
                 contextlib.redirect_stderr(salida):
                exec(codigo, self.ns)
        except Exception:
            salida.write(traceback.format_exc(limit=3))
        self._linea(salida.getvalue().rstrip('\n'))

    def guardar(self, ruta='sesion_pilas3d.py'):
        """Vuelca todo el código ejecutado a un .py reutilizable."""
        with open(ruta, 'w') as f:
            f.write('# sesión pilas3d-ide\n\n')
            f.write('\n\n'.join(self.script))
            f.write('\n')
        self._linea("guardado en %s" % os.path.abspath(ruta))


def main(ejecutar=True):
    """Abre la ventana con la consola lateral. Devuelve ``pilas``."""
    pilas = pilas3d.iniciar(titulo="pilas3d - ide")
    pilas.escena.fondo = pilas.colores.gris_oscuro
    pilas.luces.direccional.ambiente = 0.6

    consola = Consola(pilas)
    consola.organizar()
    pilas.tareas.siempre(0.5, consola.organizar)   # sigue el resize

    if pilas.ventana is not None:
        pilas.ventana.push_handlers(on_text=consola.al_texto,
                                    on_key_press=consola.al_pulsar)
    pilas.consola_ide = consola

    if ejecutar:
        pilas.ejecutar()
    return pilas


def cli():
    """Punto de entrada del comando ``pilas3d-ide``."""
    main()
