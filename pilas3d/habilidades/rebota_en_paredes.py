# -*- encoding: utf-8 -*-
"""RebotaEnParedes: el actor viaja y rebota dentro de un rectángulo.

    >>> bola.aprender(pilas.habilidades.RebotaEnParedes,
    ...               vx=3, vz=4, limites=(-8, 8, -8, 8))

``limites`` es ``(x_min, x_max, z_min, z_max)`` — al tocar un borde
invierte la velocidad de ese eje. Opcionalmente ``paredes`` es una
lista de actores: al colisionar con alguna en el plano XZ invierte
la marcha (rebote completo).
"""

import math

from pilas3d.habilidades.habilidad import Habilidad


class RebotaEnParedes(Habilidad):
    """Rebote estilo "logo de DVD" dentro de límites."""

    def iniciar(self, receptor, vx=3.0, vz=4.0,
                limites=(-8.0, 8.0, -8.0, 8.0), paredes=None):
        super(RebotaEnParedes, self).iniciar(receptor)
        receptor.vel_x_rebote = vx
        receptor.vel_z_rebote = vz
        #: (x_min, x_max, z_min, z_max)
        receptor.limites_rebote = limites
        receptor.paredes_rebote = paredes

    def actualizar(self):
        r = self.receptor
        dt = self.pilas.dt
        r.x += r.vel_x_rebote * dt
        r.z += r.vel_z_rebote * dt

        min_x, max_x, min_z, max_z = r.limites_rebote
        if r.x < min_x:
            r.x = min_x
            r.vel_x_rebote = abs(r.vel_x_rebote)
        elif r.x > max_x:
            r.x = max_x
            r.vel_x_rebote = -abs(r.vel_x_rebote)
        if r.z < min_z:
            r.z = min_z
            r.vel_z_rebote = abs(r.vel_z_rebote)
        elif r.z > max_z:
            r.z = max_z
            r.vel_z_rebote = -abs(r.vel_z_rebote)

        for p in r.paredes_rebote or ():
            if (p.esta_en_escena() and p is not r
                    and r.colisiona_en_plano_con(p)):
                r.vel_x_rebote = -r.vel_x_rebote
                r.vel_z_rebote = -r.vel_z_rebote
                break

        r.rotacion_y = -math.degrees(
            math.atan2(r.vel_x_rebote, r.vel_z_rebote))
