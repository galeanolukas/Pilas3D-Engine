# -*- encoding: utf-8 -*-
"""NPC que conversa: responde con Ollama y habla con Piper.

Le apretás ESPACIO y te dice hola; con ENTER le hacés una pregunta.
La primera vez descarga Piper + la voz (~90 MB) y el modelo de IA.

    python3 ejemplos/npc_ia.py
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - npc con IA")
pilas.escena.fondo = pilas.colores.gris_oscuro
pilas.actores.Piso(tamano=20, divisiones=20)
pilas.actores.Ejes(largo=3)

npc = pilas.actores.ActorIA('robot', nombre='Robi')
npc.decir('ESPACIO: hablo - ENTER: me preguntás algo')

pilas.actores.Texto(
    "espacio: el npc habla - enter: pregunta fija\n"
    "(la 1ra vez descarga Piper y el modelo de IA)",
    x=10, y=10, tamano=13)


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s.ESPACIO:
        npc.hablar('hola, soy Robi, tu npc parlanchín')
    elif tecla == s.ENTER:
        npc.preguntar('decime un chiste corto de robots')


pilas.escena.cuando_pulsa_tecla = al_pulsar
pilas.ejecutar()
