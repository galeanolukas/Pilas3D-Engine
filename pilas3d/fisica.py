# -*- encoding: utf-8 -*-
"""Física 2D para el mundo 3D, con pymunk (Chipmunk2D).

El motor es 3D pero la mecánica de muchos géneros es plana:

- plano ``'xy'``: plataformas / vista lateral — la gravedad tira en
  Y, la cámara mira en -Z (estilo pilas-engine 2D)
- plano ``'xz'``: vista cenital (top-down) — sin gravedad por
  defecto, los cuerpos se deslizan sobre el suelo

Uso::

    pilas.fisica.plano = 'xy'
    pilas.fisica.gravedad = (0, -9.8)

    pelota = pilas.actores.Esfera(y=6, radio=0.4)
    pelota.radio_de_colision = 0.4
    pilas.fisica.vincular(pelota, forma='circulo', elasticidad=0.8)

    suelo = pilas.actores.Piso()
    pilas.fisica.vincular(suelo, forma='caja', estatico=True,
                          ancho=30, alto=0.1)

    pilas.fisica.cuando_colisionan(pelota, suelo, al_tocar)

Requiere ``pymunk`` (``pip install pymunk``) — es opcional: el
subsistema solo lo importa al vincular el primer cuerpo y avisa con
un mensaje claro si falta.
"""

import math

_GRAVEDAD_POR_PLANO = {'xy': (0.0, -9.8), 'xz': (0.0, 0.0)}


class Cuerpo(object):
    """Envoltura en español del ``pymunk.Body`` vinculado a un actor.

    Accesible como ``actor.cuerpo`` tras ``fisica.vincular(actor)``.
    ``.pymunk`` expone el body crudo para lo avanzado.
    """

    def __init__(self, fisica, actor, body):
        self._fisica = fisica
        self.actor = actor
        self.pymunk = body

    @property
    def velocidad(self):
        """Velocidad en el plano físico: ``(u, v)`` unidades/seg."""
        v = self.pymunk.velocity
        return (v.x, v.y)

    @velocidad.setter
    def velocidad(self, uv):
        self.pymunk.velocity = tuple(uv)

    def impulsar(self, u, v):
        """Aplica un impulso (salto, disparo): suma ``(u, v)``."""
        self.pymunk.apply_impulse_at_world_point(
            (u, v), self.pymunk.position)

    def detener(self):
        """Frena el cuerpo por completo (lineal + angular)."""
        self.pymunk.velocity = (0, 0)
        self.pymunk.angular_velocity = 0.0

    @property
    def posicion(self):
        """Posición en el plano físico ``(u, v)``."""
        p = self.pymunk.position
        return (p.x, p.y)


