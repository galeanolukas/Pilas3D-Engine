# -*- encoding: utf-8 -*-
"""Cargador glTF 2.0 (.gltf/.glb) — meshes, skins y animaciones.

Soporte deliberadamente acotado (motor educativo):

- Un solo archivo: .glb binario o .gltf JSON con buffers .bin
  (o data: URIs base64) relativos al archivo.
- Primitivas solo modo TRIANGLES (4).
- Atributos: POSITION, NORMAL, TEXCOORD_0, JOINTS_0, WEIGHTS_0,
  indices opcionales.
- Una sola skin y animaciones de nodos (translation/rotation/scale)
  con interpolación LINEAR o STEP.
- Materiales: ``baseColorFactor`` como color por vértice y
  ``baseColorTexture`` (primera textura encontrada: PNG/JPEG externa,
  data URI o embebida en el .glb).

``cargar(ruta)`` retorna un dict con todo lo necesario para animar
por CPU (ver ``ModeloGLTF``).
"""

import base64
import json
import os
import struct
import urllib.parse

from pyglet.math import Mat4, Quaternion, Vec3

_COMP = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2),
         5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
_NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4,
          'MAT2': 4, 'MAT3': 9, 'MAT4': 16}


def _leer_archivo(ruta):
    """Retorna (json, [blobs_binarios])."""
    with open(ruta, 'rb') as f:
        datos = f.read()
    if datos[:4] == b'glTF':                       # .glb
        _, _, largo = struct.unpack('<4sII', datos[:12])
        pos, doc, blob = 12, None, None
        while pos < largo:
            n, tipo = struct.unpack('<I4s', datos[pos:pos + 8])
            trozo = datos[pos + 8:pos + 8 + n]
            if tipo == b'JSON':
                doc = json.loads(trozo.decode('utf-8'))
            elif tipo[:3] == b'BIN':
                blob = trozo
            pos += 8 + n
        return doc, [blob] if blob else []

    doc = json.loads(datos.decode('utf-8'))       # .gltf
    base = os.path.dirname(ruta)
    blobs = []
    for buf in doc.get('buffers', []):
        uri = buf.get('uri', '')
        if uri.startswith('data:'):
            blobs.append(base64.b64decode(uri.split(',', 1)[1]))
        else:
            with open(os.path.join(base, uri), 'rb') as f:
                blobs.append(f.read())
    return doc, blobs


_cache = {}


def cargar(ruta):
    """Parsea el archivo y retorna la escena en estructuras planas.

    Cachea por ruta absoluta: dos ``ModeloGLTF`` del mismo archivo
    no reparsen — reciben una copia profunda (cada uno puede mutar
    nodos/animaciones sin contaminar al otro ni al caché)."""
    import copy
    clave = os.path.abspath(ruta)
    if clave in _cache:
        return copy.deepcopy(_cache[clave])
    escena = _cargar_crudo(ruta)
    _cache[clave] = copy.deepcopy(escena)
    return escena


