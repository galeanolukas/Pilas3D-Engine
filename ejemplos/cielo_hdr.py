# -*- encoding: utf-8 -*-
"""Cielo HDR: un fondo equirectangular .hdr con luz que sale del mapa.

El .hdr (Radiance, los que distribuye Poly Haven) se sube como
textura float y el shader lo comprime a pantalla. Además,
``iluminar_escena`` saca la dirección del sol y el color del
ambiente del propio mapa — el fondo y la escena quedan integrados.

Caminá con las flechas. Con M/N subís y bajás la exposición.
Con el botón izquierdo del mouse orbitás la cámara alrededor del
robot para recorrer el hall — el domo sigue la cámara solo.
"""

import pilas3d

pilas = pilas3d.iniciar()

# Fondo HDR (data/hdr/, CC0 de Poly Haven).
cielo = pilas.actores.Cielo('kloofendal_48d_partly_cloudy_puresky_2k.hdr')
# cielo = pilas.actores.Cielo('mirrored_hall_2k.hdr')   # interior
cielo.iluminar_escena()              # sol + ambiente salen del mapa

camara = pilas.escena_actual().camara
camara.posicion = (0, 4, 10)
camara.usar_control_orbital()        # drag orbita, rueda zoom

pilas.actores.Piso()
robot = pilas.actores.Robot()
robot.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=5)

# Una esfera amarilla para apreciar de dónde cae la luz extraída.
pilas.actores.Esfera(x=4, y=1, z=-3, radio=0.8).color = \
    pilas.colores.amarillo


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s.m:
        cielo.exposicion = min(4.0, cielo.exposicion + 0.15)
    elif tecla == s.n:
        cielo.exposicion = max(0.1, cielo.exposicion - 0.15)


pilas.escena.cuando_pulsa_tecla = al_pulsar
pilas.ejecutar()
