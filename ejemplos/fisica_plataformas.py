# -*- encoding: utf-8 -*-
"""Física 2D en pilas3d (pymunk): un mini-plataformas.

Movés el cubo verde con las flechas y empujás las cajas; la pelota
rebota y suma puntos al tocar el cubo. ESPACIO la lanza hacia arriba.

Correr:  python3 ejemplos/fisica_plataformas.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pilas3d

pilas = pilas3d.iniciar(titulo='física: plataformas')
pilas.fisica.plano = 'xy'                     # vista lateral
pilas.fisica.gravedad = (0, -12)

# escenario estático: suelo + plataformas flotantes
def plataforma(x, y, ancho):
    p = pilas.actores.Cubo(x=x, y=y, z=0)
    p.escala_x = ancho / 2
    p.escala_y = 0.15
    p.escala_z = 0.5
    p.color = pilas.colores.gris
    pilas.fisica.vincular(p, estatico=True, ancho=ancho, alto=0.3)
    return p

plataforma(0, -0.15, 30)                      # suelo
plataforma(-4, 3, 5)
plataforma(4, 6, 5)

# jugador: cinemático — lo mueve el teclado y empuja lo dinámico
jugador = pilas.actores.Cubo(y=1)
jugador.color = pilas.colores.verde
jugador.radio_de_colision = 0.5
pilas.fisica.vincular(jugador, cinematica=True, ancho=1, alto=1)

# cajas dinámicas que caen
for i, x in enumerate((-3, 0, 3)):
    caja = pilas.actores.Cubo(x=x, y=8 + i * 2)
    caja.color = pilas.colores.naranja
    caja.radio_de_colision = 0.5
    pilas.fisica.vincular(caja, ancho=1, alto=1, elasticidad=0.3)

# pelota que rebota
pelota = pilas.actores.Esfera(radio=0.4, x=-6, y=7)
pelota.color = pilas.colores.rojo
pelota.radio_de_colision = 0.4
pilas.fisica.vincular(pelota, forma='circulo', radio=0.4,
                      elasticidad=0.9)

puntaje = pilas.actores.Puntaje(x=10, y=450, prefijo='Toques: ')
pilas.fisica.cuando_colisionan(
    pelota, jugador, lambda a, b: setattr(puntaje, 'valor',
                                         puntaje.valor + 1))

pilas.actores.Texto(
    'flechas: mover el cubo - ESPACIO: lanzar la pelota',
    x=10, y=475, tamano=12)


def cuando_pulsa(t):
    if t == pilas.simbolos.ESPACIO:
        pelota.cuerpo.velocidad = (8, 9)      # la tira en diagonal


def cuando_actualiza():
    v = 6 * pilas.dt
    if pilas.control.izquierda:
        jugador.x -= v
    if pilas.control.derecha:
        jugador.x += v
    if pilas.control.arriba:
        jugador.y += v
    if pilas.control.abajo:
        jugador.y -= v


pilas.escena.cuando_pulsa_tecla = cuando_pulsa
pilas.escena.cuando_actualiza = cuando_actualiza

camara = pilas.camara
camara.posicion = (0, 4, 22)
camara.objetivo = (0, 4, 0)

pilas.ejecutar()
