# -*- encoding: utf-8 -*-
"""Fábrica de actores: ``pilas.actores.Cubo()``, etc.

Para crear un actor propio, heredá de ``Actor``::

    from pilas3d.actores.actor import Actor
"""

from pilas3d.actores.actor import Actor
from pilas3d.actores.cubo import Cubo
from pilas3d.actores.esfera import Esfera
from pilas3d.actores.piso import Piso
from pilas3d.actores.ejes import Ejes
from pilas3d.actores.texto import Texto, Puntaje


class Actores(object):
    """Punto de acceso a los actores, como ``pilas.actores`` en pilas."""

    def __init__(self, pilas):
        self._pilas = pilas

    def Cubo(self, x=0, y=0, z=0):
        return Cubo(self._pilas, x=x, y=y, z=z)

    def Esfera(self, x=0, y=0, z=0, radio=1.0):
        return Esfera(self._pilas, x=x, y=y, z=z, radio=radio)

    def Piso(self, x=0, y=0, z=0, tamano=20, divisiones=20):
        return Piso(
            self._pilas, x=x, y=y, z=z, tamano=tamano, divisiones=divisiones
        )

    def Ejes(self, x=0, y=0, z=0, largo=5):
        return Ejes(self._pilas, x=x, y=y, z=z, largo=largo)

    def Texto(self, texto="", x=10, y=10, tamano=18):
        return Texto(self._pilas, texto=texto, x=x, y=y, tamano=tamano)

    def Puntaje(self, x=10, y=10, tamano=22, prefijo=""):
        return Puntaje(
            self._pilas, x=x, y=y, tamano=tamano, prefijo=prefijo
        )
