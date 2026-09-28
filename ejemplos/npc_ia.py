# -*- encoding: utf-8 -*-
"""NPCs que conversan: responden con Ollama y hablan con Piper.

Robi (robot, voz 'hombre') y Dani (humanoide, voz 'mujer'
argentina). Teclas:

    1      -> Robi habla
    2      -> Dani habla
    3      -> Dani responde una pregunta fija con la IA
    ENTER  -> escribís tu pregunta y Dani la responde

Las voces se descargan la primera vez a ``pilas3d/_vendor/piper/``
(~240 MB con las tres). La IA necesita Ollama corriendo.

    python3 ejemplos/npc_ia.py
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - npcs con IA")
pilas.escena.fondo = pilas.colores.gris_oscuro
pilas.actores.Piso(tamano=20, divisiones=20)

robi = pilas.actores.ActorIA('robot', nombre='Robi', voz='hombre')
robi.x = -2

dani = pilas.actores.ActorIA('humanoide', nombre='Dani', voz='mujer')
dani.x = 2
dani.subtitulo.y = 40        # su subtítulo va una línea más arriba

robi.decir('1: Robi - 2: Dani - 3: chiste - ENTER: escribir')


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s._1:
        robi.hablar('hola, soy Robi, tu npc parlanchín')
    elif tecla == s._2:
        dani.hablar('y yo soy Dani, encantada de conocerte')
    elif tecla == s._3:
        dani.preguntar('decime un chiste corto de robots')
    elif tecla == s.ENTER:
        pilas.pedir_texto('preguntale a Dani:',
                          al_aceptar=dani.preguntar)


pilas.escena.cuando_pulsa_tecla = al_pulsar
pilas.ejecutar()
