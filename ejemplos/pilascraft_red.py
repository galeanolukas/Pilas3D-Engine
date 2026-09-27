# -*- encoding: utf-8 -*-
"""PilasCraft en red: mundo voxel infinito compartido.

Uno hospeda (queda escuchando en el puerto 7777)::

    python ejemplos/pilascraft_red.py

Los demás se conectan a su IP::

    python ejemplos/pilascraft_red.py 192.168.0.7

Cada jugador ve a los demás como cubos de colores que se mueven
suave, y los bloques picados/colocados se sincronizan. El terreno
y los árboles coinciden solos porque son deterministas por semilla.

Limitación de este nivel educativo: no hay servidor autoritativo —
las ediciones hechas ANTES de que alguien se conecte no se mandan
(a excepción de las deterministas, como los árboles).
"""

import math
import os
import random
import sys

import pilas3d
from pilas3d.actores.esfera import Esfera
from pilas3d.actores.cubo import Cubo

pilas = pilas3d.iniciar(titulo="pilas3d - PilasCraft en red")

# -- red: sin argumentos hospeda, con una IP se conecta -----------
if len(sys.argv) > 1:
    red = pilas.red.conectar(sys.argv[1], puerto=7777)
    soy_host = False
else:
    red = pilas.red.hospedar(puerto=7777)
    soy_host = True
    print("Escuchando en el puerto %d — otros entran con:" % red.puerto)
    print("  python ejemplos/pilascraft_red.py <tu-ip>")

# -- mundo (idéntico al de pilascraft.py) --------------------------
MC = os.path.join(os.path.dirname(__file__), '..',
                  'Texturas Minecraf', 'assets', 'minecraft')
TEX = os.path.join(MC, 'textures', 'blocks')
SND = os.path.join(MC, 'sounds')
usa_pack = os.path.isdir(TEX)

DISTANCIA_VISTA = 3

if usa_pack:
    atlas = [os.path.join(TEX, t) for t in (
        'grass_top.png', 'grass_side.png', 'dirt.png', 'stone.png',
        'brick.png', 'sand.png', 'log_big_oak.png',
        'log_big_oak_top.png', 'leaves_oak.png')]
    tipos = {
        'cesped': (0, 1, 2), 'tierra': (2, 2, 2), 'piedra': (3, 3, 3),
        'ladrillo': (4, 4, 4), 'arena': (5, 5, 5),
        'tronco': (7, 6, 7), 'hojas': (8, 8, 8),
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

# los árboles son deterministas (misma semilla, mismo rng):
# todos los jugadores los generan igual sin sincronizarlos
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

cielo = pilas.actores.Cielo(imagen=None)
cielo.color = pilas.colores.celeste
pilas.escena.fondo = pilas.colores.celeste
pilas.escena.niebla = (pilas.colores.celeste,
                     DISTANCIA_VISTA * 16 * 0.6,
                     DISTANCIA_VISTA * 16 * 0.95)

# -- jugadores remotos: un cubo fantasma por id --------------------
COLORES = [(0.9, 0.3, 0.3), (0.3, 0.9, 0.4), (0.9, 0.8, 0.2),
           (0.7, 0.3, 0.9), (0.3, 0.7, 0.9)]
fantasmas = {}


class Fantasma(Cubo):
    """Copia remota de un jugador: interpola hacia la última
    posición que mandó por red."""

    def __init__(self, pilas, cid):
        color = COLORES[cid % len(COLORES)]
        super(Fantasma, self).__init__(pilas, y=mundo.altura_terreno_en(0, 0))
        self.cid = cid
        self.color = color
        self._objetivo = None

    def ir_a(self, pos):
        self._objetivo = pos

    def actualizar(self):
        if self._objetivo is None:
            return
        ox, oy, oz = self._objetivo
        self.x += (ox - self.x) * 0.25
        self.y += (oy - self.y) * 0.25
        self.z += (oz - self.z) * 0.25


def crear_fantasma(cid):
    if cid not in fantasmas:
        fantasmas[cid] = Fantasma(pilas, cid)


def on_hola(datos, de):
    for cid in datos.get('jugadores', []):
        crear_fantasma(cid)


def on_entro(datos, de):
    crear_fantasma(datos['id'])


def on_salio(datos, de):
    cid = datos['id']
    if cid in fantasmas:
        fantasmas.pop(cid).eliminar()


def on_posicion(datos, de):
    if de in fantasmas:
        fantasmas[de].ir_a(datos['pos'])


def on_bloque(datos, de):
    i, j, k = (int(v) for v in datos['pos'])
    if datos.get('tipo'):
        mundo.poner_bloque(i, j, k, datos['tipo'])
    else:
        mundo.sacar_bloque(i, j, k)


red.cuando_reciba('hola', on_hola)
red.cuando_reciba('entro', on_entro)
red.cuando_reciba('salio', on_salio)
red.cuando_reciba('posicion', on_posicion)
red.cuando_reciba('bloque', on_bloque)


class Jugador(Esfera):
    """Esfera invisible con física de Minecraft + sincronización."""

    def __init__(self, pilas, mundo, red):
        super(Jugador, self).__init__(
            pilas, radio=0.3, radio_de_colision=0.35)
        self.mundo = mundo
        self.red = red
        self._click_izq = False
        self._click_der = False
        self._t_envio = 0.0
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
                self.red.enviar('bloque', pos=list(bloque), tipo=None)
                self.pilas.actores.Particulas.explosion(
                    self.pilas, x=bloque[0] + 0.5, y=bloque[1] + 0.5,
                    z=bloque[2] + 0.5, cantidad=25, velocidad=3,
                    tamano=4, color=(0.45, 0.33, 0.2),
                    color_final=(0.3, 0.3, 0.3))
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
                    self.red.enviar('bloque', pos=list(donde),
                                    tipo='ladrillo')
                    if son_poner:
                        son_poner.reproducir()
        self._click_izq = c.boton_izquierdo
        self._click_der = c.boton_derecho

        # mandar posición ~10 veces por segundo
        self._t_envio += self.pilas.dt
        if self._t_envio >= 0.1:
            self._t_envio = 0.0
            self.red.enviar('posicion', pos=[self.x, self.y, self.z])

        if self.y < -20:
            self.posicion = (0.5,
                             self.mundo.altura_terreno_en(0, 0) + 1,
                             0.5)


jugador = Jugador(pilas, mundo, red)

rol = "host" if soy_host else "cliente"
pilas.actores.Texto(
    "PilasCraft en red (%s) - WASD - SPACE - click: picar/colocar" % rol,
    x=10, y=10)

pilas.ejecutar()
