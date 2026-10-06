# -*- encoding: utf-8 -*-
"""Servir la escena a un navegador (puente WebSocket + Three.js).

    python3 ejemplos/servir_web.py           # http://localhost:8000/
    python3 ejemplos/servir_web.py --lan     # visible en toda la red

El motor corre en Python (acá sin ventana, como un servidor) y el
navegador dibuja con WebGL: sombras reales, materiales PBR, niebla.
Las teclas del navegador (flechas/WASD) viajan de vuelta y entran a
``pilas.control`` — el robot se maneja desde el browser.
"""

import sys

import pilas3d
from pilas3d.luces import LuzPuntual
from pilas3d.personaje import crear_personaje
from pilas3d.esqueleto import animacion_procedural

publico = '--lan' in sys.argv

# escena de demo: personaje generado + terreno + lámparas
crear_personaje('/tmp/heroe_web.glb', alto=1.8,
                colores={'camisa': (200, 60, 60)})

pilas = pilas3d.iniciar(sin_ventana=True)   # motor sin ventana
pilas.escena.niebla = (pilas.colores.gris_oscuro, 25, 80)

pilas.actores.Terreno(celdas=24, tamano_celda=1.0)

heroe = pilas.actores.ModeloGLTF('/tmp/heroe_web.glb', y=0)
animacion_procedural(heroe, 'caminar')
heroe.animar('caminar')
heroe.aprender(pilas.habilidades.MoverseConElTeclado)

pilas.actores.Cubo(x=3, y=0.5, z=0)
pilas.actores.Esfera(x=-3, y=1, z=0)
pilas.luces.agregar(LuzPuntual(x=0, y=4, z=3,
                               color=(255, 200, 150)))

pilas.camara.posicion = (0, 4, 9)
pilas.camara.objetivo = (0, 1, 0)

pilas.web.servir(puerto=8000, publico=publico)
pilas.web.ejecutar()        # loop headless a 60 Hz
