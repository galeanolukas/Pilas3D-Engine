# -*- encoding: utf-8 -*-
"""Mini-FPS estilo Doom con mapa ASCII, pathfinding y atmósfera.

- El laberinto se define como texto: '#' pared, 'E' enemigo, 'J' jugador
- WASD/flechas: caminar (las paredes bloquean)
- Mouse: mirar alrededor
- Click izquierdo: disparar (rayo desde la cámara)
- Los enemigos te BUSCAN: persiguen con A* esquivando las paredes
- Niebla + linterna para ambientación de pasillos oscuros
- Si un enemigo te toca: volvés al inicio y perdés una vida
"""

import random

import pilas3d
from pilas3d.actores.esfera import Esfera
from pilas3d.actores.animacion import Animacion
from pilas3d.luces import LuzPuntual

# 13 filas x 14 columnas; cada celda mide 2 unidades.
MAPA = """
##############
#............#
#.E..........#
#....####....#
#....#...E...#
#....#.......#
#.E..#....E..#
#............#
#....####....#
#........E...#
#.....J......#
##############
"""

pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - mini doom")

TEX_PARED = pilas3d.obtener_ruta('data/caja.png')
TEX_PISO = pilas3d.obtener_ruta('data/pasto.png')
SPR_FANTASMA = pilas3d.obtener_ruta('data/fantasma.png')   # 8 cuadros
SPR_EXPLOSION = pilas3d.obtener_ruta('data/explosion.png')  # 7 cuadros

# Sonidos (se buscan en pilas3d/data/); si no hay placa de audio se
# cargan deshabilitados y las llamadas no hacen nada.
sonido_disparo = pilas.sonidos.cargar('tick.wav')
sonido_explosion = pilas.sonidos.cargar('explosion.wav')
sonido_herido = pilas.sonidos.cargar('grito.wav')
sonido_victoria = pilas.sonidos.cargar('smile.wav')

puntaje = pilas.actores.Puntaje(x=10, y=60, prefijo="Puntos: ")
vidas = pilas.actores.Puntaje(x=200, y=60, prefijo="Vidas: ")
vidas.valor = 3
vidas.texto = "Vidas: 3"
pilas.actores.Texto("WASD moverse - mouse mirar - click disparar",
                    x=10, y=30)
mira = pilas.actores.Texto("+", x=395, y=288, tamano=24)
mira.color = pilas.colores.rojo               # crosshair

NEGRO = pilas.colores.negro


class Enemigo(Animacion):
    """Fantasma animado (billboard) que persigue al jugador con A*."""

    def __init__(self, pilas, jugador=None, **kw):
        super(Enemigo, self).__init__(pilas, SPR_FANTASMA, columnas=8,
                                      velocidad=10, ancho=1.4, alto=1.4,
                                      **kw)
        self.radio_de_colision = 0.45  # toque: hay que acercarse
        self.radio_de_disparo = 0.75   # disparo: cubre todo el sprite
        self.jugador = jugador

    def actualizar(self):
        super(Enemigo, self).actualizar()  # avanza los cuadros
        j = self.jugador
        if j is None:
            return

        # Si toca al jugador: una vida menos y vuelta al inicio.
        # (en el plano XZ: el jugador y el enemigo tienen distinta y)
        if self.colisiona_en_plano_con(j):
            sonido_herido.reproducir()
            j.posicion = jugador_inicio
            vidas.valor -= 1
            vidas.texto = "Vidas: %d" % vidas.valor

            # flash rojo de daño (niebla se pone roja un instante)
            pilas.escena.niebla = (pilas.colores.rojo, 2, 14)
            pilas.tareas.una_vez(0.25, restaurar_niebla)

            if vidas.valor <= 0:
                pilas.actores.Texto("PERDISTE!", x=320, y=200,
                                    tamano=40)
                self.pilas.tareas.una_vez(2, pilas.terminar)


