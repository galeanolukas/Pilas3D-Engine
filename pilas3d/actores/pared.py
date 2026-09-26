# -*- encoding: utf-8 -*-

import math

from pilas3d import mallas, colores
from pilas3d.actores.actor import Actor


class Pared(Actor):
    """Una pared: prisma de ancho, alto y profundidad configurables.

    Por omisión se apoya sobre el piso (su centro queda en y = alto/2).
    Para hacer una pared lateral, rotarla::

        pared = pilas.actores.Pared(x=-5)
        pared.rotacion_y = 90
    """

    def __init__(self, pilas, x=0, y=None, z=0,
                 ancho=4.0, alto=3.0, profundidad=0.3):
        self.ancho = ancho
        self.alto = alto
        self.profundidad = profundidad
        if y is None:
            y = alto / 2.0
        super(Pared, self).__init__(pilas, x=x, y=y, z=z)
        self.color = colores.gris
        # Esfera envolvente: media diagonal del prisma.
        self.radio_de_colision = math.sqrt(
            ancho ** 2 + alto ** 2 + profundidad ** 2) / 2.0
        escena = pilas.escena_actual()
        if escena is not None:
            escena.obstaculos.append(self)

    def obtener_caja(self):
        """AABB (min_x, max_x, min_z, max_z) para colisiones de suelo."""
        from pilas3d import colisiones

        return colisiones.caja_desde_actor(
            self, self.ancho, self.profundidad)

    def _generar_geometria(self):
        return mallas.cuboide(self.ancho, self.alto, self.profundidad)
