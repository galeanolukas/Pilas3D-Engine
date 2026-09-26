# -*- encoding: utf-8 -*-
"""Interpolaciones para animar propiedades de los actores.

Port del concepto de ``pilasengine.utils.interpolaciones`` (que usaba
pytweener). Dos formas de uso::

    actor.x = [100]                          # va a 100 en 1 segundo
    actor.x = [100, -50, 0]                  # pasa por los 3 valores
    actor.x = ([100, -50], 3)                # con duración de 3s
    actor.escala = pilas.interpolaciones.ReboteFinal([2], duracion=2)
    pilas.interpolar(actor, 'rotacion', 360, duracion=3)
"""

import math


def _rebote_out(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def _rebote_in(t):
    return 1.0 - _rebote_out(1.0 - t)


def _elastico_in(t):
    if t in (0.0, 1.0):
        return t
    c5 = 2 * math.pi / 4.5
    return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c5)


def _elastico_out(t):
    if t in (0.0, 1.0):
        return t
    c4 = 2 * math.pi / 3.0
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


class _Tween(object):
    """Una interpolación en curso sobre un atributo de un actor."""

    def __init__(self, actor, atributo, interpolacion):
        self.actor = actor
        self.atributo = atributo
        self.valores = interpolacion.valores
        self.duracion = max(interpolacion.duracion, 0.0001)
        self.easing = interpolacion.easing
        self.t = -interpolacion.demora
        self.indice = 0
        self.desde = float(getattr(actor, atributo))

    def avanzar(self, dt):
        """Retorna True cuando la interpolación terminó."""
        self.t += dt
        if self.t < 0:
            return False
        n = len(self.valores)
        paso = self.duracion / n
        indice = min(int(self.t / paso), n - 1)
        if indice != self.indice:
            self.desde = self.valores[self.indice]
            self.indice = indice
        local = min((self.t - indice * paso) / paso, 1.0)
        destino = float(self.valores[indice])
        valor = self.desde + (destino - self.desde) * self.easing(local)
        setattr(self.actor, self.atributo, valor)
        return self.t >= self.duracion


class Interpolacion(object):
    """Base de las interpolaciones; cada subclase define su easing.

    ``valores`` es la lista de puntos por los que pasa la propiedad,
    ``duracion`` los segundos totales y ``demora`` segundos de espera
    antes de arrancar.
    """

    easing = staticmethod(lambda t: t)

    def __init__(self, valores, duracion=1.0, demora=0.0):
        if not isinstance(valores, (list, tuple)):
            valores = [valores]
        self.valores = list(valores)
        self.duracion = duracion
        self.demora = demora

    def iniciar(self, actor, atributo):
        """Engancha la interpolación al atributo del actor."""
        # una interpolación nueva sobre el mismo atributo pisa a la vieja
        actor._interpolaciones = [
            t for t in actor._interpolaciones if t.atributo != atributo]
        actor._interpolaciones.append(_Tween(actor, atributo, self))

    def __neg__(self):
        """La interpolación inversa (los valores en orden contrario)."""
        return self.__class__(list(reversed(self.valores)),
                              self.duracion, self.demora)


class Lineal(Interpolacion):
    """Velocidad constante."""
    pass


class AceleracionGradual(Interpolacion):
    """Arranca despacio y acelera (ease-in cúbico)."""
    easing = staticmethod(lambda t: t * t * t)


class DesaceleracionGradual(Interpolacion):
    """Arranca rápido y frena suave (ease-out cúbico)."""
    easing = staticmethod(lambda t: 1 - (1 - t) ** 3)


class ReboteInicial(Interpolacion):
    """Rebota al principio."""
    easing = staticmethod(_rebote_in)


class ReboteFinal(Interpolacion):
    """Rebota al llegar al final."""
    easing = staticmethod(_rebote_out)


class ElasticoInicial(Interpolacion):
    """Oscila como un resorte al principio."""
    easing = staticmethod(_elastico_in)


class ElasticoFinal(Interpolacion):
    """Oscila como un resorte al final."""
    easing = staticmethod(_elastico_out)
