# -*- encoding: utf-8 -*-
"""Efectos con partículas: fuego, humo, lluvia y una explosión.

Los presets de ``Particulas`` son classmethods que arman los
parámetros típicos; también podés configurar todo a mano.
"""

import pilas3d

pilas = pilas3d.iniciar(ancho=800, alto=600,
                        titulo="pilas3d - partículas")

pilas.actores.Cielo()
pilas.actores.Piso(tamano=60, divisiones=30)

# Fuego + humo sobre una fogata (cubos apilados a modo de leños).
fogata_x, fogata_z = -4, 0
for i in range(3):
    tronco = pilas.actores.Pared(x=fogata_x + i * 0.6 - 0.6,
                                 z=fogata_z, ancho=0.5, alto=0.4,
                                 profundidad=1.6)
    tronco.color = pilas.colores.marron
    tronco.rotacion_y = i * 60

pilas.actores.Particulas.fuego(pilas, x=fogata_x, y=0.4, z=fogata_z)
pilas.actores.Particulas.humo(pilas, x=fogata_x, y=1.6, z=fogata_z)

# Lluvia cayendo sobre una zona (un poco a la derecha).
pilas.actores.Particulas.lluvia(pilas, x=6, y=8, z=0)

# Una explosión única cada 4 segundos (ciclico=False se apaga sola).
def explotar():
    import random
    pilas.actores.Particulas.explosion(
        pilas, x=random.uniform(-2, 4), y=random.uniform(1, 3),
        z=random.uniform(-4, 2))

pilas.tareas.siempre(4.0, explotar)

pilas.actores.Texto("fuego + humo a la izquierda, lluvia a la "
                    "derecha, explosión cada 4s",
                    x=10, y=30, tamano=13)

camara = pilas.escena_actual().camara
camara.usar_control_orbital()

pilas.ejecutar()
