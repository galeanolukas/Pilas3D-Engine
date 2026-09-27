# -*- encoding: utf-8 -*-

import math

from pilas3d.habilidades.habilidad import Habilidad


class MoverseComoCoche(Habilidad):
    """Conduce al actor como un coche: izquierda/derecha giran,
    arriba/abajo avanzan y retroceden en la dirección actual.

    >>> auto.aprender(pilas.habilidades.MoverseComoCoche,
    ...               velocidad=8, velocidad_giro=120)
    """

    def iniciar(self, receptor, velocidad=8, velocidad_giro=120):
        super(MoverseComoCoche, self).iniciar(receptor)
        self.velocidad = velocidad
        self.velocidad_giro = velocidad_giro

    def actualizar(self):
        r = self.receptor
        c = self.pilas.control
        dt = self.pilas.dt

        if c.izquierda:
            r.rotacion_y += self.velocidad_giro * dt
        if c.derecha:
            r.rotacion_y -= self.velocidad_giro * dt

        avance = 0.0
        if c.arriba:
            avance += self.velocidad * dt
        if c.abajo:
            avance -= self.velocidad * dt
        if avance:
            yaw = math.radians(r.rotacion_y)
            r.x += -math.sin(yaw) * avance
            r.z += -math.cos(yaw) * avance
