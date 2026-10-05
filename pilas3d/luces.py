# -*- encoding: utf-8 -*-
"""Luces de la escena: una direccional (el "sol") + puntuales.

Uso::

    pilas.luces.direccional.ambiente = 0.5
    pilas.luces.direccional.color = pilas.colores.azul
    pilas.luces.agregar(pilas3d.luces.LuzPuntual(x=2, y=3, z=0,
                                               color=(1, 0.8, 0.6),
                                               alcance=8))
    pilas.luces.limpiar()       # quita las puntuales

Máximo 8 luces puntuales (el shader recorre un array fijo).
"""

import math

MAX_PUNTUALES = 8


class LuzDireccional(object):
    """Luz infinita con dirección (como el sol).

    ``ambiente`` es la intensidad base; ``ambiente_color`` la tiñe
    (``Cielo.iluminar_escena`` la extrae de un fondo ``.hdr``).
    """

    def __init__(self, direccion=(-0.4, -0.8, -0.5), color=(1, 1, 1),
                 ambiente=0.45, ambiente_color=(1, 1, 1)):
        self.direccion = direccion
        self.color = color
        self.ambiente = ambiente
        self.ambiente_color = ambiente_color


class LuzPuntual(object):
    """Luz que emite desde un punto y decae con la distancia."""

    def __init__(self, x=0, y=2, z=0, color=(1, 1, 1), alcance=10.0):
        self.x = x
        self.y = y
        self.z = z
        self.color = color
        self.alcance = alcance


class Luces(object):
    """Colección de luces de una escena."""

    def __init__(self):
        self.direccional = LuzDireccional()
        self.puntuales = []

    def agregar(self, luz):
        """Agrega una ``LuzPuntual`` o ``LuzDireccional``."""
        if isinstance(luz, LuzDireccional):
            self.direccional = luz
        else:
            self.puntuales.append(luz)
        return luz

    def quitar(self, luz):
        if luz in self.puntuales:
            self.puntuales.remove(luz)

    def limpiar(self):
        """Quita las puntuales y deja la direccional por defecto."""
        self.puntuales = []
        self.direccional = LuzDireccional()

    def aplicar(self, programa):
        """Sube los uniforms de luz al shader (una vez por frame)."""
        from pilas3d import colores

        d = self.direccional
        dx, dy, dz = d.direccion
        norma = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        # el shader usa la dirección HACIA la luz
        programa["luz_dir"] = (-dx / norma, -dy / norma, -dz / norma)
        programa["luz_dir_color"] = tuple(colores.normalizar(d.color))
        programa["luz_ambiente"] = float(d.ambiente)
        programa["luz_ambiente_color"] = \
            tuple(colores.normalizar(d.ambiente_color))

        n = min(len(self.puntuales), MAX_PUNTUALES)
        programa["cantidad_puntuales"] = n
        # pyglet quiere una tupla por elemento del array
        posiciones = [(luz.x, luz.y, luz.z) for luz in
                      self.puntuales[:MAX_PUNTUALES]]
        colores_l = [tuple(colores.normalizar(luz.color)) for luz in
                     self.puntuales[:MAX_PUNTUALES]]
        alcances = [float(luz.alcance) for luz in
                    self.puntuales[:MAX_PUNTUALES]]
        relleno = MAX_PUNTUALES - n
        posiciones += [(0.0, 0.0, 0.0)] * relleno
        colores_l += [(0.0, 0.0, 0.0)] * relleno
        alcances += [1.0] * relleno
        programa["luz_posicion"] = tuple(posiciones)
        programa["luz_color"] = tuple(colores_l)
        programa["luz_alcance"] = tuple(alcances)
