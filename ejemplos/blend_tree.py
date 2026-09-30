# -*- encoding: utf-8 -*-
"""Ejemplo: blend tree — mezcla suave entre animaciones.

El lobo (Khronos Wolf) trae idle, creep, walk y run. En vez de
cambiar de clip de golpe, ``arbol_mezcla`` interpola la pose
entre los dos clips vecinos del parámetro "velocidad".

Flechas ARRIBA/ABAJO suben y bajan la velocidad (0..3); la pose
cruza de idle a caminar a correr sin saltos.
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - blend tree")

pilas.actores.Cielo('dia')
pilas.escena.fondo = pilas.colores.celeste
piso = pilas.actores.Piso(tamano=30, divisiones=30)
piso.color = pilas.colores.verde
pilas.luces.direccional.ambiente = 0.6

lobo = pilas.actores.ModeloGLTF(
    'modelos/personajes/wolf/Wolf-Blender-2.82a.glb')
lobo.escala = 2.5

# árbol 1D: valor del parámetro -> clip
PUNTOS = [(0, '04_Idle_Armature_0'),
          (1, '03_creep_Armature_0'),
          (2, '02_walk_Armature_0'),
          (3, '01_Run_Armature_0')]
velocidad = {'v': 0.0}

info = pilas.actores.Texto(
    "ARRIBA/ABAJO: velocidad - mouse: orbitar",
    x=10, y=440, tamano=13)
estado_txt = pilas.actores.Texto("", x=10, y=410, tamano=15)
estado_txt.color = pilas.colores.amarillo


def aplicar():
    lobo.arbol_mezcla(PUNTOS, velocidad['v'])
    partes = ["%s %.0f%%" % (n.split('_')[0], p * 100)
              for n, p in sorted(lobo._mezcla.items()) if p > 0.01]
    estado_txt.texto = "v=%.1f  %s" % (velocidad['v'], ' + '.join(partes))


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s.ARRIBA:
        velocidad['v'] = min(3.0, velocidad['v'] + 0.1)
    elif tecla == s.ABAJO:
        velocidad['v'] = max(0.0, velocidad['v'] - 0.1)
    else:
        return
    aplicar()


pilas.escena.cuando_pulsa_tecla = al_pulsar
aplicar()

camara = pilas.escena.camara
camara.posicion = (0, 2.2, 4.5)
camara.objetivo = (0, 1, 0)
camara.usar_control_orbital()

pilas.ejecutar()
