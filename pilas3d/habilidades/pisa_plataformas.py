# -*- encoding: utf-8 -*-

from pyglet.window import key

from pilas3d.habilidades.habilidad import Habilidad


class PisaPlataformas(Habilidad):
    """Gravedad que aterriza sobre plataformas, no solo en y=0.

    El actor cae hasta pisar la cara superior de una plataforma —
    cualquier ``Pared`` (o actor con ``obtener_caja``), cubo o esfera.
    Sin lista explícita usa ``escena.obstaculos``.

    >>> cubo.aprender(pilas.habilidades.PisaPlataformas,
    ...               plataformas=[p1, p2], salto=9)

    Con ``salto`` > 0, SPACE salta cuando está apoyado.
    """

    def iniciar(self, receptor, plataformas=None, gravedad=25.0,
                salto=0.0):
        super(PisaPlataformas, self).iniciar(receptor)
        self.plataformas = plataformas
        self.gravedad = gravedad
        self.salto = salto
        self.vel_y = 0.0
        self.en_suelo = True
        self.plataforma_actual = None

    # -- geometría de apoyo -------------------------------------------------

    def _lista(self):
        if self.plataformas is not None:
            escena = self.pilas.escena_actual()
            return [p for p in self.plataformas if p in escena.actores]
        return self.pilas.escena_actual().obstaculos

    def _techo(self, p):
        """Y de la cara superior de la plataforma."""
        if hasattr(p, 'alto'):
            return p.y + p.alto * p.escala_y / 2.0
        if hasattr(p, 'radio'):
            return p.y + p.radio * p.escala_y
        return p.y + 0.5 * p.escala_y

    def _caja(self, p):
        """Huella XZ de la plataforma (min_x, max_x, min_z, max_z)."""
        if hasattr(p, 'obtener_caja'):
            return p.obtener_caja()
        from pilas3d import colisiones
        ancho = getattr(p, 'ancho', p.radio_de_colision)
        prof = getattr(p, 'profundidad', ancho)
        return colisiones.caja_desde_actor(
            p, ancho * p.escala_x, prof * p.escala_z)

    def _mitad(self):
        """Media altura del receptor (del centro a los pies)."""
        r = self.receptor
        if hasattr(r, 'alto'):
            return r.alto * r.escala_y / 2.0
        if hasattr(r, 'radio'):
            return r.radio * r.escala_y
        return 0.5 * r.escala_y

    def _suelo_en(self, x, z, pies):
        """Mayor techo de plataforma bajo el actor (solo si puede
        pisarlo: los pies ya están a su altura o por encima)."""
        mejor = 0.0
        elegida = None
        for p in self._lista():
            min_x, max_x, min_z, max_z = self._caja(p)
            if not (min_x <= x <= max_x and min_z <= z <= max_z):
                continue
            techo = self._techo(p)
            if techo <= pies + 0.4 and techo > mejor:
                mejor = techo
                elegida = p
        return mejor, elegida

    # -- física -------------------------------------------------------------

    def actualizar(self):
        r = self.receptor
        dt = self.pilas.dt

        self.vel_y -= self.gravedad * dt
        r.y += self.vel_y * dt

        mitad = self._mitad()
        suelo, plataforma = self._suelo_en(
            r.x, r.z, r.y - mitad)
        if r.y <= suelo + mitad:
            r.y = suelo + mitad
            self.vel_y = 0.0
            self.en_suelo = True
            self.plataforma_actual = plataforma
        else:
            self.en_suelo = False
            self.plataforma_actual = None

        if (self.salto and self.en_suelo
                and self.pilas.control.simbolo(key.SPACE)):
            self.vel_y = self.salto
