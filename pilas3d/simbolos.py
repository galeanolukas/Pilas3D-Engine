# -*- encoding: utf-8 -*-
"""Constantes de teclado, como ``pilas.simbolos`` en pilas 1.x.

Los valores son los códigos de pyglet (``key.T``, ``key.SPACE``…),
así que se comparan directo con lo que recibe
``escena.cuando_pulsa_tecla``::

    def al_pulsar(tecla):
        if tecla == pilas.simbolos.t:
            print('¡T!')
        elif tecla == pilas.simbolos.ESPACIO:
            nave.disparar()
"""

from pyglet.window import key as _k
from pyglet.window import mouse as _m

# botones del mouse
BOTON_IZQUIERDO = _m.LEFT
BOTON_DERECHO = _m.RIGHT
BOTON_MEDIO = _m.MIDDLE

# movimiento / especiales
IZQUIERDA = _k.LEFT
DERECHA = _k.RIGHT
ARRIBA = _k.UP
ABAJO = _k.DOWN
ESPACIO = _k.SPACE
ENTER = _k.ENTER
ESCAPE = _k.ESCAPE
BACKSPACE = _k.BACKSPACE
TAB = _k.TAB
CTRL = _k.LCTRL
ALT = _k.LALT
SHIFT = _k.LSHIFT
CAPSLOCK = _k.CAPSLOCK

# funciones
F1, F2, F3, F4 = _k.F1, _k.F2, _k.F3, _k.F4
F5, F6, F7, F8 = _k.F5, _k.F6, _k.F7, _k.F8
F9, F10, F11, F12 = _k.F9, _k.F10, _k.F11, _k.F12

# números de la fila superior
_0, _1, _2, _3, _4 = _k._0, _k._1, _k._2, _k._3, _k._4
_5, _6, _7, _8, _9 = _k._5, _k._6, _k._7, _k._8, _k._9

# letras (minúscula, como en pilas)
a, b, c, d, e = _k.A, _k.B, _k.C, _k.D, _k.E
f, g, h, i, j = _k.F, _k.G, _k.H, _k.I, _k.J
k, l, m, n, o = _k.K, _k.L, _k.M, _k.N, _k.O
p, q, r, s, t = _k.P, _k.Q, _k.R, _k.S, _k.T
u, v, w, x, y, z = _k.U, _k.V, _k.W, _k.X, _k.Y, _k.Z
