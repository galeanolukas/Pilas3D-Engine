# -*- encoding: utf-8 -*-
"""Cargador de modelos Wavefront OBJ (.obj).

Parsea ``v``, ``vt``, ``vn`` y ``f`` (con triangulación en abanico para
caras de más de 3 vértices). Ignora materiales/MTL: la textura se asigna
con ``actor.imagen`` como en cualquier otro actor.

Retorna datos en el mismo formato que las mallas: listas planas de
posiciones, normales y UVs + el radio de la esfera envolvente.
"""

import math
import os

_cache_obj = {}


def _resolver_indice(indice, total):
    """Los índices OBJ son 1-based; negativos son relativos al final."""
    return indice - 1 if indice > 0 else total + indice


def _cargar_materiales(ruta_obj, nombre_mtl):
    """Lee un .mtl y retorna dict nombre_material -> (r, g, b) del Kd."""
    ruta = os.path.join(os.path.dirname(ruta_obj), nombre_mtl)
    colores = {}
    if not os.path.exists(ruta):
        return colores
    actual = None
    with open(ruta, 'r', errors='replace') as f:
        for linea in f:
            campos = linea.split()
            if not campos:
                continue
            if campos[0] == 'newmtl':
                actual = ' '.join(campos[1:])
            elif campos[0] == 'Kd' and actual is not None:
                colores[actual] = tuple(
                    float(v) for v in campos[1:4])
    return colores


def cargar_obj(ruta):
    """Carga un archivo .obj y retorna un dict con la geometría.

    >>> datos = pilas3d.modelos.cargar_obj('modelos/arbol.obj')
    >>> datos['posiciones'], datos['normales'], datos['uvs'], datos['radio']
    """
    ruta = os.path.abspath(ruta)
    if ruta in _cache_obj:
        return _cache_obj[ruta]

    vertices = []     # v
    texcoords = []    # vt
    normales_obj = [] # vn
    posiciones = []
    normales = []
    uvs = []
    colores_vertices = []
    materiales = {}
    color_actual = (1.0, 1.0, 1.0)
    usa_materiales = [False]

    def emitir(cara):
        """Triangula una cara en abanico y emite cada triángulo."""
        for i in range(1, len(cara) - 1):
            tri = (cara[0], cara[i], cara[i + 1])
            _emitir_triangulo(tri)

    def _emitir_triangulo(tri):
        pos_tri = []
        tiene_normal = False
        for ref in tri:
            partes = ref.split('/')
            vi = _resolver_indice(int(partes[0]), len(vertices))
            ti = _resolver_indice(int(partes[1]), len(texcoords)) \
                if len(partes) > 1 and partes[1] else None
            ni = _resolver_indice(int(partes[2]), len(normales_obj)) \
                if len(partes) > 2 and partes[2] else None
            v = vertices[vi]
            posiciones.extend(v)
            pos_tri.append(v)
            uvs.extend(texcoords[ti] if ti is not None else (0.0, 0.0))
            colores_vertices.extend(color_actual + (1.0,))
            if ni is not None:
                normales.extend(normales_obj[ni])
                tiene_normal = True
            else:
                normales.extend((0.0, 0.0, 0.0))
        if not tiene_normal:
            # la cara no traía normales: calcula una plana
            ux, uy, uz = (pos_tri[1][j] - pos_tri[0][j] for j in range(3))
            vx, vy, vz = (pos_tri[2][j] - pos_tri[0][j] for j in range(3))
            n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
            d = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
            normales[-9:] = [n[0] / d, n[1] / d, n[2] / d] * 3

    with open(ruta, 'r', errors='replace') as f:
        for linea in f:
            campos = linea.split()
            if not campos:
                continue
            if campos[0] == 'v':
                vertices.append(tuple(map(float, campos[1:4])))
            elif campos[0] == 'vt':
                texcoords.append(tuple(map(float, campos[1:3])))
            elif campos[0] == 'vn':
                normales_obj.append(tuple(map(float, campos[1:4])))
            elif campos[0] == 'f':
                emitir(campos[1:])
            elif campos[0] == 'mtllib':
                materiales.update(_cargar_materiales(
                    ruta, ' '.join(campos[1:])))
            elif campos[0] == 'usemtl':
                nombre = ' '.join(campos[1:])
                if nombre in materiales:
                    color_actual = materiales[nombre]
                    usa_materiales[0] = True
            # 'o', 'g', 's', '#': se ignoran

    if not posiciones:
        raise IOError("El archivo '%s' no contiene caras (f)" % ruta)

    # radio de la esfera envolvente centrada en el origen
    radio = 0.0
    for i in range(0, len(posiciones), 3):
        d = math.sqrt(posiciones[i] ** 2 + posiciones[i + 1] ** 2 +
                      posiciones[i + 2] ** 2)
        if d > radio:
            radio = d

    datos = {
        'posiciones': posiciones,
        'normales': normales,
        'uvs': uvs,
        'colores': colores_vertices if usa_materiales[0] else None,
        'radio': radio,
        'triangulos': len(posiciones) // 9,
    }
    _cache_obj[ruta] = datos
    return datos