def restaurar_niebla():
    pilas.escena.niebla = (NEGRO, 4, 20)


def al_impactar(proyectil, enemigo):
    """El proyectil pegó: explosión animada + partículas."""
    pilas.actores.Animacion(
        SPR_EXPLOSION, columnas=7, velocidad=14,
        ciclica=False, eliminar_al_terminar=True,
        ancho=1.8, alto=1.8,
        x=enemigo.x, y=enemigo.y, z=enemigo.z)
    pilas.actores.Particulas.explosion(
        pilas, x=enemigo.x, y=enemigo.y, z=enemigo.z,
        color=pilas.colores.naranja)
    enemigo.eliminar()
    enemigos.remove(enemigo)
    sonido_explosion.reproducir()
    puntaje.aumentar()
    if not enemigos:
        sonido_victoria.reproducir()
        pilas.actores.Texto("GANASTE!", x=340, y=200, tamano=40)


def al_disparar():
    sonido_disparo.reproducir()


class Jugador(Esfera):
    """El cuerpo del jugador (se ve al mirar hacia abajo)."""

    def __init__(self, pilas, enemigos, **kw):
        super(Jugador, self).__init__(pilas, radio=0.4,
                                      radio_de_colision=0.35, **kw)
        self.color = pilas.colores.celeste
        self.enemigos = enemigos
        self.aprender(pilas.habilidades.CaminarEnPrimeraPersona,
                      velocidad=6, altura=1.6)
        # dispara proyectiles reales que salen de la cámara con click
        self.aprender(pilas.habilidades.Disparar,
                      desde_camara=True, con_click=True,
                      cadencia=0.3, velocidad=30, alcance=40,
                      objetivos=enemigos, cuando_impacta=al_impactar,
                      cuando_dispara=al_disparar)

    def actualizar(self):
        # la linterna sigue a la cámara
        cam = self.pilas.escena_actual().camara
        linterna.x, linterna.y, linterna.z = cam.posicion


# -- construcción del mapa desde texto ---------------------------------------

enemigos = []
spawn = {}
jugador_inicio = (0, 0.4, 0)


def hacer_pared(p, x, z):
    pared = p.actores.Pared(x=x, z=z, ancho=2, alto=3, profundidad=2)
    pared.imagen = TEX_PARED
    return pared


def hacer_enemigo(p, x, z):
    enemigo = Enemigo(p, x=x, y=0.9, z=z)
    enemigos.append(enemigo)
    return enemigo


def marcar_jugador(p, x, z):
    spawn['pos'] = (x, 0.4, z)


mapa = pilas.actores.Mapa(MAPA, {
    '#': hacer_pared,
    'E': hacer_enemigo,
    'J': marcar_jugador,
})

piso = pilas.actores.Plano(ancho=30, profundidad=30)
piso.imagen = TEX_PISO

# Cielo estrellado + ambiente nocturno + niebla de pasillos
pilas.actores.Cielo()
pilas.luces.direccional.ambiente = 0.12
pilas.luces.direccional.color = pilas.colores.gris
pilas.escena.niebla = (NEGRO, 4, 20)

# linterna: luz puntual cálida que sigue a la cámara
linterna = pilas.luces.agregar(LuzPuntual(
    x=0, y=2, z=0, alcance=12, color=(1, 0.9, 0.7)))

jugador = Jugador(pilas, enemigos)
jugador_inicio = spawn['pos']
jugador.posicion = jugador_inicio

# cada enemigo aprende a perseguir al jugador esquivando paredes (A*),
# con velocidades levemente distintas para que no marchén en fila
for enemigo in enemigos:
    enemigo.jugador = jugador
    enemigo.aprender(pilas.habilidades.PerseguirAOtroActor,
                     actor=jugador,
                     velocidad=random.uniform(1.8, 2.6),
                     tam_celda=0.8, cada=0.5)

pilas.ejecutar()
