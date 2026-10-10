# -*- encoding: utf-8 -*-
"""Personaje de sprites 2D: una hoja con filas por dirección.

    python3 ejemplos/personaje_sprite.py

El sprite es un billboard (siempre mira a la cámara) y la fila de la
hoja cambia sola según el desplazamiento: abajo/izquierda/derecha/
arriba. Quietos quedan en ``cuadro_quieto``. Es el estilo de los RPG
y los NPC de Doom/Wolfenstein — un personaje distinto al riggeado
``ModeloGLTF``.

La hoja incluida (``data/sprite_personaje.png``, 6x4) es un muñeco
mínimo; para pixel art de verdad se usan hojas estilo LPC (9x4 o
más) de OpenGameArt — mismo formato.
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="Personaje 2D")
pilas.actores.Cielo('dia')
pilas.actores.Piso(tamano=30, divisiones=30)

pj = pilas.actores.PersonajeSprite(
    'sprite_personaje.png', columnas=6, filas=4,
    ancho=1.2, alto=1.2, y=0.6, velocidad=9)
pj.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)

cam = pilas.escena_actual().camara
cam.seguir_a(pj, modo='tercera', distancia=4.0, altura=2.0)

pilas.actores.Texto("WASD/flechas: caminar — la fila cambia según "
                    "la dirección", x=10, y=10, tamano=13)

pilas.ejecutar()
