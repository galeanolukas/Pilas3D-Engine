# -*- encoding: utf-8 -*-
"""Globo: bocadillo de diálogo que flota sobre un actor.

Como ``pilas.actores.Globo`` de pilas 1.x: un cartelito 2D con texto
que sigue a un actor del mundo proyectando su posición a pantalla.
Sirve para NPCs que hablan, nombres sobre personajes, pistas, etc.::

    npc = pilas.actores.Mono(x=2)
    globo = pilas.actores.Globo(npc, 'hola!')

    globo.texto = '¿cómo andás?'     # cambia el texto
    globo.actor = otro_actor         # se puede reconectar
    globo.alto = 2.5                 # altura sobre los pies (mundo)
    globo.duracion = 3.0             # se oculta solo tras N seg

Si el actor sale de pantalla o queda detrás de la cámara el globo
se oculta solo. ``x``/``y`` en píxeles solo aplican cuando
``actor`` es None (posición fija).
"""

from pyglet.gl import GL_TRIANGLES

from pilas3d import colores
from pilas3d.actores.actor import Actor


class Globo(Actor):
    """Bocadillo 2D (borde + relleno + pico + texto) overlay."""

    es_overlay = True

    def __init__(self, pilas, actor=None, texto='', x=0, y=0,
                 alto=2.2, tamano=14, duracion=0.0):
        #: Actor al que sigue (None = posición fija en x, y).
        self.actor = actor
        #: Metros sobre los pies del actor donde flota el globo.
        self.alto = alto
        self.tamano = tamano
        #: Segundos que permanece visible tras ``decir`` (0 = siempre).
        self.duracion = duracion
        self._texto = texto
        self._visible = bool(texto)
        self._restante = 0.0
        self._label = None
        self._fondo = None
        self._borde = None
        self._pico = None
        super(Globo, self).__init__(pilas, x=x, y=y, z=0)
        self.radio_de_colision = 0.0

    @property
    def texto(self):
        return self._texto

    @texto.setter
    def texto(self, valor):
        self._texto = valor
        self._visible = bool(valor)

    def decir(self, texto, duracion=None):
        """Muestra ``texto``; si hay duración se oculta solo."""
        self.texto = texto
        if duracion is not None:
            self.duracion = duracion
        self._restante = self.duracion

    def _generar_geometria(self):
        return [], [], GL_TRIANGLES, None, None

    def actualizar(self):
        if self.actor is not None:
            camara = self.pilas.escena_actual().camara
            ax, ay, az = self.actor.posicion
            punto = camara.proyectar(ax, ay + self.alto, az)
            self._visible = bool(self._texto) and punto is not None
            if punto is not None:
                self._x, self._y = punto
        if self._restante > 0:
            self._restante -= self.pilas.dt
            if self._restante <= 0:
                self._texto = ''
                self._visible = False

    def dibujar(self):
        if not self._visible or not self._texto:
            return
        if self._label is None:
            from pyglet.text import Label
            from pyglet.shapes import Rectangle, Triangle
            self._label = Label('', font_size=self.tamano,
                                anchor_x='center', anchor_y='baseline')
            self._fondo = Rectangle(0, 0, 1, 1, color=(255, 255, 255))
            self._borde = Rectangle(0, 0, 1, 1, color=(30, 30, 30))
            self._pico = Triangle(0, 0, 0, 0, 0, 0, color=(255, 255, 255))

        self._label.text = self._texto
        self._label.font_size = self.tamano
        ancho = self._label.content_width + 20
        alto = self._label.content_height + 14
        cx, cy = self._x, self._y + 14   # el pico ocupa 14px abajo

        # borde (un poco más grande, detrás del fondo blanco)
        self._borde.x = cx - ancho / 2 - 1
        self._borde.y = cy - 1
        self._borde.width = ancho + 2
        self._borde.height = alto + 2
        self._borde.draw()
        self._fondo.x = cx - ancho / 2
        self._fondo.y = cy
        self._fondo.width = ancho
        self._fondo.height = alto
        self._fondo.draw()

        # piquito apuntando al actor
        self._pico.x = cx - 7
        self._pico.y = cy
        self._pico.x2 = cx + 7
        self._pico.y2 = cy
        self._pico.x3 = cx
        self._pico.y3 = cy - 14
        self._pico.draw()

        self._label.x = cx
        self._label.y = cy + 6
        r, g, b = colores.normalizar(colores.negro)
        self._label.color = (r, g, b, 255)
        self._label.draw()

    def eliminar(self):
        self.actor = None
        self._label = self._fondo = self._borde = self._pico = None
        super(Globo, self).eliminar()
