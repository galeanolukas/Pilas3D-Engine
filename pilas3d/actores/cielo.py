# -*- encoding: utf-8 -*-
"""Cielo: una esfera gigante alrededor de la cámara (sky dome).

Se dibuja sin iluminación (sus vértices no tienen normal), así que la
textura se ve siempre a pleno brillo, y sigue a la cámara en cada
frame para que el jugador nunca "llegue" al borde.

>>> pilas.actores.Cielo()                    # cielo estrellado
>>> pilas.actores.Cielo('mi_cielo.png')      # textura propia
"""

import math
import random

from pilas3d import mallas, colores
from pilas3d.actores.actor import Actor


def _textura_estrellas(ancho=512, alto=256):
    """Genera una textura de cielo estrellado sin archivos externos."""
    from pyglet.image import ImageData

    rng = random.Random()
    estrellas = {}
    for _ in range(700):
        x = rng.randrange(ancho)
        y = rng.randrange(alto)
        brillo = rng.choice((180, 220, 255))
        estrellas[(x, y)] = brillo
        if brillo == 255:  # algunas más grandes
            estrellas[(min(x + 1, ancho - 1), y)] = 140

    datos = bytearray(ancho * alto * 4)
    for y in range(alto):
        # degradado vertical: zenit oscuro, horizonte azulado
        t = y / float(alto)
        r = int(4 + 10 * t)
        g = int(4 + 14 * t)
        b = int(12 + 35 * t)
        for x in range(ancho):
            i = (y * ancho + x) * 4
            datos[i:i + 4] = bytes((r, g, b, 255))
    for (x, y), brillo in estrellas.items():
        i = (y * ancho + x) * 4
        datos[i:i + 4] = bytes((brillo, brillo, brillo, 255))

    # ImageData espera la fila 0 abajo; invertimos para que el zenit
    # (v alto) quede arriba en la esfera.
    imagen = ImageData(ancho, alto, "RGBA", bytes(datos))
    return imagen


class Cielo(Actor):
    """Domo de fondo que envuelve a la cámara."""

    def __init__(self, pilas, imagen="estrellas", radio=400):
        super(Cielo, self).__init__(pilas)
        self.escala = radio
        self.radio_de_colision = 0.0
        self.color = colores.blanco
        if imagen == "estrellas":
            self.imagen = _textura_estrellas()
        elif imagen:
            self.imagen = imagen

    def _generar_geometria(self):
        posiciones, normales, modo, _, uvs = mallas.esfera(
            1.0, meridianos=32, paralelos=24
        )
        # Sin normales: el shader lo dibuja a pleno brillo.
        normales = [0.0] * len(normales)
        return posiciones, normales, modo, None, uvs

    def actualizar(self):
        camara = self.pilas.escena_actual().camara
        self.x, self.y, self.z = camara.posicion
