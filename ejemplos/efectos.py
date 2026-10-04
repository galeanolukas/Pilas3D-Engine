# -*- encoding: utf-8 -*-
"""Efectos de jugo (``pilas.efectos``) sobre cualquier actor.

Cada tecla le aplica un efecto al robot — la moneda flota sola
para mostrar ``flotar`` corriendo todo el tiempo:

    1  parpadear     flash de invencibilidad (transparencia on/off)
    2  temblar       sacudida de impacto
    3  pulsar        squash & stretch (crece y vuelve)
    4  saltar        saltito y vuelve al piso
    5  flash         tinte rojo un instante
    6  desvanecer    se apaga y aparece de nuevo
    7  flotar        empieza/deja de flotar (devuelve la tarea)
    8  temblar_pantalla   shake de cámara (explosión)
    9  hit_stop      micro-pausa de impacto + shake (golpe fuerte)
    0  estela        estela de partículas on/off

    flechas: mover al robot

    python3 ejemplos/efectos.py
"""

import pilas3d

pilas = pilas3d.iniciar()
pilas.actores.Piso()
pilas.actores.Cielo('dia')

robot = pilas.actores.Robot(z=2)
robot.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=5)

moneda = pilas.actores.Esfera(x=3, y=0.6, radio=0.35)
moneda.color = pilas.colores.amarillo
pilas.efectos.flotar(moneda, altura=0.4)       # pickup flotando

pilas.actores.Texto(
    '1 parpadear - 2 temblar - 3 pulsar - 4 saltar - 5 flash\n'
    '6 desvanecer - 7 flotar - 8 shake - 9 hit-stop - 0 estela', y=10)

flote = {'tarea': None}
rastro = {'emisor': None}


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s._1:
        pilas.efectos.parpadear(robot)
    elif tecla == s._2:
        pilas.efectos.temblar(robot)
    elif tecla == s._3:
        pilas.efectos.pulsar(robot)
    elif tecla == s._4:
        pilas.efectos.saltar(robot)
    elif tecla == s._5:
        pilas.efectos.flash(robot, pilas.colores.rojo)
    elif tecla == s._6:
        # se apaga y al segundo aparece de nuevo
        pilas.efectos.desvanecer(robot)
        pilas.tareas.una_vez(1.2, lambda: pilas.efectos.aparecer(
            robot))
    elif tecla == s._7:
        if flote['tarea'] is None:
            flote['tarea'] = pilas.efectos.flotar(robot, altura=0.5)
        else:
            flote['tarea'].eliminar()
            flote['tarea'] = None
            robot.y = [0]                    # baja suave
    elif tecla == s._8:
        pilas.efectos.temblar_pantalla(intensidad=0.5)
    elif tecla == s._9:
        # combo clásico de golpe fuerte: congela + sacude + tinta
        pilas.efectos.hit_stop(0.12, escala=0.0)
        pilas.efectos.temblar_pantalla(0.4, 0.3)
        pilas.efectos.flash(robot, pilas.colores.rojo)
    elif tecla == s._0:
        emisor = rastro['emisor']
        if emisor is None or not emisor.esta_en_escena():
            rastro['emisor'] = pilas.efectos.estela(
                robot, color=pilas.colores.celeste)
        else:
            emisor.eliminar()
            rastro['emisor'] = None


pilas.escena.cuando_pulsa_tecla = al_pulsar
pilas.ejecutar()
