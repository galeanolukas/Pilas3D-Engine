# -*- encoding: utf-8 -*-
"""Actor que dibuja un modelo glTF 2.0 (.gltf/.glb) con animación
esquelética por CPU.

>>> caballero = pilas.actores.ModeloGLTF('caballero.glb', escala=0.5)
>>> caballero.animar('caminar')

El skinning se calcula en Python y se escribe en el vertex list cada
frame (como ``ModeloAnimado``): sirve para modelos de pocos miles de
vértices; modelos grandes van a ir lentos — para eso haría falta
skinning en GPU por shader.

Soporte acotado: ver ``pilas3d.gltf`` (una sola skin, color plano
``baseColorFactor`` + primera ``baseColorTexture`` como textura).
"""

import math

from pyglet.gl import GL_TRIANGLES, GL_TEXTURE_2D, \
    GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_REPEAT, glBindTexture, \
    glTexParameteri

from pilas3d import gltf, shaders
from pilas3d.actores.actor import Actor


class ModeloGLTF(Actor):

    def __init__(self, pilas, ruta, x=0, y=0, z=0, escala=1.0,
                 animacion=None, velocidad=1.0, ciclica=True):
        self.ruta = ruta
        self._escena = gltf.cargar(ruta)
        self.velocidad = velocidad
        self.ciclica = ciclica
        self.animacion = None
        self._mezcla = None           # {nombre: peso} (blend tree)
        self._t = 0.0
        self._armar_malla()
        # pose original (para reiniciar_pose / edición)
        self._trs_orig = [(n['t'][:], n['r'][:], n['s'][:])
                          for n in self._escena['nodos']]
        self._listas = None          # vertex lists por material
        self._tex_cache = {}         # imagen -> textura GL (por actor)
        super(ModeloGLTF, self).__init__(pilas, x=x, y=y, z=z)
        self.escala = escala
        self._cargar_anims_junto_al_modelo()
        if animacion:
            self.animar(animacion)

    def _cargar_anims_junto_al_modelo(self):
        """Registra automáticamente los ``<modelo>[.<nombre>].anim.json``
        que haya junto al .glb (un clip o lista de clips por archivo)."""
        import glob
        import os
        import re
        base = os.path.splitext(self.ruta)[0]
        patron = re.compile('^%s\\.(?:[^.]+\\.)?anim\\.json$'
                            % re.escape(os.path.basename(base)))
        for f in sorted(glob.glob(base + '*.anim.json')):
            if not patron.match(os.path.basename(f)):
                continue
            try:
                self.cargar_animacion(f)
            except Exception:
                pass          # json roto o incompatible: no molesta

    # -- render por material ------------------------------------------------
    # Cada primitiva glTF puede tener su propia textura y color: el actor
    # mantiene un vertex_list por grupo de material (``_listas``) en vez
    # de uno único — así un modelo multi-material no muestra la primera
    # textura pegada en todas sus partes.

    def _textura_de(self, img):
        """Convierte ``imagen`` del gltf (ruta o bytes) en textura GL."""
        if isinstance(img, bytes):
            import io
            from pyglet.image import load as _load
            ext = '.png' if img[:4] == b'\x89PNG' else '.jpg'
            img = _load('textura' + ext, file=io.BytesIO(img))
        elif isinstance(img, str):
            from pyglet.image import load as _load
            img = _load(self._resolver_imagen(img))
        tex = img.get_texture()
        glBindTexture(GL_TEXTURE_2D, tex.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        return tex

    def _construir_gl(self):
        programa = shaders.obtener_programa()
        col_tint = self._colores_efectivos(self._col,
                                           len(self._col) // 4)
        self._listas = []
        for g in self._grupos:
            v0, v1 = g['v0'], g['v1']
            vl = programa.vertex_list_indexed(
                v1 - v0, GL_TRIANGLES, g['indices'],
                position=('f', self._pos[v0 * 3:v1 * 3]),
                normal=('f', self._nor[v0 * 3:v1 * 3]),
                color=('f', col_tint[v0 * 4:v1 * 4]),
                texcoords=('f', self._uv[v0 * 2:v1 * 2]))
            self._listas.append({'vl': vl, 'imagen': g['imagen'],
                                 'tex': None})
        # compat: el primer grupo sigue siendo ``_vertex_list``
        self._vertex_list = self._listas[0]['vl'] if self._listas \
            else None

    def dibujar(self):
        """Una pasada por grupo de material, cada uno con su textura."""
        if self._listas is None:
            self._construir_gl()
        programa = shaders.obtener_programa()
        programa['modelo'] = self.matriz_modelo()
        programa['punto_tamano'] = getattr(self, 'punto_tamano', 1.0)
        programa['uv_escala'] = self._uv_escala
        programa['uv_desplazamiento'] = self._uv_desplazamiento
        programa['sin_luz'] = self.sin_luz
        if self._imagen is not None:
            # textura forzada por el usuario: una para todo el modelo
            if self._textura is None:
                self._cargar_textura()
            glBindTexture(GL_TEXTURE_2D, self._textura.id)
            programa['usar_textura'] = True
            for g in self._listas:
                g['vl'].draw(GL_TRIANGLES)
            return
        for g in self._listas:
            if g['imagen'] is not None:
                if g['tex'] is None:
                    # cache: muchas primitivas comparten la misma
                    # imagen (atlas) — se decodifica una sola vez
                    g['tex'] = self._tex_cache.get(g['imagen'])
                    if g['tex'] is None:
                        g['tex'] = self._textura_de(g['imagen'])
                        self._tex_cache[g['imagen']] = g['tex']
                glBindTexture(GL_TEXTURE_2D, g['tex'].id)
                programa['usar_textura'] = True
            else:
                programa['usar_textura'] = False
            g['vl'].draw(GL_TRIANGLES)

    def _reconstruir_gl(self):
        for g in getattr(self, '_listas', None) or []:
            g['vl'].delete()
        self._listas = None
        self._vertex_list = None        # ya quedó borrada arriba
        super(ModeloGLTF, self)._reconstruir_gl()

    def eliminar(self):
        for g in getattr(self, '_listas', None) or []:
            g['vl'].delete()
        self._listas = None
        self._vertex_list = None
        super(ModeloGLTF, self).eliminar()

    # -- carga ------------------------------------------------------------------

    def _armar_malla(self):
        """Aplana las primitivas conservando vértices únicos + índices
        (vertex list indexado): no se expanden índices, así el skinning
        por CPU trabaja una vez por vértice real en vez de por cada
        referencia — en modelos con índices rinde ~5x mejor."""
        pos, nor, uv, col = [], [], [], []
        bind_v, bind_n = [], []
        joints, pesos = [], []
        indices = []
        self._grupos = []             # un grupo por primitiva/material
        self._con_piel = False

        escena = self._escena
        glob = gltf.matrices_globales(escena)

        for m in escena['mallas']:
            base = len(pos) // 3          # offset de vértices del mesh
            idx = m['indices'] or list(range(len(m['posiciones'])))
            self._grupos.append({
                'v0': base,
                'v1': base + len(m['posiciones']),
                'indices': list(idx),      # locales: ya son del mesh
                'imagen': m.get('imagen'),
            })
            indices += [base + i for i in idx]
            # transformación del nodo que cuelga el mesh (pose de reposo)
            gn = glob[m['nodo']] if m['nodo'] is not None else None
            n_vert = len(m['posiciones'])
            for i in range(n_vert):
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
        self._indices = indices
        # solo los pares (articulación, peso) != 0 — el loop de
        # skinning no recorre pesos nulos
        self._skin = [
            tuple((j, w) for j, w in zip(js, ws) if w != 0.0)
            for js, ws in zip(joints, pesos)]

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

    @property
    def es_animado(self):
        """True si el archivo trae esqueleto (skin) — los modelos
        'rígidos' (nodos sin joints) son estáticos."""
        return bool(self._con_piel)

    @property
    def es_estatico(self):
        return not self._con_piel

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
        self._mezcla = None
        if ciclica is not None:
            self.ciclica = ciclica
        self._t = 0.0

    def detener(self):
        self.animacion = None
        self._mezcla = None

    # -- blend trees -----------------------------------------------------

    def mezclar(self, a, b, peso=0.5):
        """Mezcla dos clips con ``peso`` de 0 a 1 (0 = todo ``a``,
        1 = todo ``b``). Los dos relojes avanzan juntos; la pose
        resultante interpola hueso por hueso.

        >>> mono.mezclar('idle', 'caminar', 0.3)   # 30% caminar
        """
        self._mezcla = {a: 1.0 - peso, b: float(peso)}
        self.animacion = None
        self._t = 0.0
        self._clips_mezcla()          # valida que existan

    def arbol_mezcla(self, puntos, parametro):
        """Blend tree 1D: ``puntos`` es ``[(valor, 'anim'), ...]`` en
        orden creciente; ``parametro`` interpola entre los vecinos.

        >>> mono.arbol_mezcla([(0, 'idle'), (1, 'walk'), (2, 'run')],
        ...                   velocidad)   # idle->walk->run suave
        """
        orden = sorted(puntos)
        if parametro <= orden[0][0]:
            pesos = {orden[0][1]: 1.0}
        elif parametro >= orden[-1][0]:
            pesos = {orden[-1][1]: 1.0}
        else:
            for (v0, a), (v1, b) in zip(orden, orden[1:]):
                if v0 <= parametro <= v1:
                    f = (parametro - v0) / (v1 - v0 or 1e-6)
                    pesos = {a: 1.0 - f, b: f}
                    break
        self._mezcla = pesos
        self.animacion = None
        self._t = 0.0
        self._clips_mezcla()

    def _clips_mezcla(self):
        """[(animacion, peso)] de la mezcla activa, validando nombres."""
        anims = self._escena['animaciones']
        for nombre in self._mezcla:
            if nombre not in anims:
                raise ValueError("el modelo no tiene la animación "
                                 "'%s' (tiene: %s)"
                                 % (nombre, self.animaciones()))
        return [(anims[n], p) for n, p in self._mezcla.items()]

    # -- edición de pose (editor de personajes) ----------------------------

    def huesos(self):
        """Lista ``(indice_nodo, nombre)`` de las articulaciones."""
        skin = self._escena.get('skin')
        if not skin:
            return []
        nodos = self._escena['nodos']
        return [(j, nodos[j]['nombre'] or 'hueso_%d' % j)
                for j in skin['articulaciones']]

    def rotar_hueso(self, hueso, eje, grados):
        """Rota una articulación local ``grados`` alrededor de 'x'/'y'/'z'.

        ``hueso`` es el índice de nodo (o su nombre). Tras rotar hay que
        llamar a ``refrescar_pose()`` para ver el cambio."""
        i = self._indice_hueso(hueso)
        nodo = self._escena['nodos'][i]
        nodo['r'] = list(gltf.qmul(tuple(nodo['r']),
                                   gltf.quat_eje(eje, grados)))

    def mover_hueso(self, hueso, dx=0.0, dy=0.0, dz=0.0):
        """Desplaza localmente la articulación (stretch, offsets)."""
        i = self._indice_hueso(hueso)
        t = self._escena['nodos'][i]['t']
        t[0] += dx
        t[1] += dy
        t[2] += dz

    def posicion_hueso(self, hueso):
        """Posición mundo de una articulación en la pose actual."""
        i = self._indice_hueso(hueso)
        g = gltf.matrices_globales(self._escena)[i]
        return (self.x + g[12] * self.escala,
                self.y + g[13] * self.escala,
                self.z + g[14] * self.escala)

    def reiniciar_pose(self):
        """Vuelve a la pose de carga del archivo."""
        for nodo, (t, r, s) in zip(self._escena['nodos'], self._trs_orig):
            nodo['t'], nodo['r'], nodo['s'] = t[:], r[:], s[:]
        self.refrescar_pose()

    def refrescar_pose(self):
        """Recomputa la piel con la pose actual (sin animación)."""
        self._aplicar_piel()

    def _pose_actual(self):
        """Dict ``{indice: {'r','t','s','nombre'}}`` de los huesos."""
        nodos = self._escena['nodos']
        return {str(j): {'nombre': nodos[j]['nombre'],
                         'r': list(nodos[j]['r']),
                         't': list(nodos[j]['t']),
                         's': list(nodos[j]['s'])}
                for j, _ in self.huesos()}

    def guardar_pose(self, ruta):
        """Guarda la pose actual en JSON: ``{indice: rot_xyzw}``."""
        import json
        with open(ruta, 'w') as f:
            json.dump(self._pose_actual(), f, indent=1)

    def cargar_pose(self, ruta):
        """Aplica una pose guardada con ``guardar_pose``."""
        import json
        with open(ruta) as f:
            datos = json.load(f)
        self.aplicar_pose(datos)

    def aplicar_pose(self, datos):
        """Aplica un dict de pose como el que devuelve
        ``_pose_actual``/``guardar_pose`` (``{indice: {'r','t','s'}}``)."""
        nodos = self._escena['nodos']
        for i, d in datos.items():
            nodos[int(i)]['r'] = list(d['r'])
            if 't' in d:
                nodos[int(i)]['t'] = list(d['t'])
            if 's' in d:
                nodos[int(i)]['s'] = list(d['s'])
        self.refrescar_pose()

    def crear_animacion(self, nombre, poses, duracion=0.5):
        """Crea un clip de animación interpolando entre poses.

        ``poses`` es una lista de dicts como los que escribe
        ``guardar_pose`` (``{indice_nodo: {'r': [...], ...}}``) — cada
        pose es un keyframe; ``duracion`` son los segundos *entre*
        keyframes. El clip queda disponible para ``animar(nombre)``
        y la escena lo reproduce con interpolación LINEAR de
        quaternions (nlerp), igual que las animaciones del archivo.
        """
        nodos = self._escena['nodos']
        tiempos = [k * duracion for k in range(len(poses))]
        canales = []
        tocados = sorted({int(i) for pose in poses for i in pose})
        for i in tocados:
            base = nodos[i]
            for camino, clave in (('rotation', 'r'),
                                  ('translation', 't'),
                                  ('scale', 's')):
                valores = [list(pose[str(i)].get(clave, base[clave]))
                           if str(i) in pose else list(base[clave])
                           for pose in poses]
                if any(v != valores[0] for v in valores):
                    canales.append({'nodo': i, 'camino': camino,
                                    'nodo_nombre': base['nombre'],
                                    'tiempos': tiempos,
                                    'valores': valores,
                                    'interp': 'LINEAR'})
        if not canales:
            raise ValueError("las poses son iguales: no hay animación")
        self._escena['animaciones'][nombre] = {
            'canales': canales,
            'duracion': tiempos[-1] or duracion}
        return nombre

    def guardar_animacion(self, ruta, nombre=None):
        """Exporta un clip a JSON (p. ej. uno hecho con
        ``crear_animacion``). ``nombre`` es el clip activo por
        defecto."""
        import json
        nombre = nombre or self.animacion
        if nombre not in self._escena['animaciones']:
            raise ValueError("no hay animación '%s' (tiene: %s)"
                             % (nombre, self.animaciones()))
        anim = self._escena['animaciones'][nombre]
        with open(ruta, 'w') as f:
            json.dump({'nombre': nombre, 'duracion': anim['duracion'],
                       'canales': anim['canales']}, f)

    def cargar_animacion(self, ruta):
        """Importa clips JSON guardados con ``guardar_animacion``.

        Acepta un solo clip ``{'nombre', 'duracion', 'canales'}`` o
        una lista de ellos. Devuelve el nombre (o la lista de
        nombres) registrado — listo para ``animar``."""
        import json
        with open(ruta) as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            datos = [datos]
        nombres = []
        for clip in datos:
            canales = [self._canal_resuelto(c) for c in
                       clip['canales']]
            self._escena['animaciones'][clip['nombre']] = {
                'canales': [c for c in canales if c],
                'duracion': clip['duracion']}
            nombres.append(clip['nombre'])
        return nombres[0] if len(nombres) == 1 else nombres

    def _canal_resuelto(self, canal):
        """Valida el índice de nodo del canal contra el esqueleto.

        Los .anim.json guardan 'nodo' (índice) y 'nodo_nombre': si el
        .glb se re-exportó y cambió el orden de nodos, se remapea por
        nombre. Sin coincidencia, el canal se descarta."""
        nodos = self._escena['nodos']
        i = canal.get('nodo', -1)
        nombre = canal.get('nodo_nombre')
        if 0 <= i < len(nodos) and (nombre is None or
                                    nodos[i]['nombre'] == nombre):
            return canal
        if nombre:
            for j, n in enumerate(nodos):
                if n['nombre'] == nombre:
                    c = dict(canal)
                    c['nodo'] = j
                    return c
        return None

    def _indice_hueso(self, hueso):
        """Acepta índice de nodo, índice de articulación o nombre."""
        skin = self._escena.get('skin')
        if skin is None:
            raise ValueError("el modelo no tiene esqueleto")
        nodos = self._escena['nodos']
        if isinstance(hueso, str):
            for j in skin['articulaciones']:
                if nodos[j]['nombre'] == hueso:
                    return j
            raise ValueError("no existe el hueso '%s'" % hueso)
        if hueso in skin['articulaciones']:
            return hueso
        return skin['articulaciones'][hueso]

    def actualizar(self):
        if self._mezcla is not None:
            self._t += self.pilas.dt * self.velocidad
            clips = [(anim, self._t % (anim['duracion'] or 1e-6), p)
                     for anim, p in self._clips_mezcla()]
            gltf.muestrear_mezcla(clips, self._escena['nodos'],
                                  self._trs_orig)
            self._aplicar_piel()
            return
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
        if not self._con_piel or not self._listas:
            return
        escena = self._escena
        skin = escena['skin']
        glob = gltf.matrices_globales(escena)
        J = [tuple(glob[j] @ ibm) for j, ibm in
             zip(skin['articulaciones'], skin['ibm'])]

        pos, nor = [], []
        for (px, py, pz), (nx, ny, nz), pares in zip(
                self._bind_v, self._bind_n, self._skin):
            x = y = z = 0.0
            ax = ay = az = 0.0
            for j, w in pares:
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
        # posiciones skinneadas de este frame: pilas.web las usa
        # para reflejar la animación en los navegadores
        self._pos_skin = pos
        self._nor_skin = nor
        self._geo_version = getattr(self, '_geo_version', 0) + 1
        for g, lst in zip(self._grupos, self._listas):
            v0, v1 = g['v0'], g['v1']
            lst['vl'].position[:] = pos[v0 * 3:v1 * 3]
            lst['vl'].normal[:] = nor[v0 * 3:v1 * 3]
