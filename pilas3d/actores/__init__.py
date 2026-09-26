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
from pilas3d.actores.pared import Pared
from pilas3d.actores.plano import Plano
from pilas3d.actores.mapa import Mapa
from pilas3d.actores.cartel import Cartel
from pilas3d.actores.animacion import Animacion
from pilas3d.actores.texto import Texto, Puntaje


class Actores(object):
    """Punto de acceso a los actores, como ``pilas.actores`` en pilas."""

    def __init__(self, pilas):
        self._pilas = pilas

    def Cubo(self, x=0, y=0, z=0):
        return Cubo(self._pilas, x=x, y=y, z=z)

    def Esfera(self, x=0, y=0, z=0, radio=1.0, radio_de_colision=None):
        return Esfera(self._pilas, x=x, y=y, z=z, radio=radio,
                      radio_de_colision=radio_de_colision)

    def Piso(self, x=0, y=0, z=0, tamano=20, divisiones=20):
        return Piso(
            self._pilas, x=x, y=y, z=z, tamano=tamano, divisiones=divisiones
        )

    def Ejes(self, x=0, y=0, z=0, largo=5):
        return Ejes(self._pilas, x=x, y=y, z=z, largo=largo)

    def Pared(self, x=0, y=None, z=0, ancho=4.0, alto=3.0,
              profundidad=0.3):
        return Pared(self._pilas, x=x, y=y, z=z, ancho=ancho, alto=alto,
                     profundidad=profundidad)

    def Plano(self, x=0, y=0, z=0, ancho=20, profundidad=20):
        return Plano(self._pilas, x=x, y=y, z=z, ancho=ancho,
                     profundidad=profundidad)

    def Cartel(self, x=0, y=0, z=0, ancho=1.0, alto=1.0):
        return Cartel(self._pilas, x=x, y=y, z=z, ancho=ancho, alto=alto)

    def Animacion(self, imagen, columnas, filas=1, x=0, y=0, z=0,
                  ancho=1.0, alto=1.0, velocidad=10, ciclica=True,
                  eliminar_al_terminar=False):
        return Animacion(
            self._pilas, imagen, columnas, filas=filas, x=x, y=y, z=z,
            ancho=ancho, alto=alto, velocidad=velocidad, ciclica=ciclica,
            eliminar_al_terminar=eliminar_al_terminar)

    def Mapa(self, matriz, simbolos, tamano_celda=2.0, x=0, y=0, z=0):
        return Mapa(self._pilas, matriz, simbolos,
                    tamano_celda=tamano_celda, x=x, y=y, z=z)

    def Texto(self, texto="", x=10, y=10, tamano=18):
        return Texto(self._pilas, texto=texto, x=x, y=y, tamano=tamano)

    def Puntaje(self, x=10, y=10, tamano=22, prefijo=""):
        return Puntaje(
            self._pilas, x=x, y=y, tamano=tamano, prefijo=prefijo
        )
