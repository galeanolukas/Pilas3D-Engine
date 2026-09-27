# -*- encoding: utf-8 -*-

from pilas3d.habilidades.habilidad import Habilidad


class AumentarConRueda(Habilidad):
    """Cambia la escala del actor con la rueda del mouse.

    >>> cubo.aprender(pilas.habilidades.AumentarConRueda)
    """

    def iniciar(self, receptor, factor=1.1, escala_minima=0.05):
        super(AumentarConRueda, self).iniciar(receptor)
        self.factor = factor
        self.escala_minima = escala_minima
        ventana = self.pilas.ventana
        if ventana is not None:
            ventana.push_handlers(
                on_mouse_scroll=self._on_mouse_scroll)

    def _on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        r = self.receptor
        if scroll_y > 0:
            r.escala = r.escala * self.factor
        else:
            r.escala = max(self.escala_minima,
                           r.escala / self.factor)
