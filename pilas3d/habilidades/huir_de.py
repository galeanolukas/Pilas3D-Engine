# -*- encoding: utf-8 -*-
"""HuirDe: se aleja de un actor cuando se acerca.

    >>> presa.aprender(pilas.habilidades.HuirDe, jugador,
    ...                radio=5, velocidad=3)

Si el objetivo entra a ``radio`` metros la presa corre en dirección
contraria; si está lejos no hace nada. Complemento natural de
``PerseguirAOtroActor`` — del mismo modo que ``SeguirAlActor`` tiene
a ``HuirDe`` como inversa.
"""

import math

from pilas3d.habilidades.habilidad import Habilidad


class HuirDe(Habilidad):
    """Escapa del objetivo mientras esté dentro del radio."""

    def iniciar(self, receptor, objetivo, radio=5.0, velocidad=2.5):
        super(HuirDe, self).iniciar(receptor)
        #: El actor del que huye.
        receptor.objetivo = objetivo
        #: Distancia a la que empieza a escapar.
        receptor.radio_huida = radio
        #: Metros por segundo al escapar.
        receptor.velocidad_huida = velocidad

    def actualizar(self):
        r = self.receptor
        o = r.objetivo
        if o is None or not o.esta_en_escena():
            return
        dx, dz = r.x - o.x, r.z - o.z
        dist = math.hypot(dx, dz)
        if dist >= r.radio_huida or dist < 0.01:
            return
        paso = r.velocidad_huida * self.pilas.dt
        r.x += dx / dist * paso
        r.z += dz / dist * paso
        r.rotacion_y = -math.degrees(math.atan2(dx, dz))
