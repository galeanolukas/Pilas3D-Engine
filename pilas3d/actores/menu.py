# -*- encoding: utf-8 -*-
"""Menu: lista de opciones navegable con teclado y mouse.

Igual que un menú de juego: las opciones son textos en overlay 2D
(píxeles de ventana), se navega con flechas/WS + ENTER o se elige
haciendo click::

    menu = pilas.actores.Menu(
        opciones=[
            ("Jugar",        iniciar_juego),
            ("Calidad: alta", cambiar_calidad),   # ver abajo
            ("Salir",         pilas.terminar),
        ],
        x=260, y=300, tamano=22)

Si la función de una opción devuelve un texto nuevo, la etiqueta se
actualiza — útil para opciones que ciclan (``"Calidad: media"``).
"""

from pyglet.window import key, mouse

from pilas3d import colores
from pilas3d.actores.actor import Actor
from pilas3d.actores.texto import Texto


class Menu(Actor):
    """Menú de opciones como overlay 2D (no es geometría 3D)."""

    es_overlay = True

    def __init__(self, pilas, opciones, x=200, y=300, separacion=38,
                 tamano=22, color=None, seleccionado=None, titulo=None):
        super(Menu, self).__init__(pilas)
        self.radio_de_colision = 0.0
        self.color_base = color or colores.blanco
        self.color_sel = seleccionado or colores.amarillo
        self.separacion = separacion
        self.tamano = tamano
        self._opciones = list(opciones)
        self._sel = 0

        y0 = y
        if titulo:
            t = Texto(pilas, titulo, x=x, y=y, tamano=tamano + 10)
            t.color = self.color_sel
            self._titulo = t
            y0 -= separacion * 1.6
        else:
            self._titulo = None

        self._x = x
        self._textos = []
        for i, (texto, _fn) in enumerate(self._opciones):
            item = Texto(pilas, texto, x=x,
                         y=y0 - i * separacion, tamano=tamano)
            self._textos.append(item)
        self._pintar()

        if pilas.ventana is not None:
            pilas.ventana.push_handlers(
                on_key_press=self._al_pulsar,
                on_mouse_motion=self._al_mover_mouse,
                on_mouse_press=self._al_click_mouse)

    def _generar_geometria(self):
        return [], [], 0

    # -- estado ----------------------------------------------------------

    @property
    def opcion(self):
        """Índice de la opción seleccionada."""
        return self._sel

    def _ancho_item(self, i):
        # estimación en píxeles (el Label real se crea al dibujar)
        texto = self._opciones[i][0]
        return len(texto) * self.tamano * 0.62

    def _rect_item(self, i):
        ty = self._textos[i].y
        return (self._x, ty - 6,
                self._x + self._ancho_item(i), ty + self.tamano * 1.2)

    def _pintar(self):
        for i, item in enumerate(self._textos):
            sel = i == self._sel
            item.texto = ('» ' if sel else '  ') + self._opciones[i][0]
            item.color = self.color_sel if sel else self.color_base

    # -- navegación --------------------------------------------------------

    def mover(self, direccion):
        """Mueve la selección: 'arriba'/'abajo' o -1/+1."""
        if direccion in ('arriba', -1):
            self._sel = (self._sel - 1) % len(self._opciones)
        else:
            self._sel = (self._sel + 1) % len(self._opciones)
        self._pintar()

    def elegir(self):
        """Ejecuta la función de la opción seleccionada.

        Si la función devuelve un texto, la etiqueta se actualiza
        (para opciones que ciclan valores).
        """
        _texto, fn = self._opciones[self._sel]
        if fn is None:
            return
        nuevo = fn()
        if isinstance(nuevo, str):
            self._opciones[self._sel] = (nuevo, fn)
            self._pintar()
        return nuevo

    def fijar_texto(self, i, texto):
        """Cambia la etiqueta de la opción ``i`` (o por nombre)."""
        if isinstance(i, str):
            for n, (t, f) in enumerate(self._opciones):
                if t.startswith(i) or i in t:
                    i = n
                    break
        self._opciones[i] = (texto, self._opciones[i][1])
        self._pintar()

    # -- eventos de ventana -------------------------------------------------

    def _al_pulsar(self, simbolo, modificadores):
        if not self.esta_en_escena():
            return
        if simbolo in (key.UP, key.W):
            self.mover('arriba')
        elif simbolo in (key.DOWN, key.S):
            self.mover('abajo')
        elif simbolo in (key.RETURN, key.SPACE):
            self.elegir()

    def _bajo_mouse(self, x, y):
        for i in range(len(self._opciones)):
            x0, y0, x1, y1 = self._rect_item(i)
            if x0 <= x <= x1 and y0 <= y <= y1:
                return i
        return None

    def _al_mover_mouse(self, x, y, dx, dy):
        if not self.esta_en_escena():
            return
        i = self._bajo_mouse(x, y)
        if i is not None and i != self._sel:
            self._sel = i
            self._pintar()

    def _al_click_mouse(self, x, y, button, modifiers):
        if not self.esta_en_escena():
            return
        if button & mouse.LEFT:
            i = self._bajo_mouse(x, y)
            if i is not None:
                self._sel = i
                self._pintar()
                self.elegir()

    def eliminar(self):
        for item in self._textos:
            item.eliminar()
        if self._titulo is not None:
            self._titulo.eliminar()
        super(Menu, self).eliminar()
