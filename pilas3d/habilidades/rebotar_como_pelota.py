# -*- encoding: utf-8 -*-

from pilas3d.habilidades.habilidad import Habilidad


class RebotarComoPelota(Habilidad):
    """Gravedad sobre el eje Y y rebote contra el piso (y = radio).

    Versión 3D simplificada de la habilidad original (que usaba Box2D).

    >>> moneda.aprender(pilas.habilidades.RebotarComoPelota)
    """

    def iniciar(self, receptor, velocidad_inicial=10):
        super(RebotarComoPelota, self).iniciar(receptor)
        self.velocidad_y = velocidad_inicial
        self.gravedad = -30.0
        self.rebote = 0.7

    def actualizar(self):
        r = self.receptor
        dt = self.pilas.dt
        self.velocidad_y += self.gravedad * dt
        r.y += self.velocidad_y * dt

        altura_piso = r.radio_de_colision
        if r.y <= altura_piso:
            r.y = altura_piso
            self.velocidad_y = -self.velocidad_y * self.rebote
            if abs(self.velocidad_y) < 0.8:
                self.velocidad_y = 0.0
