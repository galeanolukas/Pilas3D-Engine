# -*- encoding: utf-8 -*-

import pilas3d
from pilas3d.habilidades.habilidad import Habilidad


class PuedeExplotar(Habilidad):
    """El actor puede explotar: genera la animación de explosión
    y se elimina.

    >>> enemigo.aprender(pilas.habilidades.PuedeExplotar)
    >>> enemigo.habilidades.PuedeExplotar.explotar()
    """

    def explotar(self, escala=2.0):
        r = self.receptor
        boom = self.pilas.actores.Animacion(
            pilas3d.obtener_ruta('data/explosion.png'),
            columnas=7, velocidad=14, ciclica=False,
            eliminar_al_terminar=True)
        boom.x, boom.y, boom.z = r.x, r.y, r.z
        boom.escala = escala
        r.eliminar()
