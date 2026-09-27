# -*- encoding: utf-8 -*-
"""SeguirAlMouse: el actor sigue al puntero del mouse.

Equivalente en 3D de seguir al puntero en pilas 2D: proyecta el rayo
del mouse sobre el plano horizontal ``y_plano`` (por defecto la
altura inicial del actor) y el actor se mueve hacia ese punto.
"""

import math

from pilas3d.habilidades.habilidad import Habilidad


class SeguirAlMouse(Habilidad):
    """El actor se mueve hacia donde apunta el mouse sobre el suelo.

    >>> guia.aprender(pilas.habilidades.SeguirAlMouse, velocidad=5)

    Con ``velocidad=0`` (default) se teletransporta al punto; con
    velocidad > 0 camina hacia él orientado.
    """

    def iniciar(self, receptor, velocidad=0, y_plano=None):
        super(SeguirAlMouse, self).iniciar(receptor)
        self.velocidad = velocidad
        self.y_plano = receptor.y if y_plano is None else y_plano

    def actualizar(self):
        punto = self.pilas.escena.camara.punto_bajo_mouse(
            self.y_plano)
        if punto is None:
            return

        dx = punto[0] - self.receptor.x
        dz = punto[2] - self.receptor.z
        dist = math.sqrt(dx * dx + dz * dz)
        self.receptor.y = punto[1]
        if dist < 1e-6:
            return
        self.receptor.rotacion_y = math.degrees(math.atan2(dx, dz))

        paso = self.velocidad * self.pilas.dt
        if self.velocidad <= 0 or dist <= paso:
            self.receptor.x = punto[0]
            self.receptor.z = punto[2]
        else:
            self.receptor.x += dx / dist * paso
            self.receptor.z += dz / dist * paso
