# -*- encoding: utf-8 -*-
"""Actores de texto dibujados como overlay 2D sobre la escena.

Equivalen a ``pilas.actores.Texto`` / ``pilas.actores.Puntaje``: sus
coordenadas x, y son píxeles de ventana (origen abajo-izquierda).
"""

from pilas3d import colores
from pilas3d.actores.actor import Actor


class Texto(Actor):
    es_overlay = True

    def __init__(self, pilas, texto="", x=10, y=10, tamano=18,
                 ancho=None):
        self._texto = texto
        self.tamano = tamano
        #: Ancho máximo en píxeles (solo para texto multilínea);
        #: las líneas más largas se recortan ahí.
        self.ancho = ancho
        self._label = None
        self._multi = None
        super(Texto, self).__init__(pilas, x=x, y=y, z=0)
        self.radio_de_colision = 0.0

    @property
    def texto(self):
        return self._texto

    @texto.setter
    def texto(self, valor):
        self._texto = valor

    def _generar_geometria(self):
        return [], [], 0

    def dibujar(self):
        multi = '\n' in self._texto
        if self._label is None or multi != self._multi:
            from pyglet.text import Label
            self._multi = multi
            ancho = self.ancho
            if ancho is None:
                ventana = self.pilas.ventana
                ancho = ventana.width - self._x if ventana else 4096
            self._label = Label(
                self._texto,
                font_size=self.tamano,
                x=self._x,
                y=self._y,
                anchor_y="baseline",
                multiline=multi,
                width=ancho,
            )
        self._label.text = self._texto
        self._label.x = self._x
        self._label.y = self._y
        r, g, b = self._color
        self._label.color = (r, g, b, 255)
        self._label.draw()


class Puntaje(Texto):
    """Muestra un puntaje numérico, como ``pilas.actores.Puntaje``."""

    def __init__(self, pilas, x=10, y=10, tamano=22, prefijo=""):
        self.valor = 0
        self.prefijo = prefijo
        super(Puntaje, self).__init__(
            pilas, texto=self._armar(), x=x, y=y, tamano=tamano
        )
        self.color = colores.amarillo

    def _armar(self):
        return "{}{}".format(self.prefijo, self.valor)

    def aumentar(self, cantidad=1):
        self.valor += cantidad
        self.texto = self._armar()
