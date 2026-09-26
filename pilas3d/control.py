# -*- encoding: utf-8 -*-
"""Estado del teclado y el mouse, accesible como ``pilas.control``.

Replica la idea de ``pilas.control`` de pilas-engine: propiedades
booleanas que se pueden consultar dentro de ``actualizar``.
"""

from pyglet.window import key, mouse


class Control(object):
    """Envuelve el estado de entrada de la ventana."""

    def __init__(self, ventana):
        self._ventana = ventana
        self._teclas = ventana.teclas

    # -- teclado ------------------------------------------------------------

    @property
    def izquierda(self):
        return bool(self._teclas[key.LEFT] or self._teclas[key.A])

    @property
    def derecha(self):
        return bool(self._teclas[key.RIGHT] or self._teclas[key.D])

    @property
    def arriba(self):
        return bool(self._teclas[key.UP] or self._teclas[key.W])

    @property
    def abajo(self):
        return bool(self._teclas[key.DOWN] or self._teclas[key.S])

    def simbolo(self, tecla):
        """Consulta cualquier tecla por su constante de pyglet.window.key."""
        return bool(self._teclas[tecla])

    # -- mouse ----------------------------------------------------------------

    @property
    def mouse_x(self):
        """Posición x del mouse en píxeles de ventana."""
        return self._ventana.mouse_x

    @property
    def mouse_y(self):
        """Posición y del mouse en píxeles de ventana (desde abajo)."""
        return self._ventana.mouse_y

    @property
    def boton_izquierdo(self):
        return bool(self._ventana.mouse_botones & mouse.LEFT)

    @property
    def boton_derecho(self):
        return bool(self._ventana.mouse_botones & mouse.RIGHT)

    @property
    def boton_medio(self):
        return bool(self._ventana.mouse_botones & mouse.MIDDLE)


class ControlNulo(object):
    """Control vacío para cuando pilas se inicia sin ventana (tests)."""

    izquierda = derecha = arriba = abajo = False
    mouse_x = mouse_y = 0
    boton_izquierdo = boton_derecho = boton_medio = False

    def simbolo(self, tecla):
        return False
