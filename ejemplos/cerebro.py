# -*- encoding: utf-8 -*-
"""Ejemplo: un NPC que piensa solo con la IA local.

Un mono con la habilidad ``Cerebro`` decide cada 3 segundos qué hacer
(moverse, girar, hablar, acercarse o alejarse del jugador). Vos sos el
robot: movete con las flechas y mirá cómo el mono reacciona.

Requiere Ollama corriendo (se instala solo la primera vez).
"""

import pilas3d

pilas = pilas3d.iniciar()
pilas.actores.Piso()
pilas.actores.Texto('Flechas: mover al robot - el mono piensa solo')

jugador = pilas.actores.Robot(z=3)
jugador.aprender(pilas.habilidades.MoverseConElTeclado)

mono = pilas.actores.Mono(x=4)
mono.aprender(pilas.habilidades.Cerebro,
              cada=3,
              personalidad='sos un mono jugueton: te gusta acercarte, '
                           'saludar y a veces escaparte de repente',
              objetivo=jugador)

pilas.ejecutar()
