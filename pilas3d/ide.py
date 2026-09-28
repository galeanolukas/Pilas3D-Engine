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
  multi-línea se detectan solos y auto-indentan — ENTER en línea
  vacía cierra el bloque)
- TAB autocompleta (con línea vacía indenta 4 espacios)
- ↑ / ↓ recorren el historial
- Ctrl+S guarda todo lo ejecutado en ``sesion_pilas3d.py``
- ``%abrir archivo.py`` carga un archivo y sigue la sesión;
  ``%run archivo.py`` solo lo ejecuta; ``%ayuda`` lista comandos
- ESC limpia la línea actual (no cierra la ventana)
"""

import codeop
import contextlib
import io
import os
import re
import rlcompleter
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
        self._completer = rlcompleter.Completer(self.ns)
        self._sugerencias = []      # candidatos de TAB en curso
        self._sug_i = 0             # índice para ciclar con TAB
        self._sug_palabra = ''      # prefijo que se completó

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
            self._sugerencias = []
            self._pintar()
        return True                 # consume todo: la consola es foco

    # -- autocompletado (TAB) ----------------------------------------------

    def _palabra_final(self):
        m = re.search(r'[\w.]*$', self.linea)
        return m.group(0) if m else ''

    def _reemplazar_palabra(self, nueva):
        self.linea = self.linea[:len(self.linea)
                                - len(self._sug_palabra)] + nueva
        self._sug_palabra = nueva

    def _completar(self):
        """TAB: completa el identificador bajo el cursor; TAB de
        nuevo cicla las opciones y las muestra en el log. Con la
        línea vacía o solo espacios, TAB inserta indentación."""
        if not self.linea.strip():
            self.linea += '    '
            return
        if self._sugerencias:
            # cicla la sugerencia siguiente
            self._sug_i = (self._sug_i + 1) % len(self._sugerencias)
            self._reemplazar_palabra(self._sugerencias[self._sug_i])
            return
        self._sug_palabra = self._palabra_final()
        if not self._sug_palabra:
            return
        sugs = []
        i = 0
        while True:
            s = self._completer.complete(self._sug_palabra, i)
            if s is None:
                break
            sugs.append(s)
            i += 1
            if i > 200:
                break
        if not sugs:
            return
        if len(sugs) == 1:
            self._reemplazar_palabra(sugs[0])
            return
        # prefijo común + candidatos en el log; TAB cicla
        comun = os.path.commonprefix(sugs)
        if len(comun) > len(self._sug_palabra):
            self._reemplazar_palabra(comun)
        self._sugerencias = sugs
        self._sug_i = 0
        # lista limpia: una columna por opción, con contador
        vista = sugs[:8]
        self._linea('  '.join(vista)
                    + ('   +%d más' % (len(sugs) - 8)
                       if len(sugs) > 8 else ''))

    def al_pulsar(self, simbolo, modificadores):
        s = self.pilas.simbolos
        if simbolo != s.TAB:
            self._sugerencias = []  # cualquier otra tecla corta el ciclo
        if modificadores & 2 and simbolo == s.s:   # Ctrl+S (MOD_CTRL)
            self.guardar()
        elif simbolo == s.TAB:
            self._completar()
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

        if entrada.startswith('%') and not self.buffer:
            self._comando(entrada.strip())
            self._pintar()
            return

        # una línea de solo espacios (el auto-indent) cierra el bloque
        self.buffer.append(entrada if entrada.strip() else '')
        src = '\n'.join(self.buffer)
        codigo = self._comp(src, '<consola>', 'single')
        if codigo is None:
            # bloque incompleto: auto-indentar la línea siguiente
            ultima = self.buffer[-1]
            base = len(ultima) - len(ultima.lstrip())
            if ultima.rstrip().endswith(':'):
                base += 4
            self.linea = ' ' * base
            self._pintar()          # prompt '...'
            return
        self.buffer = []
        self.historial.append(entrada)
        self.hist_sel = len(self.historial)
        self.script.append(src)
        self._ejecutar(src, codigo)
        self._pintar()

    # -- comandos % -----------------------------------------------------

    def _comando(self, entrada):
        """%ayuda / %run <archivo> / %abrir <archivo> / %guardar /
        %limpiar."""
        partes = entrada.split(None, 1)
        cmd, arg = partes[0], partes[1].strip() if len(partes) > 1 \
            else ''
        if cmd in ('%run', '%abrir', '%cargar'):
            self._archivo(arg, incorporar=(cmd != '%run'))
        elif cmd == '%guardar':
            self.guardar(arg or 'sesion_pilas3d.py')
        elif cmd == '%limpiar':
            self.log = []
        elif cmd == '%ayuda':
            self._linea('%run f.py ejecuta - %abrir f.py lo abre y '
                        'sigue la sesión')
            self._linea('%guardar [f.py] - %limpiar vacía el log')
        else:
            self._linea('comando desconocido: ' + cmd +
                        '  (%ayuda lista)')

    def _archivo(self, ruta, incorporar):
        """Ejecuta un .py en la consola. Con ``incorporar`` además se
        agrega al script de la sesión (Ctrl+S lo re-guarda)."""
        if not ruta:
            self._linea('falta el archivo: %run juego.py')
            return
        try:
            with open(ruta) as f:
                src = f.read()
        except OSError as e:
            self._linea('no pude abrir %s: %s' % (ruta, e.strerror))
            return
        codigo = self._comp(src, ruta, 'exec')
        if codigo is None:
            self._linea('el archivo está incompleto o mal formado')
            return
        if incorporar:
            self.script.append(src.rstrip())
            self._linea("abierto %s — ejecutado y agregado a la sesión"
                        % ruta)
        else:
            self._linea("ejecutado %s" % ruta)
        self._ejecutar(src, codigo)

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
