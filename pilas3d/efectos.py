# -*- encoding: utf-8 -*-
"""Efectos de "jugo" (game feel) aplicables a cualquier actor.

Funciones cortas sobre ``pilas.tareas`` e interpolaciones — se le
ponen a un actor y listo::

    pilas.efectos.parpadear(heroe)              # invencibilidad
    pilas.efectos.temblar(enemigo)              # recibió un golpe
    t = pilas.efectos.flotar(moneda)            # pickup flotando
    t.eliminar()                                # dejó de flotar
    pilas.efectos.pulsar(cubo)                  # squash & stretch
    pilas.efectos.flash(heroe, pilas.colores.rojo)
    pilas.efectos.desvanecer(fantasma, eliminar=True)

Los efectos continuos devuelven su :class:`Tarea` — con
``tarea.eliminar()`` se cortan antes. Si el actor sale de escena,
el efecto muere solo (salvo restauraciones, que se guardan).
"""

import math
import random
import time


class Efectos(object):
    """Punto de acceso ``pilas.efectos``."""

    def __init__(self, pilas):
        self.pilas = pilas
        self._escala = 1.0
        self._escala_hasta = 0.0

    # -- transparencia ---------------------------------------------------

    def parpadear(self, actor, veces=6, cada=0.12):
        """Flash de invencibilidad: alterna la transparencia del
        actor ``veces`` veces y la deja como estaba."""
        orig = actor.transparencia
        estado = {'n': 0}

        def tick():
            estado['n'] += 1
            if estado['n'] >= veces * 2:
                actor.transparencia = orig
                return False
            actor.transparencia = 60 if estado['n'] % 2 else orig
            return actor.esta_en_escena()

        actor.transparencia = 60
        return self.pilas.tareas.condicional(cada, tick)

    def aparecer(self, actor, duracion=1.0):
        """Fundido de entrada: arranca invisible y aparece suave."""
        actor.transparencia = 100
        actor.transparencia = ([0], duracion)
        return actor

    def desvanecer(self, actor, duracion=1.0, eliminar=False):
        """Fundido de salida; con ``eliminar=True`` borra al actor
        cuando termina de apagarse."""
        actor.transparencia = ([100], duracion)
        if eliminar:
            self.pilas.tareas.una_vez(duracion, actor.eliminar)
        return actor

    # -- posición y escala -------------------------------------------------

    def temblar(self, actor, duracion=0.4, intensidad=0.25):
        """Sacudida de impacto: offset al azar durante ``duracion``
        segundos; al terminar vuelve a su posición exacta."""
        orig = actor.posicion
        t0 = self.pilas.tareas.contador_de_tiempo

        def tick():
            paso = self.pilas.tareas.contador_de_tiempo - t0
            if paso >= duracion or not actor.esta_en_escena():
                actor.posicion = orig
                return False
            actor.posicion = (
                orig[0] + random.uniform(-1, 1) * intensidad,
                orig[1] + random.uniform(-1, 1) * intensidad * 0.5,
                orig[2] + random.uniform(-1, 1) * intensidad)
            return True

        return self.pilas.tareas.condicional(0, tick)

    def flotar(self, actor, altura=0.3, velocidad=1.5):
        """Vaivén continuo en ``y`` alrededor de la posición actual
        (pickups, fantasmas). Devuelve la tarea para detenerlo."""
        y0 = actor.y
        t0 = self.pilas.tareas.contador_de_tiempo

        def tick():
            t = self.pilas.tareas.contador_de_tiempo - t0
            actor.y = y0 + math.sin(t * velocidad * 2 * math.pi) \
                * altura
            return actor.esta_en_escena()

        return self.pilas.tareas.condicional(0, tick)

    def pulsar(self, actor, escala=1.25, duracion=0.3):
        """Squash & stretch: crece a ``escala`` y vuelve — peso,
        rebote, confirmación de algo que pasó."""
        orig = actor.escala
        actor.escala = ([orig * escala, orig], duracion)
        return actor

    def saltar(self, actor, altura=1.5, duracion=0.5):
        """Saltito: sube ``altura`` y baja al punto de partida."""
        y0 = actor.y
        actor.y = ([y0 + altura, y0], duracion)
        return actor

    def estela(self, actor, color=None, tamano=5.0, vida=0.5,
               cantidad=80):
        """Estela de partículas pegada al actor (velocidad, magia).
        Devuelve el emisor — ``emisor.eliminar()`` la quita; si el
        actor sale de escena se apaga sola."""
        emisor = self.pilas.actores.Particulas(
            cantidad=cantidad, vida=vida, velocidad=0.0,
            dispersion=0.15, tamano=tamano,
            color=color if color is not None else actor.color,
            ciclico=True)

        def seguir():
            if not actor.esta_en_escena():
                emisor.eliminar()
                return False
            emisor.posicion = actor.posicion
            return True

        self.pilas.tareas.condicional(0, seguir)
        return emisor

    # -- cámara y tiempo ---------------------------------------------------

    def temblar_pantalla(self, intensidad=0.4, duracion=0.5):
        """Shake de cámara (explosión, golpe fuerte): decae solo y
        no deja la cámara desplazada."""
        self.pilas.escena.camara.temblor(intensidad, duracion)

    def hit_stop(self, duracion=0.08, escala=0.05):
        """Micro-pausa de impacto: el mundo corre a ``escala`` del
        tiempo durante ``duracion`` segundos reales — el golpe
        "pega". No afecta al reloj de pared, solo al dt del juego."""
        self._escala = escala
        self._escala_hasta = time.time() + duracion

    def tiempo_escala(self):
        """Multiplicador de dt vigente (1.0 = normal); el bucle de
        juego lo aplica para ``hit_stop``."""
        if time.time() < self._escala_hasta:
            return self._escala
        return 1.0

    # -- color -----------------------------------------------------------

    def flash(self, actor, color=None, duracion=0.15):
        """Tinte instantáneo: pinta al actor de ``color`` por
        ``duracion`` segundos (daño recibido, cura, power-up)."""
        color = color if color is not None else \
            self.pilas.colores.rojo
        orig = actor.color
        actor.color = color

        def restaurar():
            if actor.esta_en_escena():
                actor.color = orig

        return self.pilas.tareas.una_vez(duracion, restaurar)
