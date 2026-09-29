# -*- encoding: utf-8 -*-
"""Zona: un área invisible (o visible) que detecta actores.

Dispara callbacks por flanco — al ENTRAR y al SALIR de cada actor
vigilado::

    zona = pilas.actores.Zona(x=5, z=0, radio=2)
    zona.cuando_entra(jugador, lambda: jugador.decir('llegué!'))
    zona.cuando_sale(jugador, lambda: print('salió'))

Útil para metas, checkpoints, puertas y trampas. ``visible=True``
dibuja un disco en el suelo para depurar.
"""

import math

from pilas3d import colores, mallas
from pilas3d.actores.actor import Actor


class Zona(Actor):
    """Círculo en el plano XZ que vigila quién entra y sale."""

    def __init__(self, pilas, x=0, y=0, z=0, radio=2.0, visible=False,
                 color=None):
        self.radio = radio
        #: False dibuja solo la lógica (invisible); True muestra el disco
        self.visible = visible
        self._vigilados = {}          # actor -> [dentro, fn_entra, fn_sale]
        self._tarea = None
        super(Zona, self).__init__(pilas, x=x, y=y, z=z)
        self.color = color if color is not None else colores.amarillo
        self.radio_de_colision = 0.0  # la zona no choca, solo vigila

    def _generar_geometria(self):
        posiciones, normales, modo, _, uvs = mallas.disco(
            self.radio, lados=32)
        return posiciones, normales, modo, None, uvs

    def dibujar(self):
        if self.visible:
            super(Zona, self).dibujar()

    # -- vigilancia ----------------------------------------------------------

    def cuando_entra(self, actor, funcion):
        """Llama ``funcion()`` cada vez que ``actor`` entra a la zona."""
        self._vigilar(actor)[1] = funcion
        self._arrancar_tarea()

    def cuando_sale(self, actor, funcion):
        """Llama ``funcion()`` cada vez que ``actor`` sale de la zona."""
        self._vigilar(actor)[2] = funcion
        self._arrancar_tarea()

    def _vigilar(self, actor):
        return self._vigilados.setdefault(actor, [False, None, None])

    def _arrancar_tarea(self):
        if self._tarea is None:
            self._tarea = self.pilas.tareas.condicional(
                0.05, self._chequear)

    def dentro(self, actor):
        """True si ``actor`` está ahora dentro de la zona (plano XZ)."""
        return math.hypot(actor.x - self.x, actor.z - self.z) \
            <= self.radio + getattr(actor, 'radio_de_colision', 0)

    def _chequear(self):
        if not self.esta_en_escena() or not self._vigilados:
            return False
        for actor, estado in list(self._vigilados.items()):
            if not actor.esta_en_escena():
                del self._vigilados[actor]
                continue
            adentro = self.dentro(actor)
            if adentro and not estado[0] and estado[1]:
                estado[1]()
            elif not adentro and estado[0] and estado[2]:
                estado[2]()
            estado[0] = adentro
        return True

    def eliminar(self):
        self._vigilados.clear()
        super(Zona, self).eliminar()
