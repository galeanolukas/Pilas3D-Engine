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

import pyglet

from pilas3d import colores
from pilas3d.actores import Actores
from pilas3d.control import Control, ControlNulo
from pilas3d.escenas import Escenas

VERSION = "0.1.0"


class Pilas(object):
    """Representa el área de juego; es el contenedor principal.

    Al igual que en pilas-engine, este objeto mantiene la escena actual,
    la fábrica de actores y el bucle de juego.
    """

    def __init__(self, ancho=640, alto=480, titulo="pilas3d",
                 sin_ventana=False):
        self.dt = 1 / 60.0
        self._escena_actual = None

        self.actores = Actores(self)
        self.escenas = Escenas(self)
        self.colores = colores

        if sin_ventana:
            self.ventana = None
            self.control = ControlNulo()
        else:
            from pilas3d.ventana import Ventana

            self.ventana = Ventana(self, ancho, alto, titulo)
            self.control = Control(self.ventana.teclas)

        self.escenas.Normal()

    def escena_actual(self):
        return self._escena_actual

    def _definir_escena(self, escena):
        self._escena_actual = escena

    def _tick(self, dt):
        self.dt = dt
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


def iniciar(ancho=640, alto=480, titulo="pilas3d", sin_ventana=False):
    """Inicia pilas3d y retorna el objeto principal ``Pilas``.

    ``sin_ventana=True`` permite crear el mundo sin abrir una ventana
    (útil para tests).
    """
    return Pilas(ancho=ancho, alto=alto, titulo=titulo,
                 sin_ventana=sin_ventana)
