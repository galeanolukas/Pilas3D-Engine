# -*- encoding: utf-8 -*-

import math

from pilas3d.habilidades.habilidad import Habilidad


class MoverseEnCirculo(Habilidad):
    """Orbita alrededor de un centro (x, z) o de otro actor.

    >>> luna.aprender(pilas.habilidades.MoverseEnCirculo,
    ...                  centro=tierra, radio=8, velocidad=45)

    ``velocidad`` son grados por segundo.
    """

    def iniciar(self, receptor, centro=(0, 0), radio=3.0,
                velocidad=60, angulo=0.0):
        super(MoverseEnCirculo, self).iniciar(receptor)
        self.centro = centro
        self.radio = radio
        self.velocidad = velocidad
        self.angulo = math.radians(angulo)

    def actualizar(self):
        self.angulo += math.radians(self.velocidad * self.pilas.dt)
        centro = self.centro
        if hasattr(centro, 'x'):       # orbita alrededor de un actor
            cx, cz = centro.x, centro.z
        else:                          # tupla/punto fijo
            cx, cz = centro[0], centro[1]
        r = self.receptor
        r.x = cx + math.cos(self.angulo) * self.radio
        r.z = cz + math.sin(self.angulo) * self.radio
