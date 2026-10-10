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

Hojas con solo una dirección lateral (común en RPG Maker): se mapea
la faltante a la fila espejada::

    per = pilas.actores.PersonajeSprite('chica.png', columnas=3,
        filas=3, direcciones={'abajo': 0, 'izquierda': 1, 'arriba': 2},
        espejar={'derecha': 'izquierda'})

Filas extra de la hoja se registran como **estados** (ataque, salto,
muerte...) que toman el control hasta terminar::

    per.agregar_estado('atacar', fila=4, ciclica=False)
    per.agregar_estado('morir', fila=5, ciclica=False, quedarse=True)
    per.reproducir_estado('atacar')
"""

import math

from pilas3d.actores.animacion import Animacion


class PersonajeSprite(Animacion):
    """Billboard animado que cambia de fila según hacia dónde mira."""

    #: orden por defecto de las filas en la hoja (estilo LPC)
    DIRECCIONES = {'abajo': 0, 'izquierda': 1, 'derecha': 2,
                   'arriba': 3}

    def __init__(self, pilas, imagen, columnas, filas=4,
                 direcciones=None, espejar=None, cuadro_quieto=0,
                 animar_solo_al_moverse=True, **kw):
        # mapa nombre_direccion -> indice de fila en la hoja
        self._mapa = dict(self.DIRECCIONES)
        if direcciones:
            self._mapa.update(direcciones)
        #: dirección -> dirección de la que toma la fila espejada
        self._espejar = dict(espejar or {})
        #: columna mostrada cuando el personaje no se mueve
        self.cuadro_quieto = cuadro_quieto
        self.animar_solo_al_moverse = animar_solo_al_moverse
        self._direccion = 'abajo'
        self._fila = self._mapa.get('abajo', 0) % filas
        self._flip = False
        self._moviendo = False
        self._x_prev = None
        self._z_prev = None
        self._estados = {}
        self._estado = None          # dict del estado activo o None
        self._estado_fin = False     # estado quedó congelado (morir)
        super(PersonajeSprite, self).__init__(
            pilas, imagen, columnas, filas=filas, **kw)
        inicial = 'abajo' if ('abajo' in self._mapa
                              or 'abajo' in self._espejar) \
            else next(iter(self._mapa))
        self.definir_direccion(inicial)

    # -- dirección / fila ------------------------------------------------

    @property
    def direccion(self):
        """Nombre de la dirección actual ('abajo', 'izquierda', …)."""
        return self._direccion

    @property
    def espejado(self):
        """True si el cuadro actual se dibuja espejado en X."""
        return self._flip

    @espejado.setter
    def espejado(self, valor):
        self._flip = bool(valor)
        self._encuadrar()

    def definir_direccion(self, nombre):
        """Elige la fila de la hoja ('abajo', 'izquierda', 'derecha',
        'arriba' u otra mapeada en ``direcciones``). Si el nombre está
        en ``espejar``, dibuja la fila fuente reflejada en X."""
        if nombre not in self._mapa and nombre not in self._espejar:
            raise ValueError("dirección desconocida: %r (hay %s)"
                             % (nombre, sorted(self._mapa)))
        self._direccion = nombre
        if nombre in self._espejar:
            self._flip = True
            fuente = self._espejar[nombre]
        else:
            self._flip = False
            fuente = nombre
        self._fila = self._mapa.get(fuente, 0) % self.filas
        self._encuadrar()

    def _encuadrar(self):
        """Aplica ``cuadro`` restringido a la fila activa (con flip)."""
        col = self.cuadro % self.columnas
        ancho = 1.0 / self.columnas
        if self._flip:
            self._uv_escala = (-ancho, 1.0 / self.filas)
            u = (col + 1) / float(self.columnas)
        else:
            self._uv_escala = (ancho, 1.0 / self.filas)
            u = col / float(self.columnas)
        self._uv_desplazamiento = (
            u, 1.0 - (self._fila + 1) / float(self.filas))

    # la animación corre dentro de la fila elegida
    def _aplicar_cuadro(self):
        self._encuadrar()

    def definir_cuadro(self, cuadro):
        self.cuadro = cuadro % self.columnas
        self._encuadrar()

    # -- estados extra (atacar, morir, saltar...) ------------------------

    def agregar_estado(self, nombre, fila, velocidad=None,
                       ciclica=False, quedarse=False,
                       al_terminar=None):
        """Registra una fila extra como estado reproducible.

        ``fila``         índice de la fila en la hoja
        ``velocidad``    cuadros/seg (default: la del actor)
        ``ciclica``      repite hasta ``reproducir_estado(None)``
        ``quedarse``     al terminar queda congelado en el último
                         cuadro (p. ej. 'morir')
        ``al_terminar``  callable(actor) al acabar una pasada no
                         cíclica (además de volver o quedarse)
        """
        self._estados[nombre] = {
            'nombre': nombre, 'fila': fila % self.filas,
            'velocidad': velocidad, 'ciclica': ciclica,
            'quedarse': quedarse, 'al_terminar': al_terminar,
        }

    @property
    def estado(self):
        """Estado activo, ``'caminar'``, ``'quieto'`` o None si
        terminó congelado."""
        if self._estado is not None:
            return self._estado['nombre']
        if self._estado_fin:
            return None
        return 'caminar' if self._moviendo else 'quieto'

    def reproducir_estado(self, nombre):
        """Dispara un estado registrado ('atacar', 'morir'...). Con
        ``None`` cancela el estado actual y vuelve al ciclo normal."""
        if nombre is None:
            self._estado = None
            self._estado_fin = False
            self.cuadro = self.cuadro_quieto
            self._acumulado = 0.0
            self._encuadrar()
            return
        if nombre not in self._estados:
            raise ValueError("estado desconocido: %r (hay %s)"
                             % (nombre, sorted(self._estados)))
        self._estado = dict(self._estados[nombre])
        self._estado_fin = False
        self._fila = self._estado['fila']
        self._flip = False
        self.cuadro = 0
        self._acumulado = 0.0
        self._encuadrar()

    def _actualizar_estado(self):
        """Avanza la fila del estado; True si sigue activo."""
        est = self._estado
        vel = est['velocidad'] if est['velocidad'] else self.velocidad
        self._acumulado += self.pilas.dt * vel
        if self._acumulado < 1.0:
            return True
        pasos = int(self._acumulado)
        self._acumulado -= pasos
        nuevo = self.cuadro + pasos
        if nuevo < self.columnas:
            self.definir_cuadro(nuevo)
            return True
        # terminó la pasada
        if est['ciclica']:
            self.definir_cuadro(nuevo % self.columnas)
            return True
        self.definir_cuadro(self.columnas - 1)
        if est['al_terminar']:
            est['al_terminar'](self)
        if est['quedarse']:
            self._estado_fin = True
        self._estado = None
        self._moviendo = False
        return self._estado is not None

    # -- update ----------------------------------------------------------

    def actualizar(self):
        if self._estado is not None:
            self._actualizar_estado()
            return
        if self._estado_fin:
            return                          # congelado (morir)
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
        if nombre in self._mapa or nombre in self._espejar:
            self.definir_direccion(nombre)
        # si la hoja no tiene esa fila, se queda con la anterior
