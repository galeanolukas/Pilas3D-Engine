# -*- encoding: utf-8 -*-
"""Esfera con material compuesto (ambientCG/Poliigon).

Un pack de texturas con mapas de normal, rugosidad y color se pega a
cualquier actor con ``actor.material``: la esfera gira y se ve el
relieve del normal map + el brillo especular de la rugosidad.

- N: prende/apaga el normal map (para ver la diferencia)
- R: idem con el mapa de rugosidad
- A: la misma textura pero en un Plano debajo (suelo de baldosas)
- drag o espacio + mouse: orbita - rueda: zoom
"""

import os

import pilas3d

pilas = pilas3d.iniciar()
pilas.escena.fondo = pilas.colores.gris_oscuro

CARPETA = 'modelos/Tiles144_1K-JPG'
if not os.path.isdir(CARPETA):
    CARPETA = os.path.join('modelos',
                           'Poliigon_GrassPatchyGround_4585', '2K')

mat = pilas.materiales.desde_carpeta(CARPETA)
print("material detectado:", mat)

esfera = pilas.actores.Esfera(y=1.5)
esfera.escala = 2.0
esfera.material = mat
if mat.base:
    esfera.imagen = mat.base      # el color base (igual que antes)

piso = pilas.actores.Plano(y=0, ancho=14, profundidad=14)
piso.material = mat
if mat.base:
    piso.imagen = mat.base

# una lámpara naranja realza el especular y el relieve
pilas.actores.Lampara(x=3, y=4, z=2, alcance=14)
pilas.luces.direccional.ambiente = 0.35

texto = pilas.actores.Texto(
    "N: normal map on/off | R: rugosidad | drag: orbitar",
    tamano=15, x=10, y=10)


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s.n:
        esfera.material.normal = None if esfera.material.normal \
            else mat.normal
        texto.texto = "normal: " + \
            ("on" if esfera.material.normal else "off")
    elif tecla == s.r:
        esfera.material.rugosidad = \
            None if esfera.material.rugosidad else mat.rugosidad
        texto.texto = "rugosidad: " + \
            ("on" if esfera.material.rugosidad else "off")


pilas.escena.cuando_pulsa_tecla = al_pulsar

camara = pilas.escena.camara
camara.posicion = (5, 4, 7)
camara.objetivo = (0, 1.2, 0)
camara.usar_control_orbital(
    boton=pilas.simbolos.BOTON_IZQUIERDO | pilas.simbolos.BOTON_DERECHO,
    tecla=pilas.simbolos.ESPACIO)


def girar():
    esfera.rotacion_y += 15 * pilas.dt


pilas.tareas.siempre(0, girar)
pilas.ejecutar()
