# -*- encoding: utf-8 -*-
"""Generador de personajes low-poly riggeados — escribe .glb listos
para ``ModeloGLTF`` y ``pilas3d-editor``.

La idea: un personaje estilo Minecraft/Quaternius es un esqueleto de
~19 huesos donde cada parte del cuerpo es una caja pegada 100% a un
hueso (rigid skinning — sin pesos suaves). En la pose de reposo todos
los huesos tienen rotación identidad, así que las matrices inversas
de bind son puras traslaciones y el modelo queda correcto por
construcción.

>>> from pilas3d.personaje import crear_personaje
>>> crear_personaje('modelos/personajes/heroe.glb', alto=1.8,
...                 colores={'camisa': (200, 60, 60)})
>>> heroe = pilas.actores.ModeloGLTF('modelos/personajes/heroe.glb')
>>> heroe.animar(...)  # o abrir pilas3d-editor y animarlo ahí

Los nombres de huesos siguen la convención que ``mapear_huesos``
reconoce (Left/Right + Arm/Leg/Head/Hips...), así que la animación
procedural (tecla T del editor) funciona sin configuración.
"""

import json
import os
import struct

# hueso -> (padre, posición mundo en la pose de reposo, en fracción
# del alto). Orden proximal->distal dentro de cada cadena: así
# quedan en skin.joints y así los enumera mapear_huesos.
_HUESOS = [
    ('Hips',          None,      (0.0,    0.53,  0.0)),
    ('Spine',         'Hips',    (0.0,    0.61,  0.0)),
    ('Chest',         'Spine',   (0.0,    0.70,  0.0)),
    ('Neck',          'Chest',   (0.0,    0.83,  0.0)),
    ('Head',          'Neck',    (0.0,    0.85,  0.0)),
    ('LeftShoulder',  'Chest',   (0.10,   0.80,  0.0)),
    ('LeftArm',       'LeftShoulder',  (0.145,  0.79,  0.0)),
    ('LeftForeArm',   'LeftArm',       (0.145,  0.60,  0.0)),
    ('LeftHand',      'LeftForeArm',   (0.145,  0.42,  0.0)),
    ('RightShoulder', 'Chest',   (-0.10,  0.80,  0.0)),
    ('RightArm',      'RightShoulder', (-0.145, 0.79,  0.0)),
    ('RightForeArm',  'RightArm',      (-0.145, 0.60,  0.0)),
    ('RightHand',     'RightForeArm',  (-0.145, 0.42,  0.0)),
    ('LeftUpLeg',     'Hips',    (0.06,   0.51,  0.0)),
    ('LeftLeg',       'LeftUpLeg',     (0.06,   0.27,  0.0)),
    ('LeftFoot',      'LeftLeg',       (0.06,   0.05,  0.0)),
    ('RightUpLeg',    'Hips',    (-0.06,  0.51,  0.0)),
    ('RightLeg',      'RightUpLeg',    (-0.06,  0.27,  0.0)),
    ('RightFoot',     'RightLeg',      (-0.06,  0.05,  0.0)),
]

_COLORES = {
    'piel':     (235, 190, 150),
    'camisa':   (70, 120, 200),
    'pantalon': (55, 55, 70),
    'zapatos':  (45, 35, 30),
    'ojos':     (30, 25, 25),
    'pelo':     (60, 40, 25),
}


def _caja(cx, cy, cz, sx, sy, sz):
    """Caja centrada en (cx,cy,cz) — vértices expandidos con normal
    por cara (36 vértices, sin índices)."""
    ax, ay, az = sx / 2.0, sy / 2.0, sz / 2.0
    caras = [
        ((0, 0, 1),  [(-ax, -ay, az), (ax, -ay, az), (ax, ay, az),
                      (-ax, ay, az)]),
        ((0, 0, -1), [(ax, -ay, -az), (-ax, -ay, -az), (-ax, ay, -az),
                      (ax, ay, -az)]),
        ((1, 0, 0),  [(ax, -ay, az), (ax, -ay, -az), (ax, ay, -az),
                      (ax, ay, az)]),
        ((-1, 0, 0), [(-ax, -ay, -az), (-ax, -ay, az), (-ax, ay, az),
                      (-ax, ay, -az)]),
        ((0, 1, 0),  [(-ax, ay, az), (ax, ay, az), (ax, ay, -az),
                      (-ax, ay, -az)]),
        ((0, -1, 0), [(-ax, -ay, -az), (ax, -ay, -az), (ax, ay, az),
                      (-ax, -ay, az)]),
    ]
    pos, nor = [], []
    for normal, v in caras:
        for i in (0, 1, 2, 0, 2, 3):
            pos.append((v[i][0] + cx, v[i][1] + cy, v[i][2] + cz))
            nor.append(normal)
    return pos, nor


