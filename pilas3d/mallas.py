# -*- encoding: utf-8 -*-
"""Generadores de geometría: retornan (posiciones, normales, modo).

Las posiciones y normales son listas planas de floats (x, y, z, ...).
``modo`` es una constante de pyglet.gl (GL_TRIANGLES o GL_LINES).
"""

import math

from pyglet.gl import GL_TRIANGLES, GL_LINES


def cubo(lado=1.0):
    """Cubo centrado en el origen."""
    s = lado / 2.0
    # (normal, 4 vértices de la cara)
    caras = [
        ((0, 0, 1), [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]),
        ((0, 0, -1), [(s, -s, -s), (-s, -s, -s), (-s, s, -s), (s, s, -s)]),
        ((1, 0, 0), [(s, -s, s), (s, -s, -s), (s, s, -s), (s, s, s)]),
        ((-1, 0, 0), [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)]),
        ((0, 1, 0), [(-s, s, s), (s, s, s), (s, s, -s), (-s, s, -s)]),
        ((0, -1, 0), [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)]),
    ]
    posiciones = []
    normales = []
    for normal, v in caras:
        for triangulo in (v[0], v[1], v[2], v[0], v[2], v[3]):
            posiciones.extend(triangulo)
            normales.extend(normal)
    return posiciones, normales, GL_TRIANGLES


def esfera(radio=1.0, meridianos=24, paralelos=16):
    """Esfera UV centrada en el origen."""
    posiciones = []
    normales = []

    def punto(lon, lat):
        x = radio * math.sin(lat) * math.cos(lon)
        y = radio * math.cos(lat)
        z = radio * math.sin(lat) * math.sin(lon)
        return (x, y, z)

    for i in range(paralelos):
        lat0 = math.pi * i / paralelos
        lat1 = math.pi * (i + 1) / paralelos
        for j in range(meridianos):
            lon0 = 2 * math.pi * j / meridianos
            lon1 = 2 * math.pi * (j + 1) / meridianos
            quad = [
                punto(lon0, lat0),
                punto(lon0, lat1),
                punto(lon1, lat1),
                punto(lon1, lat0),
            ]
            for v in (quad[0], quad[1], quad[2], quad[0], quad[2], quad[3]):
                posiciones.extend(v)
                normales.extend((v[0] / radio, v[1] / radio, v[2] / radio))
    return posiciones, normales, GL_TRIANGLES


def rejilla(tamano=10, divisiones=10):
    """Rejilla de líneas sobre el plano XZ (para el piso)."""
    posiciones = []
    normales = []
    paso = tamano / float(divisiones)
    mitad = tamano / 2.0
    for i in range(divisiones + 1):
        d = -mitad + i * paso
        posiciones.extend([d, 0, -mitad, d, 0, mitad])
        posiciones.extend([-mitad, 0, d, mitad, 0, d])
        normales.extend([0.0] * 12)
    return posiciones, normales, GL_LINES


def ejes(largo=5):
    """Líneas de los ejes X, Y, Z con colores propios por vértice.

    Van a y=0.01 para no pelear en profundidad con la rejilla del piso.
    """
    e = 0.01
    posiciones = [
        0, e, 0, largo, e, 0,   # X: rojo
        0, e, 0, 0, largo, 0,   # Y: verde
        0, e, 0, 0, e, largo,   # Z: azul
    ]
    normales = [0.0] * 18
    colores = [
        1, 0, 0, 1, 1, 0, 0, 1,
        0, 1, 0, 1, 0, 1, 0, 1,
        0, 0, 1, 1, 0, 0, 1, 1,
    ]
    return posiciones, normales, GL_LINES, colores