class Fisica(object):
    """Subsistema de física 2D de pilas3d (``pilas.fisica``)."""

    def __init__(self, pilas):
        self._pilas = pilas
        self._plano = 'xy'
        self._gravedad = _GRAVEDAD_POR_PLANO['xy']
        self._space = None            # pymunk.Space (lazy)
        self._cuerpos = {}            # actor -> Cuerpo
        self._tipos = {}              # actor -> collision_type
        self._prox_tipo = 1

    # -- configuración -----------------------------------------------------

    def _modulo(self):
        try:
            import pymunk
        except ImportError:
            raise RuntimeError(
                "la física necesita pymunk: 'pip install pymunk'")
        return pymunk

    @property
    def plano(self):
        """Plano donde corre la física: ``'xy'`` (lateral, gravedad
        en Y) o ``'xz'`` (cenital, sin gravedad por defecto).

        Cambiar de plano antes de vincular cuerpos; resetea la
        gravedad al valor razonable del plano."""
        return self._plano

    @plano.setter
    def plano(self, valor):
        if valor not in ('xy', 'xz'):
            raise ValueError("plano debe ser 'xy' o 'xz'")
        self._plano = valor
        self.gravedad = _GRAVEDAD_POR_PLANO[valor]

    @property
    def gravedad(self):
        """Gravedad del espacio en unidades del plano ``(gu, gv)``."""
        return self._gravedad

    @gravedad.setter
    def gravedad(self, guv):
        self._gravedad = (float(guv[0]), float(guv[1]))
        if self._space is not None:
            self._space.gravity = self._gravedad

    def _espacio(self):
        if self._space is None:
            self._space = self._modulo().Space()
            self._space.gravity = self._gravedad
        return self._space

    # -- coordenadas plano <-> mundo ---------------------------------------

    def _coords(self, actor):
        """(u, v) del actor según el plano elegido."""
        if self._plano == 'xy':
            return (actor.x, actor.y)
        return (actor.x, actor.z)

    def _poner_coords(self, actor, u, v):
        if self._plano == 'xy':
            actor.x, actor.y = u, v
        else:
            actor.x, actor.z = u, v

    def _angulo_de(self, actor):
        """Rotación del actor en radianes (convención pymunk CCW)."""
        if self._plano == 'xy':
            return math.radians(actor.rotacion_z)
        return -math.radians(actor.rotacion_y)

    def _poner_angulo(self, actor, rad):
        if self._plano == 'xy':
            actor.rotacion_z = math.degrees(rad)
        else:
            actor.rotacion_y = -math.degrees(rad)

    # -- cuerpos ------------------------------------------------------------

    def vincular(self, actor, forma='caja', estatico=False,
                 cinematica=False, ancho=None, alto=None, radio=None,
                 masa=1.0, friccion=0.7, elasticidad=0.0,
                 sensor=False):
        """Ata un ``pymunk.Body`` al actor y devuelve su ``Cuerpo``.

        - ``forma``: ``'caja'`` (por defecto), ``'circulo'`` o
          ``'segmento'`` (suelos/techos de un segmento de ``ancho``)
        - ``estatico``: no se mueve nunca (pisos, paredes)
        - ``cinematica``: lo mueve el juego (plataformas móviles,
          personajes por teclado) — el body sigue al actor
        - ``sensor``: detecta colisiones sin empujar (gatillos,
          monedas que se agarran)
        - ``ancho``/``alto``/``radio``: por defecto se deducen de
          ``actor.radio_de_colision``
        """
        pymunk = self._modulo()
        space = self._espacio()
        u, v = self._coords(actor)
        radio = actor.radio_de_colision if radio is None else radio

        if estatico:
            tipo_body = pymunk.Body.STATIC
        elif cinematica:
            tipo_body = pymunk.Body.KINEMATIC
        else:
            tipo_body = pymunk.Body.DYNAMIC

        if forma == 'circulo':
            momento = pymunk.moment_for_circle(masa, 0, radio)
        elif forma == 'segmento':
            momento = pymunk.moment_for_segment(
                masa, (-(ancho or 2 * radio) / 2, 0),
                ((ancho or 2 * radio) / 2, 0), 0)
        else:  # caja
            ancho = ancho or 2 * radio
            alto = alto or 2 * radio
            momento = pymunk.moment_for_box(masa, (ancho, alto))

        body = pymunk.Body(masa, momento, body_type=tipo_body)
        body.position = (u, v)
        body.angle = self._angulo_de(actor)

        if forma == 'circulo':
            shape = pymunk.Circle(body, radio)
        elif forma == 'segmento':
            mitad = (ancho or 2 * radio) / 2
            shape = pymunk.Segment(body, (-mitad, 0), (mitad, 0), 0.01)
        else:
            shape = pymunk.Poly.create_box(body, (ancho, alto))
        shape.friction = friccion
        shape.elasticity = elasticidad
        shape.sensor = sensor
        shape.collision_type = self._tipo_de(actor)

        space.add(body, shape)
        cuerpo = Cuerpo(self, actor, body)
        self._cuerpos[actor] = cuerpo
        actor.cuerpo = cuerpo
        return cuerpo

    def desvincular(self, actor):
        """Suelta el cuerpo del actor (deja de simularse)."""
        cuerpo = self._cuerpos.pop(actor, None)
        if cuerpo is not None and self._space is not None:
            self._space.remove(cuerpo.pymunk,
                               *cuerpo.pymunk.shapes)
            self._tipos.pop(actor, None)
        if getattr(actor, 'cuerpo', None) is cuerpo:
            actor.cuerpo = None

    def cuerpo_de(self, actor):
        """El ``Cuerpo`` vinculado a ``actor`` (o None)."""
        return self._cuerpos.get(actor)

    def limpiar(self):
        """Suelta todos los cuerpos (al cambiar de nivel/escena)."""
        for actor in list(self._cuerpos):
            self.desvincular(actor)

    def _tipo_de(self, actor):
        if actor not in self._tipos:
            self._tipos[actor] = self._prox_tipo
            self._prox_tipo += 1
        return self._tipos[actor]

    # -- colisiones ----------------------------------------------------------

    def cuando_colisionan(self, actor_a, actor_b, funcion):
        """Llama ``funcion(actor_a, actor_b)`` cuando ambos se tocan.

        Funciona también con sensores (que no empujan): sirve para
        gatillos — "la moneda desaparece al tocarla"."""
        self._modulo()
        espacio = self._espacio()

        def al_empezar(arbiter, _espacio, _datos):
            funcion(actor_a, actor_b)
            return True           # True: la respuesta física sigue

        espacio.on_collision(self._tipo_de(actor_a),
                             self._tipo_de(actor_b),
                             begin=al_empezar)

    # -- paso de simulación ----------------------------------------------------

    def _actualizar(self):
        """Un paso por frame (lo llama ``Pilas._tick``)."""
        if self._space is None or not self._cuerpos:
            return
        escena = self._pilas.escena_actual()

        # actores que desaparecieron (eliminar / cambio de escena)
        if escena is not None:
            for actor in list(self._cuerpos):
                if actor not in escena.actores:
                    self.desvincular(actor)

        # los cinemáticos siguen al actor (plataformas, jugador)
        for actor, cuerpo in self._cuerpos.items():
            if cuerpo.pymunk.body_type == self._modulo().Body.KINEMATIC:
                cuerpo.pymunk.position = self._coords(actor)
                cuerpo.pymunk.angle = self._angulo_de(actor)

        self._space.step(self._pilas.dt)

        # los dinámicos escriben su posición/rotación en el actor
        dinamico = self._modulo().Body.DYNAMIC
        for actor, cuerpo in self._cuerpos.items():
            if cuerpo.pymunk.body_type == dinamico:
                p = cuerpo.pymunk.position
                self._poner_coords(actor, p.x, p.y)
                self._poner_angulo(actor, cuerpo.pymunk.angle)