def _partes(alto, ancho, cabeza):
    """Lista de partes del cuerpo: (hueso, caja en espacio de modelo,
    clave de color). Todo en metros * fracción del alto."""
    h = alto
    w = ancho
    c = cabeza
    partes = [
        # tronco
        ('Hips',        _caja(0, 0.52 * h, 0, 0.21 * h * w,
                              0.12 * h, 0.10 * h), 'pantalon'),
        ('Chest',       _caja(0, 0.71 * h, 0, 0.22 * h * w,
                              0.26 * h, 0.11 * h), 'camisa'),
        # cabeza (escala propia para modo "chibi")
        ('Head',        _caja(0, (0.85 + 0.06 * c) * h, 0,
                              0.17 * h * c, 0.16 * h * c,
                              0.16 * h * c), 'piel'),
        ('Head',        _caja(0.04 * h * c, (0.87 + 0.06 * c) * h,
                              0.081 * h * c, 0.028 * h * c,
                              0.028 * h * c, 0.01 * h), 'ojos'),
        ('Head',        _caja(-0.04 * h * c, (0.87 + 0.06 * c) * h,
                              0.081 * h * c, 0.028 * h * c,
                              0.028 * h * c, 0.01 * h), 'ojos'),
        ('Head',        _caja(0, (0.85 + 0.135 * c) * h,
                              -0.005 * h, 0.175 * h * c,
                              0.05 * h * c, 0.17 * h * c), 'pelo'),
        # brazos (cuelgan a los costados en la pose de reposo)
        ('LeftArm',     _caja(0.145 * h * w, 0.70 * h, 0,
                              0.055 * h * w, 0.17 * h,
                              0.055 * h), 'camisa'),
        ('LeftForeArm', _caja(0.145 * h * w, 0.51 * h, 0,
                              0.05 * h * w, 0.17 * h, 0.05 * h),
         'piel'),
        ('LeftHand',    _caja(0.145 * h * w, 0.375 * h, 0,
                              0.05 * h * w, 0.08 * h, 0.05 * h),
         'piel'),
        ('RightArm',    _caja(-0.145 * h * w, 0.70 * h, 0,
                              0.055 * h * w, 0.17 * h,
                              0.055 * h), 'camisa'),
        ('RightForeArm', _caja(-0.145 * h * w, 0.51 * h, 0,
                               0.05 * h * w, 0.17 * h, 0.05 * h),
         'piel'),
        ('RightHand',   _caja(-0.145 * h * w, 0.375 * h, 0,
                              0.05 * h * w, 0.08 * h, 0.05 * h),
         'piel'),
        # piernas
        ('LeftUpLeg',   _caja(0.06 * h * w, 0.385 * h, 0,
                              0.085 * h * w, 0.23 * h,
                              0.085 * h), 'pantalon'),
        ('LeftLeg',     _caja(0.06 * h * w, 0.155 * h, 0,
                              0.075 * h * w, 0.21 * h,
                              0.075 * h), 'pantalon'),
        ('LeftFoot',    _caja(0.06 * h * w, 0.025 * h, 0.02 * h,
                              0.08 * h * w, 0.05 * h, 0.13 * h),
         'zapatos'),
        ('RightUpLeg',  _caja(-0.06 * h * w, 0.385 * h, 0,
                              0.085 * h * w, 0.23 * h,
                              0.085 * h), 'pantalon'),
        ('RightLeg',    _caja(-0.06 * h * w, 0.155 * h, 0,
                              0.075 * h * w, 0.21 * h,
                              0.075 * h), 'pantalon'),
        ('RightFoot',   _caja(-0.06 * h * w, 0.025 * h, 0.02 * h,
                              0.08 * h * w, 0.05 * h, 0.13 * h),
         'zapatos'),
    ]
    return partes


