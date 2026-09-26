# -*- encoding: utf-8 -*-
"""pilas3d: motor de videojuegos 3D simple, en español.

Inspirado en pilas-engine 1.x (Hugo Ruscitti, LGPLv3): mantiene la API
didáctica (``pilas.actores``, ``pilas.escenas``, ``pilas.ejecutar()``)
pero reemplaza el render QPainter 2D por OpenGL vía pyglet.

Uso básico::

    import pilas3d

    pilas = pilas3d.iniciar()
    cubo = pilas.actores.Cubo()
    pilas.ejecutar()
"""

import os

import pyglet

from pilas3d import colores
from pilas3d.actores import Actores
from pilas3d.control import Control, ControlNulo
from pilas3d.escenas import Escenas
from pilas3d.habilidades import Habilidades
from pilas3d.depurador import Depurador
from pilas3d.sonidos import Sonidos
from pilas3d.musica import _Musica

VERSION = "0.1.0"


class _Fps(object):
    """Acceso a la visualización de FPS: ``pilas.fps.ver()``."""

    def __init__(self, pilas):
        self._pilas = pilas

    def ver(self):
        self._pilas._fps_visible = True

    def ocultar(self):
        self._pilas._fps_visible = False

    @property
    def visible(self):
        return self._pilas._fps_visible


class Pilas(object):
    """Representa el área de juego; es el contenedor principal.

    Al igual que en pilas-engine, este objeto mantiene la escena actual,
    la fábrica de actores y el bucle de juego.
    """

    def __init__(self, ancho=640, alto=480, titulo="pilas3d",
                 sin_ventana=False):
        self.dt = 1 / 60.0
        self._escena_actual = None
        self._actor_ejes = None
        self._fps_visible = False
        self.fps = _Fps(self)

        self.actores = Actores(self)
        self.escenas = Escenas(self)
        self.colores = colores
        self.habilidades = Habilidades()
        self.depurador = Depurador(self)
        self.sonidos = Sonidos(self)
        self.musica = _Musica(self)

        if sin_ventana:
            self.ventana = None
            self.control = ControlNulo()
        else:
            from pilas3d.ventana import Ventana

            self.ventana = Ventana(self, ancho, alto, titulo)
            self.control = Control(self.ventana)

        self.escenas.Normal()

    def escena_actual(self):
        return self._escena_actual

    @property
    def tareas(self):
        """El planificador de tareas de la escena actual."""
        return self._escena_actual.tareas

    def mostrar_ejes(self, largo=50):
        """Muestra los ejes X (rojo), Y (verde) y Z (azul) del origen."""
        if self._actor_ejes is None:
            self._actor_ejes = self.actores.Ejes(largo=largo)

    def ocultar_ejes(self):
        if self._actor_ejes is not None:
            self._actor_ejes.eliminar()
            self._actor_ejes = None

    def _definir_escena(self, escena):
        self._escena_actual = escena

    def _tick(self, dt):
        # escena.actualizar actualiza self.dt
        self._escena_actual.actualizar(dt)

    def ejecutar(self):
        """Inicia el bucle de juego (llamadas a actualizar + dibujar)."""
        if self.ventana is None:
            print("pilas3d se inició con sin_ventana=True; "
                  "no hay ventana que ejecutar.")
            return
        pyglet.clock.schedule_interval(self._tick, 1 / 60.0)
        pyglet.app.run()

    def terminar(self):
        if self.ventana is not None:
            self.ventana.close()
            self.ventana = None


def obtener_ruta(nombre):
    """Ruta absoluta a un recurso dentro del paquete.

    >>> pilas3d.obtener_ruta('data/caja.png')
    """
    return os.path.join(os.path.dirname(__file__), nombre)


def iniciar(ancho=640, alto=480, titulo="pilas3d", sin_ventana=False):
    """Inicia pilas3d y retorna el objeto principal ``Pilas``.

    ``sin_ventana=True`` permite crear el mundo sin abrir una ventana
    (útil para tests).
    """
    return Pilas(ancho=ancho, alto=alto, titulo=titulo,
                 sin_ventana=sin_ventana)
