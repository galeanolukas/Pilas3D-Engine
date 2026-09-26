# -*- encoding: utf-8 -*-
"""Escena base: contenedor de actores, cámara y color de fondo."""

from pilas3d import colores
from pilas3d.escenas.camara import Camara
from pilas3d.tareas import Tareas


class Escena(object):
    def __init__(self, pilas):
        self.pilas = pilas
        self.actores = []
        self.camara = Camara(self)
        self.fondo = colores.gris_oscuro
        self.tareas = Tareas(self, pilas)
        self.obstaculos = []  # actores con caja sólida (p. ej. Pared)
        self.pilas._definir_escena(self)

    def agregar_actor(self, actor):
        self.actores.append(actor)

    def eliminar_actor(self, actor):
        if actor in self.actores:
            self.actores.remove(actor)
        if actor in self.obstaculos:
            self.obstaculos.remove(actor)

    def actualizar(self, dt):
        """Ejecuta tareas, habilidades y ``actualizar`` de cada actor."""
        self.pilas.dt = dt
        self.tareas.actualizar(dt)
        for actor in list(self.actores):
            actor.pre_actualizar()
            actor.actualizar()

    def dibujar(self):
        """Dibuja los actores 3D (los overlays se dibujan aparte)."""
        for actor in list(self.actores):
            if not actor.es_overlay:
                actor.dibujar()
        if self.pilas.depurador.activo():
            self.pilas.depurador.dibujar(self.actores)

    def dibujar_overlay(self):
        """Dibuja los actores de overlay 2D (texto, puntajes)."""
        for actor in list(self.actores):
            if actor.es_overlay:
                actor.dibujar()

    def tiene_overlays(self):
        return any(a.es_overlay for a in self.actores)