def crear_personaje(ruta='modelos/personajes/personaje.glb', alto=1.8,
                    colores=None, ancho=1.0, cabeza=1.0):
    """Genera un personaje humanoide low-poly riggeado y lo guarda
    como ``.glb`` en ``ruta``. Devuelve la ruta escrita.

    - ``alto``: altura total en metros (pies a coronilla).
    - ``ancho``: factor de anchura (hombros/cadera), 1.0 normal.
    - ``cabeza``: factor del tamaño de la cabeza — 1.4+ da estilo
      "chibi".
    - ``colores``: dict 0-255 con claves ``piel``, ``camisa``,
      ``pantalon``, ``zapatos``, ``ojos``, ``pelo`` (parciales OK —
      el resto usa el default).

    El .glb sale con skin + nombres de hueso estándar: se abre en
    ``pilas3d-editor`` para posarlo/animarlo y ``animacion_procedural``
    ya lo reconoce (caminar, correr, saludar...).
    """
    col = dict(_COLORES)
    if colores:
        col.update(colores)

    pos_mundo = {n: (p[0] * alto, p[1] * alto, p[2] * alto)
                 for n, _, p in _HUESOS}

    # -- nodos: huesos (jerarquía) + nodo del mesh -------------------
    padres = {n: p for n, p, _ in _HUESOS}
    indice = {n: i for i, (n, _, _) in enumerate(_HUESOS)}
    nodos = []
    for n, padre, _ in _HUESOS:
        pm = pos_mundo[n]
        if padre is None:
            local = pm
        else:
            pp = pos_mundo[padre]
            local = [pm[0] - pp[0], pm[1] - pp[1], pm[2] - pp[2]]
        nodos.append({'name': n, 'translation': list(local)})
    for n, padre, _ in _HUESOS:
        if padre is not None:
            nodos[indice[padre]].setdefault('children', [])\
                .append(indice[n])
    i_mesh = len(nodos)
    nodos.append({'name': 'Cuerpo', 'mesh': 0, 'skin': 0})

    # -- buffers -----------------------------------------------------
    blob = bytearray()
    vistas, accesores = [], []

    def acc(fmt, vals, comp, tipo, count, extra=None):
        while len(blob) % 4:
            blob.append(0)
        datos = struct.pack('<' + fmt * len(vals), *vals)
        vistas.append({'buffer': 0, 'byteOffset': len(blob),
                       'byteLength': len(datos)})
        blob.extend(datos)
        a = {'bufferView': len(vistas) - 1, 'componentType': comp,
             'count': count, 'type': tipo}
        if extra:
            a.update(extra)
        accesores.append(a)
        return len(accesores) - 1

    # inverse bind matrices: en reposo los huesos son traslación pura
    # (rotación identidad) -> ibm = translate(-pos_mundo)
    ibm = []
    for n, _, _ in _HUESOS:
        x, y, z = pos_mundo[n]
        ibm += [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1]
    i_ibm = acc('f', ibm, 5126, 'MAT4', len(_HUESOS))

    # -- primitivas: una por parte, todas joint=(slot,0,0,0) w=1 -----
    primitivas, materiales = [], []
    mat_por_color = {}
    for hueso, (pos, nor), clave in _partes(alto, ancho, cabeza):
        rgb = tuple(v / 255.0 for v in col[clave]) + (1.0,)
        if rgb not in mat_por_color:
            mat_por_color[rgb] = len(materiales)
            materiales.append({'pbrMetallicRoughness': {
                'baseColorFactor': list(rgb),
                'metallicFactor': 0.0, 'roughnessFactor': 1.0}})
        n_v = len(pos)
        flat_pos = [c for v in pos for c in v]
        mins = [min(v[i] for v in pos) for i in range(3)]
        maxs = [max(v[i] for v in pos) for i in range(3)]
        slot = indice[hueso]        # joints referencian skin.joints
        i_pos = acc('f', flat_pos, 5126, 'VEC3', n_v,
                    {'min': mins, 'max': maxs})
        i_nor = acc('f', [c for v in nor for c in v], 5126, 'VEC3',
                    n_v)
        i_jts = acc('B', [slot, 0, 0, 0] * n_v, 5121, 'VEC4', n_v)
        i_wgt = acc('f', [1.0, 0.0, 0.0, 0.0] * n_v, 5126, 'VEC4',
                    n_v)
        primitivas.append({
            'attributes': {'POSITION': i_pos, 'NORMAL': i_nor,
                           'JOINTS_0': i_jts, 'WEIGHTS_0': i_wgt},
            'material': mat_por_color[rgb]})

    doc = {
        'asset': {'version': '2.0',
                  'generator': 'pilas3d.personaje'},
        'scene': 0,
        'scenes': [{'nodes': [indice['Hips'], i_mesh]}],
        'nodes': nodos,
        'skins': [{'joints': list(range(len(_HUESOS))),
                   'skeleton': indice['Hips'],
                   'inverseBindMatrices': i_ibm}],
        'meshes': [{'name': 'cuerpo', 'primitives': primitivas}],
        'materials': materiales,
        'bufferViews': vistas,
        'accessors': accesores,
        'buffers': [{'byteLength': len(blob)}],
    }

    _guardar_glb(ruta, doc, bytes(blob))
    return ruta


def _guardar_glb(ruta, doc, blob):
    """Escribe el contenedor binario glTF: header + chunk JSON +
    chunk BIN (cada chunk alineado a 4 bytes)."""
    js = json.dumps(doc, separators=(',', ':')).encode('utf-8')
    js += b' ' * (-len(js) % 4)
    blob += b'\0' * (-len(blob) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    d = os.path.dirname(ruta)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(ruta, 'wb') as f:
        f.write(struct.pack('<4sII', b'glTF', 2, total))
        f.write(struct.pack('<I4s', len(js), b'JSON') + js)
        f.write(struct.pack('<I4s', len(blob), b'BIN\0') + blob)
