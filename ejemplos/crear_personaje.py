# -*- encoding: utf-8 -*-
"""Generar un personaje low-poly riggeado desde cero, sin Blender.

``pilas3d.personaje.crear_personaje`` escribe un .glb con esqueleto
(19 huesos) y malla de cajas con rigid skinning — cada parte pegada
a un hueso. El resultado lo anima ``animacion_procedural`` o el
editor (``pilas3d-editor``, tecla V crea uno ahí mismo).

python3 ejemplos/crear_personaje.py
"""

import pilas3d
from pilas3d.personaje import crear_personaje
from pilas3d.esqueleto import animacion_procedural

# 1) generar el .glb (queda en modelos/personajes/, reutilizable)
ruta = crear_personaje('modelos/personajes/heroe.glb', alto=1.8,
                       colores={'camisa': (200, 60, 60),   # roja
                                'pelo': (30, 25, 20)})

pilas = pilas3d.iniciar()
pilas.actores.Cielo('dia')
pilas.actores.Piso()

# 2) cargarlo como cualquier .glb riggeado
heroe = pilas.actores.ModeloGLTF(ruta)

# 3) animación procedural: reconoce los nombres de hueso sola
animacion_procedural(heroe, 'caminar')
heroe.animar('caminar')

heroe.aprender(pilas.habilidades.MoverseConElTeclado)
pilas.camara.seguir_a(heroe, modo='tercera')

pilas.ejecutar()
