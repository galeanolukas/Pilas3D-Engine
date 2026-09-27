# -*- encoding: utf-8 -*-
"""Panel: rectángulo 2D relleno dibujado como overlay.

Sirve para hacer zonas de interfaz oscuras detrás de textos (tipo
editor con panel lateral), sin costo extra de memoria: es un solo
cuadrilátero en el pase 2D.
"""

from pilas3d import colores
from pilas3d.actores.actor import Actor


class Panel(Actor):
    """Rectángulo de interfaz: ``x``, ``y``, ``ancho``, ``alto`` en
    píxeles de ventana (origen abajo-izquierda, como ``Texto``)."""

    es_overlay = True

    def __init__(self, pilas, x=0, y=0, ancho=200, alto=200,
                 color=None, opacidad=255):
        self.ancho = ancho
        self.alto = alto
        self.opacidad = opacidad
        self._rect = None
        super(Panel, self).__init__(pilas, x=x, y=y, z=0)
        self.color = color if color is not None else colores.gris_oscuro
        self.radio_de_colision = 0.0

    def _generar_geometria(self):
        return [], [], 0

    def dibujar(self):
        if self._rect is None:
            from pyglet.shapes import Rectangle
            self._rect = Rectangle(0, 0, 1, 1)
        self._rect.x = self._x
        self._rect.y = self._y
        self._rect.width = self.ancho
        self._rect.height = self.alto
        r, g, b = self._color
        self._rect.color = (r, g, b)
        self._rect.opacity = self.opacidad
        self._rect.draw()
