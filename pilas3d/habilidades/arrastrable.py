# -*- encoding: utf-8 -*-
"""Arrastrable: arrastrar el actor con el mouse sobre un plano.

Versión 3D de ``pilasengine.habilidades.Arrastrable``: al hacer click
sobre el actor y mantener el botón, el actor sigue al puntero sobre
el plano horizontal de su propia altura (o el ``y_plano`` indicado).
"""

from pilas3d.habilidades.habilidad import Habilidad


class Arrastrable(Habilidad):
    """El actor se puede arrastrar con el mouse.

    >>> cubo.aprender(pilas.habilidades.Arrastrable)
    >>> cubo.aprender(pilas.habilidades.Arrastrable, y_plano=0)
    """

    def iniciar(self, receptor, y_plano=None):
        super(Arrastrable, self).iniciar(receptor)
        self.y_plano = y_plano
        self._arrastrando = False
        self._boton_prev = False

    def actualizar(self):
        presionado = self.pilas.control.boton_izquierdo
        plano = (self.receptor.y if self.y_plano is None
                 else self.y_plano)
        camara = self.pilas.escena.camara

        if presionado and not self._boton_prev:
            # el click cayó sobre el actor?
            actor = camara.actor_bajo_mouse()
            self._arrastrando = actor is self.receptor
        elif not presionado:
            self._arrastrando = False

        if self._arrastrando:
            punto = camara.punto_bajo_mouse(plano)
            if punto is not None:
                self.receptor.x = punto[0]
                self.receptor.z = punto[2]

        self._boton_prev = presionado
