# -*- encoding: utf-8 -*-
"""Mundo infinito con lobos: modelo glTF esquelético + SerBot + voxel.

Los lobos son ``ModeloGLTF`` que aprenden ``SerBot``: deambulan por el
terreno procedural (que nunca termina), te siguen si te acercás y
vuelven a su zona si te alejás — con la animación correcta en cada
estado (idle / caminar / correr).

WASD moverse - mouse mirar - SPACE saltar - click: picar/colocar
L: soltar otro lobo - C: cielo - ESC salir
"""

import math
import os
import random

import pilas3d
from pilas3d.actores.esfera import Esfera
from pilas3d.actores.modelo_gltf import ModeloGLTF

pilas = pilas3d.iniciar(titulo="pilas3d - mundo infinito con lobos")

LOBO = 'modelos/personajes/wolf/Wolf-Blender-2.82a.glb'
DISTANCIA_VISTA = 3

# mundo voxel infinito (usa el pack de Minecraft si está)
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
        'cesped': (0, 1, 2), 'tierra': (2, 2, 2), 'piedra': (3, 3, 3),
        'ladrillo': (4, 4, 4), 'arena': (5, 5, 5),
        'tronco': (7, 6, 7), 'hojas': (8, 8, 8)}
    mundo = pilas.actores.Mundo(tipos=tipos, atlas=atlas, infinito=True,
                                semilla=11, altura=5,
                                distancia_vista=DISTANCIA_VISTA)
    son_picar = [pilas.sonidos.cargar(
        os.path.join(SND, 'dig', 'wood%d.ogg' % i)) for i in (1, 2, 3, 4)]
    son_poner = pilas.sonidos.cargar(os.path.join(SND, 'random', 'pop.ogg'))
else:
    mundo = pilas.actores.Mundo(infinito=True, semilla=11, altura=5,
                              distancia_vista=DISTANCIA_VISTA)
    son_picar = son_poner = None

pilas.actores.Cielo('dia')
pilas.escena.fondo = pilas.colores.celeste
pilas.escena.niebla = (pilas.colores.celeste,
                     DISTANCIA_VISTA * 16 * 0.6,
                     DISTANCIA_VISTA * 16 * 0.95)
pilas.luces.direccional.ambiente = 0.5


class Jugador(Esfera):
    """Cámara en primera persona con física de Minecraft."""

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
        if self.y < -20:
            self.posicion = (0.5,
                             self.mundo.altura_terreno_en(0, 0) + 1,
                             0.5)


class Lobo(ModeloGLTF):
    """Lobo glTF con comportamiento: deambula, te persigue, vuelve.

    La animación sigue al estado de ``SerBot``: '04_Idle' quieto,
    '02_walk' patrullando, '01_Run' cuando te persigue.
    """

    ANIM = {'patrullar': '02_walk_Armature_0',
            'perseguir': '01_Run_Armature_0',
            'volver': '02_walk_Armature_0',
            'quieto': '04_Idle_Armature_0'}

    def __init__(self, pilas, jugador, mundo, x=0, z=0):
        super(Lobo, self).__init__(pilas, LOBO, escala=1.2, x=x, z=z)
        self._moviendo = False
        self._px, self._pz = x, z
        self.animar(self.ANIM['quieto'])
        self.aprender(pilas.habilidades.SerBot, mundo=mundo,
                      objetivo=jugador, radio_vision=5,
                      radio_patron=14, velocidad=1.6,
                      espera_min=1.0, espera_max=3.0)

    def actualizar(self):
        self._moviendo = math.hypot(self.x - self._px,
                                    self.z - self._pz) > 0.001
        self._px, self._pz = self.x, self.z
        estado = self.estado if self._moviendo else 'quieto'
        clip = self.ANIM[estado]
        if clip != self.animacion:
            self.animar(clip)
        super(Lobo, self).actualizar()   # skinning + serbot via habilidades


jugador = Jugador(pilas, mundo)
lobos = []


def soltar_lobo():
    """Suelta un lobo cerca del jugador, sobre el terreno."""
    x = jugador.x + random.choice((-1, 1)) * random.uniform(6, 9)
    z = jugador.z + random.choice((-1, 1)) * random.uniform(6, 9)
    lobos.append(Lobo(pilas, jugador, mundo, x=x, z=z))


soltar_lobo()
soltar_lobo()


def al_pulsar_tecla(simbolo):
    if simbolo == pilas.simbolos.l:
        soltar_lobo()

pilas.escena.cuando_pulsa_tecla = al_pulsar_tecla

pilas.actores.Texto(
    "WASD moverse - click: picar/colocar - L: lobo - ESC salir",
    x=10, y=10)

pilas.ejecutar()
