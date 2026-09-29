# -*- encoding: utf-8 -*-
"""Vida: puntos de salud para cualquier actor.

    >>> enemigo.aprender(pilas.habilidades.Vida, vida=100)
    >>> enemigo.recibir_dano(30)
    >>> enemigo.curar(10)
    >>> enemigo.vida, enemigo.vivo
    (80, True)

Al llegar a cero: ``enemigo.vivo`` pasa a False, se emite el evento
``'murio'`` por ``pilas.eventos`` (con el actor como argumento) y se
invoca ``enemigo.al_morir()`` si existe — el juego decide si
eliminarlo, reiniciarlo, sumar puntos, etc.
"""

from pilas3d.habilidades.habilidad import Habilidad


class Vida(Habilidad):
    """Agrega ``vida``, ``recibir_dano``, ``curar`` y el estado vivo."""

    def iniciar(self, receptor, vida=100):
        super(Vida, self).iniciar(receptor)
        receptor.vida_maxima = vida
        receptor.vida = vida
        receptor.vivo = True
        receptor.recibir_dano = self._recibir_dano
        receptor.curar = self._curar

    def _recibir_dano(self, cantidad):
        r = self.receptor
        if not r.vivo:
            return
        r.vida = max(0.0, r.vida - cantidad)
        if r.vida <= 0:
            r.vivo = False
            self.pilas.eventos.emitir('murio', r)
            al_morir = getattr(r, 'al_morir', None)
            if callable(al_morir):
                al_morir()

    def _curar(self, cantidad):
        r = self.receptor
        if r.vivo:
            r.vida = min(r.vida_maxima, r.vida + cantidad)
