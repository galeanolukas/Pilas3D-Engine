# -*- encoding: utf-8 -*-
"""Menú de opciones con pilas.actores.Menu (overlay 2D).

Flechas/WS + ENTER para navegar, o click con el mouse. Tipos de
opción:

- acción:   ("Jugar", funcion)
- check:    ("Sonido", 'check', True, fn)   -> [x]/[ ]
- cíclica:  fn() devuelve texto nuevo        -> actualiza la etiqueta
- input:    ("Nombre", 'input', 'yo', fn)   -> ENTER edita, ENTER ok
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

VOLUMENES = [0.0, 0.25, 0.5, 0.75, 1.0]
vol_idx = [4]


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
    if calidad == 'baja':
        pilas.escena.niebla = ((0.5, 0.55, 0.6), 8, 30)
    elif calidad == 'media':
        pilas.escena.niebla = ((0.5, 0.55, 0.6), 20, 60)
    else:
        pilas.escena.niebla = None
    return "Calidad: %s" % calidad


def al_sonar(activo):
    pilas.sonidos.mute = not activo          # mute/sonido global


def ciclar_volumen():
    vol_idx[0] = (vol_idx[0] + 1) % len(VOLUMENES)
    v = VOLUMENES[vol_idx[0]]
    pilas.sonidos.volumen = v                # volumen maestro
    return "Volumen: %d%%" % int(v * 100)


def al_nombrar(nombre):
    pilas.actores.Texto("Hola, %s!" % nombre, x=260, y=40,
                        tamano=20)


pilas.actores.Menu(
    titulo="PILAS3D",
    opciones=[
        ("Jugar", empezar),
        ("Resolución: 640x480", ciclar_resolucion),
        ("Calidad: alta", ciclar_calidad),
        ("Sonido", 'check', True, al_sonar),
        ("Volumen: 100%", ciclar_volumen),
        ("Nombre", 'input', 'jugador', al_nombrar),
        ("Salir", pilas.terminar),
    ],
    x=230, y=360, tamano=20,
    color=pilas.colores.blanco,
    seleccionado=pilas.colores.amarillo)

pilas.actores.Texto("flechas + ENTER o click - input: ENTER edita, "
                    "ENTER confirma, ESC cancela", x=10, y=10)

pilas.ejecutar()
