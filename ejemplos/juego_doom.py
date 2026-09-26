# -*- encoding: utf-8 -*-
"""Mini-FPS estilo Doom: laberinto, enemigos que persiguen y disparo.

- WASD/flechas: caminar (las paredes bloquean)
- Mouse: mirar alrededor
- Click izquierdo: disparar (rayo desde la cámara)
- Si un enemigo te toca: volvés al inicio y perdés una vida
"""

import random

import pilas3d
from pilas3d.actores.esfera import Esfera

AREA = 14

pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - mini doom")

pilas.actores.Piso(tamano=2 * AREA, divisiones=2 * AREA)

# Perímetro del laberinto
for pos in (-AREA, AREA):
    pilas.actores.Pared(z=pos, ancho=2 * AREA, alto=3)
    pilas.actores.Pared(x=pos, ancho=2 * AREA, alto=3).rotacion_y = 90

# Paredes internas del laberinto
pilas.actores.Pared(x=-4, z=-3, ancho=8)
pilas.actores.Pared(x=5, z=4, ancho=8).rotacion_y = 90
pilas.actores.Pared(x=-6, z=7, ancho=6).rotacion_y = 90

puntaje = pilas.actores.Puntaje(x=10, y=60, prefijo="Puntos: ")
vidas = pilas.actores.Puntaje(x=200, y=60, prefijo="Vidas: ")
vidas.valor = 3
vidas.texto = "Vidas: 3"
pilas.actores.Texto("WASD moverse - mouse mirar - click disparar",
                    x=10, y=30)


class Enemigo(Esfera):
    """Esfera roja que persigue al jugador por el plano XZ."""

    def __init__(self, pilas, jugador, **kw):
        super(Enemigo, self).__init__(pilas, radio=0.7, **kw)
        self.color = pilas.colores.rojo
        self.jugador = jugador
        self.posicion = (random.uniform(-AREA + 2, AREA - 2), 0.7,
                         random.uniform(-AREA + 2, AREA - 2))

    def actualizar(self):
        j = self.jugador
        dx, dz = j.x - self.x, j.z - self.z
        d = (dx ** 2 + dz ** 2) ** 0.5
        if d > 0.1:
            v = 2.5 * self.pilas.dt
            self.x += dx / d * v
            self.z += dz / d * v
        self.rotacion_y += 60 * self.pilas.dt

        # Si toca al jugador: una vida menos y vuelta al inicio.
        if self.colisiona_con(j):
            j.posicion = (0, 0.4, 10)
            vidas.valor -= 1
            vidas.texto = "Vidas: %d" % vidas.valor
            if vidas.valor <= 0:
                pilas.actores.Texto("¡PERDISTE!", x=320, y=200, tamano=40)
                self.pilas.tareas.una_vez(2, pilas.terminar)


class Jugador(Esfera):
    """El cuerpo del jugador (se ve al mirar hacia abajo)."""

    def __init__(self, pilas, enemigos, **kw):
        super(Jugador, self).__init__(pilas, radio=0.4, **kw)
        self.color = pilas.colores.celeste
        self.enemigos = enemigos
        self.espera_disparo = 0.0
        self.aprender(pilas.habilidades.CaminarEnPrimeraPersona,
                      velocidad=6, altura=1.6)

    def actualizar(self):
        self.espera_disparo -= self.pilas.dt
        if self.pilas.control.boton_izquierdo and \
                self.espera_disparo <= 0:
            self.espera_disparo = 0.3
            blanco = self.pilas.escena_actual().camara.disparar_rayo(
                self.enemigos, alcance=40)
            if blanco:
                blanco.eliminar()
                self.enemigos.remove(blanco)
                puntaje.aumentar()
                if not self.enemigos:
                    pilas.actores.Texto("¡GANASTE!", x=340, y=200,
                                        tamano=40)


enemigos = [Enemigo(pilas, None) for _ in range(4)]
jugador = Jugador(pilas, enemigos, y=0.4, z=10)
for enemigo in enemigos:
    enemigo.jugador = jugador

pilas.ejecutar()
