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

import json
import math
import os

from pilas3d.actores.animacion import Animacion


class PersonajeSprite(Animacion):
    """Billboard animado que cambia de fila según hacia dónde mira."""

    #: orden por defecto de las filas en la hoja (estilo LPC)
    DIRECCIONES = {'abajo': 0, 'izquierda': 1, 'derecha': 2,
                   'arriba': 3}

    def __init__(self, pilas, imagen, columnas=None, filas=4,
                 direcciones=None, espejar=None, cuadro_quieto=0,
                 animar_solo_al_moverse=True, **kw):
        # ``imagen`` puede ser un ``.personaje.json``: el manifiesto
        # trae hoja, grilla, direcciones, estados y tamaño
        # (la fábrica pasa None en los kwargs sin tocar: se filtran
        # para que los valores del manifiesto o los defaults de
        # Animacion puedan aplicar)
        kw = {k: v for k, v in kw.items() if v is not None}
        estados_man = {}
        if isinstance(imagen, str) and imagen.lower().endswith('.json'):
            man, imagen, columnas, filas = _leer_manifiesto(
                imagen, columnas, filas)
            direcciones = man.get('direcciones', direcciones)
            espejar = man.get('espejar', espejar)
            cuadro_quieto = man.get('cuadro_quieto', cuadro_quieto)
            estados_man = man.get('estados', {})
            for k in ('ancho', 'alto', 'velocidad'):
                if k in man:
                    kw.setdefault(k, man[k])
        if columnas is None:
            raise ValueError(
                "PersonajeSprite necesita 'columnas' (o un "
                ".personaje.json que las traiga)")
        # mapa nombre_direccion -> indice de fila en la hoja:
        # un ``direcciones`` explícito reemplaza todo el mapa (si
        # no, las filas por defecto apuntarían a filas que la hoja
        # no tiene); lo espejado vive aparte en ``_espejar``
        self._mapa = dict(direcciones) if direcciones \
            else dict(self.DIRECCIONES)
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
        for nombre, cfg in estados_man.items():
            self.agregar_estado(nombre, **cfg)

    # -- manifiesto .personaje.json ---------------------------------------

    def manifiesto(self, hoja=None):
        """Diccionario serializable del personaje (hoja, grilla,
        direcciones, espejo, estados y tamaño)."""
        estados = {}
        for n, e in self._estados.items():
            cfg = {'fila': e['fila']}
            cfg.update({k: e[k] for k in
                        ('velocidad', 'ciclica', 'quedarse')
                        if e.get(k) not in (None, False)})
            estados[n] = cfg
        return {'hoja': hoja or self.imagen,
                'columnas': self.columnas, 'filas': self.filas,
                'direcciones': dict(self._mapa),
                'espejar': dict(self._espejar),
                'cuadro_quieto': self.cuadro_quieto,
                'velocidad': self.velocidad,
                'ancho': self.ancho, 'alto': self.alto,
                'estados': estados}

    def guardar(self, ruta):
        """Escribe el ``.personaje.json`` del personaje. Si la hoja
        es una ruta absoluta la guarda relativa al JSON para que el
        par .png + .json sea portable."""
        hoja = self.imagen
        if isinstance(hoja, str) and os.path.isabs(hoja):
            base = os.path.dirname(os.path.abspath(ruta))
            hoja = os.path.relpath(hoja, base)
        with open(ruta, 'w') as f:
            json.dump(self.manifiesto(hoja=hoja), f, indent=2)
        return ruta

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
        """Del desplazamiento a la fila, **relativo a la cámara**:
        moverse a la derecha de pantalla muestra la fila 'derecha',
        alejarse 'arriba' (espalda), acercarse 'abajo' (frente)."""
        cam = self.pilas.escena_actual().camara
        d = cam.direccion()
        fx, fz = d.x, d.z
        n = math.hypot(fx, fz)
        if n < 1e-4:
            fx, fz = 0.0, -1.0
        else:
            fx, fz = fx / n, fz / n
        rx, rz = -fz, fx                    # derecha de pantalla
        lx = dx * rx + dz * rz              # cuánto va a la derecha
        lz = dx * fx + dz * fz              # cuánto se aleja
        ang = math.degrees(math.atan2(lz, lx))   # +derecha=0, +lejos=90
        if -45 <= ang < 45:
            nombre = 'derecha'
        elif 45 <= ang < 135:
            nombre = 'arriba'
        elif -135 <= ang < -45:
            nombre = 'abajo'
        else:
            nombre = 'izquierda'
        if nombre in self._mapa or nombre in self._espejar:
            self.definir_direccion(nombre)
        # si la hoja no tiene esa fila, se queda con la anterior


def _leer_manifiesto(ruta, columnas, filas):
    """Lee un ``.personaje.json`` y devuelve
    ``(manifiesto, ruta_hoja, columnas, filas)`` con la hoja
    resuelta relativa al archivo."""
    with open(ruta) as f:
        man = json.load(f)
    if not isinstance(man, dict):
        raise ValueError("%s: el manifiesto debe ser un objeto JSON"
                         % ruta)
    if 'hoja' not in man:
        raise ValueError("%s: el manifiesto no tiene 'hoja'" % ruta)
    hoja = man['hoja']
    if not os.path.isabs(hoja):
        junto = os.path.join(os.path.dirname(os.path.abspath(ruta)),
                             hoja)
        if not os.path.exists(junto):
            # hoja empaquetada en el motor (pilas3d/data/...) o
            # encontrable como la resuelve actor.imagen
            from pilas3d.imagenes import resolver
            try:
                hoja = resolver(hoja)
            except IOError:
                hoja = junto       # que pyglet dé su error habitual
        else:
            hoja = junto
    return man, hoja, man.get('columnas', columnas), \
        man.get('filas', filas)
