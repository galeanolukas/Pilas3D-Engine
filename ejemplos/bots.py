# -*- encoding: utf-8 -*-
"""Bots: NPCs con comportamiento sobre un terreno voxel.

``pilas.actores.Bot`` crea un personaje que ya aprendió la habilidad
``SerBot`` — patrulla cerca de su casa, corre hacia ``objetivo`` si
entra en ``radio_vision`` y vuelve después. La misma habilidad se le
puede enseñar a cualquier actor::

    bicho.aprender(pilas.habilidades.SerBot, mundo=mundo,
                   objetivo=jugador, radio_vision=8)

WASD moverse - mouse mirar - SPACE saltar - ESC salir
Acercate a la araña: su estado cambia a 'perseguir'.
"""

import pilas3d
from pilas3d.actores.esfera import Esfera

pilas = pilas3d.iniciar(titulo="pilas3d - bots")

# mundo chico de bloques para que los bots caminen sobre el terreno
mundo = pilas.actores.Mundo()
mundo.generar_terreno(40, 40, altura=3, semilla=5)

cielo = pilas.actores.Cielo(imagen=None)
cielo.color = pilas.colores.celeste
pilas.escena.fondo = pilas.colores.celeste


class Jugador(Esfera):
    def __init__(self, pilas, mundo):
        super(Jugador, self).__init__(pilas, radio=0.3,
                                      radio_de_colision=0.35)
        suelo = mundo.altura_suelo(0, 0) or 4
        self.posicion = (0.5, suelo + 0.2, 0.5)
        self.aprender(pilas.habilidades.CaminarEnPrimeraPersona,
                      velocidad=5, mundo=mundo, gravedad=25, salto=9)


jugador = Jugador(pilas, mundo)

# dos bots de patrulla (distinto cuerpo, mismo comportamiento)
pilas.actores.Bot(personaje='Mono', x=-6, z=-6, mundo=mundo,
                  radio_patron=10, velocidad=2.5)
pilas.actores.Bot(personaje='Robot', x=8, z=6, mundo=mundo,
                  radio_patron=8, velocidad=2.0)

# y la araña: te persigue si te acercás
arana = pilas.actores.Bot(personaje='Arania', x=10, z=-10,
                          mundo=mundo, radio_vision=7,
                          radio_patron=12, velocidad=3,
                          objetivo=jugador)

# un espectro sin objetivo: solo deambula
pilas.actores.Bot(personaje='Espectro', x=-10, z=8,
                  mundo=mundo, radio_patron=6, velocidad=1.5)

aviso = pilas.actores.Texto("", x=10, y=40)
pilas.actores.Texto(
    "WASD - SPACE - acercate a la arania y escapá", x=10, y=10)


def refrescar_aviso():
    if arana.estado == 'perseguir':
        aviso.texto = "LA ARAÑA TE VIO"
    elif arana.estado == 'volver':
        aviso.texto = "la araña vuelve a su casa..."
    else:
        aviso.texto = ""


pilas.tareas.siempre(0.25, refrescar_aviso)

pilas.ejecutar()
