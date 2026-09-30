# -*- encoding: utf-8 -*-
"""Perseguir a otro actor evitando obstáculos (A* sobre grilla).

Port de ``pilasengine.habilidades.PerseguirAOtroActor``: en lugar de
ir derecho al objetivo (``SeguirAlActor``), calcula un camino por la
grilla que esquiva paredes y bloques.
"""

import heapq
import math

from pilas3d import colisiones
from pilas3d.habilidades.habilidad import Habilidad


class PerseguirAOtroActor(Habilidad):
    """Persigue a ``actor`` esquivando los obstáculos de la escena.

    >>> enemigo.aprender(pilas.habilidades.PerseguirAOtroActor,
    ...                  actor=jugador, velocidad=3)

    La grilla se construye con ``escena.obstaculos`` (o la lista
    ``obstaculos=`` dada). Sin obstáculos, va derecho como
    ``SeguirAlActor``.
    """

    def iniciar(self, receptor, actor, velocidad=3.0,
                tam_celda=1.0, obstaculos=None, cada=0.4):
        super(PerseguirAOtroActor, self).iniciar(receptor)
        self.actor = actor
        self.velocidad = velocidad
        self.tam_celda = tam_celda
        self.obstaculos = obstaculos
        self.cada = cada
        self._camino = []        # waypoints (x, z) restantes
        self._espera = 0.0
        self._cajas = None       # cache de obstáculos

    # -- grilla -------------------------------------------------------------

    def _caja(self, o):
        if hasattr(o, 'obtener_caja'):
            return o.obtener_caja()
        ancho = getattr(o, 'ancho', o.radio_de_colision)
        prof = getattr(o, 'profundidad', ancho)
        return colisiones.caja_desde_actor(
            o, ancho * o.escala_x, prof * o.escala_z)

    def _construir_grilla(self, x0, z0, x1, z1):
        """Grilla booleana: True = libre. Cubre obstáculos + origen y
        destino, con margen."""
        c = self.tam_celda
        obst = (self.obstaculos if self.obstaculos is not None
                else self.pilas.escena_actual().obstaculos)
        escena = self.pilas.escena_actual()
        cajas = [self._caja(o) for o in obst if o in escena.actores]

        xs = [x0, x1] + [v for caja in cajas for v in (caja[0], caja[1])]
        zs = [z0, z1] + [v for caja in cajas for v in (caja[2], caja[3])]
        min_x = math.floor(min(xs) / c) - 2
        min_z = math.floor(min(zs) / c) - 2
        max_x = math.ceil(max(xs) / c) + 2
        max_z = math.ceil(max(zs) / c) + 2

        margen = self.receptor.radio_de_colision * 0.5
        grilla = []
        for i in range(min_x, max_x + 1):
            fila = []
            for j in range(min_z, max_z + 1):
                cx, cz = (i + 0.5) * c, (j + 0.5) * c
                libre = all(not (a - margen <= cx <= b + margen and
                                 p - margen <= cz <= q + margen)
                            for a, b, p, q in cajas)
                fila.append(libre)
            grilla.append(fila)
        return grilla, min_x, min_z

    def _celda(self, x, z, min_x, min_z):
        c = self.tam_celda
        return (int(math.floor(x / c)) - min_x,
                int(math.floor(z / c)) - min_z)

    @staticmethod
    def _astar(grilla, inicio, meta):
        """A* 8-direccional sobre la grilla; devuelve lista de celdas."""
        def vecinos(n):
            i, j = n
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                ni, nj = i + di, j + dj
                if not (0 <= ni < len(grilla) and
                        0 <= nj < len(grilla[0])):
                    continue
                if not grilla[ni][nj]:
                    continue
                # no cortar esquinas en diagonal
                if di and dj and not (
                        grilla[i + di][j] and grilla[i][j + dj]):
                    continue
                yield (ni, nj)

        def h(n):
            return math.hypot(n[0] - meta[0], n[1] - meta[1])

        frente = [(h(inicio), 0.0, inicio)]
        vino_de = {inicio: None}
        costo = {inicio: 0.0}
        while frente:
            _, g, n = heapq.heappop(frente)
            if n == meta:
                camino = []
                while n is not None:
                    camino.append(n)
                    n = vino_de[n]
                return camino[::-1]
            if g > costo.get(n, 1e18):
                continue
            for v in vecinos(n):
                ng = g + math.hypot(v[0] - n[0], v[1] - n[1])
                if ng < costo.get(v, 1e18):
                    costo[v] = ng
                    vino_de[v] = n
                    heapq.heappush(frente, (ng + h(v), ng, v))
        return None

    def _recalcular(self):
        r, a = self.receptor, self.actor
        grilla, min_x, min_z = self._construir_grilla(
            r.x, r.z, a.x, a.z)
        inicio = self._celda(r.x, r.z, min_x, min_z)
        meta = self._celda(a.x, a.z, min_x, min_z)
        # si inicio/meta cae en celda bloqueada, liberarla
        for (i, j) in (inicio, meta):
            if 0 <= i < len(grilla) and 0 <= j < len(grilla[0]):
                grilla[i][j] = True
        camino = self._astar(grilla, inicio, meta)
        c = self.tam_celda
        self._camino = [((i + min_x + 0.5) * c, (j + min_z + 0.5) * c)
                        for i, j in (camino or [])][1:]

    # -- comportamiento ------------------------------------------------------

    def actualizar(self):
        if not self.actor.esta_en_escena():
            return
        r = self.receptor
        dt = self.pilas.dt

        self._espera -= dt
        if self._espera <= 0:
            self._espera = self.cada
            self._recalcular()

        if not self._camino:
            return
        tx, tz = self._camino[0]
        dx, dz = tx - r.x, tz - r.z
        d = math.hypot(dx, dz)
        paso = self.velocidad * dt
        if d <= paso:
            r.x, r.z = tx, tz
            self._camino.pop(0)
            return
        r.x += dx / d * paso
        r.z += dz / d * paso
        r.mirar_hacia(tx, tz)
