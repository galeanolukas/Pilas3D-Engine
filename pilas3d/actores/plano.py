# -*- encoding: utf-8 -*-

from pilas3d import mallas
from pilas3d.actores.actor import Actor


class Plano(Actor):
    """Cuadrado horizontal sobre el piso; ideal para textura de suelo.

    >>> piso = pilas.actores.Plano(ancho=20, profundidad=20)
    >>> piso.imagen = 'pasto.png'
    """

    def __init__(self, pilas, x=0, y=0, z=0, ancho=20, profundidad=20):
        self.ancho = ancho
        self.profundidad = profundidad
        super(Plano, self).__init__(pilas, x=x, y=y, z=z)

    def _generar_geometria(self):
        return mallas.plano(self.ancho, self.profundidad)
