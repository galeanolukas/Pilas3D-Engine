# -*- encoding: utf-8 -*-

import math

from pilas3d.habilidades.habilidad import Habilidad


class MirarAlActor(Habilidad):
    """Gira al actor para que "mire" siempre a otro actor.

    >>> torreta.aprender(pilas.habilidades.MirarAlActor, actor=jugador)
    """

    def iniciar(self, receptor, actor):
        super(MirarAlActor, self).iniciar(receptor)
        self.actor = actor

    def actualizar(self):
        if self.actor not in self.pilas.escena_actual().actores:
            return
        r = self.receptor
        dx = self.actor.x - r.x
        dz = self.actor.z - r.z
        if dx or dz:
            r.mirar_hacia(self.actor.x, self.actor.z)
