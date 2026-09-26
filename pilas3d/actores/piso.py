# -*- encoding: utf-8 -*-

from pilas3d import mallas, colores
from pilas3d.actores.actor import Actor


class Piso(Actor):
    """Rejilla de referencia sobre el plano XZ."""

    def __init__(self, pilas, x=0, y=0, z=0, tamano=20, divisiones=20):
        self.tamano = tamano
        self.divisiones = divisiones
        super(Piso, self).__init__(pilas, x=x, y=y, z=z)
        self.color = colores.gris

    def _generar_geometria(self):
        return mallas.rejilla(self.tamano, self.divisiones)