def _cargar_crudo(ruta):
    doc, blobs = _leer_archivo(ruta)
    vistas = doc.get('bufferViews', [])

    def acceso(i):
        """Lee el accessor i -> lista de tuplas (o floats si SCALAR)."""
        a = doc['accessors'][i]
        fmt, tam = _COMP[a['componentType']]
        n = _NCOMP[a['type']]
        if 'bufferView' not in a:
            # spec glTF: accessor sin bufferView arranca en ceros
            cero = (0.0,) * n if fmt == 'f' else (0,) * n
            return [cero[0] if n == 1 else cero for _ in
                    range(a['count'])]
        v = vistas[a['bufferView']]
        blob = blobs[v.get('buffer', 0)]
        base = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = v.get('byteStride') or n * tam
        out = []
        for e in range(a['count']):
            vals = struct.unpack_from('<%d%s' % (n, fmt), blob,
                                      base + e * stride)
            out.append(vals[0] if n == 1 else vals)
        return out

    # -- nodos: jerarquía + TRS ------------------------------------------------
    nodos = []
    for n in doc.get('nodes', []):
        t = n.get('translation', (0.0, 0.0, 0.0))
        r = n.get('rotation', (0.0, 0.0, 0.0, 1.0))     # xyzw
        s = n.get('scale', (1.0, 1.0, 1.0))
        nodos.append({
            'nombre': n.get('name', ''),
            'padre': -1,
            'hijos': list(n.get('children', [])),
            'matriz': Mat4(*n['matrix']) if 'matrix' in n else None,
            't': list(t), 'r': list(r), 's': list(s),
        })
    for i, n in enumerate(nodos):
        for h in n['hijos']:
            nodos[h]['padre'] = i
    raices = [i for i, n in enumerate(nodos) if n['padre'] < 0]
    if not raices:
        raices = list(range(len(nodos)))

    # -- meshes ----------------------------------------------------------------
    mallas = []
    for mesh_idx, mesh in enumerate(doc.get('meshes', [])):
        for p in mesh.get('primitives', []):
            if p.get('mode', 4) != 4:
                continue   # solo triángulos
            at = p['attributes']
            entrada = {
                'posiciones': [list(v) for v in
                               acceso(at['POSITION'])],
                'normales': [list(v) for v in
                             acceso(at['NORMAL'])] if 'NORMAL' in at
                            else None,
                # glTF: el origen V del texcoord es arriba-izquierda;
                # OpenGL/pyglet esperan abajo-izquierda -> flip de V
                'uvs': [[v[0], 1.0 - v[1]]
                        for v in acceso(at['TEXCOORD_0'])]
                       if 'TEXCOORD_0' in at else None,
                'articulaciones': [list(v) for v in
                                   acceso(at['JOINTS_0'])]
                                if 'JOINTS_0' in at else None,
                'pesos': [list(v) for v in acceso(at['WEIGHTS_0'])]
                         if 'WEIGHTS_0' in at else None,
                'indices': acceso(p['indices'])
                           if 'indices' in p else None,
                'nodo': None,
                'mesh_idx': mesh_idx,
                'color': (1.0, 1.0, 1.0, 1.0),
            }
            if 'material' in p:
                mat = doc.get('materials', [])[p['material']]
                pbr = mat.get('pbrMetallicRoughness', {})
                base_c = pbr.get('baseColorFactor')
                if base_c:
                    entrada['color'] = tuple(base_c)
                imagen = _extraer_imagen(doc, vistas, blobs,
                                         pbr.get('baseColorTexture'),
                                         os.path.dirname(ruta))
                if imagen is not None:
                    entrada['imagen'] = imagen
            mallas.append(entrada)

    # a qué nodo cuelga cada mesh (para pose de reposo)
    for i, n in enumerate(doc.get('nodes', [])):
        if 'mesh' in n:
            for m in mallas:
                if m['mesh_idx'] == n['mesh']:
                    m['nodo'] = i

    # -- skin -------------------------------------------------------------------
    skin = None
    if doc.get('skins'):
        s = doc['skins'][0]
        skin = {
            'articulaciones': list(s['joints']),
            'ibm': [Mat4(*m) for m in
                    acceso(s['inverseBindMatrices'])],
        }

    # -- animaciones ------------------------------------------------------------
    animaciones = {}
    for anim in doc.get('animations', []):
        canales = []
        for ch in anim['channels']:
            tgt = ch['target']
            if tgt.get('path') not in ('translation', 'rotation',
                                       'scale'):
                continue
            smp = anim['samplers'][ch['sampler']]
            canales.append({
                'nodo': tgt['node'],
                'camino': tgt['path'],
                'tiempos': acceso(smp['input']),
                'valores': acceso(smp['output']),
                'interp': smp.get('interpolation', 'LINEAR'),
            })
        if canales:
            dur = max(c['tiempos'][-1] for c in canales)
            animaciones[anim.get('name', 'anim%d' % len(animaciones))] = {
                'canales': canales, 'duracion': dur,
            }

    return {'mallas': mallas, 'nodos': nodos, 'raices': raices,
            'skin': skin, 'animaciones': animaciones}


def _extraer_imagen(doc, vistas, blobs, textura, base_dir):
    """Extrae la imagen de un ``textureInfo`` (baseColorTexture).

    Retorna una ruta de archivo si es externa, o ``bytes`` si viene
    embebida (bufferView del .glb o data URI)."""
    if not textura:
        return None
    fuentes = doc.get('textures', [])
    if textura.get('index', 0) >= len(fuentes):
        return None
    src = fuentes[textura['index']].get('source')
    if src is None or src >= len(doc.get('images', [])):
        return None
    img = doc['images'][src]
    if 'uri' in img:
        uri = urllib.parse.unquote(img['uri'])
        if uri.startswith('data:'):
            return base64.b64decode(uri.split(',', 1)[1])
        return os.path.join(base_dir, uri)
    if 'bufferView' in img:
        v = vistas[img['bufferView']]
        blob = blobs[v.get('buffer', 0)]
        ini = v.get('byteOffset', 0)
        return blob[ini:ini + v['byteLength']]
    return None


# -- evaluación de pose --------------------------------------------------------


def _matriz_local(nodo):
    if nodo['matriz'] is not None:
        return nodo['matriz']
    # glTF es (x,y,z,w); pyglet (w,x,y,z) y con la convención
    # conjugada (su to_mat4 rota al revés) -> conjugar
    x, y, z, w = nodo['r']
    q = Quaternion(w, -x, -y, -z)
    return Mat4.from_translation(Vec3(*nodo['t'])) \
        @ q.to_mat4() @ Mat4.from_scale(Vec3(*nodo['s']))


