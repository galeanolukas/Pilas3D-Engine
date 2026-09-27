# -*- encoding: utf-8 -*-
"""Mundo de voxels: grilla de bloques renderizada por chunks.

En lugar de un actor por cubo (miles de draw calls), los bloques se
fusionan en una malla por cada chunk de ``tamano_chunk`` columnas,
emitiendo solo las caras que tocan aire — es lo que hace Minecraft.
Editar un bloque solo reconstruye su chunk (y el vecino si está en
el borde).

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
    """Grilla de bloques renderizada en chunks de malla."""

    def __init__(self, pilas, tipos=None, atlas=None, baldosas=5,
                 tamano_chunk=16, infinito=False, semilla=0, altura=4,
                 distancia_vista=3):
        self.bloques = {}
        self.tipos = dict(tipos or TIPOS_POR_DEFECTO)
        self.tamano_chunk = tamano_chunk
        self._chunks = {}          # (ci, ck) -> vertex_list
        self._sucios = set()       # chunks a reconstruir
        self._sucio = True         # reconstruir todo (atlas, etc.)
        self._columnas = {}        # (i, k) -> techo más alto
        # modo infinito: genera chunks alrededor de la cámara
        self.infinito = infinito
        self.semilla = semilla
        self.altura_terreno = altura
        self.distancia_vista = distancia_vista
        self._generados = set()    # chunks con bloques ya creados
        rng = random.Random(semilla)
        self._fases = (rng.uniform(0, 9), rng.uniform(0, 9))
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

    def _marcar_sucio(self, i, k):
        """Marca el chunk del bloque (y vecinos si toca el borde)."""
        c = self.tamano_chunk
        ci, ck = i // c, k // c
        self._sucios.add((ci, ck))
        if i % c == 0:
            self._sucios.add((ci - 1, ck))
        if i % c == c - 1:
            self._sucios.add((ci + 1, ck))
        if k % c == 0:
            self._sucios.add((ci, ck - 1))
        if k % c == c - 1:
            self._sucios.add((ci, ck + 1))

    def _subir_columna(self, i, j, k):
        """Anota el techo de la columna (i, k) tras poner un bloque."""
        col = (i, k)
        self._columnas[col] = max(self._columnas.get(col, 0), j + 1)

    def poner_bloque(self, i, j, k, tipo='ladrillo'):
        self.bloques[(i, j, k)] = tipo
        self._subir_columna(i, j, k)
        self._marcar_sucio(i, k)

    def sacar_bloque(self, i, j, k):
        if (i, j, k) in self.bloques:
            del self.bloques[(i, j, k)]
            if self._columnas.get((i, k)) == j + 1:
                # era el más alto: buscar el nuevo techo bajando
                j -= 1
                while j >= 0 and (i, j, k) not in self.bloques:
                    j -= 1
                if j >= 0:
                    self._columnas[(i, k)] = j + 1
                else:
                    del self._columnas[(i, k)]
            self._marcar_sucio(i, k)

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
                    self._subir_columna(i - cx, j, k - cz)
        self._sucio = True   # terreno nuevo: reconstruir todo

    # -- mundo infinito: generación por demanda ------------------------------

    def altura_terreno_en(self, i, k):
        """Altura procedural de la columna (i, k) — determinista por
        ``semilla``. Igual al heightmap de ``generar_terreno``."""
        a, b = self._fases
        return 1 + int(self.altura_terreno * (
            0.5 + 0.5 * math.sin(i * 0.35 + a) * math.cos(k * 0.3 + b)))

    def _generar_chunk_bloques(self, ci, ck):
        """Crea los bloques procedurales de un chunk (una sola vez)."""
        c = self.tamano_chunk
        for i in range(ci * c, ci * c + c):
            for k in range(ck * c, ck * c + c):
                h = self.altura_terreno_en(i, k)
                for j in range(h):
                    if (i, j, k) not in self.bloques:
                        if j == h - 1:
                            tipo = 'cesped'
                        elif j >= h - 3:
                            tipo = 'tierra'
                        else:
                            tipo = 'piedra'
                        self.bloques[(i, j, k)] = tipo
                        self._subir_columna(i, j, k)
        self._generados.add((ci, ck))

    def actualizar(self):
        """En modo infinito: genera chunks cerca de la cámara y
        descarga (de la malla, no de la memoria) los lejanos."""
        if not self.infinito:
            return
        escena = self.pilas.escena_actual()
        if escena is None:
            return
        cam = escena.camara
        c = self.tamano_chunk
        ci0 = int(math.floor(cam.posicion[0] / c))
        ck0 = int(math.floor(cam.posicion[2] / c))
        d = self.distancia_vista
        for di in range(-d, d + 1):
            for dk in range(-d, d + 1):
                clave = (ci0 + di, ck0 + dk)
                if clave not in self._generados:
                    self._generar_chunk_bloques(*clave)
                if clave not in self._chunks:
                    self._sucios.add(clave)
        # descargar la malla de chunks lejanos (los bloques quedan)
        for clave in list(self._chunks):
            if abs(clave[0] - ci0) > d + 1 or abs(clave[1] - ck0) > d + 1:
                self._chunks.pop(clave).delete()

    def altura_suelo(self, x, z):
        """Altura del techo del bloque más alto de la columna (x, z),
        o None si la columna está vacía. O(1) con índice de columnas."""
        i, k = math.floor(x), math.floor(z)
        return self._columnas.get((i, k))

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

    # -- render: una malla por chunk, solo caras visibles -------------------

    def _geometria_chunk(self, ci, ck):
        """Vértices del chunk (ci, ck): solo caras que tocan aire."""
        c = self.tamano_chunk
        i0, i1 = ci * c, ci * c + c
        k0, k1 = ck * c, ck * c + c
        posiciones, normales, uvs = [], [], []
        n_baldosas = float(self.baldosas)
        for (i, j, k), tipo in self.bloques.items():
            if not (i0 <= i < i1 and k0 <= k < k1):
                continue
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
        return posiciones, normales, uvs

    def _construir_chunk(self, clave):
        from pilas3d import shaders

        posiciones, normales, uvs = self._geometria_chunk(*clave)
        viejo = self._chunks.pop(clave, None)
        if viejo is not None:
            viejo.delete()
        if not posiciones:
            return
        cantidad = len(posiciones) // 3
        self._chunks[clave] = shaders.obtener_programa().vertex_list(
            cantidad,
            GL_TRIANGLES,
            position=("f", posiciones),
            normal=("f", normales),
            color=("f", self._colores_planos(cantidad)),
            texcoords=("f", uvs),
        )

    def dibujar(self):
        from pilas3d import shaders
        from pyglet.gl import glBindTexture, GL_TEXTURE_2D

        if self._sucio:
            for vl in self._chunks.values():
                vl.delete()
            self._chunks = {}
            c = self.tamano_chunk
            self._sucios = {(i // c, k // c)
                            for (i, j, k) in self.bloques}
            self._sucio = False
        for clave in list(self._sucios):
            self._construir_chunk(clave)
            self._sucios.discard(clave)

        programa = shaders.obtener_programa()
        programa["modelo"] = self.matriz_modelo()
        programa["punto_tamano"] = 1.0
        programa["uv_escala"] = self._uv_escala
        programa["uv_desplazamiento"] = self._uv_desplazamiento
        if self._textura is None and self._imagen is not None:
            self._cargar_textura()
        if self._textura is not None:
            glBindTexture(GL_TEXTURE_2D, self._textura.id)
            programa["textura"] = 0
            programa["usar_textura"] = True
        else:
            programa["usar_textura"] = False
        for vl in self._chunks.values():
            vl.draw(GL_TRIANGLES)

    def terminar(self):
        """Libera los vertex lists de todos los chunks."""
        for vl in self._chunks.values():
            vl.delete()
        self._chunks = {}
        self._sucios = set()
