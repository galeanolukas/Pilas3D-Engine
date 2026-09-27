# -*- encoding: utf-8 -*-
"""Mini-Minecraft: mundo de bloques, picar y construir.

El mundo es UN solo actor (``Mundo``) que fusiona todos los bloques
en una malla con solo las caras visibles — como hace Minecraft con
sus chunks.

Si existe el directorio "Texturas Minecraf" usa las texturas y
sonidos reales del juego; si no, un atlas procedural generado solo.

WASD moverse - mouse mirar - SPACE saltar
Click izquierdo: picar   Click derecho: colocar ladrillo   ESC salir
"""

import math
import os
import random

import pilas3d
from pilas3d.actores.esfera import Esfera

pilas = pilas3d.iniciar(titulo="pilas3d - mini minecraft")

# -- texturas y sonidos reales (si está el pack de Minecraft) ----
MC = os.path.join(os.path.dirname(__file__), '..',
                  'Texturas Minecraf', 'assets', 'minecraft')
TEX = os.path.join(MC, 'textures', 'blocks')
SND = os.path.join(MC, 'sounds')
usa_pack = os.path.isdir(TEX)

if usa_pack:
    atlas = [os.path.join(TEX, t) for t in (
        'grass_top.png', 'grass_side.png', 'dirt.png', 'stone.png',
        'brick.png', 'sand.png', 'log_big_oak.png',
        'log_big_oak_top.png', 'leaves_oak.png')]
    tipos = {
        'cesped': (0, 1, 2),   # (arriba, costados, abajo)
        'tierra': (2, 2, 2),
        'piedra': (3, 3, 3),
        'ladrillo': (4, 4, 4),
        'arena': (5, 5, 5),
        'tronco': (7, 6, 7),   # arriba: anillos, costados: corteza
        'hojas': (8, 8, 8),
    }
    mundo = pilas.actores.Mundo(tipos=tipos, atlas=atlas)
    son_picar = [pilas.sonidos.cargar(
        os.path.join(SND, 'dig', 'wood%d.ogg' % i)) for i in (1, 2, 3, 4)]
    son_poner = pilas.sonidos.cargar(os.path.join(SND, 'random', 'pop.ogg'))
else:
    mundo = pilas.actores.Mundo()
    son_picar = son_poner = None

mundo.generar_terreno(48, 48, altura=5, semilla=3)

# unos árboles: tronco vertical + cubo de hojas
rng = random.Random(1)
for _ in range(10):
    tx, tz = rng.randint(-20, 20), rng.randint(-20, 20)
    suelo = mundo.altura_suelo(tx, tz)
    if suelo is None:
        continue
    for j in range(3):
        mundo.poner_bloque(tx, suelo + j, tz, 'tronco')
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in (2, 3):
                mundo.poner_bloque(tx + dx, suelo + dy, tz + dz, 'hojas')

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
                if son_picar:
                    random.choice(son_picar).reproducir()
        if c.boton_derecho and not self._click_der:
            bloque, donde = self.mundo.disparar_bloque(
                camara.posicion, camara.direccion(), alcance=6)
            if donde:
                px, py, pz = math.floor(self.x), math.floor(self.y), \
                    math.floor(self.z)
                if donde not in ((px, py, pz), (px, py + 1, pz)):
                    self.mundo.poner_bloque(*donde, tipo='ladrillo')
                    if son_poner:
                        son_poner.reproducir()
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
