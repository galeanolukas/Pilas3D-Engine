# -*- encoding: utf-8 -*-
"""Mini-juego completo: recolectar monedas.

Movés la esfera con flechas o WASD; al tocar una moneda suma puntos
y reaparece en otro lugar. Usa colisiones, texto y cámara que sigue.
"""

import random

import pilas3d
from pilas3d.actores.esfera import Esfera

AREA = 9  # las monedas aparecen dentro de un cuadrado de 2*AREA


class Moneda(Esfera):
    def __init__(self, pilas, **kw):
        super(Moneda, self).__init__(pilas, radio=0.4, **kw)
        self.color = pilas.colores.amarillo
        self.reposicionar()

    def reposicionar(self):
        self.posicion = (
            random.uniform(-AREA, AREA),
            0.4,
            random.uniform(-AREA, AREA),
        )

    def actualizar(self):
        self.rotacion_y += 90 * self.pilas.dt


class Jugador(Esfera):
    def __init__(self, pilas, monedas, puntaje, **kw):
        super(Jugador, self).__init__(pilas, radio=0.7, **kw)
        self.color = pilas.colores.celeste
        self.monedas = monedas
        self.puntaje = puntaje

    def actualizar(self):
        v = 8 * self.pilas.dt
        c = self.pilas.control
        if c.izquierda:
            self.x -= v
        if c.derecha:
            self.x += v
        if c.arriba:
            self.z -= v
        if c.abajo:
            self.z += v

        for moneda in self.monedas:
            if self.colisiona_con(moneda):
                moneda.reposicionar()
                self.puntaje.aumentar()

        camara = self.pilas.escena_actual().camara
        camara.posicion = (self.x, 10, self.z + 12)
        camara.objetivo = (self.x, 0, self.z)


pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - recolectar")

pilas.actores.Piso(tamano=2 * AREA + 4, divisiones=2 * AREA + 4)

# El origen del overlay está abajo a la izquierda; usar posiciones
# bajas hace que el HUD no dependa del tamaño final de la ventana.
puntaje = pilas.actores.Puntaje(x=10, y=60, prefijo="Puntos: ")
pilas.actores.Texto(
    "Recolectá las monedas - flechas/WASD", x=10, y=30
)

monedas = [Moneda(pilas) for _ in range(6)]
Jugador(pilas, monedas, puntaje, y=0.7)

pilas.ejecutar()
