# -*- encoding: utf-8 -*-
"""Escena base: contenedor de actores, cámara y color de fondo.

Para hacer una escena propia se hereda de esta clase y se redefinen
los métodos ``iniciar``, ``cuando_actualiza``, ``cuando_pulsa_tecla``
y ``terminar`` — igual que en pilas-engine::

    class Menu(pilas3d.escenas.Escena):
        def iniciar(self):
            self.pilas.actores.Texto('ENTER para jugar')

        def cuando_pulsa_tecla(self, simbolo):
            if simbolo == key.ENTER:
                Juego(self.pilas)

    pilas.escenas.vincular(Menu)
    pilas.escenas.Menu()          # crear una escena la activa sola
"""

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
        from pilas3d.luces import Luces
        self.luces = Luces()
        self.niebla = None  # o (color, inicio, fin) para niebla lineal
        self.sombras = True  # shadow map de la luz direccional
        self.pilas._definir_escena(self)
        self.iniciar()

    def iniciar(self):
        """Se invoca una vez, al activarse la escena. Redefinible."""

    def terminar(self):
        """Se invoca cuando otra escena la reemplaza. Redefinible."""

    def cuando_actualiza(self):
        """Se invoca en cada frame, tras actores y tareas."""

    def cuando_pulsa_tecla(self, simbolo):
        """Se invoca al pulsar una tecla (tras los atajos globales)."""

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
        self.camara.actualizar(dt)   # seguimiento de cámara, si hay
        self.cuando_actualiza()

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
