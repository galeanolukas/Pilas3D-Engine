# -*- encoding: utf-8 -*-

from pilas3d import mallas
from pilas3d.actores.actor import Actor


class Ejes(Actor):
    """Los tres ejes de coordenadas: X rojo, Y verde, Z azul."""

    def __init__(self, pilas, x=0, y=0, z=0, largo=5):
        self.largo = largo
        super(Ejes, self).__init__(pilas, x=x, y=y, z=z)

    def _generar_geometria(self):
        return mallas.ejes(self.largo)
