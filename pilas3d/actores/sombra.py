# -*- encoding: utf-8 -*-
"""Sombra falsa tipo "blob": un disco oscuro bajo un actor.

Técnica clásica de los juegos de los 90 (la del Doom era más compleja,
pero esta es la versión didáctica): un círculo semitransparente que
sigue al actor pegado al piso.

>>> arbol = pilas.actores.Modelo('arbol.obj')
>>> pilas.actores.Sombra(arbol)
"""

from pilas3d import mallas, colores
from pilas3d.actores.actor import Actor


class Sombra(Actor):
    """Disco oscuro que sigue a un actor en el piso (y=0.02)."""

    def __init__(self, pilas, dueno, radio=None, opacidad=60):
        super(Sombra, self).__init__(pilas)
        self.dueno = dueno
        self.radio = (radio if radio is not None
                      else dueno.radio_de_colision)
        self.color = colores.negro
        self.transparencia = opacidad
        self.escala = self.radio
        self.radio_de_colision = 0.0
        self.y = 0.02

    def _generar_geometria(self):
        return mallas.disco(1.0)

    def actualizar(self):
        if self.dueno not in self.pilas.escena_actual().actores:
            self.eliminar()
            return
        self.x = self.dueno.x
        self.z = self.dueno.z
