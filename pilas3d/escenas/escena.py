# -*- encoding: utf-8 -*-
"""Escena base: contenedor de actores, cámara y color de fondo."""

from pilas3d import colores
from pilas3d.escenas.camara import Camara


class Escena(object):
    def __init__(self, pilas):
        self.pilas = pilas
        self.actores = []
        self.camara = Camara(self)
        self.fondo = colores.gris_oscuro
        self.pilas._definir_escena(self)

    def agregar_actor(self, actor):
        self.actores.append(actor)

    def eliminar_actor(self, actor):
        if actor in self.actores:
            self.actores.remove(actor)

    def actualizar(self, dt):
        """Llama a ``actualizar`` de cada actor, ~60 veces por segundo."""
        for actor in list(self.actores):
            actor.actualizar()

    def dibujar(self):
        for actor in list(self.actores):
            actor.dibujar()
