# -*- encoding: utf-8 -*-
"""Terreno deformable: colinas, un lago y un robot que camina siguiendo
la altura real del suelo.

- flechas: camina el robot (pega al terreno con altura_suelo)
- U/J: sube/baja el vértice de la rejilla bajo el robot
- H: colina bajo el robot - B: pozo (lago si queda bajo el agua)
- P: pinta la zona con la baldosa elegida (TAB cambia baldosa)
- W: pone/saca el agua - G: guarda en mapas/ejemplo.terreno.json
- espacio + mouse: orbita la cámara - rueda: zoom
"""

import pilas3d

pilas = pilas3d.iniciar()
pilas.escena.fondo = pilas.colores.gris_oscuro

t = pilas.actores.Terreno(celdas=24)

# un par de colinas y un lago para arrancar
t.montana(6, 6, radio=4, altura=2.5)
t.montana(18, 7, radio=3, altura=1.8)
t.pozo(17, 17, radio=3, profundidad=1.8)
t.pintar_zona(17, 17, 3, 'agua')
t.agua = 0.4                       # el pozo se llena: lago

robot = pilas.actores.Robot()
robot.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=6.0)
pilas.camara.seguir_a(robot, modo='tercera')

tiles = {'n': 0}

texto = pilas.actores.Texto(
    "flechas: caminar | U/J: vértice | H colina B pozo | P pintar "
    "TAB baldosa | W agua | G guardar", tamano=14)
texto.x, texto.y = 10, 10


def al_actualizar():
    # el robot camina sobre el terreno, no por el aire
    h = t.altura_suelo(robot.x, robot.z)
    if h is not None:
        robot.y = h


pilas.tareas.siempre(0, al_actualizar)


def celda_bajo_robot():
    """Celda del terreno donde está parado el robot."""
    li = (robot.x - t.x) / t.tamano_celda + t.celdas / 2.0
    lk = (robot.z - t.z) / t.tamano_celda + t.celdas / 2.0
    return int(li), int(lk)


def al_pulsar(tecla):
    s = pilas.simbolos
    i, k = celda_bajo_robot()
    if tecla == s.u:
        t.subir(i, k, 0.3)
    elif tecla == s.j:
        t.bajar(i, k, 0.3)
    elif tecla == s.h:
        t.montana(i, k, radio=3, altura=0.8)
    elif tecla == s.b:
        t.pozo(i, k, radio=3, profundidad=0.8)
    elif tecla == s.p:
        t.pintar_zona(i, k, 2, t._tiles[tiles['n']])
    elif tecla == s.TAB:
        tiles['n'] = (tiles['n'] + 1) % len(t._tiles)
        texto.texto = "baldosa: " + t._tiles[tiles['n']]
    elif tecla == s.w:
        t.agua = None if t.agua is not None else 0.4
    elif tecla == s.g:
        ruta = t.guardar('mapas/ejemplo.terreno.json')
        texto.texto = "guardado en " + ruta


pilas.escena.cuando_pulsa_tecla = al_pulsar
pilas.ejecutar()
