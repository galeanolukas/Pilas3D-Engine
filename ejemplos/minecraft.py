# -*- encoding: utf-8 -*-
"""Mini-Minecraft: mundo de bloques, picar y construir.

El mundo es UN solo actor (``Mundo``) que fusiona todos los bloques
en una malla con solo las caras visibles — como hace Minecraft con
sus chunks.

WASD moverse - mouse mirar - SPACE saltar
Click izquierdo: picar   Click derecho: colocar ladrillo   ESC salir
"""

import math

import pilas3d
from pilas3d.actores.esfera import Esfera

pilas = pilas3d.iniciar(titulo="pilas3d - mini minecraft")

mundo = pilas.actores.Mundo()
mundo.generar_terreno(48, 48, altura=5, semilla=3)

# Cielo celeste de día (sin textura, solo color a pleno brillo)
cielo = pilas.actores.Cielo(imagen=None)
cielo.color = pilas.colores.celeste


class Jugador(Esfera):
    """Esfera invisible (la cámara va adentro) con física de Minecraft."""

    def __init__(self, pilas, mundo):
        super(Jugador, self).__init__(
            pilas, radio=0.3, radio_de_colision=0.35)
        self.mundo = mundo
        self._click_izq = False
        self._click_der = False
        suelo = mundo.altura_suelo(0.5, 0.5) or 8
        self.posicion = (0.5, suelo + 0.2, 0.5)
        self.aprender(
            pilas.habilidades.CaminarEnPrimeraPersona,
            velocidad=5, mundo=mundo, gravedad=25, salto=9)

    def actualizar(self):
        c = self.pilas.control
        camara = self.pilas.escena_actual().camara
        if c.boton_izquierdo and not self._click_izq:
            bloque, _ = self.mundo.disparar_bloque(
                camara.posicion, camara.direccion(), alcance=6)
            if bloque:
                self.mundo.sacar_bloque(*bloque)
        if c.boton_derecho and not self._click_der:
            bloque, donde = self.mundo.disparar_bloque(
                camara.posicion, camara.direccion(), alcance=6)
            if donde:
                px, py, pz = math.floor(self.x), math.floor(self.y), \
                    math.floor(self.z)
                if donde not in ((px, py, pz), (px, py + 1, pz)):
                    self.mundo.poner_bloque(*donde, tipo='ladrillo')
        self._click_izq = c.boton_izquierdo
        self._click_der = c.boton_derecho
        if self.y < -20:  # cayó del mundo
            self.posicion = (0.5, (self.mundo.altura_suelo(0.5, 0.5)
                                   or 8) + 1, 0.5)


jugador = Jugador(pilas, mundo)

pilas.actores.Texto(
    "WASD moverse - SPACE saltar - click izq: picar - der: colocar",
    x=10, y=10)

pilas.ejecutar()
