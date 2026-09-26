# -*- encoding: utf-8 -*-
"""Música de fondo, como ``pilasengine.musica``.

A diferencia de ``pilas.sonidos`` (efectos cortos), la música se
reproduce en streaming y por defecto en bucle::

    musica = pilas.musica.cargar('rayman.ogg')
    musica.reproducir()
    musica.volumen = 0.5
    musica.detener_gradualmente(3)
"""

import os

from pyglet import media

from pilas3d.sonidos import _resolver_ruta, _hay_audio


class Musica(object):
    """Una pista de música en streaming con un único reproductor."""

    deshabilitado = False

    def __init__(self, pilas, ruta):
        self._pilas = pilas
        self.ruta = ruta
        self._volumen = 1.0
        self._fuente = media.load(ruta, streaming=True)
        self._jugador = None

    @property
    def volumen(self):
        return self._volumen

    @volumen.setter
    def volumen(self, valor):
        self._volumen = valor
        if self._jugador is not None:
            self._jugador.volume = valor

    def reproducir(self, repetir=True):
        """Reproduce la pista; por defecto queda en bucle."""
        if Musica.deshabilitado:
            return
        self.detener()
        self._jugador = media.Player()
        self._jugador.queue(self._fuente)
        self._jugador.loop = repetir
        self._jugador.volume = self._volumen
        self._jugador.play()

    def detener(self):
        if self._jugador is not None:
            self._jugador.delete()
            self._jugador = None

    def pausar(self):
        if self._jugador is not None:
            self._jugador.pause()

    def continuar(self):
        if self._jugador is not None:
            self._jugador.play()

    def detener_gradualmente(self, segundos=2):
        if self._jugador is None:
            return
        pasos = max(int(segundos * 20), 1)
        jugador = self._jugador
        estado = {'restantes': pasos}

        def bajar():
            estado['restantes'] -= 1
            jugador.volume = self._volumen * estado['restantes'] / pasos
            if estado['restantes'] <= 0:
                jugador.delete()
                if self._jugador is jugador:
                    self._jugador = None
                return False
            return True

        try:
            self._pilas.tareas.condicional(0.05, bajar)
        except Exception:
            self.detener()

    def __repr__(self):
        nombre = os.path.basename(self.ruta)
        if Musica.deshabilitado:
            return "<Musica deshabilitada del archivo '%s'>" % nombre
        return "<Musica del archivo '%s'>" % nombre


class MusicaDeshabilitada(object):
    """Música nula: misma API que ``Musica`` pero sin efecto."""

    def __init__(self, ruta):
        self.ruta = ruta

    def reproducir(self, repetir=True):
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
        return "<MusicaDeshabilitada del archivo '%s'>" % nombre


class _Musica(object):
    """Punto de acceso a la música: ``pilas.musica.cargar(...)``."""

    def __init__(self, pilas):
        self._pilas = pilas

    def cargar(self, ruta):
        ruta = _resolver_ruta(ruta)
        if Musica.deshabilitado or not _hay_audio():
            return MusicaDeshabilitada(ruta)
        return Musica(self._pilas, ruta)

    def habilitar(self):
        Musica.deshabilitado = False

    def deshabilitar(self):
        Musica.deshabilitado = True
