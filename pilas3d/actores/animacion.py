# -*- encoding: utf-8 -*-
"""Animación por cuadros sobre un cartel (spritesheet).

Port del concepto ``Grilla`` + ``Animacion`` de pilas-engine: la
imagen se divide en una grilla de ``columnas`` x ``filas`` cuadros que
se recorren en orden (izquierda a derecha, arriba a abajo)::

    fantasma = pilas.actores.Animacion('fantasma.png', columnas=8,
                                       velocidad=12)

    boom = pilas.actores.Animacion('explosion.png', columnas=7,
                                   velocidad=14, ciclica=False,
                                   eliminar_al_terminar=True)
"""

from pilas3d.actores.cartel import Cartel


class Animacion(Cartel):
    """Cartel cuya textura es una grilla de cuadros animados."""

    def __init__(self, pilas, imagen, columnas, filas=1, x=0, y=0, z=0,
                 ancho=1.0, alto=1.0, velocidad=10, ciclica=True,
                 eliminar_al_terminar=False):
        super(Animacion, self).__init__(pilas, x=x, y=y, z=z,
                                        ancho=ancho, alto=alto)
        self.imagen = imagen
        self.columnas = columnas
        self.filas = filas
        self.velocidad = velocidad        # cuadros por segundo
        self.ciclica = ciclica
        self.eliminar_al_terminar = eliminar_al_terminar
        self.cuadro = 0
        self._acumulado = 0.0
        self._uv_escala = (1.0 / columnas, 1.0 / filas)
        self._aplicar_cuadro()

    @property
    def total_cuadros(self):
        return self.columnas * self.filas

    def _aplicar_cuadro(self):
        col = self.cuadro % self.columnas
        fila = self.cuadro // self.columnas
        # v=0 está abajo: la fila 0 de la grilla es la de arriba.
        self._uv_desplazamiento = (
            col / float(self.columnas),
            1.0 - (fila + 1) / float(self.filas),
        )

    def definir_cuadro(self, cuadro):
        """Salta a un cuadro de la grilla (0 .. total_cuadros - 1)."""
        self.cuadro = cuadro % self.total_cuadros
        self._aplicar_cuadro()

    def actualizar(self):
        dt = self.pilas.dt
        self._acumulado += dt * self.velocidad
        if self._acumulado < 1.0:
            return
        avance = int(self._acumulado)
        self._acumulado -= avance
        nuevo = self.cuadro + avance
        if nuevo >= self.total_cuadros:
            if self.ciclica:
                nuevo %= self.total_cuadros
            else:
                if self.eliminar_al_terminar:
                    self.eliminar()
                    return
                nuevo = self.total_cuadros - 1
        self.definir_cuadro(nuevo)
