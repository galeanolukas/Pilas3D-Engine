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

    def vincular(self, clase):
        """Registra una clase de escena propia, como en pilas-engine.

        >>> class Menu(pilas3d.escenas.Escena):
        ...     def iniciar(self): ...
        >>> pilas.escenas.vincular(Menu)
        >>> pilas.escenas.Menu()     # crea y activa la escena
        """
        nombre = clase.__name__
        setattr(self, nombre,
                lambda: clase(self._pilas))
        return clase
