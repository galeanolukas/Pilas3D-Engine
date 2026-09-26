# -*- encoding: utf-8 -*-
"""Cartel: un cuadro con textura que siempre mira a la cámara.

Es la técnica que usaban los juegos estilo Doom para personajes y
objetos: un "cartel" 2D plantado en el mundo 3D (billboard). Con PNGs
con transparencia el fondo se descarta solo.

>>> enemigo = pilas.actores.Cartel(ancho=1.2, alto=1.8)
>>> enemigo.imagen = 'alien.png'
"""

import math

from pyglet.math import Mat4, Vec3

from pilas3d import mallas
from pilas3d.actores.actor import Actor


class Cartel(Actor):
    """Cuadro vertical con textura que rota para mirar a la cámara.

    El eje Y del actor queda fijo: el cartel solo gira sobre su
    vertical (como los sprites de Doom). ``rotacion_y`` sigue
    funcionando como giro adicional relativo.
    """

    def __init__(self, pilas, x=0, y=0, z=0, ancho=1.0, alto=1.0):
        self.ancho = ancho
        self.alto = alto
        super(Cartel, self).__init__(pilas, x=x, y=y, z=z)
        self.radio_de_colision = max(ancho, alto) / 2.0

    def _generar_geometria(self):
        return mallas.cartel(self.ancho, self.alto)

    def matriz_modelo(self):
        """Rota sobre Y para mirar a la cámara; no se cachea."""
        camara = self.pilas.escena_actual().camara
        angulo = math.degrees(math.atan2(camara.x - self._x,
                                        camara.z - self._z))
        matriz = Mat4.from_translation(Vec3(self._x, self._y, self._z))
        matriz = matriz @ Mat4.from_rotation(
            math.radians(angulo + self._rotacion_y), Vec3(0, 1, 0))
        if self._rotacion_x:
            matriz = matriz @ Mat4.from_rotation(
                math.radians(self._rotacion_x), Vec3(1, 0, 0))
        if self._rotacion_z:
            matriz = matriz @ Mat4.from_rotation(
                math.radians(self._rotacion_z), Vec3(0, 0, 1))
        matriz = matriz @ Mat4.from_scale(
            Vec3(self._escala_x, self._escala_y, self._escala_z))
        self._matriz = matriz
        self._matriz_sucia = False
        return matriz
