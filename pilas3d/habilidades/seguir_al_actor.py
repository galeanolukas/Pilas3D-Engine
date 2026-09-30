# -*- encoding: utf-8 -*-

import math

from pilas3d.habilidades.habilidad import Habilidad


class SeguirAlActor(Habilidad):
    """Persigue a otro actor sobre el plano XZ.

    >>> enemigo.aprender(pilas.habilidades.SeguirAlActor,
    ...                  actor=jugador, velocidad=3,
    ...                  distancia_minima=1.0)
    """

    def iniciar(self, receptor, actor, velocidad=3,
                distancia_minima=0.0):
        super(SeguirAlActor, self).iniciar(receptor)
        self.actor = actor
        self.velocidad = velocidad
        self.distancia_minima = distancia_minima

    def actualizar(self):
        if self.actor not in self.pilas.escena_actual().actores:
            return
        r = self.receptor
        dx = self.actor.x - r.x
        dz = self.actor.z - r.z
        d = math.sqrt(dx * dx + dz * dz)
        if d <= self.distancia_minima or d < 1e-9:
            return
        v = self.velocidad * self.pilas.dt
        r.x += dx / d * v
        r.z += dz / d * v
        r.mirar_hacia(self.actor.x, self.actor.z)
