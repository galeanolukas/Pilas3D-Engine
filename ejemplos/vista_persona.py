# -*- encoding: utf-8 -*-
"""Ejemplo: camara.seguir_a — primera, segunda y tercera persona.

El robot camina con WASD; la tecla V cicla las vistas como en los
juegos: libre -> primera -> tercera (detras) -> segunda (frontal).

WASD: caminar - V: cambiar vista - ESC salir
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - vistas de camara")

pilas.actores.Cielo('dia')
pilas.escena.fondo = pilas.colores.celeste
piso = pilas.actores.Piso(tamano=30, divisiones=30)
piso.color = pilas.colores.verde
pilas.actores.Ejes()

# unos cubos para tener referencia visual al caminar
for x, z in ((-5, -8), (6, -3), (-3, 7), (8, 8)):
    pilas.actores.Cubo(x=x, z=z, y=0.5)

robot = pilas.actores.Robot(x=0, z=4)
robot.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)

camara = pilas.escena.camara
MODOS = ['libre', 'primera', 'tercera', 'segunda']
modo = ['tercera']

cartel = pilas.actores.Texto("", x=10, y=430, tamano=16)
cartel.color = pilas.colores.amarillo
pilas.actores.Texto("WASD: caminar - V: cambiar vista", x=10, y=10)


def fijar_modo():
    cartel.texto = "vista: " + modo[0]
    if modo[0] == 'libre':
        camara.dejar_de_seguir()
        camara.posicion = (0, 6, 14)
        camara.objetivo = (0, 1, 0)
    else:
        camara.seguir_a(robot, modo=modo[0], distancia=5,
                        altura=2.5, ojos=1.4)


def al_pulsar(tecla):
    if tecla == pilas.simbolos.v:
        modo[0] = MODOS[(MODOS.index(modo[0]) + 1) % len(MODOS)]
        fijar_modo()

pilas.escena.cuando_pulsa_tecla = al_pulsar
fijar_modo()

pilas.ejecutar()
