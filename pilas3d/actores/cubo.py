# -*- encoding: utf-8 -*-

from pilas3d import mallas
from pilas3d.actores.actor import Actor


class Cubo(Actor):
    """Un cubo de lado 1 centrado en su posición."""

    def __init__(self, pilas, x=0, y=0, z=0):
        super(Cubo, self).__init__(pilas, x=x, y=y, z=z)
        self.radio_de_colision = 0.87

    def _generar_geometria(self):
        return mallas.cubo(1.0)
