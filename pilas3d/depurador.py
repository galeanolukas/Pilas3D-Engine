# -*- encoding: utf-8 -*-
"""Depurador: ayudas visuales sobre la escena.

Equivalente a ``pilas.depurador`` de pilas-engine. Uso::

    pilas.depurador.definir_modos(radios_de_colision=True,
                                puntos_de_control=True,
                                fps=True, ejes=True)
"""

from pyglet.gl import GL_LINES
from pyglet.math import Mat4, Vec3

from pilas3d import mallas, shaders


class Depurador(object):
    def __init__(self, pilas):
        self.pilas = pilas
        self.radios_de_colision = False
        self.puntos_de_control = False
        self._vlist_esfera = None
        self._vlist_ejes = None

    def definir_modos(self, fps=None, ejes=None, radios_de_colision=None,
                      puntos_de_control=None):
        """Activa/desactiva modos de depuración (None = no tocar)."""
        if fps is not None:
            self.pilas.fps.ver() if fps else self.pilas.fps.ocultar()
        if ejes is not None:
            self.pilas.mostrar_ejes() if ejes else self.pilas.ocultar_ejes()
        if radios_de_colision is not None:
            self.radios_de_colision = radios_de_colision
        if puntos_de_control is not None:
            self.puntos_de_control = puntos_de_control

    def activo(self):
        return self.radios_de_colision or self.puntos_de_control

    def _obtener_esfera_wire(self):
        if self._vlist_esfera is None:
            pos, nor, modo, col = mallas.esfera_alambrada(1.0)
            self._vlist_esfera = shaders.obtener_programa().vertex_list(
                len(pos) // 3, modo,
                position=("f", pos), normal=("f", nor), color=("f", col))
        return self._vlist_esfera

    def _obtener_ejes(self):
        if self._vlist_ejes is None:
            pos, nor, modo, col = mallas.ejes(1.0)
            self._vlist_ejes = shaders.obtener_programa().vertex_list(
                len(pos) // 3, modo,
                position=("f", pos), normal=("f", nor), color=("f", col))
        return self._vlist_ejes

    def dibujar(self, actores):
        """Dibuja las ayudas de debug dentro del pase 3D."""
        programa = shaders.obtener_programa()
        for actor in actores:
            if actor.es_overlay:
                continue
            traslacion = Mat4.from_translation(Vec3(*actor.posicion))

            if self.radios_de_colision:
                r = actor.radio_de_colision
                programa["modelo"] = traslacion @ Mat4.from_scale(
                    Vec3(r, r, r))
                self._obtener_esfera_wire().draw(GL_LINES)

            if self.puntos_de_control:
                programa["modelo"] = traslacion @ Mat4.from_scale(
                    Vec3(1.5, 1.5, 1.5))
                self._obtener_ejes().draw(GL_LINES)
