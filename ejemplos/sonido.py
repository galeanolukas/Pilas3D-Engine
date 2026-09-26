# -*- encoding: utf-8 -*-
"""Sonidos.

- ESPACIO: reproduce un efecto (saltar.wav) y el cubo "salta"
- Flechas/WASD: mover el cubo
- Un tick suena solo cada 2 segundos (tarea)

Para música de fondo ver ``pilas.musica.cargar()``: funciona igual pero
reproduce en streaming y en bucle por defecto. Nota: pyglet decodifica
.wav y .ogg nativamente; .mp3 necesita ffmpeg instalado.
"""

from pyglet.window import key

import pilas3d

pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - sonidos")
pilas.fps.ver()

cubo = pilas.actores.Cubo()
cubo.color = pilas.colores.verde
cubo.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=6)

pilas.actores.Texto("ESPACIO: sonido + salto - flechas: mover",
                    x=10, y=10)

# Si no hay placa de audio se cargan "deshabilitados": misma API, no-op.
salto = pilas.sonidos.cargar('saltar.wav')
tick = pilas.sonidos.cargar('tick.wav')


def al_pulsar_tecla(simbolo, modificadores):
    if simbolo == key.SPACE:
        salto.reproducir()
        cubo.rotacion_y = 0  # marca visual
        cubo.y = 1.5


pilas.ventana.push_handlers(on_key_press=al_pulsar_tecla)


def gravedad_salto():
    if cubo.y > 0:
        cubo.y = max(0, cubo.y - 4 * pilas.dt)
        cubo.rotacion_y += 200 * pilas.dt


pilas.tareas.siempre(0.05, gravedad_salto)
pilas.tareas.siempre(2, lambda: tick.reproducir())

pilas.ejecutar()
