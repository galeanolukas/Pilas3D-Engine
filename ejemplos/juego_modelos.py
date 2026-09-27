# -*- encoding: utf-8 -*-
"""Noche en la plaza: mini-juego de recolectar usando modelos .obj.

Usa los modelos descargados en ``modelos/`` (árbol low-poly, farola
y luna). Si no están, pone reemplazos de formas simples.

WASD moverse - mouse mirar - juntar las 6 gemas - ESC salir
"""

import os
import random

import pilas3d
from pilas3d.actores.esfera import Esfera
from pilas3d.actores.cubo import Cubo

pilas = pilas3d.iniciar(titulo="pilas3d - noche en la plaza")

# --- noche: ambiente bajo y cielo estrellado ---
pilas.luces.direccional.ambiente = 0.15
pilas.luces.direccional.color = pilas.colores.gris
pilas.actores.Cielo()

piso = pilas.actores.Plano(ancho=60, profundidad=60)
piso.imagen = pilas3d.obtener_ruta('data/pasto.png')

ARBOL = 'modelos/props/low_poly_tree/Lowpoly_tree_sample.obj'
FAROLA = 'modelos/props/streetlight/Streetlight_LowRes.obj'
LUNA = 'modelos/props/moon/Moon 2K.obj'

rng = random.Random(2)
puntos = pilas.actores.Puntaje(x=10, y=450)


def hacer_arbol(x, z):
    if os.path.exists(ARBOL):
        return pilas.actores.Modelo(ARBOL, x=x, z=z, escala=0.08)
    tronco = pilas.actores.Cubo(x=x, z=z, y=0.5)
    tronco.color = pilas.colores.marron
    copa = pilas.actores.Esfera(x=x, z=z, y=2.0, radio=1.0)
    copa.color = pilas.colores.verde
    return copa


def hacer_farola(x, z):
    if os.path.exists(FAROLA):
        pilas.actores.Modelo(FAROLA, x=x, z=z, escala=0.02)
    else:
        poste = pilas.actores.Pared(x=x, z=z, ancho=0.15, alto=3.2,
                                  profundidad=0.15)
        poste.color = pilas.colores.gris
    # cada farola alumbra de verdad con una luz puntual
    pilas.luces.agregar(pilas3d.luces.LuzPuntual(
        x=x, y=3.4, z=z, color=(1.0, 0.8, 0.45), alcance=9))


def hacer_luna():
    if os.path.exists(LUNA):
        luna = pilas.actores.Modelo(LUNA, x=14, y=22, z=-30,
                                    escala=2.2)
        luna.imagen = 'modelos/props/moon/texturas/Diffuse_2K.png'
    else:
        luna = pilas.actores.Esfera(x=14, y=22, z=-30, radio=2)
        luna.color = pilas.colores.blanco
    luna.aprender(pilas.habilidades.GirarConstantemente, velocidad=4)


def hacer_gema(x, z):
    gema = pilas.actores.Esfera(x=x, y=0.6, z=z, radio=0.35,
                              radio_de_colision=0.6)
    gema.color = pilas.colores.amarillo
    gema.aprender(pilas.habilidades.GirarConstantemente, velocidad=180)
    pilas.actores.Sombra(gema)
    return gema


class Jugador(Esfera):
    """Recolecta gemas al acercarse (primera persona)."""

    def __init__(self, pilas, gemas):
        super(Jugador, self).__init__(
            pilas, radio=0.3, radio_de_colision=0.4)
        self.gemas = gemas
        self.posicion = (0, 0, 20)
        self.aprender(
            pilas.habilidades.CaminarEnPrimeraPersona, velocidad=7)

    def actualizar(self):
        for gema in list(self.gemas):
            if self.colisiona_en_plano_con(gema):
                gema.eliminar()
                self.gemas.remove(gema)
                puntos.aumentar()
                pilas.sonidos.cargar('smile.wav').reproducir()
        if not self.gemas:
            puntos.texto = "¡GANASTE!"


# --- armar la plaza ---
hacer_luna()
for x, z in [(-8, -8), (8, -8), (-8, 8), (8, 8)]:
    hacer_farola(x, z)
for _ in range(12):
    hacer_arbol(rng.randint(-22, 22), rng.randint(-22, 22))
gemas = [hacer_gema(rng.randint(-20, 20), rng.randint(-20, 20))
         for _ in range(6)]

jugador = Jugador(pilas, gemas)
pilas.actores.Texto("Juntá las 6 gemas - WASD + mouse", x=10, y=10)

pilas.ejecutar()
