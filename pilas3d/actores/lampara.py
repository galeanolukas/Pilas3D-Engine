# -*- encoding: utf-8 -*-
"""Lámpara: un actor que ilumina — une ``LuzPuntual`` con el mundo.

A diferencia de agregar una ``LuzPuntual`` a mano, la ``Lampara`` es
un actor común: se mueve, interpola, aprende habilidades, responde a
``lampara.x += 1`` y la luz lo sigue. El foco se dibuja a color plano
(``sin_luz``) para que se vea brillante.

>>> lampara = pilas.actores.Lampara(x=2, y=3, z=0, alcance=10)
>>> lampara.color = pilas.colores.naranja    # tiñe la luz también
>>> lampara.encendida = False                # se apaga sin destruirla
>>> lampara.eliminar()                       # la luz se va con ella
"""

from pilas3d import colores, mallas
from pilas3d.actores.actor import Actor
from pilas3d.luces import LuzPuntual


class Lampara(Actor):
    """Foco visible + luz puntual que lo acompaña."""

    def __init__(self, pilas, x=0, y=2, z=0, color=None, alcance=8.0,
                 visible=True):
        super(Lampara, self).__init__(pilas, x=x, y=y, z=z)
        self.sin_luz = True
        self.radio_de_colision = 0.2
        #: La ``LuzPuntual`` que ilumina (por si querés tunearla).
        self.luz = LuzPuntual(x=x, y=y, z=z,
                              color=(1.0, 0.9, 0.7), alcance=alcance)
        if color is not None:
            self.color = color
        else:
            self.color = (1.0, 0.9, 0.7)
        if not visible:
            self.transparencia = 100      # luz invisible: solo alumbra
        escena = pilas.escena_actual()
        if escena is not None:
            escena.luces.agregar(self.luz)

    def _generar_geometria(self):
        return mallas.esfera(0.15)

    # -- la luz refleja al actor -------------------------------------------

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, valor):
        Actor.color.fset(self, valor)
        if hasattr(self, 'luz'):
            self.luz.color = colores.normalizar(valor)

    @property
    def alcance(self):
        """Qué tan lejos llega la luz, en metros."""
        return self.luz.alcance

    @alcance.setter
    def alcance(self, valor):
        self.luz.alcance = valor

    @property
    def encendida(self):
        escena = self.pilas.escena_actual()
        return escena is not None and self.luz in escena.luces.puntuales

    @encendida.setter
    def encendida(self, valor):
        if valor:
            self.encender()
        else:
            self.apagar()

    def encender(self):
        luces = self.pilas.escena_actual().luces
        if self.luz not in luces.puntuales:
            luces.agregar(self.luz)

    def apagar(self):
        self.pilas.escena_actual().luces.quitar(self.luz)

    def actualizar(self):
        self.luz.x, self.luz.y, self.luz.z = self.x, self.y, self.z

    def terminar(self):
        escena = self.pilas.escena_actual()
        if escena is not None:
            escena.luces.quitar(self.luz)
