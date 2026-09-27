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


# -- modelos de bloque estilo Minecraft (.json) ------------------------------
#
# Formato "elements": cada elemento es un cuboide from..to (en unidades
# de 1/16) con caras north/south/east/west/up/down, cada una con uv
# [u1, v1, u2, v2] (también 0..16, v hacia abajo) y una referencia
# "#nombre" al dict "textures" del archivo.

_CARAS_MC = {
    # nombre: (normal, vértices (bl, br, tr, tl) vistos desde afuera)
    'north': ((0, 0, -1), lambda a, b: [
        (b[0], a[1], a[2]), (a[0], a[1], a[2]),
        (a[0], b[1], a[2]), (b[0], b[1], a[2])]),
    'south': ((0, 0, 1), lambda a, b: [
        (a[0], a[1], b[2]), (b[0], a[1], b[2]),
        (b[0], b[1], b[2]), (a[0], b[1], b[2])]),
    'east': ((1, 0, 0), lambda a, b: [
        (b[0], a[1], b[2]), (b[0], a[1], a[2]),
        (b[0], b[1], a[2]), (b[0], b[1], b[2])]),
    'west': ((-1, 0, 0), lambda a, b: [
        (a[0], a[1], a[2]), (a[0], a[1], b[2]),
        (a[0], b[1], b[2]), (a[0], b[1], a[2])]),
    'up': ((0, 1, 0), lambda a, b: [
        (a[0], b[1], b[2]), (b[0], b[1], b[2]),
        (b[0], b[1], a[2]), (a[0], b[1], a[2])]),
    'down': ((0, -1, 0), lambda a, b: [
        (a[0], a[1], a[2]), (b[0], a[1], a[2]),
        (b[0], a[1], b[2]), (a[0], a[1], b[2])]),
}


def _raiz_assets(ruta):
    """Sube directorios hasta hallar 'models' y retorna su padre
    (el assets/minecraft donde también vive 'textures')."""
    d = os.path.dirname(os.path.abspath(ruta))
    while d and os.path.basename(d) != 'models':
        nuevo = os.path.dirname(d)
        if nuevo == d:
            return os.path.dirname(os.path.abspath(ruta))
        d = nuevo
    return os.path.dirname(d)


def cargar_json_mc(ruta):
    """Carga un modelo de bloque estilo Minecraft (JSON con elements).

    Retorna el mismo dict que ``cargar_obj`` más la ruta ``imagen``
    de la textura principal (resuelta contra el directorio
    ``textures`` hermano de ``models``). Si el modelo usa varias
    texturas, se usa la primera — una sola textura por actor.
    """
    import json

    ruta = os.path.abspath(ruta)
    with open(ruta, 'r', errors='replace') as f:
        data = json.load(f)

    raiz = _raiz_assets(ruta)
    texturas = data.get('textures', {})

    def resolver_textura(ref):
        nombre = texturas.get(ref.lstrip('#'), ref.lstrip('#'))
        return os.path.join(raiz, 'textures', nombre + '.png')

    posiciones, normales, uvs = [], [], []
    textura = None
    for elemento in data.get('elements', []):
        a = [v / 16.0 - 0.5 for v in elemento['from']]
        b = [v / 16.0 - 0.5 for v in elemento['to']]
        a[1] += 0.5
        b[1] += 0.5
        for nombre, (normal, verts_fn) in _CARAS_MC.items():
            cara = elemento.get('faces', {}).get(nombre)
            if cara is None:
                continue
            if textura is None:
                textura = resolver_textura(
                    cara.get('texture', ''))
            u1, v1, u2, v2 = [v / 16.0 for v in
                              cara.get('uv', [0, 0, 16, 16])]
            quad = verts_fn(a, b)
            uv_quad = [(u1, 1 - v2), (u2, 1 - v2),
                       (u2, 1 - v1), (u1, 1 - v1)]
            for idx in (0, 1, 2, 0, 2, 3):
                posiciones.extend(quad[idx])
                normales.extend(normal)
                uvs.extend(uv_quad[idx])

    if not posiciones:
        raise IOError("El modelo '%s' no tiene elementos con caras"
                      % ruta)

    radio = 0.0
    for i in range(0, len(posiciones), 3):
        d = math.sqrt(posiciones[i] ** 2 + posiciones[i + 1] ** 2 +
                      posiciones[i + 2] ** 2)
        if d > radio:
            radio = d

    return {
        'posiciones': posiciones,
        'normales': normales,
        'uvs': uvs,
        'colores': None,
        'radio': radio,
        'triangulos': len(posiciones) // 9,
        'imagen': textura,
    }
