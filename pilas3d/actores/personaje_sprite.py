# -*- encoding: utf-8 -*-
"""Personaje de sprites 2D en el mundo 3D (estilo Doom / RPG).

A diferencia de ``Animacion`` —que reproduce la hoja entera en
secuencia— este actor interpreta cada **fila como una dirección**:
la hoja de sprites se organiza como ``columnas`` cuadros de
caminata x ``filas`` direcciones (convención LPC: abajo, izquierda,
derecha, arriba).

    per = pilas.actores.PersonajeSprite('heroe.png', columnas=9,
                                        filas=4)
    per.aprender(pilas.habilidades.MoverseConElTeclado)

Mientras se mueve anima su ciclo; quieto queda en ``cuadro_quieto``.
La fila se elige sola a partir del desplazamiento (o a mano con
``definir_direccion('arriba')``).
"""

import math

from pilas3d.actores.animacion import Animacion


class PersonajeSprite(Animacion):
    """Billboard animado que cambia de fila según hacia dónde mira."""

    #: orden por defecto de las filas en la hoja (estilo LPC)
    DIRECCIONES = {'abajo': 0, 'izquierda': 1, 'derecha': 2,
                   'arriba': 3}

    def __init__(self, pilas, imagen, columnas, filas=4,
                 direcciones=None, cuadro_quieto=0,
                 animar_solo_al_moverse=True, **kw):
        # mapa nombre_direccion -> indice de fila en la hoja
        self._mapa = dict(self.DIRECCIONES)
        if direcciones:
            self._mapa.update(direcciones)
        #: columna mostrada cuando el personaje no se mueve
        self.cuadro_quieto = cuadro_quieto
        self.animar_solo_al_moverse = animar_solo_al_moverse
        self._fila = 0
        self._moviendo = False
        self._x_prev = None
        self._z_prev = None
        super(PersonajeSprite, self).__init__(
            pilas, imagen, columnas, filas=filas, **kw)

    # -- dirección / fila ------------------------------------------------

    @property
    def direccion(self):
        """Nombre de la dirección actual ('abajo', 'izquierda', …)."""
        for nombre, fila in self._mapa.items():
            if fila == self._fila:
                return nombre
        return None

    def definir_direccion(self, nombre):
        """Elige la fila de la hoja ('abajo', 'izquierda', 'derecha',
        'arriba' u otro mapeado en ``direcciones``)."""
        if nombre not in self._mapa:
            raise ValueError("dirección desconocida: %r (hay %s)"
                             % (nombre, sorted(self._mapa)))
        self._fila = self._mapa[nombre] % self.filas
        self._encuadrar()

    def _encuadrar(self):
        """Aplica ``cuadro`` restringido a la fila activa."""
        col = self.cuadro % self.columnas
        self._uv_escala = (1.0 / self.columnas, 1.0 / self.filas)
        self._uv_desplazamiento = (
            col / float(self.columnas),
            1.0 - (self._fila + 1) / float(self.filas),
        )

    # la animación corre dentro de la fila elegida
    def _aplicar_cuadro(self):
        self._encuadrar()

    def definir_cuadro(self, cuadro):
        self.cuadro = cuadro % self.columnas
        self._encuadrar()

    def actualizar(self):
        # detectar movimiento -> fila + quieto/caminar
        if self._x_prev is None:
            self._x_prev, self._z_prev = self._x, self._z
        dx, dz = self._x - self._x_prev, self._z - self._z_prev
        self._x_prev, self._z_prev = self._x, self._z
        self._moviendo = abs(dx) + abs(dz) > 1e-6
        if self._moviendo:
            self._elegir_fila(dx, dz)
            self._acumulado += self.pilas.dt * self.velocidad
            if self._acumulado >= 1.0:
                pasos = int(self._acumulado)
                self._acumulado -= pasos
                self.definir_cuadro(self.cuadro + pasos)
        elif self.animar_solo_al_moverse:
            self.definir_cuadro(self.cuadro_quieto)
        else:
            super(PersonajeSprite, self).actualizar()

    def _elegir_fila(self, dx, dz):
        """Del vector de movimiento a la fila más cercana.
        Convención: +z mira a la cámara ('abajo'), +x a la derecha."""
        ang = math.degrees(math.atan2(dz, dx))      # +x=0, +z=90
        if -45 <= ang < 45:
            nombre = 'derecha'
        elif 45 <= ang < 135:
            nombre = 'abajo'
        elif -135 <= ang < -45:
            nombre = 'arriba'
        else:
            nombre = 'izquierda'
        self._fila = self._mapa.get(nombre, 0) % self.filas
