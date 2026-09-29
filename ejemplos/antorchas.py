# -*- encoding: utf-8 -*-
"""Noche con antorchas: lamparas con Parpadear sobre un mundo oscuro.

Caminá con las flechas entre los pilares — cada antorcha titila
solita. La escena casi no tiene ambiente: toda la luz sale de las
lámparas, así se aprecia cómo el alcance modula la oscuridad.
"""

import pilas3d

pilas = pilas3d.iniciar()

# Casi sin luz ambiental: la noche de verdad.
pilas.luces.direccional.ambiente = 0.08
pilas.luces.direccional.color = pilas.colores.azul

pilas.actores.Cielo()                      # estrellas
pilas.actores.Piso()

# Antorchas en los vértices de un pasillo.
for x, z in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, -6)]:
    pilas.actores.Pared(x=x, z=z, ancho=0.5, alto=2.5)
    antorcha = pilas.actores.Lampara(x=x, y=3, z=z,
                                   color=pilas.colores.naranja,
                                   alcance=7)
    antorcha.aprender(pilas.habilidades.Parpadear,
                      intensidad=0.3, velocidad=8)

jugador = pilas.actores.Robot()
jugador.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)
pilas.camara.seguir_a(jugador, modo='tercera')

pilas.actores.Texto('flechas: caminar entre antorchas', x=10, y=10)

pilas.ejecutar()
