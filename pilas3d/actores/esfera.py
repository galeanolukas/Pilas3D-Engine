# -*- encoding: utf-8 -*-

from pilas3d import mallas
from pilas3d.actores.actor import Actor


class Esfera(Actor):
    """Una esfera de radio configurable centrada en su posición."""

    def __init__(self, pilas, x=0, y=0, z=0, radio=1.0):
        self.radio = radio
        super(Esfera, self).__init__(pilas, x=x, y=y, z=z)
        self.radio_de_colision = radio

    def _generar_geometria(self):
        return mallas.esfera(self.radio)
