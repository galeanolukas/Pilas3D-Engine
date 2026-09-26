# -*- encoding: utf-8 -*-
"""Estado del teclado, accesible como ``pilas.control``.

Replica la idea de ``pilas.control`` de pilas-engine: propiedades
booleanas que se pueden consultar dentro de ``actualizar``.
"""

from pyglet.window import key


class Control(object):
    """Envuelve al KeyStateHandler de la ventana."""

    def __init__(self, teclas):
        self._teclas = teclas

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


class ControlNulo(object):
    """Control vacío para cuando pilas se inicia sin ventana (tests)."""

    izquierda = derecha = arriba = abajo = False

    def simbolo(self, tecla):
        return False
