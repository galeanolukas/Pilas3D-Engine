# -*- encoding: utf-8 -*-
"""Generadores de geometría.

Cada función retorna ``(posiciones, normales, modo, colores, uvs)``:

- ``posiciones`` y ``normales``: listas planas de floats (x, y, z, ...).
- ``modo``: constante de pyglet.gl (GL_TRIANGLES o GL_LINES).
- ``colores``: listas planas (r, g, b, a) por vértice, o None para usar
  el color del actor.
- ``uvs``: coordenadas de textura (u, v) por vértice. Los valores mayores
  a 1 repiten la textura (requiere GL_REPEAT).
"""

import math

from pyglet.gl import GL_TRIANGLES, GL_LINES


def cuboide(ancho=1.0, alto=1.0, profundidad=1.0):
    """Prisma rectangular centrado en el origen, con UVs que repiten
    la textura una vez por unidad de longitud."""
    ax, ay, az = ancho / 2.0, alto / 2.0, profundidad / 2.0
    # (normal, 4 vértices, escala de UV horizontal/vertical)
    caras = [
        ((0, 0, 1),
         [(-ax, -ay, az), (ax, -ay, az), (ax, ay, az), (-ax, ay, az)],
         (ancho, alto)),
        ((0, 0, -1),
         [(ax, -ay, -az), (-ax, -ay, -az), (-ax, ay, -az), (ax, ay, -az)],
         (ancho, alto)),
        ((1, 0, 0),
         [(ax, -ay, az), (ax, -ay, -az), (ax, ay, -az), (ax, ay, az)],
         (profundidad, alto)),
        ((-1, 0, 0),
         [(-ax, -ay, -az), (-ax, -ay, az), (-ax, ay, az), (-ax, ay, -az)],
         (profundidad, alto)),
        ((0, 1, 0),
         [(-ax, ay, az), (ax, ay, az), (ax, ay, -az), (-ax, ay, -az)],
         (ancho, profundidad)),
        ((0, -1, 0),
         [(-ax, -ay, -az), (ax, -ay, -az), (ax, -ay, az), (-ax, -ay, az)],
         (ancho, profundidad)),
    ]
    posiciones = []
    normales = []
    uvs = []
    uv_quad = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for normal, v, (su, sv) in caras:
        quad_uv = [(u * su, t * sv) for u, t in uv_quad]
        for i in (0, 1, 2, 0, 2, 3):
            posiciones.extend(v[i])
            normales.extend(normal)
            uvs.extend(quad_uv[i])
    return posiciones, normales, GL_TRIANGLES, None, uvs


def cubo(lado=1.0):
    """Cubo centrado en el origen."""
    return cuboide(lado, lado, lado)


def esfera(radio=1.0, meridianos=24, paralelos=16):
    """Esfera UV centrada en el origen (u = longitud, v = latitud)."""
    posiciones = []
    normales = []
    uvs = []

    def punto(lon, lat):
        x = radio * math.sin(lat) * math.cos(lon)
        y = radio * math.cos(lat)
        z = radio * math.sin(lat) * math.sin(lon)
        uv = (lon / (2 * math.pi), lat / math.pi)
        return (x, y, z), uv

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
            for i2 in (0, 1, 2, 0, 2, 3):
                v, uv = quad[i2]
                posiciones.extend(v)
                normales.extend((v[0] / radio, v[1] / radio, v[2] / radio))
                uvs.extend(uv)
    return posiciones, normales, GL_TRIANGLES, None, uvs


def plano(ancho=20.0, profundidad=20.0):
    """Cuadrado horizontal sobre XZ, centrado — ideal para piso
    con textura (la textura se repite una vez por unidad)."""
    ax, az = ancho / 2.0, profundidad / 2.0
    v = [(-ax, 0, -az), (ax, 0, -az), (ax, 0, az), (-ax, 0, az)]
    uv = [(0, 0), (ancho, 0), (ancho, profundidad), (0, profundidad)]
    posiciones = []
    normales = []
    uvs = []
    for i in (0, 1, 2, 0, 2, 3):
        posiciones.extend(v[i])
        normales.extend((0, 1, 0))
        uvs.extend(uv[i])
    return posiciones, normales, GL_TRIANGLES, None, uvs


def cartel(ancho=1.0, alto=1.0):
    """Cuadro vertical centrado en el origen, mirando hacia +Z.

    Pensado para billboards (sprites que siempre miran a la cámara)
    con textura transparente. Los UVs cubren [0, 1].
    """
    ax, ay = ancho / 2.0, alto / 2.0
    v = [(-ax, -ay, 0), (ax, -ay, 0), (ax, ay, 0), (-ax, ay, 0)]
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
    posiciones = []
    normales = []
    uvs = []
    for i in (0, 1, 2, 0, 2, 3):
        posiciones.extend(v[i])
        normales.extend((0, 0, 1))
        uvs.extend(uv[i])
    return posiciones, normales, GL_TRIANGLES, None, uvs


def disco(radio=1.0, lados=24):
    """Círculo horizontal sobre XZ, centrado — para sombras falsas."""
    posiciones = []
    normales = []
    uvs = []
    for i in range(lados):
        a0 = 2 * math.pi * i / lados
        a1 = 2 * math.pi * (i + 1) / lados
        posiciones.extend([0, 0, 0,
                           radio * math.cos(a0), 0, radio * math.sin(a0),
                           radio * math.cos(a1), 0, radio * math.sin(a1)])
        normales.extend([0, 1, 0] * 3)
        uvs.extend([0.0] * 6)
    return posiciones, normales, GL_TRIANGLES, None, uvs


def esfera_alambrada(radio=1.0, meridianos=16, paralelos=10):
    """Esfera de líneas (wireframe), rojiza, para radios de colisión."""
    posiciones = []

    # Anillos horizontales (paralelos al plano XZ)
    for i in range(1, paralelos):
        lat = math.pi * i / paralelos
        y = radio * math.cos(lat)
        r = radio * math.sin(lat)
        for j in range(meridianos):
            a0 = 2 * math.pi * j / meridianos
            a1 = 2 * math.pi * (j + 1) / meridianos
            posiciones.extend([
                r * math.cos(a0), y, r * math.sin(a0),
                r * math.cos(a1), y, r * math.sin(a1),
            ])

    # Círculos verticales que pasan por los polos
    for j in range(meridianos // 2):
        lon = math.pi * j / (meridianos // 2)
        for i in range(meridianos):
            t0 = 2 * math.pi * i / meridianos
            t1 = 2 * math.pi * (i + 1) / meridianos
            posiciones.extend([
                radio * math.sin(t0) * math.cos(lon), radio * math.cos(t0),
                radio * math.sin(t0) * math.sin(lon),
                radio * math.sin(t1) * math.cos(lon), radio * math.cos(t1),
                radio * math.sin(t1) * math.sin(lon),
            ])

    normales = [0.0] * len(posiciones)
    colores = [1.0, 0.3, 0.3, 1.0] * (len(posiciones) // 3)
    uvs = [0.0] * (len(posiciones) // 3 * 2)
    return posiciones, normales, GL_LINES, colores, uvs


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
    uvs = [0.0] * (len(posiciones) // 3 * 2)
    return posiciones, normales, GL_LINES, None, uvs


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
    uvs = [0.0] * 12
    return posiciones, normales, GL_LINES, colores, uvs
