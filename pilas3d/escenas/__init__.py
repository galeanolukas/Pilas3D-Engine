# -*- encoding: utf-8 -*-
"""Punto de acceso a las escenas: ``pilas.escenas.Normal()``."""

from pilas3d.escenas.escena import Escena
from pilas3d.escenas.normal import Normal


class Escenas(object):
    """Fábrica de escenas, accesible como ``pilas.escenas``."""

    def __init__(self, pilas):
        self._pilas = pilas

    def Normal(self):
        return Normal(self._pilas)

    def Escena(self):
        return Escena(self._pilas)
