# -*- encoding: utf-8 -*-
"""Patrullar: recorre una lista de puntos en loop.

    >>> guardia.aprender(pilas.habilidades.Patrullar,
    ...                  puntos=[(0, 0), (5, 0), (5, 5)],
    ...                  velocidad=2.0)

El actor camina de punto en punto y vuelve al primero al terminar.
``guardia.puntos_patrulla`` y ``guardia.indice_patrulla`` quedan
visibles para depurar o combinar con otros comportamientos.
"""

import math

from pilas3d.habilidades.habilidad import Habilidad


class Patrullar(Habilidad):
    """Camina en circuito por waypoints (x, z)."""

    def iniciar(self, receptor, puntos, velocidad=2.0, ida_y_vuelta=False):
        super(Patrullar, self).iniciar(receptor)
        #: Lista de waypoints ``[(x, z), ...]`` que recorre en loop.
        receptor.puntos_patrulla = [tuple(p) for p in puntos]
        #: Índice del waypoint actual.
        receptor.indice_patrulla = 0
        #: Metros por segundo.
        receptor.velocidad = velocidad
        #: True va y vuelve (0→n→0); False reinicia el circuito.
        self.ida_y_vuelta = ida_y_vuelta
        self._direccion = 1

    def actualizar(self):
        r = self.receptor
        puntos = r.puntos_patrulla
        if not puntos or not r.esta_en_escena():
            return
        tx, tz = puntos[r.indice_patrulla]
        dx, dz = tx - r.x, tz - r.z
        dist = math.hypot(dx, dz)
        if dist < 0.15:
            self._siguiente(r)
            return
        paso = min(r.velocidad * self.pilas.dt, dist)
        r.x += dx / dist * paso
        r.z += dz / dist * paso
        r.mirar_hacia(tx, tz)

    def _siguiente(self, r):
        n = len(r.puntos_patrulla)
        if self.ida_y_vuelta and n > 1:
            # ping-pong: 0,1,...,n-1,n-2,...,1,0,...
            r.indice_patrulla += self._direccion
            if r.indice_patrulla >= n - 1 or r.indice_patrulla <= 0:
                self._direccion = -self._direccion
                r.indice_patrulla = max(0, min(n - 1,
                                             r.indice_patrulla))
        else:
            r.indice_patrulla = (r.indice_patrulla + 1) % n
