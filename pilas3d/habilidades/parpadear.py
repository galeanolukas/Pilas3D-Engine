# -*- encoding: utf-8 -*-
"""Parpadear: la luz de una Lampara titila como fuego o velada.

    >>> antorcha = pilas.actores.Lampara(color=pilas.colores.naranja)
    >>> antorcha.aprender(pilas.habilidades.Parpadear,
    ...                   intensidad=0.25, velocidad=8)

Modula el ``alcance`` de la luz con saltos aleatorios suaves — la
sensación de llama viene del radio que crece y se achica, no del
color. Sirve para antorchas, velas, fuegos, luces rotas. Con
``intensidad=0`` queda fija.
"""

import random

from pilas3d.habilidades.habilidad import Habilidad


class Parpadear(Habilidad):
    """Hace titilar la ``luz`` del actor (una ``Lampara``)."""

    def iniciar(self, receptor, intensidad=0.2, velocidad=10.0):
        super(Parpadear, self).iniciar(receptor)
        #: 0..1 — cuánto varía el alcance en cada salto.
        receptor.intensidad_parpadeo = intensidad
        #: Saltos por segundo (10 se siente como llama).
        receptor.velocidad_parpadeo = velocidad
        luz = getattr(receptor, 'luz', None)
        receptor._alcance_base = luz.alcance if luz else 1.0
        receptor._espera_parpadeo = 0.0

    def actualizar(self):
        r = self.receptor
        luz = getattr(r, 'luz', None)
        if luz is None:
            return
        r._espera_parpadeo -= self.pilas.dt
        if r._espera_parpadeo > 0:
            return
        r._espera_parpadeo = 1.0 / max(r.velocidad_parpadeo, 0.1)
        base = r._alcance_base
        luz.alcance = base * (1.0 + random.uniform(
            -r.intensidad_parpadeo, r.intensidad_parpadeo))
