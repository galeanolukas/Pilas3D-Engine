# -*- encoding: utf-8 -*-
"""Hola mundo de pilas3d: un cubo girando sobre un piso con ejes."""

import pilas3d
from pilas3d.actores.actor import Actor
from pilas3d import mallas


class CuboGiratorio(Actor):
    """Un actor propio: heredá de Actor y redefiní actualizar."""

    def _generar_geometria(self):
        return mallas.cubo(2.0)

    def actualizar(self):
        self.rotacion_y += 60 * self.pilas.dt
        self.rotacion_x += 30 * self.pilas.dt


pilas = pilas3d.iniciar(titulo="pilas3d - hola cubo")

cubo = CuboGiratorio(pilas, y=1)
cubo.color = pilas.colores.celeste

pilas.actores.Piso()
pilas.actores.Ejes()
pilas.actores.Esfera(x=4, y=1, radio=0.8)

pilas.ejecutar()
