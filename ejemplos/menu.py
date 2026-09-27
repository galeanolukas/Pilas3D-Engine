# -*- encoding: utf-8 -*-
"""Menú de opciones con pilas.actores.Menu (overlay 2D).

Flechas/WS + ENTER para navegar, o click con el mouse. Las opciones
pueden devolver un texto nuevo para ciclar valores (como los menús
de gráficos de los juegos).
"""

import pilas3d

pilas = pilas3d.iniciar(ancho=640, alto=480, titulo="pilas3d - menu")

pilas.actores.Piso(tamano=40)
pilas.mostrar_ejes(3)

cubo = pilas.actores.Cubo(y=1)
cubo.color = pilas.colores.verde
cubo.aprender(pilas.habilidades.GirarConstantemente, velocidad=40)

pilas.actores.Cielo('dia')

RESOLUCIONES = [(640, 480), (800, 600), (1024, 768)]
res_idx = [0]

CALIDADES = ['baja', 'media', 'alta']
cal_idx = [2]


def empezar():
    pilas.actores.Texto("JUGANDO!", x=300, y=440, tamano=30)


def ciclar_resolucion():
    res_idx[0] = (res_idx[0] + 1) % len(RESOLUCIONES)
    ancho, alto = RESOLUCIONES[res_idx[0]]
    if pilas.ventana is not None:
        pilas.ventana.set_size(ancho, alto)
    return "Resolución: %dx%d" % (ancho, alto)


def ciclar_calidad():
    cal_idx[0] = (cal_idx[0] + 1) % len(CALIDADES)
    calidad = CALIDADES[cal_idx[0]]
    # algo visible de verdad: la niebla se cierra en 'baja'
    if calidad == 'baja':
        pilas.escena.niebla = ((0.5, 0.55, 0.6), 8, 30)
    elif calidad == 'media':
        pilas.escena.niebla = ((0.5, 0.55, 0.6), 20, 60)
    else:
        pilas.escena.niebla = None
    return "Calidad: %s" % calidad


pilas.actores.Menu(
    titulo="PILAS3D",
    opciones=[
        ("Jugar", empezar),
        ("Resolución: 640x480", ciclar_resolucion),
        ("Calidad: alta", ciclar_calidad),
        ("Salir", pilas.terminar),
    ],
    x=230, y=340, tamano=22,
    color=pilas.colores.blanco,
    seleccionado=pilas.colores.amarillo)

pilas.actores.Texto("flechas + ENTER o click con el mouse",
                    x=10, y=10)

pilas.ejecutar()
