# -*- encoding: utf-8 -*-
"""Escenas propias y cambio de escena (estilo pilas-engine).

Un menú y un juego como dos clases de escena: cada una tiene sus
propios actores, tareas y luces; al cambiar, la anterior se descarta.

ENTER: jugar - M: volver al menú - ESC: salir
"""

import pilas3d
from pilas3d.escenas import Escena
from pyglet.window import key

pilas = pilas3d.iniciar(titulo="pilas3d - escenas")


class Menu(Escena):
    """Escena de menú: solo texto de overlay."""

    def iniciar(self):
        self.fondo = pilas.colores.gris_oscuro
        pilas.actores.Texto("=== PILAS3D ===", x=220, y=300, tamano=32)
        pilas.actores.Texto("ENTER: jugar    ESC: salir",
                            x=230, y=250, tamano=16)

    def cuando_pulsa_tecla(self, simbolo):
        if simbolo == key.ENTER:
            pilas.escenas.Juego()


class Juego(Escena):
    """Escena de juego: un cubo que se mueve y gira."""

    def iniciar(self):
        pilas.actores.Piso()
        self.cubo = pilas.actores.Cubo()
        self.cubo.color = pilas.colores.verde
        self.cubo.aprender(pilas.habilidades.MoverseConElTeclado,
                           velocidad=8)
        self.cubo.aprender(pilas.habilidades.GirarConstantemente,
                           velocidad=90)
        pilas.actores.Texto("M: menu    ESC: salir", x=10, y=450)
        self.camara.posicion = (0, 6, 12)
        self.camara.objetivo = (0, 0, 0)

    def cuando_pulsa_tecla(self, simbolo):
        if simbolo == key.M:
            pilas.escenas.Menu()


pilas.escenas.vincular(Menu)
pilas.escenas.vincular(Juego)
pilas.escenas.Menu()

pilas.ejecutar()
