# -*- encoding: utf-8 -*-
"""Controles de mouse: click, arrastrar y seguir el puntero.

- Click izquierdo sobre un cubo: cambia su color (evento
  ``pilas.cuando_hace_click``).
- Arrastrá la esfera violeta con el botón apretado (habilidad
  ``Arrastrable``).
- El robot camina hacia donde apunta el mouse (habilidad
  ``SeguirAlMouse``).
- Botón derecho + drag / rueda: cámara orbital.
"""

import random

import pilas3d
from pyglet.window import mouse

pilas = pilas3d.iniciar(titulo="Mouse en 3D")

pilas.actores.Piso(tamano=40)
pilas.mostrar_ejes(3)

# orbital con el derecho para no chocar con Arrastrable (izquierdo)
pilas.escena.camara.usar_control_orbital(boton=mouse.RIGHT)

# cubos clickeables
COLORES = [pilas.colores.rojo, pilas.colores.naranja,
           pilas.colores.verde, pilas.colores.celeste,
           pilas.colores.violeta, pilas.colores.rosa]
cubos = []
for i in range(6):
    cubo = pilas.actores.Cubo(x=-7.5 + i * 3, y=0.5, z=-3)
    cubo.color = COLORES[i % len(COLORES)]
    cubos.append(cubo)

# esfera arrastrable
pelota = pilas.actores.Esfera(x=-3, z=4)
pelota.color = pilas.colores.violeta
pelota.aprender(pilas.habilidades.Arrastrable, y_plano=1.0)

# personaje que sigue al puntero
guia = pilas.actores.Robot()
guia.aprender(pilas.habilidades.SeguirAlMouse, velocidad=4)

pilas.actores.Texto(
    "click en un cubo: color | drag sobre la esfera | "
    "el robot sigue al mouse", y=-26)


def al_clickear(actor, punto):
    if actor in cubos:
        actor.color = random.choice(COLORES)
    elif actor is not None:
        # explotar cualquier otro actor clickeado
        actor.color = pilas.colores.amarillo


pilas.cuando_hace_click(al_clickear)

pilas.ejecutar()
