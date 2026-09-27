# -*- encoding: utf-8 -*-
"""Carga de modelos .obj.

- El árbol toma sus colores solos desde el .mtl (tronco/copa)
- La luna usa su textura Diffuse_2K.png vía ``actor.imagen``
- La farola es gris por defecto (su .mtl no trae textura)

Los archivos están en ``modelos/`` (ignorados por git). Para usar los
tuyos: soltá el .obj en ``modelos/`` y listo.
"""

import os
import pilas3d

RAIZ = os.path.join(os.path.dirname(__file__), '..')
M = os.path.join(RAIZ, 'modelos')

pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - modelos obj")
pilas.fps.ver()

# Árbol: los colores Bark/Tree salen solos del archivo .mtl
arbol = pilas.actores.Modelo(
    os.path.join(M, 'props', 'low_poly_tree',
                 'Lowpoly_tree_sample.obj'),
    escala=0.1)

# Luna: el obj trae coordenadas UV; la textura se asigna con imagen
luna = pilas.actores.Modelo(
    os.path.join(M, 'props', 'moon', 'Moon 2K.obj'),
    x=6, y=3.5, escala=1.5)
luna.imagen = os.path.join(M, 'props', 'moon', 'texturas',
                           'Diffuse_2K.png')
luna.aprender(pilas.habilidades.GirarConstantemente, velocidad=20)

# Farola: sin textura, queda gris (el color del material o del actor)
farola = pilas.actores.Modelo(
    os.path.join(M, 'props', 'streetlight', 'Streetlight_LowRes.obj'),
    x=-5, escala=0.012)

pilas.actores.Piso()

# Sombras falsas (disco oscuro que sigue al actor, estilo años 90)
for actor in (arbol, luna, farola):
    pilas.actores.Sombra(actor)

# Luces: ambiente más bajo + una luz puntual cálida sobre el árbol
pilas.luces.direccional.ambiente = 0.18
pilas.luces.direccional.color = pilas.colores.gris
pilas.luces.agregar(pilas3d.luces.LuzPuntual(
    x=3, y=4, z=3, color=(1.0, 0.75, 0.4), alcance=12))

camara = pilas.escena_actual().camara
camara.posicion = (0, 6, 16)
camara.objetivo = (0, 2, 0)
camara.usar_control_orbital()   # drag: orbitar - rueda: zoom

pilas.ejecutar()
