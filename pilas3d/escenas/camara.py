# -*- encoding: utf-8 -*-
"""Cámara de la escena.

Equivalente a ``pilasengine.escenas.camara`` pero en 3D: tiene una
posición (x, y, z) y un ``objetivo`` hacia el que mira.

Además ofrece ``usar_control_orbital()``: con el botón izquierdo del
mouse se orbita alrededor del objetivo y con la rueda se acerca/aleja.
"""

import math

from pyglet.math import Mat4, Vec3
from pyglet.window import mouse


class Camara(object):
    def __init__(self, escena, x=0, y=5, z=12, objetivo=(0, 0, 0)):
        self.escena = escena
        self.x = x
        self.y = y
        self.z = z
        self.objetivo = objetivo
        self._orbital = False
        self._orbital_distancia = 0.0
        self._orbital_yaw = 0.0
        self._orbital_pitch = 0.0

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

    # -- control orbital con el mouse -------------------------------------

    def usar_control_orbital(self):
        """Activa órbita con botón izquierdo + zoom con la rueda.

        La cámara gira siempre alrededor de ``self.objetivo``.
        """
        ox, oy, oz = self.objetivo
        dx, dy, dz = self.x - ox, self.y - oy, self.z - oz
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        self._orbital_distancia = d
        self._orbital_pitch = math.degrees(math.asin(dy / d))
        self._orbital_yaw = math.degrees(math.atan2(dx, dz))
        self._orbital = True

        ventana = self.escena.pilas.ventana
        if ventana is not None:
            ventana.push_handlers(
                on_mouse_drag=self._on_mouse_drag,
                on_mouse_scroll=self._on_mouse_scroll,
            )

    def _on_mouse_drag(self, x, y, dx, dy, botones, modificadores):
        if not (botones & mouse.LEFT):
            return
        self._orbital_yaw += dx * 0.4
        self._orbital_pitch = max(
            -89.0, min(89.0, self._orbital_pitch + dy * 0.4))
        self._actualizar_orbita()

    def _on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self._orbital_distancia = max(
            1.0, min(200.0,
                     self._orbital_distancia * (1.0 - scroll_y * 0.1)))
        self._actualizar_orbita()

    def _actualizar_orbita(self):
        ox, oy, oz = self.objetivo
        pitch = math.radians(self._orbital_pitch)
        yaw = math.radians(self._orbital_yaw)
        d = self._orbital_distancia
        self.x = ox + d * math.cos(pitch) * math.sin(yaw)
        self.y = oy + d * math.sin(pitch)
        self.z = oz + d * math.cos(pitch) * math.cos(yaw)
