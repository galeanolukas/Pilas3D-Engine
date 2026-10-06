# -*- encoding: utf-8 -*-
"""Mandos USB/gamepad: ``pilas.mandos``.

Envuelve ``pyglet.input.Controller`` — el layout estándar tipo SDL
(a/b/x/y, sticks, gatillos, dpad) que mapea Xbox, PlayStation y
genéricos::

    mando = pilas.mandos.obtener()          # el primero, o None
    if mando and mando.a:
        jugador.saltar()
    mando.stick_izq                         # (x, y) -1..1
    mando.gatillo_der                       # 0..1
    mando.vibrar(1.0, 0.3)                  # rumble si lo soporta

Hot-plug: conectar un mando en caliente queda disponible solo;
``cuando_conecta`` avisa por si el juego quiere reaccionar.

La parte "universal": ``pilas.control.arriba``/``abajo``/
``izquierda``/``derecha`` ya fusionan teclado + primer mando —
``MoverseConElTeclado`` y cualquier juego que lea ``pilas.control``
funcionan con gamepad sin tocar nada.
"""

UMBRAL = 0.5          # inclinación del stick que cuenta como flecha


class Mando(object):
    """Un gamepad conectado — propiedades consultables por frame."""

    def __init__(self, controller):
        self._c = controller

    # -- identidad ------------------------------------------------------------

    @property
    def nombre(self):
        """Nombre reportado por el driver ('Xbox Controller'…)."""
        return self._c.name

    @property
    def tipo(self):
        """'PS', 'XB' o 'GENERIC' — para mostrar el icono correcto."""
        return self._c.type

    @property
    def guid(self):
        return self._c.guid

    # -- dirección: dpad o stick izquierdo -------------------------------------

    # nota: lefty crudo es negativo cuando el stick va ARRIBA
    # (convención SDL) — por eso abajo va negado, no la propiedad

    @property
    def arriba(self):
        return self._c.dpady > 0 or self._c.lefty < -UMBRAL

    @property
    def abajo(self):
        return self._c.dpady < 0 or self._c.lefty > UMBRAL

    @property
    def izquierda(self):
        return self._c.dpadx < 0 or self._c.leftx < -UMBRAL

    @property
    def derecha(self):
        return self._c.dpadx > 0 or self._c.leftx > UMBRAL

    # -- botones ----------------------------------------------------------------

    @property
    def a(self):
        return self._c.a

    @property
    def b(self):
        return self._c.b

    @property
    def x(self):
        return self._c.x

    @property
    def y(self):
        return self._c.y

    @property
    def start(self):
        return self._c.start

    @property
    def select(self):
        return self._c.back

    @property
    def guia(self):
        """Botón central (logo Xbox / PS)."""
        return self._c.guide

    @property
    def bumper_izquierdo(self):
        return self._c.leftshoulder

    @property
    def bumper_derecho(self):
        return self._c.rightshoulder

    @property
    def stick_izq_boton(self):
        """Click del stick izquierdo (L3)."""
        return self._c.leftstick

    @property
    def stick_der_boton(self):
        """Click del stick derecho (R3)."""
        return self._c.rightstick

    # -- analógicos --------------------------------------------------------------

    @property
    def stick_izq(self):
        """(x, y) en -1..1 — y positivo es arriba."""
        return (self._c.leftx, -self._c.lefty)

    @property
    def stick_der(self):
        return (self._c.rightx, -self._c.righty)

    @property
    def gatillo_izq(self):
        """0..1 — cuánto está apretado el gatillo."""
        return self._c.lefttrigger

    @property
    def gatillo_der(self):
        return self._c.righttrigger

    # -- rumble -----------------------------------------------------------------

    def vibrar(self, fuerte=1.0, suave=None, duracion=0.5):
        """Rumble: ``suave`` es el motor fino (None = solo el grueso).

        No todos los mandos/drivers lo soportan — si no, no pasa nada.
        """
        try:
            self._c.rumble_play_strong(fuerte, duracion)
            if suave:
                self._c.rumble_play_weak(suave, duracion)
        except Exception:
            pass

    # -- eventos -----------------------------------------------------------------

    def cuando_pulsa(self, funcion):
        """``funcion(boton)`` — botones como 'a', 'dpup', 'start'…"""
        self._c.push_handlers(on_button_press=lambda c, b: funcion(b))

    def cuando_suelta(self, funcion):
        self._c.push_handlers(on_button_release=lambda c, b: funcion(b))


class Mandos(object):
    """``pilas.mandos`` — lista viva de gamepads conectados."""

    def __init__(self, ventana=None):
        self._ventana = ventana
        self._lista = {}
        self._callbacks_conexion = []
        try:
            from pyglet.input import ControllerManager
            self._manager = ControllerManager()
            self._manager.push_handlers(
                on_connect=self._al_conectar,
                on_disconnect=self._al_desconectar)
            for c in self._manager.get_controllers():
                self._al_conectar(c)
        except Exception:
            self._manager = None      # sin backend de input (tests)

    # -- conexión ---------------------------------------------------------------

    def _al_conectar(self, controller):
        try:
            controller.open(window=self._ventana)
        except Exception:
            pass
        mando = Mando(controller)
        self._lista[controller.guid] = mando
        for fn in self._callbacks_conexion:
            fn(mando)
        return mando

    def _al_desconectar(self, controller):
        self._lista.pop(controller.guid, None)

    # -- consulta -----------------------------------------------------------------

    def lista(self):
        """``[Mando]`` en orden de conexión."""
        return list(self._lista.values())

    def cantidad(self):
        return len(self._lista)

    def obtener(self, indice=0):
        """El mando ``indice``-ésimo (0 = el primero) o ``None``."""
        lista = self.lista()
        return lista[indice] if indice < len(lista) else None

    def cuando_conecta(self, funcion):
        """``funcion(mando)`` cada vez que se conecta uno."""
        self._callbacks_conexion.append(funcion)


class MandosNulo(object):
    """Sin ventana ni backend: la API existe pero no hay mandos."""

    def lista(self):
        return []

    def cantidad(self):
        return 0

    def obtener(self, indice=0):
        return None

    def cuando_conecta(self, funcion):
        pass
