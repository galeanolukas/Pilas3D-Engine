# -*- encoding: utf-8 -*-
"""Ejemplo: un NPC que piensa solo con la IA local.

Un mono con la habilidad ``Cerebro`` decide cada 3 segundos qué hacer
(moverse, girar, hablar, acercarse o alejarse del jugador). Vos sos el
robot: movete con las flechas y mirá cómo el mono reacciona.

Además tiene un "área de saludo": si te acercás a menos de 3 metros,
te mira y te responde con un globo — la frase la genera el LLM (o un
repertorio fijo si Ollama no está corriendo). Al alejarte a más de 6
metros el saludo se rearma, como el trigger de un juego de verdad.

Requiere Ollama corriendo (se instala solo la primera vez).
"""

import random
import threading

import pilas3d

pilas = pilas3d.iniciar()
pilas.actores.Piso()
pilas.actores.Texto(
    'Flechas: mover - acercate al mono y te saluda (<3 m)')

jugador = pilas.actores.Robot(z=3)
jugador.aprender(pilas.habilidades.MoverseConElTeclado)

mono = pilas.actores.Mono(x=4)
mono.aprender(pilas.habilidades.Cerebro,
              cada=3,
              personalidad='sos un mono jugueton: te gusta acercarte, '
                           'saludar y a veces escaparte de repente',
              objetivo=jugador)

# -- área de saludo ----------------------------------------------------------

RADIO_SALUDO = 3.0    # a esta distancia te habla
RADIO_REARME = 6.0    # hay que alejarse esto para que vuelva a saludar
saludo = {'listo': True, 'pensando': False}
SALUDOS = ['¡hola, humano!', '¿jugamos a algo?', '¡te escuché llegar!',
           '¡qué susto, casi no te veo!', '¡bananas tenemos para rato!']


def saludar():
    """Pide al LLM una frase (en un hilo, no traba el juego); si
    Ollama no responde usa el repertorio fijo."""
    if saludo['pensando']:
        return
    saludo['pensando'] = True

    def pedir():
        try:
            from pilas3d.ia import asistente
            t = asistente.llamar_ollama(
                'El jugador se te acercó. Saludalo con UNA frase muy '
                'corta.',
                system='Sos un mono NPC juguetón dentro de un '
                       'videojuego. Respondé solo la frase, sin '
                       'comillas ni emojis.')
            frase = (t or '').strip().split('\n')[0].strip('"*')
            mono.decir(frase or random.choice(SALUDOS), duracion=4)
        except Exception:
            mono.decir(random.choice(SALUDOS), duracion=4)
        finally:
            saludo['pensando'] = False

    threading.Thread(target=pedir, daemon=True).start()


def vigilar():
    """Trigger de proximidad: dispara una vez al entrar al radio y
    se rearma cuando el jugador se aleja."""
    d = jugador.distancia_plana_con(mono)
    if d < RADIO_SALUDO and saludo['listo']:
        saludo['listo'] = False
        mono.mirar_hacia(jugador.x, jugador.z)   # te encara al hablar
        saludar()
    elif d > RADIO_REARME:
        saludo['listo'] = True


pilas.tareas.siempre(0, vigilar)
pilas.ejecutar()
