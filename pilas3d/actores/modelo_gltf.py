# -*- encoding: utf-8 -*-
"""Actor que dibuja un modelo glTF 2.0 (.gltf/.glb) con animación
esquelética por CPU.

>>> caballero = pilas.actores.ModeloGLTF('caballero.glb', escala=0.5)
>>> caballero.animar('caminar')

El skinning se calcula en Python y se escribe en el vertex list cada
frame (como ``ModeloAnimado``): sirve para modelos de pocos miles de
vértices; modelos grandes van a ir lentos — para eso haría falta
skinning en GPU por shader.

Soporte acotado: ver ``pilas3d.gltf`` (un solo mesh visible de la
primera skin, color plano del material, sin texturas PBR todavía).
"""

import math

from pyglet.gl import GL_TRIANGLES

from pilas3d import gltf
from pilas3d.actores.actor import Actor


class ModeloGLTF(Actor):

    def __init__(self, pilas, ruta, x=0, y=0, z=0, escala=1.0,
                 animacion=None, velocidad=1.0, ciclica=True):
        self.ruta = ruta
        self._escena = gltf.cargar(ruta)
        self.velocidad = velocidad
        self.ciclica = ciclica
        self.animacion = None
        self._t = 0.0
        self._armar_malla()
        super(ModeloGLTF, self).__init__(pilas, x=x, y=y, z=z)
        self.escala = escala
        if animacion:
            self.animar(animacion)

    # -- carga ------------------------------------------------------------------

    def _armar_malla(self):
        """Aplana las primitivas: atributos por vértice del vertex list
        (expandiendo índices) + datos de bind para el skinning."""
        pos, nor, uv, col = [], [], [], []
        bind_v, bind_n = [], []
        joints, pesos = [], []
        self._con_piel = False

        escena = self._escena
        glob = gltf.matrices_globales(escena)

        for m in escena['mallas']:
            idx = m['indices'] or range(len(m['posiciones']))
            # transformación del nodo que cuelga el mesh (pose de reposo)
            gn = glob[m['nodo']] if m['nodo'] is not None else None
            for i in idx:
                p = list(m['posiciones'][i])
                n = list(m['normales'][i]) if m['normales'] else [0, 0, 0]
                if gn is not None and not m['articulaciones']:
                    # mesh rígido: bake de la transformación del nodo
                    p = [gn[0] * p[0] + gn[4] * p[1] + gn[8] * p[2]
                         + gn[12],
                         gn[1] * p[0] + gn[5] * p[1] + gn[9] * p[2]
                         + gn[13],
                         gn[2] * p[0] + gn[6] * p[1] + gn[10] * p[2]
                         + gn[14]]
                    n = [gn[0] * n[0] + gn[4] * n[1] + gn[8] * n[2],
                         gn[1] * n[0] + gn[5] * n[1] + gn[9] * n[2],
                         gn[2] * n[0] + gn[6] * n[1] + gn[10] * n[2]]
                pos += p
                nor += n
                bind_v.append(tuple(p))
                bind_n.append(tuple(n))
                uv += m['uvs'][i] if m['uvs'] else (0.0, 0.0)
                col += m['color']
                if m['articulaciones']:
                    self._con_piel = True
                    joints.append(tuple(m['articulaciones'][i]))
                    pesos.append(tuple(m['pesos'][i]))
                else:
                    joints.append((0, 0, 0, 0))
                    pesos.append((0.0, 0.0, 0.0, 0.0))

        self._pos = pos
        self._nor = nor
        self._uv = uv
        self._col = col
        self._bind_v = bind_v
        self._bind_n = bind_n
        self._joints = joints
        self._pesos = pesos

    def _generar_geometria(self):
        return list(self._pos), list(self._nor), GL_TRIANGLES, \
            list(self._col), list(self._uv)

    # -- animación ---------------------------------------------------------------

    def animaciones(self):
        """Nombres de las animaciones del archivo."""
        return sorted(self._escena['animaciones'])

    def animar(self, nombre=None, ciclica=None):
        """Reproduce ``nombre`` (o la primera si no se pasa)."""
        anims = self._escena['animaciones']
        if nombre is None:
            nombre = next(iter(sorted(anims)), None)
        if nombre not in anims:
            raise ValueError("el modelo no tiene la animación '%s' "
                             "(tiene: %s)" % (nombre, self.animaciones()))
        self.animacion = nombre
        if ciclica is not None:
            self.ciclica = ciclica
        self._t = 0.0

    def detener(self):
        self.animacion = None

    def actualizar(self):
        if self.animacion is None:
            return
        anim = self._escena['animaciones'][self.animacion]
        self._t += self.pilas.dt * self.velocidad
        if self._t > anim['duracion']:
            if self.ciclica:
                self._t %= anim['duracion'] or 1e-6
            else:
                self._t = anim['duracion']
        gltf.muestrear(anim, self._t, self._escena['nodos'])
        self._aplicar_piel()

    # -- skinning por CPU ---------------------------------------------------------

    def _aplicar_piel(self):
        if not self._con_piel or self._vertex_list is None:
            return
        escena = self._escena
        skin = escena['skin']
        glob = gltf.matrices_globales(escena)
        J = [tuple(glob[j] @ ibm) for j, ibm in
             zip(skin['articulaciones'], skin['ibm'])]

        pos, nor = [], []
        for (px, py, pz), (nx, ny, nz), js, ws in zip(
                self._bind_v, self._bind_n, self._joints, self._pesos):
            x = y = z = 0.0
            ax = ay = az = 0.0
            for j, w in zip(js, ws):
                if w == 0.0:
                    continue
                m = J[j]
                x += w * (m[0] * px + m[4] * py + m[8] * pz + m[12])
                y += w * (m[1] * px + m[5] * py + m[9] * pz + m[13])
                z += w * (m[2] * px + m[6] * py + m[10] * pz + m[14])
                ax += w * (m[0] * nx + m[4] * ny + m[8] * nz)
                ay += w * (m[1] * nx + m[5] * ny + m[9] * nz)
                az += w * (m[2] * nx + m[6] * ny + m[10] * nz)
            largo = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
            pos += [x, y, z]
            nor += [ax / largo, ay / largo, az / largo]
        self._vertex_list.position[:] = pos
        self._vertex_list.normal[:] = nor
