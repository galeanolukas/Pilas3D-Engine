# -*- encoding: utf-8 -*-
"""Barra: indicador de vida/energía como overlay 2D del HUD.

    >>> enemigo.aprender(pilas.habilidades.Vida, vida=100)
    >>> barra = pilas.actores.Barra(enemigo)      # muestra su vida
    >>> barra = pilas.actores.Barra(de=lambda: pilas.puntos / 10)

``de`` puede ser un actor con ``vida``/``vida_maxima`` o un callable
que devuelva la fracción 0..1. El relleno va de verde a amarillo a
rojo según baje.
"""

from pyglet.gl import GL_TRIANGLES

from pilas3d import colores
from pilas3d.actores.actor import Actor


class Barra(Actor):
    """Rectángulo de progreso en píxeles (origen abajo-izquierda)."""

    es_overlay = True

    def __init__(self, pilas, de=None, x=10, y=10, ancho=120, alto=12,
                 color=None):
        #: actor con vida/vida_maxima o callable -> fracción 0..1
        self.de = de
        self.ancho = ancho
        self.alto = alto
        self.color_fijo = color          # None = verde→rojo según nivel
        self._fondo = None
        self._relleno = None
        super(Barra, self).__init__(pilas, x=x, y=y, z=0)
        self.radio_de_colision = 0.0

    def _generar_geometria(self):
        return [], [], GL_TRIANGLES, None, None

    def fraccion(self):
        """0..1 según la fuente; 0 si no hay fuente o murió."""
        if self.de is None:
            return 1.0
        if callable(self.de):
            try:
                return max(0.0, min(1.0, float(self.de())))
            except Exception:
                return 0.0
        if getattr(self.de, 'vivo', True) is False:
            return 0.0
        maxima = getattr(self.de, 'vida_maxima', 0) or 1
        return max(0.0, min(1.0, self.de.vida / maxima))

    def dibujar(self):
        from pyglet.shapes import Rectangle
        if self._fondo is None:
            self._fondo = Rectangle(0, 0, 1, 1)
            self._relleno = Rectangle(0, 0, 1, 1)
        fr = self.fraccion()
        self._fondo.x, self._fondo.y = self._x, self._y
        self._fondo.width, self._fondo.height = self.ancho, self.alto
        self._fondo.color = colores.gris_oscuro
        self._relleno.x, self._relleno.y = self._x + 1, self._y + 1
        self._relleno.width = max(0, (self.ancho - 2) * fr)
        self._relleno.height = max(0, self.alto - 2)
        if self.color_fijo is not None:
            c = self.color_fijo
        elif fr > 0.5:
            c = colores.verde
        elif fr > 0.25:
            c = colores.amarillo
        else:
            c = colores.rojo
        self._relleno.color = (c[0], c[1], c[2])
        self._fondo.draw()
        if fr > 0:
            self._relleno.draw()
