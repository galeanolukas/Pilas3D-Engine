# -*- encoding: utf-8 -*-

import math

from pilas3d.habilidades.habilidad import Habilidad


class MoverseConElTeclado(Habilidad):
    """Mueve al actor sobre el plano XZ con flechas o WASD,
    **relativo a la cámara**: ``arriba`` es alejarse de ella,
    ``derecha`` su derecha en pantalla. Así anda igual con cámara
    fija, orbital o de seguimiento en tercera persona.

    >>> cubo.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=10)
    """

    def iniciar(self, receptor, velocidad=8):
        super(MoverseConElTeclado, self).iniciar(receptor)
        self.velocidad = velocidad

    def actualizar(self):
        c = self.pilas.control
        v = self.velocidad * self.pilas.dt
        r = self.receptor
        # frente de la cámara proyectado al suelo (plano XZ)
        d = self.pilas.escena_actual().camara.direccion()
        fx, fz = d.x, d.z
        norma = math.hypot(fx, fz)
        if norma < 1e-4:                       # cámara cenital
            fx, fz = 0.0, -1.0
        else:
            fx, fz = fx / norma, fz / norma
        rx, rz = -fz, fx                        # derecha = frente x up
        if c.arriba:
            r.x += fx * v
            r.z += fz * v
        if c.abajo:
            r.x -= fx * v
            r.z -= fz * v
        if c.derecha:
            r.x += rx * v
            r.z += rz * v
        if c.izquierda:
            r.x -= rx * v
            r.z -= rz * v
