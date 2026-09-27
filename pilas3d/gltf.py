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
- Materiales: solo ``baseColorFactor`` como color por vértice.

``cargar(ruta)`` retorna un dict con todo lo necesario para animar
por CPU (ver ``ModeloGLTF``).
"""

import base64
import json
import os
import struct

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


def cargar(ruta):
    """Parsea el archivo y retorna la escena en estructuras planas."""
    doc, blobs = _leer_archivo(ruta)
    vistas = doc.get('bufferViews', [])

    def acceso(i):
        """Lee el accessor i -> lista de tuplas (o floats si SCALAR)."""
        a = doc['accessors'][i]
        fmt, tam = _COMP[a['componentType']]
        n = _NCOMP[a['type']]
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
                'uvs': [list(v) for v in acceso(at['TEXCOORD_0'])]
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
                base_c = mat.get('pbrMetallicRoughness', {}) \
                           .get('baseColorFactor')
                if base_c:
                    entrada['color'] = tuple(base_c)
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


def _lerp(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


def _nlerp_quat(a, b, f):
    if sum(x * y for x, y in zip(a, b)) < 0:
        b = tuple(-y for y in b)
    v = [x + (y - x) * f for x, y in zip(a, b)]
    n = sum(c * c for c in v) ** 0.5 or 1.0
    return tuple(c / n for c in v)


def muestrear(animacion, t, nodos):
    """Aplica a ``nodos`` la pose de ``animacion`` en el tiempo t
    (modifica las listas 't'/'r'/'s' de los nodos animados)."""
    for c in animacion['canales']:
        tiempos, vals = c['tiempos'], c['valores']
        if t <= tiempos[0]:
            v = vals[0]
        elif t >= tiempos[-1]:
            v = vals[-1]
        else:
            i = 0
            while tiempos[i + 1] < t:
                i += 1
            if c['interp'] == 'STEP':
                v = vals[i]
            else:
                f = (t - tiempos[i]) / (tiempos[i + 1] - tiempos[i])
                if c['camino'] == 'rotation':
                    v = _nlerp_quat(vals[i], vals[i + 1], f)
                else:
                    v = _lerp(vals[i], vals[i + 1], f)
        nodo = nodos[c['nodo']]
        nodo['t' if c['camino'] == 'translation'
             else 'r' if c['camino'] == 'rotation' else 's'] = list(v)
