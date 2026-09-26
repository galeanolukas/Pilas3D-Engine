# -*- encoding: utf-8 -*-

from pilas3d.habilidades.habilidad import Habilidad


class MoverseConElTeclado(Habilidad):
    """Mueve al actor sobre el plano XZ con flechas o WASD.

    >>> cubo.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=10)
    """

    def iniciar(self, receptor, velocidad=8):
        super(MoverseConElTeclado, self).iniciar(receptor)
        self.velocidad = velocidad

    def actualizar(self):
        c = self.pilas.control
        v = self.velocidad * self.pilas.dt
        r = self.receptor
        if c.izquierda:
            r.x -= v
        if c.derecha:
            r.x += v
        if c.arriba:
            r.z -= v
        if c.abajo:
            r.z += v
