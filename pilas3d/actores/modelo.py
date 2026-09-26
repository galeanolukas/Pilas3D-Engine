# -*- encoding: utf-8 -*-
"""Actor que dibuja un modelo 3D cargado desde un archivo .obj.

>>> arbol = pilas.actores.Modelo('modelos/arbol.obj', escala=0.5)
>>> arbol.imagen = 'corteza.png'   # textura opcional

El radio de colisión se calcula solo como la esfera envolvente del
modelo (se puede ajustar con ``radio_de_colision``).
"""

from pyglet.gl import GL_TRIANGLES

from pilas3d import modelos
from pilas3d.actores.actor import Actor


class Modelo(Actor):
    """Un modelo .obj; se anima/transforma como cualquier actor."""

    def __init__(self, pilas, ruta, x=0, y=0, z=0, escala=1.0):
        self.ruta = ruta
        self._datos = modelos.cargar_obj(ruta)
        super(Modelo, self).__init__(pilas, x=x, y=y, z=z)
        self.escala = escala
        self.radio_de_colision = self._datos['radio'] * escala

    def _generar_geometria(self):
        d = self._datos
        return d['posiciones'], d['normales'], GL_TRIANGLES, \
            d['colores'], d['uvs']
