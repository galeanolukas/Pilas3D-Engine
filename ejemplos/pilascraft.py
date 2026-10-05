# -*- encoding: utf-8 -*-
"""PilasCraft: mundo voxel infinito, picar y construir.

El mundo es UN solo actor (``Mundo``) con ``infinito=True``: los
chunks se generan proceduralmente alrededor de la cámara (determinista
por ``semilla``) y sus mallas se descargan al alejarse. La niebla de
la escena disimula el borde del mundo visible — el truco clásico.

Si existe el directorio "Texturas Minecraf" usa las texturas y
sonidos reales del juego; si no, un atlas procedural generado solo.

WASD moverse - mouse mirar - SPACE saltar
Click izquierdo: picar   Click derecho: colocar ladrillo
C: cambiar el cielo (dia/estrellas/celeste)   ESC salir
"""

import math
import os
import random

import pilas3d
from pilas3d.actores.esfera import Esfera

pilas = pilas3d.iniciar(titulo="pilas3d - PilasCraft")

# -- texturas y sonidos reales (si está el pack de Minecraft) ----
MC = os.path.join(os.path.dirname(__file__), '..',
                  'Texturas Minecraf', 'assets', 'minecraft')
TEX = os.path.join(MC, 'textures', 'blocks')
SND = os.path.join(MC, 'sounds')
usa_pack = os.path.isdir(TEX)

DISTANCIA_VISTA = 3  # chunks de radio: ~48 bloques visibles

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
    mundo = pilas.actores.Mundo(
        tipos=tipos, atlas=atlas, infinito=True, semilla=7,
        altura=5, distancia_vista=DISTANCIA_VISTA)
    son_picar = [pilas.sonidos.cargar(
        os.path.join(SND, 'dig', 'wood%d.ogg' % i)) for i in (1, 2, 3, 4)]
    son_poner = pilas.sonidos.cargar(os.path.join(SND, 'random', 'pop.ogg'))
else:
    mundo = pilas.actores.Mundo(
        infinito=True, semilla=7, altura=5,
        distancia_vista=DISTANCIA_VISTA)
    son_picar = son_poner = None

# unos árboles cerca del spawn: la altura la da la misma función
# procedural del mundo (los chunks aún no existen al crear el script)
rng = random.Random(1)
for _ in range(8):
    tx, tz = rng.randint(-18, 18), rng.randint(-18, 18)
    suelo = mundo.altura_terreno_en(tx, tz)
    for j in range(3):
        mundo.poner_bloque(tx, suelo + j, tz, 'tronco')
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in (2, 3):
                mundo.poner_bloque(tx + dx, suelo + dy, tz + dz, 'hojas')

# Cielo diurno con nubes + niebla del mismo tono: el borde de los
# chunks se funde con el horizonte y el mundo "no termina".
# Tecla C cicla el cielo: dia -> estrellas -> celeste liso.
cielo = pilas.actores.Cielo('dia')

CIELOS = [('dia', pilas.colores.celeste),
          ('estrellas', (0.05, 0.05, 0.12)),
          (None, pilas.colores.celeste)]
cielo_idx = [0]


def al_pulsar_tecla(simbolo):
    if simbolo == pilas.simbolos.c:
        cielo_idx[0] = (cielo_idx[0] + 1) % len(CIELOS)
        tipo, fondo = CIELOS[cielo_idx[0]]
        cielo.tipo = tipo
        pilas.escena.fondo = fondo
        pilas.escena.niebla = (fondo,
                               DISTANCIA_VISTA * 16 * 0.6,
                               DISTANCIA_VISTA * 16 * 0.95)


pilas.escena.cuando_pulsa_tecla = al_pulsar_tecla
pilas.escena.fondo = pilas.colores.celeste
pilas.escena.niebla = (pilas.colores.celeste,
                     DISTANCIA_VISTA * 16 * 0.6,
                     DISTANCIA_VISTA * 16 * 0.95)


class Jugador(Esfera):
    """Esfera invisible (la cámara va adentro) con física de Minecraft."""

    def __init__(self, pilas, mundo):
        super(Jugador, self).__init__(
            pilas, radio=0.3, radio_de_colision=0.35)
        self.mundo = mundo
        self._click_izq = False
        self._click_der = False
        suelo = mundo.altura_terreno_en(0, 0)
        self.posicion = (0.5, suelo + 0.7, 0.5)
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
                # escombros del bloque roto
                self.pilas.actores.Particulas.explosion(
                    self.pilas, x=bloque[0] + 0.5, y=bloque[1] + 0.5,
                    z=bloque[2] + 0.5, cantidad=25, velocidad=3,
                    tamano=4, color=(115, 84, 51),
                    color_final=(77, 77, 77))
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
            self.posicion = (0.5,
                             self.mundo.altura_terreno_en(0, 0) + 1,
                             0.5)


jugador = Jugador(pilas, mundo)

pilas.actores.Texto(
    "WASD moverse - SPACE saltar - click: picar/colocar - C: cielo",
    x=10, y=10)

pilas.ejecutar()
