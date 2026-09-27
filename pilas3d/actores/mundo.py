# -*- encoding: utf-8 -*-
"""Mundo de voxels: una grilla de bloques que dibuja UNA sola malla.

En lugar de un actor por cubo (miles de draw calls), se fusiona todo
en una sola geometría emitiendo solo las caras que tocan aire — es
lo que hace Minecraft por cada chunk.

>>> mundo = pilas.actores.Mundo()
>>> mundo.generar_terreno(48, 48, altura=4)
>>> mundo.poner_bloque(2, 5, 3, 'ladrillo')
>>> mundo.sacar_bloque(2, 4, 3)
>>> bloque, adyacente = mundo.disparar_bloque(origen, direccion)

Las coordenadas de bloque son enteras: el bloque (i, j, k) ocupa el
espacio [i, i+1) x [j, j+1) x [k, k+1).
"""

import math
import random

from pyglet.gl import GL_TRIANGLES

from pilas3d import colisiones
from pilas3d.actores.actor import Actor


# Caras de un bloque: normal, índice en la tupla del tipo
# (0=arriba, 1=costados, 2=abajo) y sus 4 vértices relativos.
_CARAS = [
    ((0, 1, 0), 0, [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
    ((0, -1, 0), 2, [(0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1)]),
    ((0, 0, 1), 1, [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
    ((0, 0, -1), 1, [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)]),
    ((1, 0, 0), 1, [(1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)]),
    ((-1, 0, 0), 1, [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
]

_UV_CARA = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

# tipo -> (baldosa_arriba, baldosa_costados, baldosa_abajo) del atlas
TIPOS_POR_DEFECTO = {
    'cesped': (0, 1, 1),
    'tierra': (1, 1, 1),
    'piedra': (2, 2, 2),
    'ladrillo': (3, 3, 3),
    'arena': (4, 4, 4),
}


def _redimensionar(img, lado):
    """Ajusta una imagen a ``lado x lado`` (vecino más cercano)."""
    if img.width == lado and img.height == lado:
        return img
    from pyglet.image import ImageData

    origen = img.get_data("RGBA", img.width * 4)
    datos = bytearray(lado * lado * 4)
    for y in range(lado):
        sy = y * img.height // lado
        for x in range(lado):
            sx = x * img.width // lado
            datos[(y * lado + x) * 4:(y * lado + x) * 4 + 4] = \
                origen[(sy * img.width + sx) * 4:
                       (sy * img.width + sx) * 4 + 4]
    return ImageData(lado, lado, "RGBA", bytes(datos))


def armar_atlas(imagenes, lado=16):
    """Compone imágenes (rutas o ImageData) en un atlas horizontal.

    >>> atlas = armar_atlas(['grass_top.png', 'dirt.png'])
    """
    from pyglet.image import ImageData, load

    ancho = lado * len(imagenes)
    datos = bytearray(ancho * lado * 4)
    for i, img in enumerate(imagenes):
        if isinstance(img, str):
            img = load(img)
        img = _redimensionar(img, lado)
        src = img.get_data("RGBA", lado * 4)
        for y in range(lado):
            base = y * ancho * 4 + i * lado * 4
            datos[base:base + lado * 4] = \
                src[y * lado * 4:(y + 1) * lado * 4]
    return ImageData(ancho, lado, "RGBA", bytes(datos))


def _atlas_basico(lado=16):
    """Genera un atlas de 5 baldosas 16x16 (cesped, tierra, piedra,
    ladrillo, arena) con ruido pixelado estilo Minecraft."""
    from pyglet.image import ImageData

    baldosas = 5
    ancho, alto = lado * baldosas, lado
    rng = random.Random(7)
    bases = [(70, 160, 60), (139, 90, 43), (125, 125, 125),
             (170, 90, 60), (215, 200, 140)]
    datos = bytearray(ancho * alto * 4)
    for y in range(alto):
        for t in range(baldosas):
            for x in range(lado):
                r, g, b = bases[t]
                n = rng.randint(-18, 18)
                if t == 3 and (y % 4 == 0 or
                               (x + (8 if (y // 4) % 2 else 0)) % 8 == 0):
                    r, g, b = 205, 200, 190  # mortero del ladrillo
                i = (y * ancho + t * lado + x) * 4
                datos[i:i + 4] = bytes((
                    max(0, min(255, r + n)),
                    max(0, min(255, g + n)),
                    max(0, min(255, b + n)), 255))
    return ImageData(ancho, alto, "RGBA", bytes(datos))


class Mundo(Actor):
    """Grilla de bloques renderizada como una sola malla."""

    def __init__(self, pilas, tipos=None, atlas=None, baldosas=5):
        self.bloques = {}
        self.tipos = dict(tipos or TIPOS_POR_DEFECTO)
        self._sucio = True
        super(Mundo, self).__init__(pilas)
        if atlas is None:
            self.baldosas = baldosas
            atlas = _atlas_basico()
        elif isinstance(atlas, (list, tuple)):
            self.baldosas = len(atlas)
            atlas = armar_atlas(atlas)
        else:
            self.baldosas = baldosas
        self.imagen = atlas
        self.radio_de_colision = 0.0
        escena = pilas.escena_actual()
        if escena is not None:
            escena.obstaculos.append(self)

    # -- bloques ------------------------------------------------------------

    def poner_bloque(self, i, j, k, tipo='ladrillo'):
        self.bloques[(i, j, k)] = tipo
        self._sucio = True

    def sacar_bloque(self, i, j, k):
        if (i, j, k) in self.bloques:
            del self.bloques[(i, j, k)]
            self._sucio = True

    def hay_bloque(self, i, j, k):
        return (i, j, k) in self.bloques

    def bloque_en(self, i, j, k):
        return self.bloques.get((i, j, k))

    # -- terreno ------------------------------------------------------------

    def generar_terreno(self, ancho=48, profundidad=48, altura=4,
                        semilla=0):
        """Rellena la grilla con un heightmap de senos (pasto arriba,
        tierra debajo, piedra en el fondo), centrado en el origen."""
        rng = random.Random(semilla)
        a, b = rng.uniform(0, 9), rng.uniform(0, 9)
        cx, cz = ancho // 2, profundidad // 2
        for i in range(ancho):
            for k in range(profundidad):
                h = 1 + int(altura * (0.5 + 0.5 * math.sin(i * 0.35 + a)
                                      * math.cos(k * 0.3 + b)))
                for j in range(h):
                    if j == h - 1:
                        tipo = 'cesped'
                    elif j >= h - 3:
                        tipo = 'tierra'
                    else:
                        tipo = 'piedra'
                    self.bloques[(i - cx, j, k - cz)] = tipo
        self._sucio = True

    def altura_suelo(self, x, z):
        """Altura del techo del bloque más alto de la columna (x, z),
        o None si la columna está vacía."""
        i, k = math.floor(x), math.floor(z)
        techo = None
        for (bi, bj, bk) in self.bloques:
            if bi == i and bk == k and (techo is None or bj >= techo):
                techo = bj + 1
        return techo

    # -- rayo contra la grilla (para picar / construir) ---------------------

    def disparar_bloque(self, origen, direccion, alcance=6.0):
        """Recorre la grilla con el rayo (DDA) y retorna
        ``(bloque, adyacente)``: el bloque golpeado y la celda vacía
        previa (donde se podría colocar un bloque nuevo).
        """
        ox, oy, oz = origen
        dx, dy, dz = direccion
        x, y, z = math.floor(ox), math.floor(oy), math.floor(oz)
        paso_x = 1 if dx > 0 else -1
        paso_y = 1 if dy > 0 else -1
        paso_z = 1 if dz > 0 else -1
        dt_x = abs(1.0 / dx) if dx else float('inf')
        dt_y = abs(1.0 / dy) if dy else float('inf')
        dt_z = abs(1.0 / dz) if dz else float('inf')
        t_x = (x + 1 - ox) / dx if dx > 0 else \
            (x - ox) / dx if dx < 0 else float('inf')
        t_y = (y + 1 - oy) / dy if dy > 0 else \
            (y - oy) / dy if dy < 0 else float('inf')
        t_z = (z + 1 - oz) / dz if dz > 0 else \
            (z - oz) / dz if dz < 0 else float('inf')

        adyacente = None
        t = 0.0
        while t <= alcance:
            if (x, y, z) in self.bloques:
                return (x, y, z), adyacente
            adyacente = (x, y, z)
            if t_x <= t_y and t_x <= t_z:
                x += paso_x
                t = t_x
                t_x += dt_x
            elif t_y <= t_z:
                y += paso_y
                t = t_y
                t_y += dt_y
            else:
                z += paso_z
                t = t_z
                t_z += dt_z
        return None, None

    # -- colisión con el jugador --------------------------------------------

    def resolver_circulo(self, x, z, radio, y_min, y_max):
        """Empuja al círculo (x, z, radio) fuera de los bloques cuyo
        rango vertical [j, j+1) intersecta [y_min, y_max)."""
        cajas = []
        i0, i1 = math.floor(x - radio) - 1, math.floor(x + radio) + 1
        k0, k1 = math.floor(z - radio) - 1, math.floor(z + radio) + 1
        j0 = math.floor(y_min)
        j1 = math.floor(y_max - 1e-6)
        for i in range(i0, i1 + 1):
            for k in range(k0, k1 + 1):
                for j in range(j0, j1 + 1):
                    if (i, j, k) in self.bloques:
                        cajas.append((i, i + 1, k, k + 1))
        return colisiones.resolver_circulo_en_cajas(x, z, radio, cajas)

    # -- render: una malla con solo caras visibles --------------------------

    def dibujar(self):
        if self._sucio:
            self._reconstruir_gl()
            self._sucio = False
        super(Mundo, self).dibujar()

    def _generar_geometria(self):
        posiciones, normales, uvs = [], [], []
        n_baldosas = float(self.baldosas)
        for (i, j, k), tipo in self.bloques.items():
            baldosas = self.tipos.get(tipo)
            if baldosas is None:
                baldosas = (0, 0, 0)
            for normal, cual, verts in _CARAS:
                nx, ny, nz = normal
                if (i + nx, j + ny, k + nz) in self.bloques:
                    continue  # cara tapada por un vecino: no se dibuja
                baldosa = baldosas[cual]
                u0 = baldosa / n_baldosas
                u1 = (baldosa + 1) / n_baldosas
                quad = [(i + vx, j + vy, k + vz) for vx, vy, vz in verts]
                for idx in (0, 1, 2, 0, 2, 3):
                    posiciones.extend(quad[idx])
                    normales.extend(normal)
                    uc, vc = _UV_CARA[idx]
                    uvs.extend((u0 + uc * (u1 - u0), vc))
        return posiciones, normales, GL_TRIANGLES, None, uvs
