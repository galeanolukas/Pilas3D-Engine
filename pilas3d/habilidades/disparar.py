# -*- encoding: utf-8 -*-
"""Disparar: el actor puede lanzar proyectiles.

Port de ``pilasengine.habilidades.Disparar`` a 3D::

    nave.aprender(pilas.habilidades.Disparar,
                  objetivos=enemigos, cuando_impacta=al_pegar)
    nave.disparar()                  # sale un Proyectil

Al aprenderla, el actor gana los métodos ``disparar()``, ``puede_
disparar()`` y el atributo ``cadencia``. Con ``con_click=True``
dispara solo cuando se aprieta el botón izquierdo del mouse.
"""

import math

from pilas3d.habilidades.habilidad import Habilidad


class Disparar(Habilidad):
    """El actor aprende a disparar proyectiles.

    Parámetros de ``iniciar`` (vía ``aprender``):

    - ``proyectil``: clase del disparo (default ``Proyectil``).
    - ``velocidad``/``alcance``: se pasan al proyectil.
    - ``cadencia``: segundos mínimos entre disparos.
    - ``offset``: punto de salida relativo al actor (se rota con
      ``rotacion_y``, así ``(0, 0.5, 0.6)`` es "delante y arriba").
    - ``hacia``: dirección fija ``(x, y, z)``; None = hacia donde
      mira el actor (su ``rotacion_y``).
    - ``desde_camara``: sale de la cámara apuntando adelante (FPS).
    - ``objetivos``: lista de actores que el proyectil puede pegar.
    - ``cuando_impacta``: ``fn(proyectil, actor)`` al pegar.
    - ``cuando_dispara``: ``fn()`` cada vez que sale un proyectil.
    - ``con_click``: dispara solo al apretar el botón izquierdo.
    - ``tecla``: constante de ``pyglet.window.key`` para disparar.
    """

    def iniciar(self, receptor, proyectil=None, velocidad=20.0,
                alcance=40.0, cadencia=0.3, offset=(0, 0.5, 0),
                hacia=None, desde_camara=False, objetivos=None,
                cuando_impacta=None, cuando_dispara=None,
                con_click=False, tecla=None):
        super(Disparar, self).iniciar(receptor)
        if proyectil is None:
            from pilas3d.actores.proyectil import Proyectil
            proyectil = Proyectil
        receptor.cadencia = cadencia
        receptor._espera_disparo = 0.0
        # como en pilas 2D: la habilidad le "enseña" métodos al actor
        receptor.disparar = self.disparar
        receptor.puede_disparar = self.puede_disparar

        self.proyectil = proyectil
        self.velocidad = velocidad
        self.alcance = alcance
        self.offset = offset
        self.hacia = hacia
        self.desde_camara = desde_camara
        self.objetivos = objetivos
        self.cuando_impacta = cuando_impacta
        self.cuando_dispara = cuando_dispara
        self.con_click = con_click
        self.tecla = tecla
        self._entrada_prev = False

    def puede_disparar(self):
        return self.receptor._espera_disparo <= 0

    def _direccion_y_origen(self):
        r = self.receptor
        if self.desde_camara:
            cam = self.pilas.escena.camara
            d = cam.direccion()
            return cam.posicion, (d.x, d.y, d.z)

        if self.hacia is not None:
            dx, dy, dz = self.hacia
        else:
            rad = math.radians(r.rotacion_y)
            dx, dy, dz = math.sin(rad), 0.0, math.cos(rad)

        # el offset se rota con el actor: (0, y, z) es "delante"
        ox, oy, oz = self.offset
        rad = math.radians(r.rotacion_y)
        rx = ox * math.cos(rad) + oz * math.sin(rad)
        rz = -ox * math.sin(rad) + oz * math.cos(rad)
        return (r.x + rx, r.y + oy, r.z + rz), (dx, dy, dz)

    def disparar(self, **kwargs):
        """Crea y devuelve el proyectil (o None si está en cadencia)."""
        r = self.receptor
        if not self.puede_disparar():
            return None
        r._espera_disparo = r.cadencia

        origen, direccion = self._direccion_y_origen()
        params = dict(direccion=direccion, velocidad=self.velocidad,
                      alcance=self.alcance, objetivos=self.objetivos,
                      cuando_impacta=self.cuando_impacta, ignorar=r)
        params.update(kwargs)
        proyectil = self.proyectil(self.pilas, x=origen[0],
                                   y=origen[1], z=origen[2], **params)
        if self.cuando_dispara:
            self.cuando_dispara()
        return proyectil

    def actualizar(self):
        r = self.receptor
        r._espera_disparo -= self.pilas.dt

        entrada = False
        if self.con_click:
            entrada = self.pilas.control.boton_izquierdo
        if self.tecla is not None:
            entrada = entrada or self.pilas.control.simbolo(self.tecla)

        if entrada and not self._entrada_prev:
            self.disparar()
        self._entrada_prev = entrada
