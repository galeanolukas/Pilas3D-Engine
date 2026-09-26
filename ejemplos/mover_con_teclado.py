# -*- encoding: utf-8 -*-
"""Mover un actor con el teclado usando pilas.control (flechas o WASD)."""

import pilas3d
from pilas3d.actores.cubo import Cubo


class Nave(Cubo):
    def actualizar(self):
        velocidad = 8 * self.pilas.dt
        c = self.pilas.control
        if c.izquierda:
            self.x -= velocidad
        if c.derecha:
            self.x += velocidad
        if c.arriba:
            self.z -= velocidad
        if c.abajo:
            self.z += velocidad
        # La cámara sigue a la nave
        camara = self.pilas.escena_actual().camara
        camara.x = self.x
        camara.objetivo = (self.x, 1, self.z)


pilas = pilas3d.iniciar(titulo="pilas3d - mover con teclado")

nave = Nave(pilas, y=1)
nave.color = pilas.colores.naranja
pilas.actores.Piso()
pilas.actores.Ejes()

pilas.ejecutar()