def matrices_globales(escena):
    """Matriz mundo de cada nodo en la pose actual (TRS ya muestreado)."""
    nodos = escena['nodos']
    glob = [None] * len(nodos)

    def bajar(i, padre):
        g = _matriz_local(nodos[i]) if padre is None \
            else padre @ _matriz_local(nodos[i])
        glob[i] = g
        for h in nodos[i]['hijos']:
            bajar(h, g)

    for r in escena['raices']:
        bajar(r, None)
    return glob


# -- quaternions en convención glTF (x, y, z, w) ------------------------------


def qmul(a, b):
    """Producto a⊗b de quaternions (x,y,z,w): aplica b, luego a."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz)


def quat_eje(eje, grados):
    """Quaternion de rotación de ``grados`` alrededor de 'x'|'y'|'z'."""
    import math as _m
    a = _m.radians(grados) / 2.0
    s, c = _m.sin(a), _m.cos(a)
    if eje == 'x':
        return (s, 0.0, 0.0, c)
    if eje == 'y':
        return (0.0, s, 0.0, c)
    return (0.0, 0.0, s, c)


def _lerp(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


def _nlerp_quat(a, b, f):
    if sum(x * y for x, y in zip(a, b)) < 0:
        b = tuple(-y for y in b)
    v = [x + (y - x) * f for x, y in zip(a, b)]
    n = sum(c * c for c in v) ** 0.5 or 1.0
    return tuple(c / n for c in v)


def _valor_en(canal, t):
    """Valor interpolado del canal en el tiempo ``t``."""
    tiempos, vals = canal['tiempos'], canal['valores']
    if t <= tiempos[0]:
        return vals[0]
    if t >= tiempos[-1]:
        return vals[-1]
    i = 0
    while tiempos[i + 1] < t:
        i += 1
    if canal['interp'] == 'STEP':
        return vals[i]
    f = (t - tiempos[i]) / (tiempos[i + 1] - tiempos[i])
    if canal['camino'] == 'rotation':
        return _nlerp_quat(vals[i], vals[i + 1], f)
    return _lerp(vals[i], vals[i + 1], f)


_CLAVES = {'translation': 't', 'rotation': 'r', 'scale': 's'}


def muestrear(animacion, t, nodos):
    """Aplica a ``nodos`` la pose de ``animacion`` en el tiempo t
    (modifica las listas 't'/'r'/'s' de los nodos animados)."""
    for c in animacion['canales']:
        nodo = nodos[c['nodo']]
        nodo[_CLAVES[c['camino']]] = list(_valor_en(c, t))


def muestrear_mezcla(clips, nodos, base):
    """Blend tree: mezcla varios clips con peso en ``nodos``.

    ``clips`` es una lista de ``(animacion, t, peso)`` — cada clip se
    samplea en su propio tiempo. Los pesos se normalizan; la parte
    que un clip no anima se completa desde ``base`` (la lista
    ``_trs_orig``: ``base[i] = (t, r, s)`` de la pose de carga).
    """
    total = sum(p for _, _, p in clips) or 1.0
    # (nodo, camino) -> [(valor, peso)]
    por_canal = {}
    for anim, t, peso in clips:
        if peso <= 0:
            continue
        for c in anim['canales']:
            clave = (c['nodo'], c['camino'])
            por_canal.setdefault(clave, []).append(
                (_valor_en(c, t), peso / total))

    for (i, camino), entradas in por_canal.items():
        nodo = nodos[i]
        clave = _CLAVES[camino]
        falta = 1.0 - sum(p for _, p in entradas)
        if falta > 1e-9:
            t0, r0, s0 = base[i]
            v_base = {'t': t0, 'r': r0, 's': s0}[clave]
            entradas = entradas + [(v_base, falta)]
        if camino == 'rotation':
            # nlerp acumulado con signos consistentes respecto al
            # primer quaternion (evita el "camino largo")
            ref = entradas[0][0]
            acc = [0.0, 0.0, 0.0, 0.0]
            for v, p in entradas:
                if sum(x * y for x, y in zip(ref, v)) < 0:
                    v = tuple(-x for x in v)
                for k in range(4):
                    acc[k] += v[k] * p
            n = sum(c * c for c in acc) ** 0.5 or 1.0
            nodo['r'] = [c / n for c in acc]
        else:
            acc = [0.0, 0.0, 0.0]
            for v, p in entradas:
                for k in range(3):
                    acc[k] += v[k] * p
            nodo[clave] = acc
