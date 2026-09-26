# -*- encoding: utf-8 -*-
"""Cámara de la escena.

Equivalente a ``pilasengine.escenas.camara`` pero en 3D: tiene una
posición (x, y, z) y un ``objetivo`` hacia el que mira.
"""

from pyglet.math import Mat4, Vec3


class Camara(object):
    def __init__(self, escena, x=0, y=5, z=12, objetivo=(0, 0, 0)):
        self.escena = escena
        self.x = x
        self.y = y
        self.z = z
        self.objetivo = objetivo

    @property
    def posicion(self):
        return (self.x, self.y, self.z)

    @posicion.setter
    def posicion(self, valor):
        self.x, self.y, self.z = valor

    def matriz_vista(self):
        """Retorna la matriz view para el shader."""
        return Mat4.look_at(
            Vec3(self.x, self.y, self.z),
            Vec3(*self.objetivo),
            Vec3(0, 1, 0),
        )
