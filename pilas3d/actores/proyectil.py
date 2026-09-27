# -*- encoding: utf-8 -*-
"""Proyectil: actor que sale disparado en línea recta.

Se usa con ``habilidades.Disparar`` o directo::

    pilas.actores.Proyectil(direccion=(0, 0, 1), velocidad=20)

El proyectil avanza cada frame, se elimina al recorrer ``alcance``
unidades, y si recibe ``objetivos`` (lista de actores) choca contra
ellos: llama a ``cuando_impacta(proyectil, actor)`` y desaparece.
"""

import math

from pilas3d import colores
from pilas3d.actores.actor import Actor
from pilas3d import mallas


class Proyectil(Actor):
    """Disparo que viaja en línea recta y muere al impactar/agotarse."""

    def __init__(self, pilas, direccion=(0, 0, 1), velocidad=20.0,
                 alcance=40.0, objetivos=None, cuando_impacta=None,
                 ignorar=None, radio=0.15, color=None, x=0, y=0, z=0,
                 **kw):
        super(Proyectil, self).__init__(pilas, x=x, y=y, z=z, **kw)
        self.direccion = direccion
        self.velocidad = velocidad
        self.alcance = alcance
        self.objetivos = objetivos
        self.cuando_impacta = cuando_impacta
        self.ignorar = ignorar
        self.radio = radio
        self.radio_de_colision = radio
        self.radio_de_disparo = radio
        if color is not None:
            self.color = color
        else:
            self.color = colores.amarillo
        self._recorrido = 0.0

    def _generar_geometria(self):
        return mallas.esfera(self.radio, meridianos=8, paralelos=6)

    def actualizar(self):
        dx, dy, dz = self.direccion
        n = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        paso = self.velocidad * self.pilas.dt
        self.x += dx / n * paso
        self.y += dy / n * paso
        self.z += dz / n * paso
        self._recorrido += paso

        if self.objetivos:
            for actor in list(self.objetivos):
                if actor is self.ignorar or not actor.esta_en_escena():
                    continue
                if self.colisiona_con(actor):
                    if self.cuando_impacta:
                        self.cuando_impacta(self, actor)
                    self.eliminar()
                    return

        if self._recorrido >= self.alcance:
            self.eliminar()
