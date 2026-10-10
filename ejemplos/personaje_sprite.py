# -*- encoding: utf-8 -*-
"""Personaje de sprites 2D: hoja con filas por dirección + estados.

    python3 ejemplos/personaje_sprite.py

- WASD/flechas : caminar — la fila cambia según la dirección
- ESPACIO      : atacar (fila extra, toma el control hasta terminar)
- M            : morir (queda congelado) / R revivir

El sprite es un billboard (siempre mira a la cámara); quieto vuelve
a ``cuadro_quieto``. Es un personaje distinto al ``ModeloGLTF``
riggeado — estilo Doom/RPG.

El NPC de la derecha usa la MISMA hoja pero declara solo 3 filas de
dirección y espeja 'derecha' <- 'izquierda' (``espejar``), el truco
de las hojas que solo traen un lateral.

``data/sprite_personaje.png`` (6x6) es un muñeco mínimo generado
por script; para pixel art real valen las hojas LPC de OpenGameArt
en el mismo formato.
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="Personaje 2D")
pilas.actores.Cielo('dia')
pilas.actores.Piso(tamano=30, divisiones=30)

pj = pilas.actores.PersonajeSprite(
    'sprite_personaje.png', columnas=6, filas=6,
    ancho=1.2, alto=1.2, y=0.6, velocidad=9)
pj.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)
pj.agregar_estado('atacar', fila=4, ciclica=False)
pj.agregar_estado('morir', fila=5, ciclica=False, quedarse=True)

# NPC espejado: la hoja tiene 'derecha' real, pero igual sirve para
# mostrar el flip: le declaramos el mapa sin 'derecha' y la espejamos.
npc = pilas.actores.PersonajeSprite(
    'sprite_personaje.png', columnas=6, filas=6,
    direcciones={'abajo': 0, 'izquierda': 1, 'arriba': 3},
    espejar={'derecha': 'izquierda'},
    ancho=1.2, alto=1.2, x=3, y=0.6, z=2, velocidad=9)
npc.definir_direccion('izquierda')          # mira hacia el jugador

cam = pilas.escena_actual().camara
cam.seguir_a(pj, modo='tercera', distancia=4.0, altura=2.0)

pilas.actores.Texto(
    "WASD: caminar - ESPACIO: atacar - M: morir - R: revivir",
    x=10, y=10, tamano=13)


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s.ESPACIO and pj.estado != 'atacar':
        pj.reproducir_estado('atacar')
    elif tecla == s.m:
        pj.reproducir_estado('morir')
    elif tecla == s.r:
        pj.reproducir_estado(None)


pilas.escena.cuando_pulsa_tecla = al_pulsar
pilas.ejecutar()
