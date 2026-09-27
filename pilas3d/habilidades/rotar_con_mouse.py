# -*- encoding: utf-8 -*-

from pyglet.window import mouse

from pilas3d.habilidades.habilidad import Habilidad


class RotarConMouse(Habilidad):
    """Gira al actor arrastrando con el botón izquierdo del mouse.

    >>> cubo.aprender(pilas.habilidades.RotarConMouse)
    """

    def iniciar(self, receptor, sensibilidad=0.5):
        super(RotarConMouse, self).iniciar(receptor)
        self.sensibilidad = sensibilidad
        ventana = self.pilas.ventana
        if ventana is not None:
            ventana.push_handlers(on_mouse_drag=self._on_mouse_drag)

    def _on_mouse_drag(self, x, y, dx, dy, botones, modificadores):
        if botones & mouse.LEFT:
            self.receptor.rotacion_y += dx * self.sensibilidad
            self.receptor.rotacion_x += dy * self.sensibilidad
