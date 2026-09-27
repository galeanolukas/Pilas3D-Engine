# -*- encoding: utf-8 -*-
"""Modelo 3D animado por secuencia de archivos .obj.

Es el equivalente 3D de ``Animacion``: en lugar de una grilla de
sprites usa un archivo .obj por cuadro (técnica estilo Quake II/MD2).

>>> zombie = pilas.actores.ModeloAnimado('modelos/zombie/cuadro*.obj')
>>> zombie = pilas.actores.ModeloAnimado(
...     ['f0.obj', 'f1.obj', 'f2.obj'], velocidad=10)

Con ``suavizar=True`` interpola los vértices entre cuadros (requiere
que todos tengan la misma cantidad de vértices, como hace MD2).
"""

import glob

from pyglet.gl import GL_TRIANGLES

from pilas3d import modelos, shaders
from pilas3d.actores.actor import Actor


class ModeloAnimado(Actor):
    """Una secuencia de modelos .obj reproducida en bucle o una vez."""

    def __init__(self, pilas, rutas, velocidad=8, ciclica=True,
                 suavizar=False, eliminar_al_terminar=False,
                 x=0, y=0, z=0, escala=1.0):
        if isinstance(rutas, str):
            rutas = sorted(glob.glob(rutas))
        if not rutas:
            raise IOError(
                "ModeloAnimado: no hay archivos .obj en %r" % rutas)
        self.cuadros = [modelos.cargar_obj(r) for r in rutas]
        self.velocidad = velocidad
        self.ciclica = ciclica
        self.eliminar_al_terminar = eliminar_al_terminar
        self._tiempo = 0.0
        self._cuadro = 0
        self.reproduciendo = True
        self._listas = None

        super(ModeloAnimado, self).__init__(pilas, x=x, y=y, z=z)
        self.escala = escala
        self.radio_de_colision = max(
            d['radio'] for d in self.cuadros) * escala

        cantidades = {len(d['posiciones']) for d in self.cuadros}
        if suavizar and len(cantidades) > 1:
            raise ValueError(
                "suavizar requiere que todos los cuadros tengan la "
                "misma cantidad de vértices (hay %s)" % cantidades)
        self.suavizar = suavizar

    def _generar_geometria(self):
        # _construir_gl propio arma todas las listas; igual hay que
        # definir esto por si alguien llama al método base.
        d = self.cuadros[0]
        return d['posiciones'], d['normales'], GL_TRIANGLES, \
            d['colores'], d['uvs']

    def _construir_gl(self):
        programa = shaders.obtener_programa()
        self._modo = GL_TRIANGLES
        self._listas = []
        for d in self.cuadros:
            cantidad = len(d['posiciones']) // 3
            colores_v = d['colores'] or self._colores_planos(cantidad)
            self._listas.append(programa.vertex_list(
                cantidad,
                GL_TRIANGLES,
                position=("f", d['posiciones']),
                normal=("f", d['normales']),
                color=("f", colores_v),
                texcoords=("f", d['uvs']),
            ))
        self._vertex_list = self._listas[0]

    @property
    def cuadro_actual(self):
        return self._cuadro

    @property
    def cantidad_de_cuadros(self):
        return len(self.cuadros)

    def definir_cuadro(self, cuadro):
        """Salta a un cuadro (como ``Animacion.definir_cuadro``)."""
        self._cuadro = cuadro % len(self.cuadros)
        self._tiempo = self._cuadro / float(self.velocidad)

    def pausar(self):
        self.reproduciendo = False

    def reproducir(self):
        self.reproduciendo = True

    def actualizar(self):
        if not self.reproduciendo or len(self.cuadros) < 2:
            return
        self._tiempo += self.pilas.dt
        f = self._tiempo * self.velocidad
        n = len(self.cuadros)
        if self.ciclica:
            i0 = int(f) % n
            i1 = (i0 + 1) % n
        else:
            i0 = min(int(f), n - 1)
            i1 = i0
            if i0 == n - 1:
                self.reproduciendo = False
                if self.eliminar_al_terminar:
                    self.eliminar()
                    return
        self._cuadro = i0
        if self._listas is None:
            return  # todavía no se dibujó nada (sin ventana)
        if not self.suavizar:
            self._vertex_list = self._listas[i0]
            return
        # Interpolación de vértices y normales entre dos cuadros.
        t = f - int(f)
        p0, p1 = (self.cuadros[i]['posiciones']
                  for i in (i0, i1))
        self._vertex_list.position[:] = [
            a + (b - a) * t for a, b in zip(p0, p1)]
        n0, n1 = (self.cuadros[i]['normales']
                  for i in (i0, i1))
        self._vertex_list.normal[:] = [
            a + (b - a) * t for a, b in zip(n0, n1)]

    def _reconstruir_gl(self):
        if self._listas is not None:
            for lista in self._listas:
                lista.delete()
            self._listas = None
        self._vertex_list = None
