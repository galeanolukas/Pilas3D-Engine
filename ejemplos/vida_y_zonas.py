# -*- encoding: utf-8 -*-
"""Ejemplo: vida, barra de HUD, zona trampa y máquina de estados.

- El robot (vos) se mueve con flechas.
- El enemigo es una máquina de estados: patrulla girando hasta que te
  acercás, entonces te persigue.
- Si te toca, perdés vida (colisión por evento, no por `por siempre`).
- La zona roja te cura al entrar.
- La barra de arriba muestra tu vida; a los 0 el enemigo dice algo.
"""

import pilas3d

pilas = pilas3d.iniciar()
pilas.actores.Piso()
pilas.actores.Cielo()
pilas.actores.Texto('Flechas para moverte - la zona roja cura',
                    x=10, y=30)

jugador = pilas.actores.Robot(z=4)
jugador.aprender(pilas.habilidades.MoverseConElTeclado)
jugador.aprender(pilas.habilidades.Vida, vida=100)

enemigo = pilas.actores.Espectro(x=6, z=-4)
enemigo.aprender(pilas.habilidades.Vida, vida=50)


def patrullar(npc):
    npc.rotacion_y += 1.5
    if npc.distancia_plana_con(jugador) < 5:
        npc.cambiar_estado('perseguir')


def perseguir(npc):
    dx = jugador.x - npc.x
    dz = jugador.z - npc.z
    d = (dx * dx + dz * dz) ** 0.5 or 1
    npc.x += dx / d * 0.04
    npc.z += dz / d * 0.04
    if npc.distancia_plana_con(jugador) > 7:
        npc.cambiar_estado('patrullar')


enemigo.aprender(pilas.habilidades.MaquinaDeEstados,
                 estados={'patrullar': patrullar,
                          'perseguir': perseguir},
                 inicial='patrullar')

# evento de colisión: te lastima al tocarte (una vez por contacto)
pilas.colisiones.cuando_colisionan(
    jugador, enemigo, lambda: jugador.recibir_dano(20))

# zona de curación
zona = pilas.actores.Zona(x=-4, z=-2, radio=2, visible=True,
                          color=pilas.colores.rojo)
zona.cuando_entra(jugador, lambda: jugador.curar(40))

# HUD
pilas.actores.Barra(de=jugador, x=10, y=60, ancho=200)
pilas.actores.Texto('vida', x=10, y=78)

# game over declarativo
jugador.al_morir = lambda: pilas.actores.Texto(
    'te atraparon!', x=10, y=110, tamano=24)

pilas.camara.seguir_a(jugador, modo='tercera', distancia=8, altura=5)
pilas.ejecutar()
