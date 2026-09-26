# -*- encoding: utf-8 -*-
"""Sonidos: efectos de audio cortos, como ``pilasengine.sonidos``.

Uso::

    sonido = pilas.sonidos.cargar('explosion.wav')
    sonido.reproducir()
    sonido.reproducir(repetir=True)   # en bucle
    sonido.detener()

La ruta se busca en el directorio actual y luego en ``pilas3d/data/``.
Si no hay placa de audio (o se llamó a ``pilas.sonidos.deshabilitar()``)
se retorna un ``SonidoDeshabilitado`` con la misma API que no hace nada.
"""

import os

from pyglet import media


def _resolver_ruta(ruta):
    """Busca el archivo en cwd, en ``data/`` y en el paquete."""
    base = os.path.dirname(__file__)
    for candidato in (ruta,
                      os.path.join(base, 'data', ruta),
                      os.path.join(base, ruta)):
        if os.path.exists(candidato):
            return candidato
    raise IOError("No se encuentra el archivo de audio '%s'" % ruta)


def _hay_audio():
    try:
        from pyglet.media.drivers import get_audio_driver
        return get_audio_driver() is not None
    except Exception:
        return False


class Sonido(object):
    """Un efecto de sonido cargado desde un archivo WAV/OGG."""

    deshabilitado = False

    def __init__(self, pilas, ruta):
        self._pilas = pilas
        self.ruta = ruta
        self._volumen = 1.0
        self._fuente = media.load(ruta, streaming=False)
        self._jugador_bucle = None
        self._jugadores = []

    @property
    def volumen(self):
        return self._volumen

    @volumen.setter
    def volumen(self, valor):
        self._volumen = valor
        for jugador in [self._jugador_bucle] + self._jugadores:
            if jugador is not None:
                jugador.volume = valor

    def reproducir(self, repetir=False):
        """Reproduce el sonido; con ``repetir=True`` queda en bucle."""
        if Sonido.deshabilitado:
            return
        jugador = media.Player()
        jugador.queue(self._fuente)
        jugador.volume = self._volumen
        if repetir:
            self.detener()
            jugador.loop = True
            self._jugador_bucle = jugador
        else:
            self._jugadores = [j for j in self._jugadores if j.playing]
            self._jugadores.append(jugador)
        jugador.play()

    def detener(self):
        if self._jugador_bucle is not None:
            self._jugador_bucle.delete()
            self._jugador_bucle = None
        for jugador in self._jugadores:
            jugador.delete()
        self._jugadores = []

    def pausar(self):
        if self._jugador_bucle is not None:
            self._jugador_bucle.pause()

    def continuar(self):
        if self._jugador_bucle is not None:
            self._jugador_bucle.play()

    def detener_gradualmente(self, segundos=2):
        """Baja el volumen de a poco hasta detener el sonido."""
        if self._jugador_bucle is None:
            return
        pasos = max(int(segundos * 20), 1)
        jugador = self._jugador_bucle
        estado = {'restantes': pasos}

        def bajar():
            estado['restantes'] -= 1
            jugador.volume = self._volumen * estado['restantes'] / pasos
            if estado['restantes'] <= 0:
                jugador.delete()
                if self._jugador_bucle is jugador:
                    self._jugador_bucle = None
                return False
            return True

        try:
            self._pilas.tareas.condicional(0.05, bajar)
        except Exception:
            self.detener()

    def __repr__(self):
        nombre = os.path.basename(self.ruta)
        if Sonido.deshabilitado:
            return "<Sonido deshabilitado del archivo '%s'>" % nombre
        return "<Sonido del archivo '%s'>" % nombre


class SonidoDeshabilitado(object):
    """Sonido nulo: misma API que ``Sonido`` pero sin efecto."""

    def __init__(self, ruta):
        self.ruta = ruta

    def reproducir(self, repetir=False):
        pass

    def detener(self):
        pass

    def pausar(self):
        pass

    def continuar(self):
        pass

    def detener_gradualmente(self, segundos=2):
        pass

    @property
    def volumen(self):
        return 1.0

    @volumen.setter
    def volumen(self, valor):
        pass

    def __repr__(self):
        nombre = os.path.basename(self.ruta)
        return "<SonidoDeshabilitado del archivo '%s'>" % nombre


class Sonidos(object):
    """Punto de acceso a los sonidos: ``pilas.sonidos.cargar(...)``."""

    def __init__(self, pilas):
        self._pilas = pilas

    def cargar(self, ruta):
        """Carga un sonido. Ver ``pilas3d.sonidos`` para ejemplos."""
        ruta = _resolver_ruta(ruta)
        if Sonido.deshabilitado or not _hay_audio():
            return SonidoDeshabilitado(ruta)
        return Sonido(self._pilas, ruta)

    def habilitar(self):
        Sonido.deshabilitado = False

    def deshabilitar(self):
        Sonido.deshabilitado = True
