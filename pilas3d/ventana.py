# -*- encoding: utf-8 -*-
"""Ventana principal: reemplaza al QGLWidget de pilas-engine 2D."""

import pyglet
from pyglet.gl import (
    glEnable,
    glDisable,
    glClearColor,
    glBlendFunc,
    glViewport,
    GL_DEPTH_TEST,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
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
        self._poner_icono()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.teclas = key.KeyStateHandler()
        self.push_handlers(self.teclas)
        self._fps_display = None

        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_botones = 0

        #: Área de la ventana donde se dibuja la escena 3D, en
        #: píxeles ``(x, y, ancho, alto)``. ``None`` = toda la
        #: ventana. Sirve para dejar zonas libres para paneles de
        #: interfaz (ver ``actores.Panel``).
        self.area_3d = None

    def _poner_icono(self):
        """Icono de la ventana: el logo del motor (data/logo.png)."""
        import os
        from pyglet.image import load
        ruta = os.path.join(os.path.dirname(__file__), 'data',
                            'logo.png')
        if os.path.exists(ruta):
            self.set_icon(load(ruta))

    def on_key_press(self, simbolo, modificadores):
        """Atajos globales de la ventana.

        - ESC: termina el juego (cierra la ventana)
        - F9:  ejes X/Y/Z del origen
        - F10: radios de colisión (como en pilas 1.x)
        - F11: FPS
        - F12: puntos de control (como en pilas 1.x)
        """
        dep = self.pilas.depurador
        if simbolo == key.ESCAPE:
            self.pilas.terminar()
        elif simbolo == key.F9:
            dep.definir_modos(
                ejes=self.pilas._actor_ejes is None)
        elif simbolo == key.F10:
            dep.definir_modos(
                radios_de_colision=not dep.radios_de_colision)
        elif simbolo == key.F11:
            dep.definir_modos(fps=not self.pilas.fps.visible)
        elif simbolo == key.F12:
            dep.definir_modos(
                puntos_de_control=not dep.puntos_de_control)

        # Despues de los atajos globales, la escena recibe la tecla.
        if simbolo != key.ESCAPE:
            escena = self.pilas.escena_actual()
            if escena is not None:
                escena.cuando_pulsa_tecla(simbolo)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse_x = x
        self.mouse_y = y
        self.mouse_botones |= button

    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse_x = x
        self.mouse_y = y
        self.mouse_botones &= ~button

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x = x
        self.mouse_y = y

    def on_draw(self):
        escena = self.pilas.escena_actual()
        fondo = colores.normalizar(escena.fondo)
        glClearColor(fondo[0], fondo[1], fondo[2], 1.0)
        self.clear()

        programa = shaders.obtener_programa()
        if self.area_3d:
            vx, vy, vw, vh = self.area_3d
            glViewport(int(vx), int(vy), int(vw), int(vh))
            aspecto = vw / float(vh)
        else:
            aspecto = self.width / float(self.height)

        with programa:
            programa["proyeccion"] = Mat4.perspective_projection(
                aspecto, 0.1, 1000.0, fov=60
            )
            programa["vista"] = escena.camara.matriz_vista()
            escena.luces.aplicar(programa)
            programa["cam_pos"] = tuple(escena.camara.posicion)
            niebla = escena.niebla
            programa["usar_niebla"] = niebla is not None
            if niebla is not None:
                color, inicio, fin = niebla
                programa["niebla_color"] = tuple(
                    colores.normalizar(color))
                programa["niebla_inicio"] = float(inicio)
                programa["niebla_fin"] = float(fin)
            escena.dibujar()

        if self.area_3d:
            glViewport(0, 0, self.width, self.height)

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
