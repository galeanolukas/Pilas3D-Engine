# -*- encoding: utf-8 -*-
"""Ventana principal: reemplaza al QGLWidget de pilas-engine 2D."""

import pyglet
from pyglet.gl import (
    glEnable,
    glDisable,
    glClearColor,
    GL_DEPTH_TEST,
)
from pyglet.math import Mat4
from pyglet.window import key

from pilas3d import shaders
from pilas3d import colores


class Ventana(pyglet.window.Window):
    """Ventana con contexto OpenGL donde se dibuja la escena 3D."""

    def __init__(self, pilas, ancho=640, alto=480, titulo="pilas3d"):
        super(Ventana, self).__init__(
            width=ancho, height=alto, caption=titulo, resizable=True
        )
        self.pilas = pilas
        self.set_minimum_size(160, 120)
        glEnable(GL_DEPTH_TEST)

        self.teclas = key.KeyStateHandler()
        self.push_handlers(self.teclas)
        self._fps_display = None

    def on_draw(self):
        escena = self.pilas.escena_actual()
        fondo = colores.normalizar(escena.fondo)
        glClearColor(fondo[0], fondo[1], fondo[2], 1.0)
        self.clear()

        programa = shaders.obtener_programa()
        aspecto = self.width / float(self.height)

        with programa:
            programa["proyeccion"] = Mat4.perspective_projection(
                aspecto, 0.1, 1000.0, fov=60
            )
            programa["vista"] = escena.camara.matriz_vista()
            escena.dibujar()

        if escena.tiene_overlays() or self.pilas._fps_visible:
            glDisable(GL_DEPTH_TEST)
            self.projection = Mat4.orthogonal_projection(
                0, self.width, 0, self.height, -255, 255
            )
            self.view = Mat4()
            escena.dibujar_overlay()
            if self.pilas._fps_visible:
                if self._fps_display is None:
                    self._fps_display = pyglet.window.FPSDisplay(self)
                self._fps_display.draw()
            glEnable(GL_DEPTH_TEST)
