# -*- encoding: utf-8 -*-
"""SerBot: convierte a cualquier actor en un NPC con comportamiento.

A diferencia de ``pilas.actores.Bot`` (que ya trae un cuerpo), esta
habilidad se le puede enseñar a CUALQUIER actor — un personaje
predefinido, uno creado heredando de ``Actor``, un modelo, lo que sea::

    mono = pilas.actores.Mono(x=5, z=5)
    mono.aprender(pilas.habilidades.SerBot,
                  mundo=mundo, objetivo=jugador,
                  radio_vision=8, radio_patron=10)
    mono.estado        # 'patrullar' | 'perseguir' | 'volver'
    mono.objetivo      # a quién persigue (cambiable en caliente)

El bot patrulla a puntos al azar alrededor de ``casa`` (por defecto
donde aprendió la habilidad), corre hacia ``objetivo`` si entra en
``radio_vision``, y vuelve a casa cuando lo pierde. Con ``mundo``
(un Mundo voxel) camina sobre el terreno.
"""

import math
import random

from pilas3d.habilidades.habilidad import Habilidad


class SerBot(Habilidad):

    def iniciar(self, receptor, casa=None, radio_patron=8,
                velocidad=2.0, radio_vision=8, mundo=None,
                objetivo=None, espera_min=0.5, espera_max=2.0):
        super(SerBot, self).iniciar(receptor)
        r = receptor
        r.casa = casa or (r.x, r.z)
        r.radio_patron = radio_patron
        r.velocidad = velocidad
        r.radio_vision = radio_vision
        r.mundo = mundo
        r.objetivo = objetivo
        r.estado = 'patrullar'
        r._destino_bot = None
        r._espera_bot = 0.0
        self._espera_min = espera_min
        self._espera_max = espera_max

    def _elegir_destino(self, r):
        a = random.uniform(0, math.pi * 2)
        d = random.uniform(1, r.radio_patron)
        r._destino_bot = (r.casa[0] + math.cos(a) * d,
                          r.casa[1] + math.sin(a) * d)
        r._espera_bot = random.uniform(self._espera_min,
                                       self._espera_max)

    def _caminar_hacia(self, r, tx, tz, dt, rapido=False):
        dx, dz = tx - r.x, tz - r.z
        dist = math.hypot(dx, dz)
        # primero orientar: si ya llegó (o está pegado al objetivo)
        # igual debe quedar mirándolo, no congelado en la última
        # dirección de marcha
        r.mirar_hacia(tx, tz)
        if dist < 0.15:
            return True
        v = r.velocidad * (1.6 if rapido else 1.0)
        paso = min(v * dt, dist)
        r.x += dx / dist * paso
        r.z += dz / dist * paso
        if r.mundo is not None:
            suelo = r.mundo.altura_suelo(r.x, r.z)
            if suelo is not None:
                r.y = suelo + 0.8
        return False

    def actualizar(self):
        r = self.receptor
        dt = self.pilas.dt
        obj = r.objetivo
        d = None
        if obj is not None and obj.esta_en_escena():
            d = math.hypot(obj.x - r.x, obj.z - r.z)

        if d is not None and d <= r.radio_vision:
            r.estado = 'perseguir'
        elif r.estado == 'perseguir':
            r.estado = 'volver'
        elif r.estado == 'volver' and \
                math.hypot(r.casa[0] - r.x, r.casa[1] - r.z) < 1:
            r.estado = 'patrullar'

        if r.estado == 'perseguir':
            self._caminar_hacia(r, obj.x, obj.z, dt, rapido=True)
        elif r.estado == 'volver':
            if self._caminar_hacia(r, r.casa[0], r.casa[1], dt):
                r.estado = 'patrullar'
        else:   # patrullar
            if r._destino_bot is None:
                self._elegir_destino(r)
            if r._espera_bot > 0:
                r._espera_bot -= dt
            elif self._caminar_hacia(r, r._destino_bot[0],
                                     r._destino_bot[1], dt):
                r._destino_bot = None
