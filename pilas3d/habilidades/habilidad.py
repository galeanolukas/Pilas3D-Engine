# -*- encoding: utf-8 -*-
"""Habilidad base: comportamiento reutilizable que un actor aprende.

Port de ``pilasengine.habilidades.habilidad.Habilidad``.
"""


class Habilidad(object):
    def __init__(self, pilas):
        self.pilas = pilas
        self.receptor = None

    def iniciar(self, receptor):
        """Se llama una vez cuando el actor aprende la habilidad."""
        self.receptor = receptor

    def actualizar(self):
        """Se llama ~60 veces por segundo, antes del actualizar del actor."""
        pass

    def eliminar(self):
        self.receptor.eliminar_habilidad(self.__class__)

    def __repr__(self):
        return '<Habilidad: {0}>'.format(self.__class__.__name__)
