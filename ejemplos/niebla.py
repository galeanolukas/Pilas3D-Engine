# -*- encoding: utf-8 -*-
"""Niebla: ``escena.niebla = (color, inicio, fin)``.

Niebla lineal por distancia a la cámara aplicada solo a fragmentos
iluminados (el cielo y el texto quedan limpios). Combinando
``escena.fondo`` con el color de la niebla el horizonte se funde —
el mismo truco que usa PilasCraft para disimular el borde del mundo.

Tecla N: cicla entre apagada / niebla abierta / niebla cerrada
(noche de terror, con una luz puntual como linterna).
WASD moverse - mouse mirar - ESC salir.
"""

import pilas3d
from pilas3d.actores.esfera import Esfera
from pilas3d.luces import LuzPuntual

pilas = pilas3d.iniciar(titulo="pilas3d - niebla")

# noche: piso oscuro, paredes sueltas y una luz puntual tipo linterna
pilas.actores.Piso(tamano=60, divisiones=30)
pilas.escena.fondo = pilas.colores.negro
cielo = pilas.actores.Cielo(imagen=None)
cielo.color = pilas.colores.negro

import random
rng = random.Random(2)
for _ in range(25):
    x, z = rng.randint(-25, 25), rng.randint(-25, 25)
    pared = pilas.actores.Pared(x=x, z=z,
                              ancho=rng.uniform(2, 5),
                              alto=rng.uniform(1.5, 4))
    pared.rotacion_y = rng.uniform(0, 90)

linterna = pilas.luces.agregar(LuzPuntual(
    x=0, y=2, z=0, alcance=14, color=(1, 0.85, 0.6)))
pilas.luces.direccional.ambiente = 0.15

MODOS = [
    ("niebla apagada", None),
    ("niebla abierta (30-70)", ((0.4, 0.4, 0.45), 30, 70)),
    ("niebla cerrada (3-18)", ((0.1, 0.1, 0.12), 3, 18)),
]
modo = [2]  # arranca en modo terror


class Jugador(Esfera):
    def __init__(self, pilas):
        super(Jugador, self).__init__(pilas, radio=0.3,
                                      radio_de_colision=0.35)
        self.posicion = (0, 1.7, 0)
        self._n = False
        self.aprender(pilas.habilidades.CaminarEnPrimeraPersona,
                      velocidad=5)

    def actualizar(self):
        # la linterna sigue a la cámara
        cam = self.pilas.escena.camara
        linterna.x, linterna.y, linterna.z = cam.x, cam.y, cam.z
        c = self.pilas.control
        if c.simbolo(pilas.simbolos.n) and not self._n:
            modo[0] = (modo[0] + 1) % len(MODOS)
            nombre, niebla = MODOS[modo[0]]
            self.pilas.escena.niebla = niebla
            cartel.texto = nombre
        self._n = c.simbolo(pilas.simbolos.n)


jugador = Jugador(pilas)
pilas.escena.niebla = MODOS[modo[0]][1]

cartel = pilas.actores.Texto(MODOS[modo[0]][0], x=10, y=40)
pilas.actores.Texto("WASD - N: cambiar niebla", x=10, y=10)

pilas.ejecutar()
